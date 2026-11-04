# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You may not use this file except in compliance
# with the License. A copy of the License is located at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# or in the "license" file accompanying this file. This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES
# OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing
# permissions and limitations under the License.

"""
CATS - Data Protection and Policy Enforcement

This test verifies:
- LZA-SEC-DPPE-2: S3 public access block configured at account level
- LZA-SEC-DPPE-3: SCP manual changes are reverted by the LZA EventBridge rule and Lambda
- LZA-SEC-DPPE-4: Organization tagging policies configured
- LZA-SEC-DPPE-5: Organization backup policies configured
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

import pytest
from cats import GetAccountFixture, cats
from cats.config import Settings
from cats.constants import get_account_fixture_names

from cats_utils.boto import DEFAULT_RETRY_CONFIG
from cats_utils.cats_cache import get_sns_topic_arns
from cats_utils.evidence import Evidence
from lza_utils.lza_config import lza_config

if TYPE_CHECKING:
    from mypy_boto3_cloudformation.client import CloudFormationClient
    from mypy_boto3_organizations.client import OrganizationsClient
    from mypy_boto3_organizations.type_defs import PolicySummaryTypeDef

    from cats_types import ManagementAccount

logger = logging.getLogger(__name__)

# The RevertScpChanges construct (LZA constructs/lib/aws-events/revert-scp-changes.ts) is
# deployed by the Finalize stack. Its rule and function carry no explicit names, so they are
# resolved through CloudFormation by the construct's logical ID prefixes.
_REVERT_SCP_RULE_LOGICAL_ID_PREFIX = "RevertScpChangesModifyScpRule"
_REVERT_SCP_FUNCTION_LOGICAL_ID_PREFIX = "RevertScpChangesRevertScpChangesFunction"


def _finalize_stack_name(management_account_id: str) -> str:
    """Name of the LZA Finalize stack: `${AcceleratorPrefix}-FinalizeStack-${managementAccountId}-${globalRegion}`."""
    config = lza_config()
    return f"{config.accelerator_prefix}-FinalizeStack-{management_account_id}-{config.global_region}"


def _stack_physical_ids(cfn_client: CloudFormationClient, stack_name: str, resource_type: str, logical_id_prefix: str) -> list[str]:
    """Physical IDs of a stack's resources of one type whose logical ID starts with the construct prefix."""
    return [
        resource["PhysicalResourceId"]
        for page in cfn_client.get_paginator("list_stack_resources").paginate(StackName=stack_name)
        for resource in page["StackResourceSummaries"]
        if resource["ResourceType"] == resource_type and resource["LogicalResourceId"].startswith(logical_id_prefix)
    ]


def _policies_have_targets(client: OrganizationsClient, policies: list[PolicySummaryTypeDef]) -> bool:
    """Check if any policy in the list is attached to at least one target."""
    for policy in policies:
        targets_paginator = client.get_paginator("list_targets_for_policy")
        targets = [t for page in targets_paginator.paginate(PolicyId=policy["Id"]) for t in page["Targets"]]
        if targets:
            return True
    return False


@pytest.mark.parametrize("account_fixture_name", get_account_fixture_names())
@cats(standard_name=["LZA-SEC-DPPE-2"], test_suite="s3", test_id="1", evidence=Evidence.CONFIGURATION)
def test_s3_public_access_block(account_fixture_name: str, get_account_fixture: GetAccountFixture) -> None:
    """Verify S3 public access block is configured at the account level."""
    # act
    account = get_account_fixture(account_fixture_name)
    client = account.session.client("s3control", region_name=lza_config().home_region, config=DEFAULT_RETRY_CONFIG)
    response = client.get_public_access_block(AccountId=account.account_id)
    config = response["PublicAccessBlockConfiguration"]

    # assert
    assert config["BlockPublicAcls"] is True, f"BlockPublicAcls not enabled in {account_fixture_name}"
    assert config["IgnorePublicAcls"] is True, f"IgnorePublicAcls not enabled in {account_fixture_name}"
    assert config["BlockPublicPolicy"] is True, f"BlockPublicPolicy not enabled in {account_fixture_name}"
    assert config["RestrictPublicBuckets"] is True, f"RestrictPublicBuckets not enabled in {account_fixture_name}"


@cats(standard_name=["LZA-SEC-DPPE-3"], test_suite="organizations", test_id="15", evidence=Evidence.CONFIGURATION)
def test_scp_revert_changes_rule_targets_revert_lambda(Management_account: ManagementAccount) -> None:
    """Verify the SCP revert automation is deployed as declared by scpRevertChangesConfig.

    LZA deploys an EventBridge rule matching Organizations policy mutations via CloudTrail
    and a Lambda that re-applies the LZA-managed SCPs, optionally notifying an SNS topic.
    """
    # arrange
    config = lza_config()
    revert_config = config.scp_revert_changes_config
    assert revert_config.enable is True, "scpRevertChangesConfig.enable is not true in security-config.yaml"

    partition = Settings().cats_deployment_settings.partition
    expected_sns_topic_arn = (
        f"arn:{partition}:sns:{config.home_region}:{Management_account.account_id}:{config.sns_topic_name_prefix}-{revert_config.sns_topic_name}"
        if revert_config.sns_topic_name
        else ""
    )
    stack_name = _finalize_stack_name(Management_account.account_id)
    cfn_client = Management_account.session.client("cloudformation", region_name=config.global_region, config=DEFAULT_RETRY_CONFIG)
    events_client = Management_account.session.client("events", region_name=config.global_region, config=DEFAULT_RETRY_CONFIG)
    lambda_client = Management_account.session.client("lambda", region_name=config.global_region, config=DEFAULT_RETRY_CONFIG)

    # act
    rule_names = _stack_physical_ids(cfn_client, stack_name, "AWS::Events::Rule", _REVERT_SCP_RULE_LOGICAL_ID_PREFIX)
    function_names = _stack_physical_ids(cfn_client, stack_name, "AWS::Lambda::Function", _REVERT_SCP_FUNCTION_LOGICAL_ID_PREFIX)
    assert len(rule_names) == 1, f"Expected one {_REVERT_SCP_RULE_LOGICAL_ID_PREFIX}* rule in {stack_name}, found {rule_names}"
    assert len(function_names) == 1, f"Expected one {_REVERT_SCP_FUNCTION_LOGICAL_ID_PREFIX}* function in {stack_name}, found {function_names}"

    rule = events_client.describe_rule(Name=rule_names[0])
    target_arns = [
        target["Arn"] for page in events_client.get_paginator("list_targets_by_rule").paginate(Rule=rule_names[0]) for target in page["Targets"]
    ]
    function_configuration = lambda_client.get_function(FunctionName=function_names[0])["Configuration"]
    environment = function_configuration["Environment"]["Variables"]

    sns_topic_exists = expected_sns_topic_arn in get_sns_topic_arns(Management_account, config.home_region) if revert_config.sns_topic_name else None

    # assert
    expected: dict[str, Any] = {
        "rule_state": "ENABLED",
        "event_pattern": {
            "source": ["aws.organizations"],
            "detail-type": ["AWS API Call via CloudTrail"],
            "detail": {
                # LZA hardcodes this eventSource for every partition (revert-scp-changes.ts, ModifyScpRule).
                "eventSource": ["organizations.amazonaws.com"],  # partition: fixed
                "eventName": ["AttachPolicy", "DetachPolicy", "UpdatePolicy"],
            },
        },
        "target_arns": [function_configuration["FunctionArn"]],
        "accelerator_prefix": config.accelerator_prefix,
        "sns_topic_arn": expected_sns_topic_arn,
        "sns_topic_exists": True if revert_config.sns_topic_name else None,
    }
    actual: dict[str, Any] = {
        "rule_state": rule["State"],
        "event_pattern": json.loads(rule["EventPattern"]),
        "target_arns": target_arns,
        "accelerator_prefix": environment["ACCELERATOR_PREFIX"],
        "sns_topic_arn": environment["SNS_TOPIC_ARN"],
        "sns_topic_exists": sns_topic_exists,
    }
    assert actual == expected


@cats(standard_name=["LZA-SEC-DPPE-4"], test_suite="organizations", test_id="13", evidence=Evidence.CONFIGURATION)
def test_organization_tagging_policy(Management_account: ManagementAccount) -> None:
    """Verify organization tagging policies are configured and attached."""
    # act
    cfg = lza_config()
    client = Management_account.session.client("organizations", region_name=cfg.home_region, config=DEFAULT_RETRY_CONFIG)
    paginator = client.get_paginator("list_policies")
    policies = [p for page in paginator.paginate(Filter="TAG_POLICY") for p in page["Policies"]]

    # assert
    assert policies, "No organization tagging policies found"
    assert _policies_have_targets(client, policies), "Tagging policies exist but none are attached to any targets"


@cats(standard_name=["LZA-SEC-DPPE-5"], test_suite="organizations", test_id="14", evidence=Evidence.CONFIGURATION)
def test_organization_backup_policy(Management_account: ManagementAccount) -> None:
    """Verify organization backup policies are configured and attached."""
    # act
    cfg = lza_config()
    client = Management_account.session.client("organizations", region_name=cfg.home_region, config=DEFAULT_RETRY_CONFIG)
    paginator = client.get_paginator("list_policies")
    policies = [p for page in paginator.paginate(Filter="BACKUP_POLICY") for p in page["Policies"]]

    # assert
    assert policies, "No organization backup policies found"
    assert _policies_have_targets(client, policies), "Backup policies exist but none are attached to any targets"

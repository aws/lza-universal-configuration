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

"""CATS - CloudFormation Stack Policy Protection.

Verifies that LZA-managed CloudFormation stacks have stack policies that
deny destructive updates on critical networking resource types.

- LZA-G-OM-7: CloudFormation stack protection (stack policy)
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

import pytest
from cats import GetAccountFixture, cats

from cats_utils.accounts import non_management_accounts
from cats_utils.boto import DEFAULT_RETRY_CONFIG
from cats_utils.evidence import Evidence
from lza_utils.lza_config import lza_config

if TYPE_CHECKING:
    from mypy_boto3_cloudformation import CloudFormationClient

logger = logging.getLogger(__name__)


def _get_accelerator_stack_names(
    cfn_client: CloudFormationClient,
    accelerator_prefix: str,
) -> list[str]:
    """Return names of active LZA-prefixed CloudFormation stacks."""
    paginator = cfn_client.get_paginator("list_stacks")
    stacks: list[str] = []
    for page in paginator.paginate(StackStatusFilter=["CREATE_COMPLETE", "UPDATE_COMPLETE"]):
        for summary in page["StackSummaries"]:
            if summary["StackName"].startswith(accelerator_prefix):
                stacks.append(summary["StackName"])
    return stacks


def _get_stack_policy(cfn_client: CloudFormationClient, stack_name: str) -> dict[str, Any] | None:
    """Fetch and parse a stack's policy JSON. Returns None if no policy is set."""
    response = cfn_client.get_stack_policy(StackName=stack_name)
    body: str | None = response.get("StackPolicyBody")
    if body is None:
        return None
    policy: dict[str, Any] = json.loads(body)
    return policy


def _has_deny_replace_and_delete(policy: dict[str, Any]) -> bool:
    """Check that a policy contains a Deny statement covering Update:Replace and Update:Delete.

    LZA applies this deny scoped to specific resource types via a Condition
    block with StringEquals on ResourceType (e.g., AWS::EC2::VPC, etc.).
    """
    for stmt in policy.get("Statement", []):
        if stmt.get("Effect") != "Deny":
            continue
        actions = stmt.get("Action", [])
        if isinstance(actions, str):
            actions = [actions]
        if "Update:Replace" not in actions or "Update:Delete" not in actions:
            continue
        # Verify the condition scopes to ResourceType
        condition = stmt.get("Condition", {})
        resource_types = condition.get("StringEquals", {}).get("ResourceType", [])
        if resource_types:
            return True
    return False


def _get_protected_resource_types(policy: dict[str, Any]) -> set[str]:
    """Extract the set of resource types protected by Deny Update:Replace/Delete."""
    for stmt in policy.get("Statement", []):
        if stmt.get("Effect") != "Deny":
            continue
        actions = stmt.get("Action", [])
        if isinstance(actions, str):
            actions = [actions]
        if "Update:Replace" not in actions or "Update:Delete" not in actions:
            continue
        condition = stmt.get("Condition", {})
        resource_types = condition.get("StringEquals", {}).get("ResourceType", [])
        if isinstance(resource_types, str):
            resource_types = [resource_types]
        if resource_types:
            return set(resource_types)
    return set()


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@pytest.mark.parametrize("account_fixture_name", non_management_accounts())
@cats(
    standard_name=["LZA-G-OM-7"],
    test_suite="operations",
    test_id="7",
    mutating=False,
    evidence=Evidence.CONFIGURATION,
)
def test_cfn_stack_policy_denies_destructive_updates(
    account_fixture_name: str,
    region: str,
    get_account_fixture: GetAccountFixture,
) -> None:
    """Verify LZA stacks have a policy denying Update:Replace and Update:Delete."""
    # arrange
    account = get_account_fixture(account_fixture_name)
    cfn_client: CloudFormationClient = account.session.client("cloudformation", region_name=region, config=DEFAULT_RETRY_CONFIG)
    accelerator_prefix = lza_config().accelerator_prefix

    # act
    accelerator_stacks = _get_accelerator_stack_names(cfn_client, accelerator_prefix)
    assert accelerator_stacks, f"No {accelerator_prefix}-prefixed stacks found in {account_fixture_name} {region}"

    missing_policy: list[str] = []
    inadequate_policy: list[str] = []

    for stack_name in accelerator_stacks:
        policy = _get_stack_policy(cfn_client, stack_name)
        if policy is None:
            missing_policy.append(stack_name)
        elif not _has_deny_replace_and_delete(policy):
            inadequate_policy.append(stack_name)

    # assert
    assert missing_policy == [], f"Stacks with no stack policy in {account_fixture_name} {region}: {missing_policy}"
    assert inadequate_policy == [], f"Stacks missing Deny on Update:Replace/Update:Delete in {account_fixture_name} {region}: {inadequate_policy}"


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@pytest.mark.parametrize("account_fixture_name", non_management_accounts())
@cats(
    standard_name=["LZA-G-OM-7"],
    test_suite="operations",
    test_id="7b",
    mutating=False,
    evidence=Evidence.CONFIGURATION,
)
def test_cfn_stack_policy_blocks_protected_resource_update(
    account_fixture_name: str,
    region: str,
    get_account_fixture: GetAccountFixture,
) -> None:
    """Verify stack policy protects the expected networking resource types.

    LZA applies a stack policy that denies Update:Replace and Update:Delete
    scoped to critical networking resource types (VPC, TransitGateway, Subnet,
    etc.) during stack updates. This test validates the protected types match
    the expected set from global-config.yaml.
    """
    # arrange
    account = get_account_fixture(account_fixture_name)
    cfn_client: CloudFormationClient = account.session.client("cloudformation", region_name=region, config=DEFAULT_RETRY_CONFIG)
    accelerator_prefix = lza_config().accelerator_prefix

    expected_protected_types = {
        "AWS::EC2::FlowLog",
        "AWS::EC2::InternetGateway",
        "AWS::EC2::NatGateway",
        "AWS::EC2::PrefixList",
        "AWS::EC2::Route",
        "AWS::EC2::RouteTable",
        "AWS::EC2::SecurityGroup",
        "AWS::EC2::Subnet",
        "AWS::EC2::SubnetRouteTableAssociation",
        "AWS::EC2::TransitGateway",
        "AWS::EC2::TransitGatewayPeeringAttachment",
        "AWS::EC2::TransitGatewayVpcAttachment",
        "AWS::EC2::VPC",
        "AWS::EC2::VPCCidrBlock",
    }

    # act
    accelerator_stacks = _get_accelerator_stack_names(cfn_client, accelerator_prefix)
    assert accelerator_stacks, f"No {accelerator_prefix}-prefixed stacks found in {account_fixture_name} {region}"

    # Find a stack with the deny policy and verify protected types
    for stack_name in accelerator_stacks:
        policy = _get_stack_policy(cfn_client, stack_name)
        if policy is None:
            continue
        protected_types = _get_protected_resource_types(policy)
        if protected_types:
            missing_types = expected_protected_types - protected_types
            assert missing_types == set(), f"Stack {stack_name} policy missing protection for: {sorted(missing_types)}"
            return

    pytest.fail(f"No stack with a resource-type-scoped deny policy found in {account_fixture_name} {region}")

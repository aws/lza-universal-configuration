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
CATS - SCP Enforcement: CloudFormation, SSM, S3, EventBridge

This test verifies:
- LZA-G-SCP-14: Restricts the modification of CloudFormation stacks managed by LZA
- LZA-G-SCP-15: Restricts the modification of SSM Parameter Store parameters managed by LZA
- LZA-G-SCP-16: Restricts the modification of S3 bucket settings managed by LZA
- LZA-G-SCP-18: Restricts the modification of EventBridge settings managed by LZA
"""

from __future__ import annotations

import logging

import pytest
from botocore.exceptions import ClientError
from cats import GetAccountFixture, cats

from cats_utils.accounts import non_management_accounts
from cats_utils.boto import DEFAULT_RETRY_CONFIG
from cats_utils.cats_cache import get_s3_buckets
from cats_utils.evidence import Evidence
from lza_utils.lza_config import lza_config

logger = logging.getLogger(__name__)


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@pytest.mark.parametrize("account_fixture_name", non_management_accounts())
@cats(standard_name=["LZA-G-SCP-14"], test_suite="scp", test_id="14", mutating=True, evidence=Evidence.BEHAVIORAL)
def test_scp_blocks_cloudformation_stack_modification(account_fixture_name: str, region: str, get_account_fixture: GetAccountFixture) -> None:
    """Verify SCP denies modification of LZA CloudFormation stacks."""
    # arrange - a stack under an LZA stage stem is inside both the core and deployment SCP scopes
    account = get_account_fixture(account_fixture_name)
    client = account.session.client("cloudformation", region_name=region, config=DEFAULT_RETRY_CONFIG)
    stage_prefixes = lza_config().stage_resource_prefixes

    stacks = [
        stack
        for page in client.get_paginator("list_stacks").paginate(StackStatusFilter=["CREATE_COMPLETE", "UPDATE_COMPLETE"])
        for stack in page["StackSummaries"]
    ]
    protected = [s for s in stacks if s["StackName"].startswith(stage_prefixes)]
    assert protected, f"No CloudFormation stacks under {stage_prefixes} found in {account_fixture_name} {region}"

    # act & assert
    with pytest.raises(ClientError, match="explicit deny in a service control policy"):
        client.delete_stack(StackName=protected[0]["StackName"])


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@pytest.mark.parametrize("account_fixture_name", non_management_accounts())
@cats(standard_name=["LZA-G-SCP-15"], test_suite="scp", test_id="15", mutating=True, evidence=Evidence.BEHAVIORAL)
def test_scp_blocks_ssm_parameter_modification(account_fixture_name: str, region: str, get_account_fixture: GetAccountFixture) -> None:
    """Verify SCP denies modification of LZA SSM parameters."""
    # arrange - LZA writes <ssm prefix>/<prefix>-<Stack>-<account>-<region>/{stack-id,version} for every
    # stack in every account and region; that path sits inside both the core (<ssm prefix>*) and
    # deployment (<ssm prefix>/<prefix>-*) SCP scopes
    account = get_account_fixture(account_fixture_name)
    client = account.session.client("ssm", region_name=region, config=DEFAULT_RETRY_CONFIG)
    stack_parameter_prefix = f"{lza_config().ssm_parameter_prefix}/{lza_config().accelerator_prefix}-"

    params = client.describe_parameters(
        ParameterFilters=[{"Key": "Name", "Option": "BeginsWith", "Values": [stack_parameter_prefix]}],
        MaxResults=1,
    )["Parameters"]
    assert params, f"No {stack_parameter_prefix} SSM parameters found in {account_fixture_name} {region}"

    # act & assert
    with pytest.raises(ClientError, match="explicit deny in a service control policy"):
        client.delete_parameter(Name=params[0]["Name"])


@pytest.mark.parametrize("account_fixture_name", non_management_accounts())
@cats(standard_name=["LZA-G-SCP-16"], test_suite="scp", test_id="16", mutating=True, evidence=Evidence.BEHAVIORAL)
def test_scp_blocks_s3_bucket_policy_modification(account_fixture_name: str, get_account_fixture: GetAccountFixture) -> None:
    """Verify SCP denies modification of LZA S3 bucket settings."""
    # arrange
    account = get_account_fixture(account_fixture_name)
    client = account.session.client("s3", config=DEFAULT_RETRY_CONFIG)
    bucket_prefix = f"{lza_config().bucket_name_prefix}-"

    bucket_names = get_s3_buckets(account)
    protected = [name for name in bucket_names if name.startswith(bucket_prefix)]
    assert protected, f"No {bucket_prefix} S3 buckets found in {account_fixture_name}"

    # act & assert
    with pytest.raises(ClientError, match="explicit deny in a service control policy"):
        client.delete_bucket_policy(Bucket=protected[0])


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@pytest.mark.parametrize("account_fixture_name", non_management_accounts())
@cats(standard_name=["LZA-G-SCP-18"], test_suite="scp", test_id="18", mutating=True, evidence=Evidence.BEHAVIORAL)
def test_scp_blocks_eventbridge_modification(account_fixture_name: str, region: str, get_account_fixture: GetAccountFixture) -> None:
    """Verify SCP denies modification of LZA EventBridge rules."""
    # arrange
    account = get_account_fixture(account_fixture_name)
    client = account.session.client("events", region_name=region, config=DEFAULT_RETRY_CONFIG)
    accelerator_prefix = lza_config().accelerator_prefix

    rules = [rule for page in client.get_paginator("list_rules").paginate(NamePrefix=accelerator_prefix) for rule in page["Rules"]]
    assert rules, f"No {accelerator_prefix}-prefixed EventBridge rules found in {account_fixture_name} {region}"

    # act & assert
    with pytest.raises(ClientError, match="explicit deny in a service control policy"):
        client.delete_rule(Name=rules[0]["Name"])

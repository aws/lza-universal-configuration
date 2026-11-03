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
CATS - SCP Enforcement: Lambda, EBS, Control Tower

This test verifies:
- LZA-G-SCP-3: Restricts the modification of Lambda functions created by LZA
- LZA-G-SCP-5: Restricts the modification of EC2 EBS encryption settings
- LZA-G-SCP-6: Restricts the modification of Control Tower Config resources
"""

from __future__ import annotations

import logging

import pytest
from botocore.exceptions import ClientError
from cats import GetAccountFixture, cats, cats_requires

from cats_utils.accounts import core_ou_accounts, non_management_accounts
from cats_utils.boto import DEFAULT_RETRY_CONFIG
from cats_utils.evidence import Evidence
from cats_utils.requirement import Requirement
from lza_utils.lza_config import lza_config

logger = logging.getLogger(__name__)


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@pytest.mark.parametrize("account_fixture_name", non_management_accounts())
@cats(standard_name=["LZA-G-SCP-3"], test_suite="scp", test_id="3", mutating=True, evidence=Evidence.BEHAVIORAL)
def test_scp_blocks_lambda_modification(account_fixture_name: str, region: str, get_account_fixture: GetAccountFixture) -> None:
    """Verify SCP denies modification of LZA Lambda functions."""
    # arrange - a function under an LZA stage stem is inside both the core and deployment SCP scopes
    account = get_account_fixture(account_fixture_name)
    client = account.session.client("lambda", region_name=region, config=DEFAULT_RETRY_CONFIG)
    stage_prefixes = lza_config().stage_resource_prefixes

    functions = [function for page in client.get_paginator("list_functions").paginate() for function in page["Functions"]]
    protected = [f for f in functions if f["FunctionName"].startswith(stage_prefixes)]
    assert protected, f"No Lambda functions under {stage_prefixes} found in {account_fixture_name} {region}"

    # act & assert
    with pytest.raises(ClientError, match="explicit deny in a service control policy"):
        client.update_function_configuration(FunctionName=protected[0]["FunctionName"], Description="CATS SCP test")


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@pytest.mark.parametrize("account_fixture_name", non_management_accounts())
@cats(standard_name=["LZA-G-SCP-5"], test_suite="scp", test_id="5", mutating=True, evidence=Evidence.BEHAVIORAL)
def test_scp_blocks_ebs_encryption_disable(account_fixture_name: str, region: str, get_account_fixture: GetAccountFixture) -> None:
    """Verify SCP denies disabling EBS encryption by default."""
    # arrange
    account = get_account_fixture(account_fixture_name)
    client = account.session.client("ec2", region_name=region, config=DEFAULT_RETRY_CONFIG)

    # act & assert
    with pytest.raises(ClientError, match="explicit deny in a service control policy"):
        client.disable_ebs_encryption_by_default()


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@pytest.mark.parametrize("account_fixture_name", core_ou_accounts())
@cats_requires(Requirement.CONTROL_TOWER)
@cats(standard_name=["LZA-G-SCP-6"], test_suite="scp", test_id="6", mutating=True, evidence=Evidence.BEHAVIORAL)
def test_scp_blocks_controltower_config_modification(account_fixture_name: str, region: str, get_account_fixture: GetAccountFixture) -> None:
    """Verify Control Tower's SCP denies modification of its Config rules.

    The ``AWSControlTower*`` detective rules exist only in the core OU families; the container
    deployment's ``LzaDeployment`` OU is Control Tower governed but carries none of them. Requires
    ``control-tower``: the Organizations-only variant has no such rules in any account, and the SCP
    that protects them is Control Tower's own, so there is nothing to probe and the test is
    recorded ``not_run``.
    """
    # arrange
    account = get_account_fixture(account_fixture_name)
    client = account.session.client("config", region_name=region, config=DEFAULT_RETRY_CONFIG)

    rules = [rule for page in client.get_paginator("describe_config_rules").paginate() for rule in page["ConfigRules"]]
    ct_rules = [r for r in rules if r["ConfigRuleName"].startswith("AWSControlTower")]
    assert ct_rules, f"No AWSControlTower Config Rules found in {account_fixture_name} {region}"

    rule_name = ct_rules[0]["ConfigRuleName"]

    # act & assert
    with pytest.raises(ClientError, match="explicit deny in a service control policy"):
        client.delete_config_rule(ConfigRuleName=rule_name)

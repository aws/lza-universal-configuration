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
CATS - SCP Enforcement: Account Management and Network Firewall

This test verifies:
- LZA-G-SCP-28: Restricts the modification of Account Management settings
- LZA-G-SCP-31: Restricts the modification of LZA Network Firewall settings for Infrastructure accounts
"""

from __future__ import annotations

import logging

import pytest
from botocore.exceptions import ClientError
from cats import GetAccountFixture, cats

from cats_utils.accounts import non_management_accounts
from cats_utils.boto import ACCESS_DENIED_NOT_BY_IDENTITY_POLICY, DEFAULT_RETRY_CONFIG
from cats_utils.evidence import Evidence
from lza_utils.lza_config import lza_config

logger = logging.getLogger(__name__)


@pytest.mark.parametrize("account_fixture_name", non_management_accounts())
@cats(standard_name=["LZA-G-SCP-28"], test_suite="scp", test_id="28", mutating=True, evidence=Evidence.BEHAVIORAL)
def test_scp_blocks_account_region_modification(account_fixture_name: str, get_account_fixture: GetAccountFixture) -> None:
    """Verify SCP denies account:EnableRegion."""
    # arrange
    account = get_account_fixture(account_fixture_name)
    client = account.session.client("account", region_name=lza_config().home_region, config=DEFAULT_RETRY_CONFIG)

    # act & assert
    with pytest.raises(ClientError, match=ACCESS_DENIED_NOT_BY_IDENTITY_POLICY):
        client.enable_region(RegionName="ap-east-1")


@pytest.mark.parametrize("account_fixture_name", lza_config().account_fixture_names_in_ous(["Infrastructure"]))
@cats(standard_name=["LZA-G-SCP-31"], test_suite="scp", test_id="31", mutating=True, evidence=Evidence.BEHAVIORAL)
def test_scp_blocks_network_firewall_rule_group_creation(account_fixture_name: str, get_account_fixture: GetAccountFixture) -> None:
    """Verify SCP denies creating Network Firewall rule groups with accelerator prefix."""
    # arrange
    account = get_account_fixture(account_fixture_name)
    client = account.session.client("network-firewall", region_name=lza_config().home_region, config=DEFAULT_RETRY_CONFIG)
    test_rule_group_name = f"{lza_config().accelerator_prefix}-cats-scp-test"

    # act & assert
    with pytest.raises(ClientError, match=ACCESS_DENIED_NOT_BY_IDENTITY_POLICY):
        client.create_rule_group(
            RuleGroupName=test_rule_group_name,
            Type="STATELESS",
            Capacity=100,
            RuleGroup={
                "RulesSource": {"StatelessRulesAndCustomActions": {"StatelessRules": []}},
            },
        )

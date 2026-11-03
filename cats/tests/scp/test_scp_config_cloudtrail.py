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
CATS - SCP Enforcement: AWS Config and CloudTrail Protection

This test verifies:
- LZA-G-SCP-1: Restricts the modification of AWS Config Rules managed by LZA
- LZA-G-SCP-2: Restricts the modification of AWS CloudTrail resources
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


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@pytest.mark.parametrize("account_fixture_name", non_management_accounts())
@cats(standard_name=["LZA-G-SCP-1"], test_suite="scp", test_id="1", mutating=True, evidence=Evidence.BEHAVIORAL)
def test_scp_blocks_config_rule_modification(account_fixture_name: str, region: str, get_account_fixture: GetAccountFixture) -> None:
    """Verify SCP denies modification of LZA-managed Config Rules."""
    # arrange
    account = get_account_fixture(account_fixture_name)
    client = account.session.client("config", region_name=region, config=DEFAULT_RETRY_CONFIG)
    accelerator_prefix = lza_config().accelerator_prefix

    # act - find an accelerator-prefixed config rule
    rules = [rule for page in client.get_paginator("describe_config_rules").paginate() for rule in page["ConfigRules"]]
    protected_rules = [r for r in rules if r["ConfigRuleName"].startswith(accelerator_prefix)]
    assert protected_rules, f"No {accelerator_prefix}-prefixed Config Rules found in {account_fixture_name} {region}"

    rule_name = protected_rules[0]["ConfigRuleName"]

    # assert - attempt to delete the protected rule
    with pytest.raises(ClientError, match="explicit deny in a service control policy"):
        client.delete_config_rule(ConfigRuleName=rule_name)


@pytest.mark.parametrize("account_fixture_name", non_management_accounts())
@cats(standard_name=["LZA-G-SCP-2"], test_suite="scp", test_id="2", mutating=True, evidence=Evidence.BEHAVIORAL)
def test_member_account_cannot_modify_cloudtrail(account_fixture_name: str, get_account_fixture: GetAccountFixture) -> None:
    """Verify member accounts cannot modify the organization CloudTrail trail.

    Protection is via org trail ownership (not SCP) — member accounts get
    AccessDenied when attempting to modify the Management-owned trail.
    """
    # arrange
    account = get_account_fixture(account_fixture_name)
    client = account.session.client("cloudtrail", region_name=lza_config().home_region, config=DEFAULT_RETRY_CONFIG)

    all_trails = client.describe_trails()["trailList"]
    org_trails = [t for t in all_trails if t.get("IsOrganizationTrail") is True]
    assert org_trails, f"No organization CloudTrail trail visible in {account_fixture_name}"

    # act & assert
    with pytest.raises(ClientError, match=ACCESS_DENIED_NOT_BY_IDENTITY_POLICY):
        client.update_trail(Name=org_trails[0]["TrailARN"], IncludeGlobalServiceEvents=True)

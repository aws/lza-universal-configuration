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
CATS - SCP Enforcement: Organizations

This test verifies:
- LZA-G-SCP-17: Restricts modification when Quarantine SCP is applied
- LZA-G-SCP-35: Restricts the ability of accounts to leave the Organization
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

import pytest
from botocore.exceptions import ClientError
from cats import GetAccountFixture, cats

from cats_utils.accounts import non_management_accounts
from cats_utils.boto import ACCESS_DENIED_NOT_BY_IDENTITY_POLICY, DEFAULT_RETRY_CONFIG
from cats_utils.evidence import Evidence
from lza_utils.lza_config import lza_config

if TYPE_CHECKING:
    from cats_types import ManagementAccount

logger = logging.getLogger(__name__)


@cats(standard_name=["LZA-G-SCP-17"], test_suite="scp", test_id="17", mutating=False, evidence=Evidence.CONFIGURATION)
def test_quarantine_scp_exists(Management_account: ManagementAccount) -> None:
    """Verify the Quarantine SCP exists and denies all actions."""
    # arrange
    client = Management_account.session.client("organizations", region_name=lza_config().home_region, config=DEFAULT_RETRY_CONFIG)
    expected_name = f"{lza_config().accelerator_prefix}-Quarantine-New-Object"

    # act
    all_policies = {
        policy["Name"]: policy
        for page in client.get_paginator("list_policies").paginate(Filter="SERVICE_CONTROL_POLICY")
        for policy in page["Policies"]
    }

    # assert
    assert expected_name in all_policies, f"Quarantine SCP '{expected_name}' not found in organization"

    policy_detail = client.describe_policy(PolicyId=all_policies[expected_name]["Id"])
    content = json.loads(policy_detail["Policy"]["Content"])
    statements = content["Statement"]

    deny_all = any(s.get("Effect") == "Deny" and s.get("Action") == "*" for s in statements)
    assert deny_all is True, "Quarantine SCP does not contain a Deny * statement"


@cats(standard_name=["LZA-G-SCP-35"], test_suite="scp", test_id="35a", mutating=False, evidence=Evidence.CONFIGURATION)
def test_scp_leave_organization_deny_exists(Management_account: ManagementAccount) -> None:
    """Verify an SCP exists that denies organizations:LeaveOrganization."""
    # arrange
    client = Management_account.session.client("organizations", region_name=lza_config().home_region, config=DEFAULT_RETRY_CONFIG)

    # act
    all_policies = [policy for page in client.get_paginator("list_policies").paginate(Filter="SERVICE_CONTROL_POLICY") for policy in page["Policies"]]

    def _denies_leave_org(policy_content: str) -> bool:
        statements = json.loads(policy_content).get("Statement", [])
        return any(
            "leaveorganization" in action.lower()
            for stmt in statements
            if stmt.get("Effect") == "Deny"
            for action in (stmt.get("Action", []) if isinstance(stmt.get("Action"), list) else [stmt.get("Action", "")])
        )

    compliant_policies = [
        policy["Name"] for policy in all_policies if _denies_leave_org(client.describe_policy(PolicyId=policy["Id"])["Policy"]["Content"])
    ]

    # assert
    assert compliant_policies, "No SCP found with a Deny statement for organizations:LeaveOrganization"


@pytest.mark.parametrize("account_fixture_name", non_management_accounts())
@cats(standard_name=["LZA-G-SCP-35"], test_suite="scp", test_id="35b", mutating=True, evidence=Evidence.BEHAVIORAL)
def test_scp_blocks_leave_organization(account_fixture_name: str, get_account_fixture: GetAccountFixture) -> None:
    """Verify SCP denies organizations:LeaveOrganization."""
    # arrange
    account = get_account_fixture(account_fixture_name)
    client = account.session.client("organizations", region_name=lza_config().home_region, config=DEFAULT_RETRY_CONFIG)

    # act & assert - Organizations API returns AccessDeniedException (not the typical
    # "explicit deny in a service control policy" message) when SCP blocks with conditions
    with pytest.raises(ClientError, match=ACCESS_DENIED_NOT_BY_IDENTITY_POLICY):
        client.leave_organization()

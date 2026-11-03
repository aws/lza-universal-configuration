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
CATS - AWS Organizations and Account Placement

This test verifies:
- LZA-G-OM-1: AWS Organizations enabled with ALL features
- LZA-G-OM-2: Security OU exists
- LZA-G-OM-3: Infrastructure OU exists
- LZA-G-OM-4: All OUs from config exist in the organization
- LZA-G-OM-5: Quarantine SCP exists and denies all actions
- LZA-G-ACT-1: Management account is in Root
- LZA-G-ACT-2: LogArchive account is in Security OU
- LZA-G-ACT-3: Audit account is in Security OU
- LZA-G-ACT-4: Network account is in Infrastructure OU
- LZA-G-ACT-5: SharedServices account is in Infrastructure OU
- LZA-G-ACT-6: Perimeter account is in Infrastructure OU
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from cats import cats

from cats_utils.boto import DEFAULT_RETRY_CONFIG
from cats_utils.cats_cache import (
    get_account_ids_in_parent,
    get_organization,
    get_organization_accounts,
    get_organization_ous,
    get_organization_root_id,
    get_organization_scps,
)
from cats_utils.evidence import Evidence
from lza_utils.lza_config import lza_config

if TYPE_CHECKING:
    from cats_types import ManagementAccount

logger = logging.getLogger(__name__)


@cats(standard_name=["LZA-G-OM-1"], test_suite="organizations", test_id="1", evidence=Evidence.CONFIGURATION)
def test_organizations_enabled_all_features(Management_account: ManagementAccount) -> None:
    """Verify AWS Organizations is enabled with ALL features."""
    # arrange / act
    org = get_organization(Management_account)

    # assert
    assert org["FeatureSet"] == "ALL", f"Organizations FeatureSet is '{org['FeatureSet']}', expected 'ALL'"


@cats(standard_name=["LZA-G-OM-2"], test_suite="organizations", test_id="2", evidence=Evidence.CONFIGURATION)
def test_security_ou_exists(Management_account: ManagementAccount) -> None:
    """Verify Security OU exists in the organization."""
    # act
    actual_ous = get_organization_ous(Management_account)

    # assert
    assert "Security" in actual_ous, f"Security OU not found. Existing OUs: {sorted(actual_ous.keys())}"


@cats(standard_name=["LZA-G-OM-3"], test_suite="organizations", test_id="3", evidence=Evidence.CONFIGURATION)
def test_infrastructure_ou_exists(Management_account: ManagementAccount) -> None:
    """Verify Infrastructure OU exists in the organization."""
    # act
    actual_ous = get_organization_ous(Management_account)

    # assert
    assert "Infrastructure" in actual_ous, f"Infrastructure OU not found. Existing OUs: {sorted(actual_ous.keys())}"


@cats(standard_name=["LZA-G-OM-4"], test_suite="organizations", test_id="4", evidence=Evidence.CONFIGURATION)
def test_all_configured_ous_exist(Management_account: ManagementAccount) -> None:
    """Verify all OUs defined in LZA config exist in the organization."""
    # arrange
    config = lza_config()
    expected_ous = {ou.name for ou in config.organization.organizational_units if not ou.ignore}

    # act
    actual_ous = get_organization_ous(Management_account)

    # assert
    missing_ous = expected_ous - set(actual_ous.keys())
    assert missing_ous == set(), f"OUs missing from organization: {sorted(missing_ous)}"


@cats(standard_name=["LZA-G-OM-5"], test_suite="organizations", test_id="5", evidence=Evidence.CONFIGURATION)
def test_quarantine_scp_denies_all(Management_account: ManagementAccount) -> None:
    """Verify the Quarantine SCP exists and denies all actions."""
    # arrange
    config = lza_config()
    quarantine_config = config.organization.quarantine_new_accounts
    assert quarantine_config is not None, "quarantineNewAccounts not configured in organization config"
    assert quarantine_config.enable is True, "quarantineNewAccounts is not enabled in organization config"
    assert quarantine_config.scp_policy_name is not None, "quarantineNewAccounts.scpPolicyName not set"
    expected_name = quarantine_config.scp_policy_name.replace("{{ AcceleratorPrefix }}", config.accelerator_prefix)

    # act
    all_scps = get_organization_scps(Management_account)

    # assert - policy exists
    assert expected_name in all_scps, f"Quarantine SCP '{expected_name}' not found. Existing SCPs: {sorted(all_scps.keys())}"

    # assert - policy denies all
    client = Management_account.session.client("organizations", region_name=config.home_region, config=DEFAULT_RETRY_CONFIG)
    policy_detail = client.describe_policy(PolicyId=all_scps[expected_name]["Id"])
    content = json.loads(policy_detail["Policy"]["Content"])
    statements = content["Statement"]
    deny_all = any(s.get("Effect") == "Deny" and s.get("Action") == "*" for s in statements)
    assert deny_all is True, f"Quarantine SCP '{expected_name}' does not contain a Deny * statement"


@cats(standard_name=["LZA-G-ACT-1"], test_suite="organizations", test_id="6", evidence=Evidence.CONFIGURATION)
def test_management_account_in_root(Management_account: ManagementAccount) -> None:
    """Verify the Management account is directly in the organization root."""
    # arrange
    org = get_organization(Management_account)
    management_account_id = org["MasterAccountId"]
    root_id = get_organization_root_id(Management_account)

    # act
    account_ids_in_root = get_account_ids_in_parent(Management_account, root_id)

    # assert
    assert management_account_id in account_ids_in_root, f"Management account {management_account_id} is not in the organization root"


@cats(standard_name=["LZA-G-ACT-2"], test_suite="organizations", test_id="7", evidence=Evidence.CONFIGURATION)
def test_logarchive_in_security_ou(Management_account: ManagementAccount) -> None:
    """Verify the LogArchive account is in the Security OU."""
    _assert_account_in_ou(Management_account, account_name="LogArchive", ou_name="Security")


@cats(standard_name=["LZA-G-ACT-3"], test_suite="organizations", test_id="8", evidence=Evidence.CONFIGURATION)
def test_audit_in_security_ou(Management_account: ManagementAccount) -> None:
    """Verify the Audit account is in the Security OU."""
    _assert_account_in_ou(Management_account, account_name="Audit", ou_name="Security")


@cats(standard_name=["LZA-G-ACT-4"], test_suite="organizations", test_id="9", evidence=Evidence.CONFIGURATION)
def test_network_in_infrastructure_ou(Management_account: ManagementAccount) -> None:
    """Verify the Network account is in the Infrastructure OU."""
    _assert_account_in_ou(Management_account, account_name="Network", ou_name="Infrastructure")


@cats(standard_name=["LZA-G-ACT-5"], test_suite="organizations", test_id="10", evidence=Evidence.CONFIGURATION)
def test_sharedservices_in_infrastructure_ou(Management_account: ManagementAccount) -> None:
    """Verify the SharedServices account is in the Infrastructure OU."""
    _assert_account_in_ou(Management_account, account_name="SharedServices", ou_name="Infrastructure")


@cats(standard_name=["LZA-G-ACT-6"], test_suite="organizations", test_id="11", evidence=Evidence.CONFIGURATION)
def test_perimeter_in_infrastructure_ou(Management_account: ManagementAccount) -> None:
    """Verify the Perimeter account is in the Infrastructure OU."""
    _assert_account_in_ou(Management_account, account_name="Perimeter", ou_name="Infrastructure")


def _assert_account_in_ou(management_account: ManagementAccount, account_name: str, ou_name: str) -> None:
    """Assert that a named account is in the specified OU."""
    # arrange
    all_accounts = get_organization_accounts(management_account)
    assert account_name in all_accounts, f"Account '{account_name}' not found in organization"
    account_id = all_accounts[account_name]

    ous = get_organization_ous(management_account)
    assert ou_name in ous, f"OU '{ou_name}' not found in organization"
    ou_id = ous[ou_name]

    # act
    account_ids_in_ou = get_account_ids_in_parent(management_account, ou_id)

    # assert
    assert account_id in account_ids_in_ou, f"Account '{account_name}' ({account_id}) is not in the '{ou_name}' OU"

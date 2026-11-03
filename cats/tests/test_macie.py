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
CATS - Macie Configuration Validation

This test verifies:
- LZA-SEC-MACIE-1: Macie enabled in all accounts/regions
- LZA-SEC-MACIE-2: Macie administration delegated to Audit account
- LZA-SEC-MACIE-3: Findings published to Security Hub
- LZA-SEC-MACIE-4: Publishing frequency is FIFTEEN_MINUTES
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pytest
from cats import GetAccountFixture, cats
from cats.constants import get_account_fixture_names

from cats_utils.boto import DEFAULT_RETRY_CONFIG
from cats_utils.cats_cache import get_macie_session
from cats_utils.evidence import Evidence
from lza_utils.lza_config import lza_config

if TYPE_CHECKING:
    from cats_types import AuditAccount

logger = logging.getLogger(__name__)


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@pytest.mark.parametrize("account_fixture_name", get_account_fixture_names())
@cats(standard_name=["LZA-SEC-MACIE-1"], test_suite="macie", test_id="1", evidence=Evidence.CONFIGURATION)
def test_macie_enabled(account_fixture_name: str, region: str, get_account_fixture: GetAccountFixture) -> None:
    """Verify Macie is enabled in all accounts and regions."""
    # act
    account = get_account_fixture(account_fixture_name)
    session = get_macie_session(account, region)

    # assert
    assert session["status"] == "ENABLED", f"Macie not enabled in {account_fixture_name} / {region} (status: {session['status']})"


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@cats(standard_name=["LZA-SEC-MACIE-2"], test_suite="macie", test_id="2a", evidence=Evidence.CONFIGURATION)
def test_macie_delegated_to_audit(region: str, Audit_account: AuditAccount) -> None:
    """Verify Macie administration is delegated to the Audit account."""
    # act
    client = Audit_account.session.client("macie2", region_name=region, config=DEFAULT_RETRY_CONFIG)
    members = [m for page in client.get_paginator("list_members").paginate() for m in page["members"]]

    # assert
    assert members, f"Audit account has no Macie members in {region} — delegation may not be configured"


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@cats(standard_name=["LZA-SEC-MACIE-2"], test_suite="macie", test_id="2b", evidence=Evidence.CONFIGURATION)
def test_macie_all_accounts_registered(region: str, Audit_account: AuditAccount, get_account_fixture: GetAccountFixture) -> None:
    """Verify all org accounts are registered as Macie members with the delegated administrator."""
    # arrange
    delegated_admin = lza_config().delegated_admin_account()
    expected_member_ids = {get_account_fixture(name).account_id for name in get_account_fixture_names() if name != delegated_admin}

    # act
    client = Audit_account.session.client("macie2", region_name=region, config=DEFAULT_RETRY_CONFIG)
    members = [m for page in client.get_paginator("list_members").paginate() for m in page["members"]]
    actual_member_ids = {m["accountId"] for m in members}

    # assert
    missing = expected_member_ids - actual_member_ids
    assert missing == set(), f"Accounts not registered as Macie members in {region}: {missing}"


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@pytest.mark.parametrize("account_fixture_name", get_account_fixture_names())
@cats(standard_name=["LZA-SEC-MACIE-3"], test_suite="macie", test_id="3", evidence=Evidence.CONFIGURATION)
def test_macie_findings_published_to_security_hub(account_fixture_name: str, region: str, get_account_fixture: GetAccountFixture) -> None:
    """Verify Macie findings are published to Security Hub."""
    # act
    account = get_account_fixture(account_fixture_name)
    client = account.session.client("macie2", region_name=region, config=DEFAULT_RETRY_CONFIG)
    config = client.get_findings_publication_configuration()
    publish_policy = config["securityHubConfiguration"]["publishPolicyFindings"]

    # assert
    assert publish_policy is True, f"Macie policy findings not published to Security Hub in {account_fixture_name} / {region}"


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@pytest.mark.parametrize("account_fixture_name", get_account_fixture_names())
@cats(standard_name=["LZA-SEC-MACIE-4"], test_suite="macie", test_id="4", evidence=Evidence.CONFIGURATION)
def test_macie_publishing_frequency(account_fixture_name: str, region: str, get_account_fixture: GetAccountFixture) -> None:
    """Verify Macie publishing frequency is FIFTEEN_MINUTES."""
    # arrange
    config = lza_config()
    macie_config = config.security.central_security_services.macie
    assert macie_config is not None, "centralSecurityServices.macie is not declared in security-config.yaml"
    expected = macie_config.policy_findings_publishing_frequency
    assert expected is not None, "policyFindingsPublishingFrequency not set in LZA config"

    # act
    account = get_account_fixture(account_fixture_name)
    session = get_macie_session(account, region)
    actual = session["findingPublishingFrequency"]

    # assert
    assert actual == expected.value, f"Macie publishing frequency in {account_fixture_name} / {region}: '{actual}', expected '{expected.value}'"

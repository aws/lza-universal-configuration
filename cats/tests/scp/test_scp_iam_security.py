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
CATS - SCP Enforcement: IAM and Security Service Protection

This test verifies:
- LZA-G-SCP-9: Restricts the modification of IAM account and user settings
- LZA-G-SCP-10: Restricts the modification of LZA IAM resources
- LZA-G-SCP-11: Restricts the modification of GuardDuty settings
- LZA-G-SCP-12: Restricts the modification of Security Hub settings
- LZA-G-SCP-13: Restricts the modification of Macie settings
- LZA-G-SCP-26: Restricts the modification of IAM Access Analyzer settings
- LZA-G-SCP-36: Restricts the modification of IAM roles tagged with Accelerator prefix
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pytest
from botocore.exceptions import ClientError
from cats import GetAccountFixture, cats

from cats_utils.accounts import non_management_accounts
from cats_utils.boto import DEFAULT_RETRY_CONFIG
from cats_utils.cats_cache import get_guardduty_detector_id
from cats_utils.evidence import Evidence
from lza_utils.lza_config import lza_config

if TYPE_CHECKING:
    from cats_types import AuditAccount

logger = logging.getLogger(__name__)


@pytest.mark.parametrize("account_fixture_name", non_management_accounts())
@cats(standard_name=["LZA-G-SCP-9"], test_suite="scp", test_id="9", mutating=True, evidence=Evidence.BEHAVIORAL)
def test_scp_blocks_account_password_policy_modification(account_fixture_name: str, get_account_fixture: GetAccountFixture) -> None:
    """Verify SCP denies modification of account password policy."""
    # arrange
    account = get_account_fixture(account_fixture_name)
    client = account.session.client("iam", config=DEFAULT_RETRY_CONFIG)

    # act & assert
    with pytest.raises(ClientError, match="explicit deny in a service control policy"):
        client.update_account_password_policy(MinimumPasswordLength=14)


@pytest.mark.parametrize("account_fixture_name", non_management_accounts())
@cats(standard_name=["LZA-G-SCP-10"], test_suite="scp", test_id="10", mutating=True, evidence=Evidence.BEHAVIORAL)
def test_scp_blocks_lza_iam_role_modification(account_fixture_name: str, get_account_fixture: GetAccountFixture) -> None:
    """Verify SCP denies modification of LZA IAM roles."""
    # arrange - the role need not exist: the deny evaluates on the request ARN. Naming it under
    # an LZA stage stem puts it inside both the core and deployment SCP scopes.
    account = get_account_fixture(account_fixture_name)
    client = account.session.client("iam", config=DEFAULT_RETRY_CONFIG)
    role_name = f"{lza_config().stage_resource_prefixes[0]}-CATS-SCP-Test-Role"

    # act & assert - attempt to delete an accelerator role
    with pytest.raises(ClientError, match="explicit deny in a service control policy"):
        client.delete_role(RoleName=role_name)


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@pytest.mark.parametrize("account_fixture_name", non_management_accounts())
@cats(standard_name=["LZA-G-SCP-11"], test_suite="scp", test_id="11", mutating=True, evidence=Evidence.BEHAVIORAL)
def test_scp_blocks_guardduty_modification(account_fixture_name: str, region: str, get_account_fixture: GetAccountFixture) -> None:
    """Verify SCP denies modification of GuardDuty detectors."""
    # arrange
    account = get_account_fixture(account_fixture_name)
    client = account.session.client("guardduty", region_name=region, config=DEFAULT_RETRY_CONFIG)

    detector_id = get_guardduty_detector_id(account, region)

    # act & assert
    with pytest.raises(ClientError, match="explicit deny in a service control policy"):
        client.update_detector(DetectorId=detector_id, Enable=True, FindingPublishingFrequency="SIX_HOURS")


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@pytest.mark.parametrize("account_fixture_name", non_management_accounts())
@cats(standard_name=["LZA-G-SCP-12"], test_suite="scp", test_id="12", mutating=True, evidence=Evidence.BEHAVIORAL)
def test_scp_blocks_securityhub_modification(account_fixture_name: str, region: str, get_account_fixture: GetAccountFixture) -> None:
    """Verify SCP denies disabling Security Hub."""
    # arrange
    account = get_account_fixture(account_fixture_name)
    client = account.session.client("securityhub", region_name=region, config=DEFAULT_RETRY_CONFIG)

    # act & assert
    with pytest.raises(ClientError, match="explicit deny in a service control policy"):
        client.disable_security_hub()


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@pytest.mark.parametrize("account_fixture_name", non_management_accounts())
@cats(standard_name=["LZA-G-SCP-13"], test_suite="scp", test_id="13", mutating=True, evidence=Evidence.BEHAVIORAL)
def test_scp_blocks_macie_modification(account_fixture_name: str, region: str, get_account_fixture: GetAccountFixture) -> None:
    """Verify SCP denies disabling Macie."""
    # arrange
    account = get_account_fixture(account_fixture_name)
    client = account.session.client("macie2", region_name=region, config=DEFAULT_RETRY_CONFIG)

    # act & assert
    with pytest.raises(ClientError, match="explicit deny in a service control policy"):
        client.disable_macie()


@pytest.mark.parametrize("account_fixture_name", non_management_accounts())
@cats(standard_name=["LZA-G-SCP-36"], test_suite="scp", test_id="36", mutating=True, evidence=Evidence.BEHAVIORAL)
def test_scp_blocks_accelerator_tagged_role_modification(account_fixture_name: str, get_account_fixture: GetAccountFixture) -> None:
    """Verify SCP denies modification of IAM roles tagged with Accelerator prefix."""
    # arrange
    account = get_account_fixture(account_fixture_name)
    client = account.session.client("iam", config=DEFAULT_RETRY_CONFIG)
    accelerator_prefix = lza_config().accelerator_prefix

    # act & assert - attempt to untag an accelerator-prefixed role
    with pytest.raises(ClientError, match="explicit deny in a service control policy"):
        client.untag_role(RoleName=f"{accelerator_prefix}-Backup-Role", TagKeys=["Accelerator"])


@cats(standard_name=["LZA-G-SCP-26"], test_suite="scp", test_id="26", mutating=True, evidence=Evidence.BEHAVIORAL)
def test_scp_blocks_access_analyzer_deletion(Audit_account: AuditAccount) -> None:
    """Verify SCP denies deletion of IAM Access Analyzer."""
    # arrange
    client = Audit_account.session.client("accessanalyzer", region_name=lza_config().home_region, config=DEFAULT_RETRY_CONFIG)

    # act - find an existing analyzer
    analyzers = [analyzer for page in client.get_paginator("list_analyzers").paginate(type="ORGANIZATION") for analyzer in page["analyzers"]]
    assert analyzers, "No organization Access Analyzers found in Audit account"

    # assert - attempt to delete the analyzer
    with pytest.raises(ClientError, match="explicit deny in a service control policy"):
        client.delete_analyzer(analyzerName=analyzers[0]["name"])

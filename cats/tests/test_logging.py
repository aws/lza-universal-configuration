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
CATS - Logging Configuration Validation

This test verifies:
- LZA-LOG-1: Central logging bucket exists in LogArchive account
- LZA-LOG-2: ELB access logs buckets exist per region in LogArchive
- LZA-LOG-3: S3 access logs buckets exist per region in LogArchive
- LZA-LOG-4: Central log bucket lifecycle matches LZA config
- LZA-LOG-5: Organization-level CloudTrail exists and is active
- LZA-LOG-6: Backup vaults deployed to target accounts
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pytest
from cats import GetAccountFixture, cats

from cats_utils.boto import DEFAULT_RETRY_CONFIG
from cats_utils.cats_cache import (
    get_backup_vault_names,
    get_cloudtrail_trails,
    get_s3_buckets,
    get_s3_lifecycle_rules,
)
from cats_utils.evidence import Evidence
from lza_utils.lza_config import lza_config

if TYPE_CHECKING:
    from cats_types import LogArchiveAccount, ManagementAccount

logger = logging.getLogger(__name__)


def _elb_access_logs_bucket_name(account_id: str, region: str) -> str:
    return lza_config().elb_access_logs_bucket_name(account_id, region)


def _s3_access_logs_bucket_name(account_id: str, region: str) -> str:
    return f"{lza_config().resource_prefix}-s3-access-logs-{account_id}-{region}"


@cats(standard_name=["LZA-LOG-1"], test_suite="logging", test_id="1", evidence=Evidence.CONFIGURATION)
def test_central_logging_bucket_exists(LogArchive_account: LogArchiveAccount) -> None:
    """Verify the central logging bucket exists in the LogArchive account."""
    # arrange
    expected = lza_config().central_logs_bucket_name(LogArchive_account.account_id)

    # act
    buckets = get_s3_buckets(LogArchive_account)

    # assert
    assert expected in buckets, f"Central logging bucket '{expected}' not found. Available: {sorted(buckets)}"


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@cats(standard_name=["LZA-LOG-2"], test_suite="logging", test_id="2", evidence=Evidence.CONFIGURATION)
def test_elb_access_logs_bucket_exists(region: str, LogArchive_account: LogArchiveAccount) -> None:
    """Verify ELB access logs bucket exists for each enabled region."""
    # arrange
    expected = _elb_access_logs_bucket_name(LogArchive_account.account_id, region)

    # act
    buckets = get_s3_buckets(LogArchive_account)

    # assert
    assert expected in buckets, f"ELB access logs bucket '{expected}' not found in LogArchive"


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@cats(standard_name=["LZA-LOG-3"], test_suite="logging", test_id="3", evidence=Evidence.CONFIGURATION)
def test_s3_access_logs_bucket_exists(region: str, LogArchive_account: LogArchiveAccount) -> None:
    """Verify S3 access logs bucket exists for each enabled region."""
    # arrange
    expected = _s3_access_logs_bucket_name(LogArchive_account.account_id, region)

    # act
    buckets = get_s3_buckets(LogArchive_account)

    # assert
    assert expected in buckets, f"S3 access logs bucket '{expected}' not found in LogArchive"


@cats(standard_name=["LZA-LOG-4"], test_suite="logging", test_id="4", evidence=Evidence.CONFIGURATION)
def test_central_log_bucket_lifecycle(LogArchive_account: LogArchiveAccount) -> None:
    """Verify central log bucket lifecycle rules match LZA configuration."""
    # arrange
    config = lza_config()
    bucket_name = lza_config().central_logs_bucket_name(LogArchive_account.account_id)
    central_log_bucket_config = config.global_.logging.central_log_bucket
    assert central_log_bucket_config is not None, "centralLogBucket not configured in global config"
    expected_lifecycle = central_log_bucket_config.lifecycle_rules
    assert expected_lifecycle, "No lifecycle rules configured for central log bucket"

    # act
    actual_rules = get_s3_lifecycle_rules(LogArchive_account, bucket_name)

    # assert
    mismatches: list[str] = []
    for expected_rule in expected_lifecycle:
        if not expected_rule.enabled:
            continue
        for transition in expected_rule.transitions or []:
            days = int(transition.transition_after)
            storage_class = transition.storage_class.value
            found = any(
                t.get("Days") == days and t.get("StorageClass") == storage_class
                for rule in actual_rules
                if rule.get("Status") == "Enabled"
                for t in rule.get("Transitions", [])
            )
            if not found:
                mismatches.append(f"Missing transition: {days} days -> {storage_class}")
        if expected_rule.expiration is not None:
            exp_days = int(expected_rule.expiration)
            found = any(rule["Expiration"]["Days"] == exp_days for rule in actual_rules if rule.get("Status") == "Enabled")
            if not found:
                mismatches.append(f"Missing expiration: {exp_days} days")

    assert mismatches == [], f"Lifecycle mismatches on '{bucket_name}': {mismatches}"

    # assert — independent minimum retention values per compliance standard
    actual_transition_days = [
        t["Days"] for rule in actual_rules if rule.get("Status") == "Enabled" for t in rule.get("Transitions", []) if "Days" in t
    ]
    actual_expiration_days = [
        rule["Expiration"]["Days"]
        for rule in actual_rules
        if rule.get("Status") == "Enabled" and "Expiration" in rule and "Days" in rule["Expiration"]
    ]

    assert any(d >= 365 for d in actual_transition_days), (
        f"Central log bucket '{bucket_name}' has no transition >= 365 days. Found: {actual_transition_days}"
    )
    assert any(d >= 1000 for d in actual_expiration_days), (
        f"Central log bucket '{bucket_name}' has no expiration >= 1000 days. Found: {actual_expiration_days}"
    )


@cats(standard_name=["LZA-LOG-5"], test_suite="logging", test_id="5", evidence=Evidence.CONFIGURATION)
def test_organization_cloudtrail_exists(Management_account: ManagementAccount) -> None:
    """Verify an organization-level CloudTrail exists and is actively logging."""
    # act
    config = lza_config()
    trails = get_cloudtrail_trails(Management_account)
    org_trails = [t for t in trails if t.get("IsOrganizationTrail") is True]

    # assert
    assert org_trails, f"No organization-level CloudTrail found. Trails: {[t.get('Name') for t in trails]}"

    client = Management_account.session.client("cloudtrail", region_name=config.home_region, config=DEFAULT_RETRY_CONFIG)
    status = client.get_trail_status(Name=org_trails[0]["Name"])
    assert status["IsLogging"] is True, f"Organization trail '{org_trails[0]['Name']}' is not actively logging"


def _get_backup_vault_params() -> list[tuple[str, str]]:
    """Get (account_fixture_name, vault_name) tuples for parameterization."""
    config = lza_config()
    if not config.global_.backup:
        return []
    params: list[tuple[str, str]] = []
    for vault in config.global_.backup.vaults:
        targets = vault.deployment_targets
        fixture_names = config.account_fixture_names_from_targets(targets.organizational_units or [], targets.accounts or [])
        for fixture_name in fixture_names:
            params.append((fixture_name, vault.name))
    return params


@pytest.mark.parametrize(("account_fixture_name", "vault_name"), _get_backup_vault_params())
@cats(standard_name=["LZA-LOG-6"], test_suite="logging", test_id="6", evidence=Evidence.CONFIGURATION)
def test_backup_vault_deployed(account_fixture_name: str, vault_name: str, get_account_fixture: GetAccountFixture) -> None:
    """Verify backup vaults are deployed to target accounts."""
    # act
    account = get_account_fixture(account_fixture_name)
    actual_vaults = get_backup_vault_names(account)

    # assert
    assert vault_name in actual_vaults, f"Backup vault '{vault_name}' not found in {account_fixture_name}. Available vaults: {actual_vaults}"

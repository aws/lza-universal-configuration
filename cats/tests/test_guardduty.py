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
CATS - GuardDuty Configuration Validation

This test verifies:
- LZA-SEC-GD-1: GuardDuty enabled in all accounts/regions
- LZA-SEC-GD-2: S3 protection enabled
- LZA-SEC-GD-3: EKS protection enabled
- LZA-SEC-GD-4: finding updates published at the configured frequency in every account, and
  the delegated administrator exporting the organization's findings to the central logs bucket

GuardDuty exports member accounts' findings through the administrator account's publishing
destination (GuardDuty User Guide, "Exporting generated GuardDuty findings to Amazon S3
buckets"). LZA 1.16 also created a redundant per-account destination; LZA 1.17 creates only
the delegated administrator's. The export test therefore checks the delegated administrator,
which holds on both.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pytest
from cats import GetAccountFixture, cats
from cats.config import Settings
from cats.constants import get_account_fixture_names

from cats_utils.boto import DEFAULT_RETRY_CONFIG
from cats_utils.cats_cache import get_guardduty_detector, get_guardduty_detector_id
from cats_utils.evidence import Evidence
from lza_utils.lza_config import lza_config

if TYPE_CHECKING:
    from mypy_boto3_guardduty.client import GuardDutyClient
    from mypy_boto3_guardduty.type_defs import DestinationTypeDef

logger = logging.getLogger(__name__)


def _list_publishing_destinations(guardduty_client: GuardDutyClient, detector_id: str) -> list[DestinationTypeDef]:
    """All publishing destinations for a detector; GuardDuty has no paginator for this call."""
    destinations: list[DestinationTypeDef] = []
    next_token: str | None = None
    while True:
        response = (
            guardduty_client.list_publishing_destinations(DetectorId=detector_id, NextToken=next_token)
            if next_token
            else guardduty_client.list_publishing_destinations(DetectorId=detector_id)
        )
        destinations.extend(response["Destinations"])
        next_token = response.get("NextToken")
        if not next_token:
            return destinations


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@pytest.mark.parametrize("account_fixture_name", get_account_fixture_names())
@cats(standard_name=["LZA-SEC-GD-1"], test_suite="guardduty", test_id="1", evidence=Evidence.CONFIGURATION)
def test_guardduty_enabled(account_fixture_name: str, region: str, get_account_fixture: GetAccountFixture) -> None:
    """Verify GuardDuty is enabled in all accounts and regions."""
    # act
    account = get_account_fixture(account_fixture_name)
    detector = get_guardduty_detector(account, region)

    # assert
    assert detector["Status"] == "ENABLED", f"GuardDuty not enabled in {account_fixture_name} / {region} (status: {detector['Status']})"


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@pytest.mark.parametrize("account_fixture_name", get_account_fixture_names())
@cats(standard_name=["LZA-SEC-GD-2"], test_suite="guardduty", test_id="2", evidence=Evidence.CONFIGURATION)
def test_guardduty_s3_protection_enabled(account_fixture_name: str, region: str, get_account_fixture: GetAccountFixture) -> None:
    """Verify GuardDuty S3 protection is enabled."""
    # act
    account = get_account_fixture(account_fixture_name)
    detector = get_guardduty_detector(account, region)
    s3_status = detector["DataSources"]["S3Logs"]["Status"]

    # assert
    assert s3_status == "ENABLED", f"GuardDuty S3 protection not enabled in {account_fixture_name} / {region} (status: {s3_status})"


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@pytest.mark.parametrize("account_fixture_name", get_account_fixture_names())
@cats(standard_name=["LZA-SEC-GD-3"], test_suite="guardduty", test_id="3", evidence=Evidence.CONFIGURATION)
def test_guardduty_eks_protection_enabled(account_fixture_name: str, region: str, get_account_fixture: GetAccountFixture) -> None:
    """Verify GuardDuty EKS protection is enabled."""
    # act
    account = get_account_fixture(account_fixture_name)
    detector = get_guardduty_detector(account, region)
    eks_status = detector["DataSources"]["Kubernetes"]["AuditLogs"]["Status"]

    # assert
    assert eks_status == "ENABLED", f"GuardDuty EKS protection not enabled in {account_fixture_name} / {region} (status: {eks_status})"


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@pytest.mark.parametrize("account_fixture_name", get_account_fixture_names())
@cats(standard_name=["LZA-SEC-GD-4"], test_suite="guardduty", test_id="4", evidence=Evidence.CONFIGURATION)
def test_guardduty_findings_export_frequency(account_fixture_name: str, region: str, get_account_fixture: GetAccountFixture) -> None:
    """Verify every detector publishes finding updates at the configured frequency."""
    # arrange
    expected_frequency = lza_config().security.central_security_services.guardduty.export_configuration.export_frequency.value
    account = get_account_fixture(account_fixture_name)

    # act
    actual_frequency = get_guardduty_detector(account, region)["FindingPublishingFrequency"]

    # assert
    assert actual_frequency == expected_frequency, (
        f"GuardDuty publishing frequency in {account_fixture_name} / {region}: '{actual_frequency}', expected '{expected_frequency}'"
    )


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@cats(standard_name=["LZA-SEC-GD-4"], test_suite="guardduty", test_id="4b", evidence=Evidence.CONFIGURATION)
def test_guardduty_findings_exported_to_central_logs_bucket(region: str, get_account_fixture: GetAccountFixture) -> None:
    """Verify the delegated administrator exports the organization's findings to the central logs bucket.

    GuardDuty exports member accounts' findings through the administrator account's
    publishing destination, so the control is one destination on the delegated admin's
    detector per region, and it must be LZA's: the central logs bucket under the configured
    prefix, encrypted with the LogArchive account's key. Any other S3 destination (for
    example one added by account tooling) does not satisfy the control.
    """
    # arrange
    config = lza_config()
    delegated_admin = get_account_fixture(config._to_fixture_name(config.security.central_security_services.delegated_admin_account))
    log_archive = get_account_fixture(config._to_fixture_name(config.global_.logging.account))
    expected_destination_arn = config.guardduty_findings_destination_arn(log_archive.account_id)
    # The bucket's key lives with the bucket in the centralized logging region, whichever region the detector is in.
    central_logs_region = config.global_.logging.centralized_logging_region or config.home_region
    expected_kms_key_arn_prefix = f"arn:{Settings().cats_deployment_settings.partition}:kms:{central_logs_region}:{log_archive.account_id}:key/"
    guardduty_client = delegated_admin.session.client("guardduty", region_name=region, config=DEFAULT_RETRY_CONFIG)
    detector_id = get_guardduty_detector_id(delegated_admin, region)

    # act
    destinations = {
        destination["DestinationId"]: guardduty_client.describe_publishing_destination(
            DetectorId=detector_id, DestinationId=destination["DestinationId"]
        )
        for destination in _list_publishing_destinations(guardduty_client, detector_id)
    }
    actual = {
        destination_id: {
            "type": destination["DestinationType"],
            "status": destination["Status"],
            "arn": destination["DestinationProperties"].get("DestinationArn", "<DestinationArn not returned by API>"),
            "kms_key_owner": destination["DestinationProperties"].get("KmsKeyArn", "<KmsKeyArn not returned by API>").rsplit("/", 1)[0] + "/",
        }
        for destination_id, destination in destinations.items()
    }
    lza_destinations = {destination_id: d for destination_id, d in actual.items() if d["arn"] == expected_destination_arn}

    # assert
    assert len(lza_destinations) == 1, (
        f"Expected one GuardDuty S3 destination to {expected_destination_arn} on {delegated_admin.name} / {region}, found: {actual}"
    )
    (destination,) = lza_destinations.values()
    expected = {"type": "S3", "status": "PUBLISHING", "arn": expected_destination_arn, "kms_key_owner": expected_kms_key_arn_prefix}
    assert destination == expected

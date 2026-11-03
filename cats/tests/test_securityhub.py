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
CATS - Security Hub Configuration Validation

This test verifies:
- LZA-SEC-SecHub-1: Security Hub enabled in all accounts/regions
- LZA-SEC-SecHub-2: AWS Foundational Security Best Practices v1.0.0 subscribed and enabled
- LZA-SEC-SecHub-3: CIS AWS Foundations Benchmark v3.0.0 subscribed and enabled
- LZA-SEC-SecHub-4: NIST Special Publication 800-53 Revision 5 subscribed and enabled

Each standard test reads the standard by name from ``securityHub.standards`` in
``security-config.yaml`` and fails if the config does not enable it, resolves the exact
``StandardsArn`` through ``DescribeStandards`` (the same lookup LZA performs), and requires
the subscription in every account and region to prove the standard enabled:
``StandardsStatus`` ``READY``, or ``PENDING`` only while Security Hub is adding new controls to
a standard that is already enabled (no ``StandardsStatusReason``, controls
``READY_FOR_UPDATES``; see ``cats_utils.securityhub``). A first enablement that has not
finished, ``INCOMPLETE`` (some controls failed to enable; the reason names why), ``FAILED`` and
``DELETING`` all fail with every field the verdict used in the message.
"""

from __future__ import annotations

import logging

import pytest
from cats import GetAccountFixture, cats
from cats.constants import get_account_fixture_names

from cats_utils.boto import DEFAULT_RETRY_CONFIG
from cats_utils.cats_cache import get_securityhub_enabled_standards, get_securityhub_standards_catalog
from cats_utils.evidence import Evidence
from cats_utils.securityhub import describe_subscription_state, is_standard_enabled
from lza_utils.lza_config import lza_config

logger = logging.getLogger(__name__)

STANDARDS_NOT_IN_CONFIG = "<standard not in security-config.yaml>"


def assert_securityhub_standard_ready(account_fixture_name: str, region: str, get_account_fixture: GetAccountFixture, standard_name: str) -> None:
    """Assert ``security-config.yaml`` enables the standard and the account's subscription proves it enabled.

    Three assertions on purpose: "config does not enable it", "not subscribed" and
    "subscribed but not enabled" are different diagnoses. The last accepts ``READY`` and the
    control-rollout ``PENDING`` (``cats_utils.securityhub.is_standard_enabled``).
    """
    # arrange
    configured_standards = {standard.name: standard.enable for standard in lza_config().security.central_security_services.security_hub.standards}
    assert configured_standards.get(standard_name, STANDARDS_NOT_IN_CONFIG) is True, (
        f"security-config.yaml does not enable '{standard_name}': {configured_standards}"
    )
    account = get_account_fixture(account_fixture_name)
    expected_standard_arn = get_securityhub_standards_catalog(account, region)[standard_name]

    # act
    subscriptions_by_arn = {subscription["StandardsArn"]: subscription for subscription in get_securityhub_enabled_standards(account, region)}
    subscription = subscriptions_by_arn.get(expected_standard_arn)

    # assert
    assert subscription is not None, (
        f"'{standard_name}' not subscribed in {account_fixture_name} / {region}. Subscribed: {sorted(subscriptions_by_arn)}"
    )
    assert is_standard_enabled(subscription) is True, (
        f"'{standard_name}' in {account_fixture_name} / {region} is {describe_subscription_state(subscription)}, not enabled"
    )


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@pytest.mark.parametrize("account_fixture_name", get_account_fixture_names())
@cats(standard_name=["LZA-SEC-SecHub-1"], test_suite="securityhub", test_id="1", evidence=Evidence.CONFIGURATION)
def test_securityhub_enabled(account_fixture_name: str, region: str, get_account_fixture: GetAccountFixture) -> None:
    """Verify Security Hub is enabled in all accounts and regions."""
    # act
    account = get_account_fixture(account_fixture_name)
    client = account.session.client("securityhub", region_name=region, config=DEFAULT_RETRY_CONFIG)
    response = client.describe_hub()

    # assert
    assert response["HubArn"], f"Security Hub not enabled in {account_fixture_name} / {region}"


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@pytest.mark.parametrize("account_fixture_name", get_account_fixture_names())
@cats(standard_name=["LZA-SEC-SecHub-3"], test_suite="securityhub", test_id="3", evidence=Evidence.CONFIGURATION)
def test_cis_v3_standard_ready(account_fixture_name: str, region: str, get_account_fixture: GetAccountFixture) -> None:
    """Verify the CIS AWS Foundations Benchmark v3.0.0 subscription proves the standard enabled."""
    assert_securityhub_standard_ready(account_fixture_name, region, get_account_fixture, "CIS AWS Foundations Benchmark v3.0.0")


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@pytest.mark.parametrize("account_fixture_name", get_account_fixture_names())
@cats(standard_name=["LZA-SEC-SecHub-2"], test_suite="securityhub", test_id="2", evidence=Evidence.CONFIGURATION)
def test_fsbp_standard_ready(account_fixture_name: str, region: str, get_account_fixture: GetAccountFixture) -> None:
    """Verify the AWS Foundational Security Best Practices v1.0.0 subscription proves the standard enabled."""
    assert_securityhub_standard_ready(account_fixture_name, region, get_account_fixture, "AWS Foundational Security Best Practices v1.0.0")


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@pytest.mark.parametrize("account_fixture_name", get_account_fixture_names())
@cats(standard_name=["LZA-SEC-SecHub-4"], test_suite="securityhub", test_id="4", evidence=Evidence.CONFIGURATION)
def test_nist_800_53_standard_ready(account_fixture_name: str, region: str, get_account_fixture: GetAccountFixture) -> None:
    """Verify the NIST Special Publication 800-53 Revision 5 subscription proves the standard enabled."""
    assert_securityhub_standard_ready(account_fixture_name, region, get_account_fixture, "NIST Special Publication 800-53 Revision 5")

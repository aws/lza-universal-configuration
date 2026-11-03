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
CATS - AWS Data Protection Policy Enforcements

This test verifies:
- LZA-SEC-DPPE-1: Configures EBS default volume encryption for the new EBS volumes and snapshots created in the environment
"""

from __future__ import annotations

import logging

import pytest
from cats import GetAccountFixture, cats
from cats.constants import get_account_fixture_names

from cats_utils.boto import DEFAULT_RETRY_CONFIG
from cats_utils.evidence import Evidence
from lza_utils.lza_config import lza_config

# Set Logging (conftest.py handles configuration)
logger = logging.getLogger(__name__)


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@pytest.mark.parametrize("account_fixture_name", get_account_fixture_names())
@cats(standard_name=["LZA-SEC-DPPE-1"], test_suite="ebs", test_id="2", evidence=Evidence.CONFIGURATION)
def test_ebs_encryption_by_default(account_fixture_name: str, region: str, get_account_fixture: GetAccountFixture) -> None:
    """Verify that EBS encryption by default is enabled for all accounts in all regions."""
    # Arrange
    account = get_account_fixture(account_fixture_name)
    client = account.role.default.client("ec2", region_name=region, config=DEFAULT_RETRY_CONFIG)

    # Act
    response = client.get_ebs_encryption_by_default()

    # Assert
    encryption_enabled = response["EbsEncryptionByDefault"]
    assert encryption_enabled is True, f"EBS encryption by default is not enabled in account {account_fixture_name} region {region}"

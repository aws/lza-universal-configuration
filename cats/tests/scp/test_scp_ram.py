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
CATS - SCP Enforcement: Resource Access Manager Protection

This test verifies:
- LZA-G-SCP-25: Restricts the modification of Resource Access Manager resources

The probe needs a RAM resource share the account owns. LZA creates one wherever
network-config.yaml gives a Transit Gateway ``shareTargets``, so the test runs in each of those
accounts and regions (the Network account in every enabled region on the Universal
Configuration) rather than in an account named in the test.
"""

from __future__ import annotations

import logging

import pytest
from botocore.exceptions import ClientError
from cats import GetAccountFixture, cats

from cats_utils.boto import DEFAULT_RETRY_CONFIG
from cats_utils.evidence import Evidence
from lza_utils.lza_config import get_shared_transit_gateway_account_region_combinations

logger = logging.getLogger(__name__)


@pytest.mark.parametrize(("account_fixture_name", "region"), get_shared_transit_gateway_account_region_combinations())
@cats(standard_name=["LZA-G-SCP-25"], test_suite="scp", test_id="25", mutating=True, evidence=Evidence.BEHAVIORAL)
def test_scp_blocks_ram_resource_share_modification(account_fixture_name: str, region: str, get_account_fixture: GetAccountFixture) -> None:
    """Verify SCP denies modification of RAM resource shares."""
    # arrange
    account = get_account_fixture(account_fixture_name)
    client = account.session.client("ram", region_name=region, config=DEFAULT_RETRY_CONFIG)

    # act - find existing resource shares
    resource_shares = [
        share for page in client.get_paginator("get_resource_shares").paginate(resourceOwner="SELF") for share in page["resourceShares"]
    ]
    assert resource_shares, f"No RAM resource shares found in {account_fixture_name} {region}"

    share = resource_shares[0]

    # assert - attempt to update the resource share
    with pytest.raises(ClientError, match="explicit deny in a service control policy"):
        client.update_resource_share(
            resourceShareArn=share["resourceShareArn"],
            name=f"{share['name']}-cats-scp-test",
            allowExternalPrincipals=share["allowExternalPrincipals"],
        )

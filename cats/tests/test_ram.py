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
CATS - Resource Access Manager (RAM) Sharing Validation

This test verifies:
- LZA-RAM-1: Transit Gateway is shared via RAM to configured OUs
- LZA-RAM-2: IPAM pools are shared via RAM to configured accounts/OUs
"""

from __future__ import annotations

import logging

import pytest
from cats import AccountUnderTest, GetAccountFixture, cats

from cats_utils.boto import DEFAULT_RETRY_CONFIG
from cats_utils.evidence import Evidence
from lza_utils.lza_config import (
    get_ipam_pools_with_share_targets,
    get_transit_gateway_account_region_combinations,
    get_transit_gateway_configs,
    lza_config,
)

logger = logging.getLogger(__name__)


def _get_tgw_share_target_fixtures() -> list[str]:
    """Get fixture names for accounts that should receive TGW shares (excludes the owner account)."""
    config = lza_config()
    owner_fixtures: set[str] = set()
    targets: set[str] = set()
    for tgw in config.network.transit_gateways:
        owner_fixtures.add(config._to_fixture_name(tgw.account))
        if tgw.share_targets:
            fixtures = config.account_fixture_names_from_targets(
                tgw.share_targets.organizational_units or [],
                tgw.share_targets.accounts or [],
            )
            targets.update(fixtures)
    return sorted(targets - owner_fixtures)


def _get_ipam_share_target_fixtures() -> list[str]:
    """Get fixture names for accounts that should receive IPAM pool shares (excludes the owner account)."""
    config = lza_config()
    pools = get_ipam_pools_with_share_targets()
    owner_fixtures: set[str] = set()
    central = config.network.central_network_services
    if central:
        owner_fixtures.add(config._to_fixture_name(central.delegated_admin_account))
    targets: set[str] = set()
    for pool in pools:
        targets.update(pool["fixture_names"])
    return sorted(targets - owner_fixtures)


@pytest.mark.parametrize(
    ("account_fixture_name", "region"),
    get_transit_gateway_account_region_combinations(),
)
@cats(standard_name=["LZA-RAM-1"], test_suite="ram", test_id="1", evidence=Evidence.CONFIGURATION)
def test_transit_gateway_shared_via_ram(
    account_fixture_name: str,
    region: str,
    get_account_fixture: GetAccountFixture,
) -> None:
    """Verify Transit Gateway is shared via RAM resource shares."""
    # arrange
    account = get_account_fixture(account_fixture_name)
    ram_client = account.session.client("ram", region_name=region, config=DEFAULT_RETRY_CONFIG)

    # act
    shares = [share for page in ram_client.get_paginator("get_resource_shares").paginate(resourceOwner="SELF") for share in page["resourceShares"]]
    tgw_share_arns = {
        resource["resourceShareArn"]
        for page in ram_client.get_paginator("list_resources").paginate(resourceOwner="SELF", resourceType="ec2:TransitGateway")
        for resource in page["resources"]
    }
    tgw_shares = [share for share in shares if share["resourceShareArn"] in tgw_share_arns]

    # assert
    assert tgw_shares, f"No RAM resource shares containing a Transit Gateway in {account_fixture_name} / {region}"

    tgw_configs = get_transit_gateway_configs()
    for tgw_config in tgw_configs:
        assert tgw_config.share_targets, f"TGW '{tgw_config.name}' has no shareTargets in config"

    # assert — shares have principals (OUs/accounts) configured
    principals_by_share_arn: dict[str, list[str]] = {share["resourceShareArn"]: [] for share in tgw_shares}
    for page in ram_client.get_paginator("list_principals").paginate(resourceOwner="SELF", resourceShareArns=sorted(principals_by_share_arn)):
        for principal in page["principals"]:
            principals_by_share_arn[principal["resourceShareArn"]].append(principal["id"])

    shares_missing_principals = [share["name"] for share in tgw_shares if not principals_by_share_arn[share["resourceShareArn"]]]
    assert shares_missing_principals == [], f"RAM shares have no principals — share targets not applied: {shares_missing_principals}"


@cats(standard_name=["LZA-RAM-2"], test_suite="ram", test_id="2", evidence=Evidence.CONFIGURATION)
def test_ipam_pools_shared_via_ram(
    Network_account: AccountUnderTest,
) -> None:
    """Verify IPAM pools with shareTargets are shared via RAM.

    IPAM RAM shares are created in the home region by the delegated admin account,
    not per TGW region. The receiver-side is covered by test_ipam_pool_resource_access.
    """
    # arrange
    config = lza_config()
    pools_with_targets = get_ipam_pools_with_share_targets()
    assert pools_with_targets, "No IPAM pools with shareTargets configured — LZA-RAM-2 requires IPAM sharing"

    central = config.network.central_network_services
    assert central, "No centralNetworkServices in network config — LZA-RAM-2 requires IPAM sharing"
    owner_fixture = config._to_fixture_name(central.delegated_admin_account)
    region = config.home_region

    # Sharing a pool with its own owner account associates no RAM principal, so
    # only pools with at least one non-owner target are expected to have principals.
    # If every pool targets only the owner account, this set is empty and the
    # principal check below verifies nothing — share existence is still asserted.
    pools_with_external_targets = {
        pool["pool_name"] for pool in pools_with_targets if any(fixture_name != owner_fixture for fixture_name in pool["fixture_names"])
    }
    # LZA names IPAM pool RAM shares "{pool_name}_IpamPoolShare"
    expected_shares_with_principals = {f"{pool_name}_IpamPoolShare" for pool_name in pools_with_external_targets}

    ram_client = Network_account.session.client("ram", region_name=region, config=DEFAULT_RETRY_CONFIG)

    # act
    shares = [share for page in ram_client.get_paginator("get_resource_shares").paginate(resourceOwner="SELF") for share in page["resourceShares"]]
    ipam_share_arns = {
        resource["resourceShareArn"]
        for page in ram_client.get_paginator("list_resources").paginate(resourceOwner="SELF", resourceType="ec2:IpamPool")
        for resource in page["resources"]
    }
    ipam_shares = [share for share in shares if share["resourceShareArn"] in ipam_share_arns]

    # assert
    assert ipam_shares, f"No RAM resource shares containing IPAM pools in {owner_fixture} / {region}"

    # assert — shares for pools with non-owner targets have principals configured
    principals_by_share_arn: dict[str, list[str]] = {share["resourceShareArn"]: [] for share in ipam_shares}
    for page in ram_client.get_paginator("list_principals").paginate(resourceOwner="SELF", resourceShareArns=sorted(principals_by_share_arn)):
        for principal in page["principals"]:
            principals_by_share_arn[principal["resourceShareArn"]].append(principal["id"])

    missing_principals = [
        share["name"]
        for share in ipam_shares
        if share["name"] in expected_shares_with_principals and not principals_by_share_arn[share["resourceShareArn"]]
    ]
    assert missing_principals == [], f"RAM shares with configured non-owner targets have no principals: {missing_principals}"


@pytest.mark.parametrize("account_fixture_name", _get_tgw_share_target_fixtures())
@cats(standard_name=["LZA-RAM-1"], test_suite="ram", test_id="1b", evidence=Evidence.CONFIGURATION)
def test_transit_gateway_resource_access(
    account_fixture_name: str,
    get_account_fixture: GetAccountFixture,
) -> None:
    """Verify target accounts can see Transit Gateway shared via RAM."""
    # arrange
    account = get_account_fixture(account_fixture_name)
    home_region = lza_config().home_region
    ram_client = account.session.client("ram", region_name=home_region, config=DEFAULT_RETRY_CONFIG)

    # act - look for resource shares shared WITH this account
    shares = [
        share for page in ram_client.get_paginator("get_resource_shares").paginate(resourceOwner="OTHER-ACCOUNTS") for share in page["resourceShares"]
    ]
    tgw_shares = [s["name"] for s in shares if "transit" in s["name"].lower() or "tgw" in s["name"].lower()]

    # assert
    assert tgw_shares, f"No Transit Gateway RAM shares visible to {account_fixture_name} — expected share access based on config shareTargets"


@pytest.mark.parametrize("account_fixture_name", _get_ipam_share_target_fixtures())
@cats(standard_name=["LZA-RAM-2"], test_suite="ram", test_id="2b", evidence=Evidence.CONFIGURATION)
def test_ipam_pool_resource_access(
    account_fixture_name: str,
    get_account_fixture: GetAccountFixture,
) -> None:
    """Verify target accounts can see IPAM pools shared via RAM."""
    # arrange
    account = get_account_fixture(account_fixture_name)
    home_region = lza_config().home_region
    ram_client = account.session.client("ram", region_name=home_region, config=DEFAULT_RETRY_CONFIG)

    # act - look for resource shares shared WITH this account
    shares = [
        share for page in ram_client.get_paginator("get_resource_shares").paginate(resourceOwner="OTHER-ACCOUNTS") for share in page["resourceShares"]
    ]
    ipam_shares = [s["name"] for s in shares if "ipam" in s["name"].lower()]

    # assert
    assert ipam_shares, f"No IPAM pool RAM shares visible to {account_fixture_name} — expected share access based on config shareTargets"

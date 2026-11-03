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
CATS - Transit Gateway Validation

This test verifies:
- LZA-TGW-1: TGW exists with route tables and default association/propagation disabled
- LZA-TGW-2: TGW VPC attachments have appliance mode enabled where configured
- LZA-TGW-3: TGW route tables for traffic flow separation
- LZA-RAM-1: TGW resource sharing to OUs with autoAcceptSharingAttachments
"""

from __future__ import annotations

import logging

import pytest
from cats import GetAccountFixture, cats

from cats_utils.boto import DEFAULT_RETRY_CONFIG
from cats_utils.ec2 import (
    get_active_transit_gateways,
    get_name_tag,
    get_transit_gateway_route_tables_by_transit_gateway_id,
    get_transit_gateway_vpc_attachments,
)
from cats_utils.evidence import Evidence
from lza_utils.lza_config import (
    get_transit_gateway_account_region_combinations,
    get_transit_gateway_configs_for_region,
    lza_config,
)

logger = logging.getLogger(__name__)


@pytest.mark.parametrize(
    ("account_fixture_name", "region"),
    get_transit_gateway_account_region_combinations(),
)
@cats(standard_name=["LZA-TGW-1"], test_suite="transit_gateway", test_id="1", evidence=Evidence.CONFIGURATION)
def test_transit_gateway_exists_with_routing(
    account_fixture_name: str,
    region: str,
    get_account_fixture: GetAccountFixture,
) -> None:
    """Verify TGW exists with default association/propagation disabled and route tables present."""
    # arrange
    account = get_account_fixture(account_fixture_name)

    # act
    active_tgws = get_active_transit_gateways(account, region)
    route_tables_by_tgw_id = get_transit_gateway_route_tables_by_transit_gateway_id(account, region)

    # assert
    assert active_tgws, f"No active Transit Gateways in {account_fixture_name} / {region}"

    non_compliant: dict[str, list[str]] = {}
    for tgw in active_tgws:
        tgw_id = tgw["TransitGatewayId"]
        options = tgw["Options"]
        issues: list[str] = []

        if options["DefaultRouteTableAssociation"] != "disable":
            issues.append("defaultRouteTableAssociation not disabled")
        if options["DefaultRouteTablePropagation"] != "disable":
            issues.append("defaultRouteTablePropagation not disabled")
        if not route_tables_by_tgw_id.get(tgw_id):
            issues.append("no route tables found")

        if issues:
            non_compliant[tgw_id] = issues

    assert non_compliant == {}, f"TGW compliance issues: {non_compliant}"


@pytest.mark.parametrize(
    ("account_fixture_name", "region"),
    get_transit_gateway_account_region_combinations(),
)
@cats(standard_name=["LZA-TGW-2"], test_suite="transit_gateway", test_id="2", evidence=Evidence.CONFIGURATION)
def test_transit_gateway_appliance_mode(
    account_fixture_name: str,
    region: str,
    get_account_fixture: GetAccountFixture,
) -> None:
    """Verify TGW VPC attachments have appliance mode enabled where LZA config requires it."""
    # arrange
    account = get_account_fixture(account_fixture_name)

    # Determine which VPCs require appliance mode from config
    config = lza_config()
    vpcs_requiring_appliance_mode: set[str] = set()
    for vpc in config.network.vpcs or []:
        for attachment in vpc.transit_gateway_attachments or []:
            if attachment.options and attachment.options.appliance_mode_support == "enable":
                vpcs_requiring_appliance_mode.add(vpc.name)

    # act
    attachments = [att for att in get_transit_gateway_vpc_attachments(account, region) if att["State"] == "available"]

    # assert
    non_compliant: list[str] = []
    for att in attachments:
        name = get_name_tag(att.get("Tags", [])) or att["TransitGatewayAttachmentId"]

        # Only check attachments for VPCs that require appliance mode
        if any(vpc_name in name for vpc_name in vpcs_requiring_appliance_mode):
            if att["Options"]["ApplianceModeSupport"] != "enable":
                non_compliant.append(name)

    assert non_compliant == [], f"Attachments missing appliance mode: {non_compliant}"


@pytest.mark.parametrize(
    ("account_fixture_name", "region"),
    get_transit_gateway_account_region_combinations(),
)
@cats(standard_name=["LZA-RAM-1"], test_suite="transit_gateway", test_id="3", evidence=Evidence.CONFIGURATION)
def test_transit_gateway_resource_sharing(
    account_fixture_name: str,
    region: str,
    get_account_fixture: GetAccountFixture,
) -> None:
    """Verify TGW has autoAcceptSharingAttachments enabled and shareTargets configured."""
    # arrange
    account = get_account_fixture(account_fixture_name)
    tgw_configs = get_transit_gateway_configs_for_region(region)

    # act
    active_tgws = get_active_transit_gateways(account, region)

    # assert
    assert active_tgws, f"No active Transit Gateways in {account_fixture_name} / {region}"

    non_compliant: dict[str, str] = {}
    for tgw in active_tgws:
        tgw_id = tgw["TransitGatewayId"]
        if tgw["Options"]["AutoAcceptSharedAttachments"] != "enable":
            non_compliant[tgw_id] = "autoAcceptSharingAttachments not enabled"

    assert non_compliant == {}, f"TGW sharing issues: {non_compliant}"

    # Validate config has shareTargets
    for tgw_config in tgw_configs:
        assert tgw_config.share_targets, f"TGW '{tgw_config.name}' has no shareTargets configured"
        ous = tgw_config.share_targets.organizational_units or []
        assert ous, f"TGW '{tgw_config.name}' has no OUs in shareTargets"


@pytest.mark.parametrize(
    ("account_fixture_name", "region"),
    get_transit_gateway_account_region_combinations(),
)
@cats(standard_name=["LZA-TGW-3"], test_suite="transit_gateway", test_id="5", evidence=Evidence.CONFIGURATION)
def test_transit_gateway_route_tables_for_traffic_separation(
    account_fixture_name: str,
    region: str,
    get_account_fixture: GetAccountFixture,
) -> None:
    """Verify TGW route tables exist matching LZA config for traffic flow separation."""
    # arrange
    account = get_account_fixture(account_fixture_name)
    ec2_client = account.session.client("ec2", region_name=region, config=DEFAULT_RETRY_CONFIG)
    tgw_configs = get_transit_gateway_configs_for_region(region)

    expected_rt_names: list[str] = []
    for tgw_config in tgw_configs:
        for rt_config in tgw_config.route_tables:
            expected_rt_names.append(rt_config.name)

    assert expected_rt_names, f"No TGW route tables defined in LZA config for {region}"

    # act
    active_tgw_ids = [tgw["TransitGatewayId"] for tgw in get_active_transit_gateways(account, region)]
    assert active_tgw_ids, f"No active Transit Gateways in {account_fixture_name} / {region}"

    route_tables_by_tgw_id = get_transit_gateway_route_tables_by_transit_gateway_id(account, region)
    deployed_rts = [route_table for tgw_id in active_tgw_ids for route_table in route_tables_by_tgw_id.get(tgw_id, [])]

    deployed_rt_names = [name for deployed_rt in deployed_rts if (name := get_name_tag(deployed_rt.get("Tags", []))) is not None]

    # assert — every configured route table must be deployed
    missing_rts = [name for name in expected_rt_names if name not in deployed_rt_names]
    assert missing_rts == [], f"TGW route tables missing in {account_fixture_name} / {region}: {missing_rts}"

    # assert — each deployed route table has at least one route (proving traffic separation config)
    empty_rts: list[str] = []
    for deployed_rt in deployed_rts:
        rt_id = deployed_rt["TransitGatewayRouteTableId"]
        rt_name = get_name_tag(deployed_rt.get("Tags", [])) or rt_id
        if rt_name not in expected_rt_names:
            continue
        routes = [
            route
            for page in ec2_client.get_paginator("search_transit_gateway_routes").paginate(
                TransitGatewayRouteTableId=rt_id,
                Filters=[{"Name": "state", "Values": ["active", "blackhole"]}],
            )
            for route in page["Routes"]
        ]
        if not routes:
            empty_rts.append(rt_name)

    assert empty_rts == [], f"TGW route tables with no routes (no traffic separation): {empty_rts}"

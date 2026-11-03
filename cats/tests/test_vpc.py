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
CATS - Validate VPC Network Architecture Configuration

This test verifies:
- LZA-NET-ARC-1: Network Architecture - Shared VPC Model (optional configuration)
- LZA-NET-ARC-2: Network Architecture - Hub-and-Spoke VPC Model (default configuration)
- LZA-VPC-DSGN-1: VPC Design - Static CIDR definitions
- LZA-VPC-DSGN-2: VPC Design - IPAM allocations
- LZA-VPC-DSGN-3: VPC Design - Subnets exist in target accounts with correct CIDR
- LZA-VPC-DSGN-4: VPC Design - Transit Gateway attachments exist and match configuration
- LZA-VPC-DSGN-5: VPC Design - Gateway Endpoints for S3
- LZA-VPC-DSGN-6: VPC Design - Gateway Endpoints for DynamoDB
- LZA-VPC-DSGN-7: VPC Design - NAT Gateways provisioned only in Perimeter account
- LZA-IGW-1: VPC Design - Internet Gateways exist for VPCs with internetGateway: true

The Universal Configuration has one internet edge: the Perimeter account, plus the LZA deployment
account on a container deployment (LZA-IGW-2, tests/test_deployment_account.py). The gateway tests
hold the deployed estate to that shape rather than to network-config.yaml: the two accounts are
identified by cats.yaml tag via ``internet_facing_accounts()``, and every other account under test
is checked whether or not the config declares a VPC there. Tests 5a/6a check Perimeter has NAT and
internet gateways in every enabled region, as many as network-config.yaml declares. Tests 5b/6b
check no other account has either in any enabled region.
"""

from __future__ import annotations

import logging

import pytest
from cats import GetAccountFixture, cats

from cats_utils.accounts import non_internet_facing_accounts, perimeter_account
from cats_utils.ec2 import (
    get_internet_gateways,
    get_nat_gateways,
    get_subnet_names_by_vpc_id,
    get_transit_gateway_attachment_names_by_vpc_id,
    get_vpc_endpoint_service_names_by_vpc_id,
    get_vpcs_by_name,
)
from cats_utils.evidence import Evidence
from lza_utils.lza_config import (
    get_vpc_account_region_combinations,
    get_vpc_account_region_combinations_with_interface_endpoints,
    get_vpcs_for_account_region,
    get_vpcs_with_cidrs,
    get_vpcs_with_gateway_endpoints,
    get_vpcs_with_interface_endpoints,
    get_vpcs_with_internet_gateway,
    get_vpcs_with_ipam_allocations,
    get_vpcs_with_nat_gateways,
    get_vpcs_with_subnets,
    get_vpcs_with_transit_gateway_attachments,
    lza_config,
)

logger = logging.getLogger(__name__)


@pytest.mark.parametrize(("account_fixture_name", "region"), get_vpc_account_region_combinations())
@cats(
    standard_name=["LZA-NET-ARC-1", "LZA-NET-ARC-2"],
    test_suite="vpc",
    test_id="1",
    evidence=Evidence.CONFIGURATION,
)
def test_vpc_exists_in_target_account(
    account_fixture_name: str,
    region: str,
    get_account_fixture: GetAccountFixture,
) -> None:
    """Test that each VPC from network config exists in the correct account and region."""
    # arrange
    account = get_account_fixture(account_fixture_name)
    account_vpcs = get_vpcs_for_account_region(account_fixture_name, region)
    assert account_vpcs, f"No VPCs configured for {account_fixture_name} in {region}"

    # act
    deployed_vpcs = get_vpcs_by_name(account, region)

    # assert
    missing_vpcs = [vpc_config.name for vpc_config in account_vpcs if vpc_config.name not in deployed_vpcs]
    assert missing_vpcs == [], f"VPCs not found: {missing_vpcs}"


@pytest.mark.parametrize(("account_fixture_name", "region"), get_vpc_account_region_combinations())
@cats(standard_name=["LZA-VPC-DSGN-3"], test_suite="vpc", test_id="2", evidence=Evidence.CONFIGURATION)
def test_subnets_exist_in_target_account(
    account_fixture_name: str,
    region: str,
    get_account_fixture: GetAccountFixture,
) -> None:
    """Test that each subnet from network config exists."""
    # arrange
    account = get_account_fixture(account_fixture_name)
    account_vpcs = get_vpcs_with_subnets(account_fixture_name, region)
    assert account_vpcs, f"No VPCs with subnets configured for {account_fixture_name} in {region}"

    # act
    deployed_vpcs = get_vpcs_by_name(account, region)
    subnet_names_by_vpc_id = get_subnet_names_by_vpc_id(account, region)

    # assert
    missing_subnets: dict[str, list[str]] = {}
    for vpc_config in account_vpcs:
        assert vpc_config.name in deployed_vpcs, f"VPC {vpc_config.name} not found"
        deployed_subnet_names = subnet_names_by_vpc_id.get(deployed_vpcs[vpc_config.name]["VpcId"], set())
        missing = [subnet_config.name for subnet_config in vpc_config.subnets or [] if subnet_config.name not in deployed_subnet_names]
        if missing:
            missing_subnets[vpc_config.name] = missing

    assert missing_subnets == {}, f"Subnets not found: {missing_subnets}"


@pytest.mark.parametrize(("account_fixture_name", "region"), get_vpc_account_region_combinations())
@cats(standard_name=["LZA-VPC-DSGN-4"], test_suite="vpc", test_id="3", evidence=Evidence.CONFIGURATION)
def test_transit_gateway_attachments_exist(
    account_fixture_name: str,
    region: str,
    get_account_fixture: GetAccountFixture,
) -> None:
    """Test that Transit Gateway attachments exist for VPCs with transitGatewayAttachments."""
    # arrange
    account = get_account_fixture(account_fixture_name)
    account_vpcs = get_vpcs_with_transit_gateway_attachments(account_fixture_name, region)

    # act
    deployed_vpcs = get_vpcs_by_name(account, region)
    attachment_names_by_vpc_id = get_transit_gateway_attachment_names_by_vpc_id(account, region)

    # assert
    missing_attachments: dict[str, list[str]] = {}
    for vpc_config in account_vpcs:
        assert vpc_config.name in deployed_vpcs, f"VPC {vpc_config.name} not found"
        deployed_attachment_names = attachment_names_by_vpc_id.get(deployed_vpcs[vpc_config.name]["VpcId"], set())
        missing = [tgw_config.name for tgw_config in vpc_config.transit_gateway_attachments or [] if tgw_config.name not in deployed_attachment_names]
        if missing:
            missing_attachments[vpc_config.name] = missing

    assert missing_attachments == {}, f"TGW attachments not found: {missing_attachments}"


@pytest.mark.parametrize(("account_fixture_name", "region"), get_vpc_account_region_combinations())
@cats(
    standard_name=["LZA-VPC-DSGN-5", "LZA-VPC-DSGN-6"],
    test_suite="vpc",
    test_id="4",
    evidence=Evidence.CONFIGURATION,
)
def test_vpc_gateway_endpoints_exist(
    account_fixture_name: str,
    region: str,
    get_account_fixture: GetAccountFixture,
) -> None:
    """Test that VPC gateway endpoints (S3, DynamoDB) exist when configured."""
    # arrange
    account = get_account_fixture(account_fixture_name)
    account_vpcs = get_vpcs_with_gateway_endpoints(account_fixture_name, region)

    # act
    deployed_vpcs = get_vpcs_by_name(account, region)
    service_names_by_vpc_id = get_vpc_endpoint_service_names_by_vpc_id(account, region, "Gateway")

    # assert
    missing_endpoints: dict[str, list[str]] = {}
    for vpc_config in account_vpcs:
        assert vpc_config.name in deployed_vpcs, f"VPC {vpc_config.name} not found"
        deployed_service_names = service_names_by_vpc_id.get(deployed_vpcs[vpc_config.name]["VpcId"], set())

        endpoints_config = vpc_config.gateway_endpoints
        if not endpoints_config or not endpoints_config.endpoints:
            continue

        missing = [
            str(endpoint_config.service)
            for endpoint_config in endpoints_config.endpoints
            if f"com.amazonaws.{region}.{endpoint_config.service}" not in deployed_service_names
        ]
        if missing:
            missing_endpoints[vpc_config.name] = missing

    assert missing_endpoints == {}, f"Gateway endpoints missing: {missing_endpoints}"


def _perimeter_region_params() -> list[tuple[str, str]]:
    """``(perimeter fixture name, region)`` for every enabled region."""
    return [(perimeter_account(), region) for region in lza_config().enabled_regions]


def _non_internet_facing_account_region_params() -> list[tuple[str, str]]:
    """``(fixture name, region)`` for every non-internet-facing account under test in every enabled region."""
    return [(account_fixture_name, region) for account_fixture_name in non_internet_facing_accounts() for region in lza_config().enabled_regions]


@pytest.mark.parametrize(("account_fixture_name", "region"), _perimeter_region_params())
@cats(standard_name=["LZA-VPC-DSGN-7"], test_suite="vpc", test_id="5a", evidence=Evidence.CONFIGURATION)
def test_nat_gateways_exist_in_perimeter(
    account_fixture_name: str,
    region: str,
    get_account_fixture: GetAccountFixture,
) -> None:
    """Verify the Perimeter account has NAT gateways in every enabled region, as many as network-config.yaml declares."""
    # arrange
    account = get_account_fixture(account_fixture_name)
    account_vpcs = get_vpcs_with_nat_gateways(account_fixture_name, region)
    assert account_vpcs, f"No NAT gateway VPC declared for {account_fixture_name} in {region}; Perimeter needs one in every enabled region"
    expected_count = sum(len(vpc.nat_gateways or []) for vpc in account_vpcs)

    # act
    nat_gateways = get_nat_gateways(account, region)
    active_nat_gateways = [ngw for ngw in nat_gateways if ngw["State"] in ["available", "pending"]]

    # assert
    assert len(active_nat_gateways) == expected_count, (
        f"Expected {expected_count} NAT Gateways in {account_fixture_name} {region}, found {len(active_nat_gateways)}"
    )


@pytest.mark.parametrize(("account_fixture_name", "region"), _non_internet_facing_account_region_params())
@cats(standard_name=["LZA-VPC-DSGN-7"], test_suite="vpc", test_id="5b", evidence=Evidence.CONFIGURATION)
def test_nat_gateways_not_in_non_internet_facing_accounts(
    account_fixture_name: str,
    region: str,
    get_account_fixture: GetAccountFixture,
) -> None:
    """Verify no NAT gateway exists in any non-internet-facing account, in any enabled region."""
    # arrange
    account = get_account_fixture(account_fixture_name)

    # act
    nat_gateways = get_nat_gateways(account, region)
    active_nat_gateway_ids = sorted(ngw["NatGatewayId"] for ngw in nat_gateways if ngw["State"] in ["available", "pending"])

    # assert
    assert active_nat_gateway_ids == [], f"NAT Gateways found in {account_fixture_name} {region}: {active_nat_gateway_ids}"


@pytest.mark.parametrize(("account_fixture_name", "region"), _perimeter_region_params())
@cats(standard_name=["LZA-IGW-1"], test_suite="vpc", test_id="6a", evidence=Evidence.CONFIGURATION)
def test_internet_gateway_exists_in_perimeter(
    account_fixture_name: str,
    region: str,
    get_account_fixture: GetAccountFixture,
) -> None:
    """Verify the Perimeter account has attached internet gateways in every enabled region, one per VPC network-config.yaml declares one on."""
    # arrange
    account = get_account_fixture(account_fixture_name)
    vpcs_with_igw = get_vpcs_with_internet_gateway(account_fixture_name, region)
    assert vpcs_with_igw, f"No internet gateway VPC declared for {account_fixture_name} in {region}; Perimeter needs one in every enabled region"

    # act
    igws = get_internet_gateways(account, region)
    attached_igws = [igw for igw in igws if igw.get("Attachments")]

    # assert
    assert len(attached_igws) >= len(vpcs_with_igw), (
        f"Expected at least {len(vpcs_with_igw)} IGWs in {account_fixture_name} {region}, found {len(attached_igws)}"
    )


@pytest.mark.parametrize(("account_fixture_name", "region"), _non_internet_facing_account_region_params())
@cats(standard_name=["LZA-IGW-1"], test_suite="vpc", test_id="6b", evidence=Evidence.CONFIGURATION)
def test_internet_gateway_not_in_non_internet_facing_accounts(
    account_fixture_name: str,
    region: str,
    get_account_fixture: GetAccountFixture,
) -> None:
    """Verify no attached internet gateway exists in any non-internet-facing account, in any enabled region."""
    # arrange
    account = get_account_fixture(account_fixture_name)

    # act
    igws = get_internet_gateways(account, region)
    attached_igw_ids = sorted(igw["InternetGatewayId"] for igw in igws if igw.get("Attachments"))

    # assert
    assert attached_igw_ids == [], f"Internet Gateways found in {account_fixture_name} {region}: {attached_igw_ids}"


@pytest.mark.parametrize(("account_fixture_name", "region"), get_vpc_account_region_combinations())
@cats(standard_name=["LZA-VPC-DSGN-1"], test_suite="vpc", test_id="7", evidence=Evidence.CONFIGURATION)
def test_vpc_has_static_cidr(
    account_fixture_name: str,
    region: str,
    get_account_fixture: GetAccountFixture,
) -> None:
    """Verify VPCs with static CIDRs in config have matching CIDR blocks deployed."""
    # arrange
    account = get_account_fixture(account_fixture_name)
    vpcs_with_static_cidrs = get_vpcs_with_cidrs(account_fixture_name, region)

    # act
    deployed_vpcs = get_vpcs_by_name(account, region)

    # assert
    mismatches: dict[str, str] = {}
    for vpc_config in vpcs_with_static_cidrs:
        assert vpc_config.name in deployed_vpcs, f"VPC {vpc_config.name} not found"
        vpc = deployed_vpcs[vpc_config.name]

        actual_cidrs = sorted([assoc["CidrBlock"] for assoc in vpc.get("CidrBlockAssociationSet", []) if assoc.get("CidrBlock")])
        expected_cidrs = sorted(vpc_config.cidrs or [])

        if actual_cidrs != expected_cidrs:
            mismatches[vpc_config.name] = f"expected {expected_cidrs}, got {actual_cidrs}"

    assert mismatches == {}, f"VPC CIDR mismatches: {mismatches}"


@pytest.mark.parametrize(("account_fixture_name", "region"), get_vpc_account_region_combinations())
@cats(standard_name=["LZA-VPC-DSGN-2"], test_suite="vpc", test_id="8", evidence=Evidence.CONFIGURATION)
def test_vpc_has_ipam_allocation(
    account_fixture_name: str,
    region: str,
    get_account_fixture: GetAccountFixture,
) -> None:
    """Verify VPCs with IPAM allocations in config have a CIDR block deployed."""
    # arrange
    account = get_account_fixture(account_fixture_name)
    vpcs_with_ipam = get_vpcs_with_ipam_allocations(account_fixture_name, region)

    # act
    deployed_vpcs = get_vpcs_by_name(account, region)

    # assert
    missing_cidrs: list[str] = []
    for vpc_config in vpcs_with_ipam:
        assert vpc_config.name in deployed_vpcs, f"VPC {vpc_config.name} not found"
        if not deployed_vpcs[vpc_config.name].get("CidrBlockAssociationSet", []):
            missing_cidrs.append(vpc_config.name)

    assert missing_cidrs == [], f"VPCs with IPAM allocation but no CIDR: {missing_cidrs}"


@pytest.mark.parametrize(("account_fixture_name", "region"), get_vpc_account_region_combinations_with_interface_endpoints())
@cats(standard_name=["LZA-NET-ARC-3"], test_suite="vpc", test_id="9", evidence=Evidence.CONFIGURATION)
def test_vpc_interface_endpoints_exist(
    account_fixture_name: str,
    region: str,
    get_account_fixture: GetAccountFixture,
) -> None:
    """Verify interface endpoints exist in VPCs where configured."""
    # arrange
    account = get_account_fixture(account_fixture_name)
    vpcs_with_endpoints = get_vpcs_with_interface_endpoints(account_fixture_name, region)
    assert vpcs_with_endpoints, f"No VPCs with interface endpoints for {account_fixture_name} in {region}"

    # act
    deployed_vpcs = get_vpcs_by_name(account, region)
    service_names_by_vpc_id = get_vpc_endpoint_service_names_by_vpc_id(account, region, "Interface")

    # assert
    missing: dict[str, list[str]] = {}
    for vpc_config in vpcs_with_endpoints:
        assert vpc_config.name in deployed_vpcs, f"VPC {vpc_config.name} not found"
        deployed_service_names = service_names_by_vpc_id.get(deployed_vpcs[vpc_config.name]["VpcId"], set())

        endpoint_config = vpc_config.interface_endpoints
        assert endpoint_config

        missing_services = [ep.service for ep in endpoint_config.endpoints if f"com.amazonaws.{region}.{ep.service}" not in deployed_service_names]
        if missing_services:
            missing[vpc_config.name] = missing_services

    assert missing == {}, f"Interface endpoints missing: {missing}"

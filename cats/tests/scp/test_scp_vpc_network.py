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
CATS - SCP Enforcement: VPC and Network Protection

This test verifies:
- LZA-G-SCP-20: Restricts the ability to provision a default VPC
- LZA-G-SCP-21: Restricts the ability to provision or modify an Internet Gateway
- LZA-G-SCP-22: Restricts the modification of VPCs provisioned by LZA
- LZA-G-SCP-23: Restricts the modification of NAT Gateways
- LZA-G-SCP-24: Restricts the modification of Transit Gateways
"""

from __future__ import annotations

import logging

import pytest
from botocore.exceptions import ClientError
from cats import AccountUnderTest, GetAccountFixture, cats, cats_requires

from cats_utils.accounts import infrastructure_accounts, non_management_accounts, workload_account_params
from cats_utils.boto import DEFAULT_RETRY_CONFIG
from cats_utils.evidence import Evidence
from cats_utils.requirement import Requirement
from lza_utils.lza_config import lza_config

logger = logging.getLogger(__name__)


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@pytest.mark.parametrize("account_fixture_name", non_management_accounts())
@cats(standard_name=["LZA-G-SCP-20"], test_suite="scp", test_id="20", mutating=True, evidence=Evidence.BEHAVIORAL)
def test_scp_blocks_default_vpc_creation(account_fixture_name: str, region: str, get_account_fixture: GetAccountFixture) -> None:
    """Verify SCP denies creation of default VPC."""
    # arrange
    account = get_account_fixture(account_fixture_name)
    client = account.session.client("ec2", region_name=region, config=DEFAULT_RETRY_CONFIG)

    # act & assert
    with pytest.raises(ClientError, match="explicit deny in a service control policy"):
        client.create_default_vpc(DryRun=False)


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@pytest.mark.parametrize("account_fixture_name", non_management_accounts())
@cats(standard_name=["LZA-G-SCP-21"], test_suite="scp", test_id="21", mutating=True, evidence=Evidence.BEHAVIORAL)
def test_scp_blocks_internet_gateway_creation(account_fixture_name: str, region: str, get_account_fixture: GetAccountFixture) -> None:
    """Verify SCP denies creation of Internet Gateways."""
    # arrange
    account = get_account_fixture(account_fixture_name)
    client = account.session.client("ec2", region_name=region, config=DEFAULT_RETRY_CONFIG)

    # act & assert
    with pytest.raises(ClientError, match="explicit deny in a service control policy"):
        client.create_internet_gateway(DryRun=False)


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@pytest.mark.parametrize("account_fixture_name", non_management_accounts())
@cats(standard_name=["LZA-G-SCP-22"], test_suite="scp", test_id="22", mutating=True, evidence=Evidence.BEHAVIORAL)
def test_scp_blocks_vpc_creation(account_fixture_name: str, region: str, get_account_fixture: GetAccountFixture) -> None:
    """Verify SCP denies creation of VPCs."""
    # arrange
    account = get_account_fixture(account_fixture_name)
    client = account.session.client("ec2", region_name=region, config=DEFAULT_RETRY_CONFIG)

    # act & assert
    with pytest.raises(ClientError, match="explicit deny in a service control policy"):
        client.create_vpc(CidrBlock="10.255.255.0/24", DryRun=False)


_infrastructure_only = lza_config().account_fixture_names_in_ous(["Infrastructure"])


def _assert_nat_gateway_creation_denied(account: AccountUnderTest) -> None:
    """CreateNatGateway in the home region, against a real subnet, must be denied by SCP.

    Uses home_region because CreateNatGateway requires a real subnet ID; subnets only exist where
    VPCs are deployed (home region in UC).
    """
    # arrange
    client = account.session.client("ec2", region_name=lza_config().home_region, config=DEFAULT_RETRY_CONFIG)
    subnets = client.describe_subnets(MaxResults=5)["Subnets"]
    assert subnets, f"No subnets found in {account.name} / {lza_config().home_region}"

    # act & assert
    with pytest.raises(ClientError, match="explicit deny in a service control policy"):
        client.create_nat_gateway(SubnetId=subnets[0]["SubnetId"])


def _assert_transit_gateway_creation_denied(account: AccountUnderTest, region: str) -> None:
    """CreateTransitGateway must be denied by SCP."""
    client = account.session.client("ec2", region_name=region, config=DEFAULT_RETRY_CONFIG)
    with pytest.raises(ClientError, match="explicit deny in a service control policy"):
        client.create_transit_gateway(DryRun=True)


def _assert_transit_gateway_deletion_denied(account: AccountUnderTest, region: str) -> None:
    """DeleteTransitGateway must be denied by SCP."""
    client = account.session.client("ec2", region_name=region, config=DEFAULT_RETRY_CONFIG)
    with pytest.raises(ClientError, match="explicit deny in a service control policy"):
        client.delete_transit_gateway(TransitGatewayId="tgw-00000000000000000", DryRun=True)


@pytest.mark.parametrize("account_fixture_name", infrastructure_accounts())
@cats(standard_name=["LZA-G-SCP-23"], test_suite="scp", test_id="23a", mutating=True, evidence=Evidence.BEHAVIORAL)
def test_scp_blocks_nat_gateway_creation_infrastructure(account_fixture_name: str, get_account_fixture: GetAccountFixture) -> None:
    """Verify the Infrastructure SCP denies creation of NAT Gateways."""
    _assert_nat_gateway_creation_denied(get_account_fixture(account_fixture_name))


@cats_requires(Requirement.WORKLOAD_ACCOUNTS)
@pytest.mark.parametrize("account_fixture_name", workload_account_params())
@cats(standard_name=["LZA-G-SCP-23"], test_suite="scp", test_id="23a-workload", mutating=True, evidence=Evidence.BEHAVIORAL)
def test_scp_blocks_nat_gateway_creation_workload(account_fixture_name: str, get_account_fixture: GetAccountFixture) -> None:
    """Verify the Workloads SCP denies creation of NAT Gateways."""
    _assert_nat_gateway_creation_denied(get_account_fixture(account_fixture_name))


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@pytest.mark.parametrize("account_fixture_name", _infrastructure_only)
@cats(standard_name=["LZA-G-SCP-23"], test_suite="scp", test_id="23b", mutating=True, evidence=Evidence.BEHAVIORAL)
def test_scp_blocks_nat_gateway_deletion(account_fixture_name: str, region: str, get_account_fixture: GetAccountFixture) -> None:
    """Verify SCP denies deletion of NAT Gateways (Infrastructure OU only)."""
    # arrange
    account = get_account_fixture(account_fixture_name)
    client = account.session.client("ec2", region_name=region, config=DEFAULT_RETRY_CONFIG)

    # act & assert
    with pytest.raises(ClientError, match="explicit deny in a service control policy"):
        client.delete_nat_gateway(NatGatewayId="nat-00000000000000000", DryRun=True)


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@pytest.mark.parametrize("account_fixture_name", infrastructure_accounts())
@cats(standard_name=["LZA-G-SCP-24"], test_suite="scp", test_id="24a", mutating=True, evidence=Evidence.BEHAVIORAL)
def test_scp_blocks_transit_gateway_creation_infrastructure(account_fixture_name: str, region: str, get_account_fixture: GetAccountFixture) -> None:
    """Verify the Infrastructure SCP denies creation of Transit Gateways."""
    _assert_transit_gateway_creation_denied(get_account_fixture(account_fixture_name), region)


@cats_requires(Requirement.WORKLOAD_ACCOUNTS)
@pytest.mark.parametrize("region", lza_config().enabled_regions)
@pytest.mark.parametrize("account_fixture_name", workload_account_params())
@cats(standard_name=["LZA-G-SCP-24"], test_suite="scp", test_id="24a-workload", mutating=True, evidence=Evidence.BEHAVIORAL)
def test_scp_blocks_transit_gateway_creation_workload(account_fixture_name: str, region: str, get_account_fixture: GetAccountFixture) -> None:
    """Verify the Workloads SCP denies creation of Transit Gateways."""
    _assert_transit_gateway_creation_denied(get_account_fixture(account_fixture_name), region)


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@pytest.mark.parametrize("account_fixture_name", infrastructure_accounts())
@cats(standard_name=["LZA-G-SCP-24"], test_suite="scp", test_id="24b", mutating=True, evidence=Evidence.BEHAVIORAL)
def test_scp_blocks_transit_gateway_deletion_infrastructure(account_fixture_name: str, region: str, get_account_fixture: GetAccountFixture) -> None:
    """Verify the Infrastructure SCP denies deletion of Transit Gateways."""
    _assert_transit_gateway_deletion_denied(get_account_fixture(account_fixture_name), region)


@cats_requires(Requirement.WORKLOAD_ACCOUNTS)
@pytest.mark.parametrize("region", lza_config().enabled_regions)
@pytest.mark.parametrize("account_fixture_name", workload_account_params())
@cats(standard_name=["LZA-G-SCP-24"], test_suite="scp", test_id="24b-workload", mutating=True, evidence=Evidence.BEHAVIORAL)
def test_scp_blocks_transit_gateway_deletion_workload(account_fixture_name: str, region: str, get_account_fixture: GetAccountFixture) -> None:
    """Verify the Workloads SCP denies deletion of Transit Gateways."""
    _assert_transit_gateway_deletion_denied(get_account_fixture(account_fixture_name), region)


# The Security OU's SCP (lza-core-security-guardrails-1) carries GRNETSEC1 only, which denies
# CreateInternetGateway and CreateVpc. The egress-only IGW, Elastic IP and IPAM denies
# (GRNETSEC2) live in the Infrastructure, Workloads and Sandbox SCPs, so Audit and LogArchive
# would create those resources rather than be denied.
_non_security = [f for f in non_management_accounts() if f not in lza_config().account_fixture_names_in_ous(["Security"], inherit=True)]


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@pytest.mark.parametrize("account_fixture_name", _non_security)
@cats(standard_name=["LZA-G-SCP-21"], test_suite="scp", test_id="21b", mutating=True, evidence=Evidence.BEHAVIORAL)
def test_scp_blocks_egress_only_internet_gateway_creation(account_fixture_name: str, region: str, get_account_fixture: GetAccountFixture) -> None:
    """Verify SCP denies creation of Egress-Only Internet Gateways."""
    # arrange
    account = get_account_fixture(account_fixture_name)
    client = account.session.client("ec2", region_name=region, config=DEFAULT_RETRY_CONFIG)

    # act & assert
    with pytest.raises(ClientError, match="explicit deny in a service control policy"):
        client.create_egress_only_internet_gateway(VpcId="vpc-00000000000000000", DryRun=True)


@cats(standard_name=["LZA-G-SCP-21"], test_suite="scp", test_id="21c", mutating=True, evidence=Evidence.BEHAVIORAL)
def test_scp_blocks_internet_gateway_detachment(Perimeter_account: AccountUnderTest) -> None:
    """Verify SCP denies detachment of Internet Gateways (Perimeter account)."""
    # arrange
    client = Perimeter_account.session.client("ec2", region_name=lza_config().home_region, config=DEFAULT_RETRY_CONFIG)

    igws = [igw for page in client.get_paginator("describe_internet_gateways").paginate() for igw in page["InternetGateways"]]
    attached = [(igw["InternetGatewayId"], att["VpcId"]) for igw in igws for att in igw.get("Attachments", []) if att.get("State") == "available"]  # type: ignore[comparison-overlap]

    assert attached, "No attached Internet Gateways found to test detachment protection"

    # act & assert
    igw_id, vpc_id = attached[0]
    with pytest.raises(ClientError, match="explicit deny in a service control policy"):
        client.detach_internet_gateway(InternetGatewayId=igw_id, VpcId=vpc_id, DryRun=True)


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@pytest.mark.parametrize("account_fixture_name", _non_security)
@cats(standard_name=["LZA-G-SCP-22"], test_suite="scp", test_id="22b", mutating=True, evidence=Evidence.BEHAVIORAL)
def test_scp_blocks_elastic_ip_allocation(account_fixture_name: str, region: str, get_account_fixture: GetAccountFixture) -> None:
    """Verify SCP denies allocation of Elastic IP addresses."""
    # arrange
    account = get_account_fixture(account_fixture_name)
    client = account.session.client("ec2", region_name=region, config=DEFAULT_RETRY_CONFIG)

    # act & assert
    with pytest.raises(ClientError, match="explicit deny in a service control policy"):
        client.allocate_address(Domain="vpc", DryRun=True)


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@pytest.mark.parametrize("account_fixture_name", _non_security)
@cats(standard_name=["LZA-G-SCP-22"], test_suite="scp", test_id="22c", mutating=True, evidence=Evidence.BEHAVIORAL)
def test_scp_blocks_ipam_creation(account_fixture_name: str, region: str, get_account_fixture: GetAccountFixture) -> None:
    """Verify SCP denies creation of IPAM resources."""
    # arrange
    account = get_account_fixture(account_fixture_name)
    client = account.session.client("ec2", region_name=region, config=DEFAULT_RETRY_CONFIG)

    # act & assert
    with pytest.raises(ClientError, match="explicit deny in a service control policy"):
        client.create_ipam(DryRun=True)


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@pytest.mark.parametrize("account_fixture_name", _non_security)
@cats(standard_name=["LZA-G-SCP-22"], test_suite="scp", test_id="22d", mutating=True, evidence=Evidence.BEHAVIORAL)
def test_scp_blocks_ipam_deletion(account_fixture_name: str, region: str, get_account_fixture: GetAccountFixture) -> None:
    """Verify SCP denies deletion of IPAM resources."""
    # arrange
    account = get_account_fixture(account_fixture_name)
    client = account.session.client("ec2", region_name=region, config=DEFAULT_RETRY_CONFIG)

    # act & assert
    with pytest.raises(ClientError, match="explicit deny in a service control policy"):
        client.delete_ipam(IpamId="ipam-00000000000000000", DryRun=True)

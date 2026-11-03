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
EC2 lookups batched per account and region.

Each fetcher reads one resource type for an account and region through its
paginator, caches it with cats_cache.cached(), and returns it indexed for local
correlation. The index_* functions are pure and unit tested in test_ec2.py.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from cats_utils.boto import DEFAULT_RETRY_CONFIG
from cats_utils.cats_cache import cached

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    from mypy_boto3_ec2.type_defs import (
        FlowLogTypeDef,
        InternetGatewayTypeDef,
        NatGatewayTypeDef,
        NetworkAclTypeDef,
        RouteTableTypeDef,
        RouteTypeDef,
        SecurityGroupTypeDef,
        SubnetTypeDef,
        TagTypeDef,
        TransitGatewayRouteTableTypeDef,
        TransitGatewayTypeDef,
        TransitGatewayVpcAttachmentTypeDef,
        VpcEndpointTypeDef,
        VpcTypeDef,
    )

    from cats_types import CatsAccountProtocol


# ============================================================================
# Pure indexing functions
# ============================================================================


def get_name_tag(tags: Sequence[TagTypeDef]) -> str | None:
    """Value of the Name tag, or None when the resource has no Name tag."""
    return next((tag["Value"] for tag in tags if tag.get("Key") == "Name"), None)


def index_vpcs_by_name(vpcs: Iterable[VpcTypeDef]) -> dict[str, VpcTypeDef]:
    """{Name tag: VPC}. VPCs without a Name tag are left out. Raises ValueError when two VPCs share a Name tag."""
    vpcs_by_name: dict[str, VpcTypeDef] = {}
    for vpc in vpcs:
        name = get_name_tag(vpc.get("Tags", []))
        if name is None:
            continue
        if name in vpcs_by_name:
            raise ValueError(f"Two VPCs share the Name tag '{name}': {vpcs_by_name[name]['VpcId']} and {vpc['VpcId']}")
        vpcs_by_name[name] = vpc
    return vpcs_by_name


def index_subnet_names_by_vpc_id(subnets: Iterable[SubnetTypeDef]) -> dict[str, set[str]]:
    """{vpc_id: {subnet Name tags}}. Subnets without a Name tag are left out."""
    names_by_vpc_id: dict[str, set[str]] = {}
    for subnet in subnets:
        name = get_name_tag(subnet.get("Tags", []))
        if name is not None:
            names_by_vpc_id.setdefault(subnet["VpcId"], set()).add(name)
    return names_by_vpc_id


def index_transit_gateway_attachment_names_by_vpc_id(attachments: Iterable[TransitGatewayVpcAttachmentTypeDef]) -> dict[str, set[str]]:
    """{vpc_id: {attachment Name tags}}. Attachments without a Name tag are left out."""
    names_by_vpc_id: dict[str, set[str]] = {}
    for attachment in attachments:
        name = get_name_tag(attachment.get("Tags", []))
        if name is not None:
            names_by_vpc_id.setdefault(attachment["VpcId"], set()).add(name)
    return names_by_vpc_id


def index_vpc_endpoint_service_names_by_vpc_id(
    endpoints: Iterable[VpcEndpointTypeDef],
    endpoint_type: Literal["Gateway", "Interface"],
) -> dict[str, set[str]]:
    """{vpc_id: {service names}} for endpoints of one type."""
    service_names_by_vpc_id: dict[str, set[str]] = {}
    for endpoint in endpoints:
        if endpoint["VpcEndpointType"] == endpoint_type:
            service_names_by_vpc_id.setdefault(endpoint["VpcId"], set()).add(endpoint["ServiceName"])
    return service_names_by_vpc_id


def index_security_groups_by_vpc_id(security_groups: Iterable[SecurityGroupTypeDef]) -> dict[str, list[SecurityGroupTypeDef]]:
    """{vpc_id: [security groups]}."""
    security_groups_by_vpc_id: dict[str, list[SecurityGroupTypeDef]] = {}
    for security_group in security_groups:
        security_groups_by_vpc_id.setdefault(security_group["VpcId"], []).append(security_group)
    return security_groups_by_vpc_id


def index_network_acl_names_by_vpc_id(network_acls: Iterable[NetworkAclTypeDef]) -> dict[str, set[str]]:
    """{vpc_id: {NACL Name tags}}. NACLs without a Name tag (e.g. the VPC default) are left out."""
    names_by_vpc_id: dict[str, set[str]] = {}
    for network_acl in network_acls:
        name = get_name_tag(network_acl.get("Tags", []))
        if name is not None:
            names_by_vpc_id.setdefault(network_acl["VpcId"], set()).add(name)
    return names_by_vpc_id


def index_active_flow_logs_by_resource_id(flow_logs: Iterable[FlowLogTypeDef]) -> dict[str, list[FlowLogTypeDef]]:
    """{resource_id: [ACTIVE flow logs]}. Resource IDs are VPC, subnet, ENI or transit gateway IDs."""
    flow_logs_by_resource_id: dict[str, list[FlowLogTypeDef]] = {}
    for flow_log in flow_logs:
        if flow_log["FlowLogStatus"] == "ACTIVE":
            flow_logs_by_resource_id.setdefault(flow_log["ResourceId"], []).append(flow_log)
    return flow_logs_by_resource_id


def index_transit_gateway_route_tables_by_transit_gateway_id(
    route_tables: Iterable[TransitGatewayRouteTableTypeDef],
) -> dict[str, list[TransitGatewayRouteTableTypeDef]]:
    """{transit_gateway_id: [route tables]}."""
    route_tables_by_transit_gateway_id: dict[str, list[TransitGatewayRouteTableTypeDef]] = {}
    for route_table in route_tables:
        route_tables_by_transit_gateway_id.setdefault(route_table["TransitGatewayId"], []).append(route_table)
    return route_tables_by_transit_gateway_id


_DEFAULT_ROUTE_CIDR = "0.0.0.0/0"


def _route_target(route: RouteTypeDef) -> str:
    """The ID a route points at (``igw-…``, ``nat-…``, ``tgw-…``, …), whichever target key it carries."""
    return (
        route.get("GatewayId")
        or route.get("NatGatewayId")
        or route.get("TransitGatewayId")
        or route.get("VpcPeeringConnectionId")
        or route.get("NetworkInterfaceId")
        or route.get("InstanceId")
        or route.get("EgressOnlyInternetGatewayId")
        or route.get("CarrierGatewayId")
        or route.get("LocalGatewayId")
        or route.get("CoreNetworkArn")
        or "<no target>"
    )


def index_default_route_targets_by_vpc_id(route_tables: Iterable[RouteTableTypeDef]) -> dict[str, list[str]]:
    """{vpc_id: sorted targets of every IPv4 default route (0.0.0.0/0) in the VPC's route tables}.

    A route whose State is not ``active`` is reported as ``<state>:<target>`` so a blackhole
    shows up as such. One target routed to from several route tables appears once. A VPC with
    no default route is absent.
    """
    targets_by_vpc_id: dict[str, set[str]] = {}
    for route_table in route_tables:
        for route in route_table.get("Routes", []):
            if route.get("DestinationCidrBlock") != _DEFAULT_ROUTE_CIDR:
                continue
            target = _route_target(route)
            state = route.get("State", "<no state>")
            targets_by_vpc_id.setdefault(route_table["VpcId"], set()).add(target if state == "active" else f"{state}:{target}")
    return {vpc_id: sorted(targets) for vpc_id, targets in targets_by_vpc_id.items()}


# ============================================================================
# Cached fetchers: one paginated call per account and region
# ============================================================================


def get_vpcs(account: CatsAccountProtocol, region: str) -> list[VpcTypeDef]:
    """Every VPC in the account and region, including default VPCs."""

    def fetch() -> list[VpcTypeDef]:
        client = account.session.client("ec2", region_name=region, config=DEFAULT_RETRY_CONFIG)
        return [vpc for page in client.get_paginator("describe_vpcs").paginate() for vpc in page["Vpcs"]]

    return cached(f"ec2_vpcs:{account.account_id}:{region}", fetch)


def get_vpcs_by_name(account: CatsAccountProtocol, region: str) -> dict[str, VpcTypeDef]:
    """{Name tag: VPC} for the account and region. See index_vpcs_by_name."""
    return index_vpcs_by_name(get_vpcs(account, region))


def get_subnet_names_by_vpc_id(account: CatsAccountProtocol, region: str) -> dict[str, set[str]]:
    """{vpc_id: {subnet Name tags}} for the account and region."""

    def fetch() -> list[SubnetTypeDef]:
        client = account.session.client("ec2", region_name=region, config=DEFAULT_RETRY_CONFIG)
        return [subnet for page in client.get_paginator("describe_subnets").paginate() for subnet in page["Subnets"]]

    return index_subnet_names_by_vpc_id(cached(f"ec2_subnets:{account.account_id}:{region}", fetch))


def get_transit_gateway_vpc_attachments(account: CatsAccountProtocol, region: str) -> list[TransitGatewayVpcAttachmentTypeDef]:
    """Every transit gateway VPC attachment in the account and region, in any state."""

    def fetch() -> list[TransitGatewayVpcAttachmentTypeDef]:
        client = account.session.client("ec2", region_name=region, config=DEFAULT_RETRY_CONFIG)
        paginator = client.get_paginator("describe_transit_gateway_vpc_attachments")
        return [attachment for page in paginator.paginate() for attachment in page["TransitGatewayVpcAttachments"]]

    return cached(f"ec2_tgw_vpc_attachments:{account.account_id}:{region}", fetch)


def get_transit_gateway_attachment_names_by_vpc_id(account: CatsAccountProtocol, region: str) -> dict[str, set[str]]:
    """{vpc_id: {attachment Name tags}} for the account and region."""
    return index_transit_gateway_attachment_names_by_vpc_id(get_transit_gateway_vpc_attachments(account, region))


def get_vpc_endpoint_service_names_by_vpc_id(
    account: CatsAccountProtocol,
    region: str,
    endpoint_type: Literal["Gateway", "Interface"],
) -> dict[str, set[str]]:
    """{vpc_id: {service names}} for endpoints of one type in the account and region."""

    def fetch() -> list[VpcEndpointTypeDef]:
        client = account.session.client("ec2", region_name=region, config=DEFAULT_RETRY_CONFIG)
        return [endpoint for page in client.get_paginator("describe_vpc_endpoints").paginate() for endpoint in page["VpcEndpoints"]]

    return index_vpc_endpoint_service_names_by_vpc_id(cached(f"ec2_vpc_endpoints:{account.account_id}:{region}", fetch), endpoint_type)


def get_security_groups_by_vpc_id(account: CatsAccountProtocol, region: str) -> dict[str, list[SecurityGroupTypeDef]]:
    """{vpc_id: [security groups]} for the account and region."""

    def fetch() -> list[SecurityGroupTypeDef]:
        client = account.session.client("ec2", region_name=region, config=DEFAULT_RETRY_CONFIG)
        return [group for page in client.get_paginator("describe_security_groups").paginate() for group in page["SecurityGroups"]]

    return index_security_groups_by_vpc_id(cached(f"ec2_security_groups:{account.account_id}:{region}", fetch))


def get_network_acl_names_by_vpc_id(account: CatsAccountProtocol, region: str) -> dict[str, set[str]]:
    """{vpc_id: {NACL Name tags}} for the account and region."""

    def fetch() -> list[NetworkAclTypeDef]:
        client = account.session.client("ec2", region_name=region, config=DEFAULT_RETRY_CONFIG)
        return [acl for page in client.get_paginator("describe_network_acls").paginate() for acl in page["NetworkAcls"]]

    return index_network_acl_names_by_vpc_id(cached(f"ec2_network_acls:{account.account_id}:{region}", fetch))


def get_active_flow_logs_by_resource_id(account: CatsAccountProtocol, region: str) -> dict[str, list[FlowLogTypeDef]]:
    """{resource_id: [ACTIVE flow logs]} for the account and region. Serves VPC and transit gateway lookups."""

    def fetch() -> list[FlowLogTypeDef]:
        client = account.session.client("ec2", region_name=region, config=DEFAULT_RETRY_CONFIG)
        return [flow_log for page in client.get_paginator("describe_flow_logs").paginate() for flow_log in page["FlowLogs"]]

    return index_active_flow_logs_by_resource_id(cached(f"ec2_flow_logs:{account.account_id}:{region}", fetch))


def get_active_transit_gateways(account: CatsAccountProtocol, region: str) -> list[TransitGatewayTypeDef]:
    """Transit gateways in state 'available' in the account and region."""

    def fetch() -> list[TransitGatewayTypeDef]:
        client = account.session.client("ec2", region_name=region, config=DEFAULT_RETRY_CONFIG)
        return [tgw for page in client.get_paginator("describe_transit_gateways").paginate() for tgw in page["TransitGateways"]]

    return [tgw for tgw in cached(f"ec2_transit_gateways:{account.account_id}:{region}", fetch) if tgw["State"] == "available"]


def get_transit_gateway_route_tables_by_transit_gateway_id(
    account: CatsAccountProtocol,
    region: str,
) -> dict[str, list[TransitGatewayRouteTableTypeDef]]:
    """{transit_gateway_id: [route tables]} for the account and region."""

    def fetch() -> list[TransitGatewayRouteTableTypeDef]:
        client = account.session.client("ec2", region_name=region, config=DEFAULT_RETRY_CONFIG)
        paginator = client.get_paginator("describe_transit_gateway_route_tables")
        return [route_table for page in paginator.paginate() for route_table in page["TransitGatewayRouteTables"]]

    return index_transit_gateway_route_tables_by_transit_gateway_id(cached(f"ec2_tgw_route_tables:{account.account_id}:{region}", fetch))


def get_nat_gateways(account: CatsAccountProtocol, region: str) -> list[NatGatewayTypeDef]:
    """Every NAT gateway in the account and region, in any state."""

    def fetch() -> list[NatGatewayTypeDef]:
        client = account.session.client("ec2", region_name=region, config=DEFAULT_RETRY_CONFIG)
        return [nat_gateway for page in client.get_paginator("describe_nat_gateways").paginate() for nat_gateway in page["NatGateways"]]

    return cached(f"ec2_nat_gateways:{account.account_id}:{region}", fetch)


def get_internet_gateways(account: CatsAccountProtocol, region: str) -> list[InternetGatewayTypeDef]:
    """Every internet gateway in the account and region, attached or not."""

    def fetch() -> list[InternetGatewayTypeDef]:
        client = account.session.client("ec2", region_name=region, config=DEFAULT_RETRY_CONFIG)
        paginator = client.get_paginator("describe_internet_gateways")
        return [internet_gateway for page in paginator.paginate() for internet_gateway in page["InternetGateways"]]

    return cached(f"ec2_internet_gateways:{account.account_id}:{region}", fetch)


def get_route_tables(account: CatsAccountProtocol, region: str) -> list[RouteTableTypeDef]:
    """Every route table in the account and region, main and custom."""

    def fetch() -> list[RouteTableTypeDef]:
        client = account.session.client("ec2", region_name=region, config=DEFAULT_RETRY_CONFIG)
        return [route_table for page in client.get_paginator("describe_route_tables").paginate() for route_table in page["RouteTables"]]

    return cached(f"ec2_route_tables:{account.account_id}:{region}", fetch)


def get_default_route_targets_by_vpc_id(account: CatsAccountProtocol, region: str) -> dict[str, list[str]]:
    """{vpc_id: sorted 0.0.0.0/0 route targets} for the account and region. See index_default_route_targets_by_vpc_id."""
    return index_default_route_targets_by_vpc_id(get_route_tables(account, region))

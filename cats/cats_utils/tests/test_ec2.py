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

"""Unit tests for the index_* functions in cats_utils.ec2."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from cats_utils.ec2 import (
    get_name_tag,
    index_active_flow_logs_by_resource_id,
    index_default_route_targets_by_vpc_id,
    index_network_acl_names_by_vpc_id,
    index_security_groups_by_vpc_id,
    index_subnet_names_by_vpc_id,
    index_transit_gateway_attachment_names_by_vpc_id,
    index_transit_gateway_route_tables_by_transit_gateway_id,
    index_vpc_endpoint_service_names_by_vpc_id,
    index_vpcs_by_name,
)

if TYPE_CHECKING:
    from mypy_boto3_ec2.type_defs import (
        FlowLogTypeDef,
        NetworkAclTypeDef,
        RouteTableTypeDef,
        SecurityGroupTypeDef,
        SubnetTypeDef,
        TransitGatewayRouteTableTypeDef,
        TransitGatewayVpcAttachmentTypeDef,
        VpcEndpointTypeDef,
        VpcTypeDef,
    )


def test_get_name_tag_returns_name_value() -> None:
    assert get_name_tag([{"Key": "Accelerator", "Value": "AWSAccelerator"}, {"Key": "Name", "Value": "Network-Inspection"}]) == "Network-Inspection"


def test_get_name_tag_without_name_tag_returns_none() -> None:
    assert get_name_tag([{"Key": "Accelerator", "Value": "AWSAccelerator"}]) is None


def test_get_name_tag_empty_tags_returns_none() -> None:
    assert get_name_tag([]) is None


def test_index_vpcs_by_name_keys_by_name_tag_and_drops_unnamed() -> None:
    # arrange
    inspection: VpcTypeDef = {"VpcId": "vpc-1", "Tags": [{"Key": "Name", "Value": "Network-Inspection"}]}
    endpoints: VpcTypeDef = {"VpcId": "vpc-2", "Tags": [{"Key": "Name", "Value": "Network-Endpoints"}]}
    default_vpc: VpcTypeDef = {"VpcId": "vpc-3", "IsDefault": True}

    # act
    result = index_vpcs_by_name([inspection, endpoints, default_vpc])

    # assert
    expected = {"Network-Inspection": inspection, "Network-Endpoints": endpoints}
    assert result == expected


def test_index_vpcs_by_name_duplicate_name_raises() -> None:
    # arrange
    first: VpcTypeDef = {"VpcId": "vpc-1", "Tags": [{"Key": "Name", "Value": "Network-Inspection"}]}
    second: VpcTypeDef = {"VpcId": "vpc-2", "Tags": [{"Key": "Name", "Value": "Network-Inspection"}]}

    # act & assert
    with pytest.raises(ValueError, match="Two VPCs share the Name tag 'Network-Inspection': vpc-1 and vpc-2"):
        index_vpcs_by_name([first, second])


def test_index_subnet_names_by_vpc_id_groups_by_vpc() -> None:
    # arrange
    subnets: list[SubnetTypeDef] = [
        {"SubnetId": "subnet-1", "VpcId": "vpc-1", "Tags": [{"Key": "Name", "Value": "Network-Inspection-A"}]},
        {"SubnetId": "subnet-2", "VpcId": "vpc-1", "Tags": [{"Key": "Name", "Value": "Network-Inspection-B"}]},
        {"SubnetId": "subnet-3", "VpcId": "vpc-2", "Tags": [{"Key": "Name", "Value": "Network-Endpoints-A"}]},
        {"SubnetId": "subnet-4", "VpcId": "vpc-2"},
    ]

    # act
    result = index_subnet_names_by_vpc_id(subnets)

    # assert
    expected = {"vpc-1": {"Network-Inspection-A", "Network-Inspection-B"}, "vpc-2": {"Network-Endpoints-A"}}
    assert result == expected


def test_index_transit_gateway_attachment_names_by_vpc_id_groups_by_vpc() -> None:
    # arrange
    attachments: list[TransitGatewayVpcAttachmentTypeDef] = [
        {"TransitGatewayAttachmentId": "tgw-attach-1", "VpcId": "vpc-1", "Tags": [{"Key": "Name", "Value": "Network-Inspection"}]},
        {"TransitGatewayAttachmentId": "tgw-attach-2", "VpcId": "vpc-2", "Tags": [{"Key": "Name", "Value": "Network-Endpoints"}]},
    ]

    # act
    result = index_transit_gateway_attachment_names_by_vpc_id(attachments)

    # assert
    expected = {"vpc-1": {"Network-Inspection"}, "vpc-2": {"Network-Endpoints"}}
    assert result == expected


def test_index_vpc_endpoint_service_names_by_vpc_id_filters_by_type() -> None:
    # arrange
    endpoints: list[VpcEndpointTypeDef] = [
        {"VpcEndpointId": "vpce-1", "VpcId": "vpc-1", "VpcEndpointType": "Gateway", "ServiceName": "com.amazonaws.us-east-1.s3"},
        {"VpcEndpointId": "vpce-2", "VpcId": "vpc-1", "VpcEndpointType": "Gateway", "ServiceName": "com.amazonaws.us-east-1.dynamodb"},
        {"VpcEndpointId": "vpce-3", "VpcId": "vpc-1", "VpcEndpointType": "Interface", "ServiceName": "com.amazonaws.us-east-1.ssm"},
    ]

    # act
    gateway_result = index_vpc_endpoint_service_names_by_vpc_id(endpoints, "Gateway")
    interface_result = index_vpc_endpoint_service_names_by_vpc_id(endpoints, "Interface")

    # assert
    assert gateway_result == {"vpc-1": {"com.amazonaws.us-east-1.s3", "com.amazonaws.us-east-1.dynamodb"}}
    assert interface_result == {"vpc-1": {"com.amazonaws.us-east-1.ssm"}}


def test_index_security_groups_by_vpc_id_groups_by_vpc() -> None:
    # arrange
    default_sg: SecurityGroupTypeDef = {"GroupId": "sg-1", "GroupName": "default", "VpcId": "vpc-1"}
    app_sg: SecurityGroupTypeDef = {"GroupId": "sg-2", "GroupName": "Management", "VpcId": "vpc-1"}
    other_sg: SecurityGroupTypeDef = {"GroupId": "sg-3", "GroupName": "default", "VpcId": "vpc-2"}

    # act
    result = index_security_groups_by_vpc_id([default_sg, app_sg, other_sg])

    # assert
    expected = {"vpc-1": [default_sg, app_sg], "vpc-2": [other_sg]}
    assert result == expected


def test_index_network_acl_names_by_vpc_id_drops_unnamed_default_acl() -> None:
    # arrange
    network_acls: list[NetworkAclTypeDef] = [
        {"NetworkAclId": "acl-1", "VpcId": "vpc-1", "IsDefault": True},
        {"NetworkAclId": "acl-2", "VpcId": "vpc-1", "Tags": [{"Key": "Name", "Value": "Network-Inspection-Nacl"}]},
    ]

    # act
    result = index_network_acl_names_by_vpc_id(network_acls)

    # assert
    assert result == {"vpc-1": {"Network-Inspection-Nacl"}}


def test_index_active_flow_logs_by_resource_id_keeps_only_active() -> None:
    # arrange
    vpc_flow_log: FlowLogTypeDef = {"FlowLogId": "fl-1", "ResourceId": "vpc-1", "FlowLogStatus": "ACTIVE"}
    tgw_flow_log: FlowLogTypeDef = {"FlowLogId": "fl-2", "ResourceId": "tgw-1", "FlowLogStatus": "ACTIVE"}
    inactive_flow_log: FlowLogTypeDef = {"FlowLogId": "fl-3", "ResourceId": "vpc-2", "FlowLogStatus": "INACTIVE"}

    # act
    result = index_active_flow_logs_by_resource_id([vpc_flow_log, tgw_flow_log, inactive_flow_log])

    # assert
    expected = {"vpc-1": [vpc_flow_log], "tgw-1": [tgw_flow_log]}
    assert result == expected


def test_index_transit_gateway_route_tables_by_transit_gateway_id_groups_by_tgw() -> None:
    # arrange
    core: TransitGatewayRouteTableTypeDef = {"TransitGatewayRouteTableId": "tgw-rtb-1", "TransitGatewayId": "tgw-1"}
    inspection: TransitGatewayRouteTableTypeDef = {"TransitGatewayRouteTableId": "tgw-rtb-2", "TransitGatewayId": "tgw-1"}
    other: TransitGatewayRouteTableTypeDef = {"TransitGatewayRouteTableId": "tgw-rtb-3", "TransitGatewayId": "tgw-2"}

    # act
    result = index_transit_gateway_route_tables_by_transit_gateway_id([core, inspection, other])

    # assert
    expected = {"tgw-1": [core, inspection], "tgw-2": [other]}
    assert result == expected


def test_index_default_route_targets_by_vpc_id_collects_active_targets_once_per_vpc() -> None:
    # arrange
    public: RouteTableTypeDef = {
        "RouteTableId": "rtb-public",
        "VpcId": "vpc-1",
        "Routes": [
            {"DestinationCidrBlock": "10.0.0.0/16", "GatewayId": "local", "State": "active"},
            {"DestinationCidrBlock": "0.0.0.0/0", "GatewayId": "igw-1", "State": "active"},
        ],
    }
    private_a: RouteTableTypeDef = {
        "RouteTableId": "rtb-private-a",
        "VpcId": "vpc-1",
        "Routes": [{"DestinationCidrBlock": "0.0.0.0/0", "NatGatewayId": "nat-a", "State": "active"}],
    }
    private_b: RouteTableTypeDef = {
        "RouteTableId": "rtb-private-b",
        "VpcId": "vpc-1",
        "Routes": [{"DestinationCidrBlock": "0.0.0.0/0", "NatGatewayId": "nat-a", "State": "active"}],
    }
    isolated: RouteTableTypeDef = {
        "RouteTableId": "rtb-isolated",
        "VpcId": "vpc-2",
        "Routes": [{"DestinationCidrBlock": "10.1.0.0/16", "GatewayId": "local", "State": "active"}],
    }

    # act
    result = index_default_route_targets_by_vpc_id([public, private_a, private_b, isolated])

    # assert
    expected = {"vpc-1": ["igw-1", "nat-a"]}
    assert result == expected


def test_index_default_route_targets_by_vpc_id_marks_non_active_routes_with_state() -> None:
    # arrange
    route_table: RouteTableTypeDef = {
        "RouteTableId": "rtb-1",
        "VpcId": "vpc-1",
        "Routes": [
            {"DestinationCidrBlock": "0.0.0.0/0", "NatGatewayId": "nat-gone", "State": "blackhole"},
            {"DestinationCidrBlock": "0.0.0.0/0", "TransitGatewayId": "tgw-1", "State": "active"},
        ],
    }

    # act
    result = index_default_route_targets_by_vpc_id([route_table])

    # assert
    expected = {"vpc-1": ["blackhole:nat-gone", "tgw-1"]}
    assert result == expected

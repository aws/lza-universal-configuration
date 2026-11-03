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
CATS - VPC Security Configuration Validation

This test verifies:
- LZA-NET-SEC-4: Network Firewall exists in configured VPCs
- LZA-NET-SEC-5: Security Groups and NACLs are configured per LZA network config
- LZA-NET-SEC-6: Default VPCs are deleted in all non-management accounts
- LZA-NET-SEC-7: Default security group egress rules are removed
"""

from __future__ import annotations

import logging

import pytest
from cats import GetAccountFixture, cats

from cats_utils.accounts import non_management_accounts
from cats_utils.cats_cache import get_network_firewalls
from cats_utils.ec2 import (
    get_network_acl_names_by_vpc_id,
    get_security_groups_by_vpc_id,
    get_vpcs,
    get_vpcs_by_name,
)
from cats_utils.evidence import Evidence
from lza_utils.lza_config import (
    get_network_firewall_account_region_combinations,
    get_vpc_account_region_combinations,
    get_vpcs_for_account_region,
    lza_config,
)

logger = logging.getLogger(__name__)


@pytest.mark.parametrize(
    ("account_fixture_name", "region"),
    get_network_firewall_account_region_combinations(),
)
@cats(standard_name=["LZA-NET-SEC-4"], test_suite="vpc_security", test_id="1", evidence=Evidence.CONFIGURATION)
def test_network_firewall_exists(
    account_fixture_name: str,
    region: str,
    get_account_fixture: GetAccountFixture,
) -> None:
    """Verify Network Firewall exists in accounts/regions where configured."""
    # arrange
    account = get_account_fixture(account_fixture_name)

    # act
    firewalls = get_network_firewalls(account, region)

    # assert
    assert firewalls, f"No Network Firewalls found in {account_fixture_name} / {region}"


@pytest.mark.parametrize(("account_fixture_name", "region"), get_vpc_account_region_combinations())
@cats(standard_name=["LZA-NET-SEC-5"], test_suite="vpc_security", test_id="2", evidence=Evidence.CONFIGURATION)
def test_security_groups_exist(
    account_fixture_name: str,
    region: str,
    get_account_fixture: GetAccountFixture,
) -> None:
    """Verify LZA-configured security groups exist in target VPCs."""
    # arrange
    account = get_account_fixture(account_fixture_name)
    vpcs_with_sgs = [vpc for vpc in get_vpcs_for_account_region(account_fixture_name, region) if vpc.security_groups]

    # act
    deployed_vpcs = get_vpcs_by_name(account, region)
    security_groups_by_vpc_id = get_security_groups_by_vpc_id(account, region)

    # assert
    missing: dict[str, list[str]] = {}
    for vpc_config in vpcs_with_sgs:
        assert vpc_config.name in deployed_vpcs, f"VPC {vpc_config.name} not found"
        deployed_group_names = {sg["GroupName"] for sg in security_groups_by_vpc_id.get(deployed_vpcs[vpc_config.name]["VpcId"], [])}
        missing_groups = [sg_config.name for sg_config in vpc_config.security_groups or [] if sg_config.name not in deployed_group_names]
        if missing_groups:
            missing[vpc_config.name] = missing_groups

    assert missing == {}, f"Security groups not found: {missing}"


@pytest.mark.parametrize(("account_fixture_name", "region"), get_vpc_account_region_combinations())
@cats(standard_name=["LZA-NET-SEC-5"], test_suite="vpc_security", test_id="3", evidence=Evidence.CONFIGURATION)
def test_network_acls_exist(
    account_fixture_name: str,
    region: str,
    get_account_fixture: GetAccountFixture,
) -> None:
    """Verify LZA-configured NACLs exist in target VPCs."""
    # arrange
    account = get_account_fixture(account_fixture_name)
    vpcs_with_nacls = [vpc for vpc in get_vpcs_for_account_region(account_fixture_name, region) if vpc.network_acls]

    # act
    deployed_vpcs = get_vpcs_by_name(account, region)
    network_acl_names_by_vpc_id = get_network_acl_names_by_vpc_id(account, region)

    # assert
    missing: dict[str, list[str]] = {}
    for vpc_config in vpcs_with_nacls:
        assert vpc_config.name in deployed_vpcs, f"VPC {vpc_config.name} not found"
        deployed_nacl_names = network_acl_names_by_vpc_id.get(deployed_vpcs[vpc_config.name]["VpcId"], set())
        missing_nacls = [nacl_config.name for nacl_config in vpc_config.network_acls or [] if nacl_config.name not in deployed_nacl_names]
        if missing_nacls:
            missing[vpc_config.name] = missing_nacls

    assert missing == {}, f"NACLs not found: {missing}"


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@pytest.mark.parametrize("account_fixture_name", non_management_accounts())
@cats(standard_name=["LZA-NET-SEC-6"], test_suite="vpc_security", test_id="4", evidence=Evidence.CONFIGURATION)
def test_no_default_vpc(
    account_fixture_name: str,
    region: str,
    get_account_fixture: GetAccountFixture,
) -> None:
    """Verify default VPCs have been deleted after LZA deployment."""
    # arrange
    account = get_account_fixture(account_fixture_name)

    # act
    vpcs = get_vpcs(account, region)
    default_vpcs = [vpc for vpc in vpcs if vpc.get("IsDefault") is True]

    # assert
    assert default_vpcs == [], f"Default VPC still exists in {account_fixture_name} / {region}: {[vpc['VpcId'] for vpc in default_vpcs]}"


@pytest.mark.parametrize(("account_fixture_name", "region"), get_vpc_account_region_combinations())
@cats(standard_name=["LZA-NET-SEC-7"], test_suite="vpc_security", test_id="5", evidence=Evidence.CONFIGURATION)
def test_default_security_group_egress_removed(
    account_fixture_name: str,
    region: str,
    get_account_fixture: GetAccountFixture,
) -> None:
    """Verify default security group allow-all egress rules are removed for LZA VPCs."""
    # arrange
    account = get_account_fixture(account_fixture_name)
    vpcs_config = get_vpcs_for_account_region(account_fixture_name, region)
    vpcs_requiring_deletion = [vpc for vpc in vpcs_config if vpc.default_security_group_rules_deletion is True]

    # act
    deployed_vpcs = get_vpcs_by_name(account, region)
    security_groups_by_vpc_id = get_security_groups_by_vpc_id(account, region)

    # assert
    non_compliant: dict[str, list[str]] = {}
    for vpc_config in vpcs_requiring_deletion:
        assert vpc_config.name in deployed_vpcs, f"VPC {vpc_config.name} not found"
        vpc_id = deployed_vpcs[vpc_config.name]["VpcId"]
        default_sgs = [sg for sg in security_groups_by_vpc_id.get(vpc_id, []) if sg["GroupName"] == "default"]

        for sg in default_sgs:
            egress_rules = sg["IpPermissionsEgress"]
            allow_all = [
                rule
                for rule in egress_rules
                if rule.get("IpProtocol") == "-1" and any(r.get("CidrIp") == "0.0.0.0/0" for r in rule.get("IpRanges", []))
            ]
            if allow_all:
                non_compliant.setdefault(vpc_config.name, []).append(sg["GroupId"])

    assert non_compliant == {}, f"Default SGs still have allow-all egress in {account_fixture_name} / {region}: {non_compliant}"

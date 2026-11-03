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
CATS - Validate DNS Resolution Controls

Related LZA Controls and Tests:
- LZA-NET-SEC-2: External DNS servers unreachable (packet path)
  * test_dns_resolution_blocked_infrastructure
  * test_dns_resolution_blocked_workload (requires ``workload-accounts``)
- LZA-NET-SEC-8: Route 53 Resolver DNS Firewall blocks managed threat lists
  * test_dns_firewall_blocks_managed_list_domains_infrastructure
  * test_dns_firewall_blocks_managed_list_domains_workload (requires ``workload-accounts``)
"""

from __future__ import annotations

import logging

import pytest
from cats import AccountUnderTest, CatsNetworkResponse, GetAccountFixture, cats, cats_requires

from cats_utils.accounts import declared_network_handlers, infrastructure_accounts, workload_account_params
from cats_utils.evidence import Evidence
from cats_utils.requirement import Requirement
from lza_types.network_config import DnsFirewallManagedDomainListsType
from lza_utils.lza_config import lza_config

logger = logging.getLogger(__name__)

DNS_SERVER = "8.8.8.8"

# AWS-documented control domains: resolve to 1.2.3.4 unless blocked, so a BLOCK
# rule surfaces as DNS_FAILURE. The us-east-1 names are fixed across regions, and the
# managed lists exist only in partitions where the names resolve (see Requirement.DNS_FIREWALL).
# https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/resolver-dns-firewall-managed-domain-lists.html
_CONTROL_DOMAIN_SUFFIX = "firewall.route53resolver.us-east-1.amazonaws.com"  # partition: fixed
MANAGED_LIST_CONTROL_DOMAINS = {
    DnsFirewallManagedDomainListsType.aws_managed_domains_aggregate_threat_list: f"controldomain1.aggregatelist.{_CONTROL_DOMAIN_SUFFIX}",
    DnsFirewallManagedDomainListsType.aws_managed_domains_malware_domain_list: f"controldomain1.malwarelist.{_CONTROL_DOMAIN_SUFFIX}",
    DnsFirewallManagedDomainListsType.aws_managed_domains_botnet_commandand_control: f"controldomain1.botnetlist.{_CONTROL_DOMAIN_SUFFIX}",
}


def _get_dns_firewall_control_domains() -> dict[DnsFirewallManagedDomainListsType, str]:
    """Control domains for every managed list the LZA config BLOCKs, keyed by list."""
    blocked_lists = lza_config().dns_firewall_blocked_managed_lists
    assert blocked_lists, "No BLOCK rules using managed domain lists in DNS firewall config"
    return {managed_list: MANAGED_LIST_CONTROL_DOMAINS[managed_list] for managed_list in blocked_lists}


def _assert_external_dns_blocked(account: AccountUnderTest) -> None:
    """Probe the external DNS server from every declared handler in the account and require every call to time out."""
    # arrange
    handlers = declared_network_handlers(account)
    expected = {f"{account.name}.{handler.name}->{DNS_SERVER}:53": CatsNetworkResponse.TIMEOUT for handler in handlers}

    # act
    results = {f"{account.name}.{handler.name}->{DNS_SERVER}:53": handler.tcp_call(DNS_SERVER, 53) for handler in handlers}

    # assert
    assert results == expected, f"External DNS should be BLOCKED from {account.name}"


def _assert_managed_list_domains_blocked(account: AccountUnderTest) -> None:
    """Resolve every blocked managed list's control domain from every declared handler and require DNS failure."""
    # arrange
    handlers = declared_network_handlers(account)
    control_domains = _get_dns_firewall_control_domains()
    expected = {
        f"{account.name}.{handler.name}->{domain}": CatsNetworkResponse.DNS_FAILURE for handler in handlers for domain in control_domains.values()
    }

    # act
    results = {
        f"{account.name}.{handler.name}->{domain}": handler.tcp_call(domain, 443) for handler in handlers for domain in control_domains.values()
    }

    # assert
    assert results == expected, f"DNS Firewall managed lists should BLOCK resolution from {account.name}"


@pytest.mark.parametrize("account_fixture_name", infrastructure_accounts())
@cats(standard_name=["LZA-NET-SEC-2"], test_suite="dns", test_id="1", evidence=Evidence.BEHAVIORAL)
def test_dns_resolution_blocked_infrastructure(account_fixture_name: str, get_account_fixture: GetAccountFixture) -> None:
    """LZA-NET-SEC-2: Validate external DNS servers are unreachable from infrastructure VPCs."""
    _assert_external_dns_blocked(get_account_fixture(account_fixture_name))


@cats_requires(Requirement.WORKLOAD_ACCOUNTS)
@pytest.mark.parametrize("account_fixture_name", workload_account_params())
@cats(standard_name=["LZA-NET-SEC-2"], test_suite="dns", test_id="1-workload", evidence=Evidence.BEHAVIORAL)
def test_dns_resolution_blocked_workload(account_fixture_name: str, get_account_fixture: GetAccountFixture) -> None:
    """LZA-NET-SEC-2: Validate external DNS servers are unreachable from workload VPCs."""
    _assert_external_dns_blocked(get_account_fixture(account_fixture_name))


@cats_requires(Requirement.DNS_FIREWALL)
@pytest.mark.parametrize("account_fixture_name", infrastructure_accounts())
@cats(standard_name=["LZA-NET-SEC-8"], test_suite="dns", test_id="2", evidence=Evidence.BEHAVIORAL)
def test_dns_firewall_blocks_managed_list_domains_infrastructure(account_fixture_name: str, get_account_fixture: GetAccountFixture) -> None:
    """LZA-NET-SEC-8: Validate the Route 53 Resolver DNS Firewall blocks managed threat list domains in infrastructure VPCs."""
    _assert_managed_list_domains_blocked(get_account_fixture(account_fixture_name))


@cats_requires(Requirement.WORKLOAD_ACCOUNTS, Requirement.DNS_FIREWALL)
@pytest.mark.parametrize("account_fixture_name", workload_account_params())
@cats(standard_name=["LZA-NET-SEC-8"], test_suite="dns", test_id="2-workload", evidence=Evidence.BEHAVIORAL)
def test_dns_firewall_blocks_managed_list_domains_workload(account_fixture_name: str, get_account_fixture: GetAccountFixture) -> None:
    """LZA-NET-SEC-8: Validate the Route 53 Resolver DNS Firewall blocks managed threat list domains in workload VPCs."""
    _assert_managed_list_domains_blocked(get_account_fixture(account_fixture_name))

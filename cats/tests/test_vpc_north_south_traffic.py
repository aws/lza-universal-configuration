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
CATS - Validate North-South Traffic Controls

Related LZA Controls and Tests:
- LZA-NET-SEC-2: Validate internet access blocking from infrastructure and workload VPCs
  * test_internet_access_blocking_infrastructure
  * test_internet_access_blocking_workload (requires ``workload-accounts``)
- LZA-NET-SEC-3: Validate perimeter to hub connectivity with port filtering
  * test_perimeter_to_hub_allowed / test_perimeter_to_hub_blocked
  * test_hub_to_perimeter_allowed / test_hub_to_perimeter_blocked
"""

from __future__ import annotations

import logging
from itertools import product

import pytest
from cats import AccountUnderTest, CatsNetworkResponse, CatsNetworkResult, GetAccountFixture, cats, cats_requires

from cats_utils.accounts import declared_network_handlers, infrastructure_accounts, workload_account_params
from cats_utils.evidence import Evidence
from cats_utils.requirement import Requirement
from lza_utils.lza_config import lza_config

logger = logging.getLogger(__name__)

# Stable anycast IPs, probed directly: public names resolve here (AmazonProvidedDNS
# answers regardless of internet routing), so domain probes fail at connect stage
# non-deterministically. Direct IPs deterministically evidence the blocked packet path.
INTERNET_TARGETS = ["1.1.1.1", "8.8.8.8", "9.9.9.9"]

# Exact handler names (account_network_under_test keys in cats.yaml).
# Perimeter public subnets carry TGW routes to internal CIDRs - they are the north-south probes.
# SharedServices data is excluded by design: empty route table, isolated.
PERIMETER_HANDLERS = ("ingresspublic", "egresspublic")
HUB_HANDLERS = ("web", "app")


def _get_test_ports() -> list[int]:
    """Get allowed ports from LZA config."""
    allowed = lza_config().firewall_allowed_ports()
    assert allowed, "No allowed ports found in network firewall config"
    return allowed


def _get_blocked_test_ports() -> list[int]:
    """Get sample blocked ports for verifying firewall denies traffic."""
    allowed = set(_get_test_ports())
    blocked = [22, 80, 8080]
    ports = [p for p in blocked if p not in allowed]
    assert ports, f"All candidate blocked ports {blocked} are in the allowed set - cannot test blocking"
    return ports


def _tcp_probe_pairs(
    source_account: AccountUnderTest,
    source_names: tuple[str, ...],
    target_account: AccountUnderTest,
    target_names: tuple[str, ...],
    port: int,
) -> dict[str, CatsNetworkResult]:
    """TCP-probe every source->target handler pair, keyed 'source->target:port'."""
    results: dict[str, CatsNetworkResult] = {}
    for source_name, target_name in product(source_names, target_names):
        source_handler = getattr(source_account, source_name)
        target_handler = getattr(target_account, target_name)
        logger.info(f"Testing {source_name} -> {target_name}:{port}")
        result = source_handler.tcp_call(target_handler.ec2_dns_name, port)
        logger.info(f"  Result: {result}")
        results[f"{source_name}->{target_name}:{port}"] = result
    return results


def _expected_pairs(
    source_names: tuple[str, ...],
    target_names: tuple[str, ...],
    port: int,
    response: CatsNetworkResponse,
) -> dict[str, CatsNetworkResponse]:
    """Expected results for every source->target probe pair, keyed 'source->target:port'."""
    return {f"{source_name}->{target_name}:{port}": response for source_name, target_name in product(source_names, target_names)}


def _assert_internet_access_blocked(account: AccountUnderTest, target: str, port: int) -> None:
    """Probe every declared handler in the account toward the internet target and require every call to time out."""
    # arrange
    handlers = declared_network_handlers(account)
    expected = {f"{account.name}.{handler.name}->{target}:{port}": CatsNetworkResponse.TIMEOUT for handler in handlers}

    # act
    results = {f"{account.name}.{handler.name}->{target}:{port}": handler.http_call(target, port) for handler in handlers}

    # assert
    assert results == expected, f"Internet access should be BLOCKED from {account.name}"


@pytest.mark.parametrize("account_fixture_name", infrastructure_accounts())
@pytest.mark.parametrize("target", INTERNET_TARGETS)
@pytest.mark.parametrize("port", _get_test_ports())
@cats(standard_name=["LZA-NET-SEC-2"], test_suite="vpc", test_id="NS-1", evidence=Evidence.BEHAVIORAL)
def test_internet_access_blocking_infrastructure(
    account_fixture_name: str,
    target: str,
    port: int,
    get_account_fixture: GetAccountFixture,
) -> None:
    """LZA-NET-SEC-2: Validate internet access is blocked from infrastructure VPCs."""
    _assert_internet_access_blocked(get_account_fixture(account_fixture_name), target, port)


@cats_requires(Requirement.WORKLOAD_ACCOUNTS)
@pytest.mark.parametrize("account_fixture_name", workload_account_params())
@pytest.mark.parametrize("target", INTERNET_TARGETS)
@pytest.mark.parametrize("port", _get_test_ports())
@cats(standard_name=["LZA-NET-SEC-2"], test_suite="vpc", test_id="NS-1-workload", evidence=Evidence.BEHAVIORAL)
def test_internet_access_blocking_workload(
    account_fixture_name: str,
    target: str,
    port: int,
    get_account_fixture: GetAccountFixture,
) -> None:
    """LZA-NET-SEC-2: Validate internet access is blocked from workload VPCs."""
    _assert_internet_access_blocked(get_account_fixture(account_fixture_name), target, port)


@pytest.mark.parametrize("port", _get_test_ports())
@cats(standard_name=["LZA-NET-SEC-3"], test_suite="vpc", test_id="NS-3a-allow", evidence=Evidence.BEHAVIORAL)
def test_perimeter_to_hub_allowed(
    port: int,
    Perimeter_account: AccountUnderTest,
    SharedServices_account: AccountUnderTest,
) -> None:
    """LZA-NET-SEC-3: Validate perimeter->hub connectivity is ALLOWED on firewall ports."""
    # arrange
    expected = _expected_pairs(PERIMETER_HANDLERS, HUB_HANDLERS, port, CatsNetworkResponse.SUCCESS)

    # act
    results = _tcp_probe_pairs(Perimeter_account, PERIMETER_HANDLERS, SharedServices_account, HUB_HANDLERS, port)

    # assert
    assert results == expected, f"perimeter->hub port {port} should be ALLOWED"


@pytest.mark.parametrize("port", _get_blocked_test_ports())
@cats(standard_name=["LZA-NET-SEC-3"], test_suite="vpc", test_id="NS-3a-block", evidence=Evidence.BEHAVIORAL)
def test_perimeter_to_hub_blocked(
    port: int,
    Perimeter_account: AccountUnderTest,
    SharedServices_account: AccountUnderTest,
) -> None:
    """LZA-NET-SEC-3: Validate perimeter->hub connectivity is BLOCKED on non-firewall ports."""
    # arrange
    expected = _expected_pairs(PERIMETER_HANDLERS, HUB_HANDLERS, port, CatsNetworkResponse.TIMEOUT)

    # act
    results = _tcp_probe_pairs(Perimeter_account, PERIMETER_HANDLERS, SharedServices_account, HUB_HANDLERS, port)

    # assert
    assert results == expected, f"perimeter->hub port {port} should be BLOCKED"


@pytest.mark.parametrize("port", _get_test_ports())
@cats(standard_name=["LZA-NET-SEC-3"], test_suite="vpc", test_id="NS-3b-allow", evidence=Evidence.BEHAVIORAL)
def test_hub_to_perimeter_allowed(
    port: int,
    Perimeter_account: AccountUnderTest,
    SharedServices_account: AccountUnderTest,
) -> None:
    """LZA-NET-SEC-3: Validate hub->perimeter connectivity is ALLOWED on firewall ports."""
    # arrange
    expected = _expected_pairs(HUB_HANDLERS, PERIMETER_HANDLERS, port, CatsNetworkResponse.SUCCESS)

    # act
    results = _tcp_probe_pairs(SharedServices_account, HUB_HANDLERS, Perimeter_account, PERIMETER_HANDLERS, port)

    # assert
    assert results == expected, f"hub->perimeter port {port} should be ALLOWED"


@pytest.mark.parametrize("port", _get_blocked_test_ports())
@cats(standard_name=["LZA-NET-SEC-3"], test_suite="vpc", test_id="NS-3b-block", evidence=Evidence.BEHAVIORAL)
def test_hub_to_perimeter_blocked(
    port: int,
    Perimeter_account: AccountUnderTest,
    SharedServices_account: AccountUnderTest,
) -> None:
    """LZA-NET-SEC-3: Validate hub->perimeter connectivity is BLOCKED on non-firewall ports."""
    # arrange
    expected = _expected_pairs(HUB_HANDLERS, PERIMETER_HANDLERS, port, CatsNetworkResponse.TIMEOUT)

    # act
    results = _tcp_probe_pairs(SharedServices_account, HUB_HANDLERS, Perimeter_account, PERIMETER_HANDLERS, port)

    # assert
    assert results == expected, f"hub->perimeter port {port} should be BLOCKED"

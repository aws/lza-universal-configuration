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
CATS - Validate East-West Traffic Controls

Related LZA Controls and Tests:
- LZA-NET-SEC-1: Test network connectivity from workload accounts to SharedServices hub
  * test_workload_to_hub_connectivity
  * test_hub_to_workload_connectivity
  * test_workload_isolation

Every test requires ``workload-accounts`` (Requirement.WORKLOAD_ACCOUNTS): an unmodified
Universal Configuration has empty Workloads OUs and nothing to test from, so with no
account tagged ``workload`` these are recorded ``not_run`` rather than failed.
"""

from __future__ import annotations

import logging
from itertools import permutations
from typing import TYPE_CHECKING

import pytest
from cats import AccountUnderTest, CatsNetworkResponse, GetAccountFixture, cats, cats_requires

from cats_utils.accounts import workload_account_params, workload_accounts
from cats_utils.evidence import Evidence
from cats_utils.requirement import Requirement
from lza_utils.lza_config import lza_config

if TYPE_CHECKING:
    from _pytest.mark.structures import ParameterSet

logger = logging.getLogger(__name__)


def _get_test_ports() -> list[int]:
    """Get allowed ports from LZA config for connectivity tests."""
    allowed = lza_config().firewall_allowed_ports()
    assert allowed, "No allowed ports found in network firewall config"
    return allowed


def _workload_pair_params() -> list[tuple[str, str] | ParameterSet]:
    """Every ordered pair of workload accounts; the not_run placeholder when there are none; a worded skip when there is one.

    A single workload account is a complete deployment that cannot demonstrate
    spoke-to-spoke isolation, so EW-3 is skipped with that reason rather than failed.
    """
    accounts = workload_accounts()
    if not accounts:
        return [pytest.param("<no workload accounts>", "<no workload accounts>", id="none")]
    if len(accounts) == 1:
        reason = f"Isolation needs two workload accounts; only {accounts[0]} is tagged 'workload'"
        return [pytest.param(accounts[0], accounts[0], marks=pytest.mark.skip(reason=reason))]
    return list(permutations(accounts, 2))


@cats_requires(Requirement.WORKLOAD_ACCOUNTS)
@pytest.mark.parametrize("account_fixture_name", workload_account_params())
@pytest.mark.parametrize("port", _get_test_ports())
@cats(standard_name=["LZA-NET-SEC-1"], test_suite="vpc", test_id="EW-1", evidence=Evidence.BEHAVIORAL)
def test_workload_to_hub_connectivity(
    account_fixture_name: str,
    port: int,
    get_account_fixture: GetAccountFixture,
    SharedServices_account: AccountUnderTest,
) -> None:
    """LZA-NET-SEC-1: Test that workload VPCs can reach SharedServices hub on allowed ports."""
    # arrange
    workload = get_account_fixture(account_fixture_name)
    assert "app" in workload.available_network_targets, f"{account_fixture_name} has no 'app' handler"
    assert "app" in SharedServices_account.available_network_targets, "SharedServices has no 'app' handler"

    # act
    logger.info(f"Testing {workload.name}.app -> SharedServices.app:{port}")
    result = workload.app.tcp_call(SharedServices_account.app.ec2_dns_name, port)

    # assert
    logger.info(f"  Result: {result}")
    assert result == CatsNetworkResponse.SUCCESS, f"{workload.name}.app should reach SharedServices.app:{port}"


@cats_requires(Requirement.WORKLOAD_ACCOUNTS)
@pytest.mark.parametrize("account_fixture_name", workload_account_params())
@pytest.mark.parametrize("port", _get_test_ports())
@cats(standard_name=["LZA-NET-SEC-1"], test_suite="vpc", test_id="EW-2", evidence=Evidence.BEHAVIORAL)
def test_hub_to_workload_connectivity(
    account_fixture_name: str,
    port: int,
    get_account_fixture: GetAccountFixture,
    SharedServices_account: AccountUnderTest,
) -> None:
    """LZA-NET-SEC-1: Test that SharedServices hub can reach workload VPCs on allowed ports."""
    # arrange
    workload = get_account_fixture(account_fixture_name)
    assert "app" in workload.available_network_targets, f"{account_fixture_name} has no 'app' handler"
    assert "app" in SharedServices_account.available_network_targets, "SharedServices has no 'app' handler"

    # act
    logger.info(f"Testing SharedServices.app -> {workload.name}.app:{port}")
    result = SharedServices_account.app.tcp_call(workload.app.ec2_dns_name, port)

    # assert
    logger.info(f"  Result: {result}")
    assert result == CatsNetworkResponse.SUCCESS, f"SharedServices.app should reach {workload.name}.app:{port}"


@cats_requires(Requirement.WORKLOAD_ACCOUNTS)
@pytest.mark.parametrize(("source_fixture", "target_fixture"), _workload_pair_params())
@pytest.mark.parametrize("port", _get_test_ports())
@cats(standard_name=["LZA-NET-SEC-1"], test_suite="vpc", test_id="EW-3", evidence=Evidence.BEHAVIORAL)
def test_workload_isolation(
    source_fixture: str,
    target_fixture: str,
    port: int,
    get_account_fixture: GetAccountFixture,
) -> None:
    """LZA-NET-SEC-1: Test that workload VPCs cannot communicate directly with each other."""
    # arrange
    source = get_account_fixture(source_fixture)
    target = get_account_fixture(target_fixture)
    assert "app" in source.available_network_targets, f"{source_fixture} has no 'app' handler"
    assert "app" in target.available_network_targets, f"{target_fixture} has no 'app' handler"

    # act
    logger.info(f"Testing isolation: {source.name}.app -> {target.name}.app:{port}")
    result = source.app.tcp_call(target.app.ec2_dns_name, port)

    # assert
    logger.info(f"  Result: {result}")
    assert result == CatsNetworkResponse.TIMEOUT, (
        f"Isolation violated or path misclassified: {source.name}.app -> {target.name}.app:{port} returned {result}"
    )

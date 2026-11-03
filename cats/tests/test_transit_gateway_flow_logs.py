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
CATS - Transit Gateway Flow Logs Validation

Verifies Transit Gateway flow logs are enabled and configured as specified
in the LZA Universal Configuration network-config.yaml.

- LZA-NET-LOG-8: Transit Gateway flow logs enabled with CloudWatch Logs destination
"""

from __future__ import annotations

import logging

import pytest
from cats import GetAccountFixture, cats

from cats_utils.ec2 import get_active_flow_logs_by_resource_id, get_active_transit_gateways
from cats_utils.evidence import Evidence
from lza_utils.lza_config import (
    get_transit_gateway_account_region_combinations,
)

logger = logging.getLogger(__name__)


@pytest.mark.parametrize(
    ("account_fixture_name", "region"),
    get_transit_gateway_account_region_combinations(),
)
@cats(standard_name=["LZA-NET-LOG-8"], test_suite="transit_gateway", test_id="6", mutating=False, evidence=Evidence.CONFIGURATION)
def test_transit_gateway_flow_logs_enabled(
    account_fixture_name: str,
    region: str,
    get_account_fixture: GetAccountFixture,
) -> None:
    """Verify Transit Gateway flow logs are enabled with expected configuration."""
    # arrange
    account = get_account_fixture(account_fixture_name)

    # act — find active TGWs
    active_tgws = get_active_transit_gateways(account, region)
    assert active_tgws, f"No active Transit Gateways in {account_fixture_name} / {region}"

    # act — check flow logs for each TGW
    flow_logs_by_resource_id = get_active_flow_logs_by_resource_id(account, region)

    tgws_without_flow_logs: list[str] = []
    non_compliant: dict[str, list[str]] = {}

    for tgw in active_tgws:
        tgw_id = tgw["TransitGatewayId"]
        active_flow_logs = flow_logs_by_resource_id.get(tgw_id, [])

        if not active_flow_logs:
            tgws_without_flow_logs.append(tgw_id)
            continue

        # Validate flow log configuration
        issues: list[str] = []
        for fl in active_flow_logs:
            # Check destination is CloudWatch Logs
            if fl.get("LogDestinationType") != "cloud-watch-logs":
                issues.append(f"destination is '{fl.get('LogDestinationType')}', expected 'cloud-watch-logs'")

            # Check aggregation interval
            if fl.get("MaxAggregationInterval") != 60:
                issues.append(f"aggregation interval is {fl.get('MaxAggregationInterval')}, expected 60")

        if issues:
            non_compliant[tgw_id] = issues

    # assert
    assert tgws_without_flow_logs == [], f"Transit Gateways without flow logs: {tgws_without_flow_logs}"
    assert non_compliant == {}, f"Transit Gateway flow log configuration issues: {non_compliant}"

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
CATS - Validate Network Logging Configuration

Related LZA Controls:
- LZA-NET-LOG-4: VPC Flow Logs - Enabled on LZA VPCs
- LZA-NET-LOG-2: VPC Flow Logs - Sends VPC Flow Logs to CloudWatch Logs
- LZA-NET-LOG-1 / LZA-NET-LOG-3: VPC Flow Logs - Centralized in LogArchive via CloudWatch Logs
  subscription filters, which is the path to Amazon S3
- LZA-NET-LOG-6: Network Firewall Logs - Sends Network Firewall logs to Amazon S3
- LZA-NET-LOG-7: Network Firewall Logs - Sends Network Firewall Logs to CloudWatch Logs
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pytest
from cats import AccountUnderTest, GetAccountFixture, cats

from cats_utils.boto import DEFAULT_RETRY_CONFIG
from cats_utils.cats_cache import get_network_firewalls
from cats_utils.ec2 import get_active_flow_logs_by_resource_id, get_vpcs_by_name
from cats_utils.evidence import Evidence
from lza_utils.lza_config import (
    VpcInfo,
    get_network_firewall_account_region_combinations,
    get_vpc_account_region_combinations_with_flow_logs,
    get_vpc_names_with_flow_logs_for_account_region,
    get_vpcs_with_flow_logs,
)

if TYPE_CHECKING:
    from mypy_boto3_logs.client import CloudWatchLogsClient
    from mypy_boto3_logs.type_defs import SubscriptionFilterTypeDef

logger = logging.getLogger(__name__)


def _arn_account(arn: str) -> str:
    """Account field of an ARN (arn:partition:service:region:account:...), or the input unchanged if it is not an ARN."""
    parts = arn.split(":")
    return parts[4] if len(parts) > 4 else arn


def get_subscription_filters(logs_client: CloudWatchLogsClient, log_group_name: str) -> list[SubscriptionFilterTypeDef]:
    """All subscription filters on a log group. A missing log group raises ResourceNotFoundException."""
    paginator = logs_client.get_paginator("describe_subscription_filters")
    return [sub_filter for page in paginator.paginate(logGroupName=log_group_name) for sub_filter in page["subscriptionFilters"]]


@pytest.mark.parametrize(
    "vpc_info",
    get_vpcs_with_flow_logs(),
    ids=lambda v: f"{v['fixture_name']}-{v['region']}-{v['vpc_name']}",
)
@cats(standard_name=["LZA-NET-LOG-4"], test_suite="network", test_id="1", evidence=Evidence.CONFIGURATION)
def test_vpc_flow_logs_enabled(vpc_info: VpcInfo, get_account_fixture: GetAccountFixture) -> None:
    """Test that every LZA-configured VPC has an active flow log."""
    # arrange
    account_fixture_name = vpc_info["fixture_name"]
    region = vpc_info["region"]
    vpc_name = vpc_info["vpc_name"]
    account = get_account_fixture(account_fixture_name)

    # act
    deployed_vpcs = get_vpcs_by_name(account, region)
    assert vpc_name in deployed_vpcs, f"VPC {vpc_name} not found in {account_fixture_name} / {region}"
    vpc_id = deployed_vpcs[vpc_name]["VpcId"]
    flow_logs = get_active_flow_logs_by_resource_id(account, region).get(vpc_id, [])

    # assert
    assert flow_logs, f"VPC {vpc_name} ({vpc_id}) has no active flow logs"


@pytest.mark.parametrize(("account_fixture_name", "region"), get_vpc_account_region_combinations_with_flow_logs())
@cats(standard_name=["LZA-NET-LOG-2"], test_suite="network", test_id="2", evidence=Evidence.CONFIGURATION)
def test_vpc_flow_logs_cloudwatch_destination(account_fixture_name: str, region: str, get_account_fixture: GetAccountFixture) -> None:
    """Test that VPC Flow Logs are sent to CloudWatch Logs."""
    # arrange
    account = get_account_fixture(account_fixture_name)
    expected_vpc_names = get_vpc_names_with_flow_logs_for_account_region(account_fixture_name, region)
    assert expected_vpc_names, f"No VPCs configured for {account_fixture_name} in {region}"

    # act
    deployed_vpcs = get_vpcs_by_name(account, region)
    missing_vpcs = [vpc_name for vpc_name in expected_vpc_names if vpc_name not in deployed_vpcs]
    assert missing_vpcs == [], f"VPCs not found in {account_fixture_name} / {region}: {missing_vpcs}"

    flow_logs_by_resource_id = get_active_flow_logs_by_resource_id(account, region)

    vpcs_without_cloudwatch: dict[str, str] = {}
    for vpc_name in expected_vpc_names:
        vpc_id = deployed_vpcs[vpc_name]["VpcId"]
        flow_logs = flow_logs_by_resource_id.get(vpc_id, [])
        if not any(fl.get("LogDestinationType") == "cloud-watch-logs" for fl in flow_logs):
            vpcs_without_cloudwatch[vpc_name] = vpc_id

    # assert
    assert vpcs_without_cloudwatch == {}, f"VPCs missing CloudWatch destination: {vpcs_without_cloudwatch}"


@pytest.mark.parametrize(("account_fixture_name", "region"), get_vpc_account_region_combinations_with_flow_logs())
@cats(standard_name=["LZA-NET-LOG-1", "LZA-NET-LOG-3"], test_suite="network", test_id="3", evidence=Evidence.CONFIGURATION)
def test_vpc_flow_logs_centralized_in_logarchive(
    account_fixture_name: str,
    region: str,
    get_account_fixture: GetAccountFixture,
    LogArchive_account: AccountUnderTest,
) -> None:
    """Test that VPC Flow Logs are forwarded to LogArchive via CloudWatch Logs subscription filters.

    LZA delivers flow logs to a CloudWatch log group in each account and forwards
    them to the LogArchive account (and on to S3) with a subscription filter. The
    filter's destination account is what makes the logs "centralized" (NET-LOG-1)
    and is the path by which they reach S3 (NET-LOG-3).
    """
    # arrange
    account = get_account_fixture(account_fixture_name)
    logs_client = account.session.client("logs", region_name=region, config=DEFAULT_RETRY_CONFIG)
    expected_vpc_names = get_vpc_names_with_flow_logs_for_account_region(account_fixture_name, region)
    assert expected_vpc_names, f"No VPCs configured for {account_fixture_name} in {region}"
    expected_destination_account = LogArchive_account.account_id

    # act
    deployed_vpcs = get_vpcs_by_name(account, region)
    missing_vpcs = [vpc_name for vpc_name in expected_vpc_names if vpc_name not in deployed_vpcs]
    assert missing_vpcs == [], f"VPCs not found in {account_fixture_name} / {region}: {missing_vpcs}"

    flow_logs_by_resource_id = get_active_flow_logs_by_resource_id(account, region)

    vpcs_not_centralized: dict[str, str] = {}
    for vpc_name in expected_vpc_names:
        vpc_id = deployed_vpcs[vpc_name]["VpcId"]
        flow_logs = flow_logs_by_resource_id.get(vpc_id, [])
        cloudwatch_logs = [fl for fl in flow_logs if fl.get("LogDestinationType") == "cloud-watch-logs"]

        if not cloudwatch_logs:
            vpcs_not_centralized[vpc_name] = "No CloudWatch destination"
            continue

        # LZA creates one flow log per VPC; check the first CloudWatch destination
        log_group_name = cloudwatch_logs[0].get("LogGroupName")
        if not log_group_name:
            vpcs_not_centralized[vpc_name] = "No log group name"
            continue

        filters = get_subscription_filters(logs_client, log_group_name)
        if not filters:
            vpcs_not_centralized[vpc_name] = "No subscription filters"
            continue

        destination_accounts = sorted({_arn_account(sub_filter.get("destinationArn", "<no destinationArn>")) for sub_filter in filters})
        if destination_accounts != [expected_destination_account]:
            vpcs_not_centralized[vpc_name] = f"Subscription filters target {destination_accounts}, expected [{expected_destination_account}]"

    # assert
    assert vpcs_not_centralized == {}, f"VPC Flow Logs not centralized in LogArchive: {vpcs_not_centralized}"


@pytest.mark.parametrize(("account_fixture_name", "region"), get_network_firewall_account_region_combinations())
@cats(standard_name=["LZA-NET-LOG-6"], test_suite="network", test_id="6", evidence=Evidence.CONFIGURATION)
def test_network_firewall_logs_s3_destination(account_fixture_name: str, region: str, get_account_fixture: GetAccountFixture) -> None:
    """Test that Network Firewall logs are sent to S3 via CloudWatch Logs."""
    # arrange
    account = get_account_fixture(account_fixture_name)
    nfw_client = account.session.client("network-firewall", region_name=region, config=DEFAULT_RETRY_CONFIG)
    logs_client = account.session.client("logs", region_name=region, config=DEFAULT_RETRY_CONFIG)

    # act
    firewalls = get_network_firewalls(account, region)
    assert firewalls, f"No Network Firewalls found in {account_fixture_name} region {region}"

    firewalls_without_s3: dict[str, str] = {}
    for firewall in firewalls:
        firewall_name = firewall["FirewallName"]
        logging_config = nfw_client.describe_logging_configuration(FirewallName=firewall_name).get("LoggingConfiguration", {})

        log_destinations = logging_config.get("LogDestinationConfigs", [])
        cloudwatch_destinations = [ld for ld in log_destinations if ld.get("LogDestinationType") == "CloudWatchLogs"]

        if not cloudwatch_destinations:
            firewalls_without_s3[firewall_name] = "No CloudWatch destination"
            continue

        has_s3_forwarding = False
        for dest in cloudwatch_destinations:
            log_group_name = dest["LogDestination"]["logGroup"]
            # A missing log group raises ResourceNotFoundException here and fails the
            # test: the firewall claims to log to a group that does not exist.
            if get_subscription_filters(logs_client, log_group_name):
                has_s3_forwarding = True

        if not has_s3_forwarding:
            firewalls_without_s3[firewall_name] = "No S3 subscription filters"

    # assert
    assert firewalls_without_s3 == {}, f"Firewalls missing S3 logging: {firewalls_without_s3}"


@pytest.mark.parametrize(("account_fixture_name", "region"), get_network_firewall_account_region_combinations())
@cats(standard_name=["LZA-NET-LOG-7"], test_suite="network", test_id="7", evidence=Evidence.CONFIGURATION)
def test_network_firewall_logs_cloudwatch_destination(account_fixture_name: str, region: str, get_account_fixture: GetAccountFixture) -> None:
    """Test that Network Firewall logs are sent to CloudWatch Logs."""
    # arrange
    account = get_account_fixture(account_fixture_name)
    nfw_client = account.session.client("network-firewall", region_name=region, config=DEFAULT_RETRY_CONFIG)

    # act
    firewalls = get_network_firewalls(account, region)
    assert firewalls, f"No Network Firewalls found in {account_fixture_name} region {region}"

    firewalls_without_cloudwatch = {}
    for firewall in firewalls:
        firewall_name = firewall["FirewallName"]
        logging_config = nfw_client.describe_logging_configuration(FirewallName=firewall_name).get("LoggingConfiguration", {})

        log_destinations = logging_config.get("LogDestinationConfigs", [])
        cloudwatch_destinations = [ld for ld in log_destinations if ld.get("LogDestinationType") == "CloudWatchLogs"]

        if not cloudwatch_destinations:
            firewalls_without_cloudwatch[firewall_name] = "No CloudWatch destination"

    # assert
    assert firewalls_without_cloudwatch == {}, f"Firewalls missing CloudWatch logging: {firewalls_without_cloudwatch}"

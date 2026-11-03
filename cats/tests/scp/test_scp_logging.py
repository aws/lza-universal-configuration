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
CATS - SCP Enforcement: Logging Resource Protection

This test verifies:
- LZA-G-SCP-4: Restricts the modification of SNS topics created by LZA
- LZA-G-SCP-7: Restricts the modification of LZA CloudWatch Log Group settings
- LZA-G-SCP-8: Restricts the modification of LZA CloudWatch Log Stream settings
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pytest
from botocore.exceptions import ClientError
from cats import GetAccountFixture, cats

from cats_utils.accounts import non_management_accounts
from cats_utils.boto import DEFAULT_RETRY_CONFIG
from cats_utils.evidence import Evidence
from lza_utils.lza_config import lza_config

if TYPE_CHECKING:
    from mypy_boto3_logs.client import CloudWatchLogsClient

    from cats_types import LogArchiveAccount

logger = logging.getLogger(__name__)


def _protected_log_group_prefixes() -> list[str]:
    """Log-group name prefixes every guardrail SCP denies on: the aws-accelerator-* groups and the stage-stem Lambda groups.

    The core SCP covers /aws/lambda/<prefix>*; the deployment SCP only /aws/lambda/<prefix>-<stage stem>*.
    """
    return ["aws-accelerator-", *(f"/aws/lambda/{stage_prefix}" for stage_prefix in lza_config().stage_resource_prefixes)]


def _protected_log_groups(client: CloudWatchLogsClient) -> list[str]:
    """Names of the log groups under every protected prefix, in prefix order."""
    return [
        log_group["logGroupName"]
        for prefix in _protected_log_group_prefixes()
        for page in client.get_paginator("describe_log_groups").paginate(logGroupNamePrefix=prefix)
        for log_group in page["logGroups"]
    ]


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@cats(standard_name=["LZA-G-SCP-4"], test_suite="scp", test_id="4", mutating=True, evidence=Evidence.BEHAVIORAL)
def test_scp_blocks_sns_topic_modification(LogArchive_account: LogArchiveAccount, region: str) -> None:
    """Verify SCP denies modification of LZA SNS topics (aws-accelerator-* prefix)."""
    # arrange
    client = LogArchive_account.session.client("sns", region_name=region, config=DEFAULT_RETRY_CONFIG)

    # act - find an aws-accelerator- prefixed topic
    all_topics = [topic for page in client.get_paginator("list_topics").paginate() for topic in page["Topics"]]
    protected_topic_arns = [t["TopicArn"] for t in all_topics if t["TopicArn"].split(":")[-1].startswith("aws-accelerator-")]
    assert protected_topic_arns, f"No aws-accelerator- SNS topics found in LogArchive {region}"

    # assert - attempt to set attributes on the protected topic
    with pytest.raises(ClientError, match="explicit deny in a service control policy"):
        client.set_topic_attributes(TopicArn=protected_topic_arns[0], AttributeName="DisplayName", AttributeValue="cats-scp-test")


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@pytest.mark.parametrize("account_fixture_name", non_management_accounts())
@cats(standard_name=["LZA-G-SCP-7"], test_suite="scp", test_id="7", mutating=True, evidence=Evidence.BEHAVIORAL)
def test_scp_blocks_cloudwatch_log_group_modification(account_fixture_name: str, region: str, get_account_fixture: GetAccountFixture) -> None:
    """Verify SCP denies modification of LZA CloudWatch Log Groups."""
    # arrange
    account = get_account_fixture(account_fixture_name)
    client = account.session.client("logs", region_name=region, config=DEFAULT_RETRY_CONFIG)

    # act
    protected_log_groups = _protected_log_groups(client)
    assert protected_log_groups, f"No log groups under {_protected_log_group_prefixes()} found in {account_fixture_name} {region}"

    # assert - attempt to set retention policy
    with pytest.raises(ClientError, match="explicit deny in a service control policy"):
        client.put_retention_policy(logGroupName=protected_log_groups[0], retentionInDays=30)


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@pytest.mark.parametrize("account_fixture_name", non_management_accounts())
@cats(standard_name=["LZA-G-SCP-8"], test_suite="scp", test_id="8", mutating=True, evidence=Evidence.BEHAVIORAL)
def test_scp_blocks_cloudwatch_log_stream_deletion(account_fixture_name: str, region: str, get_account_fixture: GetAccountFixture) -> None:
    """Verify SCP denies deletion of log streams in LZA-protected log groups."""
    # arrange
    account = get_account_fixture(account_fixture_name)
    client = account.session.client("logs", region_name=region, config=DEFAULT_RETRY_CONFIG)

    # act
    protected_log_groups = _protected_log_groups(client)
    assert protected_log_groups, f"No log groups under {_protected_log_group_prefixes()} found in {account_fixture_name} {region}"

    # find a log stream in the first matching log group
    log_streams = client.describe_log_streams(logGroupName=protected_log_groups[0], limit=1)["logStreams"]
    assert log_streams, f"No log streams found in {protected_log_groups[0]} in {account_fixture_name} {region}"

    # assert - attempt to delete the log stream
    with pytest.raises(ClientError, match="explicit deny in a service control policy"):
        client.delete_log_stream(logGroupName=protected_log_groups[0], logStreamName=log_streams[0]["logStreamName"])

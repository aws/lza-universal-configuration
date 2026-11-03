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
CATS - SCP Enforcement: Kinesis and Firehose Protection

This test verifies:
- LZA-G-SCP-29: Restricts the modification of LZA Kinesis Data Stream settings
- LZA-G-SCP-30: Restricts the modification of LZA Kinesis Firehose settings
"""

from __future__ import annotations

import logging

import pytest
from botocore.exceptions import ClientError
from cats import GetAccountFixture, cats

from cats_utils.accounts import non_management_accounts
from cats_utils.boto import DEFAULT_RETRY_CONFIG
from cats_utils.evidence import Evidence
from lza_utils.lza_config import lza_config

logger = logging.getLogger(__name__)


@pytest.mark.parametrize("account_fixture_name", non_management_accounts())
@cats(standard_name=["LZA-G-SCP-29"], test_suite="scp", test_id="29a", mutating=True, evidence=Evidence.BEHAVIORAL)
def test_scp_blocks_kinesis_stream_creation(account_fixture_name: str, get_account_fixture: GetAccountFixture) -> None:
    """Verify SCP denies creation of Kinesis streams with accelerator prefix."""
    # arrange
    account = get_account_fixture(account_fixture_name)
    client = account.session.client("kinesis", region_name=lza_config().home_region, config=DEFAULT_RETRY_CONFIG)
    test_stream_name = f"{lza_config().accelerator_prefix}-cats-scp-test-stream"

    # act & assert
    with pytest.raises(ClientError, match="explicit deny in a service control policy"):
        client.create_stream(StreamName=test_stream_name, ShardCount=1)


@pytest.mark.parametrize("account_fixture_name", non_management_accounts())
@cats(standard_name=["LZA-G-SCP-29"], test_suite="scp", test_id="29b", mutating=True, evidence=Evidence.BEHAVIORAL)
def test_scp_blocks_kinesis_stream_deletion(account_fixture_name: str, get_account_fixture: GetAccountFixture) -> None:
    """Verify SCP denies deletion of Kinesis streams with accelerator prefix."""
    # arrange
    account = get_account_fixture(account_fixture_name)
    client = account.session.client("kinesis", region_name=lza_config().home_region, config=DEFAULT_RETRY_CONFIG)
    test_stream_name = f"{lza_config().accelerator_prefix}-cats-scp-test-stream"

    # act & assert
    with pytest.raises(ClientError, match="explicit deny in a service control policy"):
        client.delete_stream(StreamName=test_stream_name)


@pytest.mark.parametrize("account_fixture_name", non_management_accounts())
@cats(standard_name=["LZA-G-SCP-30"], test_suite="scp", test_id="30a", mutating=True, evidence=Evidence.BEHAVIORAL)
def test_scp_blocks_firehose_delivery_stream_creation(account_fixture_name: str, get_account_fixture: GetAccountFixture) -> None:
    """Verify SCP denies creation of Firehose delivery streams with accelerator prefix."""
    # arrange
    account = get_account_fixture(account_fixture_name)
    client = account.session.client("firehose", region_name=lza_config().home_region, config=DEFAULT_RETRY_CONFIG)
    test_stream_name = f"{lza_config().accelerator_prefix}-cats-scp-test-delivery-stream"

    # act & assert
    with pytest.raises(ClientError, match="explicit deny in a service control policy"):
        client.create_delivery_stream(DeliveryStreamName=test_stream_name, DeliveryStreamType="DirectPut")


@pytest.mark.parametrize("account_fixture_name", non_management_accounts())
@cats(standard_name=["LZA-G-SCP-30"], test_suite="scp", test_id="30b", mutating=True, evidence=Evidence.BEHAVIORAL)
def test_scp_blocks_firehose_delivery_stream_deletion(account_fixture_name: str, get_account_fixture: GetAccountFixture) -> None:
    """Verify SCP denies deletion of Firehose delivery streams with accelerator prefix."""
    # arrange
    account = get_account_fixture(account_fixture_name)
    client = account.session.client("firehose", region_name=lza_config().home_region, config=DEFAULT_RETRY_CONFIG)
    test_stream_name = f"{lza_config().accelerator_prefix}-cats-scp-test-delivery-stream"

    # act & assert
    with pytest.raises(ClientError, match="explicit deny in a service control policy"):
        client.delete_delivery_stream(DeliveryStreamName=test_stream_name)

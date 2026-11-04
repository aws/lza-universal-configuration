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
CATS - SNS Topic Configuration Validation

This test verifies:
- LZA-SEC-SNS-1: Security SNS topics exist in Management account with Lambda subscriptions
- LZA-SEC-SNS-2: Security SNS topics exist in LogArchive account
- LZA-SEC-SNS-3: SecurityHigh topic exists in Management account
- LZA-SEC-SNS-4: SecurityMedium topic exists in Management account
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from cats import cats

from cats_utils.boto import DEFAULT_RETRY_CONFIG
from cats_utils.cats_cache import get_sns_topic_arns
from cats_utils.evidence import Evidence
from lza_utils.lza_config import lza_config

if TYPE_CHECKING:
    from cats_types import LogArchiveAccount, ManagementAccount

logger = logging.getLogger(__name__)


def _expected_topic_names() -> list[str]:
    """Get expected SNS topic names from LZA config."""
    config = lza_config()
    sns_config = config.global_.sns_topics
    assert sns_config is not None, "snsTopics not configured in global config"
    return [f"{config.sns_topic_name_prefix}-{topic.name}" for topic in sns_config.topics]


@cats(standard_name=["LZA-SEC-SNS-1"], test_suite="sns", test_id="1", evidence=Evidence.CONFIGURATION)
def test_sns_topics_in_management_with_lambda(Management_account: ManagementAccount) -> None:
    """Verify security SNS topics exist in Management account with Lambda subscriptions."""
    # arrange
    config = lza_config()
    expected = _expected_topic_names()

    # act
    topic_arns = get_sns_topic_arns(Management_account, config.home_region)
    topic_names = [arn.split(":")[-1] for arn in topic_arns]
    missing = [t for t in expected if t not in topic_names]

    # assert
    assert missing == [], f"Missing SNS topics in Management account: {missing}"

    # verify lambda subscriptions
    client = Management_account.session.client("sns", region_name=config.home_region, config=DEFAULT_RETRY_CONFIG)
    no_lambda: list[str] = []
    for arn in topic_arns:
        name = arn.split(":")[-1]
        if name not in expected:
            continue
        subscriptions = [
            subscription
            for page in client.get_paginator("list_subscriptions_by_topic").paginate(TopicArn=arn)
            for subscription in page["Subscriptions"]
        ]
        if not any(subscription["Protocol"] == "lambda" for subscription in subscriptions):
            no_lambda.append(name)

    assert no_lambda == [], f"SNS topics without Lambda subscriptions: {no_lambda}"


@cats(standard_name=["LZA-SEC-SNS-2"], test_suite="sns", test_id="2", evidence=Evidence.CONFIGURATION)
def test_sns_topics_exist(LogArchive_account: LogArchiveAccount) -> None:
    """Verify all security SNS topics exist in LogArchive account."""
    # arrange
    config = lza_config()
    expected = _expected_topic_names()

    # act
    topic_arns = get_sns_topic_arns(LogArchive_account, config.home_region)
    topic_names = [arn.split(":")[-1] for arn in topic_arns]
    missing = [t for t in expected if t not in topic_names]

    # assert
    assert missing == [], f"Missing SNS topics: {missing}"


@cats(standard_name=["LZA-SEC-SNS-3"], test_suite="sns", test_id="3", evidence=Evidence.CONFIGURATION)
def test_sns_security_high_topic(Management_account: ManagementAccount) -> None:
    """Verify SecurityHigh SNS topic exists."""
    # arrange
    config = lza_config()
    expected_name = f"{config.sns_topic_name_prefix}-SecurityHigh"

    # act
    topic_arns = get_sns_topic_arns(Management_account, config.home_region)
    topic_names = [arn.split(":")[-1] for arn in topic_arns]

    # assert
    assert expected_name in topic_names, f"SecurityHigh topic '{expected_name}' not found. Topics: {topic_names}"


@cats(standard_name=["LZA-SEC-SNS-4"], test_suite="sns", test_id="4", evidence=Evidence.CONFIGURATION)
def test_sns_security_medium_topic(Management_account: ManagementAccount) -> None:
    """Verify SecurityMedium SNS topic exists."""
    # arrange
    config = lza_config()
    expected_name = f"{config.sns_topic_name_prefix}-SecurityMedium"

    # act
    topic_arns = get_sns_topic_arns(Management_account, config.home_region)
    topic_names = [arn.split(":")[-1] for arn in topic_arns]

    # assert
    assert expected_name in topic_names, f"SecurityMedium topic '{expected_name}' not found. Topics: {topic_names}"

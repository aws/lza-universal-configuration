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
CATS - Validate Route53 Query Logging Configuration

Related LZA Controls:
- LZA-NET-LOG-5: Route53 Query Logging - Enabled on LZA VPCs
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pytest
from cats import GetAccountFixture, cats
from cats.constants import get_account_fixture_names

from cats_utils.boto import DEFAULT_RETRY_CONFIG
from cats_utils.evidence import Evidence
from lza_utils.lza_config import get_vpcs_for_account_region, lza_config

if TYPE_CHECKING:
    from mypy_boto3_route53resolver.client import Route53ResolverClient

logger = logging.getLogger(__name__)

_account_region_with_vpcs = [
    (f, region) for f in get_account_fixture_names() for region in lza_config().enabled_regions if get_vpcs_for_account_region(f, region)
]


@pytest.mark.parametrize(("account_fixture_name", "region"), _account_region_with_vpcs)
@cats(standard_name=["LZA-NET-LOG-5"], test_suite="network", test_id="5", evidence=Evidence.CONFIGURATION)
def test_route53_query_logging_enabled(account_fixture_name: str, region: str, get_account_fixture: GetAccountFixture) -> None:
    """Test that Route53 Resolver query logging is associated with VPCs."""
    # arrange
    account = get_account_fixture(account_fixture_name)
    resolver_client: Route53ResolverClient = account.session.client("route53resolver", region_name=region, config=DEFAULT_RETRY_CONFIG)

    # act
    query_log_configs = [
        config for page in resolver_client.get_paginator("list_resolver_query_log_configs").paginate() for config in page["ResolverQueryLogConfigs"]
    ]

    # assert
    assert query_log_configs, f"No Route53 query log configs found in {account_fixture_name} region {region}"

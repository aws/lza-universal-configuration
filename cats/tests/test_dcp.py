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

"""CATS - VPC Block Public Access declarative policy enforcement.

Verifies the `<AcceleratorPrefix>-Vpc-Block-Public-Access-Guardrail` policy:

- LZA-G-DCP-1: VPC Block Public Access prevents unauthorized internet
              accessibility for VPC resources.

Enforcement is proved by the combination of two checks:

1. Mode is set to `block-bidirectional`
   (test_dcp_vpc_block_public_access_mode).
2. No exclusions exist that carve traffic out of the policy
   (test_dcp_vpc_block_public_access_no_exclusions).

Per AWS's published contract for VPC BPA, these two conditions together prove
that no internet traffic can ingress or egress via an IGW in the account and
region under test. Data-plane confirmation of the overall "no internet"
posture lives in test_vpc_north_south_traffic.py.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pytest
from cats import GetAccountFixture, cats

from cats_utils.boto import DEFAULT_RETRY_CONFIG
from cats_utils.evidence import Evidence
from lza_utils.lza_config import lza_config

if TYPE_CHECKING:
    from mypy_boto3_ec2 import EC2Client
    from mypy_boto3_ec2.type_defs import VpcBlockPublicAccessExclusionTypeDef

logger = logging.getLogger(__name__)

_VPC_BPA_GUARDRAIL_POLICY = f"{lza_config().accelerator_prefix}-Vpc-Block-Public-Access-Guardrail"
_EXPECTED_BLOCK_MODE = "block-bidirectional"


def _describe_all_vpc_bpa_exclusions(client: EC2Client) -> list[VpcBlockPublicAccessExclusionTypeDef]:
    """Return every VPC BPA exclusion. No native paginator, so walk NextToken.

    MaxResults is required by this API (one of MaxResults or ExclusionIds must
    be provided). 1000 is the documented maximum.
    """
    max_results = 1000
    response = client.describe_vpc_block_public_access_exclusions(MaxResults=max_results)
    exclusions: list[VpcBlockPublicAccessExclusionTypeDef] = list(response["VpcBlockPublicAccessExclusions"])
    next_token = response.get("NextToken")
    while next_token is not None:
        response = client.describe_vpc_block_public_access_exclusions(MaxResults=max_results, NextToken=next_token)
        exclusions.extend(response["VpcBlockPublicAccessExclusions"])
        next_token = response.get("NextToken")
    return exclusions


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@pytest.mark.parametrize(
    "account_fixture_name",
    lza_config().declarative_policy_targets(_VPC_BPA_GUARDRAIL_POLICY),
)
@cats(standard_name=["LZA-G-DCP-1"], test_suite="dcp", test_id="1", evidence=Evidence.CONFIGURATION)
def test_dcp_vpc_block_public_access_mode(
    account_fixture_name: str,
    region: str,
    get_account_fixture: GetAccountFixture,
) -> None:
    """VPC Block Public Access is configured to block bidirectional IGW traffic."""
    # arrange
    account = get_account_fixture(account_fixture_name)
    client = account.session.client("ec2", region_name=region, config=DEFAULT_RETRY_CONFIG)

    # act
    options = client.describe_vpc_block_public_access_options()["VpcBlockPublicAccessOptions"]
    actual_mode = options.get(
        "InternetGatewayBlockMode",
        "<InternetGatewayBlockMode not returned by API>",
    )

    # assert
    assert actual_mode == _EXPECTED_BLOCK_MODE, (
        f"VPC Block Public Access mode mismatch in {account_fixture_name} {region}: expected {_EXPECTED_BLOCK_MODE}, got {actual_mode}"
    )


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@pytest.mark.parametrize(
    "account_fixture_name",
    lza_config().declarative_policy_targets(_VPC_BPA_GUARDRAIL_POLICY),
)
@cats(standard_name=["LZA-G-DCP-1"], test_suite="dcp", test_id="2", evidence=Evidence.CONFIGURATION)
def test_dcp_vpc_block_public_access_no_exclusions(
    account_fixture_name: str,
    region: str,
    get_account_fixture: GetAccountFixture,
) -> None:
    """No VPC Block Public Access exclusions exist - nothing carves out the policy."""
    # arrange
    account = get_account_fixture(account_fixture_name)
    client = account.session.client("ec2", region_name=region, config=DEFAULT_RETRY_CONFIG)

    # act
    exclusions = _describe_all_vpc_bpa_exclusions(client)

    # assert
    assert exclusions == [], f"VPC Block Public Access exclusions present in {account_fixture_name} {region}: {exclusions}"

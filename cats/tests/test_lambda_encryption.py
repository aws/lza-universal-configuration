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
CATS - Lambda Encryption Validation

This test verifies:
- LZA-SEC-CRY-1: Lambda environment variables encrypted with KMS CMK
"""

from __future__ import annotations

import logging

import pytest
from cats import GetAccountFixture, cats
from cats.constants import get_account_fixture_names

from cats_utils.boto import DEFAULT_RETRY_CONFIG
from cats_utils.evidence import Evidence
from lza_utils.lza_config import lza_config

logger = logging.getLogger(__name__)


@pytest.mark.xfail(
    reason="Upstream LZA gap: CDK custom resource Lambdas missing CMK. https://github.com/awslabs/landing-zone-accelerator-on-aws/issues/846"
)
@pytest.mark.parametrize("region", lza_config().enabled_regions)
@pytest.mark.parametrize("account_fixture_name", get_account_fixture_names())
@cats(standard_name=["LZA-SEC-CRY-1"], test_suite="lambda", test_id="1", evidence=Evidence.CONFIGURATION)
def test_lambda_env_vars_encrypted_with_cmk(
    account_fixture_name: str,
    region: str,
    get_account_fixture: GetAccountFixture,
) -> None:
    """Verify LZA Lambda functions use KMS CMK for environment variable encryption."""
    # arrange
    config = lza_config()
    account = get_account_fixture(account_fixture_name)
    client = account.session.client("lambda", region_name=region, config=DEFAULT_RETRY_CONFIG)
    prefix = config.accelerator_prefix

    # act
    paginator = client.get_paginator("list_functions")
    lza_functions = [f for page in paginator.paginate() for f in page["Functions"] if prefix in f["FunctionName"]]

    assert lza_functions, f"No LZA Lambda functions (prefix '{prefix}') in {account.name} / {region}"

    # assert
    missing_cmk = [f["FunctionName"] for f in lza_functions if f.get("Environment", {}).get("Variables") and not f.get("KMSKeyArn")]
    assert missing_cmk == [], f"Lambda functions with env vars not using CMK: {missing_cmk}"

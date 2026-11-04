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
CATS - S3 Encryption Verification

This test verifies:
- LZA-SEC-CRY-2: Configures server-side encryption with SSE-S3 or Customer Managed KMS Key
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pytest
from cats import GetAccountFixture, cats
from cats.constants import get_account_fixture_names

from cats_utils.boto import DEFAULT_RETRY_CONFIG
from cats_utils.cats_cache import get_s3_buckets
from cats_utils.evidence import Evidence
from lza_utils.lza_config import lza_config

if TYPE_CHECKING:
    from mypy_boto3_s3.client import S3Client

logger = logging.getLogger(__name__)

# Buckets where the AWS API does not support SSE-KMS with CMK — AES256 is compliant.
# Log destination buckets: AWS requires AES256 for S3 access log destinations.
# CUR bucket: neither the CUR API nor LZA schema exposes an encryption parameter.
_BUCKET_PREFIX = lza_config().bucket_name_prefix
_AES256_ALLOWED_PREFIXES = (
    f"{_BUCKET_PREFIX}-s3-access-logs-",
    f"{_BUCKET_PREFIX}-s3-logs-",
    f"{_BUCKET_PREFIX}-elb-access-logs-",
    f"{_BUCKET_PREFIX}-assets-logs-",
    f"{_BUCKET_PREFIX}-cur-",
)


def _is_lza_bucket(bucket_name: str) -> bool:
    return bucket_name.startswith(f"{_BUCKET_PREFIX}-")


def _get_encryption_algorithm(s3_client: S3Client, bucket_name: str) -> str | None:
    rules = s3_client.get_bucket_encryption(Bucket=bucket_name)["ServerSideEncryptionConfiguration"]["Rules"]
    if not rules:
        return None
    return rules[0]["ApplyServerSideEncryptionByDefault"]["SSEAlgorithm"]


def _has_cmk(s3_client: S3Client, bucket_name: str) -> bool:
    rules = s3_client.get_bucket_encryption(Bucket=bucket_name)["ServerSideEncryptionConfiguration"]["Rules"]
    return "KMSMasterKeyID" in rules[0].get("ApplyServerSideEncryptionByDefault", {})


@pytest.mark.parametrize("account_fixture_name", get_account_fixture_names())
@cats(standard_name=["LZA-SEC-CRY-2"], test_suite="encryption", test_id="1", evidence=Evidence.CONFIGURATION)
def test_s3_buckets_have_server_side_encryption(account_fixture_name: str, get_account_fixture: GetAccountFixture) -> None:
    """Verify LZA S3 buckets use SSE-KMS with CMK, except log destinations which must use AES256."""
    account = get_account_fixture(account_fixture_name)
    # S3 list_buckets is global; bucket operations route to the correct region automatically.
    s3_client: S3Client = account.session.client("s3", config=DEFAULT_RETRY_CONFIG)

    bucket_names = get_s3_buckets(account)
    assert bucket_names, f"No S3 buckets found in {account_fixture_name}"

    non_compliant: dict[str, str] = {}
    for name in bucket_names:
        if not _is_lza_bucket(name):
            continue

        algorithm = _get_encryption_algorithm(s3_client, name)
        if algorithm is None:
            non_compliant[name] = "no encryption rules"
        elif name.startswith(_AES256_ALLOWED_PREFIXES):
            if algorithm != "AES256":
                non_compliant[name] = f"expected AES256 (API constraint), got {algorithm}"
        elif algorithm != "aws:kms":
            non_compliant[name] = f"expected SSE-KMS (aws:kms), got {algorithm}"
        elif not _has_cmk(s3_client, name):
            non_compliant[name] = "SSE-KMS but no CMK configured"

    assert non_compliant == {}, f"S3 encryption issues in {account_fixture_name}: {non_compliant}"

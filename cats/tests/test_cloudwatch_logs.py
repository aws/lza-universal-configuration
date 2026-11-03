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
CATS - Validate CloudWatch Logs

Related LZA Controls and Tests:
- LZA-SEC-CWL-1: CloudWatch log groups have retention set to configured days
  * test_cloudwatch_logs_retention
  * test_cloudwatch_logs_retention_bootstrap_log_groups
- LZA-SEC-CWL-2: Dynamic partitioning for CloudWatch Logs
  * test_cloudwatch_logs_dynamic_partitioning
- LZA-SEC-CWL-3: Subscription filters for CloudWatch logs
  * test_cloudwatch_logs_subscription_filters
  * test_cloudwatch_logs_subscription_filters_bootstrap_log_groups
- LZA-SEC-CWL-4: Customer-managed KMS Key (CMK) to encrypt CloudWatch logs
  * test_cloudwatch_logs_cmk_encryption
  * test_cloudwatch_logs_cmk_encryption_bootstrap_log_groups

LZA applies retention, encryption and subscription settings to log groups via
an event-driven mechanism deployed by its Logging stack. Log groups created at
or before that stage escape it - LZA issue #875. This file therefore splits
each check into two tests:

- Strict tests (test IDs 1, 3, 4) cover "managed" log groups: those created
  after the Logging stack deployed, which LZA configures reliably. These must
  pass in every account/region. A failure here is a real regression in the
  landing zone and must be investigated.

- Known-gap tests (test IDs 1b, 3b, 4b) cover "bootstrap" log groups: those
  created at or before the Logging stage (classified by
  lza_utils.log_groups.is_lza_bootstrap_log_group). Each runs once, checking
  all accounts and regions together, and is marked xfail:

  * XFAIL is the expected outcome while LZA issue #875 is open. It means the
    known defect manifested somewhere. No action is required; the captured
    assertion lists every affected log group as evidence for the compliance
    workbook caveat.
  * XPASS means every bootstrap log group in this environment is currently
    compliant (upstream fix, manual remediation, or a lucky deployment).
    Still no action: do NOT remove the xfail marker until #875 is fixed in
    the deployed LZA version, because any LZA pipeline run can recreate
    non-compliant log groups.
  * The tests aggregate all accounts/regions because the defect is a
    per-log-group race: per-account results would flip between pass and fail
    across deployments, telling the reader nothing.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING

import pytest
from cats import GetAccountFixture, cats
from cats.constants import get_account_fixture_names

from cats_utils.boto import DEFAULT_RETRY_CONFIG
from cats_utils.cats_cache import get_cloudwatch_log_groups
from cats_utils.evidence import Evidence
from lza_utils.log_groups import (
    collect_bootstrap_log_groups,
    expected_subscription_destination,
    get_lza_managed_log_groups,
)
from lza_utils.lza_config import lza_config

if TYPE_CHECKING:
    from cats_types import LogArchiveAccount

_BOOTSTRAP_GAP_XFAIL_REASON = """\
Expected failure while LZA issue #875 is open: log groups created at or before the \
Logging stage miss LZA's event-driven retention/encryption/subscription config, or keep \
the installer's retention default instead of the configured value. \
XFAIL = the known defect manifested; no action required, the assertion output lists the \
affected log groups as evidence. \
XPASS = all affected log groups are currently compliant; still no action - keep this \
marker until the fix lands in the deployed LZA version, as any pipeline run can \
reintroduce misses. \
https://github.com/awslabs/landing-zone-accelerator-on-aws/issues/875"""


# Cap on collection threads for the subscription bootstrap test's per-account check.
_MAX_COLLECTION_WORKERS = 16


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@pytest.mark.parametrize("account_fixture_name", get_account_fixture_names())
@cats(standard_name=["LZA-SEC-CWL-1"], test_suite="cloudwatch", test_id="1", evidence=Evidence.CONFIGURATION)
def test_cloudwatch_logs_retention(
    account_fixture_name: str,
    region: str,
    get_account_fixture: GetAccountFixture,
) -> None:
    """Test that LZA-managed CloudWatch log groups have retention set to configured days."""
    # arrange
    expected_retention_days = lza_config().log_retention_days
    account = get_account_fixture(account_fixture_name)

    # act
    managed_log_groups = get_lza_managed_log_groups(get_cloudwatch_log_groups(account, region))
    assert managed_log_groups != {}

    # assert - absent retentionInDays means the log group never expires
    incorrect_log_group_retention_days: dict[str, int | str] = {
        name: log_group.get("retentionInDays", "Never expire")
        for name, log_group in managed_log_groups.items()
        if log_group.get("retentionInDays") != expected_retention_days
    }
    assert incorrect_log_group_retention_days == {}, (
        f"Incorrect retention (expected {expected_retention_days} days): {incorrect_log_group_retention_days}"
    )


@pytest.mark.xfail(reason=_BOOTSTRAP_GAP_XFAIL_REASON)
@cats(standard_name=["LZA-SEC-CWL-1"], test_suite="cloudwatch", test_id="1b", evidence=Evidence.CONFIGURATION)
def test_cloudwatch_logs_retention_bootstrap_log_groups(get_account_fixture: GetAccountFixture) -> None:
    """Test that LZA bootstrap-stage log groups have retention set to configured days (known LZA defect).

    Expected to XFAIL while LZA issue #875 is open - see the module docstring
    for how to interpret XFAIL vs XPASS.
    """
    # arrange
    expected_retention_days = lza_config().log_retention_days

    # act - check all accounts and regions in one test: see module docstring for why
    bootstrap_log_groups = collect_bootstrap_log_groups({name: get_account_fixture(name) for name in get_account_fixture_names()})
    assert bootstrap_log_groups != {}, "No LZA bootstrap log groups found in any account/region"

    # assert
    incorrect_log_group_retention_days: dict[str, int | str] = {
        f"{account_fixture_name}:{region}:{name}": log_group.get("retentionInDays", "Never expire")
        for (account_fixture_name, region, name), log_group in bootstrap_log_groups.items()
        if log_group.get("retentionInDays") != expected_retention_days
    }
    assert incorrect_log_group_retention_days == {}, (
        f"Incorrect retention (expected {expected_retention_days} days): {incorrect_log_group_retention_days}"
    )


@cats(standard_name=["LZA-SEC-CWL-2"], test_suite="cloudwatch", test_id="2", evidence=Evidence.CONFIGURATION)
def test_cloudwatch_logs_dynamic_partitioning(
    LogArchive_account: LogArchiveAccount,
) -> None:
    """Test that verifies CloudWatch Logs have dynamic partitioning configured correctly in the LogArchive account.

    This test validates that the infrastructure for dynamic partitioning exists:
    - Lambda function for processing Firehose records
    - Kinesis stream for log data
    - Required environment variables for configuration
    """
    # arrange
    lambda_function_name = f"{lza_config().accelerator_prefix}-FirehoseRecordsProcessor"
    required_env_vars = ["DynamicS3LogPartitioningByAccountId", "DynamicS3LogPartitioningMapping", "KinesisStreamArn"]

    lambda_client = LogArchive_account.session.client("lambda", config=DEFAULT_RETRY_CONFIG)
    kinesis_client = LogArchive_account.session.client("kinesis", config=DEFAULT_RETRY_CONFIG)

    # act
    lambda_response = lambda_client.get_function(FunctionName=lambda_function_name)
    env_vars = lambda_response["Configuration"].get("Environment", {}).get("Variables", {})

    # assert
    missing_vars = [var for var in required_env_vars if var not in env_vars]
    assert missing_vars == [], f"Lambda {lambda_function_name} missing env vars: {missing_vars}"

    kinesis_stream_arn = env_vars["KinesisStreamArn"]
    kinesis_response = kinesis_client.describe_stream(StreamARN=kinesis_stream_arn)
    stream_status = kinesis_response["StreamDescription"]["StreamStatus"]
    assert stream_status == "ACTIVE", f"Kinesis stream {kinesis_stream_arn} status: {stream_status}"


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@pytest.mark.parametrize("account_fixture_name", get_account_fixture_names())
@cats(standard_name=["LZA-SEC-CWL-3"], test_suite="cloudwatch", test_id="3", evidence=Evidence.CONFIGURATION)
def test_cloudwatch_logs_subscription_filters(
    account_fixture_name: str,
    region: str,
    get_account_fixture: GetAccountFixture,
    LogArchive_account: LogArchiveAccount,
) -> None:
    """Test that LZA-managed log groups forward to the LogArchive CloudWatchToS3 destination."""
    # arrange
    account = get_account_fixture(account_fixture_name)
    logs_client = account.session.client("logs", region_name=region, config=DEFAULT_RETRY_CONFIG)

    managed_log_groups = get_lza_managed_log_groups(get_cloudwatch_log_groups(account, region))
    assert managed_log_groups != {}

    expected_destination = expected_subscription_destination(region, LogArchive_account.account_id)

    # act & assert
    incorrect_destinations: dict[str, list[str]] = {}
    for name in managed_log_groups:
        destinations = [
            subscription_filter.get("destinationArn", "<no destinationArn>")
            for page in logs_client.get_paginator("describe_subscription_filters").paginate(logGroupName=name)
            for subscription_filter in page["subscriptionFilters"]
        ]
        if destinations != [expected_destination]:
            incorrect_destinations[name] = destinations

    assert incorrect_destinations == {}, f"Log groups not forwarding to {expected_destination}: {incorrect_destinations}"


@pytest.mark.xfail(reason=_BOOTSTRAP_GAP_XFAIL_REASON)
@cats(standard_name=["LZA-SEC-CWL-3"], test_suite="cloudwatch", test_id="3b", evidence=Evidence.CONFIGURATION)
def test_cloudwatch_logs_subscription_filters_bootstrap_log_groups(
    get_account_fixture: GetAccountFixture,
    LogArchive_account: LogArchiveAccount,
) -> None:
    """Test that LZA bootstrap-stage log groups forward to the LogArchive destination (known LZA defect).

    Expected to XFAIL while LZA issue #875 is open - see the module docstring
    for how to interpret XFAIL vs XPASS.
    """
    # arrange - the FirehoseRecordsProcessor log group is excluded by design: it implements the
    # forwarding pipeline, so subscribing its own log group to it would be recursive
    firehose_processor_log_group = f"/aws/lambda/{lza_config().accelerator_prefix}-FirehoseRecordsProcessor"

    # act - collect once, then check subscription filters for each group
    accounts = {name: get_account_fixture(name) for name in get_account_fixture_names()}
    bootstrap_log_groups = collect_bootstrap_log_groups(accounts)
    assert bootstrap_log_groups != {}, "No LZA bootstrap log groups found in any account/region"

    def check_account(account_fixture_name: str) -> dict[str, list[str]]:
        account = accounts[account_fixture_name]
        account_incorrect: dict[str, list[str]] = {}
        # Group collected names by region to create one client per region
        regions: dict[str, list[str]] = {}
        for (acct, region, name), _ in bootstrap_log_groups.items():
            if acct == account_fixture_name and name != firehose_processor_log_group:
                regions.setdefault(region, []).append(name)
        for region, names in regions.items():
            logs_client = account.session.client("logs", region_name=region, config=DEFAULT_RETRY_CONFIG)
            expected_destination = expected_subscription_destination(region, LogArchive_account.account_id)
            for name in names:
                destinations = [
                    subscription_filter.get("destinationArn", "<no destinationArn>")
                    for page in logs_client.get_paginator("describe_subscription_filters").paginate(logGroupName=name)
                    for subscription_filter in page["subscriptionFilters"]
                ]
                if destinations != [expected_destination]:
                    account_incorrect[f"{account_fixture_name}:{region}:{name}"] = destinations
        return account_incorrect

    incorrect_destinations: dict[str, list[str]] = {}
    with ThreadPoolExecutor(max_workers=min(len(accounts), _MAX_COLLECTION_WORKERS)) as pool:
        for account_result in pool.map(check_account, accounts.keys()):
            incorrect_destinations.update(account_result)

    # assert
    assert incorrect_destinations == {}, f"Log groups not forwarding to the LogArchive CloudWatchToS3 destination: {incorrect_destinations}"


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@pytest.mark.parametrize("account_fixture_name", get_account_fixture_names())
@cats(standard_name=["LZA-SEC-CWL-4"], test_suite="cloudwatch", test_id="4", evidence=Evidence.CONFIGURATION)
def test_cloudwatch_logs_cmk_encryption(
    account_fixture_name: str,
    region: str,
    get_account_fixture: GetAccountFixture,
) -> None:
    """Test that LZA-managed log groups are encrypted with customer-managed KMS keys."""
    # arrange
    account = get_account_fixture(account_fixture_name)
    kms_client = account.session.client("kms", region_name=region, config=DEFAULT_RETRY_CONFIG)

    managed_log_groups = get_lza_managed_log_groups(get_cloudwatch_log_groups(account, region))
    assert managed_log_groups != {}

    # act & assert
    key_managers: dict[str, str] = {}
    non_compliant_log_groups: dict[str, str] = {}
    for log_group_name, log_group in managed_log_groups.items():
        kms_key_id = log_group.get("kmsKeyId")
        if kms_key_id is None:
            non_compliant_log_groups[log_group_name] = "NONE"
            continue
        if kms_key_id not in key_managers:
            key_managers[kms_key_id] = kms_client.describe_key(KeyId=kms_key_id)["KeyMetadata"].get("KeyManager", "<KeyManager not returned by API>")
        if key_managers[kms_key_id] != "CUSTOMER":
            non_compliant_log_groups[log_group_name] = key_managers[kms_key_id]

    assert non_compliant_log_groups == {}, f"Log groups not using customer-managed KMS: {non_compliant_log_groups}"


@pytest.mark.xfail(reason=_BOOTSTRAP_GAP_XFAIL_REASON)
@cats(standard_name=["LZA-SEC-CWL-4"], test_suite="cloudwatch", test_id="4b", evidence=Evidence.CONFIGURATION)
def test_cloudwatch_logs_cmk_encryption_bootstrap_log_groups(get_account_fixture: GetAccountFixture) -> None:
    """Test that LZA bootstrap-stage log groups use customer-managed KMS keys (known LZA defect).

    Expected to XFAIL while LZA issue #875 is open - see the module docstring
    for how to interpret XFAIL vs XPASS.
    """
    # act - check all accounts and regions in one test: see module docstring for why
    bootstrap_log_groups = collect_bootstrap_log_groups({name: get_account_fixture(name) for name in get_account_fixture_names()})
    assert bootstrap_log_groups != {}, "No LZA bootstrap log groups found in any account/region"

    key_managers: dict[str, str] = {}
    non_compliant_log_groups: dict[str, str] = {}
    for (account_fixture_name, region, name), log_group in bootstrap_log_groups.items():
        kms_key_id = log_group.get("kmsKeyId")
        if kms_key_id is None:
            non_compliant_log_groups[f"{account_fixture_name}:{region}:{name}"] = "NONE"
            continue
        if kms_key_id not in key_managers:
            kms_client = get_account_fixture(account_fixture_name).session.client("kms", region_name=region, config=DEFAULT_RETRY_CONFIG)
            key_managers[kms_key_id] = kms_client.describe_key(KeyId=kms_key_id)["KeyMetadata"].get("KeyManager", "<KeyManager not returned by API>")
        if key_managers[kms_key_id] != "CUSTOMER":
            non_compliant_log_groups[f"{account_fixture_name}:{region}:{name}"] = key_managers[kms_key_id]

    # assert
    assert non_compliant_log_groups == {}, f"Log groups not using customer-managed KMS: {non_compliant_log_groups}"

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

"""LZA CloudWatch log group classification and collection.

Pure filters over already-fetched log group data (see
cats_utils.cats_cache.get_cloudwatch_log_groups for the cached fetch). These
encode LZA domain knowledge: which log groups belong to LZA, and which of
those the event-driven config mechanism predictably manages versus the
bootstrap-stage class affected by LZA issue #875.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING

from cats.config import Settings

from cats_utils.cats_cache import get_cloudwatch_log_groups
from lza_utils.lza_config import lza_config

if TYPE_CHECKING:
    from collections.abc import Mapping

    from mypy_boto3_logs.type_defs import LogGroupTypeDef

    from cats_types import CatsAccountProtocol

# Cap on collection threads: each thread owns a boto3 session (memory, sockets) and
# writes to the SQLite-backed diskcache on cold runs, so one-thread-per-account stops
# scaling well beyond this when many accounts are under test.
_MAX_COLLECTION_WORKERS = 16


def get_lza_log_groups(log_groups: dict[str, LogGroupTypeDef]) -> dict[str, LogGroupTypeDef]:
    """Filter log groups to only those belonging to LZA."""
    # TODO can we avoid hardcoding these? Is this an exhaustive list?
    # TODO are these all prefix patterns? "in" vs "startswith" - have assumed they are prefixes
    accelerator_prefix = lza_config().accelerator_prefix
    patterns = {"aws-accelerator-", "/aws/lambda/awsaccelerator", "/awsaccelerator-", "awsaccelerator-", accelerator_prefix.lower()}

    return {name: data for name, data in log_groups.items() if any(p in name.lower() for p in patterns)}


# LZA stacks whose log groups exist at or before the Logging stage deploys the
# event-driven mechanism that applies retention, encryption and subscription
# settings. LZA cannot reliably configure these log groups: they are created
# before the mechanism exists (bootstrap stacks), concurrently with it
# (LoggingStack's own custom resources - a race, see LZA issue #875), or with
# the installer's own retention default instead of the global config value.
# OrganizationsStack runs after Logging but was observed with unmanaged groups,
# so it is classified as bootstrap. Verified against a full 9-account x
# 5-region sweep (2026-08-04): every retention/encryption/subscription finding
# fell inside this class; all 1,315 log groups outside it were compliant.
# InstallerContainerStack is the container deployment's installer (LZA as an
# ECS task in the LzaDeployment account); its Lambda log group carries the
# installer's own retention default like InstallerStack's.
# https://github.com/awslabs/landing-zone-accelerator-on-aws/issues/875
_LZA_BOOTSTRAP_STACK_NAMES = (
    "InstallerStack",
    "InstallerContainerStack",
    "PipelineStack",
    "DiagnosticsPackStack",
    "PrepareStack",
    "AccountsStack",
    "OrganizationsStack",
    "LoggingStack",
)

# LoggingStack creates the Firehose delivery stream's own log group in LogArchive
# (constructs/lib/aws-firehose/cloudwatch-to-s3-firehose.ts, hardcoded prefix) in the
# same deployment as the subscription mechanism, so it is in the #875 race class
# although it is not a Lambda log group.
_LZA_FIREHOSE_LOG_GROUP_PREFIX = "/accelerator/logs/firehose/"


def is_lza_bootstrap_log_group(log_group_name: str) -> bool:
    """Return True if a log group belongs to LZA's bootstrap/solution machinery.

    CloudFormation truncates stack names inside lambda log group names
    (e.g. "AWSAccelerator-LoggingSta-..."), so the stack fragment is matched
    as a prefix of the full stack name.
    """
    accelerator_prefix = lza_config().accelerator_prefix
    if log_group_name.startswith(f"/aws/codebuild/{accelerator_prefix}"):
        return True
    if log_group_name == f"/aws/lambda/{accelerator_prefix}-FirehoseRecordsProcessor":
        return True
    if log_group_name.startswith(f"{_LZA_FIREHOSE_LOG_GROUP_PREFIX}{accelerator_prefix}-LoggingStack-"):
        return True
    lambda_prefix = f"/aws/lambda/{accelerator_prefix}-"
    if not log_group_name.startswith(lambda_prefix):
        return False
    stack_fragment = log_group_name.removeprefix(lambda_prefix).split("-", 1)[0]
    return any(stack_name.startswith(stack_fragment) for stack_name in _LZA_BOOTSTRAP_STACK_NAMES)


def get_lza_managed_log_groups(log_groups: dict[str, LogGroupTypeDef]) -> dict[str, LogGroupTypeDef]:
    """LZA log groups the event-driven config mechanism predictably manages."""
    return {name: data for name, data in get_lza_log_groups(log_groups).items() if not is_lza_bootstrap_log_group(name)}


def get_lza_bootstrap_log_groups(log_groups: dict[str, LogGroupTypeDef]) -> dict[str, LogGroupTypeDef]:
    """LZA log groups created at or before the Logging stage (known-gap class)."""
    return {name: data for name, data in get_lza_log_groups(log_groups).items() if is_lza_bootstrap_log_group(name)}


def collect_bootstrap_log_groups(
    accounts: Mapping[str, CatsAccountProtocol],
) -> dict[tuple[str, str, str], LogGroupTypeDef]:
    """Bootstrap-class log groups from every account and region under test.

    Keyed (account_fixture_name, region, log_group_name). The known-gap tests
    each run as a single test on one pytest-xdist worker, so the walk over
    accounts is parallelized with threads here rather than relying on pytest
    workers.
    """

    def fetch_account(item: tuple[str, CatsAccountProtocol]) -> dict[tuple[str, str, str], LogGroupTypeDef]:
        account_fixture_name, account = item
        return {
            (account_fixture_name, region, name): log_group
            for region in lza_config().enabled_regions
            for name, log_group in get_lza_bootstrap_log_groups(get_cloudwatch_log_groups(account, region)).items()
        }

    collected: dict[tuple[str, str, str], LogGroupTypeDef] = {}
    with ThreadPoolExecutor(max_workers=min(len(accounts), _MAX_COLLECTION_WORKERS)) as pool:
        for account_result in pool.map(fetch_account, accounts.items()):
            collected.update(account_result)
    return collected


def expected_subscription_destination(region: str, logarchive_account_id: str) -> str:
    """The expected CloudWatchToS3 logs destination ARN in the LogArchive account."""
    partition = Settings().cats_deployment_settings.partition
    return f"arn:{partition}:logs:{region}:{logarchive_account_id}:destination:{lza_config().accelerator_prefix}CloudWatchToS3"

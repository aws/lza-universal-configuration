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
CATS Caching Utilities

This module provides cross-process caching for AWS API calls using diskcache,
enabling cache sharing across pytest-xdist workers.

Key Principles:
1. NEVER cache the account fixture itself
2. Cache only the AWS API response data (config rules, IAM roles, etc.)
3. Use diskcache for cross-process sharing with xdist

Design Pattern:
- Tests call get_account_fixture() directly (registers account)
- Tests use cached data retrieval functions (not fixtures)
- Cache functions take the account fixture as input
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, cast

from diskcache import Cache  # type: ignore[import-untyped]

from cats_utils.boto import DEFAULT_RETRY_CONFIG
from lza_utils.lza_config import lza_config

if TYPE_CHECKING:
    from collections.abc import Callable

    from mypy_boto3_cloudtrail.type_defs import TrailTypeDef
    from mypy_boto3_config.type_defs import ConfigRuleOutputTypeDef, RemediationConfigurationOutputTypeDef
    from mypy_boto3_controltower.type_defs import EnabledBaselineSummaryTypeDef, EnabledControlSummaryTypeDef
    from mypy_boto3_guardduty.type_defs import GetDetectorResponseTypeDef
    from mypy_boto3_iam.type_defs import PasswordPolicyTypeDef, RoleTypeDef
    from mypy_boto3_logs.type_defs import LogGroupTypeDef
    from mypy_boto3_macie2.type_defs import GetMacieSessionResponseTypeDef
    from mypy_boto3_network_firewall.type_defs import FirewallMetadataTypeDef
    from mypy_boto3_organizations.client import OrganizationsClient
    from mypy_boto3_organizations.type_defs import OrganizationTypeDef, PolicySummaryTypeDef
    from mypy_boto3_s3.type_defs import LifecycleRuleOutputTypeDef
    from mypy_boto3_securityhub.type_defs import StandardsSubscriptionTypeDef

    from cats_types import CatsAccountProtocol

logger = logging.getLogger(__name__)

_cache = Cache(".pytest_cache/cats_diskcache")


def cached[T](cache_key: str, fetch: Callable[[], T]) -> T:
    """Fetch from cache or call fetch() and cache the result."""
    cached_value = _cache.get(cache_key)
    if cached_value is not None:
        logger.info(f"[CACHE HIT] {cache_key}")
        return cast("T", cached_value)

    logger.info(f"[CACHE MISS] {cache_key}")
    result = fetch()
    _cache.set(cache_key, result)
    return result


# ============================================================================
# Config Rules Caching
# ============================================================================


def get_config_rules(account_fixture: CatsAccountProtocol, region: str) -> dict[str, ConfigRuleOutputTypeDef]:
    """Get AWS Config Rules for an account in a region, using cache when available."""

    def fetch() -> dict[str, ConfigRuleOutputTypeDef]:
        client = account_fixture.session.client("config", region_name=region, config=DEFAULT_RETRY_CONFIG)
        paginator = client.get_paginator("describe_config_rules")
        return {rule["ConfigRuleName"]: rule for page in paginator.paginate() for rule in page["ConfigRules"]}

    return cached(f"config_rules:{account_fixture.account_id}:{region}", fetch)


# describe_remediation_configurations accepts at most this many rule names per call.
_DESCRIBE_REMEDIATION_CONFIGURATIONS_BATCH_SIZE = 25


def get_remediation_configurations(account_fixture: CatsAccountProtocol, region: str) -> dict[str, RemediationConfigurationOutputTypeDef]:
    """Get remediation configurations for every LZA-configured remediated Config rule, keyed by rule name.

    One batched call per 25 rule names (the API has no paginator and no list-all form);
    a rule with no remediation configuration deployed is absent from the result.
    """

    def fetch() -> dict[str, RemediationConfigurationOutputTypeDef]:
        client = account_fixture.session.client("config", region_name=region, config=DEFAULT_RETRY_CONFIG)
        rule_names = lza_config().remediated_config_rule_names
        remediation_configurations: dict[str, RemediationConfigurationOutputTypeDef] = {}
        for start in range(0, len(rule_names), _DESCRIBE_REMEDIATION_CONFIGURATIONS_BATCH_SIZE):
            batch = rule_names[start : start + _DESCRIBE_REMEDIATION_CONFIGURATIONS_BATCH_SIZE]
            response = client.describe_remediation_configurations(ConfigRuleNames=batch)
            remediation_configurations.update({remediation["ConfigRuleName"]: remediation for remediation in response["RemediationConfigurations"]})
        return remediation_configurations

    return cached(f"remediation_configurations:{account_fixture.account_id}:{region}", fetch)


# ============================================================================
# IAM Roles Caching
# ============================================================================


def get_iam_roles(account_fixture: CatsAccountProtocol, home_region: str) -> dict[str, RoleTypeDef]:
    """Get IAM roles for an account, using cache when available."""

    def fetch() -> dict[str, RoleTypeDef]:
        client = account_fixture.session.client("iam", region_name=home_region, config=DEFAULT_RETRY_CONFIG)
        paginator = client.get_paginator("list_roles")
        return {role["RoleName"]: role for page in paginator.paginate() for role in page["Roles"]}

    return cached(f"iam_roles:{account_fixture.account_id}", fetch)


# ============================================================================
# CloudWatch Logs Caching
# ============================================================================


def get_cloudwatch_log_groups(account_fixture: CatsAccountProtocol, region: str) -> dict[str, LogGroupTypeDef]:
    """Get CloudWatch Log Groups for an account in a region, using cache when available."""

    def fetch() -> dict[str, LogGroupTypeDef]:
        client = account_fixture.session.client("logs", region_name=region, config=DEFAULT_RETRY_CONFIG)
        paginator = client.get_paginator("describe_log_groups")
        return {lg["logGroupName"]: lg for page in paginator.paginate() for lg in page["logGroups"]}

    return cached(f"cloudwatch_logs:{account_fixture.account_id}:{region}", fetch)


# ============================================================================
# Helper Functions
# ============================================================================


def get_protected_iam_roles(roles: dict[str, RoleTypeDef]) -> dict[str, RoleTypeDef]:
    """Filter IAM roles to only those protected by LZA SCPs."""
    # TODO can we avoid hardcoding these? Is this an exhaustive list?
    protected_prefixes = ("AWSAccelerator", "cdk-accel", "AWSControlTowerExecution")
    protected_roles = {name: data for name, data in roles.items() if any(name.startswith(p) for p in protected_prefixes)}
    logger.info(f"Found {len(protected_roles)} protected IAM roles")
    return protected_roles


# ============================================================================
# IAM Policy Caching
# ============================================================================


def get_password_policy(account_fixture: CatsAccountProtocol) -> PasswordPolicyTypeDef:
    """Get IAM password policy for an account, using cache when available."""

    def fetch() -> PasswordPolicyTypeDef:
        client = account_fixture.session.client("iam", config=DEFAULT_RETRY_CONFIG)
        return client.get_account_password_policy()["PasswordPolicy"]

    return cached(f"password_policy:{account_fixture.account_id}", fetch)


def get_local_policy_names(account_fixture: CatsAccountProtocol) -> list[str]:
    """Get all customer-managed IAM policy names for an account, using cache when available."""

    def fetch() -> list[str]:
        client = account_fixture.session.client("iam", config=DEFAULT_RETRY_CONFIG)
        return [policy["PolicyName"] for page in client.get_paginator("list_policies").paginate(Scope="Local") for policy in page["Policies"]]

    return cached(f"iam_local_policies:{account_fixture.account_id}", fetch)


# ============================================================================
# Organizations Caching
# ============================================================================


def get_organization(account_fixture: CatsAccountProtocol) -> OrganizationTypeDef:
    """Get the organization description, using cache when available."""

    def fetch() -> OrganizationTypeDef:
        client = account_fixture.session.client("organizations", region_name=lza_config().home_region, config=DEFAULT_RETRY_CONFIG)
        return client.describe_organization()["Organization"]

    return cached(f"organization:{account_fixture.account_id}", fetch)


def get_organization_root_id(account_fixture: CatsAccountProtocol) -> str:
    """Get the organization root ID, using cache when available."""

    def fetch() -> str:
        client = account_fixture.session.client("organizations", region_name=lza_config().home_region, config=DEFAULT_RETRY_CONFIG)
        roots = [root for page in client.get_paginator("list_roots").paginate() for root in page["Roots"]]
        return roots[0]["Id"]

    return cached(f"org_root_id:{account_fixture.account_id}", fetch)


def get_organization_ous(account_fixture: CatsAccountProtocol) -> dict[str, str]:
    """Get all OUs in the organization as {name_or_path: ou_id}, using cache when available."""

    def fetch() -> dict[str, str]:
        client = account_fixture.session.client("organizations", region_name=lza_config().home_region, config=DEFAULT_RETRY_CONFIG)
        root_id = get_organization_root_id(account_fixture)
        result: dict[str, str] = {}
        _collect_ous(client, root_id, "", result)
        return result

    return cached(f"org_ous:{account_fixture.account_id}", fetch)


def _collect_ous(client: OrganizationsClient, parent_id: str, path: str, result: dict[str, str]) -> None:
    """Recursively collect all OUs under a parent into result dict."""
    paginator = client.get_paginator("list_organizational_units_for_parent")
    for page in paginator.paginate(ParentId=parent_id):
        for ou in page["OrganizationalUnits"]:
            current_path = f"{path}/{ou['Name']}" if path else ou["Name"]
            result[current_path] = ou["Id"]
            _collect_ous(client, ou["Id"], current_path, result)


def get_account_ids_in_parent(account_fixture: CatsAccountProtocol, parent_id: str) -> list[str]:
    """Get account IDs directly under a parent (OU or root), using cache when available."""

    def fetch() -> list[str]:
        client = account_fixture.session.client("organizations", region_name=lza_config().home_region, config=DEFAULT_RETRY_CONFIG)
        paginator = client.get_paginator("list_accounts_for_parent")
        return [account["Id"] for page in paginator.paginate(ParentId=parent_id) for account in page["Accounts"]]

    return cached(f"accounts_in_parent:{account_fixture.account_id}:{parent_id}", fetch)


def get_organization_accounts(account_fixture: CatsAccountProtocol) -> dict[str, str]:
    """Get all accounts in the organization as {account_name: account_id}, using cache when available."""

    def fetch() -> dict[str, str]:
        client = account_fixture.session.client("organizations", region_name=lza_config().home_region, config=DEFAULT_RETRY_CONFIG)
        paginator = client.get_paginator("list_accounts")
        return {account["Name"]: account["Id"] for page in paginator.paginate() for account in page["Accounts"]}

    return cached(f"org_accounts:{account_fixture.account_id}", fetch)


def get_organization_scps(account_fixture: CatsAccountProtocol) -> dict[str, PolicySummaryTypeDef]:
    """Get all SCPs in the organization as {policy_name: policy_summary}, using cache when available."""

    def fetch() -> dict[str, PolicySummaryTypeDef]:
        client = account_fixture.session.client("organizations", region_name=lza_config().home_region, config=DEFAULT_RETRY_CONFIG)
        paginator = client.get_paginator("list_policies")
        return {policy["Name"]: policy for page in paginator.paginate(Filter="SERVICE_CONTROL_POLICY") for policy in page["Policies"]}

    return cached(f"org_scps:{account_fixture.account_id}", fetch)


def get_scps_attached_to_target(account_fixture: CatsAccountProtocol, target_id: str) -> list[PolicySummaryTypeDef]:
    """Every SCP directly attached to one root, OU or account, using cache when available.

    Direct attachments only: policies inherited from a parent are not returned by the API.
    """

    def fetch() -> list[PolicySummaryTypeDef]:
        client = account_fixture.session.client("organizations", region_name=lza_config().home_region, config=DEFAULT_RETRY_CONFIG)
        paginator = client.get_paginator("list_policies_for_target")
        return [policy for page in paginator.paginate(TargetId=target_id, Filter="SERVICE_CONTROL_POLICY") for policy in page["Policies"]]

    return cached(f"org_scps_for_target:{account_fixture.account_id}:{target_id}", fetch)


# ============================================================================
# S3 Bucket Caching
# ============================================================================


def get_s3_buckets(account_fixture: CatsAccountProtocol) -> list[str]:
    """Get all S3 bucket names for an account, using cache when available."""

    def fetch() -> list[str]:
        client = account_fixture.session.client("s3", config=DEFAULT_RETRY_CONFIG)
        return [bucket["Name"] for page in client.get_paginator("list_buckets").paginate() for bucket in page["Buckets"]]

    return cached(f"s3_buckets:{account_fixture.account_id}", fetch)


def get_s3_lifecycle_rules(account_fixture: CatsAccountProtocol, bucket_name: str) -> list[LifecycleRuleOutputTypeDef]:
    """Get lifecycle rules for an S3 bucket, using cache when available."""

    def fetch() -> list[LifecycleRuleOutputTypeDef]:
        client = account_fixture.session.client("s3", config=DEFAULT_RETRY_CONFIG)
        response = client.get_bucket_lifecycle_configuration(Bucket=bucket_name)
        return response["Rules"]

    return cached(f"s3_lifecycle:{account_fixture.account_id}:{bucket_name}", fetch)


# ============================================================================
# CloudTrail Caching
# ============================================================================


def get_cloudtrail_trails(account_fixture: CatsAccountProtocol) -> list[TrailTypeDef]:
    """Get CloudTrail trails for an account, using cache when available."""

    def fetch() -> list[TrailTypeDef]:
        client = account_fixture.session.client("cloudtrail", region_name=lza_config().home_region, config=DEFAULT_RETRY_CONFIG)
        return client.describe_trails()["trailList"]

    return cached(f"cloudtrail_trails:{account_fixture.account_id}", fetch)


# ============================================================================
# Backup Caching
# ============================================================================


def get_backup_vault_names(account_fixture: CatsAccountProtocol) -> list[str]:
    """Get backup vault names for an account in the home region, using cache when available."""

    def fetch() -> list[str]:
        client = account_fixture.session.client("backup", region_name=lza_config().home_region, config=DEFAULT_RETRY_CONFIG)
        return [vault["BackupVaultName"] for page in client.get_paginator("list_backup_vaults").paginate() for vault in page["BackupVaultList"]]

    return cached(f"backup_vaults:{account_fixture.account_id}", fetch)


# ============================================================================
# GuardDuty Caching
# ============================================================================


def get_guardduty_detector_id(account_fixture: CatsAccountProtocol, region: str) -> str:
    """Get the single GuardDuty detector ID for an account/region, using cache when available."""

    def fetch() -> str:
        client = account_fixture.session.client("guardduty", region_name=region, config=DEFAULT_RETRY_CONFIG)
        detector_ids = [detector_id for page in client.get_paginator("list_detectors").paginate() for detector_id in page["DetectorIds"]]
        assert detector_ids, f"No GuardDuty detector in {account_fixture.name} / {region}"
        return detector_ids[0]

    return cached(f"guardduty_detector_id:{account_fixture.account_id}:{region}", fetch)


def get_guardduty_detector(account_fixture: CatsAccountProtocol, region: str) -> GetDetectorResponseTypeDef:
    """Get GuardDuty detector config for an account/region, using cache when available."""

    def fetch() -> GetDetectorResponseTypeDef:
        client = account_fixture.session.client("guardduty", region_name=region, config=DEFAULT_RETRY_CONFIG)
        return client.get_detector(DetectorId=get_guardduty_detector_id(account_fixture, region))

    return cached(f"guardduty_detector:{account_fixture.account_id}:{region}", fetch)


# ============================================================================
# Macie Caching
# ============================================================================


def get_macie_session(account_fixture: CatsAccountProtocol, region: str) -> GetMacieSessionResponseTypeDef:
    """Get Macie session status for an account/region, using cache when available."""

    def fetch() -> GetMacieSessionResponseTypeDef:
        client = account_fixture.session.client("macie2", region_name=region, config=DEFAULT_RETRY_CONFIG)
        return client.get_macie_session()

    return cached(f"macie_session:{account_fixture.account_id}:{region}", fetch)


# ============================================================================
# Security Hub Caching
# ============================================================================


def get_securityhub_enabled_standards(account_fixture: CatsAccountProtocol, region: str) -> list[StandardsSubscriptionTypeDef]:
    """Get enabled Security Hub standards for an account/region, using cache when available."""

    def fetch() -> list[StandardsSubscriptionTypeDef]:
        client = account_fixture.session.client("securityhub", region_name=region, config=DEFAULT_RETRY_CONFIG)
        paginator = client.get_paginator("get_enabled_standards")
        return [s for page in paginator.paginate() for s in page["StandardsSubscriptions"]]

    return cached(f"securityhub_standards:{account_fixture.account_id}:{region}", fetch)


def get_securityhub_standards_catalog(account_fixture: CatsAccountProtocol, region: str) -> dict[str, str]:
    """``{standard name: StandardsArn}`` for every standard Security Hub offers in the region, using cache when available.

    ``DescribeStandards`` lists the regional service catalog, not account state, so the result is
    cached per region and the first account to ask serves every other account in that region. The
    names are the strings LZA accepts in ``securityHub.standards[].name``; LZA resolves them to
    ARNs the same way.
    """

    def fetch() -> dict[str, str]:
        client = account_fixture.session.client("securityhub", region_name=region, config=DEFAULT_RETRY_CONFIG)
        return {
            standard["Name"]: standard["StandardsArn"]
            for page in client.get_paginator("describe_standards").paginate()
            for standard in page["Standards"]
        }

    return cached(f"securityhub_standards_catalog:{region}", fetch)


# ============================================================================
# SNS Caching
# ============================================================================


def get_sns_topic_arns(account_fixture: CatsAccountProtocol, region: str) -> list[str]:
    """Get all SNS topic ARNs for an account/region, using cache when available."""

    def fetch() -> list[str]:
        client = account_fixture.session.client("sns", region_name=region, config=DEFAULT_RETRY_CONFIG)
        paginator = client.get_paginator("list_topics")
        return [t["TopicArn"] for page in paginator.paginate() for t in page["Topics"]]

    return cached(f"sns_topics:{account_fixture.account_id}:{region}", fetch)


# ============================================================================
# Network Firewall Caching
# ============================================================================


def get_network_firewalls(account_fixture: CatsAccountProtocol, region: str) -> list[FirewallMetadataTypeDef]:
    """Get all Network Firewalls for an account/region, using cache when available."""

    def fetch() -> list[FirewallMetadataTypeDef]:
        client = account_fixture.session.client("network-firewall", region_name=region, config=DEFAULT_RETRY_CONFIG)
        return [firewall for page in client.get_paginator("list_firewalls").paginate() for firewall in page["Firewalls"]]

    return cached(f"network_firewalls:{account_fixture.account_id}:{region}", fetch)


# ============================================================================
# RCP (Resource Control Policy) Caching
# ============================================================================


def get_organization_rcps(account_fixture: CatsAccountProtocol) -> dict[str, PolicySummaryTypeDef]:
    """Get all RCPs in the organization as {policy_name: policy_summary}, using cache when available."""

    def fetch() -> dict[str, PolicySummaryTypeDef]:
        client = account_fixture.session.client("organizations", region_name=lza_config().home_region, config=DEFAULT_RETRY_CONFIG)
        paginator = client.get_paginator("list_policies")
        return {policy["Name"]: policy for page in paginator.paginate(Filter="RESOURCE_CONTROL_POLICY") for policy in page["Policies"]}

    return cached(f"org_rcps:{account_fixture.account_id}", fetch)


def get_rcp_policy_content(account_fixture: CatsAccountProtocol, policy_id: str) -> str:
    """Get the JSON content of an RCP by policy ID, using cache when available."""

    def fetch() -> str:
        client = account_fixture.session.client("organizations", region_name=lza_config().home_region, config=DEFAULT_RETRY_CONFIG)
        return client.describe_policy(PolicyId=policy_id)["Policy"]["Content"]

    return cached(f"rcp_content:{policy_id}", fetch)


# ============================================================================
# Control Tower Caching
# ============================================================================


def get_enabled_controls(account_fixture: CatsAccountProtocol) -> list[EnabledControlSummaryTypeDef]:
    """Get every Control Tower control enabled on any OU, with its deployment and drift status, using cache when available.

    Called from the Management account in the home region, where the landing zone lives.
    """

    def fetch() -> list[EnabledControlSummaryTypeDef]:
        client = account_fixture.session.client("controltower", region_name=lza_config().home_region, config=DEFAULT_RETRY_CONFIG)
        return [control for page in client.get_paginator("list_enabled_controls").paginate() for control in page["enabledControls"]]

    return cached(f"controltower_enabled_controls:{account_fixture.account_id}", fetch)


def get_enabled_baselines(account_fixture: CatsAccountProtocol) -> list[EnabledBaselineSummaryTypeDef]:
    """Get every Control Tower baseline enabled on an OU or account (children included), using cache when available.

    ``includeChildren`` returns the per-account baselines inherited from a registered OU, which is
    how an enrolled account appears as its own target. Called from the Management account.
    """

    def fetch() -> list[EnabledBaselineSummaryTypeDef]:
        client = account_fixture.session.client("controltower", region_name=lza_config().home_region, config=DEFAULT_RETRY_CONFIG)
        paginator = client.get_paginator("list_enabled_baselines")
        return [baseline for page in paginator.paginate(includeChildren=True) for baseline in page["enabledBaselines"]]

    return cached(f"controltower_enabled_baselines:{account_fixture.account_id}", fetch)

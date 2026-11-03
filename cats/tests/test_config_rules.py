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
CATS - AWS Config Managed Rules

Every test proves one LZA-SEC-Config control: the Config rule the Universal
Configuration declares in ``awsConfig.ruleSets`` is deployed, under its configured
name, and ``ACTIVE`` in every account and region the pack believes that ruleSet
covers. The
Universal Configuration declares two ruleSets, and the account sets below state
where each one lives; they are not read from ``deploymentTargets``, so a config that
drops an account fails the test instead of shrinking it. Control Tower deploys rules
of the same name to the OUs it governs; those are a Control Tower side effect, not
the LZA control, and are not accepted here.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import pytest
from cats import GetAccountFixture, cats

from cats_utils.accounts import all_accounts
from cats_utils.cats_cache import get_config_rules, get_iam_roles, get_remediation_configurations
from cats_utils.evidence import Evidence
from lza_utils.config_remediation import AUTOMATION_ASSUME_ROLE_PARAMETER, expected_remediation_configuration
from lza_utils.lza_config import lza_config

if TYPE_CHECKING:
    from cats_types import AuditAccount, CatsAccountProtocol, LogArchiveAccount, ManagementAccount

logger = logging.getLogger(__name__)

# The first ruleSet (24 rules) targets the Root OU: every account in the organization.
# The second (11 rules) targets the Management account alone; those tests take it directly.
ROOT_RULE_SET_ACCOUNTS = all_accounts()


def lza_config_rule_name(rule_name: str) -> str:
    """The configured (deployed) name of a Universal Configuration Config rule."""
    return f"{lza_config().accelerator_prefix}-{rule_name}"


def assert_lza_config_rule_active(account: CatsAccountProtocol, region: str, rule_name: str) -> None:
    """Assert the LZA-declared Config rule is deployed and ``ACTIVE`` in the account and region.

    A rule in any other state (``EVALUATING`` after a deploy, ``DELETING`` after a failed
    one) exists but is not evaluating compliance, so existence alone proves nothing.
    """
    lza_rule_name = lza_config_rule_name(rule_name)
    account_config_rules = get_config_rules(account, region)
    deployed_rule = account_config_rules.get(lza_rule_name)
    assert deployed_rule is not None, (
        f"Config rule '{lza_rule_name}' not deployed in {account.name} {region} ({len(account_config_rules)} rules found)"
    )
    rule_state = deployed_rule.get("ConfigRuleState", "<ConfigRuleState not returned by API>")
    assert rule_state == "ACTIVE", f"Config rule '{lza_rule_name}' in {account.name} {region} is {rule_state}, not ACTIVE"


def check_config_rule_remediation(
    account: CatsAccountProtocol, region: str, rule_name: str, audit_account_id: str, log_archive_account_id: str
) -> None:
    """Assert the LZA rule's deployed remediation configuration matches its remediation block in security-config.yaml.

    Everything LZA derives from the config is compared as one object. The one value LZA
    cannot declare, the CDK-named remediation role in ``AutomationAssumeRole``, is checked
    to be a single role that exists in the account.
    """
    config = lza_config()
    lza_rule_name = lza_config_rule_name(rule_name)
    expected = expected_remediation_configuration(config.config_rule(lza_rule_name), region, audit_account_id, log_archive_account_id)

    remediation_configurations = get_remediation_configurations(account, region)
    assert lza_rule_name in remediation_configurations, f"No remediation configuration for '{lza_rule_name}' in {account.name} {region}"
    actual: dict[str, Any] = dict(remediation_configurations[lza_rule_name])
    del actual["Arn"]  # AWS-assigned, carries a random suffix

    automation_assume_role_arns: list[str] = []
    if "Parameters" in expected:
        actual_parameters = dict(actual["Parameters"])
        automation_assume_role_arns = actual_parameters.pop(AUTOMATION_ASSUME_ROLE_PARAMETER)["StaticValue"]["Values"]
        actual["Parameters"] = actual_parameters

    assert actual == expected, f"Remediation configuration for '{lza_rule_name}' in {account.name} {region} does not match security-config.yaml"

    if "Parameters" in expected:
        assert len(automation_assume_role_arns) == 1, (
            f"Expected one {AUTOMATION_ASSUME_ROLE_PARAMETER} for '{lza_rule_name}': {automation_assume_role_arns}"
        )
        role_name = automation_assume_role_arns[0].rsplit("/", 1)[-1]
        iam_roles = get_iam_roles(account, config.home_region)
        deployed_role_arn = iam_roles[role_name]["Arn"] if role_name in iam_roles else None
        assert deployed_role_arn == automation_assume_role_arns[0], f"Remediation role for '{lza_rule_name}' not found in {account.name}"


# ============================================================================
# Test Functions (1-10)
# ============================================================================


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@cats(standard_name=["LZA-SEC-Config-1"], test_suite="config", test_id="1", evidence=Evidence.CONFIGURATION)
def test_sagemaker_notebook_instance_kms_key_configured_rule(region: str, Management_account: ManagementAccount) -> None:
    """LZA-SEC-Config-1: Verify the sagemaker-notebook-instance-kms-key-configured Config rule is deployed and ACTIVE"""
    assert_lza_config_rule_active(Management_account, region, "sagemaker-notebook-instance-kms-key-configured")


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@pytest.mark.parametrize("account_fixture_name", ROOT_RULE_SET_ACCOUNTS)
@cats(standard_name=["LZA-SEC-Config-2"], test_suite="config", test_id="2", evidence=Evidence.CONFIGURATION)
def test_sagemaker_endpoint_configuration_kms_key_configured_rule(
    account_fixture_name: str, region: str, get_account_fixture: GetAccountFixture
) -> None:
    """LZA-SEC-Config-2: Verify the sagemaker-endpoint-configuration-kms-key-configured Config rule is deployed and ACTIVE"""
    account = get_account_fixture(account_fixture_name)
    assert_lza_config_rule_active(account, region, "sagemaker-endpoint-configuration-kms-key-configured")


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@pytest.mark.parametrize("account_fixture_name", ROOT_RULE_SET_ACCOUNTS)
@cats(standard_name=["LZA-SEC-Config-3"], test_suite="config", test_id="3", evidence=Evidence.CONFIGURATION)
def test_ebs_in_backup_plan_rule(account_fixture_name: str, region: str, get_account_fixture: GetAccountFixture) -> None:
    """LZA-SEC-Config-3: Verify the ebs-in-backup-plan Config rule is deployed and ACTIVE"""
    account = get_account_fixture(account_fixture_name)
    assert_lza_config_rule_active(account, region, "ebs-in-backup-plan")


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@pytest.mark.parametrize("account_fixture_name", ROOT_RULE_SET_ACCOUNTS)
@cats(standard_name=["LZA-SEC-Config-4"], test_suite="config", test_id="4", evidence=Evidence.CONFIGURATION)
def test_rds_in_backup_plan_rule(account_fixture_name: str, region: str, get_account_fixture: GetAccountFixture) -> None:
    """LZA-SEC-Config-4: Verify the rds-in-backup-plan Config rule is deployed and ACTIVE"""
    account = get_account_fixture(account_fixture_name)
    assert_lza_config_rule_active(account, region, "rds-in-backup-plan")


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@cats(standard_name=["LZA-SEC-Config-5"], test_suite="config", test_id="5", evidence=Evidence.CONFIGURATION)
def test_securityhub_enabled_rule(region: str, Management_account: ManagementAccount) -> None:
    """LZA-SEC-Config-5: Verify the securityhub-enabled Config rule is deployed and ACTIVE"""
    assert_lza_config_rule_active(Management_account, region, "securityhub-enabled")


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@cats(standard_name=["LZA-SEC-Config-6"], test_suite="config", test_id="6", evidence=Evidence.CONFIGURATION)
def test_internet_gateway_authorized_vpc_only_rule(region: str, Management_account: ManagementAccount) -> None:
    """LZA-SEC-Config-6: Verify the internet-gateway-authorized-vpc-only Config rule is deployed and ACTIVE"""
    assert_lza_config_rule_active(Management_account, region, "internet-gateway-authorized-vpc-only")


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@pytest.mark.parametrize("account_fixture_name", ROOT_RULE_SET_ACCOUNTS)
@cats(standard_name=["LZA-SEC-Config-7"], test_suite="config", test_id="7", evidence=Evidence.CONFIGURATION)
def test_dynamodb_table_encrypted_kms_rule(account_fixture_name: str, region: str, get_account_fixture: GetAccountFixture) -> None:
    """LZA-SEC-Config-7: Verify the dynamodb-table-encrypted-kms Config rule is deployed and ACTIVE"""
    account = get_account_fixture(account_fixture_name)
    assert_lza_config_rule_active(account, region, "dynamodb-table-encrypted-kms")


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@pytest.mark.parametrize("account_fixture_name", ROOT_RULE_SET_ACCOUNTS)
@cats(standard_name=["LZA-SEC-Config-8"], test_suite="config", test_id="8", evidence=Evidence.CONFIGURATION)
def test_guardduty_non_archived_findings_rule(account_fixture_name: str, region: str, get_account_fixture: GetAccountFixture) -> None:
    """LZA-SEC-Config-8: Verify the guardduty-non-archived-findings Config rule is deployed and ACTIVE"""
    account = get_account_fixture(account_fixture_name)
    assert_lza_config_rule_active(account, region, "guardduty-non-archived-findings")


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@pytest.mark.parametrize("account_fixture_name", ROOT_RULE_SET_ACCOUNTS)
@cats(standard_name=["LZA-SEC-Config-9"], test_suite="config", test_id="9", evidence=Evidence.CONFIGURATION)
def test_cloudtrail_security_trail_enabled_rule(account_fixture_name: str, region: str, get_account_fixture: GetAccountFixture) -> None:
    """LZA-SEC-Config-9: Verify the cloudtrail-security-trail-enabled Config rule is deployed and ACTIVE"""
    account = get_account_fixture(account_fixture_name)
    assert_lza_config_rule_active(account, region, "cloudtrail-security-trail-enabled")


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@pytest.mark.parametrize("account_fixture_name", ROOT_RULE_SET_ACCOUNTS)
@cats(standard_name=["LZA-SEC-Config-10"], test_suite="config", test_id="10", evidence=Evidence.CONFIGURATION)
def test_cloudtrail_enabled_rule(account_fixture_name: str, region: str, get_account_fixture: GetAccountFixture) -> None:
    """LZA-SEC-Config-10: Verify the cloudtrail-enabled Config rule is deployed and ACTIVE"""
    account = get_account_fixture(account_fixture_name)
    assert_lza_config_rule_active(account, region, "cloudtrail-enabled")


# ============================================================================
# Test Functions (11-20)
# ============================================================================


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@pytest.mark.parametrize("account_fixture_name", ROOT_RULE_SET_ACCOUNTS)
@cats(standard_name=["LZA-SEC-Config-11"], test_suite="config", test_id="11", evidence=Evidence.CONFIGURATION)
def test_ec2_instance_detailed_monitoring_enabled_rule(account_fixture_name: str, region: str, get_account_fixture: GetAccountFixture) -> None:
    """LZA-SEC-Config-11: Verify the ec2-instance-detailed-monitoring-enabled Config rule is deployed and ACTIVE"""
    account = get_account_fixture(account_fixture_name)
    assert_lza_config_rule_active(account, region, "ec2-instance-detailed-monitoring-enabled")


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@pytest.mark.parametrize("account_fixture_name", ROOT_RULE_SET_ACCOUNTS)
@cats(standard_name=["LZA-SEC-Config-12"], test_suite="config", test_id="12", evidence=Evidence.CONFIGURATION)
def test_ec2_instances_in_vpc_rule(account_fixture_name: str, region: str, get_account_fixture: GetAccountFixture) -> None:
    """LZA-SEC-Config-12: Verify the ec2-instances-in-vpc Config rule is deployed and ACTIVE"""
    account = get_account_fixture(account_fixture_name)
    assert_lza_config_rule_active(account, region, "ec2-instances-in-vpc")


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@pytest.mark.parametrize("account_fixture_name", ROOT_RULE_SET_ACCOUNTS)
@cats(standard_name=["LZA-SEC-Config-13"], test_suite="config", test_id="13", evidence=Evidence.CONFIGURATION)
def test_s3_bucket_policy_grantee_check_rule(account_fixture_name: str, region: str, get_account_fixture: GetAccountFixture) -> None:
    """LZA-SEC-Config-13: Verify the s3-bucket-policy-grantee-check Config rule is deployed and ACTIVE"""
    account = get_account_fixture(account_fixture_name)
    assert_lza_config_rule_active(account, region, "s3-bucket-policy-grantee-check")


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@pytest.mark.parametrize("account_fixture_name", ROOT_RULE_SET_ACCOUNTS)
@cats(standard_name=["LZA-SEC-Config-14"], test_suite="config", test_id="14", evidence=Evidence.CONFIGURATION)
def test_iam_user_group_membership_check_rule(account_fixture_name: str, region: str, get_account_fixture: GetAccountFixture) -> None:
    """LZA-SEC-Config-14: Verify the iam-user-group-membership-check Config rule is deployed and ACTIVE"""
    account = get_account_fixture(account_fixture_name)
    assert_lza_config_rule_active(account, region, "iam-user-group-membership-check")


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@cats(standard_name=["LZA-SEC-Config-15"], test_suite="config", test_id="15", evidence=Evidence.CONFIGURATION)
def test_cloudtrail_s3_dataevents_enabled_rule(region: str, Management_account: ManagementAccount) -> None:
    """LZA-SEC-Config-15: Verify the cloudtrail-s3-dataevents-enabled Config rule is deployed and ACTIVE"""
    assert_lza_config_rule_active(Management_account, region, "cloudtrail-s3-dataevents-enabled")


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@cats(standard_name=["LZA-SEC-Config-16"], test_suite="config", test_id="16", evidence=Evidence.CONFIGURATION)
def test_iam_group_has_users_check_rule(region: str, Management_account: ManagementAccount) -> None:
    """LZA-SEC-Config-16: Verify the iam-group-has-users-check Config rule is deployed and ACTIVE"""
    assert_lza_config_rule_active(Management_account, region, "iam-group-has-users-check")


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@pytest.mark.parametrize("account_fixture_name", ROOT_RULE_SET_ACCOUNTS)
@cats(standard_name=["LZA-SEC-Config-17"], test_suite="config", test_id="17", evidence=Evidence.CONFIGURATION)
def test_api_gw_cache_enabled_and_encrypted_rule(account_fixture_name: str, region: str, get_account_fixture: GetAccountFixture) -> None:
    """LZA-SEC-Config-17: Verify the api-gw-cache-enabled-and-encrypted Config rule is deployed and ACTIVE"""
    account = get_account_fixture(account_fixture_name)
    assert_lza_config_rule_active(account, region, "api-gw-cache-enabled-and-encrypted")


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@pytest.mark.parametrize("account_fixture_name", ROOT_RULE_SET_ACCOUNTS)
@cats(standard_name=["LZA-SEC-Config-18"], test_suite="config", test_id="18", evidence=Evidence.CONFIGURATION)
def test_ec2_volume_inuse_check_rule(account_fixture_name: str, region: str, get_account_fixture: GetAccountFixture) -> None:
    """LZA-SEC-Config-18: Verify the ec2-volume-inuse-check Config rule is deployed and ACTIVE"""
    account = get_account_fixture(account_fixture_name)
    assert_lza_config_rule_active(account, region, "ec2-volume-inuse-check")


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@pytest.mark.parametrize("account_fixture_name", ROOT_RULE_SET_ACCOUNTS)
@cats(standard_name=["LZA-SEC-Config-19"], test_suite="config", test_id="19", evidence=Evidence.CONFIGURATION)
def test_emr_kerberos_enabled_rule(account_fixture_name: str, region: str, get_account_fixture: GetAccountFixture) -> None:
    """LZA-SEC-Config-19: Verify the emr-kerberos-enabled Config rule is deployed and ACTIVE"""
    account = get_account_fixture(account_fixture_name)
    assert_lza_config_rule_active(account, region, "emr-kerberos-enabled")


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@cats(standard_name=["LZA-SEC-Config-20"], test_suite="config", test_id="20", evidence=Evidence.CONFIGURATION)
def test_iam_no_inline_policy_check_rule(region: str, Management_account: ManagementAccount) -> None:
    """LZA-SEC-Config-20: Verify the iam-no-inline-policy-check Config rule is deployed and ACTIVE"""
    assert_lza_config_rule_active(Management_account, region, "iam-no-inline-policy-check")


# ============================================================================
# Test Functions (21-30)
# ============================================================================


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@cats(standard_name=["LZA-SEC-Config-21"], test_suite="config", test_id="21", evidence=Evidence.CONFIGURATION)
def test_cloudwatch_log_group_encrypted_rule(region: str, Management_account: ManagementAccount) -> None:
    """LZA-SEC-Config-21: Verify the cloudwatch-log-group-encrypted Config rule is deployed and ACTIVE"""
    assert_lza_config_rule_active(Management_account, region, "cloudwatch-log-group-encrypted")


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@pytest.mark.parametrize("account_fixture_name", ROOT_RULE_SET_ACCOUNTS)
@cats(standard_name=["LZA-SEC-Config-22"], test_suite="config", test_id="22", evidence=Evidence.CONFIGURATION)
def test_account_part_of_organizations_rule(account_fixture_name: str, region: str, get_account_fixture: GetAccountFixture) -> None:
    """LZA-SEC-Config-22: Verify the account-part-of-organizations Config rule is deployed and ACTIVE"""
    account = get_account_fixture(account_fixture_name)
    assert_lza_config_rule_active(account, region, "account-part-of-organizations")


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@pytest.mark.parametrize("account_fixture_name", ROOT_RULE_SET_ACCOUNTS)
@cats(standard_name=["LZA-SEC-Config-23"], test_suite="config", test_id="23", evidence=Evidence.CONFIGURATION)
def test_codebuild_project_artifact_encryption_rule(account_fixture_name: str, region: str, get_account_fixture: GetAccountFixture) -> None:
    """LZA-SEC-Config-23: Verify the codebuild-project-artifact-encryption Config rule is deployed and ACTIVE"""
    account = get_account_fixture(account_fixture_name)
    assert_lza_config_rule_active(account, region, "codebuild-project-artifact-encryption")


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@pytest.mark.parametrize("account_fixture_name", ROOT_RULE_SET_ACCOUNTS)
@cats(standard_name=["LZA-SEC-Config-24"], test_suite="config", test_id="24", evidence=Evidence.CONFIGURATION)
def test_dynamodb_throughput_limit_check_rule(account_fixture_name: str, region: str, get_account_fixture: GetAccountFixture) -> None:
    """LZA-SEC-Config-24: Verify the dynamodb-throughput-limit-check Config rule is deployed and ACTIVE"""
    account = get_account_fixture(account_fixture_name)
    assert_lza_config_rule_active(account, region, "dynamodb-throughput-limit-check")


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@pytest.mark.parametrize("account_fixture_name", ROOT_RULE_SET_ACCOUNTS)
@cats(standard_name=["LZA-SEC-Config-25"], test_suite="config", test_id="25", evidence=Evidence.CONFIGURATION)
def test_ebs_optimized_instance_rule(account_fixture_name: str, region: str, get_account_fixture: GetAccountFixture) -> None:
    """LZA-SEC-Config-25: Verify the ebs-optimized-instance Config rule is deployed and ACTIVE"""
    account = get_account_fixture(account_fixture_name)
    assert_lza_config_rule_active(account, region, "ebs-optimized-instance")


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@pytest.mark.parametrize("account_fixture_name", ROOT_RULE_SET_ACCOUNTS)
@cats(standard_name=["LZA-SEC-Config-26"], test_suite="config", test_id="26", evidence=Evidence.CONFIGURATION)
def test_lambda_dlq_check_rule(account_fixture_name: str, region: str, get_account_fixture: GetAccountFixture) -> None:
    """LZA-SEC-Config-26: Verify the lambda-dlq-check Config rule is deployed and ACTIVE"""
    account = get_account_fixture(account_fixture_name)
    assert_lza_config_rule_active(account, region, "lambda-dlq-check")


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@pytest.mark.parametrize("account_fixture_name", ROOT_RULE_SET_ACCOUNTS)
@cats(standard_name=["LZA-SEC-Config-27"], test_suite="config", test_id="27", evidence=Evidence.CONFIGURATION)
def test_secretsmanager_using_cmk_rule(account_fixture_name: str, region: str, get_account_fixture: GetAccountFixture) -> None:
    """LZA-SEC-Config-27: Verify the secretsmanager-using-cmk Config rule is deployed and ACTIVE"""
    account = get_account_fixture(account_fixture_name)
    assert_lza_config_rule_active(account, region, "secretsmanager-using-cmk")


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@pytest.mark.parametrize("account_fixture_name", ROOT_RULE_SET_ACCOUNTS)
@cats(standard_name=["LZA-SEC-Config-28"], test_suite="config", test_id="28", evidence=Evidence.CONFIGURATION)
def test_aurora_resources_protected_by_backup_plan_rule(account_fixture_name: str, region: str, get_account_fixture: GetAccountFixture) -> None:
    """LZA-SEC-Config-28: Verify the aurora-resources-protected-by-backup-plan Config rule is deployed and ACTIVE"""
    account = get_account_fixture(account_fixture_name)
    assert_lza_config_rule_active(account, region, "aurora-resources-protected-by-backup-plan")


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@cats(standard_name=["LZA-SEC-Config-29"], test_suite="config", test_id="29", evidence=Evidence.CONFIGURATION)
def test_backup_plan_min_frequency_and_min_retention_check_rule(region: str, Management_account: ManagementAccount) -> None:
    """LZA-SEC-Config-29: Verify the backup-plan-min-frequency-and-min-retention-check Config rule is deployed and ACTIVE"""
    assert_lza_config_rule_active(Management_account, region, "backup-plan-min-frequency-and-min-retention-check")


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@cats(standard_name=["LZA-SEC-Config-30"], test_suite="config", test_id="30", evidence=Evidence.CONFIGURATION)
def test_backup_recovery_point_manual_deletion_disabled_rule(region: str, Management_account: ManagementAccount) -> None:
    """LZA-SEC-Config-30: Verify the backup-recovery-point-manual-deletion-disabled Config rule is deployed and ACTIVE"""
    assert_lza_config_rule_active(Management_account, region, "backup-recovery-point-manual-deletion-disabled")


# ============================================================================
# Test Functions (31-34)
# ============================================================================


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@pytest.mark.parametrize("account_fixture_name", ROOT_RULE_SET_ACCOUNTS)
@cats(standard_name=["LZA-SEC-Config-31"], test_suite="config", test_id="31", evidence=Evidence.CONFIGURATION)
def test_backup_recovery_point_encrypted_rule(account_fixture_name: str, region: str, get_account_fixture: GetAccountFixture) -> None:
    """LZA-SEC-Config-31: Verify the backup-recovery-point-encrypted Config rule is deployed and ACTIVE"""
    account = get_account_fixture(account_fixture_name)
    assert_lza_config_rule_active(account, region, "backup-recovery-point-encrypted")


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@cats(standard_name=["LZA-SEC-Config-32"], test_suite="config", test_id="32", evidence=Evidence.CONFIGURATION)
def test_ec2_resources_protected_by_backup_plan_rule(region: str, Management_account: ManagementAccount) -> None:
    """LZA-SEC-Config-32: Verify the ec2-resources-protected-by-backup-plan Config rule is deployed and ACTIVE"""
    assert_lza_config_rule_active(Management_account, region, "ec2-resources-protected-by-backup-plan")


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@pytest.mark.parametrize("account_fixture_name", ROOT_RULE_SET_ACCOUNTS)
@cats(standard_name=["LZA-SEC-Config-33"], test_suite="config", test_id="33", evidence=Evidence.CONFIGURATION)
def test_attach_ec2_instance_profile_custom_rule(
    account_fixture_name: str,
    region: str,
    get_account_fixture: GetAccountFixture,
    Audit_account: AuditAccount,
    LogArchive_account: LogArchiveAccount,
) -> None:
    """LZA-SEC-Config-33: Verify the ec2-instance-profile-attached Config rule is deployed and ACTIVE with its configured automatic remediation."""
    account = get_account_fixture(account_fixture_name)
    assert_lza_config_rule_active(account, region, "ec2-instance-profile-attached")
    check_config_rule_remediation(account, region, "ec2-instance-profile-attached", Audit_account.account_id, LogArchive_account.account_id)


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@pytest.mark.parametrize("account_fixture_name", ROOT_RULE_SET_ACCOUNTS)
@cats(standard_name=["LZA-SEC-Config-34"], test_suite="config", test_id="34", evidence=Evidence.CONFIGURATION)
def test_elb_logging_enabled_custom_rule(
    account_fixture_name: str,
    region: str,
    get_account_fixture: GetAccountFixture,
    Audit_account: AuditAccount,
    LogArchive_account: LogArchiveAccount,
) -> None:
    """LZA-SEC-Config-34: Verify the elb-logging-enabled Config rule is deployed and ACTIVE with its configured automatic remediation."""
    account = get_account_fixture(account_fixture_name)
    assert_lza_config_rule_active(account, region, "elb-logging-enabled")
    check_config_rule_remediation(account, region, "elb-logging-enabled", Audit_account.account_id, LogArchive_account.account_id)

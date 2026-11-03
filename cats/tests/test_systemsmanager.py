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
CATS - Validate Amazon Systems Manager

Related LZA Controls and Tests:
- LZA-SEC-SSM-1: Systems Manager Sessions Manager is configured to encrypt data using KMS
  * test_session_manager_kms_encryption

- LZA-SEC-SSM-2: Session Manager is configured to send session log data to CloudWatch Logs
  * test_session_manager_cloudwatch_logging

- LZA-SEC-SSM-3: Session Manager session logs are delivered to Amazon S3 using CloudWatch Logs
  * test_session_manager_s3_logging_via_cloudwatch (cross-account test)

- LZA-SEC-SSM-4: Public sharing of SSM documents is blocked in every account and region
  * test_ssm_public_document_sharing_blocked

- LZA-SEC-SSM-5: EC2-Default-SSM-Role exists in all accounts but NOT in Management account
  * test_ec2_ssm_iam_role (uses IAM roles caching)

- LZA-SEC-SSM-6: SSM documents exist in source account and are shared to organization
  * test_ssm_document_source
  * test_ssm_document_sharing

Test IDs track Compliance Workbook v1.3.0, which inserted SSM-4 (block public
document sharing) and shifted the former SSM-4/SSM-5 to SSM-5/SSM-6.
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

import pytest
from botocore.exceptions import ClientError
from cats import AccountUnderTest, GetAccountFixture, cats
from cats.config import Settings
from cats.constants import get_account_fixture_names

from cats_utils.accounts import management_account
from cats_utils.boto import DEFAULT_RETRY_CONFIG, get_error_code
from cats_utils.cats_cache import get_cloudwatch_log_groups, get_iam_roles
from cats_utils.evidence import Evidence
from cats_utils.iam import trusted_service_principals
from lza_types.iam_config import AssumedByType
from lza_utils.lza_config import lza_config

if TYPE_CHECKING:
    from mypy_boto3_iam import IAMClient
    from mypy_boto3_logs import CloudWatchLogsClient
    from mypy_boto3_ssm import SSMClient

logger = logging.getLogger(__name__)


def get_session_manager_document(ssm_client: SSMClient) -> dict[str, Any]:
    """Fetch and parse the SSM-SessionManagerRunShell document."""
    doc_content = ssm_client.get_document(Name="SSM-SessionManagerRunShell", DocumentVersion="$LATEST")
    result: dict[str, Any] = json.loads(doc_content["Content"])
    return result


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@pytest.mark.parametrize("account_fixture_name", get_account_fixture_names())
@cats(standard_name=["LZA-SEC-SSM-1"], test_suite="systemsmanager", test_id="1", evidence=Evidence.CONFIGURATION)
def test_session_manager_kms_encryption(
    account_fixture_name: str,
    region: str,
    get_account_fixture: GetAccountFixture,
) -> None:
    """Test that Session Manager is configured to encrypt data using KMS."""
    # arrange
    account = get_account_fixture(account_fixture_name)
    ssm_client: SSMClient = account.session.client("ssm", region_name=region, config=DEFAULT_RETRY_CONFIG)

    # act
    session_manager_document = get_session_manager_document(ssm_client)
    kms_key_id = session_manager_document.get("inputs", {}).get("kmsKeyId")

    # assert
    assert kms_key_id is not None, f"Session Manager not configured with KMS encryption in {account_fixture_name} {region}"


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@pytest.mark.parametrize("account_fixture_name", get_account_fixture_names())
@cats(standard_name=["LZA-SEC-SSM-2"], test_suite="systemsmanager", test_id="2", evidence=Evidence.CONFIGURATION)
def test_session_manager_cloudwatch_logging(
    account_fixture_name: str,
    region: str,
    get_account_fixture: GetAccountFixture,
) -> None:
    """Test that Session Manager is configured to send session logs to CloudWatch Logs."""
    # arrange
    account = get_account_fixture(account_fixture_name)
    ssm_client: SSMClient = account.session.client("ssm", region_name=region, config=DEFAULT_RETRY_CONFIG)

    # act
    session_manager_document = get_session_manager_document(ssm_client)
    cloudwatch_log_group = session_manager_document.get("inputs", {}).get("cloudWatchLogGroupName")

    # assert - config exists
    assert cloudwatch_log_group is not None, f"Session Manager not configured with CloudWatch logging in {account_fixture_name} {region}"

    # assert - log group exists
    log_groups = get_cloudwatch_log_groups(account, region)
    assert cloudwatch_log_group in log_groups, f"CloudWatch log group {cloudwatch_log_group} not found in {account_fixture_name} {region}"


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@pytest.mark.parametrize("account_fixture_name", get_account_fixture_names())
@cats(standard_name=["LZA-SEC-SSM-3"], test_suite="systemsmanager", test_id="3", evidence=Evidence.CONFIGURATION)
def test_session_manager_s3_logging_via_cloudwatch(
    account_fixture_name: str,
    region: str,
    get_account_fixture: GetAccountFixture,
    LogArchive_account: AccountUnderTest,
) -> None:
    """Test that Session Manager logs are delivered to S3 via CloudWatch Logs subscription filters."""
    # arrange
    account = get_account_fixture(account_fixture_name)
    ssm_client: SSMClient = account.session.client("ssm", region_name=region, config=DEFAULT_RETRY_CONFIG)
    logs_client: CloudWatchLogsClient = account.session.client("logs", region_name=region, config=DEFAULT_RETRY_CONFIG)

    # act
    session_manager_document = get_session_manager_document(ssm_client)
    cloudwatch_log_group = session_manager_document.get("inputs", {}).get("cloudWatchLogGroupName")

    assert cloudwatch_log_group is not None, f"Session Manager not configured with CloudWatch logging in {account_fixture_name} {region}"

    filters = [
        subscription_filter
        for page in logs_client.get_paginator("describe_subscription_filters").paginate(logGroupName=cloudwatch_log_group)
        for subscription_filter in page["subscriptionFilters"]
    ]

    # assert
    logarchive_destinations = [f for f in filters if LogArchive_account.account_id in f.get("destinationArn", "")]
    assert len(logarchive_destinations) >= 1, f"No subscription filter to LogArchive for {cloudwatch_log_group} in {account_fixture_name} {region}"


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@pytest.mark.parametrize("account_fixture_name", get_account_fixture_names())
@cats(standard_name=["LZA-SEC-SSM-4"], test_suite="systemsmanager", test_id="4", evidence=Evidence.CONFIGURATION)
def test_ssm_public_document_sharing_blocked(
    account_fixture_name: str,
    region: str,
    get_account_fixture: GetAccountFixture,
) -> None:
    """Test that the SSM public document sharing service setting is disabled."""
    # arrange
    block_public_sharing = lza_config().ssm_block_public_document_sharing
    assert block_public_sharing.enable is True, "ssmSettings.blockPublicDocumentSharing.enable is not true in LZA security config"
    excluded_fixture_names = lza_config().account_fixture_names_from_targets([], block_public_sharing.exclude_accounts or [])
    expected_setting_value = "Enable" if account_fixture_name in excluded_fixture_names else "Disable"
    account = get_account_fixture(account_fixture_name)
    ssm_client: SSMClient = account.session.client("ssm", region_name=region, config=DEFAULT_RETRY_CONFIG)

    # act
    setting = ssm_client.get_service_setting(SettingId="/ssm/documents/console/public-sharing-permission")["ServiceSetting"]

    # assert
    assert setting["SettingValue"] == expected_setting_value, (
        f"SSM public document sharing is {setting['SettingValue']} in {account_fixture_name} {region}, expected {expected_setting_value}"
    )


@pytest.mark.parametrize("account_fixture_name", get_account_fixture_names())
@cats(standard_name=["LZA-SEC-SSM-5"], test_suite="systemsmanager", test_id="5", evidence=Evidence.CONFIGURATION)
def test_ec2_ssm_iam_role(
    account_fixture_name: str,
    get_account_fixture: GetAccountFixture,
) -> None:
    """Test that EC2-Default-SSM-Role exists in all accounts but NOT in Management account."""
    # arrange
    home_region = lza_config().home_region
    role_name = "EC2-Default-SSM-Role"

    lza_config_iam_roles = {r.name: r for r in lza_config().iam_roles}

    # TODO confirm EC2-Default-SSM-Role is mandatory in every non-management account; if the
    # configuration can omit it, gate the test on the configuration rather than on the role's presence.
    assert role_name in lza_config_iam_roles, "EC2-Default-SSM-Role not configured in LZA IAM config"

    account = get_account_fixture(account_fixture_name)
    iam_roles = get_iam_roles(account, home_region)
    is_management_account = account_fixture_name == management_account()
    role_exists = role_name in iam_roles

    # assert - Management account should NOT have this role
    if is_management_account:
        assert role_exists is False, "EC2-Default-SSM-Role should not exist in Management account"
        return

    # assert - workload accounts should have this role
    assert role_exists is True, f"EC2-Default-SSM-Role not found in {account_fixture_name}"

    # assert - role has instance profile
    iam_client: IAMClient = account.session.client("iam", region_name=home_region, config=DEFAULT_RETRY_CONFIG)
    instance_profiles = [
        profile
        for page in iam_client.get_paginator("list_instance_profiles_for_role").paginate(RoleName=role_name)
        for profile in page["InstanceProfiles"]
    ]
    assert len(instance_profiles) >= 1, f"EC2-Default-SSM-Role has no instance profile in {account_fixture_name}"

    # assert - trust policy allows exactly the service principals the LZA config declares
    lza_expected_ssm_role_config = lza_config_iam_roles[role_name]
    expected_trusted_services = {
        assumed_by.principal
        for assumed_by in lza_expected_ssm_role_config.assumed_by
        if assumed_by.type == AssumedByType.service and assumed_by.principal is not None
    }
    assert expected_trusted_services, f"{role_name} has no service principal in assumedBy in iam-config.yaml"
    actual_trusted_services = trusted_service_principals(iam_roles[role_name]["AssumeRolePolicyDocument"])
    assert actual_trusted_services == expected_trusted_services, f"{role_name} trust policy in {account_fixture_name}"

    # assert - required policies attached
    required_policies = lza_expected_ssm_role_config.policies.aws_managed if lza_expected_ssm_role_config.policies else []
    if required_policies:
        attached_names = [
            policy.get("PolicyName", "<UNNAMED POLICY>")
            for page in iam_client.get_paginator("list_attached_role_policies").paginate(RoleName=role_name)
            for policy in page["AttachedPolicies"]
        ]
        missing = [p for p in required_policies if p not in attached_names]
        assert missing == [], f"EC2-Default-SSM-Role missing policies {missing} in {account_fixture_name}"


@cats(standard_name=["LZA-SEC-SSM-6"], test_suite="systemsmanager", test_id="6", evidence=Evidence.CONFIGURATION)
def test_ssm_document_source(
    Audit_account: AccountUnderTest,
) -> None:
    """Test that SSM documents exist in the source account (where they are created)."""
    # arrange
    home_region = lza_config().home_region
    ssm_document_shares = lza_config().ssm_document_shares

    assert ssm_document_shares, "No SSM document shares configured in LZA config"

    ssm_client: SSMClient = Audit_account.session.client("ssm", region_name=home_region, config=DEFAULT_RETRY_CONFIG)
    expected_doc_names = [doc["document_name"] for doc in ssm_document_shares]

    # act
    missing_docs: list[str] = []
    for doc_name in expected_doc_names:
        try:
            ssm_client.describe_document(Name=doc_name)
        except ClientError as e:
            if get_error_code(e) == "InvalidDocument":
                missing_docs.append(doc_name)
            else:
                raise

    # assert
    assert missing_docs == [], f"SSM documents not found in Audit account: {missing_docs}"


def _ssm_document_share_recipient_accounts() -> list[str]:
    """Every account under test except the document owner (the delegated admin) and Management, which LZA shares to no document."""
    excluded = {management_account(), lza_config().delegated_admin_account()}
    return [name for name in get_account_fixture_names() if name not in excluded]


@pytest.mark.parametrize("account_fixture_name", _ssm_document_share_recipient_accounts())
@cats(standard_name=["LZA-SEC-SSM-6"], test_suite="systemsmanager", test_id="7", evidence=Evidence.BEHAVIORAL)
def test_ssm_document_sharing(
    account_fixture_name: str,
    get_account_fixture: GetAccountFixture,
    Audit_account: AccountUnderTest,
) -> None:
    """Test that SSM documents are shared and accessible from member accounts."""
    # arrange
    home_region = lza_config().home_region
    ssm_document_shares = lza_config().ssm_document_shares

    assert ssm_document_shares, "No SSM document shares configured in LZA config"

    account = get_account_fixture(account_fixture_name)
    ssm_client: SSMClient = account.session.client("ssm", region_name=home_region, config=DEFAULT_RETRY_CONFIG)

    # Shared documents must be accessed via full ARN from member accounts
    owner_account_id = Audit_account.account_id
    partition = Settings().cats_deployment_settings.partition

    # act
    not_accessible: list[str] = []
    for doc in ssm_document_shares:
        doc_arn = f"arn:{partition}:ssm:{home_region}:{owner_account_id}:document/{doc['document_name']}"
        try:
            ssm_client.describe_document(Name=doc_arn)
        except ClientError as e:
            if get_error_code(e) == "InvalidDocument":
                not_accessible.append(doc_arn)
            else:
                raise

    # assert
    assert not_accessible == [], f"SSM documents not accessible in {account_fixture_name}: {not_accessible}"

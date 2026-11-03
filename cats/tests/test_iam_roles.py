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
CATS - IAM Role Verification

This test verifies:
- LZA-SEC-IAM-ROLE-1: Creates EC2 Default Systems Manager (SSM) role
- LZA-SEC-IAM-ROLE-2: Creates Backup role for AWS Backup service
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pytest
from cats import GetAccountFixture, cats

from cats_utils.accounts import non_management_accounts
from cats_utils.boto import DEFAULT_RETRY_CONFIG
from cats_utils.evidence import Evidence
from lza_utils.lza_config import lza_config

if TYPE_CHECKING:
    from mypy_boto3_iam.client import IAMClient
    from mypy_boto3_iam.type_defs import AttachedPolicyTypeDef

logger = logging.getLogger(__name__)

# Build role lookup dict from config
_iam_roles = {r.name: r for r in lza_config().iam_roles}
_SSM_ROLE_NAME = "EC2-Default-SSM-Role"
_BACKUP_ROLE_NAME = f"{lza_config().accelerator_prefix}-Backup-Role"


def _expected_policy_names(role_name: str) -> list[str]:
    """Get expected AWS managed policy names for a role, stripping path prefixes."""
    role = _iam_roles[role_name]
    aws_managed = role.policies.aws_managed if role.policies else []
    return sorted(p.split("/")[-1] for p in (aws_managed or []))


def _get_attached_policy_names(iam_client: IAMClient, role_name: str) -> list[str]:
    """Return sorted attached managed policy names for a role."""
    policies: list[AttachedPolicyTypeDef] = [
        policy for page in iam_client.get_paginator("list_attached_role_policies").paginate(RoleName=role_name) for policy in page["AttachedPolicies"]
    ]
    return sorted(policy["PolicyName"] for policy in policies)


@pytest.mark.parametrize("account_fixture_name", non_management_accounts())
@cats(standard_name=["LZA-SEC-IAM-ROLE-1"], test_suite="iam", test_id="role-1", evidence=Evidence.CONFIGURATION)
def test_ec2_ssm_role_exists_with_expected_policies(account_fixture_name: str, get_account_fixture: GetAccountFixture) -> None:
    """Verify EC2-Default-SSM-Role exists with correct managed policies."""
    # arrange
    account = get_account_fixture(account_fixture_name)
    iam_client: IAMClient = account.session.client("iam", config=DEFAULT_RETRY_CONFIG)
    expected = _expected_policy_names(_SSM_ROLE_NAME)

    # act
    iam_client.get_role(RoleName=_SSM_ROLE_NAME)
    attached = _get_attached_policy_names(iam_client, _SSM_ROLE_NAME)

    # assert
    missing = sorted(set(expected) - set(attached))
    assert missing == [], f"EC2 SSM role in {account_fixture_name} missing policies: {missing}"


@pytest.mark.parametrize("account_fixture_name", non_management_accounts())
@cats(standard_name=["LZA-SEC-IAM-ROLE-2"], test_suite="iam", test_id="role-2", evidence=Evidence.CONFIGURATION)
def test_backup_role_exists_with_expected_policies(account_fixture_name: str, get_account_fixture: GetAccountFixture) -> None:
    """Verify Backup role exists with correct managed policies."""
    # arrange
    account = get_account_fixture(account_fixture_name)
    iam_client: IAMClient = account.session.client("iam", config=DEFAULT_RETRY_CONFIG)
    expected = _expected_policy_names(_BACKUP_ROLE_NAME)

    # act
    iam_client.get_role(RoleName=_BACKUP_ROLE_NAME)
    attached = _get_attached_policy_names(iam_client, _BACKUP_ROLE_NAME)

    # assert
    missing = sorted(set(expected) - set(attached))
    assert missing == [], f"Backup role in {account_fixture_name} missing policies: {missing}"

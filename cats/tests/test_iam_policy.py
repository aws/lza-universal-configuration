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
CATS - IAM Policy Deployment Verification

This test verifies:
- LZA-SEC-IAM-POL-1: Default boundary policy deployed to all non-management accounts
- LZA-SEC-IAM-POL-2: Default Systems Manager S3 policy deployed to all non-management accounts
- LZA-SEC-IDC-1: Identity Center is created and delegated to the SharedServices account. Requires
  ``identity-center`` (Requirement.IDENTITY_CENTER), derived from the ``identityCenter`` block in
  iam-config.yaml; the Organizations-only variant omits it and the test is recorded ``not_run``.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pytest
from cats import GetAccountFixture, cats, cats_requires

from cats_utils.accounts import non_management_accounts
from cats_utils.boto import DEFAULT_RETRY_CONFIG
from cats_utils.cats_cache import get_local_policy_names
from cats_utils.evidence import Evidence
from cats_utils.requirement import Requirement
from lza_utils.lza_config import lza_config

if TYPE_CHECKING:
    from cats_types import ManagementAccount, SharedServicesAccount

logger = logging.getLogger(__name__)


@pytest.mark.parametrize("account_fixture_name", non_management_accounts())
@cats(standard_name=["LZA-SEC-IAM-POL-1"], test_suite="iam", test_id="pol-1", evidence=Evidence.CONFIGURATION)
def test_boundary_policy_exists(account_fixture_name: str, get_account_fixture: GetAccountFixture) -> None:
    """Verify LZA default boundary policy exists in account."""
    # arrange
    account = get_account_fixture(account_fixture_name)
    expected_policy_name = f"{lza_config().accelerator_prefix}-End-User-Policy"

    # act
    policy_names = get_local_policy_names(account)

    # assert
    assert expected_policy_name in policy_names, f"Boundary policy '{expected_policy_name}' not found in {account_fixture_name}"


@pytest.mark.parametrize("account_fixture_name", non_management_accounts())
@cats(standard_name=["LZA-SEC-IAM-POL-2"], test_suite="iam", test_id="pol-2", evidence=Evidence.CONFIGURATION)
def test_ssm_s3_policy_exists(account_fixture_name: str, get_account_fixture: GetAccountFixture) -> None:
    """Verify LZA default Systems Manager S3 policy exists in account."""
    # arrange
    account = get_account_fixture(account_fixture_name)
    expected_policy_name = f"{lza_config().accelerator_prefix}-Default-SSM-S3-Policy"

    # act
    policy_names = get_local_policy_names(account)

    # assert
    assert expected_policy_name in policy_names, f"SSM S3 policy '{expected_policy_name}' not found in {account_fixture_name}"


@cats_requires(Requirement.IDENTITY_CENTER)
@cats(standard_name=["LZA-SEC-IDC-1"], test_suite="iam", test_id="idc-1", evidence=Evidence.CONFIGURATION)
def test_identity_center_delegated_to_shared_services(
    Management_account: ManagementAccount,
    SharedServices_account: SharedServicesAccount,
) -> None:
    """Verify Identity Center is created and delegated to SharedServices account.

    Requires ``identity-center``: without the ``identityCenter`` block LZA manages no instance and
    delegates no administrator, so there is nothing for this control to verify.
    """
    # arrange
    org_client = Management_account.session.client("organizations", region_name=lza_config().home_region, config=DEFAULT_RETRY_CONFIG)
    sso_client = Management_account.session.client("sso-admin", region_name=lza_config().home_region, config=DEFAULT_RETRY_CONFIG)

    # act - verify Identity Center instance exists
    instances = [instance for page in sso_client.get_paginator("list_instances").paginate() for instance in page["Instances"]]
    assert instances, "No Identity Center instances found"

    # act - verify SharedServices is delegated admin
    delegated_admins = [
        admin
        # Service principals keep the same suffix in every partition.
        for page in org_client.get_paginator("list_delegated_administrators").paginate(ServicePrincipal="sso.amazonaws.com")  # partition: fixed
        for admin in page["DelegatedAdministrators"]
    ]
    delegated_account_ids = [admin["Id"] for admin in delegated_admins]

    # assert
    assert SharedServices_account.account_id in delegated_account_ids, (
        f"SharedServices ({SharedServices_account.account_id}) is not delegated as Identity Center administrator"
    )

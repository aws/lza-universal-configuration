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
CATS - SCP and RCP Enforcement: Root Access, RDS Encryption, EFS Encryption,
KMS Key Protection

This test verifies:
- LZA-G-SCP-32: Restricts root account access
- LZA-G-SCP-33: Restricts creation of EFS without encryption
- LZA-G-SCP-34: Restricts creation of RDS without encryption
- LZA-G-RCP-13: Restricts modification of LZA KMS settings
"""

from __future__ import annotations

import logging
import secrets
from typing import TYPE_CHECKING

import pytest
from botocore.exceptions import ClientError
from cats import GetAccountFixture, cats

from cats_utils.accounts import core_ou_accounts, non_management_accounts
from cats_utils.boto import ACCESS_DENIED_NOT_BY_IDENTITY_POLICY, DEFAULT_RETRY_CONFIG
from cats_utils.evidence import Evidence
from lza_utils.lza_config import lza_config

if TYPE_CHECKING:
    from cats_types import ManagementAccount

logger = logging.getLogger(__name__)


@cats(standard_name=["LZA-G-SCP-32"], test_suite="scp", test_id="32", mutating=False, evidence=Evidence.CONFIGURATION)
def test_root_access_restriction_scp_exists(Management_account: ManagementAccount) -> None:
    """Verify SCP restricting root account access exists in the organization."""
    # arrange
    client = Management_account.session.client("organizations", region_name=lza_config().home_region, config=DEFAULT_RETRY_CONFIG)

    # act - search for SCP with root access restrictions
    all_policy_contents = {
        policy["Name"]: client.describe_policy(PolicyId=policy["Id"])["Policy"]["Content"]
        for page in client.get_paginator("list_policies").paginate(Filter="SERVICE_CONTROL_POLICY")
        for policy in page["Policies"]
    }
    root_scps = [
        name for name, content in all_policy_contents.items() if "aws:PrincipalArn" in content and ":root" in content and "aws:AssumedRoot" in content
    ]

    # assert
    assert root_scps, "No SCP found with root account access restrictions (aws:PrincipalArn :root + aws:AssumedRoot)"


@pytest.mark.parametrize("account_fixture_name", non_management_accounts())
@cats(standard_name=["LZA-G-SCP-34"], test_suite="scp", test_id="34", mutating=True, evidence=Evidence.BEHAVIORAL)
def test_scp_blocks_unencrypted_rds_creation(account_fixture_name: str, get_account_fixture: GetAccountFixture) -> None:
    """Verify SCP denies creation of RDS instances without encryption."""
    # arrange
    account = get_account_fixture(account_fixture_name)
    client = account.session.client("rds", region_name=lza_config().home_region, config=DEFAULT_RETRY_CONFIG)

    # act & assert
    with pytest.raises(ClientError, match="explicit deny in a service control policy"):
        client.create_db_instance(
            DBInstanceIdentifier=f"cats-scp-test-{account.account_id}",
            DBInstanceClass="db.t3.micro",
            Engine="mysql",
            MasterUsername="testuser",
            # Never used: the SCP denies the call. Generated so no literal that looks like a
            # credential sits in the repository for secret scanners to flag.
            MasterUserPassword=secrets.token_urlsafe(24),
            AllocatedStorage=20,
            StorageEncrypted=False,
        )


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@pytest.mark.parametrize("account_fixture_name", non_management_accounts())
@cats(standard_name=["LZA-G-SCP-33"], test_suite="scp", test_id="33", mutating=True, evidence=Evidence.BEHAVIORAL)
def test_scp_blocks_unencrypted_efs_creation(account_fixture_name: str, region: str, get_account_fixture: GetAccountFixture) -> None:
    """Verify SCP denies creation of EFS file systems without encryption."""
    # arrange
    account = get_account_fixture(account_fixture_name)
    client = account.session.client("efs", region_name=region, config=DEFAULT_RETRY_CONFIG)

    # act & assert - SCP uses condition (Encrypted=false) so denial message
    # may say "not authorized to perform" rather than "explicit deny in a service control policy"
    with pytest.raises(ClientError, match=ACCESS_DENIED_NOT_BY_IDENTITY_POLICY):
        client.create_file_system(
            CreationToken=f"cats-scp-test-{account.account_id}-{region}",
            Encrypted=False,
        )


@pytest.mark.parametrize("region", lza_config().enabled_regions)
@pytest.mark.parametrize("account_fixture_name", core_ou_accounts())
@cats(standard_name=["LZA-G-RCP-13"], test_suite="rcp", test_id="13b", mutating=True, evidence=Evidence.BEHAVIORAL)
def test_rcp_blocks_kms_key_modification(account_fixture_name: str, region: str, get_account_fixture: GetAccountFixture) -> None:
    """Verify RCP denies modification of LZA-managed KMS keys."""
    # arrange
    account = get_account_fixture(account_fixture_name)
    client = account.session.client("kms", region_name=region, config=DEFAULT_RETRY_CONFIG)
    tagging_client = account.session.client("resourcegroupstaggingapi", region_name=region, config=DEFAULT_RETRY_CONFIG)

    # act - find KMS keys tagged Accelerator=AWSAccelerator
    accelerator_key_arns = [
        resource["ResourceARN"]
        for page in tagging_client.get_paginator("get_resources").paginate(
            ResourceTypeFilters=["kms:key"],
            TagFilters=[{"Key": "Accelerator", "Values": ["AWSAccelerator"]}],
        )
        for resource in page["ResourceTagMappingList"]
    ]

    assert accelerator_key_arns, f"No KMS keys tagged Accelerator=AWSAccelerator found in {account_fixture_name} {region}"

    # assert - attempt to update the key description (denied by RCP)
    with pytest.raises(ClientError, match="explicit deny in a resource control policy"):
        client.update_key_description(KeyId=accelerator_key_arns[0], Description="cats-scp-test")

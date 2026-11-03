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
CATS - SCP Enforcement: LZA installer resources (container deployment only)

This test verifies:
- LZA-G-SCP-38: Restricts the deletion of LZA installer resources in the deployment account.
  GRINSTRES1 denies deletes on resources tagged ``Accelerator=<AcceleratorPrefix>``; GRINSTRES2
  denies them on the module state tables and log groups tagged ``Accelerator=<AcceleratorQualifier>``.

Recorded ``not_run`` unless ``test_selection.provides`` lists ``container-deployment``: the
``LzaDeployment-Guardrails`` SCPs attach only to the LzaDeployment OU that variant creates. Their
other 17 statements apply controls the pack already probes (LZA-G-SCP-1 to -35) and are
evidenced by running those probes in the deployment account; see
``cats_utils.accounts.non_management_accounts``.

Both denies key on ``aws:ResourceTag``, so each probe aims at a real tagged resource the
InstallerContainerStack creates, the way LZA-G-SCP-36 untags ``<prefix>-Backup-Role``. The
prefix-tagged target is the stack's VPC and the action ``ec2:DeleteTags``: the one action in
GRINSTRES1 that is recoverable were the deny absent. GRINSTRES2 denies only ``DeleteTable`` and
``DeleteLogGroup``; the verbose module log group, named after the qualifier, is the smaller loss.
"""

from __future__ import annotations

import pytest
from botocore.exceptions import ClientError
from cats import GetAccountFixture, cats, cats_requires

from cats_utils.accounts import lza_deployment_account
from cats_utils.boto import DEFAULT_RETRY_CONFIG
from cats_utils.evidence import Evidence
from cats_utils.requirement import Requirement
from lza_utils.lza_config import lza_config


@cats_requires(Requirement.CONTAINER_DEPLOYMENT)
@cats(standard_name=["LZA-G-SCP-38"], test_suite="scp", test_id="38a", mutating=True, evidence=Evidence.BEHAVIORAL)
def test_scp_blocks_installer_resource_untagging(get_account_fixture: GetAccountFixture) -> None:
    """Verify SCP denies removing the Accelerator tag from the installer VPC (GRINSTRES1)."""
    # arrange
    config = lza_config()
    deployment_account = get_account_fixture(lza_deployment_account())
    client = deployment_account.session.client("ec2", region_name=config.home_region, config=DEFAULT_RETRY_CONFIG)
    vpcs = client.describe_vpcs(Filters=[{"Name": "tag:Accelerator", "Values": [config.accelerator_prefix]}])["Vpcs"]
    assert len(vpcs) == 1, (
        f"Expected one VPC tagged Accelerator={config.accelerator_prefix} in {deployment_account.name}, found {[v['VpcId'] for v in vpcs]}"
    )

    # act & assert
    with pytest.raises(ClientError, match="explicit deny in a service control policy"):
        client.delete_tags(Resources=[vpcs[0]["VpcId"]], Tags=[{"Key": "Accelerator"}])


@cats_requires(Requirement.CONTAINER_DEPLOYMENT)
@cats(standard_name=["LZA-G-SCP-38"], test_suite="scp", test_id="38b", mutating=True, evidence=Evidence.BEHAVIORAL)
def test_scp_blocks_installer_module_log_group_deletion(get_account_fixture: GetAccountFixture) -> None:
    """Verify SCP denies deleting the installer's module log group, tagged with the qualifier (GRINSTRES2)."""
    # arrange
    config = lza_config()
    deployment_account = get_account_fixture(lza_deployment_account())
    client = deployment_account.session.client("logs", region_name=config.home_region, config=DEFAULT_RETRY_CONFIG)
    log_group_name = f"{config.replacements['AcceleratorQualifier']}-Module-Verbose-Logs"

    # act & assert
    with pytest.raises(ClientError, match="explicit deny in a service control policy"):
        client.delete_log_group(logGroupName=log_group_name)

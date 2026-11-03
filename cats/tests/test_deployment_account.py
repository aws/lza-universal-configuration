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
CATS - LZA Deployment Account (container deployment only)

This test verifies:
- LZA-G-ACT-7: the dedicated deployment account sits in the LzaDeployment OU and hosts the
  InstallerContainerStack with its ECS cluster, RunEngine SSM document and config bucket.
- LZA-G-OM-6: the LzaDeployment OU exists and carries exactly the SCPs organization-config.yaml
  targets at it (the Deployment-Guardrails policies), so the OU governs the deployment account.
  AWS-managed ``FullAWSAccess`` and the ``aws-guardrails-*`` SCP Control Tower attaches to every
  OU it governs are not declared in organization-config.yaml and are excluded from the comparison.
- LZA-IGW-2: the deployment account has exactly one VPC, in the home region, with one attached
  internet gateway and no VPC or internet gateway in any other enabled region; and every default
  route in that VPC targets either the attached internet gateway or an available NAT gateway,
  with every available NAT gateway routed to. The deployment account's network is created by the
  InstallerContainerStack rather than declared in network-config.yaml, and the stack publishes no
  VPC identifier (no output, no SSM parameter), so the expected state is the Universal
  Configuration design stated above, the VPC is identified as the account's only one, and the
  evidence is what EC2 reports.

Recorded ``not_run`` unless ``test_selection.provides`` lists ``container-deployment``. The
deployment account is the one in the ``LzaDeployment`` OU of accounts-config.yaml (its name
varies between configurations) and must be declared in cats.yaml tagged ``lza-deployment``,
which is how the fixture is resolved. It is resolved with ``get_account_fixture`` rather than
a fixture parameter because the engine warns about undeclared account fixtures at collection,
before selection holds these tests back.

The InstallerContainerStack names its resources after the ``AcceleratorQualifier`` when
deployed outside the management account (``lza1-ecs-cluster``, ``lza1-RunEngine``), so the
stack is found by its ``LzaDeploymentAccountEmail`` parameter and
``DeploySolutionDocumentOutput`` output, and its resources read by logical ID.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from cats import GetAccountFixture, cats, cats_requires

from cats_utils.accounts import lza_deployment_account
from cats_utils.boto import DEFAULT_RETRY_CONFIG
from cats_utils.cats_cache import (
    get_account_ids_in_parent,
    get_organization_accounts,
    get_organization_ous,
    get_s3_buckets,
    get_scps_attached_to_target,
)
from cats_utils.ec2 import get_default_route_targets_by_vpc_id, get_internet_gateways, get_nat_gateways, get_vpcs
from cats_utils.evidence import Evidence
from cats_utils.requirement import Requirement
from lza_utils.lza_config import CONTAINER_DEPLOYMENT_OU, lza_config

if TYPE_CHECKING:
    from mypy_boto3_cloudformation.type_defs import StackTypeDef

    from cats_types import CatsAccountProtocol, ManagementAccount

_DEPLOYMENT_ACCOUNT_EMAIL_PARAMETER = "LzaDeploymentAccountEmail"
_DEPLOY_DOCUMENT_OUTPUT = "DeploySolutionDocumentOutput"
_EXISTING_CONFIG_BUCKET_PARAMETER = "ExistingConfigBucketName"
# Logical IDs in the InstallerContainerStack. ConfigBucket exists only when UseExistingConfig is No.
_ECS_CLUSTER = "EcsCluster"
_DEPLOY_DOCUMENT = "DeploySolutionDocument"
_CONFIG_BUCKET = "ConfigBucket"
# Control Tower attaches one SCP of this name to every OU it governs; it is customer-managed in
# Organizations' terms (AwsManaged is False) but not declared in organization-config.yaml.
_CONTROL_TOWER_SCP_PREFIX = "aws-guardrails-"


def _get_installer_container_stack(deployment_account: CatsAccountProtocol) -> StackTypeDef:
    """The one InstallerContainerStack in the deployment account's home region, found by shape (module docstring)."""
    client = deployment_account.session.client("cloudformation", region_name=lza_config().home_region, config=DEFAULT_RETRY_CONFIG)
    matching = [
        stack
        for page in client.get_paginator("describe_stacks").paginate()
        for stack in page["Stacks"]
        if any(parameter["ParameterKey"] == _DEPLOYMENT_ACCOUNT_EMAIL_PARAMETER for parameter in stack.get("Parameters", []))
        and any(output["OutputKey"] == _DEPLOY_DOCUMENT_OUTPUT for output in stack.get("Outputs", []))
    ]
    assert len(matching) == 1, (
        f"Expected exactly one InstallerContainerStack in {deployment_account.name}, found {[s['StackName'] for s in matching]}"
    )
    return matching[0]


def _get_stack_resource_physical_ids(deployment_account: CatsAccountProtocol, stack_name: str) -> dict[str, str]:
    """``{logical_id: physical_id}`` for every resource in a stack."""
    client = deployment_account.session.client("cloudformation", region_name=lza_config().home_region, config=DEFAULT_RETRY_CONFIG)
    return {
        resource["LogicalResourceId"]: resource["PhysicalResourceId"]
        for page in client.get_paginator("list_stack_resources").paginate(StackName=stack_name)
        for resource in page["StackResourceSummaries"]
        if "PhysicalResourceId" in resource
    }


def _deployment_vpc_id(deployment_account: CatsAccountProtocol) -> str:
    """The one VPC in the deployment account's home region (module docstring)."""
    vpc_ids = sorted(vpc["VpcId"] for vpc in get_vpcs(deployment_account, lza_config().home_region))
    assert len(vpc_ids) == 1, f"Expected exactly one VPC in {deployment_account.name} ({lza_config().home_region}), found {vpc_ids}"
    return vpc_ids[0]


def _attached_internet_gateway_ids(deployment_account: CatsAccountProtocol, region: str, vpc_id: str) -> list[str]:
    """Sorted IDs of the internet gateways attached to ``vpc_id``."""
    return sorted(
        igw["InternetGatewayId"]
        for igw in get_internet_gateways(deployment_account, region)
        if any(attachment["VpcId"] == vpc_id for attachment in igw.get("Attachments", []))
    )


def _config_bucket_name(stack: StackTypeDef, resources: dict[str, str]) -> str:
    """The stack's own ConfigBucket, or the pre-existing bucket it was pointed at."""
    if _CONFIG_BUCKET in resources:
        return resources[_CONFIG_BUCKET]
    parameters = {p["ParameterKey"]: p["ParameterValue"] for p in stack.get("Parameters", []) if "ParameterValue" in p}
    existing = parameters.get(_EXISTING_CONFIG_BUCKET_PARAMETER, "")
    assert existing != "", f"Stack '{stack['StackName']}' creates no {_CONFIG_BUCKET} and names no {_EXISTING_CONFIG_BUCKET_PARAMETER}"
    return existing


@cats_requires(Requirement.CONTAINER_DEPLOYMENT)
@cats(standard_name=["LZA-G-ACT-7"], test_suite="deployment", test_id="1", evidence=Evidence.CONFIGURATION)
def test_deployment_account_in_lza_deployment_ou(Management_account: ManagementAccount, get_account_fixture: GetAccountFixture) -> None:
    """Verify the deployment account exists in the organization and sits in the LzaDeployment OU.

    Matched by account ID: the account's ``name`` in accounts-config.yaml is a logical key that
    LZA documents need not equal the Organizations account name.
    """
    # arrange
    deployment_account = get_account_fixture(lza_deployment_account())
    organization_account_ids = sorted(get_organization_accounts(Management_account).values())
    assert deployment_account.account_id in organization_account_ids, (
        f"Deployment account {deployment_account.account_id} not found in organization. Accounts: {organization_account_ids}"
    )
    ous = get_organization_ous(Management_account)
    assert CONTAINER_DEPLOYMENT_OU in ous, f"OU '{CONTAINER_DEPLOYMENT_OU}' not found in organization. OUs: {sorted(ous)}"

    # act
    account_ids_in_ou = get_account_ids_in_parent(Management_account, ous[CONTAINER_DEPLOYMENT_OU])

    # assert
    assert deployment_account.account_id in account_ids_in_ou, (
        f"Deployment account {deployment_account.account_id} is not in the '{CONTAINER_DEPLOYMENT_OU}' OU: {sorted(account_ids_in_ou)}"
    )


@cats_requires(Requirement.CONTAINER_DEPLOYMENT)
@cats(standard_name=["LZA-G-ACT-7"], test_suite="deployment", test_id="2", evidence=Evidence.CONFIGURATION)
def test_installer_container_stack_deployed(get_account_fixture: GetAccountFixture) -> None:
    """Verify the InstallerContainerStack is deployed with its ECS cluster, RunEngine document and config bucket."""
    # arrange
    deployment_account = get_account_fixture(lza_deployment_account())
    home_region = lza_config().home_region
    stack = _get_installer_container_stack(deployment_account)
    assert stack["StackStatus"] in ("CREATE_COMPLETE", "UPDATE_COMPLETE"), f"Stack '{stack['StackName']}' status is {stack['StackStatus']}"
    resources = _get_stack_resource_physical_ids(deployment_account, stack["StackName"])
    missing = sorted({_ECS_CLUSTER, _DEPLOY_DOCUMENT} - set(resources))
    assert missing == [], f"Stack '{stack['StackName']}' lacks resources {missing}"
    bucket_name = _config_bucket_name(stack, resources)
    ecs_client = deployment_account.session.client("ecs", region_name=home_region, config=DEFAULT_RETRY_CONFIG)
    ssm_client = deployment_account.session.client("ssm", region_name=home_region, config=DEFAULT_RETRY_CONFIG)
    expected = {"ecs_cluster_status": "ACTIVE", "ssm_document_status": "Active", "config_bucket_present": True}

    # act
    clusters = ecs_client.describe_clusters(clusters=[resources[_ECS_CLUSTER]])["clusters"]
    document = ssm_client.describe_document(Name=resources[_DEPLOY_DOCUMENT])["Document"]
    actual = {
        "ecs_cluster_status": clusters[0].get("status", "<not returned>") if clusters else "<cluster not found>",
        "ssm_document_status": document.get("Status", "<not returned>"),
        "config_bucket_present": bucket_name in get_s3_buckets(deployment_account),
    }

    # assert
    assert actual == expected, (
        f"Stack '{stack['StackName']}': cluster {resources[_ECS_CLUSTER]}, document {resources[_DEPLOY_DOCUMENT]}, bucket {bucket_name}"
    )


def _configured_scp_names_targeting_ou(ou_name: str) -> list[str]:
    """Names of configured SCPs whose deploymentTargets.organizationalUnits lists the OU.

    An SCP that also declares ``excludedAccounts`` is attached by LZA to the remaining
    accounts individually rather than to the OU, so its presence here fails loudly rather
    than produce a wrong expected set.
    """
    names: list[str] = []
    for policy in lza_config().organization.service_control_policies:
        if ou_name not in (policy.deployment_targets.organizational_units or []):
            continue
        assert (policy.deployment_targets.excluded_accounts or []) == [], (
            f"SCP '{policy.name}' declares excludedAccounts for OU '{ou_name}', which this test does not support"
        )
        names.append(policy.name)
    return sorted(names)


@cats_requires(Requirement.CONTAINER_DEPLOYMENT)
@cats(standard_name=["LZA-G-OM-6"], test_suite="deployment", test_id="3", evidence=Evidence.CONFIGURATION)
def test_lza_deployment_ou_carries_configured_scps(Management_account: ManagementAccount) -> None:
    """Verify the LzaDeployment OU exists and has exactly the configured Deployment-Guardrails SCPs attached.

    Two policies attached to the OU are not LZA's and are left out of the comparison:
    ``FullAWSAccess`` (AWS-managed, attached to every OU by default) and Control Tower's
    ``aws-guardrails-*`` SCP, which Control Tower attaches to every OU it governs.
    """
    # arrange
    expected_scp_names = _configured_scp_names_targeting_ou(CONTAINER_DEPLOYMENT_OU)
    assert expected_scp_names != [], f"organization-config.yaml targets no SCP at the '{CONTAINER_DEPLOYMENT_OU}' OU"
    ous = get_organization_ous(Management_account)
    assert CONTAINER_DEPLOYMENT_OU in ous, f"OU '{CONTAINER_DEPLOYMENT_OU}' not found in organization. OUs: {sorted(ous)}"

    # act
    attached_policies = get_scps_attached_to_target(Management_account, ous[CONTAINER_DEPLOYMENT_OU])
    actual_scp_names = sorted(
        policy["Name"] for policy in attached_policies if policy["AwsManaged"] is False and not policy["Name"].startswith(_CONTROL_TOWER_SCP_PREFIX)
    )

    # assert
    all_attached_scp_names = sorted(policy["Name"] for policy in attached_policies)
    assert actual_scp_names == expected_scp_names, (
        f"SCPs attached to the '{CONTAINER_DEPLOYMENT_OU}' OU differ from organization-config.yaml. All attached: {all_attached_scp_names}"
    )


@cats_requires(Requirement.CONTAINER_DEPLOYMENT)
@cats(standard_name=["LZA-IGW-2"], test_suite="deployment", test_id="4", evidence=Evidence.CONFIGURATION)
def test_deployment_account_internet_gateway_in_home_vpc_only(get_account_fixture: GetAccountFixture) -> None:
    """Verify the deployment account's one VPC has one attached internet gateway and no other region has a VPC or gateway."""
    # arrange
    deployment_account = get_account_fixture(lza_deployment_account())
    home_region = lza_config().home_region
    enabled_regions = lza_config().enabled_regions
    vpc_id = _deployment_vpc_id(deployment_account)
    expected = {
        "vpcs_by_region": {region: 0 for region in enabled_regions} | {home_region: 1},
        "attached_internet_gateways_by_region": {region: 0 for region in enabled_regions} | {home_region: 1},
        "unattached_internet_gateways_by_region": {region: 0 for region in enabled_regions},
    }

    # act
    internet_gateways_by_region = {region: get_internet_gateways(deployment_account, region) for region in enabled_regions}
    actual = {
        "vpcs_by_region": {region: len(get_vpcs(deployment_account, region)) for region in enabled_regions},
        "attached_internet_gateways_by_region": {
            region: len([igw for igw in igws if igw.get("Attachments", [])]) for region, igws in internet_gateways_by_region.items()
        },
        "unattached_internet_gateways_by_region": {
            region: len([igw for igw in igws if not igw.get("Attachments", [])]) for region, igws in internet_gateways_by_region.items()
        },
    }

    # assert
    assert actual == expected, (
        f"Deployment account {deployment_account.name} internet gateway footprint differs from one attached gateway on VPC {vpc_id}"
    )


@cats_requires(Requirement.CONTAINER_DEPLOYMENT)
@cats(standard_name=["LZA-IGW-2"], test_suite="deployment", test_id="5", evidence=Evidence.CONFIGURATION)
def test_deployment_vpc_default_routes_only_via_nat_and_internet_gateway(get_account_fixture: GetAccountFixture) -> None:
    """Verify every default route in the deployment VPC targets an available NAT gateway or its attached internet gateway.

    Every available NAT gateway in the VPC must be routed to, and nothing else (transit gateway,
    peering, instance, blackhole) may carry a default route, so the account's only internet path
    is outbound through NAT from private subnets and the internet gateway from public ones.
    """
    # arrange
    deployment_account = get_account_fixture(lza_deployment_account())
    home_region = lza_config().home_region
    vpc_id = _deployment_vpc_id(deployment_account)
    attached_internet_gateway_ids = _attached_internet_gateway_ids(deployment_account, home_region, vpc_id)
    available_nat_gateway_ids = sorted(
        nat_gateway["NatGatewayId"]
        for nat_gateway in get_nat_gateways(deployment_account, home_region)
        if nat_gateway["VpcId"] == vpc_id and nat_gateway["State"] == "available"
    )
    assert available_nat_gateway_ids != [], f"No available NAT gateway in deployment VPC {vpc_id}"
    expected = sorted(attached_internet_gateway_ids + available_nat_gateway_ids)

    # act
    actual = get_default_route_targets_by_vpc_id(deployment_account, home_region).get(vpc_id, [])

    # assert
    assert actual == expected, f"Default route targets in deployment VPC {vpc_id} are not exactly its attached IGW and available NAT gateways"

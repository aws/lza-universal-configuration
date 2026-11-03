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
CATS - SCP Enforcement: AgentCore

This test verifies:
- LZA-G-SCP-19: Enforces AgentCore VPC settings for resource creation
- LZA-G-SCP-27: Enforces AgentCore Runtime invocation only from a VPC source
- LZA-G-SCP-37: Enforces customer-managed KMS encryption for AgentCore Memory

Each control gets the same triplet: (a) the deployed statement equals the configured
one, (b) the policy is attached exactly where the config says, (c) the denied action
is actually denied. (a) and (b) are shared implementations parametrized per SCP that
declares the control's statement Sid; only (c) is control-specific.
"""

from __future__ import annotations

import json
import time
import uuid
from typing import TYPE_CHECKING, Any

import pytest
from botocore.exceptions import ClientError
from cats import AccountUnderTest, cats
from cats.config import Settings

from cats_utils.boto import ACCESS_DENIED_NOT_BY_IDENTITY_POLICY, DEFAULT_RETRY_CONFIG, get_error_code
from cats_utils.cats_cache import get_organization_accounts, get_organization_ous, get_organization_scps
from cats_utils.evidence import Evidence
from lza_utils.lza_config import load_policy_file, lza_config

if TYPE_CHECKING:
    from mypy_boto3_bedrock_agentcore_control.client import BedrockAgentCoreControlClient

    from cats_types import SharedServicesAccount
    from lza_types.organization_config import ServiceControlPolicyConfig

AGENTCORE_STATEMENT_SID = "GRAGENTCORE1"
AGENTCORE_INVOKE_STATEMENT_SID = "GRAGENTCORE2"
AGENTCORE_MEMORY_KMS_STATEMENT_SID = "GRAGENTCORE3"


def _statements_with_sid(policy_document: dict[str, Any], sid: str) -> list[dict[str, Any]]:
    """Return all statements in a policy document that carry the given Sid."""
    return [statement for statement in policy_document["Statement"] if statement.get("Sid") == sid]


def get_scp_names_declaring_sid(sid: str) -> list[str]:
    """Names of configured SCPs that declare a statement with the given Sid."""
    policies = lza_config().organization.service_control_policies
    names = sorted(policy.name for policy in policies if _statements_with_sid(load_policy_file(policy.policy), sid))
    assert names, f"No configured SCP declares the {sid} statement"
    return names


def _configured_scp(policy_name: str) -> ServiceControlPolicyConfig:
    """The configured SCP entry by name."""
    policies_by_name = {policy.name: policy for policy in lza_config().organization.service_control_policies}
    return policies_by_name[policy_name]


def _deployed_scp_id(Management_account: AccountUnderTest, policy_name: str) -> str:
    """The Organizations policy ID of a configured SCP, failing if it is not deployed."""
    deployed_policies = get_organization_scps(Management_account)
    assert policy_name in deployed_policies, f"Configured SCP '{policy_name}' is not deployed"
    return deployed_policies[policy_name]["Id"]


def assert_scp_statement_matches_config(Management_account: AccountUnderTest, policy_name: str, sid: str) -> None:
    """Deployed statements with the given Sid equal the configured policy's, byte-for-byte.

    The configured side is resolved through the LZA ${VARIABLE} substitution helper;
    an unresolved placeholder fails the equality below with a visible diff.
    """
    # arrange
    config = lza_config()
    expected_statements = _statements_with_sid(config.resolve_policy_file(_configured_scp(policy_name).policy), sid)

    # act
    client = Management_account.session.client("organizations", region_name=config.home_region, config=DEFAULT_RETRY_CONFIG)
    content = json.loads(client.describe_policy(PolicyId=_deployed_scp_id(Management_account, policy_name))["Policy"]["Content"])
    deployed_statements = _statements_with_sid(content, sid)

    # assert
    assert deployed_statements == expected_statements, f"Deployed {sid} in '{policy_name}' differs from configured policy"


def assert_scp_attachment_scope(Management_account: AccountUnderTest, policy_name: str) -> None:
    """Deployed SCP attachments equal the configured deploymentTargets, resolved to organization IDs."""
    # arrange - excludedAccounts changes how LZA attaches the policy; fail loudly rather
    # than compute a wrong expected set if a config ever declares it here.
    config = lza_config()
    deployment_targets = _configured_scp(policy_name).deployment_targets
    excluded_accounts = deployment_targets.excluded_accounts or []
    assert excluded_accounts == [], f"SCP '{policy_name}' declares excludedAccounts, which this test does not support"
    target_accounts = deployment_targets.accounts or []
    target_ous = deployment_targets.organizational_units or []
    accounts_by_name = get_organization_accounts(Management_account)
    ous_by_path = get_organization_ous(Management_account)
    missing_targets = sorted(set(target_accounts) - set(accounts_by_name)) + sorted(set(target_ous) - set(ous_by_path))
    assert missing_targets == [], f"Configured deployment targets not found in the organization: {missing_targets}"
    expected_target_ids = {accounts_by_name[name] for name in target_accounts} | {ous_by_path[path] for path in target_ous}

    # act
    client = Management_account.session.client("organizations", region_name=config.home_region, config=DEFAULT_RETRY_CONFIG)
    actual_target_ids = {
        target["TargetId"]
        for page in client.get_paginator("list_targets_for_policy").paginate(PolicyId=_deployed_scp_id(Management_account, policy_name))
        for target in page["Targets"]
    }

    # assert
    assert actual_target_ids == expected_target_ids, f"SCP '{policy_name}' attachments do not match configured deployment targets"


# --- LZA-G-SCP-19: AgentCore resources must be created with VPC network settings ---


@pytest.mark.parametrize("policy_name", get_scp_names_declaring_sid(AGENTCORE_STATEMENT_SID))
@cats(standard_name=["LZA-G-SCP-19"], test_suite="scp", test_id="19a", mutating=False, evidence=Evidence.CONFIGURATION)
def test_scp_agentcore_statement_matches_config(policy_name: str, Management_account: AccountUnderTest) -> None:
    """LZA-G-SCP-19: Deployed GRAGENTCORE1 statement matches the configured policy JSON."""
    assert_scp_statement_matches_config(Management_account, policy_name, AGENTCORE_STATEMENT_SID)


@pytest.mark.parametrize("policy_name", get_scp_names_declaring_sid(AGENTCORE_STATEMENT_SID))
@cats(standard_name=["LZA-G-SCP-19"], test_suite="scp", test_id="19b", mutating=False, evidence=Evidence.CONFIGURATION)
def test_scp_agentcore_attachment_scope(policy_name: str, Management_account: AccountUnderTest) -> None:
    """LZA-G-SCP-19: SCP attachments match the configured deployment targets exactly."""
    assert_scp_attachment_scope(Management_account, policy_name)


def _delete_browser(client: BedrockAgentCoreControlClient, browser_id: str) -> None:
    """Delete a browser created when the SCP unexpectedly allowed it.

    Teardown on an already-failing path: raises on unexpected errors rather
    than deciding the test outcome (pytest reports it as an error).
    """
    delete_token = str(uuid.uuid4())
    for _ in range(15):
        try:
            client.delete_browser(browserId=browser_id, clientToken=delete_token)
            return
        except ClientError as error:
            if get_error_code(error) == "ResourceNotFoundException":
                return
            if get_error_code(error) != "ConflictException":
                raise
        time.sleep(2)
    raise TimeoutError(f"AgentCore browser {browser_id} still transitioning after delete retries")


@cats(standard_name=["LZA-G-SCP-19"], test_suite="scp", test_id="19c", mutating=True, evidence=Evidence.BEHAVIORAL)
def test_scp_blocks_agentcore_public_browser_creation(SharedServices_account: SharedServicesAccount) -> None:
    """LZA-G-SCP-19: SCP denies AgentCore browser creation without VPC settings."""
    # arrange
    config = lza_config()
    client = SharedServices_account.session.client(
        "bedrock-agentcore-control",
        region_name=config.home_region,
        config=DEFAULT_RETRY_CONFIG,
    )
    browser_name = f"{config.accelerator_prefix}-cats-scp-19-{uuid.uuid4().hex}"

    # act & assert - bedrock-agentcore-control returns a bare AccessDenied/AccessDeniedException
    # (not the "explicit deny in a service control policy" message) when the SCP's
    # condition-based deny blocks CreateBrowser, so match the code alone.
    browser_id: str | None = None
    try:
        with pytest.raises(ClientError, match=ACCESS_DENIED_NOT_BY_IDENTITY_POLICY):
            browser_id = client.create_browser(
                name=browser_name,
                networkConfiguration={"networkMode": "PUBLIC"},
                clientToken=str(uuid.uuid4()),
            )["browserId"]
    finally:
        if browser_id is not None:
            _delete_browser(client, browser_id)


# --- LZA-G-SCP-27: AgentCore Runtime may only be invoked from a VPC source ---


@pytest.mark.parametrize("policy_name", get_scp_names_declaring_sid(AGENTCORE_INVOKE_STATEMENT_SID))
@cats(standard_name=["LZA-G-SCP-27"], test_suite="scp", test_id="27a", mutating=False, evidence=Evidence.CONFIGURATION)
def test_scp_agentcore_invoke_statement_matches_config(policy_name: str, Management_account: AccountUnderTest) -> None:
    """LZA-G-SCP-27: Deployed GRAGENTCORE2 statement matches the configured policy JSON."""
    assert_scp_statement_matches_config(Management_account, policy_name, AGENTCORE_INVOKE_STATEMENT_SID)


@pytest.mark.parametrize("policy_name", get_scp_names_declaring_sid(AGENTCORE_INVOKE_STATEMENT_SID))
@cats(standard_name=["LZA-G-SCP-27"], test_suite="scp", test_id="27b", mutating=False, evidence=Evidence.CONFIGURATION)
def test_scp_agentcore_invoke_attachment_scope(policy_name: str, Management_account: AccountUnderTest) -> None:
    """LZA-G-SCP-27: SCP attachments match the configured deployment targets exactly."""
    assert_scp_attachment_scope(Management_account, policy_name)


@cats(standard_name=["LZA-G-SCP-27"], test_suite="scp", test_id="27c", mutating=False, evidence=Evidence.BEHAVIORAL)
def test_scp_blocks_agentcore_invoke_from_non_vpc(SharedServices_account: SharedServicesAccount) -> None:
    """LZA-G-SCP-27: SCP denies AgentCore Runtime invocation from a non-VPC source."""
    # arrange - InvokeAgentRuntime lives on the bedrock-agentcore data-plane client,
    # distinct from the -control plane used by SCP-19. The SCP denies when
    # aws:SourceVpc is null, so a public-network call to the regional endpoint
    # triggers the deny regardless of whether the referenced runtime exists.
    # The placeholder ARN is well-formed and never created: were the SCP absent,
    # the call would surface ResourceNotFoundException rather than pass silently.
    config = lza_config()
    client = SharedServices_account.session.client(
        "bedrock-agentcore",
        region_name=config.home_region,
        config=DEFAULT_RETRY_CONFIG,
    )
    runtime_id = f"cats-scp-27-{uuid.uuid4().hex}"
    partition = Settings().cats_deployment_settings.partition
    fake_runtime_arn = f"arn:{partition}:bedrock-agentcore:{config.home_region}:{SharedServices_account.account_id}:runtime/{runtime_id}"

    # act & assert - bedrock-agentcore returns AccessDenied/AccessDeniedException
    # when the SCP's condition-based deny blocks InvokeAgentRuntime. The test role
    # grants this action explicitly and the matcher rejects identity-policy denials,
    # so an AccessDenied here can only come from an SCP.
    with pytest.raises(ClientError, match=ACCESS_DENIED_NOT_BY_IDENTITY_POLICY):
        client.invoke_agent_runtime(
            agentRuntimeArn=fake_runtime_arn,
            payload=b"{}",
            contentType="application/json",
        )


# --- LZA-G-SCP-37: AgentCore Memory must be encrypted with a customer-managed KMS key ---


@pytest.mark.parametrize("policy_name", get_scp_names_declaring_sid(AGENTCORE_MEMORY_KMS_STATEMENT_SID))
@cats(standard_name=["LZA-G-SCP-37"], test_suite="scp", test_id="37a", mutating=False, evidence=Evidence.CONFIGURATION)
def test_scp_agentcore_memory_kms_statement_matches_config(policy_name: str, Management_account: AccountUnderTest) -> None:
    """LZA-G-SCP-37: Deployed GRAGENTCORE3 statement matches the configured policy JSON."""
    assert_scp_statement_matches_config(Management_account, policy_name, AGENTCORE_MEMORY_KMS_STATEMENT_SID)


@pytest.mark.parametrize("policy_name", get_scp_names_declaring_sid(AGENTCORE_MEMORY_KMS_STATEMENT_SID))
@cats(standard_name=["LZA-G-SCP-37"], test_suite="scp", test_id="37b", mutating=False, evidence=Evidence.CONFIGURATION)
def test_scp_agentcore_memory_kms_attachment_scope(policy_name: str, Management_account: AccountUnderTest) -> None:
    """LZA-G-SCP-37: SCP attachments match the configured deployment targets exactly."""
    assert_scp_attachment_scope(Management_account, policy_name)


def _delete_memory(client: BedrockAgentCoreControlClient, memory_id: str) -> None:
    """Delete a memory created when the SCP unexpectedly allowed it.

    Teardown on an already-failing path: raises on unexpected errors rather
    than deciding the test outcome (pytest reports it as an error).
    """
    delete_token = str(uuid.uuid4())
    for _ in range(15):
        try:
            client.delete_memory(memoryId=memory_id, clientToken=delete_token)
            return
        except ClientError as error:
            if get_error_code(error) == "ResourceNotFoundException":
                return
            if get_error_code(error) != "ConflictException":
                raise
        time.sleep(2)
    raise TimeoutError(f"AgentCore memory {memory_id} still transitioning after delete retries")


@cats(standard_name=["LZA-G-SCP-37"], test_suite="scp", test_id="37c", mutating=True, evidence=Evidence.BEHAVIORAL)
def test_scp_blocks_agentcore_memory_without_cmk(SharedServices_account: SharedServicesAccount) -> None:
    """LZA-G-SCP-37: SCP denies AgentCore memory creation without a customer-managed KMS key."""
    # arrange - GRAGENTCORE3 denies CreateMemory when bedrock-agentcore:KmsKeyArn is
    # null, so omitting encryptionKeyArn is the controlled condition.
    config = lza_config()
    client = SharedServices_account.session.client(
        "bedrock-agentcore-control",
        region_name=config.home_region,
        config=DEFAULT_RETRY_CONFIG,
    )
    # Name must match [a-zA-Z][a-zA-Z0-9_]{0,47}; a shortened uuid keeps it within 48 chars.
    memory_name = f"cats_scp_37_{uuid.uuid4().hex[:16]}"

    # act & assert - bedrock-agentcore-control returns a bare AccessDenied/AccessDeniedException
    # (not the "explicit deny in a service control policy" message) when the SCP's
    # condition-based deny blocks CreateMemory, so match the code alone.
    memory_id: str | None = None
    try:
        with pytest.raises(ClientError, match=ACCESS_DENIED_NOT_BY_IDENTITY_POLICY):
            memory_id = client.create_memory(
                name=memory_name,
                eventExpiryDuration=7,
                clientToken=str(uuid.uuid4()),
            )["memory"]["id"]
    finally:
        if memory_id is not None:
            _delete_memory(client, memory_id)

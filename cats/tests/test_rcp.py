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
CATS - Resource Control Policy (RCP) Verification

Verifies the deployed Core RCP Guardrails policy (``rcp-policies/lza-core-rcp-guardrails-1.json``
in the LZA config). RCP enforcement cannot be probed from inside the Organization: a denial
needs a request from an outside principal or over plain HTTP. Each test instead inspects the
deployed statement that implements its control, twice:

- Control: the statement is a Deny on the control's resource with exactly the condition the
  control requires and at least one action of the control's service. The condition is written
  in the test; the live Organization, the partition and the LZA config supply its values.
- Fidelity: the statement equals the configured one, resolved the way LZA resolves it at
  deploy time (``${ORG_ID}`` from the live Organization, ``${LOGARCHIVE_ACCOUNT_ID}`` from
  the LogArchive account, every other placeholder from the config files).

- LZA-G-RCP-1: S3 operations restricted to AWS services and Organization members
- LZA-G-RCP-2: S3 denied when request originates outside Organization
- LZA-G-RCP-3: SQS denied when request originates outside Organization
- LZA-G-RCP-4: KMS denied when request originates outside Organization
- LZA-G-RCP-5: Secrets Manager denied when request originates outside Organization
- LZA-G-RCP-6: STS denied when request originates outside Organization
- LZA-G-RCP-7: S3 denied over unencrypted HTTP (HTTPS only)
- LZA-G-RCP-8: SQS denied over unencrypted HTTP (HTTPS only)
- LZA-G-RCP-9: KMS denied over unencrypted HTTP (HTTPS only)
- LZA-G-RCP-10: Secrets Manager denied over unencrypted HTTP (HTTPS only)
- LZA-G-RCP-11: STS denied over unencrypted HTTP (HTTPS only)
- LZA-G-RCP-12: Control Tower logs S3 bucket protected
- LZA-G-RCP-13: LZA KMS settings modification restricted
- LZA-G-RCP-14: STS cross-account role assumption restricted to Organization members
- LZA-G-RCP-15: SQS operations restricted to Organization members
- LZA-G-RCP-16: Secrets Manager operations restricted to Organization members
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from cats import cats
from cats.config import Settings

from cats_utils.cats_cache import get_organization, get_organization_rcps, get_rcp_policy_content
from cats_utils.evidence import Evidence
from cats_utils.iam import canonical_statement
from lza_utils.lza_config import lza_config

if TYPE_CHECKING:
    from cats_types import LogArchiveAccount, ManagementAccount
    from lza_types.organization_config import ResourceControlPolicyConfig

_CORE_RCP_NAME_STEM = "Core-Rcp-Guardrails"

# Sids of the configured statements that implement each control.
_S3_DATA_PERIMETER_SID = "GRS3DPB"
_EXTERNAL_SOURCE_SID = "GRECDP"
_SECURE_TRANSPORT_SID = "GRRST"
_LZA_KMS_SID = "GRKMS"
_STS_DATA_PERIMETER_SID = "GRSTSDPB"
_SQS_DATA_PERIMETER_SID = "GRSQSDPB"
_SECRETS_MANAGER_DATA_PERIMETER_SID = "GSMDPB"
_CONTROL_TOWER_LOGS_SID = "GRS3OBJ"


def _core_rcp_name() -> str:
    return f"{lza_config().accelerator_prefix}-{_CORE_RCP_NAME_STEM}"


def _configured_core_rcp() -> ResourceControlPolicyConfig:
    """The Core RCP Guardrails entry in organization-config.yaml."""
    policies_by_name = {policy.name: policy for policy in lza_config().organization.resource_control_policies or []}
    name = _core_rcp_name()
    assert name in policies_by_name, f"RCP '{name}' is not declared in organization-config.yaml. Declared: {sorted(policies_by_name)}"
    return policies_by_name[name]


def _statements_by_sid(document: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Canonical statements keyed by Sid, so deployed and configured content compare by value.

    Organizations stores RCP content with one-element lists collapsed to strings; see
    ``canonical_statement``.
    """
    statements: list[dict[str, Any]] = document["Statement"]
    unnamed = [statement for statement in statements if "Sid" not in statement]
    assert unnamed == [], f"RCP statements must each carry a Sid for this comparison; unnamed: {unnamed}"
    by_sid = {statement["Sid"]: canonical_statement(statement) for statement in statements}
    assert len(by_sid) == len(statements), "RCP statements must each carry a unique Sid for this comparison"
    return by_sid


def _expected_statements(Management_account: ManagementAccount, LogArchive_account: LogArchiveAccount) -> dict[str, dict[str, Any]]:
    """Configured Core RCP Guardrails statements with LZA's deploy-time substitutions applied."""
    deployment_values = {"${ORG_ID}": get_organization(Management_account)["Id"], "${LOGARCHIVE_ACCOUNT_ID}": LogArchive_account.account_id}
    return _statements_by_sid(lza_config().resolve_policy_file(_configured_core_rcp().policy, deployment_values))


def _deployed_statements(Management_account: ManagementAccount) -> dict[str, dict[str, Any]]:
    """Deployed Core RCP Guardrails statements, failing if the policy is not deployed."""
    name = _core_rcp_name()
    rcps = get_organization_rcps(Management_account)
    assert name in rcps, f"RCP '{name}' not found in organization. Found: {sorted(rcps)}"
    return _statements_by_sid(json.loads(get_rcp_policy_content(Management_account, rcps[name]["Id"])))


def _denied_services(statement: dict[str, Any]) -> set[str]:
    """Service namespaces of a Deny statement's actions (``{"s3", "sqs"}``)."""
    assert statement["Effect"] == "Deny", f"Statement {statement['Sid']} is not a Deny"
    actions: str | list[str] = statement["Action"]
    return {action.split(":")[0].lower() for action in ([actions] if isinstance(actions, str) else actions)}


def _canonical_condition(condition: dict[str, dict[str, str | list[str]]]) -> dict[str, Any]:
    """``condition`` in the list form ``_statements_by_sid`` compares in."""
    canonical: dict[str, Any] = canonical_statement({"Condition": condition})["Condition"]
    return canonical


def _organization_principal_condition(Management_account: ManagementAccount) -> dict[str, dict[str, str | list[str]]]:
    """Deny unless the principal belongs to this Organization or is an AWS service principal."""
    org_id = get_organization(Management_account)["Id"]
    return {"BoolIfExists": {"aws:PrincipalIsAWSService": "false"}, "StringNotEqualsIfExists": {"aws:PrincipalOrgID": org_id}}


def _external_source_condition(Management_account: ManagementAccount) -> dict[str, dict[str, str | list[str]]]:
    """Deny an AWS service acting for a resource outside this Organization."""
    org_id = get_organization(Management_account)["Id"]
    return {"StringNotEqualsIfExists": {"aws:SourceOrgID": org_id}, "Bool": {"aws:PrincipalIsAWSService": "true"}, "Null": {"aws:SourceArn": "false"}}


_INSECURE_TRANSPORT_CONDITION: dict[str, dict[str, str | list[str]]] = {"BoolIfExists": {"aws:SecureTransport": "false"}}


def _control_tower_logs_condition() -> dict[str, dict[str, str | list[str]]]:
    """Deny unless called via Config or CloudTrail, by the management access role, or by an AWS service."""
    config = lza_config()
    partition = Settings().cats_deployment_settings.partition
    return {
        "ForAllValues:StringNotEquals": {"aws:CalledVia": ["config.amazonaws.com", "cloudtrail.amazonaws.com"]},  # partition: fixed
        "ArnNotLike": {"aws:PrincipalARN": f"arn:{partition}:iam::*:role/{config.global_.management_account_access_role}"},
        "BoolIfExists": {"aws:PrincipalIsAWSService": "false"},
    }


def _lza_kms_condition() -> dict[str, dict[str, str | list[str]]]:
    """Deny on Accelerator-tagged keys unless by an LZA, CDK or management access role, or an AWS service."""
    config = lza_config()
    partition = Settings().cats_deployment_settings.partition
    prefix = config.accelerator_prefix
    return {
        "StringEquals": {"aws:ResourceTag/Accelerator": prefix},
        "ArnNotLike": {
            "aws:PrincipalARN": [
                f"arn:{partition}:iam::*:role/{prefix}*",
                f"arn:{partition}:iam::*:role/{config.global_.management_account_access_role}",
                f"arn:{partition}:iam::*:role/cdk-accel*",
            ]
        },
        "BoolIfExists": {"aws:PrincipalIsAWSService": "false"},
    }


def _control_tower_logs_bucket_objects(LogArchive_account: LogArchiveAccount) -> str:
    partition = Settings().cats_deployment_settings.partition
    return f"arn:{partition}:s3:::aws-controltower-logs-{LogArchive_account.account_id}-{lza_config().home_region}/*"


def _assert_control_statement(
    Management_account: ManagementAccount,
    LogArchive_account: LogArchiveAccount,
    sid: str,
    service: str,
    condition: dict[str, dict[str, str | list[str]]],
    resource: str = "*",
) -> None:
    """The deployed statement ``sid`` enforces the control and equals the configured statement.

    Control: the statement is a Deny on ``resource`` with exactly ``condition`` and at least
    one ``service`` action. The condition is spelled out by the control, with the live
    Organization, the partition and the LZA config supplying its values, so a weakened
    condition fails even when the configured policy carries the same change. The service
    check separates controls that share a statement (GRECDP covers five services).

    Fidelity: the whole statement equals the configured one after LZA's substitutions, so
    any other edit to the deployed policy also fails.
    """
    # arrange
    expected = _expected_statements(Management_account, LogArchive_account)
    assert sid in expected, f"Configured RCP '{_core_rcp_name()}' has no statement {sid}; declared: {sorted(expected)}"
    expected_condition = _canonical_condition(condition)

    # act
    deployed = _deployed_statements(Management_account)
    assert sid in deployed, f"Deployed RCP '{_core_rcp_name()}' has no statement {sid}; found: {sorted(deployed)}"

    # assert
    assert service in _denied_services(deployed[sid]), f"Deployed {sid} does not deny any {service} action: {deployed[sid]['Action']}"
    assert deployed[sid]["Resource"] == [resource], f"Deployed {sid} is not scoped to {resource}: {deployed[sid]['Resource']}"
    assert deployed[sid]["Condition"] == expected_condition, f"Deployed {sid} condition does not enforce the control"
    assert deployed[sid] == expected[sid], f"Deployed {sid} in '{_core_rcp_name()}' differs from the configured policy"


@cats(standard_name=["LZA-G-RCP-1"], test_suite="rcp", test_id="1", mutating=False, evidence=Evidence.CONFIGURATION)
def test_s3_organization_restriction(Management_account: ManagementAccount, LogArchive_account: LogArchiveAccount) -> None:
    """Verify RCP denies S3 write operations unless the principal is in the Organization or is an AWS service."""
    _assert_control_statement(
        Management_account,
        LogArchive_account,
        _S3_DATA_PERIMETER_SID,
        "s3",
        _organization_principal_condition(Management_account),
    )


@cats(standard_name=["LZA-G-RCP-2"], test_suite="rcp", test_id="2", mutating=False, evidence=Evidence.CONFIGURATION)
def test_s3_external_access_denial(Management_account: ManagementAccount, LogArchive_account: LogArchiveAccount) -> None:
    """Verify RCP denies S3 when an AWS service calls on behalf of a resource outside the Organization."""
    _assert_control_statement(Management_account, LogArchive_account, _EXTERNAL_SOURCE_SID, "s3", _external_source_condition(Management_account))


@cats(standard_name=["LZA-G-RCP-3"], test_suite="rcp", test_id="3", mutating=False, evidence=Evidence.CONFIGURATION)
def test_sqs_external_access_denial(Management_account: ManagementAccount, LogArchive_account: LogArchiveAccount) -> None:
    """Verify RCP denies SQS when an AWS service calls on behalf of a resource outside the Organization."""
    _assert_control_statement(Management_account, LogArchive_account, _EXTERNAL_SOURCE_SID, "sqs", _external_source_condition(Management_account))


@cats(standard_name=["LZA-G-RCP-4"], test_suite="rcp", test_id="4", mutating=False, evidence=Evidence.CONFIGURATION)
def test_kms_external_access_denial(Management_account: ManagementAccount, LogArchive_account: LogArchiveAccount) -> None:
    """Verify RCP denies KMS when an AWS service calls on behalf of a resource outside the Organization."""
    _assert_control_statement(Management_account, LogArchive_account, _EXTERNAL_SOURCE_SID, "kms", _external_source_condition(Management_account))


@cats(standard_name=["LZA-G-RCP-5"], test_suite="rcp", test_id="5", mutating=False, evidence=Evidence.CONFIGURATION)
def test_secrets_external_access_denial(Management_account: ManagementAccount, LogArchive_account: LogArchiveAccount) -> None:
    """Verify RCP denies Secrets Manager when an AWS service calls on behalf of a resource outside the Organization."""
    _assert_control_statement(
        Management_account,
        LogArchive_account,
        _EXTERNAL_SOURCE_SID,
        "secretsmanager",
        _external_source_condition(Management_account),
    )


@cats(standard_name=["LZA-G-RCP-6"], test_suite="rcp", test_id="6", mutating=False, evidence=Evidence.CONFIGURATION)
def test_sts_external_access_denial(Management_account: ManagementAccount, LogArchive_account: LogArchiveAccount) -> None:
    """Verify RCP denies STS when an AWS service calls on behalf of a resource outside the Organization."""
    _assert_control_statement(Management_account, LogArchive_account, _EXTERNAL_SOURCE_SID, "sts", _external_source_condition(Management_account))


@cats(standard_name=["LZA-G-RCP-7"], test_suite="rcp", test_id="7", mutating=False, evidence=Evidence.CONFIGURATION)
def test_s3_https_enforcement(Management_account: ManagementAccount, LogArchive_account: LogArchiveAccount) -> None:
    """Verify RCP denies S3 over unencrypted HTTP."""
    _assert_control_statement(Management_account, LogArchive_account, _SECURE_TRANSPORT_SID, "s3", _INSECURE_TRANSPORT_CONDITION)


@cats(standard_name=["LZA-G-RCP-8"], test_suite="rcp", test_id="8", mutating=False, evidence=Evidence.CONFIGURATION)
def test_sqs_https_enforcement(Management_account: ManagementAccount, LogArchive_account: LogArchiveAccount) -> None:
    """Verify RCP denies SQS over unencrypted HTTP."""
    _assert_control_statement(Management_account, LogArchive_account, _SECURE_TRANSPORT_SID, "sqs", _INSECURE_TRANSPORT_CONDITION)


@cats(standard_name=["LZA-G-RCP-9"], test_suite="rcp", test_id="9", mutating=False, evidence=Evidence.CONFIGURATION)
def test_kms_https_enforcement(Management_account: ManagementAccount, LogArchive_account: LogArchiveAccount) -> None:
    """Verify RCP denies KMS over unencrypted HTTP."""
    _assert_control_statement(Management_account, LogArchive_account, _SECURE_TRANSPORT_SID, "kms", _INSECURE_TRANSPORT_CONDITION)


@cats(standard_name=["LZA-G-RCP-10"], test_suite="rcp", test_id="10", mutating=False, evidence=Evidence.CONFIGURATION)
def test_secrets_https_enforcement(Management_account: ManagementAccount, LogArchive_account: LogArchiveAccount) -> None:
    """Verify RCP denies Secrets Manager over unencrypted HTTP."""
    _assert_control_statement(Management_account, LogArchive_account, _SECURE_TRANSPORT_SID, "secretsmanager", _INSECURE_TRANSPORT_CONDITION)


@cats(standard_name=["LZA-G-RCP-11"], test_suite="rcp", test_id="11", mutating=False, evidence=Evidence.CONFIGURATION)
def test_sts_https_enforcement(Management_account: ManagementAccount, LogArchive_account: LogArchiveAccount) -> None:
    """Verify RCP denies STS over unencrypted HTTP."""
    _assert_control_statement(Management_account, LogArchive_account, _SECURE_TRANSPORT_SID, "sts", _INSECURE_TRANSPORT_CONDITION)


@cats(standard_name=["LZA-G-RCP-12"], test_suite="rcp", test_id="12", mutating=False, evidence=Evidence.CONFIGURATION)
def test_control_tower_logs_protection(Management_account: ManagementAccount, LogArchive_account: LogArchiveAccount) -> None:
    """Verify RCP denies object access on the Control Tower logs bucket except via Config, CloudTrail, the management role or AWS services."""
    _assert_control_statement(
        Management_account,
        LogArchive_account,
        _CONTROL_TOWER_LOGS_SID,
        "s3",
        _control_tower_logs_condition(),
        resource=_control_tower_logs_bucket_objects(LogArchive_account),
    )


@cats(standard_name=["LZA-G-RCP-13"], test_suite="rcp", test_id="13a", mutating=False, evidence=Evidence.CONFIGURATION)
def test_lza_kms_modification_restriction(Management_account: ManagementAccount, LogArchive_account: LogArchiveAccount) -> None:
    """Verify RCP denies modification of Accelerator-tagged KMS keys except by LZA, CDK and management roles or AWS services."""
    _assert_control_statement(Management_account, LogArchive_account, _LZA_KMS_SID, "kms", _lza_kms_condition())


@cats(standard_name=["LZA-G-RCP-14"], test_suite="rcp", test_id="14", mutating=False, evidence=Evidence.CONFIGURATION)
def test_sts_identity_perimeter(Management_account: ManagementAccount, LogArchive_account: LogArchiveAccount) -> None:
    """Verify RCP denies role assumption unless the principal is in the Organization or is an AWS service."""
    _assert_control_statement(
        Management_account,
        LogArchive_account,
        _STS_DATA_PERIMETER_SID,
        "sts",
        _organization_principal_condition(Management_account),
    )


@cats(standard_name=["LZA-G-RCP-15"], test_suite="rcp", test_id="15", mutating=False, evidence=Evidence.CONFIGURATION)
def test_sqs_identity_perimeter(Management_account: ManagementAccount, LogArchive_account: LogArchiveAccount) -> None:
    """Verify RCP denies SQS operations unless the principal is in the Organization or is an AWS service."""
    _assert_control_statement(
        Management_account,
        LogArchive_account,
        _SQS_DATA_PERIMETER_SID,
        "sqs",
        _organization_principal_condition(Management_account),
    )


@cats(standard_name=["LZA-G-RCP-16"], test_suite="rcp", test_id="16", mutating=False, evidence=Evidence.CONFIGURATION)
def test_secrets_manager_identity_perimeter(Management_account: ManagementAccount, LogArchive_account: LogArchiveAccount) -> None:
    """Verify RCP denies Secrets Manager operations unless the principal is in the Organization or is an AWS service."""
    _assert_control_statement(
        Management_account,
        LogArchive_account,
        _SECRETS_MANAGER_DATA_PERIMETER_SID,
        "secretsmanager",
        _organization_principal_condition(Management_account),
    )

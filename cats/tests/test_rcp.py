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

Verifies the RCP policy document contains expected deny statements.
These tests inspect policy JSON rather than triggering denials, since RCP
enforcement requires external-org or HTTP-mode requests.

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
import logging
from typing import TYPE_CHECKING, Any

from cats import cats

from cats_utils.cats_cache import get_organization_rcps, get_rcp_policy_content
from cats_utils.evidence import Evidence
from lza_utils.lza_config import lza_config

if TYPE_CHECKING:
    from cats_types import ManagementAccount

logger = logging.getLogger(__name__)


def _get_rcp_statements(account: ManagementAccount) -> list[dict[str, Any]]:
    """Fetch and parse the Core RCP Guardrails policy statements."""
    config = lza_config()
    expected_name = f"{config.accelerator_prefix}-Core-Rcp-Guardrails"
    rcps = get_organization_rcps(account)
    assert expected_name in rcps, f"RCP '{expected_name}' not found in organization. Found: {sorted(rcps.keys())}"
    content = get_rcp_policy_content(account, rcps[expected_name]["Id"])
    policy: dict[str, list[dict[str, Any]]] = json.loads(content)
    return policy["Statement"]


def _find_deny_statements_for_service(statements: list[dict[str, Any]], service_prefix: str) -> list[dict[str, Any]]:
    """Find Deny statements that contain actions for a given service prefix."""
    result: list[dict[str, Any]] = []
    for stmt in statements:
        if stmt.get("Effect") != "Deny":
            continue
        actions = stmt.get("Action", [])
        if isinstance(actions, str):
            actions = [actions]
        if any(a.lower().startswith(service_prefix) for a in actions):
            result.append(stmt)
    return result


def _has_condition_key(statement: dict[str, Any], condition_key: str) -> bool:
    """Check if a statement's Condition block references a given key (case-insensitive)."""
    conditions_str = json.dumps(statement.get("Condition", {})).lower()
    return condition_key.lower() in conditions_str


def _denies_insecure_transport(statement: dict[str, Any]) -> bool:
    """Check that a Deny statement fires when aws:SecureTransport is false (non-HTTPS).

    Accepts both Bool and BoolIfExists operators.
    """
    condition = statement.get("Condition", {})
    for operator in ("Bool", "BoolIfExists"):
        value = condition.get(operator, {}).get("aws:SecureTransport")
        if value is not None and str(value).lower() == "false":
            return True
    return False


@cats(standard_name=["LZA-G-RCP-1"], test_suite="rcp", test_id="1", mutating=False, evidence=Evidence.CONFIGURATION)
def test_s3_organization_restriction(Management_account: ManagementAccount) -> None:
    """Verify RCP denies S3 operations unless from org members or AWS services."""
    statements = _get_rcp_statements(Management_account)
    s3_denies = _find_deny_statements_for_service(statements, "s3:")
    compliant = [s for s in s3_denies if _has_condition_key(s, "aws:PrincipalOrgID") and _has_condition_key(s, "aws:PrincipalIsAWSService")]
    assert compliant, "No S3 deny statement with PrincipalOrgID + PrincipalIsAWSService conditions"


@cats(standard_name=["LZA-G-RCP-2"], test_suite="rcp", test_id="2", mutating=False, evidence=Evidence.CONFIGURATION)
def test_s3_external_access_denial(Management_account: ManagementAccount) -> None:
    """Verify RCP denies S3 when request originates outside the Organization."""
    statements = _get_rcp_statements(Management_account)
    s3_denies = _find_deny_statements_for_service(statements, "s3:")
    compliant = [s for s in s3_denies if _has_condition_key(s, "aws:SourceOrgID")]
    assert compliant, "No S3 deny statement with aws:SourceOrgID condition"


@cats(standard_name=["LZA-G-RCP-3"], test_suite="rcp", test_id="3", mutating=False, evidence=Evidence.CONFIGURATION)
def test_sqs_external_access_denial(Management_account: ManagementAccount) -> None:
    """Verify RCP denies SQS when request originates outside the Organization."""
    statements = _get_rcp_statements(Management_account)
    sqs_denies = _find_deny_statements_for_service(statements, "sqs:")
    compliant = [s for s in sqs_denies if _has_condition_key(s, "aws:SourceOrgID")]
    assert compliant, "No SQS deny statement with aws:SourceOrgID condition"


@cats(standard_name=["LZA-G-RCP-4"], test_suite="rcp", test_id="4", mutating=False, evidence=Evidence.CONFIGURATION)
def test_kms_external_access_denial(Management_account: ManagementAccount) -> None:
    """Verify RCP denies KMS when request originates outside the Organization."""
    statements = _get_rcp_statements(Management_account)
    kms_denies = _find_deny_statements_for_service(statements, "kms:")
    compliant = [s for s in kms_denies if _has_condition_key(s, "aws:SourceOrgID")]
    assert compliant, "No KMS deny statement with aws:SourceOrgID condition"


@cats(standard_name=["LZA-G-RCP-5"], test_suite="rcp", test_id="5", mutating=False, evidence=Evidence.CONFIGURATION)
def test_secrets_external_access_denial(Management_account: ManagementAccount) -> None:
    """Verify RCP denies Secrets Manager when request originates outside the Organization."""
    statements = _get_rcp_statements(Management_account)
    sm_denies = _find_deny_statements_for_service(statements, "secretsmanager:")
    compliant = [s for s in sm_denies if _has_condition_key(s, "aws:SourceOrgID")]
    assert compliant, "No Secrets Manager deny statement with aws:SourceOrgID condition"


@cats(standard_name=["LZA-G-RCP-6"], test_suite="rcp", test_id="6", mutating=False, evidence=Evidence.CONFIGURATION)
def test_sts_external_access_denial(Management_account: ManagementAccount) -> None:
    """Verify RCP denies STS when request originates outside the Organization."""
    statements = _get_rcp_statements(Management_account)
    sts_denies = _find_deny_statements_for_service(statements, "sts:")
    compliant = [s for s in sts_denies if _has_condition_key(s, "aws:SourceOrgID")]
    assert compliant, "No STS deny statement with aws:SourceOrgID condition"


@cats(standard_name=["LZA-G-RCP-7"], test_suite="rcp", test_id="7", mutating=False, evidence=Evidence.CONFIGURATION)
def test_s3_https_enforcement(Management_account: ManagementAccount) -> None:
    """Verify RCP denies S3 over unencrypted HTTP."""
    statements = _get_rcp_statements(Management_account)
    s3_denies = _find_deny_statements_for_service(statements, "s3:")
    compliant = [s for s in s3_denies if _denies_insecure_transport(s)]
    assert compliant, "No S3 deny statement with aws:SecureTransport == false"


@cats(standard_name=["LZA-G-RCP-8"], test_suite="rcp", test_id="8", mutating=False, evidence=Evidence.CONFIGURATION)
def test_sqs_https_enforcement(Management_account: ManagementAccount) -> None:
    """Verify RCP denies SQS over unencrypted HTTP."""
    statements = _get_rcp_statements(Management_account)
    sqs_denies = _find_deny_statements_for_service(statements, "sqs:")
    compliant = [s for s in sqs_denies if _denies_insecure_transport(s)]
    assert compliant, "No SQS deny statement with aws:SecureTransport == false"


@cats(standard_name=["LZA-G-RCP-9"], test_suite="rcp", test_id="9", mutating=False, evidence=Evidence.CONFIGURATION)
def test_kms_https_enforcement(Management_account: ManagementAccount) -> None:
    """Verify RCP denies KMS over unencrypted HTTP."""
    statements = _get_rcp_statements(Management_account)
    kms_denies = _find_deny_statements_for_service(statements, "kms:")
    compliant = [s for s in kms_denies if _denies_insecure_transport(s)]
    assert compliant, "No KMS deny statement with aws:SecureTransport == false"


@cats(standard_name=["LZA-G-RCP-10"], test_suite="rcp", test_id="10", mutating=False, evidence=Evidence.CONFIGURATION)
def test_secrets_https_enforcement(Management_account: ManagementAccount) -> None:
    """Verify RCP denies Secrets Manager over unencrypted HTTP."""
    statements = _get_rcp_statements(Management_account)
    sm_denies = _find_deny_statements_for_service(statements, "secretsmanager:")
    compliant = [s for s in sm_denies if _denies_insecure_transport(s)]
    assert compliant, "No Secrets Manager deny statement with aws:SecureTransport == false"


@cats(standard_name=["LZA-G-RCP-11"], test_suite="rcp", test_id="11", mutating=False, evidence=Evidence.CONFIGURATION)
def test_sts_https_enforcement(Management_account: ManagementAccount) -> None:
    """Verify RCP denies STS over unencrypted HTTP."""
    statements = _get_rcp_statements(Management_account)
    sts_denies = _find_deny_statements_for_service(statements, "sts:")
    compliant = [s for s in sts_denies if _denies_insecure_transport(s)]
    assert compliant, "No STS deny statement with aws:SecureTransport == false"


@cats(standard_name=["LZA-G-RCP-12"], test_suite="rcp", test_id="12", mutating=False, evidence=Evidence.CONFIGURATION)
def test_control_tower_logs_protection(Management_account: ManagementAccount) -> None:
    """Verify RCP protects Control Tower logs S3 bucket from unauthorized access."""
    statements = _get_rcp_statements(Management_account)
    s3_denies = _find_deny_statements_for_service(statements, "s3:")
    resources_json = [json.dumps(s.get("Resource", [])).lower() for s in s3_denies]
    compliant = [r for r in resources_json if "controltower" in r or "control-tower" in r]
    assert compliant, "No S3 deny statement protecting Control Tower log resources"


@cats(standard_name=["LZA-G-RCP-13"], test_suite="rcp", test_id="13a", mutating=False, evidence=Evidence.CONFIGURATION)
def test_lza_kms_modification_restriction(Management_account: ManagementAccount) -> None:
    """Verify RCP restricts modification of LZA-managed KMS keys."""
    statements = _get_rcp_statements(Management_account)
    kms_denies = _find_deny_statements_for_service(statements, "kms:")
    accelerator_prefix = lza_config().accelerator_prefix.lower()
    compliant = [s for s in kms_denies if accelerator_prefix in json.dumps(s).lower() or "accelerator" in json.dumps(s).lower()]
    assert compliant, "No KMS deny statement restricting LZA/Accelerator key modifications"


@cats(standard_name=["LZA-G-RCP-14"], test_suite="rcp", test_id="14", mutating=False, evidence=Evidence.CONFIGURATION)
def test_sts_identity_perimeter(Management_account: ManagementAccount) -> None:
    """Verify RCP denies cross-account role assumption from principals outside the Organization."""
    statements = _get_rcp_statements(Management_account)
    sts_denies = _find_deny_statements_for_service(statements, "sts:")
    compliant = [s for s in sts_denies if _has_condition_key(s, "aws:PrincipalOrgID") and _has_condition_key(s, "aws:PrincipalIsAWSService")]
    assert compliant, "No STS deny statement with PrincipalOrgID + PrincipalIsAWSService conditions"


@cats(standard_name=["LZA-G-RCP-15"], test_suite="rcp", test_id="15", mutating=False, evidence=Evidence.CONFIGURATION)
def test_sqs_identity_perimeter(Management_account: ManagementAccount) -> None:
    """Verify RCP denies SQS operations from principals outside the Organization."""
    statements = _get_rcp_statements(Management_account)
    sqs_denies = _find_deny_statements_for_service(statements, "sqs:")
    compliant = [s for s in sqs_denies if _has_condition_key(s, "aws:PrincipalOrgID") and _has_condition_key(s, "aws:PrincipalIsAWSService")]
    assert compliant, "No SQS deny statement with PrincipalOrgID + PrincipalIsAWSService conditions"


@cats(standard_name=["LZA-G-RCP-16"], test_suite="rcp", test_id="16", mutating=False, evidence=Evidence.CONFIGURATION)
def test_secrets_manager_identity_perimeter(Management_account: ManagementAccount) -> None:
    """Verify RCP denies Secrets Manager operations from principals outside the Organization."""
    statements = _get_rcp_statements(Management_account)
    sm_denies = _find_deny_statements_for_service(statements, "secretsmanager:")
    compliant = [s for s in sm_denies if _has_condition_key(s, "aws:PrincipalOrgID") and _has_condition_key(s, "aws:PrincipalIsAWSService")]
    assert compliant, "No Secrets Manager deny statement with PrincipalOrgID + PrincipalIsAWSService conditions"

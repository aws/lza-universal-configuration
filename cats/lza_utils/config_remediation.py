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

"""Expected AWS Config remediation configuration for an LZA Config rule.

Mirrors ``setupConfigRuleRemediation`` and ``getRemediationParameters`` in LZA's
``security-resources-stack.ts`` so that a value built from ``security-config.yaml``
compares equal to the ``describe_remediation_configurations`` output for the
deployed rule, except for ``AutomationAssumeRole``: LZA lets CDK name the
remediation role, so that parameter is verified separately by the test.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from cats.config import Settings

from lza_utils.lza_config import lza_config

if TYPE_CHECKING:
    from lza_types.security_config import ConfigRule, RemediationParametersConfigType

# A document name AWS reserves; LZA passes such a targetId through as a bare name
# rather than building an ARN in the Audit account (IsPublicSsmDoc in LZA).
_PUBLIC_SSM_DOCUMENT_PREFIXES = re.compile(r"^(AWS-|AMZN-|AMAZON-|AWSEC2-|AWSConfigRemediation-|AWSSupport-)", re.IGNORECASE)
_ACCEL_LOOKUP = re.compile(r"\$\{ACCEL_LOOKUP::([a-zA-Z0-9-/:]*)}")

# The remediation parameter LZA adds itself, holding the CDK-named remediation role ARN.
AUTOMATION_ASSUME_ROLE_PARAMETER = "AutomationAssumeRole"


def remediation_target_id(target_id: str, region: str, audit_account_id: str) -> str:
    """The TargetId LZA deploys: a bare name for an AWS-owned document, else a document ARN in the Audit account."""
    if _PUBLIC_SSM_DOCUMENT_PREFIXES.match(target_id):
        return target_id
    partition = Settings().cats_deployment_settings.partition
    return f"arn:{partition}:ssm:{region}:{audit_account_id}:document/{target_id}"


def _resolve_lookup(lookup: str, region: str, log_archive_account_id: str) -> str:
    """Resolve one ``${ACCEL_LOOKUP::Type:Value}`` reference the way LZA does for remediation parameters."""
    lookup_type, _, lookup_value = lookup.partition(":")
    if lookup_type == "InstanceProfile":
        # LZA names an instance profile after its role, so the lookup value is the deployed value.
        return lookup_value
    if lookup_type == "Bucket" and lookup_value.lower() == "elblogs":
        return lza_config().elb_access_logs_bucket_name(log_archive_account_id, region)
    msg = f"ACCEL_LOOKUP type '{lookup_type}' is not supported for remediation parameters in this test pack: ${{ACCEL_LOOKUP::{lookup}}}"
    raise NotImplementedError(msg)


def remediation_parameter_value(parameter: RemediationParametersConfigType, region: str, log_archive_account_id: str) -> dict[str, Any]:
    """The deployed value of one configured remediation parameter."""
    lookups = [match.group(1) for item in parameter.value.split(",") if (match := _ACCEL_LOOKUP.search(item))]
    if lookups:
        # LZA keeps only the resolved lookups from a comma-separated value, and joins them for a String parameter.
        resolved = [_resolve_lookup(lookup, region, log_archive_account_id) for lookup in lookups]
        values = resolved if parameter.type == "StringList" else [",".join(resolved)]
        return {"StaticValue": {"Values": values}}
    if parameter.value == "RESOURCE_ID":
        return {"ResourceValue": {"Value": "RESOURCE_ID"}}
    return {"StaticValue": {"Values": parameter.value.split(",")}}


def expected_remediation_configuration(rule: ConfigRule, region: str, audit_account_id: str, log_archive_account_id: str) -> dict[str, Any]:
    """The remediation configuration LZA deploys for ``rule``, without ``AutomationAssumeRole``.

    Mirrors ``CfnRemediationConfiguration`` in LZA's security-resources-stack.ts. Optional
    fields are present only when configured, matching what the API returns.
    """
    remediation = rule.remediation
    assert remediation is not None, f"Config rule '{rule.name}' has no remediation block in security-config.yaml"

    expected: dict[str, Any] = {
        "ConfigRuleName": rule.name,
        "TargetType": "SSM_DOCUMENT",
        "TargetId": remediation_target_id(remediation.target_id, region, audit_account_id),
        "Automatic": remediation.automatic,
    }
    if remediation.target_version is not None:
        expected["TargetVersion"] = remediation.target_version
    if remediation.maximum_automatic_attempts is not None:
        expected["MaximumAutomaticAttempts"] = int(remediation.maximum_automatic_attempts)
    if remediation.retry_attempt_seconds is not None:
        expected["RetryAttemptSeconds"] = int(remediation.retry_attempt_seconds)
    if remediation.parameters is not None:
        expected["Parameters"] = {
            parameter.name: remediation_parameter_value(parameter, region, log_archive_account_id) for parameter in remediation.parameters
        }
    return expected

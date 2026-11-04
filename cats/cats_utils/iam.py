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
IAM policy document helpers.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any
from urllib.parse import unquote

if TYPE_CHECKING:
    from collections.abc import Mapping

    from mypy_boto3_iam.type_defs import PolicyDocumentTypeDef


def _as_list(value: str | list[str]) -> list[str]:
    return [value] if isinstance(value, str) else value


def trusted_service_principals(assume_role_policy_document: PolicyDocumentTypeDef | Mapping[str, Any]) -> set[str]:
    """Service principals an IAM role's trust policy allows to assume it.

    ``list_roles`` returns the document URL-decoded as a dict; ``get_role`` and the raw API return
    a URL-encoded JSON string. Both shapes are accepted.
    """
    document: Mapping[str, Any] = (
        json.loads(unquote(assume_role_policy_document)) if isinstance(assume_role_policy_document, str) else assume_role_policy_document
    )
    statements: list[dict[str, Any]] = document["Statement"] if isinstance(document["Statement"], list) else [document["Statement"]]
    return {
        principal
        for statement in statements
        if statement["Effect"] == "Allow" and isinstance(statement.get("Principal"), dict)
        for principal in _as_list(statement["Principal"].get("Service", []))
    }


# Statement elements IAM accepts as either one string or a list of strings.
_LIST_OR_STRING_ELEMENTS = ("Action", "NotAction", "Resource", "NotResource")


def canonical_statement(statement: Mapping[str, Any]) -> dict[str, Any]:
    """A statement with every element IAM accepts as string-or-list written as a list.

    ``Action``, ``NotAction``, ``Resource``, ``NotResource``, each ``Principal`` /
    ``NotPrincipal`` entry and each condition value may be written as one string or a
    one-element list; IAM treats them as the same policy. Organizations stores RCP content
    with one-element lists collapsed to strings (SCP content keeps them), so a deployed
    RCP statement only compares equal to its configured source after both pass through
    here. Anything else is returned untouched.
    """
    canonical = dict(statement)
    for element in _LIST_OR_STRING_ELEMENTS:
        if element in canonical:
            canonical[element] = _as_list(canonical[element])
    for element in ("Principal", "NotPrincipal"):
        if isinstance(canonical.get(element), dict):
            canonical[element] = {kind: _as_list(value) for kind, value in canonical[element].items()}
    if "Condition" in canonical:
        canonical["Condition"] = {
            operator: {key: _as_list(value) for key, value in pairs.items()} for operator, pairs in canonical["Condition"].items()
        }
    return canonical

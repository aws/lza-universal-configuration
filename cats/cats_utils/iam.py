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

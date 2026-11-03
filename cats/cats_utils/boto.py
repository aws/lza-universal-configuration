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
Boto3 and AWS API utilities.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from botocore.config import Config

if TYPE_CHECKING:
    from botocore.exceptions import ClientError


def get_retry_config(max_attempts: int = 10, mode: Literal["legacy", "standard", "adaptive"] = "adaptive") -> Config:
    """Get a boto3 Config object with retry settings."""
    return Config(retries={"total_max_attempts": max_attempts, "mode": mode}, connect_timeout=5, read_timeout=10, max_pool_connections=50)


DEFAULT_RETRY_CONFIG = get_retry_config()


def get_error_code(e: ClientError) -> str:
    """Extract error code from ClientError."""
    return e.response["Error"]["Code"]


# For SCP probes against services that return a bare AccessDenied/AccessDeniedException
# instead of the "explicit deny in a service control policy" message. The test role is
# least-privilege, so a missing grant would also surface as AccessDenied. IAM's message for
# that case names an identity-based policy, which this pattern refuses, so an
# under-permissioned role fails the test rather than passing it. Pass it as the `match`
# argument of pytest.raises for ClientError.
ACCESS_DENIED_NOT_BY_IDENTITY_POLICY = r"(?s)\AAn error occurred \(AccessDenied(?:Exception)?\)(?!.*identity-based policy)"

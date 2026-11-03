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

# Pydantic models of the Landing Zone Accelerator on AWS configuration schema
# (https://github.com/awslabs/landing-zone-accelerator-on-aws, Apache-2.0). The field descriptions
# are LZA's own documentation. Generated, and replaced as a unit when the pack moves to a new LZA
# release; edits made here by hand are lost at that point.
from __future__ import annotations

from .accounts_config import AccountsConfig
from .global_config import GlobalConfig
from .iam_config import IamConfig
from .network_config import NetworkConfig
from .organization_config import OrganizationConfig
from .replacements_config import ReplacementsConfig
from .security_config import SecurityConfig

__all__ = [
    "AccountsConfig",
    "GlobalConfig",
    "IamConfig",
    "NetworkConfig",
    "OrganizationConfig",
    "ReplacementsConfig",
    "SecurityConfig",
]

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
CATS - IAM Access Analyzer Validation

This test verifies:
- LZA-SEC-IAA-1: IAM Access Analyzer with Organization as zone of trust
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from cats import cats

from cats_utils.boto import DEFAULT_RETRY_CONFIG
from cats_utils.evidence import Evidence
from lza_utils.lza_config import lza_config

if TYPE_CHECKING:
    from cats_types import AuditAccount

logger = logging.getLogger(__name__)


@cats(standard_name=["LZA-SEC-IAA-1"], test_suite="iam", test_id="iaa-1", evidence=Evidence.CONFIGURATION)
def test_access_analyzer_organization_zone(Audit_account: AuditAccount) -> None:
    """Verify an IAM Access Analyzer exists with Organization as zone of trust."""
    # act
    client = Audit_account.session.client("accessanalyzer", region_name=lza_config().home_region, config=DEFAULT_RETRY_CONFIG)
    analyzers = [analyzer for page in client.get_paginator("list_analyzers").paginate() for analyzer in page["analyzers"]]
    org_analyzers = [a for a in analyzers if a["type"] == "ORGANIZATION" and a["status"] == "ACTIVE"]

    # assert
    assert org_analyzers, f"No active ORGANIZATION-type Access Analyzer found. Analyzers: {[a['name'] for a in analyzers]}"

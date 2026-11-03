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

"""Unit tests for lza_utils.log_groups.is_lza_bootstrap_log_group.

These verify the classification predicate that determines which log groups
are treated as strict (must pass) vs known-gap (xfail) in the CloudWatch
Logs tests. No AWS credentials required.
"""

from __future__ import annotations

import pytest

from lza_utils.log_groups import is_lza_bootstrap_log_group


@pytest.mark.parametrize(
    ("log_group_name", "expected"),
    [
        # Bootstrap stacks - should be classified as bootstrap
        ("/aws/lambda/AWSAccelerator-InstallerStack-SomeFunc-abc123", True),
        ("/aws/lambda/AWSAccelerator-InstallerC-ResourceNamePrefixesReso-XIKlCUY0TiOm", True),
        ("/aws/lambda/AWSAccelerator-PipelineSta-SomeFunc-abc123", True),
        ("/aws/lambda/AWSAccelerator-DiagnosticsP-Lambda-xyz", True),
        ("/aws/lambda/AWSAccelerator-PrepareSta-CustomResource-def456", True),
        ("/aws/lambda/AWSAccelerator-AccountsSta-Lambda-ghi789", True),
        ("/aws/lambda/AWSAccelerator-Organization-Lambda-jkl012", True),
        ("/aws/lambda/AWSAccelerator-LoggingSta-CustomResource-mno345", True),
        # CodeBuild log groups - always bootstrap
        ("/aws/codebuild/AWSAccelerator-InstallerProject", True),
        ("/aws/codebuild/AWSAccelerator-BuildProject", True),
        # FirehoseRecordsProcessor - bootstrap (excluded from subscription checks separately)
        ("/aws/lambda/AWSAccelerator-FirehoseRecordsProcessor", True),
        # LoggingStack's Firehose delivery stream log group in LogArchive - bootstrap (#875 race)
        ("/accelerator/logs/firehose/AWSAccelerator-LoggingStack-111111111111-us-east-1-LogsKinesisStreamCfn-9AXonp5xDWQo", True),
        # A Firehose log group from another stack is not LZA's bootstrap machinery
        ("/accelerator/logs/firehose/AWSAccelerator-CustomizationsStack-SomeStream-abc123", False),
        # Post-Logging stacks - should NOT be classified as bootstrap
        ("/aws/lambda/AWSAccelerator-SecuritySta-CustomResource-abc123", False),
        ("/aws/lambda/AWSAccelerator-NetworkSta-Lambda-def456", False),
        ("/aws/lambda/AWSAccelerator-OperationsSt-Lambda-ghi789", False),
        ("/aws/lambda/AWSAccelerator-FinalizeSta-Lambda-jkl012", False),
        ("/aws/lambda/AWSAccelerator-CustomizationsS-Lambda-mno345", False),
        # Non-lambda LZA log groups - not bootstrap
        ("/aws-accelerator-somegroup/something", False),
        # Non-LZA log groups - not bootstrap
        ("/aws/lambda/my-custom-lambda", False),
        ("/aws/rds/cluster/my-cluster", False),
        # Edge case: stack name fragment that is a prefix of a non-bootstrap stack
        # "Security" starts with "Se" which does NOT match any bootstrap stack prefix
        ("/aws/lambda/AWSAccelerator-Se-Lambda-abc", False),
        # Edge case: exact stack name match (not truncated)
        ("/aws/lambda/AWSAccelerator-InstallerStack-abc", True),
        # Edge case: fragment matches beginning of bootstrap stack but is a different stack
        # "Pipe" matches "PipelineStack" prefix
        ("/aws/lambda/AWSAccelerator-Pipe-Lambda-abc", True),
    ],
    ids=[
        "InstallerStack-lambda",
        "InstallerContainerStack-lambda-truncated",
        "PipelineStack-lambda-truncated",
        "DiagnosticsPackStack-lambda-truncated",
        "PrepareStack-lambda-truncated",
        "AccountsStack-lambda-truncated",
        "OrganizationsStack-lambda-truncated",
        "LoggingStack-lambda-truncated",
        "codebuild-installer",
        "codebuild-build",
        "firehose-processor",
        "firehose-logging-stack-log-group",
        "firehose-other-stack-not-bootstrap",
        "SecurityStack-not-bootstrap",
        "NetworkStack-not-bootstrap",
        "OperationsStack-not-bootstrap",
        "FinalizeStack-not-bootstrap",
        "CustomizationsStack-not-bootstrap",
        "non-lambda-lza-group",
        "non-lza-lambda",
        "non-lza-rds",
        "short-fragment-no-match",
        "full-stack-name-match",
        "prefix-match-pipeline",
    ],
)
def test_is_lza_bootstrap_log_group(log_group_name: str, expected: bool) -> None:
    """Verify classification of log group names as bootstrap vs managed."""
    assert is_lza_bootstrap_log_group(log_group_name) is expected

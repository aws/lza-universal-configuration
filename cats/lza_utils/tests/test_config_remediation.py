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

"""Tests for the expected remediation configuration derived from security-config.yaml."""

from __future__ import annotations

import pytest

from lza_types.security_config import RemediationParametersConfigType, Type
from lza_utils.config_remediation import (
    expected_remediation_configuration,
    remediation_parameter_value,
    remediation_target_id,
)
from lza_utils.lza_config import lza_config

AUDIT_ACCOUNT_ID = "111111111111"
LOG_ARCHIVE_ACCOUNT_ID = "222222222222"
REGION = "eu-west-2"


def test_expected_remediation_configuration_ec2_instance_profile_attached() -> None:
    # arrange
    rule = lza_config().config_rule("AWSAccelerator-ec2-instance-profile-attached")
    expected = {
        "ConfigRuleName": "AWSAccelerator-ec2-instance-profile-attached",
        "TargetType": "SSM_DOCUMENT",
        "TargetId": f"arn:aws:ssm:{REGION}:{AUDIT_ACCOUNT_ID}:document/AWSAccelerator-Attach-IAM-Instance-Profile",
        "Automatic": True,
        "MaximumAutomaticAttempts": 5,
        "RetryAttemptSeconds": 60,
        "Parameters": {
            "InstanceId": {"ResourceValue": {"Value": "RESOURCE_ID"}},
            "IamInstanceProfile": {"StaticValue": {"Values": ["EC2-Default-SSM-Role"]}},
        },
    }

    # act
    result = expected_remediation_configuration(rule, REGION, AUDIT_ACCOUNT_ID, LOG_ARCHIVE_ACCOUNT_ID)

    # assert
    assert result == expected


def test_expected_remediation_configuration_elb_logging_enabled() -> None:
    # arrange
    rule = lza_config().config_rule("AWSAccelerator-elb-logging-enabled")
    expected = {
        "ConfigRuleName": "AWSAccelerator-elb-logging-enabled",
        "TargetType": "SSM_DOCUMENT",
        "TargetId": f"arn:aws:ssm:{REGION}:{AUDIT_ACCOUNT_ID}:document/AWSAccelerator-SSM-ELB-Enable-Logging",
        "Automatic": True,
        "MaximumAutomaticAttempts": 5,
        "RetryAttemptSeconds": 60,
        "Parameters": {
            "LoadBalancerArn": {"ResourceValue": {"Value": "RESOURCE_ID"}},
            "LogDestination": {"StaticValue": {"Values": [f"aws-accelerator-elb-access-logs-{LOG_ARCHIVE_ACCOUNT_ID}-{REGION}"]}},
        },
    }

    # act
    result = expected_remediation_configuration(rule, REGION, AUDIT_ACCOUNT_ID, LOG_ARCHIVE_ACCOUNT_ID)

    # assert
    assert result == expected


def test_remediated_config_rule_names_in_universal_configuration() -> None:
    # act
    result = lza_config().remediated_config_rule_names

    # assert
    assert result == ["AWSAccelerator-ec2-instance-profile-attached", "AWSAccelerator-elb-logging-enabled"]


def test_remediation_target_id_aws_owned_document_is_bare_name() -> None:
    # act
    result = remediation_target_id("AWSConfigRemediation-EnableCloudTrailLogFileValidation", REGION, AUDIT_ACCOUNT_ID)

    # assert
    assert result == "AWSConfigRemediation-EnableCloudTrailLogFileValidation"


def test_remediation_parameter_value_string_lookup_joins_values() -> None:
    # arrange
    parameter = RemediationParametersConfigType(name="Buckets", type=Type.string, value="${ACCEL_LOOKUP::Bucket:elbLogs}")
    expected = {"StaticValue": {"Values": [f"aws-accelerator-elb-access-logs-{LOG_ARCHIVE_ACCOUNT_ID}-{REGION}"]}}

    # act
    result = remediation_parameter_value(parameter, REGION, LOG_ARCHIVE_ACCOUNT_ID)

    # assert
    assert result == expected


def test_remediation_parameter_value_literal_splits_on_comma() -> None:
    # arrange
    parameter = RemediationParametersConfigType(name="Ports", type=Type.string_list, value="443,8443")
    expected = {"StaticValue": {"Values": ["443", "8443"]}}

    # act
    result = remediation_parameter_value(parameter, REGION, LOG_ARCHIVE_ACCOUNT_ID)

    # assert
    assert result == expected


def test_remediation_parameter_value_unsupported_lookup_raises() -> None:
    # arrange
    parameter = RemediationParametersConfigType(name="Key", type=Type.string, value="${ACCEL_LOOKUP::KMS:alias/foo}")

    # act / assert
    with pytest.raises(NotImplementedError, match="ACCEL_LOOKUP type 'KMS' is not supported"):
        remediation_parameter_value(parameter, REGION, LOG_ARCHIVE_ACCOUNT_ID)

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

"""Tests for cats_utils.securityhub over every StandardsStatus the service model defines."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from cats_utils.securityhub import describe_subscription_state, is_standard_enabled

if TYPE_CHECKING:
    from mypy_boto3_securityhub.literals import StandardsControlsUpdatableType, StandardsStatusType, StatusReasonCodeType
    from mypy_boto3_securityhub.type_defs import StandardsSubscriptionTypeDef

_STANDARD_ARN = "arn:aws:securityhub:us-east-1::standards/aws-foundational-security-best-practices/v/1.0.0"
_SUBSCRIPTION_ARN = "arn:aws:securityhub:us-east-1:111111111111:subscription/aws-foundational-security-best-practices/v/1.0.0"


def _subscription(
    status: StandardsStatusType,
    *,
    controls_updatable: StandardsControlsUpdatableType | None = "READY_FOR_UPDATES",
    reason: StatusReasonCodeType | None = None,
) -> StandardsSubscriptionTypeDef:
    """A GetEnabledStandards subscription with the optional fields present only when given."""
    subscription: StandardsSubscriptionTypeDef = {
        "StandardsSubscriptionArn": _SUBSCRIPTION_ARN,
        "StandardsArn": _STANDARD_ARN,
        "StandardsInput": {},
        "StandardsStatus": status,
    }
    if controls_updatable is not None:
        subscription["StandardsControlsUpdatable"] = controls_updatable
    if reason is not None:
        subscription["StandardsStatusReason"] = {"StatusReasonCode": reason}
    return subscription


def test_ready_is_enabled() -> None:
    assert is_standard_enabled(_subscription("READY")) is True


def test_pending_control_rollout_on_an_enabled_standard_is_enabled() -> None:
    """AWS adding controls to an already-enabled standard: no reason, controls still configurable."""
    assert is_standard_enabled(_subscription("PENDING", controls_updatable="READY_FOR_UPDATES")) is True


@pytest.mark.parametrize(
    ("subscription", "expected_state"),
    [
        pytest.param(
            _subscription("PENDING", controls_updatable="NOT_READY_FOR_UPDATES"),
            "PENDING (reason=<no StandardsStatusReason>, controls=NOT_READY_FOR_UPDATES)",
            id="pending-first-enablement",
        ),
        pytest.param(
            _subscription("PENDING", controls_updatable=None),
            "PENDING (reason=<no StandardsStatusReason>, controls=<no StandardsControlsUpdatable>)",
            id="pending-updatable-not-returned",
        ),
        pytest.param(
            _subscription("PENDING", reason="INTERNAL_ERROR"), "PENDING (reason=INTERNAL_ERROR, controls=READY_FOR_UPDATES)", id="pending-with-reason"
        ),
        pytest.param(
            _subscription("INCOMPLETE", reason="NO_AVAILABLE_CONFIGURATION_RECORDER"),
            "INCOMPLETE (reason=NO_AVAILABLE_CONFIGURATION_RECORDER, controls=READY_FOR_UPDATES)",
            id="incomplete",
        ),
        pytest.param(
            _subscription("INCOMPLETE", reason="MAXIMUM_NUMBER_OF_CONFIG_RULES_EXCEEDED"),
            "INCOMPLETE (reason=MAXIMUM_NUMBER_OF_CONFIG_RULES_EXCEEDED, controls=READY_FOR_UPDATES)",
            id="incomplete-rule-limit",
        ),
        pytest.param(_subscription("FAILED", reason="INTERNAL_ERROR"), "FAILED (reason=INTERNAL_ERROR, controls=READY_FOR_UPDATES)", id="failed"),
        pytest.param(_subscription("DELETING"), "DELETING (reason=<no StandardsStatusReason>, controls=READY_FOR_UPDATES)", id="deleting"),
    ],
)
def test_every_other_state_is_not_enabled_and_is_described(subscription: StandardsSubscriptionTypeDef, expected_state: str) -> None:
    assert is_standard_enabled(subscription) is False
    assert describe_subscription_state(subscription) == expected_state


def test_describe_ready_state() -> None:
    assert describe_subscription_state(_subscription("READY")) == "READY (reason=<no StandardsStatusReason>, controls=READY_FOR_UPDATES)"

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

"""Reading a Security Hub standards subscription as evidence that the standard is enabled.

``GetEnabledStandards`` reports ``StandardsStatus`` as one of five values (botocore
``securityhub/2018-10-26``):

- ``READY``: the standard is enabled.
- ``PENDING``: "the standard is in the process of being enabled. Or the standard is already
  enabled and Security Hub CSPM is adding new controls to the standard." AWS ships new
  FSBP and NIST controls several times a month, region by region, and every subscription in
  the region reads ``PENDING`` for the rollout with nobody in the organization acting.
- ``INCOMPLETE`` / ``FAILED``: enabling / disabling could not complete; ``StandardsStatusReason``
  carries ``NO_AVAILABLE_CONFIGURATION_RECORDER``, ``MAXIMUM_NUMBER_OF_CONFIG_RULES_EXCEEDED``
  or ``INTERNAL_ERROR``.
- ``DELETING``: the standard is being disabled.

Only the second ``PENDING`` case is evidence of an enabled standard, and the subscription
tells the two apart: ``StandardsControlsUpdatable`` is ``READY_FOR_UPDATES`` when "controls
in the standard can be retrieved and configured", which a standard still being enabled for
the first time cannot offer. An error state always carries a reason, so a ``PENDING`` with
one is not the rollout case either.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mypy_boto3_securityhub.type_defs import StandardsSubscriptionTypeDef

NO_STATUS_REASON = "<no StandardsStatusReason>"
NO_CONTROLS_UPDATABLE = "<no StandardsControlsUpdatable>"


def is_standard_enabled(subscription: StandardsSubscriptionTypeDef) -> bool:
    """Whether the subscription proves its standard enabled: ``READY``, or ``PENDING`` for a control rollout.

    The rollout case is ``PENDING`` with no ``StandardsStatusReason`` and controls
    ``READY_FOR_UPDATES``; see the module docstring. Every other status, and ``PENDING`` with a
    reason or with controls not updatable, is not evidence of an enabled standard.
    """
    status = subscription["StandardsStatus"]
    if status == "READY":
        return True
    if status != "PENDING":
        return False
    return "StandardsStatusReason" not in subscription and subscription.get("StandardsControlsUpdatable") == "READY_FOR_UPDATES"


def describe_subscription_state(subscription: StandardsSubscriptionTypeDef) -> str:
    """``<status> (reason=<code>, controls=<updatable>)`` so a failure names every field the verdict used."""
    status = subscription["StandardsStatus"]
    reason = subscription.get("StandardsStatusReason", {}).get("StatusReasonCode", NO_STATUS_REASON)
    controls_updatable = subscription.get("StandardsControlsUpdatable", NO_CONTROLS_UPDATABLE)
    return f"{status} (reason={reason}, controls={controls_updatable})"

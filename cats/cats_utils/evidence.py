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

"""Evidence type for the @cats(evidence=...) marker.

Every test declares the kind of evidence it produces. The value flows into
report.json and OSCAL props (name="evidence") via reporting.custom_markers.
"""

from __future__ import annotations

from enum import StrEnum


class Evidence(StrEnum):
    """The kind of evidence a test produces for its control.

    BEHAVIORAL: the test performs the controlled action and observes
        enforcement (SCP denial probes, live network traffic). Supports
        operating-effectiveness claims.
    CONFIGURATION: the test reads deployed state (describe/list APIs,
        policy documents) and asserts it matches declared intent. Supports
        design claims.
    """

    BEHAVIORAL = "behavioral"
    CONFIGURATION = "configuration"

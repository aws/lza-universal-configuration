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

"""Unit tests read the rendered Universal Configuration fixture unless the caller points elsewhere.

``fixtures/lza-config/`` is a rendered hub-and-spoke configuration (replacements and the
per-region ``include/`` fragments already produced by the Universal Configuration release scripts), so the tests of the
config loader run offline. Set ``LZA_LOCAL_CONFIG_DIR`` to test against another configuration.
"""

from __future__ import annotations

import os
from pathlib import Path

from lza_utils.config_source import LOCAL_CONFIG_DIR_VARIABLE

FIXTURE_CONFIG_DIR = Path(__file__).resolve().parents[2] / "lza_utils" / "tests" / "fixtures" / "lza-config"

os.environ.setdefault(LOCAL_CONFIG_DIR_VARIABLE, str(FIXTURE_CONFIG_DIR))

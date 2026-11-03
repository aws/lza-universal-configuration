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

"""The Universal Configuration ships for the aws, aws-us-gov and aws-eusc partitions.

A test that hardcodes ``arn:aws:`` or ``amazonaws.com`` false-fails or false-passes on the other
two. ARNs must derive from ``Settings().cats_deployment_settings.partition``; a literal that is
the same in every partition (a service principal, an AWS-published fixed hostname, a value LZA
itself hardcodes) carries ``# partition: fixed`` on its line with the reason nearby.
"""

from __future__ import annotations

import re
from pathlib import Path

_TESTS_DIR = Path(__file__).resolve().parents[2] / "tests"
_PARTITION_LITERAL = re.compile(r"arn:aws:|amazonaws\.com")
_FIXED_MARKER = "# partition: fixed"


def _unmarked_partition_literals(root: Path) -> dict[str, list[int]]:
    """``{relative path: [line numbers]}`` of lines with a partition literal and no marker."""
    offenders: dict[str, list[int]] = {}
    for path in sorted(root.rglob("*.py")):
        lines = [
            number
            for number, line in enumerate(path.read_text().splitlines(), start=1)
            if _PARTITION_LITERAL.search(line) and _FIXED_MARKER not in line
        ]
        if lines:
            offenders[str(path.relative_to(root))] = lines
    return offenders


def test_no_unmarked_partition_literals_in_tests() -> None:
    assert _unmarked_partition_literals(_TESTS_DIR) == {}, "derive from cats_deployment_settings.partition or mark the line `# partition: fixed`"


def test_scanner_reports_unmarked_lines_only(tmp_path: Path) -> None:
    # arrange
    (tmp_path / "test_a.py").write_text('x = "arn:aws:s3:::b"\ny = "ec2.amazonaws.com"  # partition: fixed\nz = "https://sts.amazonaws.com"\n')
    (tmp_path / "test_b.py").write_text('w = f"arn:{partition}:s3:::b"\n')

    # act
    offenders = _unmarked_partition_literals(tmp_path)

    # assert
    assert offenders == {"test_a.py": [1, 3]}

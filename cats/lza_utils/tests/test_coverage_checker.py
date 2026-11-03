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

"""Unit tests for lza_utils.coverage_checker AST extraction.

Each test writes a small tests/ tree to tmp_path and runs the extractor over
it, so the assertions are independent of the real test suite. A final test
pins the shipped tests/ directory to zero duplicate (test_suite, test_id)
pairs, which is what CI enforces.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from lza_utils.coverage_checker import (
    _TESTS_DIR,
    extract_duplicate_test_ids,
    extract_evidence_violations,
    extract_standards_from_tests,
)

if TYPE_CHECKING:
    from pathlib import Path

_HEADER = "from cats import cats\nfrom cats_utils.evidence import Evidence\n\n"


def _decorated_test(name: str, **cats_kwargs: str) -> str:
    """One @cats-decorated stub test. Kwarg values are emitted verbatim as Python source."""
    rendered_kwargs = ", ".join(f"{key}={value}" for key, value in cats_kwargs.items())
    return f"@cats({rendered_kwargs})\ndef {name}() -> None: ...\n\n"


def _write_test_module(directory: Path, name: str, *tests: str) -> None:
    (directory / name).write_text(_HEADER + "".join(tests))


def test_duplicate_test_ids_reports_pairs_declared_twice(tmp_path: Path) -> None:
    # arrange
    _write_test_module(
        tmp_path,
        "test_a.py",
        _decorated_test("test_one", standard_name='["LZA-X-1"]', test_suite='"scp"', test_id='"31"', evidence="Evidence.BEHAVIORAL"),
    )
    _write_test_module(
        tmp_path,
        "test_b.py",
        _decorated_test("test_two", standard_name='["LZA-X-1"]', test_suite='"scp"', test_id='"31"', evidence="Evidence.BEHAVIORAL"),
        _decorated_test("test_three", standard_name='["LZA-X-2"]', test_suite='"scp"', test_id='"32"', evidence="Evidence.BEHAVIORAL"),
    )
    expected = {("scp", "31"): ["test_a.py::test_one", "test_b.py::test_two"]}

    # act
    duplicates = extract_duplicate_test_ids(tmp_path)

    # assert
    assert duplicates == expected


def test_duplicate_test_ids_treats_suites_independently(tmp_path: Path) -> None:
    # arrange - same test_id under different suites is not a duplicate
    _write_test_module(
        tmp_path,
        "test_a.py",
        _decorated_test("test_one", standard_name='["LZA-X-1"]', test_suite='"scp"', test_id='"13"', evidence="Evidence.BEHAVIORAL"),
        _decorated_test("test_two", standard_name='["LZA-X-1"]', test_suite='"rcp"', test_id='"13"', evidence="Evidence.BEHAVIORAL"),
    )

    # act
    duplicates = extract_duplicate_test_ids(tmp_path)

    # assert
    assert duplicates == {}


def test_duplicate_test_ids_ignores_decorators_without_both_kwargs(tmp_path: Path) -> None:
    # arrange - a decorator missing test_suite or test_id cannot collide
    _write_test_module(
        tmp_path,
        "test_a.py",
        _decorated_test("test_one", standard_name='["LZA-X-1"]', test_id='"1"', evidence="Evidence.BEHAVIORAL"),
        _decorated_test("test_two", standard_name='["LZA-X-1"]', test_suite='"scp"', evidence="Evidence.BEHAVIORAL"),
        _decorated_test("test_three", standard_name='["LZA-X-1"]', test_id='"1"', evidence="Evidence.BEHAVIORAL"),
    )

    # act
    duplicates = extract_duplicate_test_ids(tmp_path)

    # assert
    assert duplicates == {}


def test_standards_extraction_maps_ids_to_test_names(tmp_path: Path) -> None:
    # arrange
    _write_test_module(
        tmp_path,
        "test_a.py",
        _decorated_test("test_one", standard_name='["LZA-X-1", "LZA-X-2"]', test_suite='"s"', test_id='"1"', evidence="Evidence.CONFIGURATION"),
        _decorated_test("test_two", standard_name='["LZA-X-1"]', test_suite='"s"', test_id='"2"', evidence="Evidence.CONFIGURATION"),
        _decorated_test("test_untagged", test_suite='"s"', test_id='"3"', evidence="Evidence.CONFIGURATION"),
    )
    expected = {"LZA-X-1": ["test_one", "test_two"], "LZA-X-2": ["test_one"]}

    # act
    standards = extract_standards_from_tests(tmp_path)

    # assert
    assert standards == expected


def test_evidence_violations_flag_missing_and_raw_string(tmp_path: Path) -> None:
    # arrange
    _write_test_module(
        tmp_path,
        "test_a.py",
        _decorated_test("test_missing", standard_name='["LZA-X-1"]', test_suite='"s"', test_id='"1"'),
        _decorated_test("test_raw", standard_name='["LZA-X-1"]', test_suite='"s"', test_id='"2"', evidence='"behavioral"'),
        _decorated_test("test_ok", standard_name='["LZA-X-1"]', test_suite='"s"', test_id='"3"', evidence="Evidence.BEHAVIORAL"),
    )

    # act
    violations = extract_evidence_violations(tmp_path)

    # assert - two violations, reported against the offending test names
    violating_tests = [violation.split("::")[1].split(":")[0] for violation in violations]
    assert violating_tests == ["test_missing", "test_raw"]


def test_shipped_tests_have_no_duplicate_test_ids() -> None:
    """Pin the real suite: every (test_suite, test_id) pair is unique."""
    assert extract_duplicate_test_ids(_TESTS_DIR) == {}

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

"""Coverage checker: compare LZA compliance standards against test coverage.

AST-parses tests/ to find @cats(standard_name=[...]) decorators and reports
which standards from the committed compliance mapping are covered, uncovered,
or referenced but unknown.

Usage:
    uv run python -m lza_utils.coverage_checker
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

from cats_utils.evidence import Evidence
from lza_utils.compliance_map import default_compliance_map

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_TESTS_DIR = _PROJECT_ROOT / "tests"


def _iter_cats_decorators(directory: Path) -> list[tuple[Path, ast.FunctionDef, ast.Call]]:
    """AST-parse test files, yielding (file, test_function, @cats decorator call)."""
    found: list[tuple[Path, ast.FunctionDef, ast.Call]] = []
    for test_file in sorted(directory.rglob("test_*.py")):
        source = test_file.read_text()
        tree = ast.parse(source, filename=str(test_file))
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue
            for decorator in node.decorator_list:
                if not isinstance(decorator, ast.Call):
                    continue
                func = decorator.func
                if (isinstance(func, ast.Name) and func.id == "cats") or (isinstance(func, ast.Attribute) and func.attr == "cats"):
                    found.append((test_file, node, decorator))
    return found


def extract_evidence_violations(directory: Path) -> list[str]:
    """Find @cats decorators missing the evidence kwarg or not using the Evidence enum.

    Every test must declare evidence=Evidence.BEHAVIORAL (the test performs
    the controlled action) or evidence=Evidence.CONFIGURATION (the test reads
    deployed state). Raw strings are rejected so the Evidence StrEnum stays
    the single source of truth. The value flows into report.json and OSCAL props.
    """
    member_names = tuple(Evidence.__members__)
    violations: list[str] = []
    for test_file, node, decorator in _iter_cats_decorators(directory):
        location = f"{test_file.relative_to(directory)}::{node.name}"
        evidence_kwargs = [kw for kw in decorator.keywords if kw.arg == "evidence"]
        if not evidence_kwargs:
            violations.append(f"{location}: missing evidence kwarg on @cats")
            continue
        value = evidence_kwargs[0].value
        is_enum_member = (
            isinstance(value, ast.Attribute) and isinstance(value.value, ast.Name) and value.value.id == "Evidence" and value.attr in member_names
        )
        if not is_enum_member:
            violations.append(f"{location}: evidence must be an Evidence enum member ({member_names}) - got {ast.unparse(value)!r}")
    return violations


def extract_standards_from_tests(directory: Path) -> dict[str, list[str]]:
    """AST-parse test files to extract {lza_id: [test_function_name, ...]}."""
    results: dict[str, list[str]] = {}
    for _test_file, node, decorator in _iter_cats_decorators(directory):
        for kw in decorator.keywords:
            if kw.arg != "standard_name" or not isinstance(kw.value, ast.List):
                continue
            for elt in kw.value.elts:
                if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                    results.setdefault(elt.value, []).append(node.name)
    return results


def extract_duplicate_test_ids(directory: Path) -> dict[tuple[str, str], list[str]]:
    """Find (test_suite, test_id) pairs declared by more than one @cats decorator.

    The pair is the stable identity of a test in report.json and OSCAL output,
    so two tests sharing one collapse into a single result. Returns
    {(suite, id): [location, ...]} for every pair declared more than once.
    """
    locations_by_pair: dict[tuple[str, str], list[str]] = {}
    for test_file, node, decorator in _iter_cats_decorators(directory):
        kwargs = {kw.arg: kw.value for kw in decorator.keywords if kw.arg is not None}
        suite = kwargs.get("test_suite")
        test_id = kwargs.get("test_id")
        if not (isinstance(suite, ast.Constant) and isinstance(suite.value, str)):
            continue
        if not (isinstance(test_id, ast.Constant) and isinstance(test_id.value, str)):
            continue
        location = f"{test_file.relative_to(directory)}::{node.name}"
        locations_by_pair.setdefault((suite.value, test_id.value), []).append(location)
    return {pair: locations for pair, locations in sorted(locations_by_pair.items()) if len(locations) > 1}


def main() -> int:
    cm = default_compliance_map()
    all_controls = set(cm.lza_controls())
    tested_standards = extract_standards_from_tests(_TESTS_DIR)
    covered_ids = set(tested_standards.keys())

    covered = all_controls & covered_ids
    uncovered = sorted(all_controls - covered_ids)
    unknown = sorted(covered_ids - all_controls)

    total = len(all_controls)
    pct = (len(covered) / total * 100) if total else 0

    print(f"Coverage: {len(covered)}/{total} ({pct:.1f}%)\n")

    if uncovered:
        print(f"Uncovered ({len(uncovered)}):")
        for lza_id in uncovered:
            meta = cm.metadata(lza_id)
            label = f" [{meta.capability}]" if meta else ""
            print(f"  {lza_id}{label}")
        print()

    if unknown:
        print(f"Referenced in tests but not in workbook ({len(unknown)}):")
        for lza_id in unknown:
            print(f"  {lza_id}")
        print()

    if not uncovered and not unknown:
        print("All standards covered. No orphaned references.")

    evidence_violations = extract_evidence_violations(_TESTS_DIR)
    if evidence_violations:
        print(f"\nEvidence marker violations ({len(evidence_violations)}):")
        for violation in evidence_violations:
            print(f"  {violation}")

    duplicate_test_ids = extract_duplicate_test_ids(_TESTS_DIR)
    if duplicate_test_ids:
        print(f"\nDuplicate (test_suite, test_id) pairs ({len(duplicate_test_ids)}):")
        for (suite, test_id), locations in duplicate_test_ids.items():
            print(f"  {suite}/{test_id}: {', '.join(locations)}")

    return 1 if uncovered or evidence_violations or duplicate_test_ids else 0


if __name__ == "__main__":
    sys.exit(main())

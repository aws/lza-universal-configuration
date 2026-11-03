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

"""The pytest_cats_standards hook: the OSCAL registry built from the shipped workbook."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, cast

import pytest
from cats.exceptions import CatsConfigError
from cats.hookspecs import StandardMetadata

if TYPE_CHECKING:
    from types import ModuleType

_ROOT = Path(__file__).resolve().parents[2]


def _root_conftest() -> ModuleType:
    """tests/conftest.py loaded by path (pytest's conftests are not a package)."""
    spec = importlib.util.spec_from_file_location("lza_root_conftest", _ROOT / "tests" / "conftest.py")
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_registry_without_a_framework_reports_workbook_control_ids(monkeypatch: pytest.MonkeyPatch) -> None:
    """No framework is chosen for the user: unset, every control resolves to its own workbook ID."""
    # arrange
    monkeypatch.delenv("LZA_OSCAL_FRAMEWORK", raising=False)
    monkeypatch.delenv("LZA_COMPLIANCE_MAP", raising=False)

    # act
    registry = _root_conftest().pytest_cats_standards()

    # assert
    assert registry is not None
    assert len(registry) == 193
    assert registry["LZA-G-OM-1"] == StandardMetadata(control_ids=["LZA-G-OM-1"], control_group="Governance")


def test_registry_resolves_nist_800_53_when_selected(monkeypatch: pytest.MonkeyPatch) -> None:
    # arrange
    monkeypatch.setenv("LZA_OSCAL_FRAMEWORK", "NIST 800-53 Rev5")

    # act
    registry = _root_conftest().pytest_cats_standards()

    # assert
    assert registry is not None
    assert registry["LZA-G-OM-1"] == StandardMetadata(control_ids=["AC-2.1", "CM-8", "PL-9", "SA-8.14", "SC-2", "SC-2.1"], control_group="Governance")


def test_registry_resolves_the_selected_framework(monkeypatch: pytest.MonkeyPatch) -> None:
    # arrange
    monkeypatch.setenv("LZA_OSCAL_FRAMEWORK", "ISM New Zealand")

    # act
    registry = _root_conftest().pytest_cats_standards()

    # assert
    assert registry is not None
    assert registry["LZA-G-OM-1"] == StandardMetadata(control_ids=["CID-5820"], control_group="Governance")


def test_unknown_framework_fails_the_registry(monkeypatch: pytest.MonkeyPatch) -> None:
    """A framework name that is not a workbook column (the pre-1.4.0 'C5:2020') must not quietly resolve nothing."""
    # arrange
    monkeypatch.setenv("LZA_OSCAL_FRAMEWORK", "C5:2020")

    # act / assert
    with pytest.raises(CatsConfigError, match=r"LZA_OSCAL_FRAMEWORK='C5:2020' is not a framework column"):
        _root_conftest().pytest_cats_standards()


def test_unknown_framework_fails_the_session_at_configure(monkeypatch: pytest.MonkeyPatch) -> None:
    """The engine turns an exception from pytest_cats_standards into a warning and reports without the
    registry, so the check has to fail the session earlier: a misspelled framework must never produce
    a report keyed by workbook IDs when the user asked for a framework."""
    # arrange
    monkeypatch.setenv("LZA_OSCAL_FRAMEWORK", "C5:2020")
    config = cast("pytest.Config", SimpleNamespace(option=SimpleNamespace()))

    # act / assert
    with pytest.raises(pytest.UsageError, match=r"LZA_OSCAL_FRAMEWORK='C5:2020' is not a framework column in the compliance workbook"):
        _root_conftest().pytest_configure(config)


def test_configure_accepts_an_unset_framework(monkeypatch: pytest.MonkeyPatch) -> None:
    # arrange
    monkeypatch.delenv("LZA_OSCAL_FRAMEWORK", raising=False)
    config = cast("pytest.Config", SimpleNamespace(option=SimpleNamespace(dist="load")))

    # act
    _root_conftest().pytest_configure(config)

    # assert
    assert config.option.dist == "worksteal"

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

"""Root conftest — CATS hook implementations for the test pack.

Implements ``pytest_cats_test_pack`` so the AWS API calls CATS makes on behalf
of this pack carry ``AwsCatsPack/lza_uc#<version>`` in their User-Agent
alongside the engine's ``AwsCats/<version>`` token. The version is read from
``pyproject.toml`` so a release bump propagates without a code change.

Implements ``pytest_cats_provides`` so an unedited cats.yaml provides every requirement the
deployment satisfies (``standard-deployment``, ``workload-accounts``, ``control-tower``,
``identity-center``; see the hook and ``cats_utils.requirement``).

Implements ``pytest_cats_standards`` so the OSCAL AR writer can resolve
LZA control IDs (e.g. ``LZA-G-DCP-1``) to framework-specific IDs
(e.g. NIST ``AC-3``, ``SC-7``) and attach a ``control-group`` label
(LZA "Core Foundation") for grouping observations in viewer.oscal.io.

The mapping and target framework are read from environment variables so
they can be set per-environment without touching code:

* ``LZA_COMPLIANCE_MAP`` — path to a compliance workbook CSV in the LZA Compliance
  Workbook format. Defaults to the shipped ``lza-compliance-workbook-<version>.csv``.
* ``LZA_OSCAL_FRAMEWORK`` — framework column header from the workbook. There is
  no default: unset, every result is reported under its workbook control ID and
  no framework mapping is applied. A value that is not a column header fails the
  session before any test runs (``pytest_configure``), because the engine treats
  an exception from ``pytest_cats_standards`` itself as a warning and drops the
  registry, which would quietly produce a report in the wrong vocabulary.

If the mapping file is absent the hook returns ``None`` and CATS falls
back to decorator values then to ``[standard_name]`` as a single
control ID (see ``cats.hookspecs.pytest_cats_standards``).
"""

from __future__ import annotations

import logging
import os
import tomllib
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from cats import CatsTestPack
from cats.exceptions import CatsConfigError
from cats.hookspecs import StandardMetadata
from diskcache import Cache  # type: ignore[import-untyped]

from cats_utils.requirement import Requirement, provided_requirements
from lza_utils.compliance_map import DEFAULT_COMPLIANCE_WORKBOOK_PATH, ComplianceMap
from lza_utils.lza_config import lza_config

if TYPE_CHECKING:
    from cats.config import CatsConfig

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_PYPROJECT_PATH = _PROJECT_ROOT / "pyproject.toml"


def pytest_sessionstart(session: pytest.Session) -> None:
    """Clear the diskcache at the start of each test run."""
    cache = Cache(".pytest_cache/cats_diskcache")
    cache.clear()


def pytest_configure(config: pytest.Config) -> None:
    """Use worksteal distribution for xdist, and refuse a framework name the workbook does not have.

    Worksteal lets idle workers take tests from busy ones, improving overall parallelism
    when test durations vary.

    The framework check runs here, not only in ``pytest_cats_standards``, because the engine
    catches an exception from that hook, warns, and reports without the registry. A misspelled
    ``LZA_OSCAL_FRAMEWORK`` would then produce a report keyed by workbook IDs instead of the
    framework the user asked for, which is wrong evidence delivered quietly.

    Raises:
        pytest.UsageError: ``LZA_OSCAL_FRAMEWORK`` is set to something other than a framework
            column header of the compliance workbook.
    """
    if hasattr(config.option, "dist"):
        config.option.dist = "worksteal"
    map_path = compliance_map_path()
    if map_path.is_file():
        try:
            selected_framework(ComplianceMap.from_csv(map_path))
        except CatsConfigError as e:
            raise pytest.UsageError(str(e)) from e


def compliance_map_path() -> Path:
    """The compliance workbook CSV: ``LZA_COMPLIANCE_MAP``, or the one shipped with the pack."""
    return Path(os.environ.get("LZA_COMPLIANCE_MAP", DEFAULT_COMPLIANCE_WORKBOOK_PATH))


def selected_framework(cmap: ComplianceMap) -> str | None:
    """The framework ``LZA_OSCAL_FRAMEWORK`` names, or ``None`` when it is unset.

    There is no default framework: a report is only ever aligned to a framework the user chose.

    Raises:
        CatsConfigError: The value is not a framework column header in ``cmap``.
    """
    framework = os.environ.get("LZA_OSCAL_FRAMEWORK")
    if framework is None:
        return None
    if framework not in cmap.frameworks():
        raise CatsConfigError(
            f"LZA_OSCAL_FRAMEWORK={framework!r} is not a framework column in the compliance workbook; valid values: {cmap.frameworks()}"
        )
    return framework


def pytest_cats_test_pack() -> CatsTestPack:
    """Identify this test pack in the User-Agent of every AWS API call CATS makes.

    Read once per process by the CATS plugin's ``pytest_configure``; this
    ``tests/conftest.py`` is loaded before that because pytest collects
    ``test*/`` directory conftests up front.
    """
    with _PYPROJECT_PATH.open("rb") as pyproject_file:
        project = tomllib.load(pyproject_file)["project"]
    return CatsTestPack(name="lza_uc", version=project["version"])


def pytest_cats_provides(cats_config: CatsConfig) -> set[Requirement]:
    """Provide what cats.yaml and the deployed LZA config show this deployment has, so an unedited config runs every applicable test.

    See ``cats_utils.requirement.provided_requirements`` for the rules. Called by the engine from
    ``pytest_collection_modifyitems``, after every test module has imported, so ``lza_config()`` is
    already loaded (``LZA_LOCAL_CONFIG_DIR`` honoured) by the time this runs. If it cannot load, the
    same error has already failed collection of every module that parametrizes from it, and the
    engine names this hook in a warning as well: nothing is silently provided or withheld.
    """
    return provided_requirements(cats_config, lza_config())


def pytest_cats_standards() -> dict[str, StandardMetadata] | None:
    """Build a standard_name → StandardMetadata registry from the LZA compliance mapping.

    Called once per session on the main process, after collection and before
    the first test runs, per ``cats.hookspecs.CatsHookSpec.pytest_cats_standards``.
    Every implementer's registry is merged, so a standard declared elsewhere
    must carry the same value. Returning ``None`` opts this pack out.

    With ``LZA_OSCAL_FRAMEWORK`` set, each workbook control resolves to that framework's
    control IDs. Unset, each control resolves to itself, so the report stays in the
    workbook's own vocabulary; the ``control-group`` (core foundation) is attached either way.
    """
    map_path = compliance_map_path()
    if not map_path.is_file():
        logger.info("\nCompliance workbook not found at %s - standards registry disabled", map_path)
        return None

    cmap = ComplianceMap.from_csv(map_path)
    framework = selected_framework(cmap)
    logger.info("\nLoaded compliance workbook from %s (framework=%s)", map_path, framework or "none, reporting workbook control IDs")

    registry: dict[str, StandardMetadata] = {}
    for lza_id in cmap.lza_controls():
        meta = cmap.metadata(lza_id)
        registry[lza_id] = StandardMetadata(
            control_ids=cmap.resolve(lza_id, framework) if framework is not None else [lza_id],
            control_group=meta.foundation if meta and meta.foundation else None,
        )
    return registry

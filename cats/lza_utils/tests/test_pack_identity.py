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

"""The pack's User-Agent identity."""

from __future__ import annotations

import importlib.util
import tomllib
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cats import CatsTestPack

_ROOT = Path(__file__).resolve().parents[2]
_PYPROJECT = _ROOT / "pyproject.toml"


def pytest_cats_test_pack() -> CatsTestPack:
    """The hook as implemented in tests/conftest.py, loaded by path (pytest's conftests are not a package)."""
    spec = importlib.util.spec_from_file_location("lza_root_conftest", _ROOT / "tests" / "conftest.py")
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    pack: CatsTestPack = module.pytest_cats_test_pack()
    return pack


def test_user_agent_token_is_lza_uc_at_the_project_version() -> None:
    # arrange
    with _PYPROJECT.open("rb") as pyproject_file:
        pyproject = tomllib.load(pyproject_file)
    expected = ("lza_uc", pyproject["project"]["version"])

    # act
    pack = pytest_cats_test_pack()

    # assert
    assert (pack.name, pack.version) == expected

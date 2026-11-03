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

"""Tests for the account-set beliefs in cats_utils.accounts.

The oracle is a hand-written organization, not the loaded cats.yaml, so these tests assert
concrete expected lists and hold under every shipped config. A container deployment's
``LzaDeployment`` account is included so the ``lza-deployment`` carve-out is always exercised.
"""

from __future__ import annotations

import pytest

import cats_utils.accounts
from cats_utils.accounts import (
    all_accounts,
    core_ou_accounts,
    infrastructure_accounts,
    internet_facing_accounts,
    lza_deployment_account,
    management_account,
    non_internet_facing_accounts,
    non_management_accounts,
    perimeter_account,
    workload_account_params,
    workload_accounts,
)

_ORGANIZATION: dict[str, dict[str, str]] = {
    "Management": {"management": ""},
    "Audit": {},
    "LogArchive": {},
    "Network": {"infrastructure": ""},
    "Perimeter": {"infrastructure": "", "perimeter": ""},
    "Dev": {"workload": ""},
    "LzaDeployment": {"lza-deployment": ""},
}


def _patch_organization(monkeypatch: pytest.MonkeyPatch, organization: dict[str, dict[str, str]]) -> None:
    """Replace the engine's cats.yaml readers with a fixed organization."""
    monkeypatch.setattr(cats_utils.accounts, "get_account_fixture_names", lambda: [f"{name}_account" for name in organization])
    monkeypatch.setattr(
        cats_utils.accounts, "get_accounts_by_tag", lambda key: [f"{name}_account" for name, tags in organization.items() if key in tags]
    )


def test_all_accounts_is_every_account_under_test_sorted(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_organization(monkeypatch, _ORGANIZATION)
    assert all_accounts() == [
        "Audit_account",
        "Dev_account",
        "LogArchive_account",
        "LzaDeployment_account",
        "Management_account",
        "Network_account",
        "Perimeter_account",
    ]


def test_management_account_is_the_one_tagged_management(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_organization(monkeypatch, _ORGANIZATION)
    assert management_account() == "Management_account"


def test_management_account_rejects_no_management_tag(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_organization(monkeypatch, {"Audit": {}, "LogArchive": {}})
    with pytest.raises(AssertionError, match="Exactly one account under test must be tagged 'management', found \\[\\]"):
        management_account()


def test_management_account_rejects_two_management_tags(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_organization(monkeypatch, {"Management": {"management": ""}, "Audit": {"management": ""}})
    with pytest.raises(AssertionError, match="found \\['Audit_account', 'Management_account'\\]"):
        management_account()


def test_non_management_accounts_is_everything_but_management(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_organization(monkeypatch, _ORGANIZATION)
    assert non_management_accounts() == [
        "Audit_account",
        "Dev_account",
        "LogArchive_account",
        "LzaDeployment_account",
        "Network_account",
        "Perimeter_account",
    ]


def test_non_management_accounts_rejects_a_management_only_config(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_organization(monkeypatch, {"Management": {"management": ""}})
    with pytest.raises(AssertionError, match="No account under test other than the one tagged 'management'"):
        non_management_accounts()


def test_core_ou_accounts_exclude_the_lza_deployment_account(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_organization(monkeypatch, _ORGANIZATION)
    assert core_ou_accounts() == ["Audit_account", "Dev_account", "LogArchive_account", "Network_account", "Perimeter_account"]


def test_core_ou_accounts_equal_non_management_on_a_standard_deployment(monkeypatch: pytest.MonkeyPatch) -> None:
    standard = {name: tags for name, tags in _ORGANIZATION.items() if name != "LzaDeployment"}
    _patch_organization(monkeypatch, standard)
    expected = ["Audit_account", "Dev_account", "LogArchive_account", "Network_account", "Perimeter_account"]
    assert core_ou_accounts() == non_management_accounts() == expected


def test_core_ou_accounts_rejects_only_deployment_members(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_organization(monkeypatch, {"Management": {"management": ""}, "LzaDeployment": {"lza-deployment": ""}})
    with pytest.raises(AssertionError, match="No member account under test other than those tagged 'lza-deployment'"):
        core_ou_accounts()


def test_lza_deployment_account_is_the_one_tagged_lza_deployment(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_organization(monkeypatch, _ORGANIZATION)
    assert lza_deployment_account() == "LzaDeployment_account"


def test_lza_deployment_account_rejects_a_standard_deployment(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_organization(monkeypatch, {"Management": {"management": ""}, "Audit": {}})
    with pytest.raises(AssertionError, match="Exactly one account under test must be tagged 'lza-deployment', found \\[\\]"):
        lza_deployment_account()


def test_perimeter_account_is_the_one_tagged_perimeter(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_organization(monkeypatch, _ORGANIZATION)
    assert perimeter_account() == "Perimeter_account"


def test_perimeter_account_is_found_by_tag_not_by_name(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_organization(monkeypatch, {"Management": {"management": ""}, "Edge": {"infrastructure": "", "perimeter": ""}})
    assert perimeter_account() == "Edge_account"


def test_perimeter_account_rejects_no_perimeter_tag(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_organization(monkeypatch, {"Management": {"management": ""}, "Perimeter": {"infrastructure": ""}})
    with pytest.raises(AssertionError, match="Exactly one account under test must be tagged 'perimeter', found \\[\\]"):
        perimeter_account()


def test_perimeter_account_rejects_two_perimeter_tags(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_organization(monkeypatch, {"Perimeter": {"perimeter": ""}, "Network": {"perimeter": ""}})
    with pytest.raises(AssertionError, match="found \\['Network_account', 'Perimeter_account'\\]"):
        perimeter_account()


def test_internet_facing_accounts_are_perimeter_and_the_lza_deployment_account(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_organization(monkeypatch, _ORGANIZATION)
    assert internet_facing_accounts() == ["LzaDeployment_account", "Perimeter_account"]


def test_internet_facing_accounts_are_perimeter_only_on_a_standard_deployment(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_organization(monkeypatch, {name: tags for name, tags in _ORGANIZATION.items() if name != "LzaDeployment"})
    assert internet_facing_accounts() == ["Perimeter_account"]


def test_non_internet_facing_accounts_are_everything_else_management_included(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_organization(monkeypatch, _ORGANIZATION)
    assert non_internet_facing_accounts() == ["Audit_account", "Dev_account", "LogArchive_account", "Management_account", "Network_account"]


def test_non_internet_facing_accounts_rejects_only_internet_facing_members(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_organization(monkeypatch, {"Perimeter": {"perimeter": ""}, "LzaDeployment": {"lza-deployment": ""}})
    with pytest.raises(AssertionError, match="No account under test other than those tagged 'perimeter' or 'lza-deployment'"):
        non_internet_facing_accounts()


def test_infrastructure_accounts_are_those_tagged_infrastructure_sorted(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_organization(monkeypatch, _ORGANIZATION)
    assert infrastructure_accounts() == ["Network_account", "Perimeter_account"]


def test_infrastructure_accounts_rejects_no_infrastructure_tag(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_organization(monkeypatch, {"Management": {"management": ""}, "Audit": {}})
    with pytest.raises(AssertionError, match="No account under test is tagged 'infrastructure'"):
        infrastructure_accounts()


def test_workload_accounts_are_those_tagged_workload(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_organization(monkeypatch, _ORGANIZATION)
    assert workload_accounts() == ["Dev_account"]
    assert workload_account_params() == ["Dev_account"]


def test_workload_accounts_are_empty_not_an_error_on_an_unmodified_universal_configuration(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_organization(monkeypatch, {name: tags for name, tags in _ORGANIZATION.items() if name != "Dev"})
    assert workload_accounts() == []
    assert workload_account_params() == [pytest.param("<no workload accounts>", id="none")]

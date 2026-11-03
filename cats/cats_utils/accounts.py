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

"""Account fixture selection helpers shared across test files.

The account sets below are what the pack believes about a Universal Configuration
organization. They are read from the account tags in cats.yaml (``management``,
``lza-deployment``, ``perimeter``, alongside the existing ``workload`` and
``infrastructure``), so they do not depend on how an account is named. State a belief here
once rather than deriving it per test.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from cats import get_accounts_by_tag
from cats.constants import get_account_fixture_names

if TYPE_CHECKING:
    from collections.abc import Sequence

    from _pytest.mark.structures import ParameterSet

    from cats_types import CatsAccountProtocol, NetworkTargetProtocol

MANAGEMENT_TAG = "management"
LZA_DEPLOYMENT_TAG = "lza-deployment"
PERIMETER_TAG = "perimeter"
INFRASTRUCTURE_TAG = "infrastructure"
WORKLOAD_TAG = "workload"


def all_accounts() -> list[str]:
    """Every account under test, Management included."""
    return sorted(get_account_fixture_names())


def management_account() -> str:
    """The one account tagged ``management`` in cats.yaml."""
    tagged = get_accounts_by_tag(MANAGEMENT_TAG)
    assert len(tagged) == 1, f"Exactly one account under test must be tagged '{MANAGEMENT_TAG}', found {sorted(tagged)}"
    return tagged[0]


def lza_deployment_account() -> str:
    """The one account tagged ``lza-deployment`` in cats.yaml: the container deployment's LZA account.

    Resolved by tag, not by name: its ``name`` in accounts-config.yaml (``LzaDeployment``,
    ``LzaDeploymentAccount``, ...) need not match its key in cats.yaml.
    """
    tagged = get_accounts_by_tag(LZA_DEPLOYMENT_TAG)
    assert len(tagged) == 1, f"Exactly one account under test must be tagged '{LZA_DEPLOYMENT_TAG}', found {sorted(tagged)}"
    return tagged[0]


def perimeter_account() -> str:
    """The one account tagged ``perimeter`` in cats.yaml."""
    tagged = get_accounts_by_tag(PERIMETER_TAG)
    assert len(tagged) == 1, f"Exactly one account under test must be tagged '{PERIMETER_TAG}', found {sorted(tagged)}"
    return tagged[0]


def internet_facing_accounts() -> list[str]:
    """The accounts allowed an internet or NAT gateway: ``perimeter`` plus, if tagged, ``lza-deployment``. Sorted."""
    return sorted([perimeter_account(), *get_accounts_by_tag(LZA_DEPLOYMENT_TAG)])


def non_internet_facing_accounts() -> list[str]:
    """Every account under test except ``internet_facing_accounts()``, Management included."""
    internet_facing = internet_facing_accounts()
    others = [name for name in all_accounts() if name not in internet_facing]
    assert others, f"No account under test other than those tagged '{PERIMETER_TAG}' or '{LZA_DEPLOYMENT_TAG}'"
    return others


def non_management_accounts() -> list[str]:
    """Every account under test except Management: the organization's member accounts.

    This is the set the SCP enforcement probes run in. Every member account is governed by LZA
    guardrail SCPs that deny the probed actions: the core, infrastructure and workloads
    guardrails in the Security, Infrastructure and Workloads OU families, and the
    ``LzaDeployment-Guardrails`` SCPs in the container deployment's ``LzaDeployment`` OU, whose
    statements deny every action the core guardrails deny. The deployment SCPs scope some denies
    to ``<prefix>-<stage stem>*`` resources; probes aim inside that scope
    (``lza_config().stage_resource_prefixes``) so one target holds in every account.
    """
    management = management_account()
    members = [name for name in all_accounts() if name != management]
    assert members, "No account under test other than the one tagged 'management'"
    return members


def core_ou_accounts() -> list[str]:
    """The member accounts in the Security, Infrastructure and Workloads OU families.

    The belief: every member account sits in one of those families, except the container
    deployment's account (tagged ``lza-deployment``), which the Universal Configuration keeps in
    its own ``LzaDeployment`` OU. Two things attach to the core families only and so are probed
    here only: the ``Core-Rcp-Guardrails`` RCP (the ``LzaDeployment`` OU carries no RCP) and
    Control Tower's detective ``AWSControlTower-*`` Config rules (the ``LzaDeployment`` OU is
    governed by Control Tower but has none). A standard deployment has no such account, so this
    set then equals ``non_management_accounts()``.
    """
    deployment_accounts = get_accounts_by_tag(LZA_DEPLOYMENT_TAG)
    core = [name for name in non_management_accounts() if name not in deployment_accounts]
    assert core, f"No member account under test other than those tagged '{LZA_DEPLOYMENT_TAG}'"
    return core


def infrastructure_accounts() -> list[str]:
    """The accounts tagged ``infrastructure`` in cats.yaml, sorted for pytest-xdist; every deployment has them."""
    tagged = sorted(get_accounts_by_tag(INFRASTRUCTURE_TAG))
    assert tagged, f"No account under test is tagged '{INFRASTRUCTURE_TAG}'"
    return tagged


def workload_accounts() -> list[str]:
    """The accounts tagged ``workload`` in cats.yaml, sorted for pytest-xdist; empty on an unmodified Universal Configuration."""
    return sorted(get_accounts_by_tag(WORKLOAD_TAG))


def workload_account_params() -> list[str | ParameterSet]:
    """One ``account_fixture_name`` parameter per workload account, or a single placeholder when there are none.

    pyproject sets ``empty_parameter_set_mark = fail_at_collect``, so a deployment with no workload
    accounts needs one parameter to collect at all; ``@cats_requires(Requirement.WORKLOAD_ACCOUNTS)``
    on the test then records the item ``not_run``. The placeholder never reaches a test body.
    """
    return list(workload_accounts()) or [pytest.param("<no workload accounts>", id="none")]


def declared_network_handlers(account: CatsAccountProtocol) -> Sequence[NetworkTargetProtocol]:
    """Network handlers for every target declared for the account in cats.yaml.

    The engine builds these from cats.yaml and refuses to construct the account when a
    declared target is missing from the deployed stack. Fails when none are declared:
    probing zero handlers would pass vacuously.
    """
    handlers = account.network_handlers
    assert handlers, f"No network handlers declared for {account.name}"
    return handlers

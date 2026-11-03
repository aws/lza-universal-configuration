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

"""Deployment requirements for the @cats_requires(...) decorator.

A test that applies to one Universal Configuration variant declares it, e.g.
``@cats_requires(Requirement.CONTAINER_DEPLOYMENT)``; the engine runs it only when
``test_selection.provides`` (or ``pytest_cats_provides`` in tests/conftest.py)
provides every requirement it names, and records it ``not_run`` otherwise.
Use the enum members: a misspelled string is a test that never runs anywhere.

``provided_requirements`` derives every requirement a deployment provides from cats.yaml
and the deployed LZA config, so nothing but ``container-deployment`` ever has to be listed
in ``test_selection.provides``.
"""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cats.config import CatsConfig

    from lza_utils.lza_config import LzaConfig


class Requirement(StrEnum):
    """A property of the deployment a test needs in order to apply.

    STANDARD_DEPLOYMENT: LZA runs from CodePipeline in the management account.
        Provided by default.
    CONTAINER_DEPLOYMENT: LZA runs as an ECS task in a dedicated LzaDeployment
        account (InstallerContainerStack). Provided only when listed in
        ``test_selection.provides``. Mutually exclusive with STANDARD_DEPLOYMENT.
    WORKLOAD_ACCOUNTS: at least one account under test is tagged ``workload``.
        An unmodified Universal Configuration creates the Workloads OUs empty, so
        the east-west traffic tests do not apply until a customer adds accounts.
        Provided when cats.yaml tags any.
    CONTROL_TOWER: the organization is governed by AWS Control Tower
        (``controlTower.enable: true`` in global-config.yaml). The Organizations-only
        variant has no landing zone, no enabled controls and no ``AWSControlTower-*``
        Config rules, so the tests that verify and protect Control Tower itself do not
        apply there. Provided from the LZA config.
    IDENTITY_CENTER: iam-config.yaml declares an ``identityCenter`` block, so LZA
        manages an IAM Identity Center instance and its delegated administrator.
        Provided from the LZA config.
    DNS_FIREWALL: network-config.yaml BLOCKs at least one Route 53 Resolver DNS
        Firewall managed domain list. The European Sovereign Cloud package removes
        the rule groups because managed domain lists do not exist in that partition,
        so the probes that resolve the lists' control domains do not apply there.
        Provided from the LZA config.
    """

    STANDARD_DEPLOYMENT = "standard-deployment"
    CONTAINER_DEPLOYMENT = "container-deployment"
    WORKLOAD_ACCOUNTS = "workload-accounts"
    CONTROL_TOWER = "control-tower"
    IDENTITY_CENTER = "identity-center"
    DNS_FIREWALL = "dns-firewall"


def provided_requirements(cats_config: CatsConfig, lza: LzaConfig) -> set[Requirement]:
    """Every requirement this deployment provides, derived from cats.yaml and the LZA config.

    ``standard-deployment`` unless the user declared the container variant in
    ``test_selection.provides`` (the two are mutually exclusive); ``workload-accounts`` when
    any account under test is tagged ``workload``; ``control-tower`` when global-config.yaml
    enables Control Tower; ``identity-center`` when iam-config.yaml declares the block;
    ``dns-firewall`` when network-config.yaml BLOCKs a managed domain list. The
    engine unions the result with ``test_selection.provides`` before applying
    ``@cats_requires``, so a requirement derived here never has to be listed there.
    """
    provided: set[Requirement] = set()
    if Requirement.CONTAINER_DEPLOYMENT not in cats_config.test_selection.provides:
        provided.add(Requirement.STANDARD_DEPLOYMENT)
    if any("workload" in account.tags for account in cats_config.accounts_under_test.values()):
        provided.add(Requirement.WORKLOAD_ACCOUNTS)
    if lza.control_tower_enabled:
        provided.add(Requirement.CONTROL_TOWER)
    if lza.identity_center_declared:
        provided.add(Requirement.IDENTITY_CENTER)
    if lza.dns_firewall_declared:
        provided.add(Requirement.DNS_FIREWALL)
    return provided

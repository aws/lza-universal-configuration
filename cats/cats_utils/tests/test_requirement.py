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

"""Tests for cats_utils.requirement.provided_requirements.

Each variant of the deployment is built from the loaded cats.yaml and LZA config with one fact
changed, and the expected set is written out by hand, so the rules hold under every shipped
config rather than only the one the test run happens to load.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from cats.config import Settings

from cats_utils.requirement import Requirement, provided_requirements
from lza_utils.lza_config import LzaConfig, lza_config

if TYPE_CHECKING:
    from cats.config import CatsConfig


def _cats_variant(*, provides: list[str], workload_tagged: bool) -> CatsConfig:
    """The loaded cats.yaml with ``test_selection.provides`` replaced and a workload-tagged account present or absent.

    The shipped cats.yaml lists no workload account (the Universal Configuration creates none),
    so the tagged variant adds one modelled on an existing entry rather than relying on the
    config under test to carry it.
    """
    cats_config = Settings()
    accounts = {name: account for name, account in cats_config.accounts_under_test.items() if "workload" not in account.tags}
    if workload_tagged:
        template = next(iter(accounts.values()))
        accounts["Workload"] = template.model_copy(update={"tags": {**template.tags, "workload": None}})
    return cats_config.model_copy(
        update={"test_selection": cats_config.test_selection.model_copy(update={"provides": provides}), "accounts_under_test": accounts}
    )


def _lza_variant(*, control_tower_enabled: bool, identity_center_declared: bool, dns_firewall_declared: bool = True) -> LzaConfig:
    """The loaded LZA config with ``controlTower.enable`` set and the ``identityCenter`` block and DNS Firewall rule groups kept or dropped."""
    loaded = lza_config()
    if identity_center_declared:
        assert loaded.iam.identity_center is not None, "the loaded iam-config.yaml declares no identityCenter block"
    central = loaded.network.central_network_services
    assert central is not None, "the loaded network-config.yaml declares no centralNetworkServices"
    assert central.route53_resolver is not None, "the loaded network-config.yaml declares no route53Resolver"
    if dns_firewall_declared:
        assert central.route53_resolver.firewall_rule_groups, "the loaded network-config.yaml declares no DNS Firewall rule groups"
        network = loaded.network
    else:
        # The EUSC package comments the rule groups out of the config.
        network = loaded.network.model_copy(
            update={
                "central_network_services": central.model_copy(
                    update={"route53_resolver": central.route53_resolver.model_copy(update={"firewall_rule_groups": None})}
                )
            }
        )
    return LzaConfig(
        accounts=loaded.accounts,
        global_=loaded.global_.model_copy(
            update={"control_tower": loaded.global_.control_tower.model_copy(update={"enable": control_tower_enabled})}
        ),
        organization=loaded.organization,
        security=loaded.security,
        iam=loaded.iam if identity_center_declared else loaded.iam.model_copy(update={"identity_center": None}),
        network=network,
        replacements=loaded.replacements,
    )


def test_control_tower_enabled_reads_global_config() -> None:
    assert _lza_variant(control_tower_enabled=True, identity_center_declared=True).control_tower_enabled is True
    assert _lza_variant(control_tower_enabled=False, identity_center_declared=True).control_tower_enabled is False


def test_identity_center_declared_reads_iam_config() -> None:
    assert _lza_variant(control_tower_enabled=True, identity_center_declared=True).identity_center_declared is True
    assert _lza_variant(control_tower_enabled=True, identity_center_declared=False).identity_center_declared is False


def test_dns_firewall_declared_reads_network_config() -> None:
    assert _lza_variant(control_tower_enabled=True, identity_center_declared=True, dns_firewall_declared=True).dns_firewall_declared is True
    assert _lza_variant(control_tower_enabled=True, identity_center_declared=True, dns_firewall_declared=False).dns_firewall_declared is False


def test_dns_firewall_blocked_managed_lists_is_sorted_and_deduplicated() -> None:
    lza = _lza_variant(control_tower_enabled=True, identity_center_declared=True)
    lists = lza.dns_firewall_blocked_managed_lists
    assert lists == sorted(set(lists))
    assert lists, "the loaded network-config.yaml BLOCKs no managed domain list"


def test_unmodified_universal_configuration_provides_every_derived_requirement() -> None:
    """Control Tower on, Identity Center declared, workload accounts tagged, nothing listed in provides."""
    # arrange
    cats_config = _cats_variant(provides=[], workload_tagged=True)
    lza = _lza_variant(control_tower_enabled=True, identity_center_declared=True)

    # act
    provided = provided_requirements(cats_config, lza)

    # assert
    assert provided == {
        Requirement.STANDARD_DEPLOYMENT,
        Requirement.WORKLOAD_ACCOUNTS,
        Requirement.CONTROL_TOWER,
        Requirement.IDENTITY_CENTER,
        Requirement.DNS_FIREWALL,
    }


def test_organizations_only_container_deployment_provides_neither_governance_requirement() -> None:
    """Container variant, controlTower.enable false, no identityCenter block, no workload accounts."""
    # arrange
    cats_config = _cats_variant(provides=[Requirement.CONTAINER_DEPLOYMENT], workload_tagged=False)
    lza = _lza_variant(control_tower_enabled=False, identity_center_declared=False, dns_firewall_declared=False)

    # act
    provided = provided_requirements(cats_config, lza)

    # assert - container-deployment itself comes from test_selection.provides, which the engine unions in
    assert provided == set()


@pytest.mark.parametrize(
    ("control_tower_enabled", "identity_center_declared", "expected"),
    [
        (True, False, {Requirement.STANDARD_DEPLOYMENT, Requirement.CONTROL_TOWER, Requirement.DNS_FIREWALL}),
        (False, True, {Requirement.STANDARD_DEPLOYMENT, Requirement.IDENTITY_CENTER, Requirement.DNS_FIREWALL}),
    ],
    ids=["control-tower-without-identity-center", "identity-center-without-control-tower"],
)
def test_governance_requirements_are_independent(control_tower_enabled: bool, identity_center_declared: bool, expected: set[Requirement]) -> None:
    # arrange
    cats_config = _cats_variant(provides=[], workload_tagged=False)
    lza = _lza_variant(control_tower_enabled=control_tower_enabled, identity_center_declared=identity_center_declared)

    # act
    provided = provided_requirements(cats_config, lza)

    # assert
    assert provided == expected


def test_listing_container_deployment_withholds_standard_deployment_only() -> None:
    # arrange
    cats_config = _cats_variant(provides=[Requirement.CONTAINER_DEPLOYMENT], workload_tagged=True)
    lza = _lza_variant(control_tower_enabled=True, identity_center_declared=True)

    # act
    provided = provided_requirements(cats_config, lza)

    # assert
    assert provided == {Requirement.WORKLOAD_ACCOUNTS, Requirement.CONTROL_TOWER, Requirement.IDENTITY_CENTER, Requirement.DNS_FIREWALL}


def test_eusc_package_without_dns_firewall_withholds_dns_firewall_only() -> None:
    """The European Sovereign Cloud replacements comment the DNS Firewall rule groups out of network-config.yaml."""
    # arrange
    cats_config = _cats_variant(provides=[], workload_tagged=False)
    lza = _lza_variant(control_tower_enabled=True, identity_center_declared=True, dns_firewall_declared=False)

    # act
    provided = provided_requirements(cats_config, lza)

    # assert
    assert provided == {Requirement.STANDARD_DEPLOYMENT, Requirement.CONTROL_TOWER, Requirement.IDENTITY_CENTER}


def test_provided_values_are_the_strings_cats_requires_matches() -> None:
    """The engine compares provided names to the strings in @cats_requires; the enum values are those strings."""
    assert {str(requirement) for requirement in Requirement} == {
        "standard-deployment",
        "container-deployment",
        "workload-accounts",
        "control-tower",
        "identity-center",
        "dns-firewall",
    }

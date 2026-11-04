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

"""Tests for LzaConfig to verify Pydantic models match raw YAML values."""

from __future__ import annotations

import copy
import json
import re
from typing import TYPE_CHECKING, Any, cast

import pytest
import yaml
from cats.config import Settings
from cats.exceptions import CatsConfigError

from lza_types import AccountsConfig, ReplacementsConfig
from lza_utils.config_source import lza_config_dir
from lza_utils.lza_config import (
    _build_replacement_dict,
    _load_yaml,
    _make_include_loader,
    _map_lza_names_to_keys,
    _require_every_account_in_an_ou,
    get_shared_transit_gateway_account_region_combinations,
    get_vpc_names_for_account_region,
    get_vpcs_for_account,
    lza_config,
    resolve_policy_placeholders,
)

if TYPE_CHECKING:
    from pathlib import Path


def _load_config_with_replacements(filename: str) -> dict[str, Any]:
    """Load an lza-config YAML file with {{ }} replacements applied, as lza_config() does.

    The config files use LZA's replacement syntax (e.g. `enabledRegions: [ {{ EnabledRegions }} ]`),
    which is not valid YAML until replacements from replacements-config.yaml are substituted.
    """
    config_dir = lza_config_dir()
    raw_replacements = yaml.safe_load((config_dir / "replacements-config.yaml").read_text())
    subs = _build_replacement_dict(ReplacementsConfig.model_validate(raw_replacements))
    return cast("dict[str, Any]", _load_yaml(config_dir / filename, subs))


def test_replacements_match_raw_yaml() -> None:
    """Verify replacement dict values match raw YAML exactly (no Pydantic repr leakage)."""
    # arrange
    config_dir = lza_config_dir()
    raw_yaml = yaml.safe_load((config_dir / "replacements-config.yaml").read_text())
    replacements_config = ReplacementsConfig.model_validate(raw_yaml)

    # act
    result = _build_replacement_dict(replacements_config)

    # assert - check key values don't contain Pydantic repr artifacts
    for key, value in result.items():
        assert "root=" not in value, f"Replacement '{key}' has Pydantic repr leak: {value}"
        assert "NonEmptyString" not in value, f"Replacement '{key}' has type leak: {value}"

    # Verify specific critical values
    assert result["AcceleratorPrefix"] == "AWSAccelerator", f"Got: {result['AcceleratorPrefix']}"
    assert result["HomeRegion"] == "us-east-1", f"Got: {result['HomeRegion']}"


def test_accelerator_prefix_is_plain_string() -> None:
    """Verify accelerator_prefix returns plain string, not Pydantic model repr."""
    # act
    cfg = lza_config()

    # assert
    prefix = cfg.accelerator_prefix
    assert prefix == "AWSAccelerator", f"Expected 'AWSAccelerator', got '{prefix}'"
    assert "root=" not in prefix, f"Pydantic repr leak in prefix: {prefix}"


@pytest.mark.parametrize(
    ("accelerator_prefix", "expected_bucket_prefix", "expected_sns_prefix", "expected_log_group_prefix", "expected_ssm_prefix"),
    [
        ("AWSAccelerator", "aws-accelerator", "aws-accelerator", "aws-accelerator", "/accelerator"),
        ("CustomPrefix", "customprefix", "CustomPrefix", "CustomPrefix", "/CustomPrefix"),
        ("my-org", "my-org", "my-org", "my-org", "/my-org"),
    ],
)
def test_resource_name_prefixes_mirror_lza_set_resource_prefixes(
    accelerator_prefix: str,
    expected_bucket_prefix: str,
    expected_sns_prefix: str,
    expected_log_group_prefix: str,
    expected_ssm_prefix: str,
) -> None:
    """Verify the per-resource prefixes follow LZA's setResourcePrefixes() for the default and a custom AcceleratorPrefix.

    LZA special-cases ``AWSAccelerator`` and otherwise lower-cases the prefix for bucket names
    while leaving it unchanged for SNS topic and log group names.
    """
    # arrange
    cfg = copy.copy(lza_config())
    cfg.replacements = {**cfg.replacements, "AcceleratorPrefix": accelerator_prefix}

    # act / assert
    assert (cfg.bucket_name_prefix, cfg.sns_topic_name_prefix, cfg.log_group_name_prefix, cfg.ssm_parameter_prefix) == (
        expected_bucket_prefix,
        expected_sns_prefix,
        expected_log_group_prefix,
        expected_ssm_prefix,
    )


def test_enabled_regions_are_plain_strings() -> None:
    """Verify enabled_regions returns list of plain strings."""
    # act
    cfg = lza_config()
    regions = cfg.enabled_regions

    # assert
    assert isinstance(regions, list)
    for region in regions:
        assert isinstance(region, str), f"Region is not str: {type(region)}"
        assert "root=" not in region, f"Pydantic repr leak in region: {region}"
        assert "NonEmptyString" not in region, f"Type leak in region: {region}"


def test_home_region_is_plain_string() -> None:
    """Verify home_region returns plain string."""
    # act
    cfg = lza_config()

    # assert
    home = cfg.home_region
    assert home == "us-east-1", f"Expected 'us-east-1', got '{home}'"
    assert "root=" not in home, f"Pydantic repr leak in home_region: {home}"


def test_accounts_config_matches_yaml() -> None:
    """Verify accounts config values match the YAML (with replacements applied)."""
    # arrange
    raw_yaml = _load_config_with_replacements("accounts-config.yaml")
    cfg = lza_config()

    # assert - mandatory accounts match
    raw_mandatory = {a["name"]: a for a in raw_yaml["mandatoryAccounts"]}
    for account in cfg.accounts.mandatory_accounts:
        raw_account = raw_mandatory[account.name]
        assert account.email == raw_account["email"], f"Email mismatch for {account.name}"
        assert account.organizational_unit == raw_account["organizationalUnit"], f"OU mismatch for {account.name}"


def test_global_config_matches_yaml() -> None:
    """Verify global config values match the YAML (with replacements applied)."""
    # arrange
    raw_yaml = _load_config_with_replacements("global-config.yaml")
    cfg = lza_config()

    # assert
    assert cfg.global_.home_region == raw_yaml["homeRegion"], "homeRegion mismatch"
    assert cfg.global_.enabled_regions == raw_yaml["enabledRegions"], "enabledRegions mismatch"
    assert int(cfg.global_.cloudwatch_log_retention_in_days) == raw_yaml["cloudwatchLogRetentionInDays"], "log retention mismatch"


def test_security_config_matches_yaml() -> None:
    """Verify security config values match the YAML (with replacements applied)."""
    # arrange
    raw_yaml = _load_config_with_replacements("security-config.yaml")
    cfg = lza_config()

    # assert - check a few key nested values
    raw_ssm = raw_yaml["centralSecurityServices"]["ssmAutomation"]
    cfg_ssm = cfg.security.central_security_services.ssm_automation

    assert len(cfg_ssm.document_sets) == len(raw_ssm["documentSets"]), "documentSets count mismatch"

    # Check first document set name survives Pydantic validation unchanged
    expected_name = raw_ssm["documentSets"][0]["documents"][0]["name"]
    assert cfg_ssm.document_sets[0].documents[0].name == expected_name, (
        f"document name mismatch: {cfg_ssm.document_sets[0].documents[0].name} != {expected_name}"
    )


def test_iam_policy_names_are_plain_strings() -> None:
    """Verify IAM policy names are plain strings, not Pydantic wrapper types.

    This catches the NonEmptyString bug where list[NonEmptyString] items
    don't compare equal to plain strings.
    """
    # arrange
    cfg = lza_config()
    roles = {r.name: r for r in cfg.iam_roles}

    # act - get a role with policies
    role = roles.get("EC2-Default-SSM-Role")
    assert role is not None, "EC2-Default-SSM-Role not found in config"
    assert role.policies is not None, "EC2-Default-SSM-Role has no policies"
    assert role.policies.aws_managed, "EC2-Default-SSM-Role has no aws_managed policies"

    # assert - each policy name is a plain str, not a wrapper
    for policy in role.policies.aws_managed:
        assert type(policy) is str, f"Policy is {type(policy).__name__}, not str"
        # This would fail with NonEmptyString because NonEmptyString("x") != "x"
        assert policy == policy, "Self-equality check"
        assert policy in ["AmazonSSMManagedInstanceCore", "CloudWatchAgentServerPolicy"], f"Unexpected policy: {policy}"


def test_include_rejects_path_traversal(tmp_path: Path) -> None:
    """Verify !include rejects paths that escape the config directory."""
    # arrange - create a YAML file that tries to escape via ../
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    secret = tmp_path / "secret.yaml"
    secret.write_text("stolen: true")

    malicious_yaml = "data: !include ../secret.yaml\n"
    (config_dir / "evil.yaml").write_text(malicious_yaml)

    loader_cls = _make_include_loader(config_dir, {})

    # act & assert
    with pytest.raises(ValueError, match="escapes config directory"):
        yaml.load(malicious_yaml, Loader=loader_cls)  # noqa: S506


def test_available_fixtures_filters_unknown_accounts() -> None:
    """Verify account_fixture_names_in_ous excludes accounts not in CATS config.

    The fixture LZA config places Sandbox00001 in Workloads/Sandbox; no CATS config names it.
    Which other workload accounts resolve depends on the CATS config under test (the shipped
    template names none of the fixture's), so the positive assertion is that every fixture
    returned belongs to an account the CATS config declares, not a list of names.
    """
    # arrange
    cfg = lza_config()
    all_lza_workload_accounts = [a.name for a in cfg.accounts_in_ous(["Workloads"], inherit=True)]

    # act
    fixture_names = cfg.account_fixture_names_in_ous(["Workloads"], inherit=True)

    # assert
    assert "Sandbox00001" in all_lza_workload_accounts, "Test precondition: Sandbox00001 should be in LZA accounts config"
    assert "Sandbox00001_account" not in fixture_names, "Sandbox00001_account should be filtered out — not in CATS config"
    assert [name for name in fixture_names if name not in cfg._available_fixtures] == []


def test_resolve_policy_file_substitutes_every_lza_variable() -> None:
    """Verify resolve_policy_file knows every ${VARIABLE} used across the configured SCPs and RCPs.

    LZA substitutes ${Variable} placeholders at deploy time. If a policy file uses
    one our helper does not map, the live statement-match tests fail with a confusing
    diff; catch it here instead. IAM's own ${aws:...} policy variables contain a colon
    and are deliberately not matched; LZA's ${ACCEL_LOOKUP::...} lookups are. The RCP
    documents use the two placeholders only the live deployment can supply; the values
    passed here stand in for what tests/test_rcp.py reads from the Organization.
    """
    # arrange
    cfg = lza_config()
    lza_placeholder = re.compile(r"\$\{(?:[A-Za-z][A-Za-z0-9_]*|ACCEL_LOOKUP::[^}]*)\}")
    deployment_values = {"${ORG_ID}": "o-exampleorgid", "${LOGARCHIVE_ACCOUNT_ID}": "222222222222"}
    policy_paths = {
        **{policy.name: policy.policy for policy in cfg.organization.service_control_policies},
        **{policy.name: policy.policy for policy in cfg.organization.resource_control_policies or []},
    }

    # act
    unresolved = {
        name: sorted(set(lza_placeholder.findall(json.dumps(cfg.resolve_policy_file(path, deployment_values)))))
        for name, path in policy_paths.items()
    }
    unresolved = {name: placeholders for name, placeholders in unresolved.items() if placeholders}

    # assert
    assert unresolved == {}, f"resolve_policy_file left LZA placeholders unresolved: {unresolved}"


def test_stage_resource_prefixes_are_the_accelerator_prefix_per_stage_stem() -> None:
    """Verify the probe-target prefixes every guardrail SCP denies on, for the configured prefix."""
    # arrange
    prefix = lza_config().accelerator_prefix
    expected = (f"{prefix}-Sec", f"{prefix}-Log", f"{prefix}-Net", f"{prefix}-Op")

    # act
    actual = lza_config().stage_resource_prefixes

    # assert
    assert actual == expected


def test_resolve_policy_placeholders_resolves_custom_lookup_from_replacements() -> None:
    """Verify ${ACCEL_LOOKUP::CUSTOM:<Key>} resolves to the globalReplacements value of <Key>."""
    # arrange
    content = '{"Tag": "${ACCEL_LOOKUP::CUSTOM:AcceleratorQualifier}", "Role": "${ACCELERATOR_PREFIX}*"}'
    expected = '{"Tag": "lza1", "Role": "AWSAccelerator*"}'

    # act
    resolved = resolve_policy_placeholders(content, {"${ACCELERATOR_PREFIX}": "AWSAccelerator"}, {"AcceleratorQualifier": "lza1"})

    # assert
    assert resolved == expected


def test_resolve_policy_placeholders_leaves_unknown_lookup_in_place() -> None:
    """Verify a lookup of a key absent from globalReplacements survives, so a comparison against it fails visibly."""
    # arrange
    content = '{"Tag": "${ACCEL_LOOKUP::CUSTOM:AcceleratorQualifier}"}'

    # act
    resolved = resolve_policy_placeholders(content, {}, {"AcceleratorPrefix": "AWSAccelerator"})

    # assert
    assert resolved == content


def test_account_fixture_names_from_targets_honours_excluded_accounts() -> None:
    """Verify excludedAccounts carve accounts back out of an OU target."""
    # arrange
    cfg = lza_config()
    without_exclusion = cfg.account_fixture_names_from_targets(["Security"], [])

    # act
    with_exclusion = cfg.account_fixture_names_from_targets(["Security"], [], ["Audit"])

    # assert
    assert "Audit_account" in without_exclusion
    assert with_exclusion == [name for name in without_exclusion if name != "Audit_account"]


def test_get_vpcs_for_account_follows_the_cats_fixture_map(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify VPC lookup by fixture name goes through cats.yaml's account_name map, not a '_account' suffix strip."""
    # arrange
    cfg = lza_config()
    perimeter_vpc_names = sorted(vpc.name for vpc in cfg.network.vpcs or [] if vpc.account == "Perimeter")
    assert perimeter_vpc_names, "Test precondition: network config declares Perimeter VPCs"
    monkeypatch.setattr(cfg, "lza_to_fixture_map", {**cfg.lza_to_fixture_map, "Perimeter": "Edge"})

    # act
    by_customer_key = sorted(vpc.name for vpc in get_vpcs_for_account("Edge_account"))
    by_lza_name = get_vpcs_for_account("Perimeter_account")

    # assert
    assert by_customer_key == perimeter_vpc_names
    assert by_lza_name == []


def test_get_vpc_names_for_account_region_follows_the_cats_fixture_map(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify the VPC-name lookup resolves the fixture name the same way as get_vpcs_for_account."""
    # arrange
    cfg = lza_config()
    expected = sorted(vpc.name for vpc in cfg.network.vpcs or [] if vpc.account == "Perimeter" and (vpc.region or cfg.home_region) == cfg.home_region)
    assert expected, "Test precondition: network config declares Perimeter VPCs in the home region"
    monkeypatch.setattr(cfg, "lza_to_fixture_map", {**cfg.lza_to_fixture_map, "Perimeter": "Edge"})

    # act
    actual = sorted(get_vpc_names_for_account_region("Edge_account", cfg.home_region))

    # assert
    assert actual == expected


def test_delegated_admin_account_is_the_security_config_value_as_a_fixture_name() -> None:
    """Verify delegated_admin_account resolves centralSecurityServices.delegatedAdminAccount to a fixture name."""
    # arrange
    raw_yaml = _load_config_with_replacements("security-config.yaml")
    expected = f"{raw_yaml['centralSecurityServices']['delegatedAdminAccount']}_account"

    # act
    actual = lza_config().delegated_admin_account()

    # assert
    assert actual == expected == "Audit_account"


def test_delegated_admin_account_follows_the_cats_fixture_map(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify a customer keying the Audit account differently in cats.yaml still resolves."""
    # arrange
    cfg = lza_config()
    monkeypatch.setattr(cfg, "lza_to_fixture_map", {**cfg.lza_to_fixture_map, "Audit": "Security"})
    monkeypatch.setattr(cfg, "_available_fixtures", (cfg._available_fixtures - {"Audit_account"}) | {"Security_account"})

    # act
    actual = cfg.delegated_admin_account()

    # assert
    assert actual == "Security_account"


def test_delegated_admin_account_rejects_an_account_not_under_test(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify the lookup fails loudly rather than return a fixture the pack cannot resolve."""
    # arrange
    cfg = lza_config()
    monkeypatch.setattr(cfg, "_available_fixtures", cfg._available_fixtures - {"Audit_account"})

    # act / assert
    with pytest.raises(AssertionError, match="delegatedAdminAccount 'Audit' is not in accounts_under_test"):
        cfg.delegated_admin_account()


def test_shared_transit_gateway_combinations_are_the_owners_of_transit_gateways_with_share_targets() -> None:
    """Verify the RAM-share owner set is derived from shareTargets in network-config.yaml."""
    # arrange
    cfg = lza_config()
    expected = sorted({(f"{tgw.account}_account", tgw.region) for tgw in cfg.network.transit_gateways if tgw.share_targets})
    assert expected, "Test precondition: network config declares a Transit Gateway with shareTargets"

    # act
    actual = get_shared_transit_gateway_account_region_combinations()

    # assert
    assert actual == expected == [("Network_account", region) for region in sorted(cfg.enabled_regions)]


def test_scp_revert_changes_config_matches_yaml() -> None:
    """Verify scp_revert_changes_config returns the declared block, with snsTopicName optional."""
    # arrange
    raw_yaml = _load_config_with_replacements("security-config.yaml")
    raw_revert = raw_yaml["centralSecurityServices"]["scpRevertChangesConfig"]

    # act
    revert_config = lza_config().scp_revert_changes_config

    # assert
    expected = {"enable": raw_revert["enable"], "sns_topic_name": raw_revert.get("snsTopicName")}
    actual = {"enable": revert_config.enable, "sns_topic_name": revert_config.sns_topic_name}
    assert actual == expected


def test_global_region_is_us_east_1_for_the_aws_partition() -> None:
    """Verify global_region follows LZA's getGlobalRegion() for the configured partition."""
    # arrange
    partition = Settings().cats_deployment_settings.partition
    assert partition == "aws", f"Test precondition: dev config partition should be 'aws', got {partition!r}"

    # act
    global_region = lza_config().global_region

    # assert
    assert global_region == "us-east-1"


def test_every_account_in_an_ou_accepts_the_fixture_config() -> None:
    """The shipped fixture places every account in an OU, so the load-time check passes."""
    # act / assert
    _require_every_account_in_an_ou(lza_config().accounts)


def test_every_account_in_an_ou_rejects_an_unplaced_account() -> None:
    """An account without organizationalUnit fails config load by name instead of vanishing from every OU-targeted test."""
    # arrange
    raw = _load_config_with_replacements("accounts-config.yaml")
    raw["workloadAccounts"] = [{"name": "Orphan", "description": "No OU", "email": "orphan@example.com"}]
    accounts = AccountsConfig.model_validate(raw)

    # act / assert
    with pytest.raises(CatsConfigError, match=r"every account must declare organizationalUnit; missing on \['Orphan'\]"):
        _require_every_account_in_an_ou(accounts)


_LZA_NAMES = ["Management", "Audit", "LogArchive", "my-team.prod"]


def test_entry_key_is_the_lza_account_name_unless_account_name_overrides() -> None:
    """The key maps to itself; account_name maps an LZA name a key cannot spell."""
    accounts_under_test = {"Management": {"account_id": "111111111111"}, "TeamProd": {"account_name": "my-team.prod", "account_id": "222222222222"}}

    mapping = _map_lza_names_to_keys(accounts_under_test, _LZA_NAMES)

    assert mapping == {"Management": "Management", "my-team.prod": "TeamProd"}


def test_entry_naming_no_lza_account_fails_config_load() -> None:
    """A key or account_name that matches nothing is refused by entry instead of vanishing from every OU-resolved test."""
    accounts_under_test = {"Management": {"account_id": "111111111111"}, "Prod": {"account_name": "Prod0001", "account_id": "222222222222"}}

    expected = (
        r"entries name no account in accounts-config.yaml: \['Prod -> Prod0001'\]; it names \['Audit', 'LogArchive', 'Management', 'my-team.prod'\]"
    )
    with pytest.raises(CatsConfigError, match=expected):
        _map_lza_names_to_keys(accounts_under_test, _LZA_NAMES)


def test_regions_come_from_global_config_not_the_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """HOME_REGION and ENABLED_REGIONS in the environment do not override the deployed global-config.yaml."""
    # arrange
    cfg = lza_config()
    expected_home_region = cfg.global_.home_region
    expected_enabled_regions = cfg.global_.enabled_regions
    monkeypatch.setenv("HOME_REGION", "mars-north-1")
    monkeypatch.setenv("ENABLED_REGIONS", "mars-north-1,mars-south-1")

    # act / assert
    assert cfg.home_region == expected_home_region
    assert cfg.enabled_regions == expected_enabled_regions
    assert _build_replacement_dict(ReplacementsConfig.model_validate({"globalReplacements": []})) == {}

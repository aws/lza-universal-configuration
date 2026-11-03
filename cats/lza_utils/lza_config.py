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

"""Typed LZA configuration loading using generated Pydantic models."""

from __future__ import annotations

import json
import re
from functools import cache
from typing import TYPE_CHECKING, Any, TypedDict

import yaml
from cats.config import Settings
from cats.exceptions import CatsConfigError
from cats.filepath import get_cats_config_filepath

from lza_types import (
    AccountsConfig,
    GlobalConfig,
    IamConfig,
    NetworkConfig,
    OrganizationConfig,
    ReplacementsConfig,
    SecurityConfig,
)
from lza_types.network_config import DnsFirewallRuleActionType
from lza_types.replacements_config import ParameterReplacementV2
from lza_utils.config_source import lza_config_dir

if TYPE_CHECKING:
    from pathlib import Path

    from lza_types.iam_config import RoleConfig
    from lza_types.network_config import DnsFirewallManagedDomainListsType, TransitGatewayConfig, VpcConfig, VpcFlowLogsConfig
    from lza_types.security_config import AwsConfigRuleSet, BlockPublicDocumentSharingConfig, ConfigRule, ScpRevertChangesConfig

# The OU the Universal Configuration's container variant dedicates to the account hosting the
# LZA InstallerContainerStack. The account's name varies between configurations; the OU does not.
CONTAINER_DEPLOYMENT_OU = "LzaDeployment"

# Name stems of the LZA pipeline-stage stacks (SecurityStack, LoggingStack, NetworkVpcStack,
# OperationsStack, ...) and of the roles, functions and log groups those stacks create. The core
# guardrails deny on ``<prefix>*``; the LzaDeployment-Guardrails SCPs deny on ``<prefix>-<stem>*``
# only, so the InstallerContainerStack's own resources stay manageable in the deployment account.
# A probe target under one of these stems is inside both scopes.
LZA_STAGE_STEMS = ("Sec", "Log", "Net", "Op")


class VpcInfo(TypedDict):
    fixture_name: str
    region: str
    vpc_name: str


class IpamPoolShare(TypedDict):
    pool_name: str
    fixture_names: list[str]


def _extract_replacement_value(val: str | list[str] | float) -> str:
    """Extract plain string from replacement value types."""
    if isinstance(val, list):
        return ", ".join(f'"{v}"' for v in val)
    if isinstance(val, str):
        return val
    return str(val)


def _build_replacement_dict(replacements: ReplacementsConfig) -> dict[str, str]:
    """Build replacement dict from validated Pydantic config."""
    result: dict[str, str] = {}
    for r in replacements.global_replacements or []:
        if isinstance(r, ParameterReplacementV2) and r.value is not None:
            result[r.key] = _extract_replacement_value(r.value)
    return result


def _apply_replacements(content: str, subs: dict[str, str]) -> str:
    for key, val in subs.items():
        content = content.replace(f"{{{{ {key} }}}}", val)
    return content


def _make_include_loader(base_path: Path, subs: dict[str, str]) -> type[yaml.SafeLoader]:
    """Create a YAML SafeLoader subclass that resolves !include tags relative to base_path."""

    class IncludeLoader(yaml.SafeLoader):
        pass

    def include_constructor(loader: IncludeLoader, node: yaml.ScalarNode) -> object:
        include_path = (base_path / str(loader.construct_scalar(node))).resolve()
        if not include_path.is_relative_to(base_path.resolve()):
            msg = f"!include path escapes config directory: {loader.construct_scalar(node)}"
            raise ValueError(msg)
        include_content = _apply_replacements(include_path.read_text(), subs)
        # Use IncludeLoader recursively so nested !include tags are resolved
        return yaml.load(include_content, Loader=IncludeLoader)  # noqa: S506

    IncludeLoader.add_constructor("!include", include_constructor)
    return IncludeLoader


def _load_yaml(path: Path, subs: dict[str, str]) -> dict[str, object]:
    content = _apply_replacements(path.read_text(), subs)
    loader_cls = _make_include_loader(path.parent, subs)
    result = yaml.load(content, Loader=loader_cls)  # noqa: S506 - SafeLoader subclass, not arbitrary Loader
    return dict(result)


# LZA's getGlobalRegion() (source/packages/@aws-accelerator/utils/lib/common-functions.ts).
# Partitions not listed here fall back to us-east-1.
_GLOBAL_REGION_BY_PARTITION = {
    "aws-us-gov": "us-gov-west-1",
    "aws-iso": "us-iso-east-1",
    "aws-iso-b": "us-isob-east-1",
    "aws-iso-e": "eu-isoe-west-1",
    "aws-iso-f": "us-isof-south-1",
    "aws-cn": "cn-northwest-1",
    "aws-eusc": "eusc-de-east-1",
}


class LzaConfig:
    def __init__(
        self,
        accounts: AccountsConfig,
        global_: GlobalConfig,
        organization: OrganizationConfig,
        security: SecurityConfig,
        iam: IamConfig,
        network: NetworkConfig,
        replacements: dict[str, str] | None = None,
    ) -> None:
        self.accounts = accounts
        self.global_ = global_
        self.organization = organization
        self.security = security
        self.iam = iam
        self.network = network
        self.replacements = replacements or {}

        # Which cats.yaml entry is which LZA account: the entry's key is the account's name in
        # accounts-config.yaml (or its account_name, if set). An entry that names no account
        # is an error, because the tests would silently run without that account.
        cats_config_path = get_cats_config_filepath()
        cats_raw = yaml.safe_load(cats_config_path.read_text())
        accounts_under_test: dict[str, Any] = cats_raw.get("accounts_under_test", {})
        self.lza_to_fixture_map = _map_lza_names_to_keys(accounts_under_test, [a.name for a in self.all_accounts])
        # Set of fixture names that actually exist in CATS config — used to filter
        # parameterization so tests don't generate fixtures for accounts CATS can't reach.
        self._available_fixtures: set[str] = {f"{key}_account" for key in accounts_under_test}

    def _to_fixture_name(self, lza_account_name: str) -> str:
        """Convert LZA account name to CATS fixture name."""
        fixture_key = self.lza_to_fixture_map.get(lza_account_name, lza_account_name)
        return f"{fixture_key}_account"

    @property
    def accelerator_prefix(self) -> str:
        return self.replacements.get("AcceleratorPrefix", "AWSAccelerator")

    @property
    def stage_resource_prefixes(self) -> tuple[str, ...]:
        """``<prefix>-<stem>`` for every LZA_STAGE_STEMS entry: the resource-name prefixes every guardrail SCP denies on."""
        return tuple(f"{self.accelerator_prefix}-{stem}" for stem in LZA_STAGE_STEMS)

    @property
    def ssm_parameter_prefix(self) -> str:
        """SSM parameter path prefix LZA uses for its own parameters.

        Mirrors LZA's setResourcePrefixes(): '/accelerator' for the default prefix,
        otherwise '/<AcceleratorPrefix>'.
        """
        return "/accelerator" if self.accelerator_prefix == "AWSAccelerator" else f"/{self.accelerator_prefix}"

    def resolve_policy_file(self, policy_path: str) -> dict[str, Any]:
        """Load a policy JSON document with LZA ${VARIABLE} placeholders resolved.

        Mirrors the substitution LZA's generatePolicyReplacements() applies at deploy
        time, so a resolved document compares equal to deployed policy content. Only
        deployment-wide values are resolved; per-stack ones (${ACCOUNT_ID}, ${REGION},
        ${ACCOUNT_NAME}, ${ORG_ID}) are not available from the config files. A
        ``${ACCEL_LOOKUP::CUSTOM:<Key>}`` lookup resolves to the globalReplacements value
        of ``<Key>``. An unmapped placeholder survives into the result and fails that
        comparison loudly.
        """
        accelerator_prefix_no_dash = self.accelerator_prefix.removesuffix("-")
        substitutions = {
            "${PARTITION}": Settings().cats_deployment_settings.partition,
            "${ACCELERATOR_PREFIX}": self.accelerator_prefix,
            "${ACCELERATOR_PREFIX_ND}": accelerator_prefix_no_dash,
            "${ACCELERATOR_PREFIX_LND}": accelerator_prefix_no_dash.lower(),
            "${ACCELERATOR_SSM_PREFIX}": self.ssm_parameter_prefix,
            "${HOME_REGION}": self.home_region,
            "${MANAGEMENT_ACCOUNT_ACCESS_ROLE}": self.global_.management_account_access_role,
            # globalReplacements keys are also valid as ${Key} inside policy files
            **{f"${{{key}}}": value for key, value in self.replacements.items()},
        }
        document: dict[str, Any] = json.loads(resolve_policy_placeholders(_policy_file_text(policy_path), substitutions, self.replacements))
        return document

    @property
    def resource_prefix(self) -> str:
        """Kebab-case prefix used in deployed resource names (e.g. 'aws-accelerator')."""
        parts = re.findall(r"[A-Z]+(?=[A-Z][a-z])|[A-Z][a-z]*|[a-z]+", self.accelerator_prefix)
        return "-".join(parts).lower()

    def central_logs_bucket_name(self, log_archive_account_id: str) -> str:
        """Name of the central logs bucket in the LogArchive account.

        Mirrors LZA's ``centralLogsBucketName``: an imported bucket's name when
        ``logging.centralLogBucket.importedBucket`` is set, else the LZA-created bucket in
        the centralized logging region (the home region unless ``centralizedLoggingRegion``
        names another).
        """
        central_log_bucket = self.global_.logging.central_log_bucket
        if central_log_bucket is not None and central_log_bucket.imported_bucket is not None:
            return central_log_bucket.imported_bucket.name
        region = self.global_.logging.centralized_logging_region or self.home_region
        return f"{self.resource_prefix}-central-logs-{log_archive_account_id}-{region}"

    def guardduty_findings_destination_arn(self, log_archive_account_id: str) -> str:
        """S3 ARN GuardDuty publishes findings to, as LZA's SecurityStack builds it.

        ``arn:<partition>:s3:::<central logs bucket>/<prefix>`` with ``guardduty`` as the
        prefix unless ``exportConfiguration.overrideGuardDutyPrefix.useCustomPrefix`` sets one.
        """
        export = self.security.central_security_services.guardduty.export_configuration
        prefix = "guardduty"
        if export.override_guard_duty_prefix is not None and export.override_guard_duty_prefix.use_custom_prefix:
            prefix = export.override_guard_duty_prefix.custom_override or ""
        partition = Settings().cats_deployment_settings.partition
        return f"arn:{partition}:s3:::{self.central_logs_bucket_name(log_archive_account_id)}/{prefix}"

    def elb_access_logs_bucket_name(self, log_archive_account_id: str, region: str) -> str:
        """Name of the ELB access logs bucket LZA uses in ``region``.

        Mirrors ``getElbLogsBucketName`` in LZA's accelerator-stack.ts: an imported bucket's
        name when ``logging.elbLogBucket.importedBucket`` is set, else the LZA-created bucket
        in the LogArchive account.
        """
        elb_log_bucket = self.global_.logging.elb_log_bucket
        if elb_log_bucket is not None and elb_log_bucket.imported_bucket is not None:
            return elb_log_bucket.imported_bucket.name
        return f"{self.resource_prefix}-elb-access-logs-{log_archive_account_id}-{region}"

    @property
    def config_rule_sets(self) -> list[AwsConfigRuleSet]:
        return list(self.security.aws_config.rule_sets or [])

    def config_rule(self, rule_name: str) -> ConfigRule:
        """The Config rule named ``rule_name`` (with ``{{ AcceleratorPrefix }}`` resolved) in security-config.yaml."""
        matches = [rule for rule_set in self.config_rule_sets for rule in rule_set.rules if rule.name == rule_name]
        assert len(matches) == 1, f"Expected exactly one Config rule named '{rule_name}' in security-config.yaml, found {len(matches)}"
        return matches[0]

    @property
    def remediated_config_rule_names(self) -> list[str]:
        """Names of every Config rule in security-config.yaml that declares a remediation block."""
        return sorted(rule.name for rule_set in self.config_rule_sets for rule in rule_set.rules if rule.remediation is not None)

    @property
    def enabled_regions(self) -> list[str]:
        return self.global_.enabled_regions

    @property
    def home_region(self) -> str:
        return self.global_.home_region

    @property
    def log_retention_days(self) -> int:
        return int(self.global_.cloudwatch_log_retention_in_days)

    @property
    def control_tower_enabled(self) -> bool:
        """``controlTower.enable`` in global-config.yaml: whether AWS Control Tower governs the organization.

        False is the Organizations-only variant of the Universal Configuration: no landing zone,
        no enabled controls, no ``AWSControlTower-*`` Config rules in the member accounts.
        """
        return self.global_.control_tower.enable

    @property
    def identity_center_declared(self) -> bool:
        """Whether iam-config.yaml declares an ``identityCenter`` block.

        LZA manages an IAM Identity Center instance and its delegated administrator only when it
        does; the Organizations-only variant omits the block.
        """
        return self.iam.identity_center is not None

    @property
    def dns_firewall_blocked_managed_lists(self) -> list[DnsFirewallManagedDomainListsType]:
        """The Route 53 Resolver DNS Firewall managed domain lists network-config.yaml BLOCKs, sorted.

        Empty on a deployment with no ``centralNetworkServices.route53Resolver.firewallRuleGroups``:
        the European Sovereign Cloud package comments the rule groups out because managed domain
        lists do not exist in that partition.
        """
        central = self.network.central_network_services
        if central is None or central.route53_resolver is None:
            return []
        return sorted(
            {
                rule.managed_domain_list
                for group in central.route53_resolver.firewall_rule_groups or []
                for rule in group.rules
                if rule.action == DnsFirewallRuleActionType.block and rule.managed_domain_list is not None
            }
        )

    @property
    def dns_firewall_declared(self) -> bool:
        """Whether the DNS Firewall BLOCKs at least one managed domain list."""
        return bool(self.dns_firewall_blocked_managed_lists)

    @property
    def all_accounts(self) -> list[Any]:
        """All accounts (mandatory + workload)."""
        return list(self.accounts.mandatory_accounts) + list(self.accounts.workload_accounts)

    def delegated_admin_account(self) -> str:
        """Fixture name of ``centralSecurityServices.delegatedAdminAccount`` in security-config.yaml.

        The account LZA registers as delegated administrator for GuardDuty, Macie, Security Hub
        and the SSM automation documents (``Audit`` in the Universal Configuration). Resolved
        through the cats.yaml ``account_name`` map, so the fixture key need not equal the LZA
        account name. Fails loudly when the account is not under test.
        """
        fixture_name = self._to_fixture_name(self.security.central_security_services.delegated_admin_account)
        assert fixture_name in self._available_fixtures, (
            f"delegatedAdminAccount '{self.security.central_security_services.delegated_admin_account}' is not in accounts_under_test"
        )
        return fixture_name

    def _ou_matches(self, account_ou: str, target_ous: list[str], inherit: bool) -> bool:
        if "Root" in target_ous:
            return True
        if account_ou in target_ous:
            return True
        if inherit:
            return any(account_ou.startswith(f"{ou}/") for ou in target_ous)
        return False

    def accounts_in_ous(self, target_ous: list[str], inherit: bool = False) -> list[Any]:
        """Get accounts in specified OUs. If inherit=True, includes child OUs."""
        return [a for a in self.all_accounts if self._ou_matches(a.organizational_unit, target_ous, inherit)]

    def account_fixture_names_in_ous(self, target_ous: list[str], inherit: bool = False) -> list[str]:
        """Get pytest fixture names (e.g. 'Audit_account') for accounts in specified OUs.

        Only returns fixture names for accounts that exist in the CATS config.
        """
        return sorted(
            name for name in (self._to_fixture_name(a.name) for a in self.accounts_in_ous(target_ous, inherit)) if name in self._available_fixtures
        )

    def account_fixture_names_from_targets(
        self, target_ous: list[str], target_accounts: list[str], excluded_accounts: list[str] | None = None
    ) -> list[str]:
        """Convert LZA deployment targets to pytest fixture names.

        LZA deployment targets can specify accounts directly or via OUs, and carve accounts
        back out with ``excludedAccounts``. This resolves all three to fixture names
        (e.g. 'Audit_account'). Only returns fixture names for accounts that exist in the
        CATS config.
        """
        fixtures: set[str] = {self._to_fixture_name(acc) for acc in target_accounts}
        fixtures.update(self.account_fixture_names_in_ous(target_ous, inherit=True))
        fixtures.difference_update(self._to_fixture_name(acc) for acc in excluded_accounts or [])
        return sorted(fixtures & self._available_fixtures)

    @property
    def iam_roles(self) -> list[RoleConfig]:
        """All IAM roles flattened from role sets."""
        roles: list[RoleConfig] = []
        for role_set in self.iam.role_sets or []:
            roles.extend(role_set.roles)
        return roles

    @property
    def ssm_block_public_document_sharing(self) -> BlockPublicDocumentSharingConfig:
        """The ssmSettings.blockPublicDocumentSharing block from security config.

        Fails loudly when absent: the Universal Configuration declares it, and a
        missing block means the control is not configured rather than "no-op".
        """
        ssm_settings = self.security.central_security_services.ssm_settings
        assert ssm_settings is not None, "centralSecurityServices.ssmSettings is not declared in security-config.yaml"
        assert ssm_settings.block_public_document_sharing is not None, "ssmSettings.blockPublicDocumentSharing is not declared in security-config"
        return ssm_settings.block_public_document_sharing

    @property
    def scp_revert_changes_config(self) -> ScpRevertChangesConfig:
        """The centralSecurityServices.scpRevertChangesConfig block from security config.

        Fails loudly when absent: the Universal Configuration declares it, and a
        missing block means the control is not configured rather than "no-op".
        """
        revert_config = self.security.central_security_services.scp_revert_changes_config
        assert revert_config is not None, "centralSecurityServices.scpRevertChangesConfig is not declared in security-config.yaml"
        return revert_config

    @property
    def global_region(self) -> str:
        """The region LZA deploys partition-global resources to (the Finalize stack among them).

        Mirrors LZA's getGlobalRegion(): fixed per partition, independent of homeRegion.
        """
        return _GLOBAL_REGION_BY_PARTITION.get(Settings().cats_deployment_settings.partition, "us-east-1")

    @property
    def ssm_document_shares(self) -> list[dict[str, Any]]:
        """SSM document shares from security config."""
        shares: list[dict[str, Any]] = []
        ssm_automation = self.security.central_security_services.ssm_automation
        for doc_set in ssm_automation.document_sets:
            target_ous = doc_set.share_targets.organizational_units or []
            target_accounts = doc_set.share_targets.accounts or []
            for doc in doc_set.documents:
                shares.append(
                    {
                        "document_name": doc.name,
                        "template": doc.template,
                        "target_ous": target_ous,
                        "target_accounts": target_accounts,
                    }
                )
        return shares

    def declarative_policy_targets(self, policy_name: str) -> list[str]:
        """Get LZA configured account names, and use them to match CATS account fixture
        names for accounts targeted by a declarative policy.

        Args:
            policy_name: Policy name, may contain {{ AcceleratorPrefix }} placeholder

        Returns:
            Sorted list of fixture names (e.g. ['Audit_account', 'LogArchive_account'])
        """
        resolved_name = policy_name.replace("{{ AcceleratorPrefix }}", self.accelerator_prefix)
        for policy in self.organization.declarative_policies or []:
            if policy.name == resolved_name:
                targets = policy.deployment_targets
                return self.account_fixture_names_from_targets(
                    targets.organizational_units or [],
                    targets.accounts or [],
                )
        return []

    def rcp_policy_targets(self, policy_name: str) -> list[str]:
        """Get fixture names for accounts targeted by a resource control policy.

        Args:
            policy_name: Policy name, may contain {{ AcceleratorPrefix }} placeholder

        Returns:
            Sorted list of fixture names (e.g. ['Audit_account', 'Network_account'])
        """
        resolved_name = policy_name.replace("{{ AcceleratorPrefix }}", self.accelerator_prefix)
        for policy in self.organization.resource_control_policies or []:
            if policy.name == resolved_name:
                targets = policy.deployment_targets
                return self.account_fixture_names_from_targets(
                    targets.organizational_units or [],
                    targets.accounts or [],
                )
        return []

    def firewall_allowed_ports(self, port_set_name: str = "HOME_REGION_SS_PORTS") -> list[int]:
        """Get allowed ports from network firewall portSets configuration.

        Args:
            port_set_name: Name of the portSet to retrieve (default: HOME_REGION_SS_PORTS)

        Returns:
            List of allowed port numbers as integers
        """
        central = self.network.central_network_services
        if not central or not central.network_firewall:
            return []

        for rule in central.network_firewall.rules:
            if not rule.rule_group or not rule.rule_group.rule_variables:
                continue
            port_sets = rule.rule_group.rule_variables.port_sets
            if isinstance(port_sets, list):
                for ps in port_sets:
                    if ps.name == port_set_name:
                        return [int(p) for p in ps.definition]
            elif port_sets.name == port_set_name:
                return [int(p) for p in port_sets.definition]
        return []


def get_vpcs_for_account(account_fixture_name: str) -> list[VpcConfig]:
    """VPC config objects whose ``account`` maps to ``account_fixture_name`` through cats.yaml's ``account_name``."""
    config = lza_config()
    return [vpc for vpc in (config.network.vpcs or []) if config._to_fixture_name(vpc.account) == account_fixture_name]


def get_vpcs_for_account_region(account_fixture_name: str, region: str) -> list[VpcConfig]:
    """Get VPC config objects for an account and region."""
    config = lza_config()
    return [vpc for vpc in get_vpcs_for_account(account_fixture_name) if (vpc.region or config.home_region) == region]


def get_vpcs_with_transit_gateway_attachments(account_fixture_name: str, region: str) -> list[VpcConfig]:
    """Get VPCs with transit gateway attachments for an account/region."""
    return [vpc for vpc in get_vpcs_for_account_region(account_fixture_name, region) if vpc.transit_gateway_attachments]


def get_vpcs_with_gateway_endpoints(account_fixture_name: str, region: str) -> list[VpcConfig]:
    """Get VPCs with gateway endpoints for an account/region."""
    return [vpc for vpc in get_vpcs_for_account_region(account_fixture_name, region) if vpc.gateway_endpoints]


def get_vpcs_with_subnets(account_fixture_name: str, region: str) -> list[VpcConfig]:
    """Get VPCs with subnets for an account/region."""
    return [vpc for vpc in get_vpcs_for_account_region(account_fixture_name, region) if vpc.subnets]


def get_vpcs_with_nat_gateways(account_fixture_name: str, region: str) -> list[VpcConfig]:
    """Get VPCs with NAT gateways for an account/region."""
    return [vpc for vpc in get_vpcs_for_account_region(account_fixture_name, region) if vpc.nat_gateways]


def get_vpcs_with_internet_gateway(account_fixture_name: str, region: str) -> list[VpcConfig]:
    """Get VPCs with internet gateway for an account/region."""
    return [vpc for vpc in get_vpcs_for_account_region(account_fixture_name, region) if vpc.internet_gateway is True]


def _get_all_vpcs() -> list[VpcInfo]:
    """Get VpcInfo dicts for all VPCs in config."""
    config = lza_config()
    result: list[VpcInfo] = []
    for vpc in config.network.vpcs or []:
        fixture_name = config._to_fixture_name(vpc.account)
        region = vpc.region or config.home_region
        result.append(VpcInfo(fixture_name=fixture_name, region=region, vpc_name=vpc.name))
    return sorted(result, key=lambda v: (v["fixture_name"], v["region"], v["vpc_name"]))


def _has_flow_logs_enabled(vpc_flow_logs: VpcFlowLogsConfig | None, global_flow_logs: VpcFlowLogsConfig | None) -> bool:
    """Check if flow logs are enabled for a VPC (via VPC config or global config)."""
    return vpc_flow_logs is not None or global_flow_logs is not None


def get_vpcs_with_flow_logs() -> list[VpcInfo]:
    """Get VpcInfo dicts for VPCs with flow logs enabled."""
    config = lza_config()
    global_flow_logs = config.network.vpc_flow_logs
    result: list[VpcInfo] = []
    for vpc in config.network.vpcs or []:
        if _has_flow_logs_enabled(vpc.vpc_flow_logs, global_flow_logs) is True:
            fixture_name = config._to_fixture_name(vpc.account)
            region = vpc.region or config.home_region
            result.append(VpcInfo(fixture_name=fixture_name, region=region, vpc_name=vpc.name))
    return sorted(result, key=lambda v: (v["fixture_name"], v["region"], v["vpc_name"]))


def get_vpc_account_region_combinations() -> list[tuple[str, str]]:
    """Get unique (fixture_name, region) tuples for all VPCs in config."""
    unique_pairs = {(v["fixture_name"], v["region"]) for v in _get_all_vpcs()}
    return sorted(unique_pairs)


def get_vpc_account_region_combinations_with_flow_logs() -> list[tuple[str, str]]:
    """Get unique (fixture_name, region) tuples for VPCs with flow logs enabled."""
    unique_pairs = {(v["fixture_name"], v["region"]) for v in get_vpcs_with_flow_logs()}
    return sorted(unique_pairs)


def get_vpc_names_for_account_region(account_fixture_name: str, region: str) -> list[str]:
    """Get all VPC names from config for an account/region."""
    return [vpc.name for vpc in get_vpcs_for_account_region(account_fixture_name, region)]


def get_vpc_names_with_flow_logs_for_account_region(account_fixture_name: str, region: str) -> list[str]:
    """Get VPC names with flow logs enabled for an account/region."""
    return [v["vpc_name"] for v in get_vpcs_with_flow_logs() if v["fixture_name"] == account_fixture_name and v["region"] == region]


def get_network_firewall_account_region_combinations() -> list[tuple[str, str]]:
    """Get unique (fixture_name, region) tuples for Network Firewalls in config."""
    config = lza_config()
    central = config.network.central_network_services
    if not central:
        return []
    if not central.network_firewall:
        return []
    if not central.network_firewall.firewalls:
        return []

    combinations: set[tuple[str, str]] = set()
    vpc_map = {vpc.name: vpc for vpc in config.network.vpcs or []}
    for firewall in central.network_firewall.firewalls:
        vpc = vpc_map.get(firewall.vpc)
        if vpc:
            fixture_name = config._to_fixture_name(vpc.account)
            region = vpc.region or config.home_region
            combinations.add((fixture_name, region))

    return sorted(combinations)


def get_transit_gateway_configs() -> list[TransitGatewayConfig]:
    """Get all Transit Gateway configurations from network config."""
    config = lza_config()
    return list(config.network.transit_gateways)


def get_transit_gateway_configs_for_region(region: str) -> list[TransitGatewayConfig]:
    """Get Transit Gateway configurations for a specific region."""
    return [tgw for tgw in get_transit_gateway_configs() if tgw.region == region]


def get_transit_gateway_account_region_combinations() -> list[tuple[str, str]]:
    """Get (fixture_name, region) tuples for Transit Gateway deployments."""
    config = lza_config()
    combinations: list[tuple[str, str]] = []
    for tgw in config.network.transit_gateways:
        fixture_name = config._to_fixture_name(tgw.account)
        combinations.append((fixture_name, tgw.region))
    return sorted(set(combinations))


def get_shared_transit_gateway_account_region_combinations() -> list[tuple[str, str]]:
    """(fixture_name, region) for every Transit Gateway that declares ``shareTargets``.

    These are the accounts and regions where LZA creates a RAM resource share it owns, so a
    probe that needs an existing share owned by ``SELF`` has one to aim at. Only accounts under
    test are returned.
    """
    config = lza_config()
    combinations = {(config._to_fixture_name(tgw.account), tgw.region) for tgw in config.network.transit_gateways if tgw.share_targets}
    return sorted((fixture_name, region) for fixture_name, region in combinations if fixture_name in config._available_fixtures)


def get_vpcs_with_cidrs(account_fixture_name: str, region: str) -> list[VpcConfig]:
    """Get VPCs with static CIDR definitions for an account/region."""
    return [vpc for vpc in get_vpcs_for_account_region(account_fixture_name, region) if vpc.cidrs]


def get_vpcs_with_ipam_allocations(account_fixture_name: str, region: str) -> list[VpcConfig]:
    """Get VPCs with IPAM allocations for an account/region."""
    return [vpc for vpc in get_vpcs_for_account_region(account_fixture_name, region) if vpc.ipam_allocations]


def get_vpcs_with_interface_endpoints(account_fixture_name: str, region: str) -> list[VpcConfig]:
    """Get VPCs with interface endpoints for an account/region."""
    return [vpc for vpc in get_vpcs_for_account_region(account_fixture_name, region) if vpc.interface_endpoints]


def get_vpc_account_region_combinations_with_interface_endpoints() -> list[tuple[str, str]]:
    """Get unique (fixture_name, region) tuples for VPCs with interface endpoints."""
    config = lza_config()
    result: set[tuple[str, str]] = set()
    for vpc in config.network.vpcs or []:
        if vpc.interface_endpoints:
            fixture_name = config._to_fixture_name(vpc.account)
            region = vpc.region or config.home_region
            result.add((fixture_name, region))
    return sorted(result)


def get_ipam_pools_with_share_targets() -> list[IpamPoolShare]:
    """Get IPAM pools that have share targets configured."""
    config = lza_config()
    central = config.network.central_network_services
    if not central or not central.ipams:
        return []
    result: list[IpamPoolShare] = []
    for ipam in central.ipams:
        for pool in ipam.pools or []:
            if pool.share_targets:
                targets = pool.share_targets
                fixture_names = config.account_fixture_names_from_targets(
                    targets.organizational_units or [],
                    targets.accounts or [],
                )
                result.append({"pool_name": pool.name, "fixture_names": fixture_names})
    return result


def _policy_file_text(policy_path: str) -> str:
    """Raw text of a policy document in the LZA config directory."""
    return (lza_config_dir() / policy_path).read_text()


def load_policy_file(policy_path: str) -> dict[str, Any]:
    """Load a policy JSON document (SCP, RCP, ...) from the LZA config directory, unresolved."""
    document: dict[str, Any] = json.loads(_policy_file_text(policy_path))
    return document


# LZA's ${ACCEL_LOOKUP::CUSTOM:<Key>} reads the globalReplacements value of <Key> at deploy time.
_CUSTOM_LOOKUP_PLACEHOLDER = re.compile(r"\$\{ACCEL_LOOKUP::CUSTOM:([A-Za-z][A-Za-z0-9_]*)\}")


def resolve_policy_placeholders(content: str, substitutions: dict[str, str], replacements: dict[str, str]) -> str:
    """Apply LZA's deploy-time placeholder substitution to policy text.

    ``substitutions`` maps literal ``${VARIABLE}`` placeholders to values; ``replacements``
    is the globalReplacements dict that ``${ACCEL_LOOKUP::CUSTOM:<Key>}`` lookups read. A
    placeholder with no mapping is left in place so the caller's comparison fails visibly.
    """
    for variable, value in substitutions.items():
        content = content.replace(variable, value)
    return _CUSTOM_LOOKUP_PLACEHOLDER.sub(lambda match: replacements.get(match.group(1), match.group(0)), content)


def _map_lza_names_to_keys(accounts_under_test: dict[str, Any], lza_account_names: list[str]) -> dict[str, str]:
    """Return {LZA account name: cats.yaml key}; fail if an entry names an account that does not exist.

    An entry's LZA account name is its key, or its ``account_name`` if set.
    """
    lza_name_by_key = {key: (acc.get("account_name") or key) for key, acc in accounts_under_test.items()}
    unmatched = sorted(f"{key} -> {name}" for key, name in lza_name_by_key.items() if name not in lza_account_names)
    if unmatched:
        known = sorted(lza_account_names)
        raise CatsConfigError(f"cats.yaml: these accounts_under_test entries name no account in accounts-config.yaml: {unmatched}; it names {known}")
    return {name: key for key, name in lza_name_by_key.items()}


def _require_every_account_in_an_ou(accounts: AccountsConfig) -> None:
    """Refuse a configuration with an account outside any OU.

    Every deploymentTargets resolution in this module goes through the account's OU, so an
    account without one would be absent from every parametrized test with no record of why.
    The LZA schema marks ``organizationalUnit`` optional; the Universal Configuration always
    sets it, and this pack requires it.
    """
    unplaced = [account.name for account in [*accounts.mandatory_accounts, *accounts.workload_accounts] if account.organizational_unit is None]
    if unplaced:
        raise CatsConfigError(f"accounts-config.yaml: every account must declare organizationalUnit; missing on {unplaced}")


@cache
def lza_config() -> LzaConfig:
    """Load all LZA configs with template replacements applied."""
    config_dir = lza_config_dir()

    # Load and validate replacements, then extract plain string values
    raw_replacements = yaml.safe_load((config_dir / "replacements-config.yaml").read_text())
    validated_replacements = ReplacementsConfig.model_validate(raw_replacements)
    subs = _build_replacement_dict(validated_replacements)

    accounts = AccountsConfig.model_validate(_load_yaml(config_dir / "accounts-config.yaml", subs))
    _require_every_account_in_an_ou(accounts)

    return LzaConfig(
        accounts=accounts,
        global_=GlobalConfig.model_validate(_load_yaml(config_dir / "global-config.yaml", subs)),
        organization=OrganizationConfig.model_validate(_load_yaml(config_dir / "organization-config.yaml", subs)),
        security=SecurityConfig.model_validate(_load_yaml(config_dir / "security-config.yaml", subs)),
        iam=IamConfig.model_validate(_load_yaml(config_dir / "iam-config.yaml", subs)),
        network=NetworkConfig.model_validate(_load_yaml(config_dir / "network-config.yaml", subs)),
        replacements=subs,
    )

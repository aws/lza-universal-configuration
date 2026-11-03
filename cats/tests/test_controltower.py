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

"""
CATS - Validate AWS Control Tower configuration

Related LZA Controls and Tests:
- LZA-G-CT-1: Configures Control Tower for setting up and governing a secure multi-account AWS environment
  * test_controltower_landing_zone_enabled
- LZA-G-CT-2: Leverages Control Tower Dashboard for visibility into compliance status
  * test_controltower_landing_zone_not_drifted
  * test_controltower_enabled_controls_deployed_and_not_drifted
  * test_controltower_governed_accounts_enrolled
  * test_controltower_compliance_aggregator_covers_governed_accounts
- LZA-G-CT-3: Enforces default Control Tower preventive controls to enforce policies and detective controls to detect configuration violations
  * test_controltower_preventive_detective_controls

The Control Tower dashboard is a console surface, so CT-2 cannot be evidenced by looking at it.
The workbook claims it gives "real-time insights into the compliance status of all enrolled
accounts" through "guardrail status monitoring" (NIST CA-7 and its automation enhancements).
Every panel on that dashboard renders one API's state: landing-zone drift
(``GetLandingZone``), per-OU control status and drift (``ListEnabledControls``), enrolled
accounts (``ListEnabledBaselines``), and noncompliant resources (the
``aws-controltower-ConfigAggregatorForOrganization`` Config aggregator in the Audit account).
The CT-2 tests read those four surfaces and assert the status they report is healthy and
covers every account Control Tower governs. That is configuration evidence: it shows the
monitoring is on, current and complete, not that a violation would be surfaced.

Every test requires ``control-tower`` (Requirement.CONTROL_TOWER): the Organizations-only
variant of the Universal Configuration (``controlTower.enable: false``) has no landing zone
or enabled controls to verify, so they are recorded ``not_run`` there. The requirement is
derived from global-config.yaml by ``tests/conftest.py``; nothing needs listing in
``test_selection.provides``.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import TYPE_CHECKING

from cats import cats, cats_requires

from cats_utils.accounts import non_management_accounts
from cats_utils.boto import DEFAULT_RETRY_CONFIG
from cats_utils.cats_cache import get_enabled_baselines, get_enabled_controls
from cats_utils.evidence import Evidence
from cats_utils.requirement import Requirement
from lza_utils.lza_config import lza_config

if TYPE_CHECKING:
    from cats import GetAccountFixture
    from mypy_boto3_controltower.type_defs import EnabledControlSummaryTypeDef

    from cats_types import AuditAccount, ManagementAccount

# Set Logging (conftest.py handles configuration)
logger = logging.getLogger(__name__)

# Control Tower landing zone 4.0+ creates this service-linked organization aggregator in the Audit
# account; the dashboard's "noncompliant resources" view reads from it. Earlier landing zones used an
# account-level aggregator named ``aws-controltower-GuardrailsComplianceAggregator`` instead, which
# 4.0 removes (https://docs.aws.amazon.com/controltower/latest/userguide/config-updates-v4.html).
# The name is a Control Tower contract, not an LZA setting, so there is nothing to derive it from.
CONTROL_TOWER_COMPLIANCE_AGGREGATOR_NAME = "aws-controltower-ConfigAggregatorForOrganization"

# Drift states under which Control Tower still has visibility of the control. ``NOT_CHECKING`` is
# Control Tower's normal state for a control it does not drift-check (every preventive control);
# ``UNKNOWN`` means Control Tower cannot tell, which is itself a loss of visibility.
VISIBLE_DRIFT_STATUSES = frozenset({"IN_SYNC", "NOT_CHECKING"})

DEPLOYED_STATUS = "SUCCEEDED"


def _governed_account_ids(get_account_fixture: GetAccountFixture) -> set[str]:
    """Account IDs of every member account under test: Control Tower governs every OU the Universal Configuration creates.

    That includes the container deployment's ``LzaDeployment`` OU, which is registered with Control
    Tower and carries its mandatory preventive controls; it has no elective detective controls,
    which is why the Config-rule probes use the narrower ``core_ou_accounts()``, but its account is
    enrolled and aggregated like every other member.
    """
    return {get_account_fixture(name).account_id for name in non_management_accounts()}


def _control_health(control: EnabledControlSummaryTypeDef) -> tuple[str, str, str]:
    """(deployment status, overall drift status, inheritance drift status) as the dashboard shows them."""
    status = control.get("statusSummary", {}).get("status", "<statusSummary not returned by API>")
    drift_summary = control.get("driftStatusSummary", {})
    overall_drift = drift_summary.get("driftStatus", "<driftStatus not returned by API>")
    inheritance_drift = drift_summary.get("types", {}).get("inheritance", {}).get("status", "<inheritance drift not returned by API>")
    return status, overall_drift, inheritance_drift


def _control_is_visible(control: EnabledControlSummaryTypeDef) -> bool:
    """Deployed, and both drift statuses are ones Control Tower can see."""
    status, overall_drift, inheritance_drift = _control_health(control)
    return status == DEPLOYED_STATUS and overall_drift in VISIBLE_DRIFT_STATUSES and inheritance_drift in VISIBLE_DRIFT_STATUSES


def _control_label(control: EnabledControlSummaryTypeDef) -> str:
    """``<control name> @ <OU id>`` so a failure names the control and where it is enabled."""
    control_name = control.get("controlIdentifier", "<controlIdentifier not returned by API>").rsplit("/", 1)[-1]
    target = control.get("targetIdentifier", "<targetIdentifier not returned by API>").rsplit("/", 1)[-1]
    return f"{control_name} @ {target}"


def _account_id_of_baseline_target(target_identifier: str) -> str | None:
    """Account ID when a baseline target is an account ARN (``...:account/o-xxx/<id>``), else None for OU targets."""
    if ":account/" not in target_identifier:
        return None
    return target_identifier.rsplit("/", 1)[1]


@cats_requires(Requirement.CONTROL_TOWER)
@cats(standard_name=["LZA-G-CT-1"], test_suite="controltower", test_id="1", evidence=Evidence.CONFIGURATION)
def test_controltower_landing_zone_enabled(
    Management_account: ManagementAccount,
) -> None:
    """LZA-G-CT-1: Configures Control Tower for setting up and governing a secure multi-account AWS environment."""
    # arrange
    home_region = lza_config().home_region
    controltower_client = Management_account.session.client("controltower", region_name=home_region, config=DEFAULT_RETRY_CONFIG)

    # act - list landing zones and get details of the primary landing zone
    landing_zones = [zone for page in controltower_client.get_paginator("list_landing_zones").paginate() for zone in page["landingZones"]]

    logger.info(f"Found {len(landing_zones)} landing zone(s)")

    # assert - at least one landing zone must exist
    assert landing_zones, f"No Control Tower landing zones found for Management account in region {home_region}"

    primary_landing_zone = landing_zones[0]
    landing_zone_arn = primary_landing_zone["arn"]

    landing_zone_details = controltower_client.get_landing_zone(landingZoneIdentifier=landing_zone_arn)
    landing_zone_status = landing_zone_details["landingZone"]["status"]

    logger.info(f"Landing zone status: {landing_zone_status}")

    # assert - landing zone must be ACTIVE
    assert landing_zone_status == "ACTIVE", f"Control Tower landing zone is not active (status: {landing_zone_status})"


@cats_requires(Requirement.CONTROL_TOWER)
@cats(standard_name=["LZA-G-CT-2"], test_suite="controltower", test_id="2", evidence=Evidence.CONFIGURATION)
def test_controltower_landing_zone_not_drifted(
    Management_account: ManagementAccount,
) -> None:
    """LZA-G-CT-2: the landing-zone drift status the dashboard headlines is IN_SYNC.

    CT-1 asserts the landing zone is ACTIVE; drift is the monitoring signal, so it is CT-2 evidence.
    """
    # arrange
    home_region = lza_config().home_region
    controltower_client = Management_account.session.client("controltower", region_name=home_region, config=DEFAULT_RETRY_CONFIG)
    landing_zones = [zone for page in controltower_client.get_paginator("list_landing_zones").paginate() for zone in page["landingZones"]]
    assert landing_zones, f"No Control Tower landing zones found for Management account in region {home_region}"

    # act
    landing_zone = controltower_client.get_landing_zone(landingZoneIdentifier=landing_zones[0]["arn"])["landingZone"]
    drift_status = landing_zone.get("driftStatus", {}).get("status", "<driftStatus not returned by API>")

    # assert
    assert drift_status == "IN_SYNC", f"Control Tower landing zone drift status is {drift_status}"


@cats_requires(Requirement.CONTROL_TOWER)
@cats(standard_name=["LZA-G-CT-2"], test_suite="controltower", test_id="4", evidence=Evidence.CONFIGURATION)
def test_controltower_enabled_controls_deployed_and_not_drifted(
    Management_account: ManagementAccount,
) -> None:
    """LZA-G-CT-2: every enabled control reports SUCCEEDED deployment and a drift status Control Tower can see.

    This is the per-OU control status the dashboard's controls panel renders. A FAILED or
    UNDER_CHANGE control, or one DRIFTED / UNKNOWN, is a gap in the visibility the control claims.
    """
    # act
    enabled_controls = get_enabled_controls(Management_account)
    assert enabled_controls, "No Control Tower controls are enabled"

    # assert
    unhealthy_controls = {_control_label(control): _control_health(control) for control in enabled_controls if not _control_is_visible(control)}
    assert unhealthy_controls == {}, f"Enabled controls not ({DEPLOYED_STATUS}, visible drift, visible inheritance drift): {unhealthy_controls}"


@cats_requires(Requirement.CONTROL_TOWER)
@cats(standard_name=["LZA-G-CT-2"], test_suite="controltower", test_id="5", evidence=Evidence.CONFIGURATION)
def test_controltower_governed_accounts_enrolled(
    Management_account: ManagementAccount,
    get_account_fixture: GetAccountFixture,
) -> None:
    """LZA-G-CT-2: every account Control Tower governs is an enrolled baseline target in SUCCEEDED state.

    "Compliance status of all enrolled accounts" is only true for the accounts that are enrolled;
    this pins that set to the accounts under test the pack believes Control Tower governs.
    """
    # arrange
    governed_account_ids = _governed_account_ids(get_account_fixture)
    expected_enrollment = dict.fromkeys(sorted(governed_account_ids), DEPLOYED_STATUS)

    # act
    enrolled_accounts: dict[str, str] = {}
    for baseline in get_enabled_baselines(Management_account):
        account_id = _account_id_of_baseline_target(baseline["targetIdentifier"])
        if account_id in governed_account_ids:
            enrolled_accounts[account_id] = baseline["statusSummary"].get("status", "<statusSummary.status not returned by API>")

    # assert - a missing key is an unenrolled account, a differing value is a failed enrollment
    assert dict(sorted(enrolled_accounts.items())) == expected_enrollment


@cats_requires(Requirement.CONTROL_TOWER)
@cats(standard_name=["LZA-G-CT-2"], test_suite="controltower", test_id="6", evidence=Evidence.CONFIGURATION)
def test_controltower_compliance_aggregator_covers_governed_accounts(
    Audit_account: AuditAccount,
    get_account_fixture: GetAccountFixture,
) -> None:
    """LZA-G-CT-2: the Control Tower compliance aggregator holds Config rule results for every governed account.

    The dashboard's noncompliant-resources view reads this aggregator; an account with no
    aggregated compliance summary is one whose violations the dashboard could not show.
    ``describe_configuration_aggregators`` raises ``NoSuchConfigurationAggregatorException``
    when the aggregator is absent, which is the intended failure.
    """
    # arrange
    home_region = lza_config().home_region
    config_client = Audit_account.session.client("config", region_name=home_region, config=DEFAULT_RETRY_CONFIG)
    governed_account_ids = _governed_account_ids(get_account_fixture)
    config_client.describe_configuration_aggregators(ConfigurationAggregatorNames=[CONTROL_TOWER_COMPLIANCE_AGGREGATOR_NAME])

    # act - no paginator exists for this API
    accounts_with_compliance_data: set[str] = set()
    next_token = ""
    while True:
        response = config_client.get_aggregate_config_rule_compliance_summary(
            ConfigurationAggregatorName=CONTROL_TOWER_COMPLIANCE_AGGREGATOR_NAME, GroupByKey="ACCOUNT_ID", NextToken=next_token
        )
        for count in response["AggregateComplianceCounts"]:
            accounts_with_compliance_data.add(count.get("GroupName", "<GroupName not returned by API>"))
        next_token = response.get("NextToken", "")
        if not next_token:
            break

    # assert
    accounts_without_compliance_data = governed_account_ids - accounts_with_compliance_data
    assert accounts_without_compliance_data == set(), (
        f"Governed accounts with no compliance summary in {CONTROL_TOWER_COMPLIANCE_AGGREGATOR_NAME}: {sorted(accounts_without_compliance_data)}"
    )


@cats_requires(Requirement.CONTROL_TOWER)
@cats(standard_name=["LZA-G-CT-3"], test_suite="controltower", test_id="3", evidence=Evidence.CONFIGURATION)
def test_controltower_preventive_detective_controls(
    Management_account: ManagementAccount,
) -> None:
    """LZA-G-CT-3: Enforces default Control Tower preventive and detective controls."""
    # arrange
    home_region = lza_config().home_region
    controlcatalog_client = Management_account.session.client("controlcatalog", region_name=home_region, config=DEFAULT_RETRY_CONFIG)

    # act - list all enabled controls
    enabled_control_arns = {control["controlIdentifier"] for control in get_enabled_controls(Management_account)}

    assert enabled_control_arns, "No Control Tower controls are enabled"

    # Use Control Catalog to get the actual behavior (PREVENTIVE/DETECTIVE/PROACTIVE)
    # for each enabled control rather than relying on naming conventions.
    controls_by_behavior: defaultdict[str, list[str]] = defaultdict(list)

    catalog_paginator = controlcatalog_client.get_paginator("list_controls")
    for catalog_page in catalog_paginator.paginate():
        for catalog_control in catalog_page["Controls"]:
            arn: str = catalog_control["Arn"]
            if arn not in enabled_control_arns:
                continue
            behavior: str = catalog_control.get("Behavior", "")
            if behavior:
                controls_by_behavior[behavior].append(arn)

    # assert — both preventive and detective types must be present
    assert controls_by_behavior["PREVENTIVE"], "No preventive controls enabled in Control Tower"
    assert controls_by_behavior["DETECTIVE"], "No detective controls enabled in Control Tower"

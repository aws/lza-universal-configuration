# LZA Universal Configuration Controls Test Pack

Control Acceptance Testing Suite (CATS) tests for AWS Landing Zone Accelerator environments deployed with the Universal Configuration, to audit and evidence controls from the LZA Compliance Workbook.

## Prerequisites

- Python 3.14+
- [uv](https://docs.astral.sh/uv/) (or pip)
- AWS credentials that can assume `AWSControlTowerExecution` (or your configured role) into each account under test

## Installation

From this directory:

```bash
uv sync
```

`uv sync` creates `.venv` with the CATS engine (`aws-cats`, pinned to a minor release in
`pyproject.toml`, so engine patch fixes arrive with a fresh `uv sync`) and the pack's other
dependencies, and writes the versions it resolved to `uv.lock`; prefix commands with
`uv run` (`uv run cats ...`) or activate the
environment. Without uv: `python3.14 -m venv .venv && . .venv/bin/activate && pip install .`.

Intel (x86_64) macOS is not supported: the `cryptography` library the engine depends on stopped
publishing Intel macOS wheels in version 49.0, and Apple has announced macOS 26 as the last
release for Intel hardware.

## Configuration and Setup

1. Copy the example for your deployment shape from `examples/` (Control Tower or
   Organizations-only, LZA from CodePipeline or as a container; its README compares them) to this
   directory as `cats.yaml`, then edit it with your account IDs and SSM parameter paths. Every
   `CHANGE_ME` value must be replaced.
   The default test role CATS deploys into each account is least-privilege and carries no managed policy.
   Two files in `policies/` name every API action the test pack calls: `default-test-role-read.json`
   (Describe/Get/List/Search only) and `default-test-role-mutating.json` (the one action each SCP/RCP
   enforcement probe attempts, one statement per control). As shipped, the role gets only the read
   policy and the `mutating` marker is excluded under `test_selection`, so the enforcement probes are
   recorded `not_run` and nothing the tests do can change your accounts. To run the probes, uncomment
   the `CatsMutating` line, redeploy, and remove the `mutating` exclusion (see "Excluding a control, or
   running read-only" below). Keep the files next to `cats.yaml`; a test that calls a new API needs
   its action added to the matching file.
   Account tags tell the pack which account plays which role: exactly one entry must be tagged
   `management` and exactly one `perimeter` (the account hosting the ingress and egress VPCs,
   the only one allowed an internet or NAT gateway); infrastructure and workload accounts carry
   `infrastructure` / `workload`; on a container deployment the account hosting the LZA
   installer is tagged `lza-deployment`, which keeps it out of the Control Tower Config-rule and
   core RCP probes (its OU carries neither) and sanctions its own internet gateway. The examples
   have these set. Each entry's key is the account's `name` in `accounts-config.yaml`;
   set `account_name` only when that name is not a valid key (keys are letters, digits and
   underscores). An entry naming an account that does not exist fails config load, so a typo
   cannot silently drop an account from the tests. The six Universal Configuration accounts
   (`Management`, `Audit`, `LogArchive`, `Network`, `SharedServices`, `Perimeter`) keep their
   keys: the tests take them as fixtures by that name.
2. Decide where the tests read your LZA configuration from. See "The configuration under test"
   below. With nothing set, a CodePipeline deployment needs no step here: the tests fetch the
   configuration LZA last deployed from the installer's config bucket.
3. Deploy CATS test infrastructure:
   ```bash
   cats infra deploy --all
   ```

## The configuration under test

The tests prove controls against the configuration LZA actually deployed, never against the
Universal Configuration template. The UC repository's `modules/` tree is not deployable as it
stands: UC's release scripts fill `replacements-config.yaml` from the environment (home region,
enabled regions, notification emails), add the workload accounts and expand `network-config.yaml`
into per-region `include/` fragments before the zip reaches the installer bucket. Reading the
template would compare your accounts against regions, emails and VPCs that are not yours, so
the pack does not do it, and ships no copy of the configuration.

Where the configuration comes from, in order:

1. `LZA_LOCAL_CONFIG_DIR`: a directory holding an unpacked configuration, from any source.
   Useful for a configuration you have pulled by hand (`scripts/pull_lza_config.py`), or the
   `modules/temp/` directory UC's own scripts produce in a UC checkout.
2. The deployed zip in the installer config bucket, read through `deploy_role_name` in the
   account that owns the bucket and unpacked once per object version under `.pytest_cache/`.
   - CodePipeline installer: nothing to set. The bucket is
     `aws-accelerator-config-<management account ID>-<aws_region>`, key
     `zipped/aws-accelerator-config.zip`, in the account tagged `management` in `cats.yaml`.
   - Container installer: the bucket belongs to the `InstallerContainerStack` and its name
     depends on your accelerator qualifier, so set all three of `LZA_CONFIG_ACCOUNT` (the
     account's key in `cats.yaml`, for example `LzaDeployment`), `LZA_CONFIG_BUCKET` and
     `LZA_CONFIG_KEY` (`lza/aws-accelerator-config.zip`).

With neither available the run fails naming both options. A redeploy changes the object's
ETag, so the next run reads the new configuration without clearing anything.

## Running Tests

```bash
# Run all tests
cats test ./tests/ -n auto -vv

# Run a single test file
cats test ./tests/test_ebs.py -vv

# Run tests for a specific suite
cats test ./tests/ -m "scp"

# Skip network/infrastructure tests (no CATS infra deployment needed)
cats test ./tests/ --ignore=tests/test_vpc_north_south_traffic.py --ignore=tests/test_vpc_east_west_traffic.py
```

`-k`, `-m` and `--ignore` are for ad-hoc runs: a test they leave out is absent from the
reports with no record of why. To change which tests apply to your deployment permanently,
use the `test_selection` block in `cats.yaml` (below). Every test it holds back is recorded
in every report as `not_run` with its reason, so the control stays in the evidence.

## Choosing which tests apply

`test_selection` in `cats.yaml` decides which tests apply to your deployment. Every test it
holds back is recorded in every report as `not_run` with its reason, so the control stays in
the evidence; a test `-k` or `-m` removes leaves no record.

Container deployment. The Universal Configuration can run LZA as an ECS task in a dedicated
`LzaDeployment` account instead of CodePipeline. Tests for that variant (LZA-G-ACT-7,
`tests/test_deployment_account.py`; LZA-G-SCP-38, `tests/scp/test_scp_deployment_guardrails.py`)
carry `@cats_requires(Requirement.CONTAINER_DEPLOYMENT)`
and do not run by default. Add that account to `accounts_under_test` (keyed by its `name` in
`accounts-config.yaml`, tagged `lza-deployment`) and declare the variant:

```yaml
test_selection:
  provides: [container-deployment]
```

The two `examples/*-container.yaml` files have both edits made.

With `provides` empty the pack provides `standard-deployment` for you; listing
`container-deployment` switches that off.

Workload accounts. An unmodified Universal Configuration creates the Workloads OUs empty, so
nothing can be probed from a workload VPC, and the examples list none (a commented
example entry shows the shape). Tests that need one require `workload-accounts`, which the pack
provides as soon as any entry in `accounts_under_test` is tagged `workload`; until then they are
recorded `not_run` with the requirement named. Five controls are affected:

| Control | Tests held back without a workload account | What still runs |
|---|---|---|
| LZA-NET-SEC-1 | all of `tests/test_vpc_east_west_traffic.py` | nothing: the control is spoke-to-hub and spoke-to-spoke traffic |
| LZA-NET-SEC-2 | `test_internet_access_blocking_workload` (vpc NS-1-workload), `test_dns_resolution_blocked_workload` (dns 1-workload) | the same probes from the Network, SharedServices and Perimeter VPCs |
| LZA-NET-SEC-8 | `test_dns_firewall_blocks_managed_list_domains_workload` (dns 2-workload) | the same probe from the infrastructure VPCs |
| LZA-G-SCP-23 | `test_scp_blocks_nat_gateway_creation_workload` (scp 23a-workload) | the Infrastructure SCP's deny, probed from the infrastructure accounts |
| LZA-G-SCP-24 | `test_scp_blocks_transit_gateway_creation_workload`, `test_scp_blocks_transit_gateway_deletion_workload` (scp 24a/24b-workload) | the Infrastructure SCP's deny, probed from the infrastructure accounts |

The infrastructure half of each split control passes on its own, so a deployment without
workload accounts reports those four controls satisfied on infrastructure evidence and carries
a `not_run` row saying the Workloads SCP and workload VPCs were never exercised. With one
workload account the spoke-to-hub tests run and the isolation test is skipped with a reason
saying a second account is needed.

Organizations-only deployment. The Universal Configuration can run without AWS Control Tower
(`controlTower.enable: false` in global-config.yaml) and without IAM Identity Center (no
`identityCenter` block in iam-config.yaml). The tests that verify and protect Control Tower
itself (LZA-G-CT-1/2/3, `tests/test_controltower.py`; LZA-G-SCP-6,
`tests/scp/test_scp_service_protection.py`) require `control-tower`, and the Identity Center
delegation test (LZA-SEC-IDC-1, `tests/test_iam_policy.py`) requires `identity-center`. Both
are read from the deployed LZA config ("The configuration under test"), so a Control Tower
deployment never lists them; on an Organizations-only deployment they are recorded `not_run`
with the requirement named. There is no requirement for the organization CloudTrail: every
deployment must have one, whether Control Tower's or LZA's own, so LZA-LOG-5 and LZA-G-SCP-2
fail when none exists. The one `cats.yaml` edit this shape needs is the deploy role:
`AWSControlTowerExecution` does not exist without Control Tower, so `deploy_role_name` is
`OrganizationAccountAccessRole`, as in `examples/organizations-standard.yaml` and
`examples/organizations-container.yaml`.

Excluding a control, or running read-only:

```yaml
test_selection:
  excluded:
    - marker: standard_name
      values: [LZA-G-SCP-34]
      reason: "RDS not in use; accepted by CISO 2026-09-01"
    - marker: mutating
      values: [true]   # a YAML boolean, matching @cats(mutating=True)
      reason: "Change freeze until 2026-10-20"
```

`marker` is `standard_name`, `cats_requires`, or a name under `reporting.custom_markers`;
anything else fails `cats validate`. Every example carries the `mutating` exclusion
and no `CatsMutating` policy, so it is read-only until you change both; the two belong
together, since a probe with the exclusion lifted but no permission fails with an IAM denial
instead of proving the guardrail.

## Expected failures

Four tests check controls that the Universal Configuration cannot currently meet because
of two open defects in LZA. They carry `@pytest.mark.xfail` and are
reported as `xfailed` in `report.json` and `junit.xml`, so the control
stays in the evidence with the affected resources listed in the captured assertion.

| Control | Test | Upstream LZA issue | What fails |
|---|---|---|---|
| LZA-SEC-CWL-1 | `tests/test_cloudwatch_logs.py::test_cloudwatch_logs_retention_bootstrap_log_groups` (cloudwatch 1b) | [#875](https://github.com/awslabs/landing-zone-accelerator-on-aws/issues/875) | Bootstrap-stage log groups are left at never expire, or at the installer's default, instead of `log_retention_days` |
| LZA-SEC-CWL-3 | `tests/test_cloudwatch_logs.py::test_cloudwatch_logs_subscription_filters_bootstrap_log_groups` (cloudwatch 3b) | [#875](https://github.com/awslabs/landing-zone-accelerator-on-aws/issues/875) | The same log groups have no subscription filter to the LogArchive CloudWatchToS3 destination |
| LZA-SEC-CWL-4 | `tests/test_cloudwatch_logs.py::test_cloudwatch_logs_cmk_encryption_bootstrap_log_groups` (cloudwatch 4b) | [#875](https://github.com/awslabs/landing-zone-accelerator-on-aws/issues/875) | The same log groups are not encrypted with a customer-managed KMS key |
| LZA-SEC-CRY-1 | `tests/test_lambda_encryption.py::test_lambda_env_vars_encrypted_with_cmk` (lambda 1, every account and region) | [#846](https://github.com/awslabs/landing-zone-accelerator-on-aws/issues/846) | Functions created through CDK `CustomResourceProvider.getOrCreateProvider` have environment variables but no customer-managed `KMSKeyArn` |

### Why the CloudWatch Logs tests fail (#875)

LZA applies retention, the customer-managed key and the CloudWatchToS3 subscription
filter to log groups through an event-driven mechanism that its Logging stack deploys.
Log groups that exist before that mechanism does are never configured by it. They belong
to the Installer, Pipeline, DiagnosticsPack, Prepare, Accounts, Organizations and Logging
stacks and to the CodeBuild projects: their Lambda functions and builds create the log
group implicitly on first invocation with `CreateLogGroup`, which leaves retention at
never expire with no subscription filter and no customer-managed key. LZA also never
lowers the retention of an existing log group, so a later pipeline run does not correct
them. This class is defined by `lza_utils/log_groups.py::is_lza_bootstrap_log_group`
and was verified against a 9-account, 5-region sweep: every finding fell inside it, and
all 1,315 log groups outside it were compliant.

The controls are therefore split. Tests 1, 3 and 4 cover every log group created after
the Logging stage and must pass in every account and region; a failure there is a
regression. Tests `1b`, `3b` and `4b` cover the bootstrap class and run once across all
accounts and regions, because which bootstrap log groups are affected varies per
deployment, so a per-account result would flip between runs and prove nothing.

What you can do: these log groups hold LZA's own operational logs, not workload data.
You may remediate them in place with `put-retention-policy`, `associate-kms-key` to the
LZA CloudWatch key in that account and region, and `put-subscription-filter` to the
`CloudWatchToS3` destination in the LogArchive account. The `1b`/`3b`/`4b` tests then
report `xpassed`, and the strict tests are unaffected. Keep the markers: a future LZA
pipeline run that recreates one of these functions recreates its log group unconfigured.

### Why the Lambda encryption test fails (#846)

LZA attaches its Lambda customer-managed key to the functions it declares directly.
Functions created through CDK's `CustomResourceProvider.getOrCreateProvider` take no
key parameter, so their environment variables fall back to Lambda's default encryption
with an AWS-owned key; the same applies to a small number of other constructs that do
not pass the key through. The fix is a CDK aspect in LZA and is tracked upstream. The
test checks every LZA-prefixed function rather than a named list so that it catches all
of those constructs, which is why it is parametrized per account and region.

What you can do: nothing in configuration, and do not attach a key to these functions
out of band, because the next pipeline run reverts the change and the drift fails
CloudFormation. The affected environment variables carry deployment parameters (SSM
paths, account IDs, region names), not secrets, and remain encrypted at rest. Record
the deviation against LZA-SEC-CRY-1 with the `xfailed` assertion output as evidence until
the fix is in your deployed LZA version.

### Reading the outcome

- `xfailed`: the known defect manifested. No action; the assertion output lists every
  affected resource as evidence for the compliance workbook caveat.
- `xpassed`: every affected resource is currently compliant, through an upstream fix,
  manual remediation or a lucky deployment. Still no action, and do not remove the
  marker: any LZA pipeline run can recreate non-compliant resources until the fix is
  in the deployed LZA version.
- `failed`: these tests cannot report it while the marker is present. A failure in the
  strict counterpart (tests 1, 3, 4) is a real finding and must be investigated.

When the deployed LZA version includes the fix for an issue above, remove the marker
from the test, record the change in the repository `CHANGELOG.md`, and delete the row here. For #875,
the retention test keeps failing after the upgrade until the existing log groups are
remediated as above or recreated, because LZA does not lower existing retention.

## Clean up

CATS deployments are intended as ephemeral - we don't want to maintain EC2 instances longer than needed. Tear it down when done:

```bash
cats infra destroy
```

## Reports

After a test run, CATS generates:

- `report.json` — machine-readable results (CATS JSON format)
- `assessment-results.json` — OSCAL Assessment Results
- `junit.xml` — JUnit XML for CI integration

### Choosing the framework for the report

Every result carries its LZA Compliance Workbook control ID (`LZA-G-SCP-10`). To have the
OSCAL findings written against one of the workbook's compliance frameworks instead, set
`LZA_OSCAL_FRAMEWORK` to that framework's column header, exactly as the workbook spells it:

```bash
LZA_OSCAL_FRAMEWORK="ISO-27001 Annex A (2022)" uv run cats test ./tests/
```

There is no default framework. Unset, the findings are keyed by the workbook control IDs
and no framework mapping is applied. A value that is not a column header stops the run
before any test executes, and the error lists the valid names, so a misspelling never
produces a report in the wrong vocabulary. One run renders one framework; run again with
another value for another framework.

Framework control IDs are written as OSCAL tokens: NIST enhancements use the catalog
convention (`AC-2.1` for `AC-2 (1)`), and IDs that begin with a digit are prefixed with the
framework name (`nist-800-171-rev2-3.1.1`). See `lza_utils/compliance_map.py` for the rules.

The mapping is read from `lza-compliance-workbook-<version>.csv` at the pack root; the
workbook's version is in the file name (1.4.0 ships: 193 controls, 26 frameworks). Set
`LZA_COMPLIANCE_MAP` to another workbook CSV in the same format to use its framework columns.

# Change Log

All notable changes to this project will be documented in this file.

## Important

We highly recommend that you keep your environments up to date by upgrading to the latest version.

When applying updates, review the changes in this release alongside your current configuration to decide which features from this version to adopt.

## [1.3.2] - 2026-09-23

### Bug Fixes

- **CloudFormation Stack Guardrail SCP (`GRCFM`)**: Extended the `GRCFM` deny statement to cover CloudFormation stack update actions in addition to the existing `cloudformation:Delete*`. This prevents non-accelerator principals from updating, rolling back, or replacing accelerator-managed stacks.

  **Upgrade Notes**: The LZA pipeline runs under `AWSAccelerator-*` roles that are already in the exclusion list, so normal deployment is unaffected.

## [1.3.1] - 2026-09-02

### Bug Fixes

- **STS Data Perimeter RCP (`GRSTSDPB`)**: Limited the STS identity perimeter statement to `sts:AssumeRole`. This restores federated sign-in to accounts in the targeted OUs while still denying role assumption from principals outside the organization.

  **Upgrade Notes**: This change only removes actions from an existing Deny, so no reconfiguration is required. The statement continues to deny `sts:AssumeRole` from principals outside your organization, so review your accounts for any such access before deploying. IAM Access Analyzer external access findings can help you identify roles that external principals can assume. If a principal outside your organization requires access, you can allow it by adding its account ID to the `aws:PrincipalAccount` condition in the `GRSTSDPB` statement.

### Improvements

- **AWS Config Delivery Channel**: Removed the deprecated `enableDeliveryChannel` field from `security-config.yaml`. The delivery channel continues to be provisioned by `enableConfigurationRecorder`. No change to the deployed environment.

- **Declarative Policy Schema Alignment**: Removed the unsupported `type` field from the VPC Block Public Access declarative policy in `organization-config.yaml` to align with the LZA schema. No change to the deployed policy.

## [1.3.0] - 2026-07-31

### New Features

- **AWS European Sovereign Cloud Support**: Added the LZA Universal Configuration for the [AWS European Sovereign Cloud](https://aws.eu/) partition, providing the same security controls and architecture as the standard Universal Configuration, adapted for partition-specific service availability and container-based deployment.

- **Amazon Bedrock AgentCore SCP Guardrails**: Added three SCP statements (`GRAGENTCORE1`, `GRAGENTCORE2`, `GRAGENTCORE3`) to both the Workloads and Infrastructure guardrail policies enforcing VPC isolation and encryption for AgentCore resources:
  - Denies creation/update of AgentCore Runtimes, Code Interpreters, and Browsers without VPC subnet and security group configuration
  - Denies AgentCore Runtime invocations that do not originate from a VPC
  - Denies creation of AgentCore Memory resources without a customer-managed KMS key

  **Upgrade Notes**: Existing AgentCore resources deployed without VPC configuration or KMS encryption will not be affected retroactively, but any new resource creation or updates must comply with these controls. Ensure infrastructure and workload accounts have appropriate VPC subnets, security groups, and KMS keys provisioned before deploying AgentCore resources.

- **Data Perimeter Controls (RCPs)**: Added identity and resource perimeter controls for STS, SQS, and Secrets Manager (`GRSTSDPB`, `GRSQSDPB`, `GSMDPB`) to block external principals from accessing resources in member accounts.

  **Upgrade Notes**: If any accounts have legitimate cross-account integrations with principals outside the organization, these statements will block those integrations. Use IAM Access Analyzer to review existing external access findings before deploying.

- **Amazon Bedrock AgentCore VPC Endpoints**: Added PrivateLink endpoints for AgentCore services with organization-scoped endpoint policies.

- **DNS Firewall Rule Groups**: Added DNS Firewall rule groups for workload and infrastructure VPCs to control outbound DNS resolution.

- **Transit Gateway Flow Logs**: Enabled Transit Gateway flow logs for centralized network traffic visibility.

- **Route 53 Resolver Query Logging**: Enabled Route 53 Resolver query logging across all VPCs for DNS audit visibility.

- **CloudFormation Stack Policies**: Added stack policy protection for critical networking resources to prevent accidental resource deletion or replacement during stack updates.

- **Service Quotas Guidance**: Added documentation for AWS Organizations account quota considerations when deploying the LZA Universal Configuration.

### Bug Fixes

- **Egress VPC Transit Gateway Route Table**: Fixed the egress VPC Transit Gateway attachment route table association from `tgw-rt-firewall` to `tgw-rt-spoke`. This ensures symmetric routing through the inspection VPC, which is required for stateful traffic inspection to function correctly.

  **Upgrade Notes**: This change requires **two pipeline runs** with a **change window**. Run 1 removes the existing egress VPC TGW route table association and propagation. Run 2 creates the new association to `tgw-rt-spoke` and adds propagations. The TGW attachment itself does not need to be deleted. There will be connectivity downtime between Run 1 (association removed) and Run 2 (new association created) for traffic traversing the egress path. Perform during a scheduled change window and validate connectivity after Run 2 completes.

- **DNS Firewall Share Targets**: Removed the Network account from DNS Firewall share targets to prevent resource conflicts.

- **S3 Backup Policies**: Updated backup policies and permissions to resolve S3 backup operation failures.

- **Tag Policy Key**: Fixed the outer key in the S3 tag policy to match the enforced tag key name.

- **Security Hub Automation**: Fixed `AcceleratorPrefix` variable usage in S3 automation `ResourceTags` filters.

### Improvements

- **Log Analysis Documentation**: Consolidated central log bucket access guidance into the log analysis operations guide.
- **Documentation**: Categorized AWS Config Rules by service domain, corrected Network Firewall traffic description, and standardized account naming conventions.

---

## [1.2.0] - 2026-03-20

### New Features

- **Security Hub Automation**: Added automation rules for Security Hub finding suppression with documentation for all suppressed controls
- **SSM Security**: Enabled block public sharing for SSM documents
- **LZA MCP Server**: Added LZA MCP Server description to README for AI-assisted deployment management

### Bug Fixes

- **GovCloud Configuration**: Added missing account IDs for GovCloud configurations
- **Cost**: Updated pricing documentation with networking model cost details
- **Documentation**: Fixed Mermaid diagrams not rendering on GitHub
- **Documentation**: Fixed SCP config file references in Managing SCPs guide

### Note

- **Container Deployment**: LZA now supports container-based deployment, enabling deployment in AWS regions without CodeBuild and CodePipeline support. For more information, refer to the [LZA README](https://github.com/awslabs/landing-zone-accelerator-on-aws/blob/release/v1.15.0/container/README.md).

### Contributors

We want to extend a special thank you to the following external users who have contributed to this release:

- @tvancast

## [1.1.0] - 2025-12-11

### CRITICAL

If you're on an LZA installation in a non-standard AWS partition (e.g., AWS GovCloud (US)), please do not upgrade to 1.14.0 and use 1.14.1 instead. Please see this [issue](https://github.com/awslabs/landing-zone-accelerator-on-aws/issues/972).

### New Features

- **Regional Guidance**: [Added US Federal region and industry guidance](./docs/08-Region-and-Industry-Guidance/us-federal/)
- **Cost Information**: Added pricing information to help estimate deployment costs
- **AWS Control Tower**: Updated to AWS Control Tower Landing Zone 4.0

### Improvements

- **Automated Builds**: Enhanced CI/CD with AWS GovCloud (US) package generation and security scanning
- **Documentation Updates**: Added high-level architecture and organizational unit (OU) structure diagrams

### Bug Fixes

- **Networking**: Removed internet gateway from inspection VPC
- **Documentation**: Fixed broken links and documentation errors
- **Control Tower**: Fixed issue where controls were not deploying to sub-organizational units

### Contributors

We want to extend a special thank you to the following external users who have contributed to this release:

- @Conklin-Spencer-bah

## [1.0.0] - 2025-09-29

### General Changes

- Initial General Availability (GA) release

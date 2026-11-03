# Landing Zone Accelerator on AWS (LZA) Universal Configuration

The LZA Universal Configuration provides enterprise-ready configuration templates that utilize the [Landing Zone Accelerator on AWS](https://aws.amazon.com/solutions/implementations/landing-zone-accelerator-on-aws/) (LZA) to establish secure, scalable, and well-architected multi-account AWS environments. It enables rapid deployment of baseline environments supporting multiple global compliance frameworks and industry-specific requirements.

## Getting Started

**To get started with this project, please refer to the comprehensive documentation in the [`docs/`](./docs) directory.** The documentation is organized in a logical sequence to guide you through understanding, deploying, and operating your LZA environment:

1. **[Overview](./docs/01-Overview)** - Architecture overview and design principles
2. **[Getting Started](./docs/02-Getting-Started)** - Deployment prerequisites and initial setup procedures
3. **[Management & Governance](./docs/03-Management-Governance)** - Organization structure and account management
4. **[Security, Identity & Compliance](./docs/04-Security-Identity-Compliance)** - Security controls and compliance frameworks
5. **[Networking](./docs/05-Networking)** - Network architecture patterns and connectivity
6. **[Logging & Monitoring](./docs/06-Logging-Monitoring)** - Centralized logging and monitoring setup
7. **[Operations](./docs/07-Operations)** - Day-to-day operational procedures and management tasks
8. **[Controls Testing](./docs/09-Controls-Testing)** - Test that the deployed controls are in place, with results mapped to the LZA Compliance Workbook

We recommend reviewing the documentation in order, starting with the Overview and Getting Started sections.

## Specific Regional and Industry Guidelines

For detailed information about supported regions and industry-specific configurations, including compliance frameworks, regulatory requirements, and implementation guidance, please refer to:

**[Support for Regions and Industries](https://docs.aws.amazon.com/solutions/latest/landing-zone-accelerator-on-aws/support-for-regions-and-industries.html)**

This comprehensive guide covers:

- Regional compliance requirements
- Industry-specific security controls and frameworks
- Regulatory compliance mappings

## Container Deployment

LZA now supports container-based deployment, enabling deployment in AWS regions without CodeBuild and CodePipeline support while providing improved performance through an optimized deployment process. For more information, refer to the [LZA Container Deployment documentation](https://github.com/awslabs/landing-zone-accelerator-on-aws/blob/release/v1.15.0/container/README.md).

## AI-Assisted Management (Optional)

The [LZA MCP Server](https://github.com/awslabs/lza-mcp-server) is an open-source
Model Context Protocol (MCP) server that provides AI-assisted management of LZA deployments,
including built-in support for Universal Configuration:

- **Guided UC Merge**: Select a network model, customize settings, validate compatibility,
  and merge into your LZA deployment — all through natural language conversation
- **Schema Discovery**: Search and explore LZA configuration schemas for your deployed version — helping the AI verify property names, types, and constraints when suggesting configuration changes
- **Pipeline Orchestration**: Deploy, monitor, and diagnose pipeline executions from your IDE

The MCP server ships with UC release artifacts embedded in the container image, so no
separate download is needed. See the
[Universal Configuration section](https://github.com/awslabs/lza-mcp-server#universal-configuration)
of the LZA MCP Server documentation for more information.

## CATS - Control Acceptance Testing Suite

[CATS](https://github.com/aws/cats) is an open framework for testing AWS environments. It deploys
temporary test infrastructure into your accounts, runs tests through a least-privilege test role,
and writes the results as JSON, JUnit and OSCAL Assessment Results.

### LZA Universal Configuration Controls Test Pack (Optional)

The Controls Test Pack runs on the CATS engine. It tests a deployed Universal Configuration
environment and reports, control by control, whether the security controls are in place:

- **Control Evidence**: Each result is tied to a control in the LZA Compliance Workbook, and reports
  can be mapped to the frameworks in the workbook, such as NIST 800-53 Rev5
- **Configuration and Behavior Checks**: Compares your accounts with your deployed LZA configuration,
  and attempts actions your SCPs and RCPs should deny to prove that they are denied
- **Audit-Ready Output**: Writes results as JSON, JUnit and OSCAL Assessment Results

The test pack is attached to each [release](https://github.com/aws/lza-universal-configuration/releases)
as `lza-universal-config-cats-<version>.zip`; `uv sync` installs the CATS engine (`aws-cats` on PyPI)
and the other dependencies. See [Controls Testing](./docs/09-Controls-Testing/index.adoc) for what it
checks, what it deploys in your accounts, and how to run it.

## What's Included

The LZA Universal Configuration provides ready-to-deploy configuration files and implementation guidance for LZA Universal Configuration baseline:

### Configuration Modules

Pre-configured LZA Universal Configuration files organized by the following deployment patterns:

- **[Base configurations](./modules/base/default)** - Security, Governance, and Organization settings
- **[Network configurations](./modules/network)** - Hub-and-spoke, and Shared VPC networking patterns

### Documentation

Architecture guides, deployment procedures, and detailed design principles that explain the implementation rationale and configuration decisions, supported by architectural diagrams and technical documentation for secure multi-account AWS environments.

### Cost

You are responsible for the cost of the AWS services used while running this solution. As of this revision, the cost for running the Universal Configuration with the Hub and Spoke networking model in its current form through the Landing Zone Accelerator on AWS with AWS Control Tower in the US East (N. Virginia) Region within a non-critical sandbox environment with no activity or workloads is approximately **$1,372.11 (USD)** each month. Costs for the Shared VPC model will be slightly lower. If you choose to deploy only the base configuration (Security, Governance, and Organization settings) without either networking model, the monthly cost will be significantly reduced.

We recommend creating a budget through AWS Cost Explorer to help manage costs. Prices are subject to change. For full details, refer to the pricing webpage for each AWS service used in this solution.

## Sample Cost Table

The following table provides a sample cost breakdown for deploying this solution with the default parameters in the US East (N. Virginia) Region, with no activity, for one month.

| AWS Service | Monthly Cost [USD] |
|-------------|-------------------|
| AWS Network Firewall | $587.76 |
| Amazon VPC | $458.53 |
| AWS Key Management Service | $79.03 |
| Amazon EC2-Other | $66.96 |
| AWS Security Hub | $62.99 |
| Amazon CloudWatch | $27.99 |
| Amazon Kinesis | $24.29 |
| AWS CloudTrail | $22.17 |
| Amazon Data Firehose | $11.43 |
| Amazon S3 | $10.55 |
| Amazon Macie | $6.01 |
| Amazon GuardDuty | $5.80 |
| Amazon SQS | $3.10 |
| AWS CodeBuild | $1.43 |
| AWS Secrets Manager | $1.31 |
| AWS CodePipeline | $1.20 |
| **Total** | **$1,372.11** |

> **Note:** The VPC calculation is done if you're utilizing a hub-and-spoke topology. Data transfer, Amazon DynamoDB, Amazon EC2-Instances, Amazon EventBridge, Amazon Location Service, Amazon SNS, AWS CloudFormation, AWS CodeArtifact, AWS Config, AWS Glue, AWS Lambda, AWS Service Catalog, AWS Step Functions, AWS Systems Manager, and Amazon Detective are priced at the Free Tier or less than $0.01 each month.



### Scripts and CI/CD Integration

Automation utilities for configuration management and environment setup, including account configuration generation and deployment helpers. The `.gitlab-ci.yml` file demonstrates how to integrate these configurations with CI/CD options for automated multi-environment deployments.

---

IMPORTANT

LZA Universal Configuration will not, by themselves, make you compliant. They offer an opinionated, best-practice approach to establishing a well-architected AWS multi-account environment from which additional complementary solutions can be integrated. The information is not exhaustive - you must review, evaluate, and approve the solution according to your organization's security requirements. You are responsible for determining applicable regulatory requirements and ensuring compliance. While this solution addresses technical and administrative requirements, it does not help with non-technical administrative compliance requirements.

---

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This project is licensed under the Apache-2.0 License.

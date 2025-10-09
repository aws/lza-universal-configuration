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

We recommend reviewing the documentation in order, starting with the Overview and Getting Started sections.

## Specific Regional and Industry Guidelines

For detailed information about supported regions and industry-specific configurations, including compliance frameworks, regulatory requirements, and implementation guidance, please refer to:

**[Support for Regions and Industries](https://docs.aws.amazon.com/solutions/latest/landing-zone-accelerator-on-aws/support-for-regions-and-industries.html)**

This comprehensive guide covers:

- Regional compliance requirements
- Industry-specific security controls and frameworks
- Regulatory compliance mappings

## What's Included

The LZA Universal Configuration provides ready-to-deploy configuration files and implementation guidance for LZA Universal Configuration baseline:

### Configuration Modules

Pre-configured LZA Universal Configuration files organized by the following deployment patterns:

- **[Base configurations](./modules/base/default)** - Security, Governance, and Organization settings
- **[Network configurations](./modules/network)** - Hub-and-spoke, and Shared VPC networking patterns

### Documentation

Architecture guides, deployment procedures, and detailed design principles that explain the implementation rationale and configuration decisions, supported by architectural diagrams and technical documentation for secure multi-account AWS environments.

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

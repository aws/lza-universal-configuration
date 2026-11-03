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

# Pydantic models of the Landing Zone Accelerator on AWS configuration schema
# (https://github.com/awslabs/landing-zone-accelerator-on-aws, Apache-2.0). The field descriptions
# are LZA's own documentation. Generated, and replaced as a unit when the pack moves to a new LZA
# release; edits made here by hand are lost at that point.
from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class AccountIdConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    account_id: Annotated[
        str,
        Field(
            alias="accountId",
            description='**AWS Account ID** *(Required)*\n\nThe 12-digit AWS account identifier for the existing account to be managed by the Landing Zone Accelerator.\n\n### Format Requirements\n\n- Must be exactly 12 digits\n- No hyphens, spaces, or other formatting\n- Must be a valid, existing AWS account ID\n- Account must be accessible to the organization\n\n### Validation Steps\n\n```yaml # Ensure this is a valid, accessible account ID accountId: "123456789012" ```\n\n### Security Considerations\n\n- Verify account ownership before mapping\n- Ensure account is not compromised or unauthorized\n- Review existing account resources and configurations\n- Consider impact of applying LZA policies to existing resources',
            max_length=12,
            min_length=12,
        ),
    ]
    email: Annotated[
        str,
        Field(
            description="**Account Owner Email** *(Required)*\n\nEmail address of the existing AWS account owner. Must match the email currently associated with the AWS account's root user.\n\n### Requirements\n\n- Must exactly match the existing account's root email\n- Will be used for account identification and management\n- Should follow organization's email conventions for consistency\n- Cannot be changed after mapping without account access issues\n\n### Verification Process\n\n```yaml # Verify this matches the account's actual root email email: production-workload@example.com ```",
            max_length=64,
            min_length=6,
            pattern="['^\\S+@\\S+\\.\\S+$', '^\\w+$']",
        ),
    ]


class AccountConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    account_alias: Annotated[
        str | None,
        Field(
            alias="accountAlias",
            description="**Account Alias** *(Optional)*\n\nHuman-readable identifier that replaces the 12-digit account ID in the AWS sign-in URL. This creates a more user-friendly sign-in experience for console access.\n\n### Format Requirements\n\n- **Length**: 3-63 characters\n- **Characters**: Lowercase letters (a-z), digits (0-9), and hyphens (-)\n- **Pattern**: Must match `^[a-z0-9]([a-z0-9]|-(?!-)){1,61}[a-z0-9]$`\n- **Uniqueness**: Must be globally unique within the AWS partition\n- **Cannot**: Start or end with hyphen, contain consecutive hyphens\n\n### Sign-in URL Format\n\nInstead of: `https://123456789012.signin.aws.amazon.com/console` Users get: `https://my-prod-account.signin.aws.amazon.com/console`\n\n### Naming Best Practices\n\n```yaml # Environment-based aliases accountAlias: company-prod-workloads accountAlias: company-dev-sandbox accountAlias: company-staging-env\n\n# Function-based aliases accountAlias: company-shared-services accountAlias: company-security-tools accountAlias: company-log-archive\n\n# Team-based aliases accountAlias: platform-team-prod accountAlias: data-team-analytics ```\n\n### Considerations\n\n- Choose aliases that won't need to change as the organization evolves\n- Include company/organization prefix to avoid global conflicts\n- Keep aliases short but descriptive\n- Document alias patterns for consistency across accounts\n\n**Note:** Account aliases cannot be changed after creation, so choose carefully.",
            min_length=1,
            pattern="^[^\\s]*$",
        ),
    ] = None
    description: Annotated[
        str | None,
        Field(
            description='**Account Description** *(Optional)*\n\nHuman-readable description explaining the account\'s purpose, ownership, and usage. This field helps with documentation and governance but is not used during account creation.\n\n### Best Practices\n\n- Include the account\'s primary purpose\n- Mention the owning team or business unit\n- Note any special compliance or security requirements\n- Keep descriptions concise but informative\n\n### Examples\n\n```yaml description: "Production workloads for customer-facing applications" description: "Development and testing environment for Platform team" description: "Shared networking services and connectivity hub" description: "Security tooling and compliance monitoring (SOC2 compliant)" ```',
            min_length=1,
        ),
    ] = None
    email: Annotated[
        str,
        Field(
            description="**Account Email Address** *(Required)*\n\nPrimary email address for the AWS account owner. This email must be unique across all AWS accounts and will receive account-related notifications, billing information, and security alerts.\n\n### Email Requirements (AWS Enforced)\n\n- **Length**: 6-64 characters\n- **Format**: Valid RFC 5322 email format\n- **Characters**: 7-bit ASCII only\n- **Uniqueness**: Must not be associated with any existing AWS account\n- **Domain**: Must contain at least one dot in the domain portion\n\n### Character Restrictions\n\n**Local part (before",
            max_length=64,
            min_length=6,
            pattern="['^\\S+@\\S+\\.\\S+$', '^\\w+$']",
        ),
    ]
    name: Annotated[
        str,
        Field(
            description="**Account Name** *(Required)*\n\nUnique identifier for the account within the Landing Zone Accelerator configuration. This name is used to reference the account across all configuration files and becomes the AWS account name when creating new accounts.\n\n### Naming Requirements\n\n- Must be unique within the accounts configuration\n- No spaces or special characters allowed\n- Use descriptive, kebab-case naming (e.g., `prod-workload`, `dev-sandbox`)\n- Should reflect the account's business purpose\n\n### Usage Examples\n\n```yaml # Good examples name: prod-workload name: dev-environment name: shared-services name: security-tooling\n\n# Avoid name: \"Account 1\"        # Contains spaces name: prod_workload      # Use hyphens, not underscores name: account123         # Not descriptive ```\n\n**Note:** For pre-existing accounts, this name doesn't need to match the current AWS account name.",
            min_length=1,
            pattern="^[^\\s]*$",
        ),
    ]
    organizational_unit: Annotated[
        str | None,
        Field(
            alias="organizationalUnit",
            description="**Organizational Unit** *(Optional)*\n\nName of the Organizational Unit (OU) where this account will be placed within AWS Organizations. The OU determines which Service Control Policies (SCPs) and governance controls apply to the account.\n\n### Requirements\n\n- Must match an OU name defined in `organization-config.yaml`\n- OU must exist or be created before account placement\n- Affects policy inheritance and governance controls\n\n### Common Organizational Unit Patterns\n\n```yaml # By environment organizationalUnit: Production organizationalUnit: Development organizationalUnit: Sandbox\n\n# By function organizationalUnit: Workloads organizationalUnit: Security organizationalUnit: Infrastructure organizationalUnit: Shared-Services\n\n# By business unit organizationalUnit: Engineering organizationalUnit: Marketing organizationalUnit: Finance ```\n\n### Security Considerations\n\n- Production accounts should be in OUs with restrictive SCPs\n- Development accounts may have more permissive policies\n- Security accounts often have specialized compliance policies\n- Consider data classification and compliance requirements",
            min_length=1,
        ),
    ] = None
    warm: Annotated[
        bool | None,
        Field(
            description="**Account Warming** *(Optional)*\n\nPre-provision the account by creating a temporary EC2 instance that runs for 15 minutes. This prepares the account's EC2 service for immediate production workload deployment.\n\n### When to Enable\n\n- **Enable** for accounts that will immediately deploy EC2-based workloads\n- **Enable** for production accounts requiring rapid deployment capabilities\n- **Disable** for accounts primarily using serverless or managed services\n- **Disable** for cost-sensitive development/testing environments\n\n### Process Details\n\n- Warming occurs during the operations stack deployment phase\n- Creates a minimal EC2 instance in the default VPC\n- Instance automatically terminates after 15 minutes\n- No additional charges beyond the brief EC2 usage\n- Can be safely removed from configuration after initial deployment\n\n### Best Practices\n\n```yaml # Production accounts - enable warming warm: true\n\n# Development/testing - typically disable warm: false\n\n# Serverless-only accounts - disable warm: false ```"
        ),
    ] = False


class GovCloudAccountConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    account_alias: Annotated[
        str | None,
        Field(
            alias="accountAlias",
            description="**Account Alias** *(Optional)*\n\nHuman-readable identifier that replaces the 12-digit account ID in the AWS sign-in URL. This creates a more user-friendly sign-in experience for console access.\n\n### Format Requirements\n\n- **Length**: 3-63 characters\n- **Characters**: Lowercase letters (a-z), digits (0-9), and hyphens (-)\n- **Pattern**: Must match `^[a-z0-9]([a-z0-9]|-(?!-)){1,61}[a-z0-9]$`\n- **Uniqueness**: Must be globally unique within the AWS partition\n- **Cannot**: Start or end with hyphen, contain consecutive hyphens\n\n### Sign-in URL Format\n\nInstead of: `https://123456789012.signin.aws.amazon.com/console` Users get: `https://my-prod-account.signin.aws.amazon.com/console`\n\n### Naming Best Practices\n\n```yaml # Environment-based aliases accountAlias: company-prod-workloads accountAlias: company-dev-sandbox accountAlias: company-staging-env\n\n# Function-based aliases accountAlias: company-shared-services accountAlias: company-security-tools accountAlias: company-log-archive\n\n# Team-based aliases accountAlias: platform-team-prod accountAlias: data-team-analytics ```\n\n### Considerations\n\n- Choose aliases that won't need to change as the organization evolves\n- Include company/organization prefix to avoid global conflicts\n- Keep aliases short but descriptive\n- Document alias patterns for consistency across accounts\n\n**Note:** Account aliases cannot be changed after creation, so choose carefully.",
            min_length=1,
            pattern="^[^\\s]*$",
        ),
    ] = None
    description: Annotated[
        str | None,
        Field(
            description='**Account Description** *(Optional)*\n\nHuman-readable description explaining the account\'s purpose, ownership, and usage. This field helps with documentation and governance but is not used during account creation.\n\n### Best Practices\n\n- Include the account\'s primary purpose\n- Mention the owning team or business unit\n- Note any special compliance or security requirements\n- Keep descriptions concise but informative\n\n### Examples\n\n```yaml description: "Production workloads for customer-facing applications" description: "Development and testing environment for Platform team" description: "Shared networking services and connectivity hub" description: "Security tooling and compliance monitoring (SOC2 compliant)" ```',
            min_length=1,
        ),
    ] = None
    email: Annotated[
        str,
        Field(
            description="**Account Email Address** *(Required)*\n\nPrimary email address for the AWS account owner. This email must be unique across all AWS accounts and will receive account-related notifications, billing information, and security alerts.\n\n### Email Requirements (AWS Enforced)\n\n- **Length**: 6-64 characters\n- **Format**: Valid RFC 5322 email format\n- **Characters**: 7-bit ASCII only\n- **Uniqueness**: Must not be associated with any existing AWS account\n- **Domain**: Must contain at least one dot in the domain portion\n\n### Character Restrictions\n\n**Local part (before",
            max_length=64,
            min_length=6,
            pattern="['^\\S+@\\S+\\.\\S+$', '^\\w+$']",
        ),
    ]
    enable_gov_cloud: Annotated[
        bool | None,
        Field(
            alias="enableGovCloud",
            description="**Enable GovCloud Account Creation** *(Optional)*\n\nControls whether a GovCloud partition account should be created alongside the standard commercial partition account. When enabled, creates a linked account pair across both AWS partitions.\n\n### When to Enable\n\n- **Enable** for workloads requiring FedRAMP compliance\n- **Enable** for government agency workloads\n- **Enable** for regulated industries requiring GovCloud\n- **Disable** for standard commercial workloads\n\n### Account Linking\n\n- Creates paired accounts in both GovCloud and commercial partitions\n- Maintains separate identity and access management per partition\n- Requires separate email addresses for each partition account\n\n### Compliance Benefits\n\n```yaml # Government agency deployment enableGovCloud: true    # Creates GovCloud + commercial account pair\n\n# Commercial deployment only enableGovCloud: false   # Creates only commercial partition account ```",
        ),
    ] = False
    name: Annotated[
        str,
        Field(
            description="**Account Name** *(Required)*\n\nUnique identifier for the account within the Landing Zone Accelerator configuration. This name is used to reference the account across all configuration files and becomes the AWS account name when creating new accounts.\n\n### Naming Requirements\n\n- Must be unique within the accounts configuration\n- No spaces or special characters allowed\n- Use descriptive, kebab-case naming (e.g., `prod-workload`, `dev-sandbox`)\n- Should reflect the account's business purpose\n\n### Usage Examples\n\n```yaml # Good examples name: prod-workload name: dev-environment name: shared-services name: security-tooling\n\n# Avoid name: \"Account 1\"        # Contains spaces name: prod_workload      # Use hyphens, not underscores name: account123         # Not descriptive ```\n\n**Note:** For pre-existing accounts, this name doesn't need to match the current AWS account name.",
            min_length=1,
            pattern="^[^\\s]*$",
        ),
    ]
    organizational_unit: Annotated[
        str | None,
        Field(
            alias="organizationalUnit",
            description="**Organizational Unit** *(Optional)*\n\nName of the Organizational Unit (OU) where this account will be placed within AWS Organizations. The OU determines which Service Control Policies (SCPs) and governance controls apply to the account.\n\n### Requirements\n\n- Must match an OU name defined in `organization-config.yaml`\n- OU must exist or be created before account placement\n- Affects policy inheritance and governance controls\n\n### Common Organizational Unit Patterns\n\n```yaml # By environment organizationalUnit: Production organizationalUnit: Development organizationalUnit: Sandbox\n\n# By function organizationalUnit: Workloads organizationalUnit: Security organizationalUnit: Infrastructure organizationalUnit: Shared-Services\n\n# By business unit organizationalUnit: Engineering organizationalUnit: Marketing organizationalUnit: Finance ```\n\n### Security Considerations\n\n- Production accounts should be in OUs with restrictive SCPs\n- Development accounts may have more permissive policies\n- Security accounts often have specialized compliance policies\n- Consider data classification and compliance requirements",
            min_length=1,
        ),
    ] = None
    warm: Annotated[
        bool | None,
        Field(
            description="**Account Warming** *(Optional)*\n\nPre-provision the account by creating a temporary EC2 instance that runs for 15 minutes. This prepares the account's EC2 service for immediate production workload deployment in the GovCloud partition.\n\n### GovCloud Warming Considerations\n\n- Warming occurs in the GovCloud partition specifically\n- May take longer due to additional GovCloud provisioning requirements\n- Helps establish baseline EC2 service readiness for compliance workloads\n- Particularly beneficial for time-sensitive government deployments\n\n### Best Practices\n\n```yaml # Critical government workloads - enable warming warm: true\n\n# Development/testing in GovCloud - typically disable warm: false\n\n# Serverless-only GovCloud accounts - disable warm: false ```"
        ),
    ] = False


class AccountsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    account_ids: Annotated[
        list[AccountIdConfig] | None,
        Field(
            alias="accountIds",
            description="**Pre-existing Account IDs (Optional)**\n\nMap existing AWS accounts IDs to email addresses to skip dynamic lookups by the Landing Zone Accelerator. Use this section when you have existing accounts that need to be managed by the accelerator.\n\n**Use Cases:**\n- Migrating existing AWS accounts into the Landing Zone Accelerator\n- Integrating with accounts created outside the accelerator\n- Mapping legacy account structures",
        ),
    ] = None
    mandatory_accounts: Annotated[
        list[AccountConfig] | list[GovCloudAccountConfig],
        Field(
            alias="mandatoryAccounts",
            description="**Mandatory Accounts Configuration**\n\nRequired accounts that provide core Landing Zone Accelerator functionality. These accounts are essential for security, compliance, and operational management.\n\n**Required Accounts:**\n- `Management`: Primary account for organizational management and billing\n- `LogArchive`: Centralized logging and log retention account\n- `Audit`: Security auditing and compliance account",
        ),
    ]
    workload_accounts: Annotated[
        list[AccountConfig] | list[GovCloudAccountConfig],
        Field(
            alias="workloadAccounts",
            description="**Workload Accounts Configuration**\n\nApplication-specific and business workload accounts. These accounts host your applications, databases, and other business workloads, isolated by environment, business unit, or application.\n\n**Common Workload Account Types:**\n- Production environments\n- Development/testing environments\n- Shared services (networking, monitoring)\n- Business unit specific accounts\n- Sandbox accounts for experimentation",
        ),
    ]


type Model = AccountsConfig

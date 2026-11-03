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

from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class AssumedByType(StrEnum):
    service = "service"
    account = "account"
    principal_arn = "principalArn"
    provider = "provider"


class ActiveDirectoryPasswordPolicyConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    complexity: Annotated[bool, Field(description="Whether password complexity requirements are enforced.")]
    failed_attempts: Annotated[float, Field(alias="failedAttempts", description="Number of failed login attempts before the account is locked out.")]
    history: Annotated[float, Field(description="Number of previous passwords to remember and prevent reuse.")]
    lockout_attempts_reset: Annotated[
        float, Field(alias="lockoutAttemptsReset", description="Time in minutes after which the failed login attempt counter is reset.")
    ]
    lockout_duration: Annotated[float, Field(alias="lockoutDuration", description="Account lockout duration in minutes.")]
    maximum_age: Annotated[float, Field(alias="maximumAge", description="Maximum password age in days before users must change their password.")]
    minimum_age: Annotated[float, Field(alias="minimumAge", description="Minimum password age in days before users can change their password again.")]
    minimum_length: Annotated[float, Field(alias="minimumLength", description="Minimum password length in characters.")]
    reversible: Annotated[bool, Field(description="Whether passwords can be stored using reversible encryption.")]


class DeploymentTargets(BaseModel):
    model_config = ConfigDict(extra="forbid")
    accounts: Annotated[
        list[str] | None,
        Field(
            description="**Target Accounts** *(Optional)*\n\nList of specific account names where resources should be deployed. Use for precise account-level targeting."
        ),
    ] = None
    excluded_accounts: Annotated[
        list[str] | None,
        Field(
            alias="excludedAccounts",
            description="**Excluded Accounts** *(Optional)*\n\nList of account names to exclude from deployment. Takes precedence over organizational unit and account inclusions.",
        ),
    ] = None
    excluded_regions: Annotated[
        list[str] | None,
        Field(
            alias="excludedRegions",
            description="**Excluded Regions** *(Optional)*\n\nList of AWS regions to exclude from deployment. Useful for compliance requirements or cost optimization.",
        ),
    ] = None
    organizational_units: Annotated[
        list[str] | None,
        Field(
            alias="organizationalUnits",
            description="**Organizational Units** *(Optional)*\n\nList of organizational unit names where resources should be deployed. When specified, resources will be created in all accounts within these OUs.",
        ),
    ] = None


class Edition(StrEnum):
    standard = "Standard"
    enterprise = "Enterprise"


type NonEmptyString = Annotated[
    str,
    Field(
        description="## Non-Empty String Type\n\nRepresents a string that must contain at least one character. Used for required text fields throughout the Landing Zone Accelerator configuration where empty values are not permitted.\n\n```",
        min_length=1,
    ),
]


class PrincipalType(StrEnum):
    user = "USER"
    group = "GROUP"


class ActiveDirectoryConfigurationInstanceUserDataConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    script_file_path: Annotated[
        str, Field(alias="scriptFilePath", description="The file path to the PowerShell script in your configuration repository.", min_length=1)
    ]
    script_name: Annotated[
        str, Field(alias="scriptName", description="A descriptive name for the PowerShell script that will be executed.", min_length=1)
    ]


class ActiveDirectoryUserConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: Annotated[str, Field(description="The email address for the Active Directory user account.", min_length=1)]
    groups: Annotated[list[NonEmptyString], Field(description="List of Active Directory groups that this user should be added to.")]
    name: Annotated[str, Field(description="The username for the Active Directory user account.", min_length=1)]


class AssumeRoleConditionConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    key: Annotated[str, Field(description="The IAM condition key (e.g., sts:ExternalId, aws:PrincipalArn).", min_length=1)]
    type: Annotated[str, Field(description="The IAM condition operator (e.g., StringEquals, StringLike, ArnLike, IpAddress).", min_length=1)]
    values: Annotated[list[NonEmptyString], Field(description="One or more values for the condition key.")]


class AssumedByConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    conditions: Annotated[
        list[AssumeRoleConditionConfig] | None, Field(description="Optional conditions applied to this principal in the role trust policy.")
    ] = None
    principal: Annotated[
        str | None, Field(description="The principal identifier that can assume this role. The format depends on the type specified.", min_length=1)
    ] = None
    type: Annotated[AssumedByType, Field(description="The type of principal that can assume this role.")]


class CustomerManagedPolicyReferenceConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: Annotated[str, Field(description="The name of the customer managed IAM policy to use as a permissions boundary.", min_length=1)]
    path: Annotated[
        str | None,
        Field(
            description="The path to the IAM policy that you have configured in each account where you want to deploy your permission set.",
            min_length=1,
        ),
    ] = None


class IdentityCenterAssignmentPrincipalConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: Annotated[str, Field(description="The name of the principal from your identity source.", min_length=1)]
    type: Annotated[str, Field(description="The type of principal being specified.", min_length=1)]


class ManagedActiveDirectoryLogConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    group_name: Annotated[
        str, Field(alias="groupName", description="The name of the CloudWatch log group that will receive directory security logs.", min_length=1)
    ]
    retention_in_days: Annotated[
        float | None, Field(alias="retentionInDays", description="The number of days to retain log events in the CloudWatch log group.")
    ] = None


class ManagedActiveDirectorySecretConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    account: Annotated[str | None, Field(description="The AWS account where the administrator secret will be stored.", min_length=1)] = None
    admin_secret_name: Annotated[
        str | None, Field(alias="adminSecretName", description="The name for the administrator secret in AWS Secrets Manager.", min_length=1)
    ] = None
    region: Annotated[str | None, Field(description="The AWS region where the administrator secret will be stored.")] = None


class ManagedActiveDirectorySharedOuConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    excluded_accounts: Annotated[
        list[NonEmptyString] | None,
        Field(
            alias="excludedAccounts",
            description="List of AWS account names that should be excluded from directory sharing, even if they are in the specified organizational units.",
        ),
    ] = None
    organizational_units: Annotated[
        list[NonEmptyString],
        Field(alias="organizationalUnits", description="List of organizational unit names that should have access to the managed Active Directory."),
    ]


class ManagedActiveDirectoryVpcSettingsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    subnets: Annotated[list[NonEmptyString], Field(description="List of subnet names where the directory domain controllers will be deployed.")]
    vpc_name: Annotated[
        str, Field(alias="vpcName", description="The logical name of the VPC where the managed Active Directory will be deployed.", min_length=1)
    ]


class PermissionsBoundaryConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    aws_managed_policy_name: Annotated[
        str | None,
        Field(alias="awsManagedPolicyName", description="The name of an AWS managed policy to use as the permissions boundary.", min_length=1),
    ] = None
    customer_managed_policy: Annotated[
        CustomerManagedPolicyReferenceConfig | None,
        Field(
            alias="customerManagedPolicy",
            description="Configuration for a customer managed policy to use as the permissions boundary. This specifies the name and path of a customer managed policy.",
        ),
    ] = None


class PoliciesConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    aws_managed: Annotated[
        list[NonEmptyString] | None,
        Field(alias="awsManaged", description="List of AWS managed policies to attach. Values can be policy ARNs or policy names."),
    ] = None
    customer_managed: Annotated[
        list[NonEmptyString] | None, Field(alias="customerManaged", description="List of customer managed policy names to attach.")
    ] = None


class PolicyConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: Annotated[
        str,
        Field(description="The logical name for this managed policy resource. This name will be used as the policy name in AWS IAM.", min_length=1),
    ]
    policy: Annotated[str, Field(description="Path to a JSON file containing the IAM policy document.", min_length=1)]


class PolicySetConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    deployment_targets: Annotated[
        DeploymentTargets,
        Field(alias="deploymentTargets", description="Specifies the AWS accounts and/or organizational units where these policies will be created."),
    ]
    identity_center_dependency: Annotated[
        bool | None,
        Field(
            alias="identityCenterDependency",
            description="Indicates whether these policies are used in AWS Identity Center permission set assignments.",
        ),
    ] = False
    policies: Annotated[list[PolicyConfig], Field(description="List of IAM managed policies to create in the targeted accounts.")]


class RoleConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    assumed_by: Annotated[
        list[AssumedByConfig],
        Field(alias="assumedBy", description="List of principals that can assume this role and their trust relationship configuration."),
    ]
    boundary_policy: Annotated[
        str | None,
        Field(alias="boundaryPolicy", description="The name of an IAM managed policy to use as a permissions boundary for this role.", min_length=1),
    ] = None
    external_ids: Annotated[
        list[NonEmptyString] | None, Field(alias="externalIds", description="List of external IDs that must be provided when assuming this role.")
    ] = None
    instance_profile: Annotated[
        bool | None, Field(alias="instanceProfile", description="Specifies whether to create an EC2 instance profile for this role.")
    ] = False
    max_session_duration: Annotated[
        float | None, Field(alias="maxSessionDuration", description="The maximum session duration (in seconds) that you want to set for the role.")
    ] = None
    name: Annotated[
        str,
        Field(
            description="The logical name for this IAM role. This name will be used as the role name in AWS IAM and can be referenced by other AWS resources and services.",
            min_length=1,
        ),
    ]
    policies: Annotated[
        PoliciesConfig | None, Field(description="IAM policies to attach to this role, providing the permissions the role will have when assumed.")
    ] = None


class RoleSetConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    deployment_targets: Annotated[
        DeploymentTargets,
        Field(alias="deploymentTargets", description="Specifies the AWS accounts and/or organizational units where these roles will be created."),
    ]
    path: Annotated[str | None, Field(description="The path for all roles in this set.", min_length=1)] = None
    roles: Annotated[list[RoleConfig], Field(description="List of IAM roles to create in the targeted accounts.")]


class SamlProviderConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    metadata_document: Annotated[
        str,
        Field(
            alias="metadataDocument",
            description="The SAML metadata document XML file containing the identity provider's configuration.",
            min_length=1,
        ),
    ]
    name: Annotated[
        str,
        Field(
            description="The logical name for this SAML identity provider. This name will be used to reference the provider in IAM role trust policies and other AWS configurations.",
            min_length=1,
        ),
    ]


class UserConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    boundary_policy: Annotated[
        str | None,
        Field(alias="boundaryPolicy", description="The name of an IAM managed policy to use as a permissions boundary for this user.", min_length=1),
    ] = None
    disable_console_access: Annotated[
        bool | None,
        Field(alias="disableConsoleAccess", description="Controls whether the user can access the AWS Management Console with a password."),
    ] = None
    group: Annotated[
        str,
        Field(
            description="The name of the IAM group to add this user to. The group must be defined in the same deployment target scope as this user.",
            min_length=1,
        ),
    ]
    username: Annotated[
        str,
        Field(
            description="The name for the IAM user. This will be the user's sign-in name for the AWS Management Console and the name used in API calls.",
            min_length=1,
        ),
    ]


class UserSetConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    deployment_targets: Annotated[
        DeploymentTargets,
        Field(alias="deploymentTargets", description="Specifies the AWS accounts and/or organizational units where these users will be created."),
    ]
    users: Annotated[list[UserConfig], Field(description="List of IAM users to create in the targeted accounts.")]


class ActiveDirectoryConfigurationInstanceConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ad_connector_group: Annotated[
        str,
        Field(
            alias="adConnectorGroup",
            description="The name of the Active Directory group that will be used for AWS Directory Service connector permissions.",
            min_length=1,
        ),
    ]
    ad_groups: Annotated[
        list[NonEmptyString], Field(alias="adGroups", description="List of Active Directory security groups to create in the managed directory.")
    ]
    ad_password_policy: Annotated[
        ActiveDirectoryPasswordPolicyConfig,
        Field(alias="adPasswordPolicy", description="Password policy configuration for the managed Active Directory domain."),
    ]
    ad_per_account_groups: Annotated[
        list[NonEmptyString], Field(alias="adPerAccountGroups", description="List of per-account Active Directory groups to create.")
    ]
    ad_users: Annotated[
        list[ActiveDirectoryUserConfig], Field(alias="adUsers", description="List of Active Directory users to create in the managed directory.")
    ]
    enable_termination_protection: Annotated[
        bool | None,
        Field(alias="enableTerminationProtection", description="Whether to enable termination protection for the configuration instance."),
    ] = False
    image_path: Annotated[
        str, Field(alias="imagePath", description="The path to the Amazon Machine Image (AMI) for the Windows instance.", min_length=1)
    ]
    instance_role: Annotated[
        str, Field(alias="instanceRole", description="The name of the IAM role to attach to the configuration instance.", min_length=1)
    ]
    instance_type: Annotated[
        str, Field(alias="instanceType", description="The EC2 instance type for the Active Directory configuration instance.", min_length=1)
    ]
    security_group_inbound_sources: Annotated[
        list[NonEmptyString],
        Field(
            alias="securityGroupInboundSources",
            description="List of CIDR blocks or IP addresses that are allowed inbound access to the configuration instance.",
        ),
    ]
    subnet_name: Annotated[
        str, Field(alias="subnetName", description="The logical name of the subnet where the configuration instance will be deployed.", min_length=1)
    ]
    user_data_scripts: Annotated[
        list[ActiveDirectoryConfigurationInstanceUserDataConfig],
        Field(
            alias="userDataScripts",
            description="List of PowerShell scripts that will be executed on the configuration instance to set up the Active Directory environment.",
        ),
    ]
    vpc_name: Annotated[
        str, Field(alias="vpcName", description="The logical name of the VPC where the configuration instance will be deployed.", min_length=1)
    ]


class GroupConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: Annotated[
        str,
        Field(
            description="The logical name for this IAM group. This name will be used as the group name in AWS IAM and can be referenced when assigning users to groups.",
            min_length=1,
        ),
    ]
    policies: Annotated[
        PoliciesConfig | None, Field(description="IAM policies to attach to this group, defining the permissions that group members will inherit.")
    ] = None


class GroupSetConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    deployment_targets: Annotated[
        DeploymentTargets,
        Field(alias="deploymentTargets", description="Specifies the AWS accounts and/or organizational units where these groups will be created."),
    ]
    groups: Annotated[list[GroupConfig], Field(description="List of IAM groups to create in the targeted accounts.")]


class IdentityCenterAssignmentConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    deployment_targets: Annotated[
        DeploymentTargets,
        Field(alias="deploymentTargets", description="Specifies the AWS accounts and/or organizational units where this assignment will be created."),
    ]
    name: Annotated[str, Field(description="The logical name for this assignment configuration.", min_length=1)]
    permission_set_name: Annotated[
        str, Field(alias="permissionSetName", description="The name of the permission set to assign to the principals.", min_length=1)
    ]
    principal_id: Annotated[
        str | None,
        Field(
            alias="principalId",
            deprecated="This property is deprecated and will be removed in a future version. Use the `principals`\nproperty instead to specify principal names, which provides better maintainability and\nreadability.",
            description="The unique identifier of the principal (user or group) to grant access to.",
            min_length=1,
        ),
    ] = None
    principal_type: Annotated[
        PrincipalType | None,
        Field(
            alias="principalType",
            deprecated="This property is deprecated and will be removed in a future version. Use the `principals`\nproperty instead to specify both principal type and name in a more maintainable format.",
            description="The type of principal being granted access.",
        ),
    ] = None
    principals: Annotated[
        list[IdentityCenterAssignmentPrincipalConfig] | None,
        Field(description="List of principals (users or groups) to grant access to the specified AWS accounts."),
    ] = None


class IdentityCenterPoliciesConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    accelerator_managed: Annotated[
        list[NonEmptyString] | None,
        Field(alias="acceleratorManaged", description="List of accelerator-managed policy names to attach to this permission set."),
    ] = None
    aws_managed: Annotated[
        list[NonEmptyString] | None, Field(alias="awsManaged", description="List of AWS managed policies to attach to this permission set.")
    ] = None
    customer_managed: Annotated[
        list[NonEmptyString] | None,
        Field(alias="customerManaged", description="List of customer managed policy names to attach to this permission set."),
    ] = None
    inline_policy: Annotated[
        str | None,
        Field(
            alias="inlinePolicy", description="Path to a JSON file containing an inline policy to embed directly in the permission set.", min_length=1
        ),
    ] = None
    permissions_boundary: Annotated[
        PermissionsBoundaryConfig | None,
        Field(alias="permissionsBoundary", description="Permissions boundary configuration to set the maximum permissions for this permission set."),
    ] = None


class ManagedActiveDirectoryConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    account: Annotated[str, Field(description="The AWS account where the managed Active Directory will be deployed.", min_length=1)]
    active_directory_configuration_instance: Annotated[
        ActiveDirectoryConfigurationInstanceConfig | None,
        Field(
            alias="activeDirectoryConfigurationInstance",
            description="Configuration for an EC2 instance that will automatically configure users, groups, and organizational units in the managed Active Directory.",
        ),
    ] = None
    description: Annotated[str | None, Field(description="A human-readable description of the managed Active Directory.", min_length=1)] = None
    dns_name: Annotated[
        str, Field(alias="dnsName", description="The fully qualified domain name (FQDN) for the managed Active Directory.", min_length=1)
    ]
    edition: Annotated[Edition, Field(description="The edition of AWS Managed Microsoft AD to deploy.")]
    logs: Annotated[ManagedActiveDirectoryLogConfig | None, Field(description="Configuration for directory logging to Amazon CloudWatch Logs.")] = (
        None
    )
    name: Annotated[str, Field(description="The logical name for this managed Active Directory instance.", min_length=1)]
    net_bios_domain_name: Annotated[
        str, Field(alias="netBiosDomainName", description="The NetBIOS name for the Active Directory domain.", min_length=1)
    ]
    region: Annotated[str, Field(description="The AWS region where the managed Active Directory will be deployed.")]
    resolver_rule_name: Annotated[
        str | None,
        Field(
            alias="resolverRuleName",
            description="The name of a Route 53 resolver rule to update with the directory's DNS server IP addresses.\n\nThis property updates an existing FORWARD rule; it does not create one. The referenced rule must already be created with a target, so you must seed its `targetIps` with at least one placeholder IP address in network-config.yaml. On deployment, the accelerator replaces those placeholder IPs with the directory's DNS server IPs (the DNS port is read from the existing target entry). A FORWARD rule defined with no target fails network configuration validation.",
            min_length=1,
        ),
    ] = None
    secret_config: Annotated[
        ManagedActiveDirectorySecretConfig | None,
        Field(alias="secretConfig", description="Configuration for storing the directory administrator credentials in AWS Secrets Manager."),
    ] = None
    shared_accounts: Annotated[
        list[NonEmptyString] | None, Field(alias="sharedAccounts", description="List of AWS account names to share the directory with directly.")
    ] = None
    shared_organizational_units: Annotated[
        ManagedActiveDirectorySharedOuConfig | None,
        Field(alias="sharedOrganizationalUnits", description="Configuration for sharing the directory with other AWS accounts in your organization."),
    ] = None
    vpc_settings: Annotated[
        ManagedActiveDirectoryVpcSettingsConfig,
        Field(alias="vpcSettings", description="VPC configuration specifying where the managed Active Directory will be deployed."),
    ]


class IdentityCenterPermissionSetConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    description: Annotated[
        str | None, Field(description="A human-readable description of what this permission set is intended for.", min_length=1)
    ] = None
    name: Annotated[
        str,
        Field(
            description="The name for this permission set configuration. This name will be used to reference the permission set in Identity Center assignments and will be visible to users in the AWS access portal.",
            min_length=1,
        ),
    ]
    policies: Annotated[
        IdentityCenterPoliciesConfig | None, Field(description="The policy config that define the permissions for this permission set.")
    ] = None
    session_duration: Annotated[
        float | None,
        Field(alias="sessionDuration", description="The length of time (in minutes) that users can stay signed in to their AWS session."),
    ] = None


class IdentityCenterConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    delegated_admin_account: Annotated[
        str | None,
        Field(
            alias="delegatedAdminAccount",
            description="The AWS account that will serve as the delegated administrator for Identity Center operations. This serves as an override for the Delegated Admin account.",
            min_length=1,
        ),
    ] = None
    identity_center_assignments: Annotated[
        list[IdentityCenterAssignmentConfig] | None,
        Field(
            alias="identityCenterAssignments",
            description="List of assignments that grant users or groups access to AWS accounts using permission sets.\nAssignments determine which users can access which accounts with what level of permissions.",
        ),
    ] = None
    identity_center_permission_sets: Annotated[
        list[IdentityCenterPermissionSetConfig] | None,
        Field(
            alias="identityCenterPermissionSets",
            description="List of permission sets to create in AWS Identity Center. Permission sets define collections of\npolicies that determine what actions users can perform when they access AWS accounts.",
        ),
    ] = None
    name: Annotated[
        str,
        Field(
            description="The logical name for this Identity Center configuration. This name is used to reference this Identity Center instance in other accelerator configurations.",
            min_length=1,
        ),
    ]


class IamConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    group_sets: Annotated[list[GroupSetConfig] | None, Field(alias="groupSets", description="IAM group sets configuration.")] = None
    home_region: Annotated[
        str | None, Field(alias="homeRegion", description="The primary AWS region where global IAM resources will be managed and deployed.")
    ] = None
    identity_center: Annotated[
        IdentityCenterConfig | None,
        Field(
            alias="identityCenter",
            description="AWS Identity Center (successor to AWS Single Sign-On) helps you securely create or connect\nyour workforce identities and manage their access centrally across AWS accounts and applications.\nIdentity Center provides a unified administration experience to define, customize, and assign\nfine-grained permissions.",
        ),
    ] = None
    managed_active_directories: Annotated[
        list[ManagedActiveDirectoryConfig] | None,
        Field(
            alias="managedActiveDirectories",
            description="AWS Managed Microsoft AD creates a fully managed Microsoft Active Directory in the AWS Cloud.\nIt enables you to run directory-aware workloads in AWS, including Microsoft SharePoint,\nMicrosoft SQL Server Always On Availability Groups, and .NET applications.",
        ),
    ] = None
    policy_sets: Annotated[list[PolicySetConfig] | None, Field(alias="policySets", description="IAM managed policy sets configuration.")] = None
    providers: Annotated[list[SamlProviderConfig] | None, Field(description="SAML identity provider configuration for federated access to AWS.")] = (
        None
    )
    role_sets: Annotated[list[RoleSetConfig] | None, Field(alias="roleSets", description="Role sets configuration")] = None
    user_sets: Annotated[list[UserSetConfig] | None, Field(alias="userSets", description="IAM user sets configuration.")] = None


type Model = IamConfig

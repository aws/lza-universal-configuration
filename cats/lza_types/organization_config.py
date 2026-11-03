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


class Strategy(StrEnum):
    deny_list = "deny-list"
    allow_list = "allow-list"


class Type(StrEnum):
    aws_managed = "awsManaged"
    customer_managed = "customerManaged"


class OrganizationalUnit(BaseModel):
    model_config = ConfigDict(extra="forbid")
    arn: Annotated[
        str | None,
        Field(
            alias="Arn",
            description='<p>The Amazon Resource Name (ARN) of this OU.</p>          <p>For more information about ARNs in Organizations, see <a href="https://docs.aws.amazon.com/service-authorization/latest/reference/list_awsorganizations.html#awsorganizations-resources-for-iam-policies">ARN     Formats Supported by Organizations</a> in the <i>Amazon Web Services Service Authorization Reference</i>.</p>',
        ),
    ] = None
    id: Annotated[
        str | None,
        Field(
            alias="Id",
            description='<p>The unique identifier (ID) associated with this OU. The ID is unique to the             organization only.</p>          <p>The <a href="http://wikipedia.org/wiki/regex">regex pattern</a> for an organizational unit ID string requires     "ou-" followed by from 4 to 32 lowercase letters or digits (the ID of the root that contains the     OU). This string is followed by a second "-" dash and from 8 to 32 additional lowercase letters     or digits.</p>',
        ),
    ] = None
    name: Annotated[
        str | None,
        Field(
            alias="Name",
            description='<p>The friendly name of this OU.</p>          <p>The <a href="http://wikipedia.org/wiki/regex">regex pattern</a>     that is used to validate this parameter is a string of any of the characters in the ASCII     character range.</p>',
        ),
    ] = None
    path: Annotated[str | None, Field(alias="Path", description="<p>The path in the organization where this OU exists.</p>")] = None


class PolicyType(StrEnum):
    aiservices_opt_out_policy = "AISERVICES_OPT_OUT_POLICY"
    backup_policy = "BACKUP_POLICY"
    bedrock_policy = "BEDROCK_POLICY"
    chatbot_policy = "CHATBOT_POLICY"
    declarative_policy_ec2 = "DECLARATIVE_POLICY_EC2"
    inspector_policy = "INSPECTOR_POLICY"
    network_security_director_policy = "NETWORK_SECURITY_DIRECTOR_POLICY"
    resource_control_policy = "RESOURCE_CONTROL_POLICY"
    s3_policy = "S3_POLICY"
    securityhub_policy = "SECURITYHUB_POLICY"
    service_control_policy = "SERVICE_CONTROL_POLICY"
    tag_policy = "TAG_POLICY"
    upgrade_rollout_policy = "UPGRADE_ROLLOUT_POLICY"


class PolicyTypeStatus(StrEnum):
    enabled = "ENABLED"
    pending_disable = "PENDING_DISABLE"
    pending_enable = "PENDING_ENABLE"


class PolicyTypeSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Annotated[
        PolicyTypeStatus | None,
        Field(
            alias="Status",
            description="<p>The status of the policy type as it relates to the associated root. To attach a policy             of the specified type to a root or to an OU or account in that root, it must be             available in the organization and enabled for that root.</p>",
        ),
    ] = None
    type: Annotated[PolicyType | None, Field(alias="Type", description="<p>The name of the policy type.</p>")] = None


class Root(BaseModel):
    model_config = ConfigDict(extra="forbid")
    arn: Annotated[
        str | None,
        Field(
            alias="Arn",
            description='<p>The Amazon Resource Name (ARN) of the root.</p>          <p>For more information about ARNs in Organizations, see <a href="https://docs.aws.amazon.com/service-authorization/latest/reference/list_awsorganizations.html#awsorganizations-resources-for-iam-policies">ARN     Formats Supported by Organizations</a> in the <i>Amazon Web Services Service Authorization Reference</i>.</p>',
        ),
    ] = None
    id: Annotated[
        str | None,
        Field(
            alias="Id",
            description='<p>The unique identifier (ID) for the root. The ID is unique to the organization             only.</p>          <p>The <a href="http://wikipedia.org/wiki/regex">regex pattern</a> for a root ID string requires "r-" followed by     from 4 to 32 lowercase letters or digits.</p>',
        ),
    ] = None
    name: Annotated[
        str | None,
        Field(
            alias="Name",
            description='<p>The friendly name of the root.</p>          <p>The <a href="http://wikipedia.org/wiki/regex">regex pattern</a>     that is used to validate this parameter is a string of any of the characters in the ASCII     character range.</p>',
        ),
    ] = None
    policy_types: Annotated[
        list[PolicyTypeSummary] | None,
        Field(
            alias="PolicyTypes",
            description="<p>The types of policies that are currently enabled for the root and therefore can be             attached to the root or to its OUs or accounts.</p>          <note>             <p>Even if a policy type is shown as available in the organization, you can                 separately enable and disable them at the root level by using <a>EnablePolicyType</a> and <a>DisablePolicyType</a>. Use <a>DescribeOrganization</a> to see the availability of the policy types in                 that organization.</p>          </note>",
        ),
    ] = None


class BackupPolicyConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    deployment_targets: Annotated[
        DeploymentTargets,
        Field(
            alias="deploymentTargets",
            description="Specifies which organizational units this backup policy will be applied to. Determines the scope of backup requirement enforcement.",
        ),
    ]
    description: Annotated[
        str,
        Field(
            description="Human-readable description explaining what backup requirements this policy enforces. Helps administrators understand the policy's data protection and compliance purpose.",
            min_length=1,
        ),
    ]
    name: Annotated[
        str,
        Field(
            description="Unique identifier for the backup policy. The regex pattern that is used to validate this parameter is a string of any of the characters in the ASCII character range.",
            min_length=1,
        ),
    ]
    policy: Annotated[
        str,
        Field(
            description="Path to the JSON file containing the backup policy definition. File must exist in the configuration repository and define backup plans and schedules.",
            min_length=1,
        ),
    ]


class ChatbotPolicyConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    deployment_targets: Annotated[
        DeploymentTargets,
        Field(
            alias="deploymentTargets",
            description="Specifies which organizational units this chatbot policy will be applied to. Determines the scope of chat application access control.",
        ),
    ]
    description: Annotated[
        str,
        Field(
            description="Human-readable description explaining what chatbot access controls this policy enforces. Helps administrators understand the policy's security and integration purpose.",
            min_length=1,
        ),
    ]
    name: Annotated[
        str,
        Field(
            description="Unique identifier for the chatbot policy. The regex pattern that is used to validate this parameter is a string of any of the characters in the ASCII character range.",
            min_length=1,
        ),
    ]
    policy: Annotated[
        str,
        Field(
            description="Path to the JSON file containing the chatbot policy definition. File must exist in the configuration repository and define chat application access permissions.",
            min_length=1,
        ),
    ]


class DeclarativePolicyConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    deployment_targets: Annotated[
        DeploymentTargets,
        Field(alias="deploymentTargets", description="Specifies which organizational units or accounts this declarative policy will be applied to."),
    ]
    description: Annotated[
        str,
        Field(
            description="Human-readable description explaining what AWS service settings this policy manages. Helps administrators understand the policy's purpose and scope.",
            min_length=1,
        ),
    ]
    name: Annotated[
        str,
        Field(
            description="Unique identifier for the declarative policy. The regex pattern that is used to validate this parameter is a string of any of the characters in the ASCII character range.",
            min_length=1,
        ),
    ]
    policy: Annotated[
        str,
        Field(
            description="Path to the JSON file containing the declarative policy definition. File must exist in the configuration repository and define the desired AWS service states.",
            min_length=1,
        ),
    ]


class OrganizationalUnitConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ignore: Annotated[
        bool | None,
        Field(
            description="When set to true, excludes this organizational unit and its associated accounts from processing. Defaults to false if not specified."
        ),
    ] = None
    name: Annotated[
        str,
        Field(
            description='Name and hierarchical path for the organizational unit. Supports nested structures using forward slash notation (e.g., "Sandbox/Development/Application1"). This name is used as a reference in other configuration sections. Always configure all of the OUs in the path.\n\nA nested OU configuration would be like this\n- name: Sandbox\n- name: Sandbox/Pipeline\n- name: Sandbox/Development\n- name: Sandbox/Development/Application1',
            min_length=1,
        ),
    ]


class OrganizationalUnitIdConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    arn: Annotated[str, Field(description="Amazon Resource Name (ARN) of the organizational unit.", min_length=1)]
    id: Annotated[str, Field(description="AWS Organizations unique identifier for the organizational unit.", min_length=1)]
    name: Annotated[
        str,
        Field(
            description="The logical name that identifies the organizational unit. Used as a reference key for mapping to the corresponding OU ID and ARN.",
            min_length=1,
        ),
    ]
    orgs_api_response: Annotated[
        OrganizationalUnit | Root | None,
        Field(
            alias="orgsApiResponse",
            description="Optional AWS Organizations API response data. Contains the raw response from the Organizations service.",
        ),
    ] = None


class QuarantineNewAccountsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enable: Annotated[
        bool,
        Field(
            description="Controls whether quarantine policies are automatically applied to newly created accounts. When enabled, all accounts created by any means will have the specified SCP applied for security isolation."
        ),
    ]
    scp_policy_name: Annotated[
        str | None,
        Field(
            alias="scpPolicyName",
            description="Name of the Service Control Policy to apply to new accounts for quarantine purposes. This value is required when quarantine is enabled and must match a policy defined in the serviceControlPolicies section.",
            min_length=1,
        ),
    ] = None


class ResourceControlPolicyConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    deployment_targets: Annotated[
        DeploymentTargets,
        Field(
            alias="deploymentTargets",
            description="Specifies which organizational units this resource control policy will be applied to. Determines the scope of data perimeter enforcement.",
        ),
    ]
    description: Annotated[
        str,
        Field(
            description="Human-readable description explaining what data perimeter controls this policy enforces. Helps administrators understand the policy's security purpose and scope.",
            min_length=1,
        ),
    ]
    name: Annotated[
        str,
        Field(
            description="Unique identifier for the resource control policy. The regex pattern that is used to validate this parameter is a string of any of the characters in the ASCII character range.",
            min_length=1,
        ),
    ]
    policy: Annotated[
        str,
        Field(
            description="Path to the JSON file containing the resource control policy definition. File must exist in the configuration repository and define resource access restrictions.",
            min_length=1,
        ),
    ]
    strategy: Annotated[
        Strategy | None,
        Field(
            description="Defines how the resource control policy is evaluated - either deny-list (default) or allow-list. Deny-list blocks specified resources, allow-list only permits specified resources. https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_rcps_evaluation.html"
        ),
    ] = None


class ServiceControlPolicyConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    deployment_targets: Annotated[
        DeploymentTargets,
        Field(
            alias="deploymentTargets",
            description="Specifies which organizational units this service control policy will be applied to. Determines the scope of permission enforcement.",
        ),
    ]
    description: Annotated[
        str,
        Field(
            description="Human-readable description explaining what permissions this policy controls. Helps administrators understand the policy's security purpose and scope.",
            min_length=1,
        ),
    ]
    name: Annotated[
        str,
        Field(
            description="Unique identifier for the service control policy. The regex pattern that is used to validate this parameter is a string of any of the characters in the ASCII character range.",
            min_length=1,
        ),
    ]
    policy: Annotated[
        str,
        Field(
            description="Path to the JSON file containing the service control policy definition. File must exist in the configuration repository and define permission restrictions.",
            min_length=1,
        ),
    ]
    strategy: Annotated[
        Strategy | None,
        Field(
            description="Defines how the service control policy is evaluated - either deny-list (default) or allow-list. Deny-list blocks specified actions, allow-list only permits specified actions."
        ),
    ] = None
    type: Annotated[
        Type,
        Field(
            description="Specifies whether this is an AWS-managed or customer-managed policy. AWS-managed policies are predefined by AWS, customer-managed policies are custom."
        ),
    ]


class TaggingPolicyConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    deployment_targets: Annotated[
        DeploymentTargets,
        Field(
            alias="deploymentTargets",
            description="Specifies which organizational units this tagging policy will be applied to. Determines the scope of tag standardization enforcement.",
        ),
    ]
    description: Annotated[
        str,
        Field(
            description="Human-readable description explaining what tagging standards this policy enforces. Helps administrators understand the policy's compliance and governance purpose.",
            min_length=1,
        ),
    ]
    name: Annotated[
        str,
        Field(
            description="Unique identifier for the tagging policy. The regex pattern that is used to validate this parameter is a string of any of the characters in the ASCII character range.",
            min_length=1,
        ),
    ]
    policy: Annotated[
        str,
        Field(
            description="Path to the JSON file containing the tagging policy definition. File must exist in the configuration repository and define required tags and allowed values.",
            min_length=1,
        ),
    ]


class OrganizationConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    backup_policies: Annotated[
        list[BackupPolicyConfig],
        Field(
            alias="backupPolicies",
            description="Backup policy configurations that enforce organization-wide backup requirements across organizational units. These policies ensure consistent backup strategies and compliance across accounts. The policy content is loaded from a JSON file from the path specified and deployed to the specified organizational units. File must exist in the configuration repository.",
        ),
    ]
    chatbot_policies: Annotated[
        list[ChatbotPolicyConfig] | None,
        Field(
            alias="chatbotPolicies",
            description="Chat applications policy configurations that control access to organization accounts from chat applications. These policies enforce which chat applications can be used and restrict access to specific workspaces and channels. The policy content is loaded from a JSON file from the path specified and deployed to the specified organizational units. File must exist in the configuration repository.",
        ),
    ] = None
    declarative_policies: Annotated[
        list[DeclarativePolicyConfig] | None,
        Field(
            alias="declarativePolicies",
            description="Declarative policy configurations that manage AWS service settings across organizational units. The policy content is loaded from a JSON file from the path specified. File must exist in the configuration repository.",
        ),
    ] = None
    enable: Annotated[
        bool,
        Field(
            description="Controls whether AWS Organizations features are enabled for the management account. When set to true, enables the organizational structure and policies defined in this configuration."
        ),
    ]
    organizational_unit_ids: Annotated[
        list[OrganizationalUnitIdConfig] | None,
        Field(
            alias="organizationalUnitIds",
            description="Optionally provide a list of Organizational Unit IDs to bypass the usage of the AWS Organizations Client lookup. This is not a readonly member since we will initialize it with values if it is not provided.",
        ),
    ] = None
    organizational_units: Annotated[
        list[OrganizationalUnitConfig],
        Field(
            alias="organizationalUnits",
            description="List of Organizational Units to be created or managed. Supports nested organizational unit structures using forward slash notation.",
        ),
    ]
    quarantine_new_accounts: Annotated[
        QuarantineNewAccountsConfig | None,
        Field(
            alias="quarantineNewAccounts",
            description="Configuration for automatically applying quarantine policies to newly created accounts. When enabled, applies a specified Service Control Policy to all new accounts for security isolation.",
        ),
    ] = None
    resource_control_policies: Annotated[
        list[ResourceControlPolicyConfig] | None,
        Field(
            alias="resourceControlPolicies",
            description="Resource Control Policy configurations for controlling access to AWS resources. RCPs help establish data perimeters and restrict resource access patterns. The policy content is loaded from a JSON file from the path specified and deployed to the specified organizational units. File must exist in the configuration repository.",
        ),
    ] = None
    service_control_policies: Annotated[
        list[ServiceControlPolicyConfig],
        Field(
            alias="serviceControlPolicies",
            description="Service Control Policy configurations that define maximum permissions for users and roles. SCPs act as guardrails to prevent certain actions. The policy content is loaded from a JSON file from the path specified and deployed to the specified organizational units. File must exist in the configuration repository.",
        ),
    ]
    tagging_policies: Annotated[
        list[TaggingPolicyConfig],
        Field(
            alias="taggingPolicies",
            description="Tagging policy configurations that standardize tags across resources in organizational units. The policy content is loaded from a JSON file from the path specified and deployed to the specified organizational units. File must exist in the configuration repository.",
        ),
    ]


type Model = OrganizationConfig

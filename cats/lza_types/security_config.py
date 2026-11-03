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
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field


class AccessAnalyzerConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enable: Annotated[bool, Field(description="Controls whether AWS IAM Access Analyzer is enabled across your organization.")]


class AuditManagerDefaultReportsDestinationConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    destination_type: Annotated[
        Literal["S3"],
        Field(alias="destinationType", description="The type of resource for storing audit reports. Currently only Amazon S3 buckets are supported."),
    ]
    enable: Annotated[
        bool,
        Field(
            description="Controls whether AWS Audit Manager Default Reports destination is enabled. When enabled, compliance reports are automatically saved to the specified destination for audit trail purposes."
        ),
    ]


class BlockPublicDocumentSharingConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enable: Annotated[
        bool,
        Field(
            description="Indicates whether SSM Block Public Document Sharing is enabled across the organization. When true, blocks public document sharing on all accounts except those in excludeAccounts. When false, allows public document sharing on all accounts. This setting is applied in all enabled regions for comprehensive security coverage."
        ),
    ]
    exclude_accounts: Annotated[
        list[str] | None,
        Field(
            alias="excludeAccounts",
            description="List of AWS Account names to be excluded from SSM Block Public Document Sharing configuration. Accounts in this list will have public document sharing allowed regardless of the enable setting. Account names must match those defined in the accounts configuration. Exclusions are applied across all enabled regions.",
        ),
    ] = None


class ClassificationScopeExcludedBucketConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    names: Annotated[
        list[str],
        Field(
            description="List of S3 bucket names to exclude from automated sensitive data discovery in this region. Each must be the exact, resolved bucket name — no placeholders."
        ),
    ]
    region: Annotated[
        str,
        Field(
            description="AWS region where the buckets reside (e.g., `us-east-1`, `eu-west-1`). Required because the Macie API validates that each bucket exists in the target region.\n\nWhen enabling Macie in a new region for the first time, the bucket inventory may take up to 24 hours to populate. Verify the buckets appear in the Macie S3 bucket inventory in the AWS Console before adding them here to avoid `ValidationException` errors."
        ),
    ]


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


class DetectiveConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enable: Annotated[
        bool,
        Field(
            description="Controls whether Amazon Detective is enabled across your organization.\n\n**Prerequisite:** GuardDuty must be enabled and running for at least 48 hours in every targeted account and region before setting `enable: true` here. Enabling Detective before that window will cause the pipeline to fail."
        ),
    ]
    exclude_regions: Annotated[
        list[str] | None, Field(alias="excludeRegions", description="List of AWS regions where Detective should not be enabled.")
    ] = None


class GuardDutyEc2ProtectionConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enable: Annotated[bool, Field(description="Controls whether GuardDuty EC2 Malware Protection is enabled to scan your EC2 instances for malware.")]
    exclude_regions: Annotated[
        list[str] | None,
        Field(alias="excludeRegions", description="List of AWS regions where GuardDuty EC2 Malware Protection should not be enabled."),
    ] = None
    keep_snapshots: Annotated[
        bool,
        Field(
            alias="keepSnapshots",
            description="Controls whether EBS snapshots created during malware scanning are retained. When enables, snapshots are preserved.",
        ),
    ]


class GuardDutyEksProtectionConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enable: Annotated[
        bool, Field(description="Controls whether GuardDuty EKS Protection is enabled  to monitor your EKS clusters for security threats.")
    ]
    exclude_regions: Annotated[
        list[str] | None, Field(alias="excludeRegions", description="List of AWS regions where GuardDuty EKS protection should not be enabled.")
    ] = None
    manage_agent: Annotated[bool | None, Field(alias="manageAgent", description="Controls whether the GuardDuty EKS Agent is managed.")] = None


class ExportFrequency(StrEnum):
    fifteen_minutes = "FIFTEEN_MINUTES"
    one_hour = "ONE_HOUR"
    six_hours = "SIX_HOURS"


class GuardDutyLambdaProtectionConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enable: Annotated[
        bool, Field(description="Controls whether GuardDuty Lambda Protection is enabled to monitor your Lambda functions for security threats.")
    ]
    exclude_regions: Annotated[
        list[str] | None, Field(alias="excludeRegions", description="List of AWS regions where GuardDuty Lambda Protection should not be enabled.")
    ] = None


class GuardDutyRdsProtectionConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enable: Annotated[
        bool, Field(description="Controls whether GuardDuty RDS Protection is enabled to monitor your RDS databases for security threats..")
    ]
    exclude_regions: Annotated[
        list[str] | None, Field(alias="excludeRegions", description="List of AWS regions where GuardDuty RDS Protection should not be enabled.")
    ] = None


class GuardDutyS3ProtectionConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enable: Annotated[
        bool, Field(description="Controls whether GuardDuty S3 protection is enabled to monitor your S3 buckets for suspicious activity.")
    ]
    exclude_regions: Annotated[
        list[str] | None, Field(alias="excludeRegions", description="List of AWS regions where Amazon GuardDuty S3 protection should not be enabled.")
    ] = None


class IamPasswordPolicyConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    allow_users_to_change_password: Annotated[
        bool,
        Field(
            alias="allowUsersToChangePassword",
            description="Controls whether IAM users can change their own passwords through the AWS Management Console. When enabled, users can update their passwords without administrator intervention.",
        ),
    ]
    hard_expiry: Annotated[
        bool,
        Field(
            alias="hardExpiry",
            description="Controls whether IAM users can set a new password after their current password expires. When enabled, users with expired passwords cannot access the console until an administrator resets their password.",
        ),
    ]
    max_password_age: Annotated[
        float, Field(alias="maxPasswordAge", description="The maximum number of days a password remains valid before requiring a change.")
    ]
    minimum_password_length: Annotated[
        float, Field(alias="minimumPasswordLength", description="The minimum number of characters required for IAM user passwords.")
    ]
    password_reuse_prevention: Annotated[
        float, Field(alias="passwordReusePrevention", description="The number of previous passwords that users cannot reuse.")
    ]
    require_lowercase_characters: Annotated[
        bool,
        Field(
            alias="requireLowercaseCharacters",
            description="Requires passwords to contain at least one lowercase letter from the ISO basic Latin alphabet (a to z).",
        ),
    ]
    require_numbers: Annotated[bool, Field(alias="requireNumbers", description="Requires passwords to contain at least one numeric character (0-9).")]
    require_symbols: Annotated[
        bool,
        Field(
            alias="requireSymbols",
            description="Requires passwords to contain at least one special character. Allowed symbols: ! @ # $ % ^ & * ( ) _ + - = [ ] { } | '",
        ),
    ]
    require_uppercase_characters: Annotated[
        bool,
        Field(
            alias="requireUppercaseCharacters",
            description="Requires passwords to contain at least one uppercase letter from the ISO basic Latin alphabet (A to Z).",
        ),
    ]


class RemovalPolicy(StrEnum):
    destroy = "destroy"
    retain = "retain"
    snapshot = "snapshot"


class PolicyFindingsPublishingFrequency(StrEnum):
    fifteen_minutes = "FIFTEEN_MINUTES"
    one_hour = "ONE_HOUR"
    six_hours = "SIX_HOURS"


class NetworkPerimeterConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    managed_vpc_only: Annotated[
        bool | None,
        Field(alias="managedVpcOnly", description="Controls which VPCs are included when using VPC lookup parameters in resource policy templates."),
    ] = None


class Type(StrEnum):
    string = "String"
    string_list = "StringList"


class ResourceType(StrEnum):
    s3_bucket = "S3_BUCKET"
    kms_key = "KMS_KEY"
    iam_role = "IAM_ROLE"
    secrets_manager_secret = "SECRETS_MANAGER_SECRET"
    ecr_repository = "ECR_REPOSITORY"
    opensearch_domain = "OPENSEARCH_DOMAIN"
    sns_topic = "SNS_TOPIC"
    sqs_queue = "SQS_QUEUE"
    apigateway_rest_api = "APIGATEWAY_REST_API"
    lex_bot = "LEX_BOT"
    efs_file_system = "EFS_FILE_SYSTEM"
    eventbridge_eventbus = "EVENTBRIDGE_EVENTBUS"
    backup_vault = "BACKUP_VAULT"
    codeartifact_repository = "CODEARTIFACT_REPOSITORY"
    certificate_authority = "CERTIFICATE_AUTHORITY"
    lambda_function = "LAMBDA_FUNCTION"


class ResourcePolicyRemediation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    automatic: Annotated[
        bool,
        Field(
            description="Controls whether remediation actions are triggered automatically when policy violations are detected. When enabled, AWS Config will automatically attempt to correct non-compliant resource policies."
        ),
    ]
    maximum_automatic_attempts: Annotated[
        float | None,
        Field(
            alias="maximumAutomaticAttempts",
            description="Maximum number of times AWS Config will attempt to remediate a non-compliant resource. This prevents infinite retry loops while allowing for temporary failures to be resolved. After reaching this limit, manual intervention may be required.",
        ),
    ] = None
    retry_attempt_seconds: Annotated[
        float | None,
        Field(
            alias="retryAttemptSeconds",
            description="Maximum time in seconds that AWS Config waits before timing out a remediation attempt. This prevents remediation actions from running indefinitely and ensures timely completion.",
        ),
    ] = None


class S3PublicAccessBlockConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enable: Annotated[bool, Field(description="Indicates whether S3 public access blocking is enforced across all accounts in your organization.")]
    exclude_accounts: Annotated[
        list[str] | None,
        Field(alias="excludeAccounts", description="List of AWS account names that should be exempted from S3 public access blocking requirements."),
    ] = None


class SecurityHubAutomationRuleNote(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: Annotated[
        str,
        Field(
            description="The descriptive text content of the note that will be added to the finding. This should explain the reason for the automation action"
        ),
    ]
    updated_by: Annotated[str, Field(alias="updatedBy", description="The name or identifier of the entity responsible for adding this note.")]


class SecurityHubAutomationRuleRelatedFinding(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: Annotated[str, Field(description="The unique identifier of the related finding within the specified security tool.")]
    product_arn: Annotated[
        str,
        Field(
            alias="productArn",
            description="The Amazon Resource Name (ARN) of the security tool that generated the related finding. This identifies the source service or tool that created the finding you want to link to.",
        ),
    ]


class DateRange(BaseModel):
    model_config = ConfigDict(extra="forbid")
    unit: Annotated[
        Literal["DAYS"],
        Field(description='The time unit for the date range calculation. Currently only "DAYS" is supported for relative date filtering.'),
    ]
    value: Annotated[
        float,
        Field(
            description='The number of time units to look back from the current date. For example, a value of 30 with unit "DAYS" would match findings from the last 30 days.'
        ),
    ]


class SecurityHubAutomationRulesDateFilter(BaseModel):
    model_config = ConfigDict(extra="forbid")
    date_range: Annotated[
        DateRange | None,
        Field(
            alias="dateRange",
            description="Configuration for relative date range filtering based on a rolling time window. This provides a dynamic alternative to fixed start/end dates, automatically adjusting the filter criteria based on the current date and time.",
        ),
    ] = None
    end: Annotated[
        str | None,
        Field(
            description="The end date and time for the date range filter in ISO 8601 format. Findings with dates on or before this timestamp will match the filter. Use this to define the end boundary of a specific time period for filtering."
        ),
    ] = None
    start: Annotated[
        str | None,
        Field(
            description="The start date and time for the date range filter in ISO 8601 format. Findings with dates on or after this timestamp will match the filter. Use this to define the beginning of a specific time period for filtering."
        ),
    ] = None


class Comparison(StrEnum):
    equals = "EQUALS"
    not_equals = "NOT_EQUALS"
    contains = "CONTAINS"
    not_contains = "NOT_CONTAINS"


class SecurityHubAutomationRulesKeyValueFilter(BaseModel):
    model_config = ConfigDict(extra="forbid")
    comparison: Annotated[
        Comparison,
        Field(
            description="The comparison operator that defines how the filter value should be matched against the key's value. Different operators enable various matching strategies for key-value pair filtering.\n\n- EQUALS: Exact match of the value\n- NOT_EQUALS: Does not match the value exactly\n- CONTAINS: Value contains the specified text\n- NOT_CONTAINS: Value does not contain the specified text"
        ),
    ]
    key: Annotated[
        str,
        Field(
            description="The key name to filter on within key-value pair fields. This specifies which key within a structured field (like tags or user-defined fields) to examine."
        ),
    ]
    value: Annotated[
        str,
        Field(
            description="The value to match against for the specified key. This is the target value that will be compared against the actual value associated with the key."
        ),
    ]


class SecurityHubAutomationRulesNumberFilter(BaseModel):
    model_config = ConfigDict(extra="forbid")
    eq: Annotated[
        float | None,
        Field(
            description="Matches findings where the numeric field value exactly equals this number. Use this to filter for findings with specific numeric values."
        ),
    ] = None
    gt: Annotated[
        float | None,
        Field(
            description="Matches findings where the numeric field value is greater than this number. Use this for strict greater-than comparisons (excluding the boundary value)."
        ),
    ] = None
    gte: Annotated[
        float | None,
        Field(
            description="Matches findings where the numeric field value is greater than or equal to this number. Use this to filter for findings above a certain threshold (e.g., high severity scores).\n\nGreater than or equal to value"
        ),
    ] = None
    lt: Annotated[
        float | None,
        Field(
            description="Matches findings where the numeric field value is less than this number. Use this for strict less-than comparisons (excluding the boundary value)."
        ),
    ] = None
    lte: Annotated[
        float | None,
        Field(
            description="Matches findings where the numeric field value is less than or equal to this number. Use this to filter for findings below a certain threshold (e.g., low confidence scores).\n\nLess than or equal to value"
        ),
    ] = None


class Comparison1(StrEnum):
    equals = "EQUALS"
    prefix = "PREFIX"
    not_equals = "NOT_EQUALS"
    prefix_not_equals = "PREFIX_NOT_EQUALS"
    contains = "CONTAINS"
    not_contains = "NOT_CONTAINS"
    contains_word = "CONTAINS_WORD"


class SecurityHubAutomationRulesStringFilter(BaseModel):
    model_config = ConfigDict(extra="forbid")
    comparison: Annotated[
        Comparison1,
        Field(
            description="The comparison operator that defines how the filter value should be matched against finding field values. Different operators enable various matching strategies from exact matches to partial text searches.\n\n- EQUALS: Exact match\n- PREFIX: Starts with the specified value\n- NOT_EQUALS: Does not match exactly\n- PREFIX_NOT_EQUALS: Does not start with the specified value\n- CONTAINS: Contains the specified value anywhere\n- NOT_CONTAINS: Does not contain the specified value\n- CONTAINS_WORD: Contains the specified value as a complete word"
        ),
    ]
    value: Annotated[str, Field(description="The string value to match against when filtering Security Hub findings.")]


class ShareTargets(BaseModel):
    model_config = ConfigDict(extra="forbid")
    accounts: Annotated[
        list[str] | None,
        Field(
            description="**Target Accounts** *(Optional)*\n\nList of specific account names that should receive access to the shared resource. Use this for precise, account-level control over resource sharing."
        ),
    ] = None
    organizational_units: Annotated[
        list[str] | None,
        Field(
            alias="organizationalUnits",
            description="**Organizational Units** *(Optional)*\n\nList of organizational unit names that should receive access to the shared resource. When specified, all accounts within these OUs will be able to consume the shared resource.",
        ),
    ] = None


class SsmSettingsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    block_public_document_sharing: Annotated[
        BlockPublicDocumentSharingConfig | None,
        Field(
            alias="blockPublicDocumentSharing",
            description="Configuration for preventing AWS Systems Manager documents from being shared publicly. This security control helps protect sensitive automation scripts and operational procedures from unauthorized access by blocking public document sharing across your organization.",
        ),
    ] = None


class Tag(BaseModel):
    model_config = ConfigDict(extra="forbid")
    key: Annotated[
        str,
        Field(
            description="**Tag Key** *(Required)*\n\nThe tag key name that identifies the type of metadata being stored. Tag keys should follow consistent naming conventions across your organization."
        ),
    ]
    value: Annotated[
        str,
        Field(
            description="**Tag Value** *(Required)*\n\nThe tag value that provides the actual metadata content for the tag key. Values should be meaningful and follow organizational standards."
        ),
    ]


type NonEmptyString = Annotated[
    str,
    Field(
        description="## Non-Empty String Type\n\nRepresents a string that must contain at least one character. Used for required text fields throughout the Landing Zone Accelerator configuration where empty values are not permitted.\n\n```",
        min_length=1,
    ),
]


class SecurityHubSeverityLevel(StrEnum):
    critical = "CRITICAL"
    high = "HIGH"
    medium = "MEDIUM"
    low = "LOW"
    informational = "INFORMATIONAL"


class StorageClass(StrEnum):
    deep_archive = "DEEP_ARCHIVE"
    glacier = "GLACIER"
    glacier_ir = "GLACIER_IR"
    standard_ia = "STANDARD_IA"
    intelligent_tiering = "INTELLIGENT_TIERING"
    onezone_ia = "ONEZONE_IA"


class AlarmConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    alarm_description: Annotated[
        str,
        Field(
            alias="alarmDescription", description="Human-readable description explaining what this alarm monitors and when it triggers.", min_length=1
        ),
    ]
    alarm_name: Annotated[str, Field(alias="alarmName", description="Unique name for the CloudWatch alarm", min_length=1)]
    comparison_operator: Annotated[
        str,
        Field(
            alias="comparisonOperator",
            description="The comparison operator used to evaluate the metric against the threshold. This determines the condition that must be met for the alarm to trigger.",
            min_length=1,
        ),
    ]
    evaluation_periods: Annotated[
        float,
        Field(
            alias="evaluationPeriods",
            description="The number of consecutive periods over which the threshold must be breached for the alarm to trigger.",
        ),
    ]
    metric_name: Annotated[
        str, Field(alias="metricName", description="The name of the CloudWatch metric to monitor for threshold breaches.", min_length=1)
    ]
    namespace: Annotated[str, Field(description="The CloudWatch namespace where the metric is located.", min_length=1)]
    period: Annotated[float, Field(description="The length of each evaluation period in seconds.")]
    sns_alert_level: Annotated[
        str | None,
        Field(
            alias="snsAlertLevel", deprecated="This parameter is deprecated.", description="SNS notification level for alarm alerts.", min_length=1
        ),
    ] = None
    sns_topic_name: Annotated[
        str | None,
        Field(
            alias="snsTopicName",
            description="The name of the SNS topic to send alarm notifications to when the alarm state changes. This topic name must be defined in the global configuration.",
            min_length=1,
        ),
    ] = None
    statistic: Annotated[
        str,
        Field(
            description="The statistical function to apply to the metric data points within each period. This determines how multiple data points within a period are aggregated for threshold comparison.",
            min_length=1,
        ),
    ]
    threshold: Annotated[
        float,
        Field(
            description="The threshold value that the metric statistic is compared against to determine alarm state. When the metric breaches this threshold according to the comparison operator, the alarm will transition to the ALARM state and trigger notifications."
        ),
    ]
    treat_missing_data: Annotated[
        str,
        Field(
            alias="treatMissingData", description="Defines how the alarm should behave when metric data is missing or is insufficient.", min_length=1
        ),
    ]


class AlarmSetConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    alarms: Annotated[list[AlarmConfig], Field(description="Array of CloudWatch alarm configurations to deploy as part of this alarm set.")]
    deployment_targets: Annotated[
        DeploymentTargets,
        Field(alias="deploymentTargets", description="Specifies the organizational units and accounts where this set of alarms will be deployed."),
    ]
    regions: Annotated[list[str] | None, Field(description="AWS regions where the CloudWatch alarms will be deployed.")] = None


class AwsConfigAggregation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    delegated_admin_account: Annotated[
        str | None,
        Field(
            alias="delegatedAdminAccount", description="The name of the account designated to collect and store aggregated Config data.", min_length=1
        ),
    ] = None
    enable: Annotated[
        bool,
        Field(
            description="Controls whether AWS Config aggregation is enabled across your organization. When enabled, compliance data from all accounts and regions will be centralized for unified reporting and governance oversight."
        ),
    ]


class CustomRuleLambdaType(BaseModel):
    model_config = ConfigDict(extra="forbid")
    handler: Annotated[
        str,
        Field(
            description='The entry point for your Lambda function that AWS Config will invoke. Specifies the method within your code that Lambda calls to execute the compliance evaluation. Format varies by runtime (e.g., "index.handler" for Node.js, "lambda_function.lambda_handler" for Python).',
            min_length=1,
        ),
    ]
    role_policy_file: Annotated[
        str,
        Field(
            alias="rolePolicyFile",
            description="Path to the JSON file defining IAM policies for the Lambda execution role. This file must be available in the accelerator configuration repository.",
            min_length=1,
        ),
    ]
    runtime: Annotated[
        str,
        Field(
            description="The runtime environment for executing your Lambda function. Must be compatible with your function's source code language and version requirements.",
            min_length=1,
        ),
    ]
    source_file_path: Annotated[
        str,
        Field(
            alias="sourceFilePath",
            description="Path to the ZIP file containing your Lambda function source code. This file must be available in the accelerator configuration repository.",
            min_length=1,
        ),
    ]
    timeout: Annotated[float | None, Field(description="Maximum execution time for the Lambda function in seconds.")] = None


class DocumentConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: Annotated[str, Field(description="The unique identifier for the SSM document to be created.", min_length=1)]
    target_type: Annotated[
        str | None,
        Field(
            alias="targetType", description="The target resource type that defines which AWS resources this document can operate on.", min_length=1
        ),
    ] = None
    template: Annotated[
        str,
        Field(
            description="The file path to the document template containing the SSM document definition. This file must be available in the accelerator configuration repository.",
            min_length=1,
        ),
    ]


class DocumentSetConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    documents: Annotated[list[DocumentConfig], Field(description="Array of SSM documents to be shared with the specified organizational units.")]
    share_targets: Annotated[
        ShareTargets, Field(alias="shareTargets", description="Specifies the organizational units (OUs) where the SSM documents will be shared.")
    ]


class EbsDefaultVolumeEncryptionConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    deployment_targets: Annotated[
        DeploymentTargets | None,
        Field(
            alias="deploymentTargets",
            description="Specifies which organizational units (OUs) and accounts will have EBS default volume encryption enabled.",
        ),
    ] = None
    enable: Annotated[
        bool,
        Field(
            description="Controls whether EBS default volume encryption is enabled. When enabled, all new EBS volumes created in the specified accounts and regions will be encrypted by default."
        ),
    ]
    exclude_regions: Annotated[
        list[str] | None, Field(alias="excludeRegions", description="List of AWS regions where EBS default volume encryption should not be enabled.")
    ] = None
    kms_key: Annotated[
        str | None,
        Field(alias="kmsKey", description="Name of the AWS Key Management Service (KMS) key to use for encrypting EBS volumes", min_length=1),
    ] = None


class EncryptionConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kms_key_arn: Annotated[
        str | None, Field(alias="kmsKeyArn", description="References a KMS key, not managed by LZA, for log group encryption.", min_length=1)
    ] = None
    kms_key_name: Annotated[
        str | None,
        Field(
            alias="kmsKeyName",
            description="References a KMS key created and managed by Landing Zone Accelerator for log group encryption.",
            min_length=1,
        ),
    ] = None
    use_lza_managed_key: Annotated[
        bool | None,
        Field(
            alias="useLzaManagedKey",
            description="Uses the default CloudWatch Logs KMS key that is automatically deployed by Landing Zone Accelerator.",
        ),
    ] = None


class KeyConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    alias: Annotated[
        str | None, Field(description="Human-readable alias that provides an easy way to identify and use the encryption key.", min_length=1)
    ] = None
    deployment_targets: Annotated[
        DeploymentTargets,
        Field(alias="deploymentTargets", description="Specifies which organizational units and accounts the customer-managed key is deployed to."),
    ]
    description: Annotated[
        str | None, Field(description="Human-readable description explaining the purpose and intended use of this encryption key.", min_length=1)
    ] = None
    enable_key_rotation: Annotated[
        bool | None,
        Field(
            alias="enableKeyRotation",
            description="Controls whether AWS Key Management Service (KMS) automatially rotates the encryption key material.",
        ),
    ] = True
    enabled: Annotated[
        bool | None, Field(description="Controls whether the encryption key is available to be used. Disabled keys cannot encrypt or decrypt data.")
    ] = None
    name: Annotated[str, Field(description="Unique identifier for the customer-managed key.", min_length=1)]
    policy: Annotated[
        str | None,
        Field(description="Path to the file containing the key policy. The policy file must exist in your configuration repository.", min_length=1),
    ] = None
    removal_policy: Annotated[
        RemovalPolicy | None,
        Field(
            alias="removalPolicy",
            description="Determines what happens to the encryption key when it's removed from the Stack. 'retain' preserves the key for data recovery, 'destroy' permanently deletes it, 'snapshot' creates a backup.",
        ),
    ] = None


class KeyManagementServiceConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    key_sets: Annotated[
        list[KeyConfig], Field(alias="keySets", description="Array of KMS key configurations to be created and managed across your organization.")
    ]


class LogGroupsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    deployment_targets: Annotated[
        DeploymentTargets,
        Field(alias="deploymentTargets", description="Specifies the organizational units and accounts where this log group will be deployed."),
    ]
    encryption: Annotated[EncryptionConfig | None, Field(description="Configuration for encrypting log data at rest using AWS KMS.")] = None
    log_group_name: Annotated[str, Field(alias="logGroupName", description="The name of the CLoudWatch log group to create or manage.", min_length=1)]
    log_retention_in_days: Annotated[
        float, Field(alias="logRetentionInDays", description="The number of days to retain log events in the log group.")
    ]
    termination_protected: Annotated[
        bool | None, Field(alias="terminationProtected", description="Controls whether the log group should be protected from accidental deletion.")
    ] = True


class MalwareProtectionConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    account: Annotated[str, Field(description="Account that S3 bucket resides in")]
    enable_malware_protection_tags: Annotated[
        bool | None,
        Field(alias="enableMalwareProtectionTags", description="Information about whether the tags will be added to the S3 object after scanning."),
    ] = None
    object_prefixes: Annotated[
        list[str] | None,
        Field(
            alias="objectPrefixes",
            description="Information about the specified object prefixes. The S3 object will be scanned only if it belongs to any of the specified object prefixes.",
        ),
    ] = None
    region: Annotated[str, Field(description="Region that S3 bucket resides in")]
    s3_bucket_name: Annotated[str, Field(alias="s3BucketName", description="Name of the S3 bucket.")]
    tags: Annotated[list[Tag] | None, Field(description="(OPTIONAL) Tags added to the Malware Protection plan resource.")] = None


class MetricConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    default_value: Annotated[
        float | None,
        Field(
            alias="defaultValue",
            description="Th value reported to the metric filter during a period when logs are ingested but no matching logs are found.",
        ),
    ] = None
    filter_name: Annotated[str, Field(alias="filterName", description="Unique name for the metric filter within the log group.", min_length=1)]
    filter_pattern: Annotated[
        str,
        Field(
            alias="filterPattern",
            description="A symbolic description of how CloudWatch Logs should interpret the data in each log event. The pattern specifies what to look for in the log file, such as timestamps, IP addresses, strings, and so on.",
            min_length=1,
        ),
    ]
    log_group_name: Annotated[
        str,
        Field(
            alias="logGroupName",
            description="The name of the CLoudWatch Logs log group to monitor for matching events. The metric filter will scan all log streams within this log group for events that match the specified filter pattern.",
            min_length=1,
        ),
    ]
    metric_name: Annotated[
        str,
        Field(
            alias="metricName",
            description="The name of the CloudWatch metric to which the monitored log information should be published.",
            min_length=1,
        ),
    ]
    metric_namespace: Annotated[
        str, Field(alias="metricNamespace", description="The destination namespace of the new CloudWatch metric.", min_length=1)
    ]
    metric_value: Annotated[
        str,
        Field(
            alias="metricValue",
            description="The numerical value to publish to the metric each time a matching log is found. Can either be a literal number (typically “1”), or the name of a field in the structure to take the value from the matched event. If you are using a field value, the field value must have been matched using the pattern.",
            min_length=1,
        ),
    ]
    treat_missing_data: Annotated[
        str | None,
        Field(
            alias="treatMissingData",
            description="Defines how CloudWatch alarms should handle periods when no matching log events occur.",
            min_length=1,
        ),
    ] = None


class MetricSetConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    deployment_targets: Annotated[
        DeploymentTargets | None,
        Field(
            alias="deploymentTargets", description="Specfies the organizational units and accounts where this set of metric filters will be deployed."
        ),
    ] = None
    metrics: Annotated[
        list[MetricConfig], Field(description="Array of CloudWatch metric filter configurations to deploy as part of this metric set.")
    ]
    regions: Annotated[list[str] | None, Field(description="AWS regions where the CloudWatch metric filters will be deployed.")] = None


class PrefixConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    custom_override: Annotated[
        str | None,
        Field(
            alias="customOverride",
            description="**Custom Override** *(Optional)*\n\nPrefix to be used for Centralized Logging Path when useCustomPrefix is enabled. This prefix will be prepended to the default LZA logging structure.",
            min_length=1,
        ),
    ] = None
    use_custom_prefix: Annotated[
        bool,
        Field(
            alias="useCustomPrefix",
            description="**Use Custom Prefix** *(Required)*\n\nIndicates whether or not to add a custom prefix to LZA Default Centralized Logging location. If useCustomPrefix is set to true, logs will be stored in the Centralized Logging Bucket prefix.",
        ),
    ]


class RemediationParametersConfigType(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: Annotated[str, Field(description="The name of the parameter as expected by the remediation automation document.", min_length=1)]
    type: Annotated[Type, Field(description="The data type of the parameter value, determining how the remediation document interprets the input.")]
    value: Annotated[str, Field(description="The value to pass for this parameter during remediation execution.", min_length=1)]


class ResourcePolicyConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    document: Annotated[
        str,
        Field(
            description="Path to the JSON policy document file that defines the resource-based policy. This file must be available in the accelerator configuration repository.",
            min_length=1,
        ),
    ]
    resource_type: Annotated[
        ResourceType,
        Field(
            alias="resourceType",
            description="The type of AWS resource that this policy will be applied to. This determines which AWS resources will be targeted for policy enforcement, such as S3 buckets, KMS keys, IAM roles, or other supported resource types.",
        ),
    ]


class ResourcePolicySetConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    deployment_targets: Annotated[
        DeploymentTargets,
        Field(
            alias="deploymentTargets",
            description="Specifies the organizational units and accounts where the AWS Config rules and remediation actions will be deployed.",
        ),
    ]
    input_parameters: Annotated[
        dict[str, str] | None,
        Field(
            alias="inputParameters",
            description="Custom parameters that will be passed as environment variables to the AWS Config rule and remediation Lambda functions.",
        ),
    ] = None
    resource_policies: Annotated[
        list[ResourcePolicyConfig],
        Field(alias="resourcePolicies", description="Array of resource policy configurations that define the specific policies to be enforced."),
    ]


class ScpRevertChangesConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enable: Annotated[
        bool, Field(description="Indicates whether manual changes to Service Control Policies are automatically detected and reverted.")
    ]
    sns_topic_name: Annotated[
        str | None,
        Field(
            alias="snsTopicName",
            description="Name of the SNS topic that will receive alerts when unauthorized SCP changes are detected and reverted.",
            min_length=1,
        ),
    ] = None


class SecurityHubAutomationRuleCriteria(BaseModel):
    model_config = ConfigDict(extra="forbid")
    filter: Annotated[
        list[SecurityHubAutomationRulesStringFilter]
        | list[SecurityHubAutomationRulesNumberFilter]
        | list[SecurityHubAutomationRulesDateFilter]
        | list[SecurityHubAutomationRulesKeyValueFilter],
        Field(
            description="The filter conditions to apply to the specified finding field. The filter type (string, number, date, or key-value) must match the data type of the field being filtered."
        ),
    ]
    key: Annotated[str, Field(description="The name of the Security Hub finding field to filter on.")]


class SecurityHubAutomationRuleFindingFieldsUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    confidence: Annotated[
        float | None, Field(description="The confidence score (0-100) indicating how certain the automation rule is about the finding's accuracy.")
    ] = None
    criticality: Annotated[
        float | None,
        Field(description="The criticality score (0-100) representing the business impact if this finding represents a real security issue."),
    ] = None
    note: Annotated[
        SecurityHubAutomationRuleNote | None,
        Field(description="The updated note to add to the finding that documents the reason for the automated action."),
    ] = None
    related_findings: Annotated[
        list[SecurityHubAutomationRuleRelatedFinding] | None,
        Field(alias="relatedFindings", description="Array of related findings to link to this finding for correlation and context."),
    ] = None
    severity_label: Annotated[str | None, Field(alias="severityLabel", description="Severity label to assign to the finding")] = None
    types: Annotated[list[str] | None, Field(description="Array of finding types to assign, categorizing the nature of the security issue.")] = None
    user_defined_fields: Annotated[
        dict[str, str] | None,
        Field(alias="userDefinedFields", description="Custom key-value pairs to add to the finding for organization-specific metadata."),
    ] = None
    verification_state: Annotated[
        str | None,
        Field(
            alias="verificationState",
            description="The verification state to assign to the finding, indicating the validation status of the security issue. Valid values: UNKNOWN, TRUE_POSITIVE, FALSE_POSITIVE, BENIGN_POSITIVE.",
        ),
    ] = None
    workflow_status: Annotated[
        str | None,
        Field(
            alias="workflowStatus",
            description="Workflow status to assign to the finding to update information about the investigation. This controls the finding's state in your security workflow (e.g., NEW, NOTIFIED, RESOLVED, SUPPRESSED).",
        ),
    ] = None


class SecurityHubLoggingCloudwatchConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enable: Annotated[
        bool,
        Field(
            description="Controls whether Security Hub findings are automatically forwarded to CloudWatch Logs. When enabled, findings are sent to CloudWatch for integration with monitoring dashboards and alerting systems."
        ),
    ]
    log_group_name: Annotated[
        str | None, Field(alias="logGroupName", description="Name of the CloudWatch Log Group where Security Hub findings will be stored.")
    ] = None
    log_level: Annotated[
        SecurityHubSeverityLevel | None,
        Field(alias="logLevel", description="Minimum severity level for findings that will be forwarded to CloudWatch Logs."),
    ] = None


class SecurityHubLoggingConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    cloud_watch: Annotated[
        SecurityHubLoggingCloudwatchConfig | None,
        Field(alias="cloudWatch", description="Configuration for forwarding Security Hub findings to CloudWatch Logs."),
    ] = None


class SecurityHubStandardConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    controls_to_disable: Annotated[
        list[NonEmptyString] | None,
        Field(alias="controlsToDisable", description="List of specific control names within the security standard that should be disabled."),
    ] = None
    deployment_targets: Annotated[
        DeploymentTargets | None,
        Field(alias="deploymentTargets", description="Specifies which organizational units and accounts this security standard will be applied to."),
    ] = None
    enable: Annotated[
        bool,
        Field(
            description="Controls whether this Security Hub standard is enabled to monitor compliance across your specified deployment targets. When enabled, Security Hub continuously evaluates your resources against the standard's security controls."
        ),
    ]
    name: Annotated[
        str,
        Field(
            description="The name of the AWS Security Hub standard to enable or disable. This can be any valid Security Hub standard name supported by AWS.\n\nCommon examples include:\n- 'AWS Foundational Security Best Practices v1.0.0'\n- 'CIS AWS Foundations Benchmark v1.2.0'\n- 'CIS AWS Foundations Benchmark v1.4.0'\n- 'CIS AWS Foundations Benchmark v3.0.0'\n- 'NIST Special Publication 800-53 Revision 5'\n- 'AWS Resource Tagging Standard v1.0.0'\n- 'PCI DSS v3.2.1'\n- 'PCI DSS v4.0.1'\n\nNote: AWS may add new standards over time. This field accepts any string to allow for future standards without requiring code changes.",
            min_length=1,
        ),
    ]


class SnsSubscriptionConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: Annotated[
        str, Field(description="Email address that will receive the security notifications for the specified severity level.", min_length=1)
    ]
    level: Annotated[
        str,
        Field(
            description="Defines the severity level for security notifications that will trigger email alerts. Higher levels indicate more critical security events requiring immediate attention. Notification level can be high, medium or low.",
            min_length=1,
        ),
    ]


class SsmAutomationConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    document_sets: Annotated[
        list[DocumentSetConfig],
        Field(
            alias="documentSets",
            description="Array of document sets that define which SSM documents to create and share across organizational units.",
        ),
    ]
    exclude_regions: Annotated[
        list[str] | None, Field(alias="excludeRegions", description="List of AWS regions where SSM automation documents should not be deployed.")
    ] = None


class Transition(BaseModel):
    model_config = ConfigDict(extra="forbid")
    storage_class: Annotated[
        StorageClass,
        Field(
            alias="storageClass",
            description="**Target Storage Class** *(Required)*\n\nThe S3 storage class that objects should transition to after the specified time period.",
        ),
    ]
    transition_after: Annotated[
        float,
        Field(
            alias="transitionAfter",
            description="**Transition After (Days)** *(Required)*\n\nNumber of days after object creation (for current versions) or after becoming non-current (for non-current versions) when the transition should occur.",
        ),
    ]


class TriggeringResourceType(BaseModel):
    model_config = ConfigDict(extra="forbid")
    lookup_key: Annotated[
        str | None,
        Field(alias="lookupKey", description="The lookup key used to identify resources based on the specified lookup type.", min_length=1),
    ] = None
    lookup_type: Annotated[
        str,
        Field(
            alias="lookupType",
            description="The method used to identify which resources should trigger Config rule evaluations. This determines how the Config rule will find and evaluate AWS resources for compliance.",
        ),
    ]
    lookup_value: Annotated[
        list[NonEmptyString], Field(alias="lookupValue", description="Array of values used to match resources based on the lookup type and key.")
    ]


class CloudWatchConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    alarm_sets: Annotated[
        list[AlarmSetConfig],
        Field(alias="alarmSets", description="Array of alarm sets that monitor metrics and trigger notifications when thresholds are breached."),
    ]
    log_groups: Annotated[
        list[LogGroupsConfig] | None,
        Field(alias="logGroups", description="Array of CloudWatch log group configurations for centralized log management."),
    ] = None
    metric_sets: Annotated[
        list[MetricSetConfig],
        Field(alias="metricSets", description="Array of metric filter sets that extract metrics from log data for monitoring and alerting."),
    ]


class ConfigRuleRemediationType(BaseModel):
    model_config = ConfigDict(extra="forbid")
    automatic: Annotated[
        bool,
        Field(
            description="Controls whether remediation actions are triggered automatically when non-compliance is detected. When enabled, AWS Config will immediately attempt to remediate non-compliant resources without manual intervention."
        ),
    ]
    exclude_regions: Annotated[
        list[str] | None, Field(alias="excludeRegions", description="List of AWS regions where this remediation should not be applied.")
    ] = None
    maximum_automatic_attempts: Annotated[
        float | None,
        Field(
            alias="maximumAutomaticAttempts",
            description="The maximum number of remediation attempts for a single non-compliant resource. This prevents infinite retry loops while allowing for temporary failures to be resolved. After reaching this limit, manual intervention may be required.",
        ),
    ] = None
    parameters: Annotated[
        list[RemediationParametersConfigType] | None,
        Field(
            description="Array of input parameters to pass to the remediation automation document. These parameters provide the necessary context and data for the automation document to perform the appropriate corrective actions on non-compliant resources."
        ),
    ] = None
    retry_attempt_seconds: Annotated[
        float | None,
        Field(
            alias="retryAttemptSeconds",
            description="Maximum time in seconds that AWS Config waits for each remediation attempt to complete. This prevents remediation actions from running indefinitely and ensures timely failure detection.",
        ),
    ] = None
    role_policy_file: Annotated[
        str,
        Field(
            alias="rolePolicyFile",
            description="Path to the JSON file defining IAM policies for the remediation execution role. This file must be available in the configuration repository.",
            min_length=1,
        ),
    ]
    target_account_name: Annotated[
        str | None,
        Field(alias="targetAccountName", description="The name of the AWS account that owns the remediation automation document.", min_length=1),
    ] = None
    target_document_lambda: Annotated[
        CustomRuleLambdaType | None,
        Field(
            alias="targetDocumentLambda",
            description="Configuration for a Lambda function that supports the remediation automation document. This is used when the remediation requires custom logic that cannot be achieved through standard SSM automation document actions alone.",
        ),
    ] = None
    target_id: Annotated[
        str,
        Field(
            alias="targetId",
            description="The name of the AWS Systems Manager automation document that performs the remediation actions.",
            min_length=1,
        ),
    ]
    target_version: Annotated[
        str | None, Field(alias="targetVersion", description="The version of the target automation document to use for remediation.", min_length=1)
    ] = None


class CustomRuleConfigType(BaseModel):
    model_config = ConfigDict(extra="forbid")
    configuration_changes: Annotated[
        bool | None,
        Field(
            alias="configurationChanges",
            description="Controls whether the rule runs when AWS resource configurations change. When enabled, the rule will immediately evaluate affected resources whenever their configuration is modified.",
        ),
    ] = False
    lambda_: Annotated[
        CustomRuleLambdaType,
        Field(alias="lambda", description="Configuration for the Lambda function that implements the custom compliance evaluation logic."),
    ]
    maximum_execution_frequency: Annotated[
        str, Field(alias="maximumExecutionFrequency", description="The frequency at which periodic evaluations are performed.")
    ]
    periodic: Annotated[
        bool | None,
        Field(
            description="Controls whether the rule runs on a scheduled basis at regular intervals. When enabled, the rule will evaluate resources according to the specified frequency."
        ),
    ] = True
    triggering_resources: Annotated[
        TriggeringResourceType,
        Field(alias="triggeringResources", description="Specifies which AWS resources will trigger evaluations for this Config rule."),
    ]


class GuardDutyExportFindingsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    destination_type: Annotated[
        Literal["S3"],
        Field(
            alias="destinationType",
            description="The type of resource for the publishing destination. Currently only Amazon S3 buckets are supported.",
        ),
    ]
    enable: Annotated[bool, Field(description="Controls whether GuardDuty findings are automatically exported to an S3 bucket.")]
    export_frequency: Annotated[
        ExportFrequency,
        Field(
            alias="exportFrequency",
            description="An enum value that specifies how frequently findings are exported to the S3 bucket. Possible values FIFTEEN_MINUTES, ONE_HOUR, or SIX_HOURS",
        ),
    ]
    override_existing: Annotated[
        bool | None,
        Field(alias="overrideExisting", description="Controls whether existing export configurations can be overwritten with new settings."),
    ] = None
    override_guard_duty_prefix: Annotated[
        PrefixConfig | None,
        Field(
            alias="overrideGuardDutyPrefix",
            description="Custom prefix configuration for organizing GuardDuty findings in your centralized logging S3 bucket.",
        ),
    ] = None


class GuardDutyS3MalwareProtectionConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enable: Annotated[bool, Field(description="Indicates whether AWS GuardDuty S3 Malware Protection is enabled.")]
    s3_configurations: Annotated[
        list[MalwareProtectionConfig] | None,
        Field(
            alias="s3Configurations",
            description="(OPTIONAL) The S3 Malware Protection Configuration. Provide this configuration when enabling this feature.",
        ),
    ] = None


class LifecycleRule(BaseModel):
    model_config = ConfigDict(extra="forbid")
    abort_incomplete_multipart_upload: Annotated[
        float | None,
        Field(
            alias="abortIncompleteMultipartUpload",
            description="**Abort Incomplete Multipart Uploads** *(Optional)*\n\nNumber of days after which incomplete multipart uploads are automatically aborted and cleaned up. This helps prevent storage costs from abandoned multipart uploads.\n\n### Benefits\n\n- **Cost Control**: Prevents charges for incomplete upload parts\n- **Storage Cleanup**: Automatically removes orphaned multipart data\n- **Operational Hygiene**: Maintains clean bucket state\n\n### Considerations\n\n- Set based on your typical upload patterns and file sizes\n- Consider network reliability and upload duration requirements\n- Balance between cost control and operational flexibility",
        ),
    ] = None
    enabled: Annotated[
        bool | None,
        Field(
            description="**Rule Enabled** *(Optional)*\n\nControls whether this lifecycle rule is active and enforced. Allows you to temporarily disable rules without removing them from the configuration."
        ),
    ] = True
    expiration: Annotated[
        float | None,
        Field(
            description="**Object Expiration** *(Optional)*\n\nNumber of days after object creation when objects are permanently deleted from the bucket. This implements automatic data retention policies and helps manage storage costs for time-sensitive data.\n\n### Use Cases\n\n- **Log Retention**: Automatically delete old log files\n- **Compliance**: Enforce data retention policies\n- **Cost Management**: Remove data that's no longer needed\n- **Regulatory Requirements**: Meet data disposal requirements\n\n### Important Considerations\n\n- **Irreversible**: Expired objects are permanently deleted\n- **Compliance**: Ensure retention periods meet regulatory requirements\n- **Business Needs**: Consider future data access requirements\n- **Backup Strategy**: Ensure critical data is backed up before expiration"
        ),
    ] = None
    expired_object_delete_marker: Annotated[
        bool | None,
        Field(
            alias="expiredObjectDeleteMarker",
            description="**Expired Object Delete Marker Cleanup** *(Optional)*\n\nControls whether S3 automatically removes delete markers that have no non-current versions. This helps clean up versioned buckets and reduce storage costs from orphaned delete markers.\n\n### Benefits When Enabled\n\n- **Cost Reduction**: Eliminates charges for orphaned delete markers\n- **Storage Optimization**: Keeps bucket metadata clean\n- **Operational Efficiency**: Reduces clutter in versioned buckets",
        ),
    ] = False
    id: Annotated[
        str | None,
        Field(
            description="**Rule Identifier** *(Optional)*\n\nUnique, human-readable name for the lifecycle rule within the bucket. Used for rule identification, management, and troubleshooting."
        ),
    ] = None
    noncurrent_version_expiration: Annotated[
        float | None,
        Field(
            alias="noncurrentVersionExpiration",
            description="**Non-Current Version Expiration** *(Optional)*\n\nNumber of days after an object version becomes non-current when it should be permanently deleted. This manages storage costs for versioned buckets by cleaning up old object versions.\n\n### Considerations\n\n- **Recovery Needs**: Balance cost vs. ability to recover old versions\n- **Compliance**: Some regulations require version retention\n- **Storage Costs**: Non-current versions incur full storage charges\n- **Access Patterns**: Consider how often old versions are accessed",
        ),
    ] = None
    noncurrent_version_transitions: Annotated[
        list[Transition] | None,
        Field(
            alias="noncurrentVersionTransitions",
            description="**Non-Current Version Transitions** *(Optional)*\n\nArray of transition rules that specify when non-current object versions should move to different storage classes. This optimizes costs for versioned buckets by moving old versions to cheaper storage.\n\n### Storage Class Optimization\n\nNon-current versions are typically accessed less frequently than current versions, making them ideal candidates for cheaper storage classes.",
        ),
    ] = None
    prefix: Annotated[
        str | None,
        Field(
            description="**Object Key Prefix Filter** *(Optional)*\n\nObject key prefix that identifies which objects this lifecycle rule applies to. When specified, the rule only affects objects whose keys start with this prefix. When omitted, the rule applies to all objects in the bucket.\n\n\n### Best Practices\n\n- Use consistent prefix naming conventions\n- Design prefixes to support different lifecycle needs\n- Consider future organizational changes\n- Document prefix meanings and purposes",
            min_length=1,
        ),
    ] = None
    transitions: Annotated[
        list[Transition] | None,
        Field(
            description="**Current Version Transitions** *(Optional)*\n\nArray of transition rules that specify when current objects should move to different storage classes. This implements cost optimization strategies based on data access patterns and age.\n\n### Cost Optimization Strategy\n\nDesign transitions based on your data access patterns:\n- **Frequently Accessed**: Keep in Standard storage\n- **Infrequently Accessed**: Transition to Standard-IA\n- **Archive Data**: Move to Glacier or Deep Archive\n- **Long-term Retention**: Use Deep Archive for lowest cost"
        ),
    ] = None


class MacieConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    automated_discovery_enabled: Annotated[
        bool | None,
        Field(
            alias="automatedDiscoveryEnabled",
            description="When true, automated discovery continuously samples and analyzes S3 objects across\nmember accounts to detect sensitive data without requiring manual job creation.\nWhen false, explicitly disables automated discovery.",
        ),
    ] = True
    classification_scope_excluded_buckets: Annotated[
        list[ClassificationScopeExcludedBucketConfig] | None,
        Field(
            alias="classificationScopeExcludedBuckets",
            description="Specifies S3 buckets that Macie should not analyze during automated sensitive data discovery.\nThe exclusion list is applied on the delegated admin account and applies to all member accounts.\nInternally uses REPLACE operation to ensure the exclusion list matches the declared state.\n\nEach entry requires the bucket name and the AWS region where the bucket resides.\nThe Macie UpdateClassificationScope API is regional — it only accepts buckets that exist\nin the current AWS Region. The solution filters this list per-region automatically.",
        ),
    ] = None
    disabled_regions: Annotated[
        list[str] | None,
        Field(
            alias="disabledRegions",
            description="Specifies AWS regions where the security service will be explicitly disabled when the service\nis enabled (`enable: true`). LZA will enable the service in all `enabledRegions` defined in the\nglobal config, except those listed in `excludeRegions` and `disabledRegions`.",
        ),
    ] = None
    enable: Annotated[bool, Field(description="Controls whether AWS Macie is enabled across your organization")]
    exclude_regions: Annotated[
        list[str] | None,
        Field(
            alias="excludeRegions",
            description="Specifies AWS regions where LZA will not configure the security service at all.\nThese regions are completely skipped during service deployment and management,\nregardless of whether the service is enabled or disabled.",
        ),
    ] = None
    lifecycle_rules: Annotated[
        list[LifecycleRule] | None,
        Field(
            alias="lifecycleRules",
            description="Declaration of S3 Lifecycle rules that automatically manage the retention and deletion for Macie findings reports stored in S3.",
        ),
    ] = None
    override_existing: Annotated[
        bool | None,
        Field(
            alias="overrideExisting",
            description="When set to true, forces the LZA security Macie module to execute regardless of previous state checks.\nThis flag bypasses the normal state validation that determines whether the Macie module should run\nbased on its current configuration state.",
        ),
    ] = False
    policy_findings_publishing_frequency: Annotated[
        PolicyFindingsPublishingFrequency | None,
        Field(
            alias="policyFindingsPublishingFrequency",
            description="Specifies how frequently findings are published to Security Hub. Possible values: FIFTEEN_MINUTES, ONE_HOUR, or SIX_HOURS\n\nDefault value is FIFTEEN_MINUTES",
        ),
    ] = None
    publish_policy_findings: Annotated[
        bool | None,
        Field(
            alias="publishPolicyFindings", description="Specifies whether to publish findings to Security Hub and EventBridge Default value is false."
        ),
    ] = None
    publish_sensitive_data_findings: Annotated[
        bool | None,
        Field(
            alias="publishSensitiveDataFindings",
            description="Specifies whether to publish sensitive data findings to Security Hub. If you set this value to true, Amazon Macie automatically publishes all sensitive data findings that weren't suppressed by a findings filter. Default value is false.",
        ),
    ] = None


class ResourcePolicyEnforcementConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enable: Annotated[
        bool,
        Field(
            description="Controls whether resource policy enforcement is enabled across your organization. When enabled, AWS Config rules will be deployed to monitor and enforce resource-based policies according to the configured policy sets and remediation settings."
        ),
    ]
    network_perimeter: Annotated[
        NetworkPerimeterConfig | None,
        Field(
            alias="networkPerimeter",
            description="Configuration for network perimeter controls when using VPC lookup parameters in resource policies. This optional setting controls which VPCs are included when resolving network references in policy templates.",
        ),
    ] = None
    policy_sets: Annotated[
        list[ResourcePolicySetConfig],
        Field(alias="policySets", description="Array of policy sets that define which resource policies to enforce and where to deploy them."),
    ]
    remediation: Annotated[
        ResourcePolicyRemediation,
        Field(
            description="Configuration for automated remediation when policy violations are detected. This defines how AWS Config should respond when resources are found to be non-compliant."
        ),
    ]


class SecurityHubAutomationRuleAction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    finding_fields_update: Annotated[
        SecurityHubAutomationRuleFindingFieldsUpdate | None,
        Field(
            alias="findingFieldsUpdate",
            description="Configuration specifying which finding fields to update and their new values. This defines the specific modifications that will be applied to matching findings, such as changing severity, workflow status, or adding explanatory notes.",
        ),
    ] = None
    type: Annotated[str, Field(description="The type of action to perform when findings match the automation rule criteria.")]


class SecurityHubAutomationRuleConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    actions: Annotated[
        list[SecurityHubAutomationRuleAction], Field(description="Array of actions to perform on findings that match the rule criteria.")
    ]
    criteria: Annotated[
        list[SecurityHubAutomationRuleCriteria], Field(description="Array of criteria that findings must match to trigger the rule actions")
    ]
    description: Annotated[str, Field(description="A detailed description explaining what the automation rule does and when it applies.")]
    enabled: Annotated[bool, Field(description="Controls whether the automation rule is enabled and will proccess findings.")]
    exclude_regions: Annotated[
        list[str] | None, Field(alias="excludeRegions", description="List of AWS regions where this automation rule should not be applied.")
    ] = None
    is_terminal: Annotated[
        bool | None, Field(alias="isTerminal", description="Indiciates whether this rule should be the last rule applied to a matching finding.")
    ] = None
    name: Annotated[str, Field(description="The unique name identifier for the automation rule.")]
    rule_order: Annotated[
        float | None,
        Field(
            alias="ruleOrder",
            description="The execution order for this rule when multiple rules apply to the same finding. Rules with lower numbers execute first. Valid range: 1-1000.",
        ),
    ] = None


class SecurityHubConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    auto_enable_org_members: Annotated[
        bool | None,
        Field(
            alias="autoEnableOrgMembers",
            description="Controls whether Security Hub is automatically enabled for new accounts joining the organization.",
        ),
    ] = True
    automation_rules: Annotated[
        list[SecurityHubAutomationRuleConfig] | None,
        Field(
            alias="automationRules",
            description="Configuration for Security Hub automation rules that automatically update findings based on specified criteria.",
        ),
    ] = None
    deployment_targets: Annotated[
        DeploymentTargets | None,
        Field(alias="deploymentTargets", description="Specifies which organizational units and accounts should have Security Hub enabled."),
    ] = None
    enable: Annotated[bool, Field(description="Controls whether AWS Security Hub is enabled across your organization")]
    exclude_regions: Annotated[
        list[str] | None, Field(alias="excludeRegions", description="List of AWS regions where Security Hub should not be enabled.")
    ] = None
    logging: Annotated[
        SecurityHubLoggingConfig | None,
        Field(
            description="Configuration for forwarding Security Hub findings to CloudWatch Logs for centralized monitoring. When enabled, findings are automatically sent to CloudWatch for integration with your monitoring and alerting systems."
        ),
    ] = None
    notification_level: Annotated[
        str | None, Field(alias="notificationLevel", description="Minimum severity level for findings that will trigger SNS notifications.")
    ] = None
    region_aggregation: Annotated[
        bool | None,
        Field(
            alias="regionAggregation",
            description="Controls whether Security Hub findings from all regions are aggregated in your organization's home region.",
        ),
    ] = None
    sns_topic_name: Annotated[
        str | None, Field(alias="snsTopicName", description="Name of the SNS topic that will receive Security Hub notifications.")
    ] = None
    standards: Annotated[
        list[SecurityHubStandardConfig],
        Field(description="List of security and compliance standards that Security Hub will monitor across your organization."),
    ]


class AuditManagerConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    default_reports_configuration: Annotated[
        AuditManagerDefaultReportsDestinationConfig,
        Field(
            alias="defaultReportsConfiguration",
            description="Configuration for where Audit Manager stores compliance assessment reports and audit-ready evidence.",
        ),
    ]
    enable: Annotated[bool, Field(description="Controls whether AWS Audit Manager is enabled across your organization.")]
    exclude_regions: Annotated[
        list[str] | None, Field(alias="excludeRegions", description="List of AWS regions where Audit Manager should not be enabled.")
    ] = None
    lifecycle_rules: Annotated[
        list[LifecycleRule] | None,
        Field(
            alias="lifecycleRules",
            description="S3 lifecycle rules that automatically manage the retention and deletion of Audit Manager reports and evidence stored in S3.",
        ),
    ] = None


class ConfigRule(BaseModel):
    model_config = ConfigDict(extra="forbid")
    compliance_resource_types: Annotated[
        list[NonEmptyString] | None,
        Field(alias="complianceResourceTypes", description="Array of AWS resource types that this rule will evaluate for compliance."),
    ] = None
    custom_rule: Annotated[
        CustomRuleConfigType | None,
        Field(
            alias="customRule",
            description='Configuration for custom config rules backed by AWS Lambda functions. Required when type is set to "Custom" for organization-specific compliance logic.',
        ),
    ] = None
    description: Annotated[str | None, Field(description="Human-readable description explaining what this Config rule evaluates.", min_length=1)] = (
        None
    )
    identifier: Annotated[str | None, Field(description="The identifier of the AWS-managed rule to use for compliance evaluation.", min_length=1)] = (
        None
    )
    input_parameters: Annotated[
        dict[str, NonEmptyString] | None,
        Field(alias="inputParameters", description="Key-value pairs that provide configuration parameters to the Config rule."),
    ] = None
    name: Annotated[str, Field(description="Unique name for the AWS Config rule within your organization.", min_length=1)]
    remediation: Annotated[
        ConfigRuleRemediationType | None,
        Field(
            description="Configuration for automated remediation actions when resources are found non-compliant. When configured, AWS Config can automatically fix compliance violations without manual intervention, ensuring continuous compliance across your AWS environment."
        ),
    ] = None
    tags: Annotated[list[Tag] | None, Field(description="Key-value pairs to assign as tags to the Config rule.")] = None
    type: Annotated[str | None, Field(description="The type of Config rule being created.", min_length=1)] = None


class GuardDutyConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    auto_enable_org_members: Annotated[
        bool | None,
        Field(
            alias="autoEnableOrgMembers", description="Controls whether GuardDuty is automatically enabled for new accounts joining the organization."
        ),
    ] = True
    deployment_targets: Annotated[
        DeploymentTargets | None,
        Field(alias="deploymentTargets", description="Specifies which organizational units and accounts should have GuardDuty enabled."),
    ] = None
    ec2_protection: Annotated[
        GuardDutyEc2ProtectionConfig | None,
        Field(
            alias="ec2Protection",
            description="Configuration for GuardDuty EC2 Malware Protection that scans your EC2 instances for malicious software.",
        ),
    ] = None
    eks_protection: Annotated[
        GuardDutyEksProtectionConfig | None, Field(alias="eksProtection", description="(OPTIONAL) AWS GuardDuty EKS Protection configuration.")
    ] = None
    enable: Annotated[bool, Field(description="Controls whether GuardDuty is enabled across your organization to monitor for security threats.")]
    exclude_regions: Annotated[
        list[str] | None, Field(alias="excludeRegions", description="List of AWS regions where GuardDuty should not be enabled.")
    ] = None
    export_configuration: Annotated[
        GuardDutyExportFindingsConfig,
        Field(alias="exportConfiguration", description="Configuration for exporting GuardDuty findings to S3 for long-term storage and analysis."),
    ]
    lambda_protection: Annotated[
        GuardDutyLambdaProtectionConfig | None,
        Field(
            alias="lambdaProtection",
            description="Configuration for GuardDuty Lambda Protection that monitors your serverless functions for security threats.",
        ),
    ] = None
    lifecycle_rules: Annotated[
        list[LifecycleRule] | None,
        Field(
            alias="lifecycleRules",
            description="S3 lifecycle rules that automatically manage the retention and deletion of GuardDuty findings stored in S3.",
        ),
    ] = None
    rds_protection: Annotated[
        GuardDutyRdsProtectionConfig | None,
        Field(alias="rdsProtection", description="Configuration for GuardDuty RDS Protection that monitors your databases for security threats."),
    ] = None
    s3_malware_protection: Annotated[
        GuardDutyS3MalwareProtectionConfig | None,
        Field(alias="s3MalwareProtection", description="(OPTIONAL) AWS GuardDuty S3 Malware Protection configuration."),
    ] = None
    s3_protection: Annotated[
        GuardDutyS3ProtectionConfig,
        Field(alias="s3Protection", description="Configuration for GuardDuty S3 Protection that monitors your S3 buckets for suspicious activity."),
    ]


class AwsConfigRuleSet(BaseModel):
    model_config = ConfigDict(extra="forbid")
    deployment_targets: Annotated[
        DeploymentTargets,
        Field(
            alias="deploymentTargets", description="Specifies the organizational units and accounts where this set of Config rules will be deployed."
        ),
    ]
    rules: Annotated[list[ConfigRule], Field(description="Array of AWS Config rules to deploy as part of this rule set.")]


class CentralSecurityServicesConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    audit_manager: Annotated[
        AuditManagerConfig | None,
        Field(
            alias="auditManager",
            description="Configuration for AWS Audit Manager compliance automation service across your organization. Audit Manager helps automate evidence collection and assessment preparation for audits by continuously collecting and organizing evidence from your AWS services.",
        ),
    ] = None
    delegated_admin_account: Annotated[
        str,
        Field(
            alias="delegatedAdminAccount",
            description="Designated administrator account name for accelerator security services. AWS organizations designate a member account as a delegated administrator for the organization users and roles from that account can perform administrative actions for security services like Macie, GuardDuty, Detective and Security Hub. Without designated administrator account administrative tasks for security services are performed only by users or roles in the organization's management account. This helps you to separate management of the organization from management of these security services. Accelerator currently supports using the Audit account **only** as the delegated administrator account.",
            min_length=1,
        ),
    ]
    detective: Annotated[
        DetectiveConfig | None,
        Field(
            description="Configuration for Amazon Detective security investigation service across your organization. Detective helps analyze and investigate potential security issues by providing visualizations and context around security findings from GuardDuty, Security Hub, and VPC Flow Logs."
        ),
    ] = None
    ebs_default_volume_encryption: Annotated[
        EbsDefaultVolumeEncryptionConfig,
        Field(
            alias="ebsDefaultVolumeEncryption",
            description="Configuration for automatically encrypting all new EBS volumes across your organization. This ensures data-at-rest protection and helps meet compliance requirements by enforcing encryption on all EBS volumes without requiring manual configuration.\n\nAWS Elastic Block Store default encryption configuration",
        ),
    ]
    guardduty: Annotated[
        GuardDutyConfig,
        Field(
            description="Configuration for Amazon GuardDuty threat detection service across your organization. GuardDuty provides intelligent threat detection using machine learning to identify malicious activity and unauthorized behavior across your AWS environment."
        ),
    ]
    macie: Annotated[
        MacieConfig | None,
        Field(
            description="Amazon Macie is a data security service that discovers, classifies, and protects sensitive data\nstored in Amazon S3. When configured, Macie automatically scans S3 buckets to identify personally\nidentifiable information (PII), financial data, and other sensitive content types."
        ),
    ] = None
    s3_public_access_block: Annotated[
        S3PublicAccessBlockConfig,
        Field(
            alias="s3PublicAccessBlock",
            description="Configuration for blocking public access to S3 buckets across your organization. This security control prevents accidental data exposure by blocking public access at the account level, providing an additional layer of protection for sensitive data.",
        ),
    ]
    scp_revert_changes_config: Annotated[
        ScpRevertChangesConfig | None,
        Field(
            alias="scpRevertChangesConfig",
            description="Configuration for monitoring and reverting unauthorized changes to Service Control Policies. This helps maintain security governance by detecting and alerting on manual modifications to SCPs that could weaken your organization's security posture.",
        ),
    ] = None
    security_hub: Annotated[
        SecurityHubConfig,
        Field(
            alias="securityHub",
            description="Configuration for AWS Security Hub centralized security findings management across your organization. Security Hub aggregates security alerts and findings from multiple AWS security services.",
        ),
    ]
    sns_subscriptions: Annotated[
        list[SnsSubscriptionConfig] | None,
        Field(
            alias="snsSubscriptions",
            deprecated="This parameter is deprecated and will be removed in a future release.\nSNS topic configuration has been moved to the Global Config.",
            description="Configuration for SNS notification subscriptions for security alerts (DEPRECATED).",
        ),
    ] = None
    ssm_automation: Annotated[
        SsmAutomationConfig,
        Field(
            alias="ssmAutomation",
            description="Configuration for AWS Systems Manager automation documents across your organization. This enables centralized management and distribution of SSM documents for standardizing operational procedures and automating administrative tasks across all accounts.",
        ),
    ]
    ssm_settings: Annotated[
        SsmSettingsConfig | None,
        Field(alias="ssmSettings", description="Configuration for AWS Systems Manager security settinga across your organization."),
    ] = None


class AwsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    aggregation: Annotated[
        AwsConfigAggregation | None,
        Field(
            description="Configuration for AWS Config aggregation that centralizes compliance data from multiple accounts and regions. This enables organization-wide compliance reporting and centralized governance oversight."
        ),
    ] = None
    deployment_targets: Annotated[
        DeploymentTargets | None,
        Field(alias="deploymentTargets", description="Specifies the organizational units and accounts where AWS Config will be deployed."),
    ] = None
    enable_configuration_recorder: Annotated[
        bool,
        Field(
            alias="enableConfigurationRecorder",
            description="Controls whether the AWS Config configuration recorder is enabled to track resource changes.",
        ),
    ]
    enable_delivery_channel: Annotated[
        bool | None,
        Field(
            alias="enableDeliveryChannel",
            deprecated="This parameter is deprecated.",
            description="Controls whether the delivery channel is enabled for sending configuration changes to S3.",
        ),
    ] = None
    override_existing: Annotated[
        bool | None,
        Field(
            alias="overrideExisting",
            description="Controls whether to override existing Config recorder settings in accounts that already have Config enabled.",
        ),
    ] = None
    rule_sets: Annotated[
        list[AwsConfigRuleSet] | None,
        Field(alias="ruleSets", description="Array of Config rule sets that define compliance checks to be deployed across your organization."),
    ] = None
    use_service_linked_role: Annotated[
        bool | None,
        Field(
            alias="useServiceLinkedRole",
            description="Controls whether to use AWS service-linked roles for Config instead of custom IAM roles created by LZA.",
        ),
    ] = None


class SecurityConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    access_analyzer: Annotated[
        AccessAnalyzerConfig,
        Field(
            alias="accessAnalyzer",
            description="Configuration for AWS IAM Access Analyzer that identifies resources with external access and helps implement least privilege by analyzing resource policies for security risks.",
        ),
    ]
    aws_config: Annotated[
        AwsConfig,
        Field(
            alias="awsConfig",
            description="Configuration for AWS Config service that enables continuous monitoring and assessment of AWS resource configurations for compliance, security, and governance across your organization.",
        ),
    ]
    central_security_services: Annotated[
        CentralSecurityServicesConfig,
        Field(
            alias="centralSecurityServices",
            description="Configuration for centralized security services that provide organization-wide security controls.",
        ),
    ]
    cloud_watch: Annotated[
        CloudWatchConfig,
        Field(
            alias="cloudWatch",
            description="Configuration for AWS CloudWatch monitoring and logging services that provide comprehensive observability through metric filters, automated alerting, and centralized log management.",
        ),
    ]
    home_region: Annotated[
        str | None, Field(alias="homeRegion", description="The primary AWS region where the Landing Zone Accelerator is deployed and managed.")
    ] = None
    iam_password_policy: Annotated[
        IamPasswordPolicyConfig,
        Field(
            alias="iamPasswordPolicy",
            description="Configuration for organization-wide IAM password policy that enforces password complexity and security requirements for IAM users across all accounts in your organization.",
        ),
    ]
    key_management_service: Annotated[
        KeyManagementServiceConfig | None,
        Field(
            alias="keyManagementService",
            description="Configuration for AWS Key Management Service (KMS) that enables centralized management of encryption keys across your organization for data protection and compliance requirements.",
        ),
    ] = None
    resource_policy_enforcement: Annotated[
        ResourcePolicyEnforcementConfig | None,
        Field(
            alias="resourcePolicyEnforcement",
            description="Configuration for automated resource policy enforcement that uses AWS Config rules to automatically apply and maintain consistent resource-based policies across your organization, ensuring continuous compliance with security standards.",
        ),
    ] = None


type Model = SecurityConfig

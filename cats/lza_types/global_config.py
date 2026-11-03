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


class ComparisonOperator(StrEnum):
    greater_than = "GREATER_THAN"
    less_than = "LESS_THAN"
    equal_to = "EQUAL_TO"


type EmailAddress = Annotated[
    str,
    Field(
        description='## Email Address Type\n\nRepresents a valid email address with AWS-compatible formatting requirements. Used throughout the Landing Zone Accelerator for account creation, notifications, and contact information.\n\n### Format Requirements\n\n- **Length**: 6-64 characters\n- **Pattern**: Must match standard email format\n- **Domain**: Must contain at least one dot in the domain portion\n\n### Examples\n\n```typescript const email1: EmailAddress = "admin@example.com"; ```',
        max_length=64,
        min_length=6,
        pattern="['^\\S+@\\S+\\.\\S+$', '^\\w+$']",
    ),
]


class AcceleratorMetadataConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    account: Annotated[
        str, Field(description="**Account** *(Required)*\n\nThe account to save the logs in. A new S3 Bucket will be created for this purpose.")
    ]
    enable: Annotated[bool, Field(description="**Enable** *(Required)*\n\nDetermines whether or not accelerator metadata is captured")]
    read_only_access_role_arns: Annotated[
        list[str],
        Field(
            alias="readOnlyAccessRoleArns",
            description="**Read-Only Access Role ARNs** *(Required)*\n\nList of role arns that should have read-only access to the logs.",
        ),
    ]


class AcceleratorSettingsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    max_concurrent_stacks: Annotated[
        float | None,
        Field(
            alias="maxConcurrentStacks",
            description="**Max Concurrent Stacks** *(Optional)*\n\nSet the maximum number of concurrent stacks that can be processed at a time while transpiling the application.",
        ),
    ] = 100


class DeploymentMethod(StrEnum):
    change_set = "change-set"
    direct = "direct"


class CdkOptionsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    centralize_buckets: Annotated[
        bool,
        Field(
            alias="centralizeBuckets",
            description="**Centralize Buckets** *(Required)*\n\nWhen the accelerator deploys resources using the AWS CDK, assets are first built and stored in S3. By default, the S3 bucket is located within the deployment target account. Enabling this feature will utilize an S3 bucket within the management account instead.",
        ),
    ]
    custom_deployment_role: Annotated[
        str | None,
        Field(
            alias="customDeploymentRole",
            description="**Custom Deployment Role** *(Optional)*\n\nCreate a deployment role in all accounts in the home region with the specified name. This role is used by the LZA for all CDK deployment tasks.",
        ),
    ] = None
    deployment_method: Annotated[
        DeploymentMethod | None,
        Field(
            alias="deploymentMethod",
            description="**Deployment Method** *(Optional)*\n\nManage the CDK deployment method for the LZA\n\n**Options**\n- **'direct'**: Default used by the LZA\n- **'change-set'**: Provides additional progress information, can increase deployment time",
        ),
    ] = None
    force_bootstrap: Annotated[
        bool | None,
        Field(
            alias="forceBootstrap",
            description="**Force Bootstrap** *(Optional)*\n\nForces the Accelerator to deploy the bootstrapping stack and circumvent the SSM parameter check. This option is needed when adding or removing a custom deployment role",
        ),
    ] = False
    skip_static_validation: Annotated[
        bool | None,
        Field(
            alias="skipStaticValidation",
            description="** Skip Static Validation** *(Optional)*\n\nWhen enabled, the LZA pipeline will skip the static config validation step during the build phase. Helpful in cases where the config validator incorrectly throws errors for a valid configuration.",
        ),
    ] = None
    use_management_access_role: Annotated[
        bool,
        Field(
            alias="useManagementAccessRole",
            description="**Use Management Access Role** *(Required)*\n\nIndicates whether CDK operations use the IAM role specified in the  {@link  IGlobalConfig.managementAccountAccessRole `managementAccountAccessRole` option in the global config }  rather than the default roles created by CDK.",
        ),
    ]


class CentralizeCdkBucketsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enable: Annotated[
        bool,
        Field(
            deprecated="Use {@link cdkOptionsConfig }**Enable** *(Required)*\n\nIndicates whether CDK stacks in workload accounts will utilize S3 buckets in the management account rather than within the account.\n\nWhen the accelerator deploys resources using the AWS CDK, assets are first built and stored in S3. By default, the S3 bucket is\nlocated within the deployment target account."
        ),
    ]


class CloudTrailSettingsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    api_call_rate_insight: Annotated[
        bool,
        Field(
            alias="apiCallRateInsight",
            description="**API Call Rate Insight** *(Required)*\n\nWill enable CloudTrail Insights and enable the API Call Rate Insight",
        ),
    ]
    api_error_rate_insight: Annotated[
        bool,
        Field(
            alias="apiErrorRateInsight",
            description="**API Error Rate Insight** *(Required)*\n\nWill enable CloudTrail insights and enable the API Error Rate Insight",
        ),
    ]
    global_service_events: Annotated[
        bool,
        Field(
            alias="globalServiceEvents",
            description="**Global Service Events** *(Required)*\n\nFor global services, events are delivered to any trail that includes global services and are logged in the us-east-1 region.",
        ),
    ]
    lambda_data_events: Annotated[
        bool,
        Field(
            alias="lambdaDataEvents",
            description="**Lambda Data Events** *(Required)*\n\n\n\nAdds an Lambda Data Event Selector for filtering events that match Lambda operations. These events provide insight into the resource operations performed on or within a resource. These are also known as data plane operations.\n\n**Considerations** By default, this feature is enabled and will incur additional costs if enabled for your CloudTrail.",
        ),
    ]
    management_events: Annotated[
        bool,
        Field(
            alias="managementEvents",
            description="**Management Events** *(Required)*\n\nWhether or not to log management events, or control plane operations. Management events can also include non-API events that occur in your account, such as a user logging in to the account. Enabling sets ReadWriteType.ALL.",
        ),
    ]
    multi_region_trail: Annotated[
        bool,
        Field(
            alias="multiRegionTrail",
            description="**Multi-Region Trail** *(Required)*\n\nDetermines whether or not this trail delivers log files from all regions to the account.",
        ),
    ]
    s3_data_events: Annotated[
        bool,
        Field(
            alias="s3DataEvents",
            description="**S3 Data Events** *(Required)*\n\nAdds an S3 Data Event Selector for filtering events that match S3 operations. These events provide insight into the resource operations performed on or within a resource. These are also known as data plane operations.\n\n**Considerations** By default, this feature is enabled and will incur additional costs if enabled for your CloudTrail.",
        ),
    ]
    send_to_cloud_watch_logs: Annotated[
        bool,
        Field(
            alias="sendToCloudWatchLogs",
            description="**Send to CloudWatch Logs** *(Required)*\n\nDetermines whether CloudTrail pushes logs to CloudWatch logs in addition to S3.",
        ),
    ]


class CloudWatchFirehoseLambdaProcessorConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    buffer_interval: Annotated[
        float | None,
        Field(
            alias="bufferInterval",
            description="**Buffer Interval** *(Optional)*\n\nThe period of time in seconds which Amazon Data Firehose buffers incoming data before invoking the Lambda function. The AWS lambda function is invoked once the value of the buffer size, or the buffer interval is reached.\n\nValid values range from 60 - 900s.",
        ),
    ] = 60
    buffer_size: Annotated[
        float | None,
        Field(
            alias="bufferSize",
            description="**Buffer Size** *(Optional)*\n\nThe AWS Lambda function has a 6 MB invocation payload quota. Your data can expand in size after it's processed. A smaller buffer size allows for more room should the data expand after processing.\n\nValid values range from 0.2 - 3 MB.",
        ),
    ] = 0.2
    retries: Annotated[float | None, Field(description="**Retries** *(Optional)*\n\nHow many times Firehose will retry the Lambda invocation.")] = 3


class CloudWatchManagedDataProtectionIdentifierConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    categories: Annotated[list[Literal["Credentials"]], Field(description="**Categories** *(Required)*\n\nList of categories to protect.")]


class Type(StrEnum):
    account = "ACCOUNT"
    log_group = "LOG_GROUP"


class ControlTowerLandingZoneLoggingConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    access_logging_bucket_retention_days: Annotated[
        float,
        Field(
            alias="accessLoggingBucketRetentionDays",
            description="**Access Logs Retention Time** *(Required)*\n\nRetention time, in days, of the bucket access logs",
        ),
    ]
    logging_bucket_retention_days: Annotated[
        float,
        Field(
            alias="loggingBucketRetentionDays",
            description="**Bucket Retention Configuration** *(Required)*\n\nRetention time, in days, of the Amazon S3 log archive bucket",
        ),
    ]
    organization_trail: Annotated[
        bool,
        Field(
            alias="organizationTrail",
            description="**Organization-Level CloudTrail** *(Required)*\n\nWhether or not to enable organization-level CloudTrail.\n\n**Important Considerations**\n\n- Organization-level CloudTrail is different than the CloudTrail deployed by the solution\n- If both organization-level CloudTrail and solution defined CloudTrail are enabled, multiple trails will be created",
        ),
    ]


class ControlTowerLandingZoneSecurityConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enable_identity_center_access: Annotated[
        bool,
        Field(
            alias="enableIdentityCenterAccess",
            description="**Identity Center Access** *(Required)*\n\nWhen enabled, AWS Control Tower sets up AWS account access with IAM Identity Center.",
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


class ResourcePolicyStatement(BaseModel):
    model_config = ConfigDict(extra="forbid")
    policy: Annotated[
        str,
        Field(
            description="**Policy Document** *(Required)*\n\nPath to a JSON file containing a valid AWS IAM policy document, or the policy document content as a JSON string."
        ),
    ]


class RootUserManagementCapabiltiesConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    allow_root_sessions: Annotated[
        bool,
        Field(alias="allowRootSessions", description="**Allow Root Sessions** *(Required)*\n\nDetermines whether root user sessions are allowed."),
    ]
    root_credentials_management: Annotated[
        bool,
        Field(
            alias="rootCredentialsManagement",
            description="**Root Credentials Management** *(Required)*\n\nDetermines whether root user credentials are managed by the organization.",
        ),
    ]


class S3EncryptionConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    create_cmk: Annotated[
        bool,
        Field(
            alias="createCMK",
            description="**Create CMK** *(Required)*\n\nWhen enabled, the solution will create use AWS KMS CMK for S3 server-side encryption. The following buckets always use CMK regardless of this settings:\n\n- Installer bucket\n- Pipeline bucket\n- Solution-deployed CentralLogs bucket",
        ),
    ]
    deployment_targets: Annotated[
        DeploymentTargets | None,
        Field(
            alias="deploymentTargets",
            description="**Deployment Targets** *(Optional)*\n\nEnables the control of which environments will use AWS KMS CMK for S# encryption. Leaving `deploymentTargets` undefined will apply `createCMK` setting to all accounts and enabled regions.",
        ),
    ] = None


class S3GlobalConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    encryption: Annotated[
        S3EncryptionConfig | None,
        Field(
            description="**S3 Encryption Configuration** *(Optional)*\n\nAllows for the configuration of the encryption method for S3 buckets.\n\n**Important Considerations**\n- In the absence of this property, the solution will use AWS KMS CMK in every environment\n- The solution will disregard this property and create CMKs for the installer bucket, pipeline bucket, and solution deployed CentralLogs bucket as AWS KMS CMK is always used for these buckets\n\n**Example** ```yaml encryption:   createCMK: false   deploymentTargets:     organizationalUnits:       - Root ```",
            validate_default=True,
        ),
    ] = None


class ServiceEncryptionConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    deployment_targets: Annotated[
        DeploymentTargets | None,
        Field(
            alias="deploymentTargets",
            description="**Deployment Targets** *(Optional)*\n\nConfigure which environments the given configuration will be used for. When left undefined, the configuration is applied to all accounts and enabled regions.",
        ),
    ] = None
    use_cmk: Annotated[
        bool,
        Field(
            alias="useCMK",
            description="**Use CMK** *(Required)*\n\nDetermines whether or not AWS KMS CMK will be used for encryption. When set to `true`, AWS CMK KMS will be used. When set to `false`, service managed KMS will be used.",
        ),
    ]


class ServiceQuotaLimitsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    deployment_targets: Annotated[
        DeploymentTargets,
        Field(
            alias="deploymentTargets",
            description="**Deployment Targets** *(Required)*\n\nUsed to specify the accounts that should be included in the Service Quota changes. Additionally, you can target specific accounts or entire organizational units.",
        ),
    ]
    desired_value: Annotated[
        float,
        Field(
            alias="desiredValue",
            description="**Desired Value** *(Required)*\n\nThe new limit you want to request for. The value must be higher than the current quota value. Some quotas have maximum values that cannot be exceeded.",
        ),
    ]
    quota_code: Annotated[
        str,
        Field(
            alias="quotaCode",
            description="**Quota Code** *(Required)*\n\nIndicates the specific quota we are requesting a change for within the given service. You can find the quota codes in the console or using the AWS CLI command: `aws service-quotas list-service-quotas --service-code <service-code>`.\n\nExample quota codes (verify current codes in AWS console):\n- L-B99A9384 (Lambda concurrent executions)\n- L-4019AD8B (IAM roles per account)\n- L-F678F1CE (VPCs per region)\n- L-4A669CC0 (Route 53 Resolver rules per region)",
        ),
    ]
    regions: Annotated[
        list[str] | None,
        Field(
            description="**Regions** *(Optional)*\n\nRegions where this service quota increase will be requested. If undefined, the increase will only be requested in the home region. Specified regions must also be listed in the enabledRegions section. Some quotas are global (like IAM) and don't require region specification."
        ),
    ] = None
    service_code: Annotated[
        str,
        Field(
            alias="serviceCode",
            description="**Service Code** *(Required)*\n\nIndicates which service Service Quota we are requesting a change for. You can find service codes the console or using the AWS CLI command: `aws service-quotas list-services`.\n\nExample service codes (verify current codes in AWS console):\n- lambda (AWS Lambda)\n- iam (AWS Identity and Access Management)\n- vpc (Amazon Virtual Private Cloud)\n- route53resolver (Amazon Route 53 Resolver)",
        ),
    ]


class SqsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    encryption: Annotated[
        ServiceEncryptionConfig | None, Field(description="**Encryption** *(Optional)*\n\nConfigure the encryption used for SQS queues.")
    ] = None


class SsmInventoryConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    deployment_targets: Annotated[
        DeploymentTargets,
        Field(
            alias="deploymentTargets",
            description="**Deployment Targets** *(Required)*\n\nWhich accounts should the current configuration apply to. Can be specified at the account or OU level.",
        ),
    ]
    enable: Annotated[bool, Field(description="**Enable** *(Required)*\n\nWhether or not to enable SSM Inventory.")]


class StackPolicyConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enable: Annotated[
        bool,
        Field(
            description="**Enable** *(Required)*\n\nIndicates whether stack policies are enabled for the organization. When enabled, specified resource types will be protected for Update:Replace and Update:Delete operations."
        ),
    ]
    protected_types: Annotated[
        list[str],
        Field(
            alias="protectedTypes",
            description='**Protected Types** *(Required)*\n\nA list of CloudFormation resource types that should be protected for Update:Replace and Update:Delete operations.\n\n**Example**: ```yaml protectedTypes:   - "AWS::EC2::InternetGateway"   - "AWS::EC2::NatGateway" ```',
        ),
    ]


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


class NotificationType(StrEnum):
    actual = "ACTUAL"
    forecasted = "FORECASTED"


class StorageClass(StrEnum):
    deep_archive = "DEEP_ARCHIVE"
    glacier = "GLACIER"
    glacier_ir = "GLACIER_IR"
    standard_ia = "STANDARD_IA"
    intelligent_tiering = "INTELLIGENT_TIERING"
    onezone_ia = "ONEZONE_IA"


class StreamMode(StrEnum):
    on_demand = "ON_DEMAND"
    provisioned = "PROVISIONED"


class SubscriptionType(StrEnum):
    email = "EMAIL"
    sns = "SNS"


class ThresholdType(StrEnum):
    percentage = "PERCENTAGE"
    absolute_value = "ABSOLUTE_VALUE"


class AccountCloudTrailConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    deployment_targets: Annotated[
        DeploymentTargets,
        Field(
            alias="deploymentTargets",
            description="**Deployment Targets** *(Required)*\n\nDetermines which OU's or Accounts the trail will be deployed to",
        ),
    ]
    name: Annotated[str, Field(description="**Name** *(Required)*\n\nThe name that will be used to create the trail.")]
    regions: Annotated[
        list[NonEmptyString], Field(description="**Regions** *(Required)*\n\nDetermines which region(s) that this account trail will be deployed in.")
    ]
    settings: Annotated[CloudTrailSettingsConfig, Field(description="**Settings** *(Required)*\n\nAdditional settings for the trail")]


class CentralRootUserManagementConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    capabilities: Annotated[
        RootUserManagementCapabiltiesConfig,
        Field(description="**Capabilities** *(Required)*\n\nDetermines how root user management is controlled within the organization."),
    ]
    enable: Annotated[bool, Field(description="**Enable** *(Required)*\n\nDetermines whether root user management is enabled for the organization.")]


class CloudWatchDataProtectionConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    deployment_targets: Annotated[
        DeploymentTargets | None,
        Field(
            alias="deploymentTargets",
            description="**Deployment Targets** *(Optional)*\n\nEnables control over which accounts the configuration applies to. When left undefined, the configuration will be applied to all accounts and enabled regions.",
        ),
    ] = None
    managed_data_identifiers: Annotated[
        CloudWatchManagedDataProtectionIdentifierConfig,
        Field(
            alias="managedDataIdentifiers",
            description="**Managed Data Identifiers** *(Required)*\n\nProvides the selection of data identifiers to be protected. Currently only `Credentials` is supported.",
        ),
    ]
    override_existing: Annotated[
        bool | None,
        Field(
            alias="overrideExisting",
            description="**Override Existing** *(Optional)*\n\nIndicates whether any existing CloudWatch Log data protection configurations can be overwritten.",
        ),
    ] = False


class CloudWatchFirehoseConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    file_extension: Annotated[
        str | None,
        Field(
            alias="fileExtension",
            description="**File Extension** *(Optional)*\n\nDetermines what format firehose will deliver the logs in. If left undefined, firehose will delivery the logs in MimeType as application/octet-stream.\n\n**Example** ```yaml\n- fileExtension: 'json.gz' ```",
            min_length=1,
        ),
    ] = None
    lambda_processor: Annotated[
        CloudWatchFirehoseLambdaProcessorConfig | None,
        Field(
            alias="lambdaProcessor",
            description="**Lambda Processor** *(Optional)*\n\nConfigure the lambda that process the incoming data from firehose. Firehose invokes the lambda to take the source data and deliver it to the configured dynamic partition.",
        ),
    ] = None


class CloudWatchKinesisConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    retention: Annotated[
        float | None,
        Field(
            description="**Retention** *(Optional)*\n\nThe number of hours the data records are stored in shards and remain accessible.\n\nThe value should be between 24 and 8760"
        ),
    ] = 24
    shard_count: Annotated[
        float | None,
        Field(
            alias="shardCount",
            description="**Shard Count** *(Optional)*\n\nThe number of shared the stream uses. For greater throughput, increase the number of shards. Only applicable if  {@link  ICloudWatchKinesisConfig.streamingMode }  is 'Provisioned', otherwise this is ignored. Shards cannot be increased to more than double their capacity. For example, you cannot go from 1 shard to 4.",
        ),
    ] = 1
    streaming_mode: Annotated[
        StreamMode,
        Field(
            alias="streamingMode",
            description="**Streaming Mode** *(Required)*\n\nSpecifies the capacity mode for the Kinesis Data Stream. Currently, you can choose between on-demand or provisioned capacity. The service might limit how many times you can toggle between the two modes as mentioned on [this page](https://docs.aws.amazon.com/streams/latest/dev/how-do-i-size-a-stream.html#switchingmodes)",
        ),
    ]


class CloudWatchLogSkipBulkUpdateConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enable: Annotated[bool, Field(description="**Enable** *(Required)*\n\nWhether or not to enable the skip bulk updates")]
    skip_bulk_update_targets: Annotated[
        DeploymentTargets | None,
        Field(
            alias="skipBulkUpdateTargets",
            description="**Skip Bulk Update Targets** *(Required)*\n\nWhich target's log groups to skip the bulk updates of.",
        ),
    ] = None


class CloudWatchLogsExclusionConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    accounts: Annotated[
        list[NonEmptyString] | None, Field(description="**Accounts** *(Optional)*\n\nList of accounts where the exclusions will apply.")
    ] = None
    exclude_all: Annotated[
        bool | None,
        Field(
            alias="excludeAll",
            description="**Exclude All** *(Optional)*\n\nWhether or not to exclude all logs.\n\nWhen true, all replication for the listed accounts/OUs will be disabled. Setting the OU to `Root` with no region specified and having this true, will fail validation as this would be redundant. Instead use  {@link  ICloudWatchLogsConfig.enable }  to disable replication for the entire environment",
        ),
    ] = False
    log_group_names: Annotated[
        list[NonEmptyString] | None,
        Field(
            alias="logGroupNames",
            description="**Log Group Names** *(Optional)*\n\nList of log group names to be excluded\n\nWild cards are supported. If  {@link  ICloudWatchLogsExclusionConfig.excludeAll }  is enabled, then this parameter is ignored.",
        ),
    ] = None
    organizational_units: Annotated[
        list[NonEmptyString] | None,
        Field(alias="organizationalUnits", description="**Organizational Units** *(Optional)*\n\nList of OUs to exclude."),
    ] = None
    regions: Annotated[
        list[str] | None,
        Field(description="**Regions** *(Optional)*\n\nList of regions to exclude. If left undefined, exclusions will apply to all enabled regions."),
    ] = None


class CloudWatchSubscriptionConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    filter_pattern: Annotated[
        str | None,
        Field(
            alias="filterPattern",
            description="**Filter Pattern** *(Optional)*\n\nThe specific filter pattern to apply to the subscription. If no value is provided all logs events will match filter criteria. Only applicable when  {@link  ICloudWatchSubscriptionConfig.type }  is 'LOG_GROUP'",
            min_length=1,
        ),
    ] = None
    override_existing: Annotated[
        bool | None,
        Field(
            alias="overrideExisting",
            description="**Override Existing** *(Optional)*\n\nIndicates whether the existing CloudWatch Log subscription configuration can be overwritten. If enabled, any existing policy will be updated and renamed to 'ACCELERATOR_ACCOUNT_SUBSCRIPTION_POLICY'. Upon deleting the solution or disabling logging for cloudwatch in global config, this policy will be removed. If type is set to 'LOG_GROUP' this parameter will not be used.",
        ),
    ] = False
    selection_criteria: Annotated[
        str | None,
        Field(
            alias="selectionCriteria",
            description='**Selection Criteria** *(Optional)*\n\nSelection criteria for the account-wide subscription. Only used when  {@link  ICloudWatchSubscriptionConfig.type }  is \'ACCOUNT\'. This should be used to  {@link  https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/Subscriptions-recursion-prevention.html Prevent log recursion } .\n\nIn the following example, log groups with the names /aws/lambda/AWSAccelerator-FirehoseRecordsProcessor, development, or AppA will not have a subscription filter.\n\n**Example** ```yaml selectionCriteria: \'LogGroupName NOT IN ["/aws/lambda/AWSAccelerator-FirehoseRecordsProcessor", "development", "AppA"]\' ```',
            min_length=1,
        ),
    ] = None
    type: Annotated[
        Type,
        Field(
            description="**Type** *(Required)*\n\nDetermines whether an account-wide subscription is applied, or if a Lambda function will be invoked to apply each log group.\n\n**Example** ``` type: ACCOUNT ```"
        ),
    ]


class ControlTowerControlParameter(BaseModel):
    model_config = ConfigDict(extra="forbid")
    key: Annotated[str, Field(description="Parameter name (for example `AllowedRegions` or `ExemptedActions`).", min_length=1)]
    value: Annotated[
        str | float | bool | list[str | float | bool],
        Field(
            description="Parameter value. Control Tower accepts JSON-compatible scalars or arrays; `AllowedRegions`, in particular, requires an array of region strings."
        ),
    ]


class ControlTowerLandingZoneConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    account_auto_enrollment: Annotated[
        bool | None,
        Field(
            alias="accountAutoEnrollment",
            description="**Account Auto-Enrollment** *(Optional)*\n\nEnables automatic enrollment of accounts when moved between organizational units (OUs). When enabled, accounts moved into or between registered OUs automatically receive baseline resources and control configurations from the destination OU without creating inheritance drift.",
        ),
    ] = False
    logging: Annotated[
        ControlTowerLandingZoneLoggingConfig,
        Field(
            description="**Logging Configuration** *(Required)*\n\n\n- **Retention Policies**: Configure log retention periods for compliance\n- **Organization Trail**: Enable organization-wide CloudTrail logging\n- **Access Logging**: Configure access log retention for audit trails"
        ),
    ]
    security: Annotated[
        ControlTowerLandingZoneSecurityConfig,
        Field(description="**Security Configuration** *(Required)*\n\nManage Identity Center Access for Control Tower Landing Zone."),
    ]
    version: Annotated[
        str,
        Field(
            description="**Landing Zone Version** *(Required)*\n\n**Considerations**\n\n- Most recent version required for landing zone updates or resets\n- Updates or resets will occur when drift is detected or any configuration change\n- If the solution needs to perform an update or reset and the version is not the most recent, the solution will fail"
        ),
    ]


class CustomS3ResourceAndKmsPolicyOverridesConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kms_policy: Annotated[
        str | None,
        Field(
            alias="kmsPolicy",
            description="**KMS Key Policy File** *(Optional)*\n\nPath to a JSON file containing custom KMS key policy statements for the bucket's encryption key. When provided, the accelerator will use this policy instead of generating its own key policy.",
            min_length=1,
        ),
    ] = None
    s3_policy: Annotated[
        str | None,
        Field(
            alias="s3Policy",
            description="**S3 Resource Policy File** *(Optional)*\n\nPath to a JSON file containing custom S3 bucket resource policy statements. When provided, the accelerator will use this policy instead of generating its own bucket resource policy.",
            min_length=1,
        ),
    ] = None


class CustomS3ResourcePolicyOverridesConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    policy: Annotated[
        str | None,
        Field(
            description="**S3 Resource Policy File** *(Optional)*\n\nPath to a JSON file containing custom S3 bucket resource policy statements. When provided, the accelerator will use this policy instead of generating its own bucket resource policy.\n\n### Behavior\n\n- **Complete Replacement**: Overrides all accelerator-generated policies\n- **No Merging**: Does not combine with default accelerator policies\n- **Full Control**: Provides complete control over bucket access permissions\n- **Responsibility**: You are responsible for all required service access\n\n### Example\n\n```yaml policy: compliance/restricted-access-policy.json ```",
            min_length=1,
        ),
    ] = None


class DefaultEventBusConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    deployment_targets: Annotated[
        DeploymentTargets,
        Field(
            alias="deploymentTargets",
            description="**Deployment Targets** *(Required)*\n\nDetermine which accounts the configuration applies to. LZA will deploy the LZA managed, or custom policy provided in  {@link  IDefaultEventBusConfig.policy }  property, to the default Event Bus resource-based policy for the respective account(s).",
        ),
    ]
    policy: Annotated[
        str,
        Field(
            description="**Policy** *(Required)*\n\nJSON file path containing a resource-based policy definition. The file must be present in the config repository.\n\nResource-based policy definition json file. This file must be present in config repository",
            min_length=1,
        ),
    ]


class ExternalLandingZoneResourcesConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    accelerator_name: Annotated[
        str,
        Field(alias="acceleratorName", description="**Accelerator Name** *(Required)*\n\nAccelerator Name used in the ASEA deployment", min_length=1),
    ]
    accelerator_prefix: Annotated[
        str,
        Field(
            alias="acceleratorPrefix",
            description="**Accelerator Prefix** *(Required)*\n\nAccelerator Prefix used in the ASEA deployment",
            min_length=1,
        ),
    ]
    import_external_landing_zone_resources: Annotated[
        bool,
        Field(
            alias="importExternalLandingZoneResources",
            description="**Import External Landing Zone Resources** *(Required)*\n\nSetting this flag indicates that this is an Amazon Secure Environment Accelerator (ASEA) environment and imports ASEA resources to the LZA.",
        ),
    ]
    mapping_file_bucket: Annotated[
        str | None,
        Field(
            alias="mappingFileBucket", description="**Mapping File Bucket** *(Optional)*\n\nThe name of the bucket that contains the mapping file."
        ),
    ] = None


class ImportedCustomerManagedEncryptionKeyBucketConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    apply_accelerator_managed_bucket_policy: Annotated[
        bool | None,
        Field(
            alias="applyAcceleratorManagedBucketPolicy",
            description="**Apply Accelerator Managed Bucket Policy** *(Optional)*\n\nControls whether the accelerator should apply its generated resource policies to the imported bucket. When enabled, the accelerator will manage the bucket's resource policy based on enabled security services and configurations.",
        ),
    ] = False
    create_accelerator_managed_key: Annotated[
        bool | None,
        Field(
            alias="createAcceleratorManagedKey",
            description="**Create Accelerator Managed KMS Key** *(Optional)*\n\nControls whether the accelerator should create a new customer-managed KMS key and apply it to the imported bucket for encryption. When enabled, enhances bucket security with dedicated encryption key management.\n\n### Key Creation Process\n\n**When `true`:**\n- Creates a new customer-managed KMS key specifically for this bucket\n- Applies accelerator-managed key policy with appropriate service permissions\n- Configures bucket to use the new key for server-side encryption\n- Integrates key permissions with enabled security and logging services\n\n**When `false` (default):**\n- Preserves existing bucket encryption configuration\n- Uses current encryption method (S3-managed, existing KMS key, or none)\n- No new KMS key creation or encryption changes\n- Existing encryption settings remain unchanged\n\n### Important Warnings\n\n**Irreversible Change**: Once the accelerator pipeline executes with this value set to `true`, changing it back to `false` will cause CloudFormation stack failures. The KMS key becomes a permanent part of the infrastructure.",
        ),
    ] = False
    name: Annotated[
        str,
        Field(
            description="**Bucket Name** *(Required)*\n\nName of the existing S3 bucket to be imported and managed by the accelerator. The bucket must already exist in the target AWS account.\n\n### Examples\n\n```yaml name: company-sensitive-logs name: legacy-encrypted-bucket name: imported-compliance-data ```",
            min_length=1,
        ),
    ]


class ImportedS3ManagedEncryptionKeyBucketConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    apply_accelerator_managed_bucket_policy: Annotated[
        bool | None,
        Field(
            alias="applyAcceleratorManagedBucketPolicy",
            description="**Apply Accelerator Managed Bucket Policy** *(Optional)*\n\nControls whether the accelerator should apply its generated resource policies to the imported bucket. When enabled, the accelerator will manage the bucket's resource policy based on enabled security services and configurations.\n\n### Policy Generation\n\nThe accelerator automatically generates bucket policies based on:\n- **Security Services**: Macie, GuardDuty, Security Hub access requirements\n- **Logging Services**: CloudTrail, VPC Flow Logs, Config access needs\n- **Cross-Account Access**: Organization-wide service access patterns\n- **External Policies**: Additional policies from s3ResourcePolicyAttachments\n\n### Behavior Options\n\n```yaml # Let accelerator manage policies (recommended for new imports) applyAcceleratorManagedBucketPolicy: true\n\n# Preserve existing policies (use for buckets with custom policies) applyAcceleratorManagedBucketPolicy: false ```\n\n### Important Considerations\n\n**When `true`:**\n- Accelerator **REPLACES** existing bucket resource policy\n- Combines accelerator-generated policies with external policy files\n- Ensures compatibility with enabled security services\n- **WARNING**: Removes any existing custom S3 policies on the bucket\n\n**When `false` (default):**\n- Preserves existing bucket resource policy\n- Only adds policies from external s3ResourcePolicyAttachments files\n- No changes if no external policy files are provided\n- Existing policies remain intact\n\n### Best Practices\n\n- Set to `true` for buckets that need full accelerator integration\n- Set to `false` for buckets with critical existing policies\n- Review existing policies before enabling accelerator management\n- Test policy changes in non-production environments first",
        ),
    ] = False
    name: Annotated[
        str,
        Field(
            description="**Bucket Name** *(Required)*\n\nName of the existing S3 bucket to be imported and managed by the accelerator. The bucket must already exist in the target AWS account.\n\n### Example\n\n```yaml name: company-existing-logs ```",
            min_length=1,
        ),
    ]


class LambdaConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    encryption: Annotated[
        ServiceEncryptionConfig | None,
        Field(description="**Encryption** *(Optional)*\n\nDetermine what methods should be used to encrypt lambda environment variables."),
    ] = None


class NotificationConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    address: Annotated[
        str | None,
        Field(
            deprecated="Please use recipients property to specify recipients of the notification\n\nThe address that AWS sends budget notifications to, either an SNS topic ARN or an email.\n\nWhen `subscriptionType` is `EMAIL`, this must be a valid email address.\nWhen `subscriptionType` is `SNS`, this must be a full SNS topic ARN\n(e.g., `arn:aws:sns:us-east-1:123456789012:my-topic`).",
            description="**Address** *(Optional)*",
            min_length=1,
        ),
    ] = None
    comparison_operator: Annotated[
        ComparisonOperator | str,
        Field(
            alias="comparisonOperator",
            description="**Comparison Operator** *(Required)*\n\nThe comparison that's used for this notification.\n\nValid values are `GREATER_THAN`, `LESS_THAN`, and `EQUAL_TO`",
        ),
    ]
    recipients: Annotated[
        list[NonEmptyString] | None,
        Field(
            description="**Recipients** *(Optional)*\n\nA list of recipients that the notification will be sent to.\n\nWhen `subscriptionType` is `EMAIL`, each entry must be a valid email address. When `subscriptionType` is `SNS`, the list must contain exactly one full SNS topic ARN (e.g., `arn:aws:sns:us-east-1:123456789012:my-topic`)."
        ),
    ] = None
    subscription_type: Annotated[
        SubscriptionType | str,
        Field(
            alias="subscriptionType",
            description="**Subscription Type** *(Required)*\n\nThe type of notification that AWS will send to the subscribers. Must either be `SNS` or `EMAIL`",
        ),
    ]
    threshold: Annotated[
        float | None, Field(description="**Threshold** *(Optional)*\n\nThe value that, when usage exceeds, will trigger the notification.")
    ] = None
    threshold_type: Annotated[
        ThresholdType | str,
        Field(
            alias="thresholdType",
            description="**Threshold Type** *(Required)*\n\nThe type of threshold for a notification.\n\n**Types**\n- `ABSOLUTE_VALUE`: AWS sends the notification when you go over, or are forecasted to go over, the total cost of the threshold.\n- `PERCENTAGE`: AWS sends the notification when you go over, or are forecasted to go over, a certain percentage of your forecasted spend.",
        ),
    ]
    type: Annotated[
        NotificationType | str,
        Field(
            description="**Notification Type** *(Required)*\n\nDetermines whether the notification should be sent based on actual or forecasted usage.\n\nValues must either be `ACTUAL` or `FORECASTED`"
        ),
    ]


class SnsTopicConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email_addresses: Annotated[
        list[EmailAddress],
        Field(
            alias="emailAddresses",
            description='**Email Addresses** *(Required)*\n\nList of email addresses that will receive notifications from this SNS topic. Each email address will receive a subscription confirmation email that must be confirmed before notifications can be delivered.\n\n### Subscription Management\n\n- Subscriptions are created automatically during deployment\n- Each email address receives a confirmation email from AWS\n- Unconfirmed subscriptions appear as "PendingConfirmation" in the AWS console\n- Confirmed subscriptions will receive all topic notifications',
        ),
    ]
    name: Annotated[
        str,
        Field(
            description="**Topic Name** *(Required)*\n\nUnique identifier for the SNS topic within the deployment scope. This name is used to create the SNS topic and reference it in other configurations.",
            min_length=1,
        ),
    ]


class SsmParameterConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: Annotated[
        str,
        Field(
            description="**Name** *(Required)*\n\nThe user friendly name of the SSM parameter. This is used to create the CloudFormation Logical ID.",
            min_length=1,
        ),
    ]
    path: Annotated[str, Field(description="**Path** *(Required)*\n\nThe path or name used when creating the SSM parameter.", min_length=1)]
    value: Annotated[str, Field(description="**Value** *(Required)*\n\nThe value of the SSM Parameter", min_length=1)]


class SsmParametersConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    deployment_targets: Annotated[
        DeploymentTargets,
        Field(
            alias="deploymentTargets",
            description="**Deployment Targets** *(Required)*\n\nControl which environments the SSM parameters are deployed to.",
        ),
    ]
    parameters: Annotated[list[SsmParameterConfig], Field(description="**Parameters** *(Required)*\n\nA list of parameters to be created.")]


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


class VaultConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    deployment_targets: Annotated[
        DeploymentTargets,
        Field(
            alias="deploymentTargets", description="**Deployment Targets** *(Required)*\n\nThe accounts and OUs that the vault should be deployed in."
        ),
    ]
    name: Annotated[str, Field(description="**Name** *(Required)*\n\nThe name of the vault to be created.", min_length=1)]
    policy: Annotated[
        str | None, Field(description="**Policy** *(Optional)*\n\nThe path to a JSON file defining Backup Vault access policy", min_length=1)
    ] = None


class AssetBucketConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    custom_policy_overrides: Annotated[
        CustomS3ResourceAndKmsPolicyOverridesConfig | None,
        Field(
            alias="customPolicyOverrides",
            description="**Custom Policy Overrides Configuration** *(Optional)*\n\nProvide policy overrides. Policy files must contain a complete policy document.\n\n**Conflicts**\n- When s3Policy is defined, importedBucket.applyAcceleratorManagedBucketPolicy cannot be true\n- When s3Policy is defined, seResourcePolicyAttachments cannot be defined\n- When kmsPolicy is defined, importedBucket.createAcceleratorManagedKey cannot be true\n- When kmsPolicy is defined, kmsResourcePolicyAttachments cannot be defined\n\n**Example** ```yaml customPolicyOverrides:   s3Policy: path/to/policy.json   kmsPolicy: kms/full-central-logs-bucket-key-policy.json ```",
            validate_default=True,
        ),
    ] = None
    imported_bucket: Annotated[
        ImportedCustomerManagedEncryptionKeyBucketConfig | None,
        Field(
            alias="importedBucket",
            description="**Imported Bucket Configuration** *(Optional)*\n\nWhen set, the accelerator will import an existing assets bucket.\n\nUse the following configuration to imported Assets bucket, manage bucket resource policy and apply bucket encryption through the solution.\n\n**Note**: When importing your own Assets S3 Bucket, be sure to create it in the `Management` account in the `home` region.\n\n**Example ```yaml importedBucket:    name: aws-assets    applyAcceleratorManagedBucketPolicy: true    createAcceleratorManagedKey: true ```",
            validate_default=True,
        ),
    ] = None
    kms_resource_policy_attachments: Annotated[
        list[ResourcePolicyStatement] | None,
        Field(
            alias="kmsResourcePolicyAttachments",
            description="**KMS Resource Policy Attachments** *(Optional)*\n\nPolicy statements from the listed files will be added to the bucket resource policy.\n\n**Notes**\n- Cannot be used when customPolicyOverrides.kmsPolicy property has value.\n- When importing an assets bucket with createAcceleratorManagedKey set to false, this property must be undefined\n- The Assets Bucket will allow customers to have SSE-S3 (Amazon S3 managed keys) or SSE-KMS keys. Only SSE-KMS keys can adopt the KMS resource policy files.",
        ),
    ] = None
    s3_resource_policy_attachments: Annotated[
        list[ResourcePolicyStatement] | None,
        Field(
            alias="s3ResourcePolicyAttachments",
            description="**S3 Resource Policy Attachments** *(Optional)*\n\nPolicy statements from the listed files will be added to the bucket resource policy. This property cannot be used when customPolicyOverrides.s3Policy property has value.\n\n**Note**: When Block Public Access is enabled for S3 on the AWS account, you can't specify a policy that would make the S3 Bucket public.\n\n**Example ```yaml s3ResourcePolicyAttachments:   - policy: s3-policies/policy1.json   - policy: s3-policies/policy2.json ```",
        ),
    ] = None


class BackupConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    vaults: Annotated[list[VaultConfig], Field(description="**Vaults** *(Required)*\n\nConfiguration for Backup Vaults.")]


class BudgetReportConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    amount: Annotated[
        float,
        Field(
            description="**Budget Amount** *(Required)*\n\nThe cost or usage amount that defines the budget threshold. This value represents the maximum amount you want to spend (for COST budgets) or consume (for USAGE budgets) within the specified time period.\n\n### Amount Guidelines\n\n- **Cost Budgets**: Specify amount in your preferred currency unit\n- **Usage Budgets**: Specify amount in service-specific units (hours, GB, requests)\n- **RI/Savings Plans**: Specify percentage values (0-100) for utilization/coverage\n\n### Examples\n\n```yaml # Monthly cost budget of $5,000 amount: 5000 type: COST unit: USD\n\n# Daily EC2 usage budget of 1,000 hours amount: 1000 type: USAGE unit: Hrs\n\n# RI utilization target of 80% amount: 80 type: RI_UTILIZATION ```"
        ),
    ]
    deployment_targets: Annotated[
        DeploymentTargets | None,
        Field(
            alias="deploymentTargets",
            description="**Deployment Targets** *(Optional)*\n\nSpecifies which organizational units and accounts should have this budget deployed. When not specified, the budget is deployed only to the management account.\n\n### Deployment Scope\n\n- **Organizational Units**: Deploy to all accounts within specified OUs\n- **Specific Accounts**: Deploy to individually named accounts\n- **Account Exclusions**: Exclude specific accounts from OU-wide deployments\n\n### Usage Examples\n\n```yaml # Deploy to all accounts in Workloads OU deploymentTargets:   organizationalUnits:     - Workloads\n\n# Deploy to specific accounts only deploymentTargets:   accounts:     - Production     - Staging\n\n# Deploy to OU but exclude specific accounts deploymentTargets:   organizationalUnits:     - Workloads   excludedAccounts:     - Development ```\n\n### Best Practices\n\n- Use OU-based deployment for consistent budget policies\n- Deploy cost budgets to production accounts\n- Consider separate budgets for different environments\n- Exclude sandbox accounts from strict budget controls",
        ),
    ] = None
    include_credit: Annotated[
        bool | None,
        Field(
            alias="includeCredit",
            description="**Include Credits** *(Optional)*\n\nWhether to include AWS credits in the budget calculation. When enabled, credits reduce the total amount counted against the budget.\n\n### Credit Types\n\n- AWS promotional credits\n- Service credits for SLA violations\n- Partner-provided credits\n- Migration incentive credits\n\n### Best Practices\n\n- **Enable** for net cost visibility after credits\n- **Disable** for tracking actual resource consumption costs",
        ),
    ] = True
    include_discount: Annotated[
        bool | None,
        Field(
            alias="includeDiscount",
            description="**Include Discounts** *(Optional)*\n\nWhether to include discounts in the budget calculation. When enabled, discounts reduce the total amount counted against the budget.\n\n### Discount Types\n\n- Volume discounts\n- Reserved Instance discounts\n- Savings Plans discounts\n- Promotional credits\n\n### Considerations\n\n- **Enable** to see net costs after discounts\n- **Disable** to track gross costs before discounts",
        ),
    ] = True
    include_other_subscription: Annotated[
        bool | None,
        Field(
            alias="includeOtherSubscription",
            description="**Include Other Subscriptions** *(Optional)*\n\nWhether to include non-Reserved Instance subscription costs such as Savings Plans, software subscriptions, and marketplace subscriptions.\n\n### Subscription Types Included\n\n- AWS Marketplace software subscriptions\n- Third-party software licenses\n- Other recurring subscription charges",
        ),
    ] = True
    include_recurring: Annotated[
        bool | None,
        Field(
            alias="includeRecurring",
            description="**Include Recurring Costs** *(Optional)*\n\nWhether to include recurring fees such as monthly Reserved Instance charges, data transfer fees, and other predictable recurring costs.\n\n### Recurring Cost Types\n\n- Monthly RI fees (after upfront payment)\n- Data transfer charges\n- Storage fees\n- Other predictable monthly charges",
        ),
    ] = True
    include_refund: Annotated[
        bool | None,
        Field(
            alias="includeRefund",
            description="**Include Refunds** *(Optional)*\n\nWhether to include refunds in the budget calculation. When enabled, refunds reduce the total amount counted against the budget.\n\n### When to Include\n\n- **Enable** for net cost tracking that accounts for refunds\n- **Disable** for gross cost tracking without refund adjustments\n- Consider impact on budget accuracy if refunds are frequent",
        ),
    ] = True
    include_subscription: Annotated[
        bool | None,
        Field(
            alias="includeSubscription",
            description="**Include Subscriptions** *(Optional)*\n\nWhether to include general subscription costs in the budget calculation. This is a broader category that encompasses various subscription-based charges.\n\n### When to Include\n\n- **Enable** for comprehensive subscription cost tracking\n- **Disable** when focusing only on usage-based costs",
        ),
    ] = True
    include_support: Annotated[
        bool | None,
        Field(
            alias="includeSupport",
            description="**Include Support Costs** *(Optional)*\n\nWhether to include AWS Support subscription fees in the budget calculation. This includes Business, Enterprise, and other support plan charges.\n\n### When to Include\n\n- **Enable** for complete operational cost visibility\n- **Disable** when support costs are managed separately\n- Consider if support costs should be allocated to specific teams/projects",
        ),
    ] = True
    include_tax: Annotated[
        bool | None,
        Field(
            alias="includeTax",
            description="**Include Tax** *(Optional)*\n\nWhether to include taxes in the budget calculation. This includes all applicable taxes such as VAT, sales tax, and other regional taxes.\n\n### Considerations\n\n- **Enable** for total cost visibility including all charges\n- **Disable** for pre-tax budget management\n- Consider regional tax implications for multi-region deployments",
        ),
    ] = True
    include_upfront: Annotated[
        bool | None,
        Field(
            alias="includeUpfront",
            description="**Include Upfront Costs** *(Optional)*\n\nWhether to include upfront Reserved Instance costs in the budget calculation. Upfront costs are one-time payments made when purchasing Reserved Instances.\n\n### When to Include\n\n- **Enable** for comprehensive cost tracking that includes RI purchases\n- **Enable** when budgeting for periods that include RI purchases\n- **Disable** for operational cost budgets that exclude capital expenditures",
        ),
    ] = True
    name: Annotated[
        str,
        Field(
            description="**Budget Name** *(Required)*\n\nUnique identifier for the budget within the AWS account. The name appears in the AWS Billing and Cost Management console and in budget notifications.\n\n### Naming Requirements\n\n- Must be unique within the AWS account\n- Cannot contain colon (:) or backslash (\\\\) characters\n- Should be descriptive and indicate the budget's purpose\n- Recommended to include time period and budget type\n\n### Naming Best Practices\n\n```yaml # Environment-based naming name: prod-monthly-cost-budget name: dev-daily-usage-budget\n\n# Service-specific naming name: ec2-monthly-cost-limit name: s3-storage-usage-budget\n\n# Team-based naming name: platform-team-quarterly-budget name: data-team-monthly-spend ```",
            min_length=1,
        ),
    ]
    notifications: Annotated[
        list[NotificationConfig] | None,
        Field(
            description="**Budget Notifications** *(Optional)*\n\nList of notification configurations that define when and how alerts are sent when budget thresholds are exceeded or forecasted to be exceeded.\n\n### Notification Types\n\n- **ACTUAL**: Alert when actual spending/usage exceeds threshold\n- **FORECASTED**: Alert when forecasted spending/usage will exceed threshold\n\n### Threshold Types\n\n- **PERCENTAGE**: Threshold as percentage of budget amount\n- **ABSOLUTE_VALUE**: Threshold as absolute value in budget units\n\n### Best Practices\n\n```yaml notifications:   # Early warning at 75% of budget   - type: FORECASTED     thresholdType: PERCENTAGE     threshold: 75     comparisonOperator: GREATER_THAN     subscriptionType: EMAIL     recipients:       - team-lead@example.com\n\n  # Critical alert at 90% actual spend   - type: ACTUAL     thresholdType: PERCENTAGE     threshold: 90     comparisonOperator: GREATER_THAN     subscriptionType: EMAIL     recipients:       - finance-team@example.com       - platform-team@example.com ```"
        ),
    ] = None
    subscription_type: Annotated[
        SubscriptionType | str | None,
        Field(
            alias="subscriptionType",
            description="**Subscription Type** *(Optional)*\n\nDefault notification delivery method for budget alerts. This can be overridden in individual notification configurations.\n\n### Available Types\n\n- **EMAIL**: Send notifications via email (most common)\n- **SNS**: Send notifications via Amazon SNS topic\n\n### Usage Guidelines\n\n```yaml # Email notifications (recommended for most use cases) subscriptionType: EMAIL\n\n# SNS for integration with other systems subscriptionType: SNS ```\n\n**Note:** Individual notifications can override this default setting.",
        ),
    ] = None
    time_unit: Annotated[
        str,
        Field(
            alias="timeUnit",
            description="**Time Unit** *(Required)*\n\nThe time period over which the budget amount is measured and reset. Determines how frequently the budget resets and when notifications are evaluated.\n\n### Available Time Units\n\n- **DAILY**: Budget resets every day (available for all budget types)\n- **MONTHLY**: Budget resets monthly (most common, recommended)\n- **QUARTERLY**: Budget resets every 3 months\n- **ANNUALLY**: Budget resets yearly (good for annual planning)\n\n### Usage Guidelines\n\n```yaml # Most common - monthly cost monitoring timeUnit: MONTHLY type: COST\n\n# Daily monitoring for high-usage services timeUnit: DAILY type: USAGE\n\n# Annual budgets for long-term planning timeUnit: ANNUALLY type: COST ```\n\n### Special Considerations\n\n- **RI_UTILIZATION** and **RI_COVERAGE** budgets support DAILY time units\n- DAILY budgets provide more granular monitoring but may generate more alerts\n- MONTHLY is recommended for most cost management use cases",
        ),
    ]
    type: Annotated[
        str,
        Field(
            description="**Budget Type** *(Required)*\n\nSpecifies what the budget monitors - costs, usage, or Reserved Instance metrics. The budget type determines how the amount is interpreted and what data is tracked.\n\n### Budget Types\n\n- **COST**: Monitors spending in your specified currency\n- **USAGE**: Tracks service usage quantities (hours, GB, requests)\n- **RI_UTILIZATION**: Monitors Reserved Instance utilization percentage\n- **RI_COVERAGE**: Tracks Reserved Instance coverage percentage\n- **SAVINGS_PLANS_UTILIZATION**: Monitors Savings Plans utilization\n- **SAVINGS_PLANS_COVERAGE**: Tracks Savings Plans coverage\n\n### Type-Specific Considerations\n\n```yaml # Cost monitoring (most common) type: COST amount: 5000 unit: USD\n\n# Usage monitoring type: USAGE amount: 1000 unit: Hrs\n\n# Reserved Instance optimization type: RI_UTILIZATION amount: 80  # Target 80% utilization\n\n# Savings Plans monitoring type: SAVINGS_PLANS_COVERAGE amount: 70  # Target 70% coverage ```"
        ),
    ]
    unit: Annotated[
        str | None,
        Field(
            description="**Budget Unit** *(Optional)*\n\nUnit of measurement for the budget amount. The unit depends on the budget type and determines how the amount value is interpreted.\n\n### Common Units by Budget Type\n\n**Cost Budgets:**\n- `USD`, `EUR`, `GBP`, `JPY` (currency codes)\n\n**Usage Budgets:**\n- `Hrs` (hours for compute services)\n- `GB` (gigabytes for storage)\n- `Requests` (for API calls)\n- Service-specific units\n\n**RI/Savings Plans Budgets:**\n- Percentage values (no unit specified)\n\n### Examples\n\n```yaml # Cost budget in US Dollars type: COST amount: 5000 unit: USD\n\n# Usage budget in hours type: USAGE amount: 1000 unit: Hrs\n\n# RI utilization (no unit needed) type: RI_UTILIZATION amount: 80 ```",
            min_length=1,
        ),
    ] = None
    use_amortized: Annotated[
        bool | None,
        Field(
            alias="useAmortized",
            description="**Use Amortized Costs** *(Optional)*\n\nWhether to use amortized costs for Reserved Instances and Savings Plans. Amortized costs spread upfront payments across the term of the commitment.\n\n### Amortized vs. Unblended\n\n- **Amortized**: Spreads upfront RI costs across the RI term\n- **Unblended**: Shows actual charges as they occur\n\n### When to Use\n\n- **Enable** for consistent monthly cost allocation\n- **Disable** for cash flow and actual billing tracking\n- Useful for chargeback and cost allocation scenarios",
        ),
    ] = False
    use_blended: Annotated[
        bool | None,
        Field(
            alias="useBlended",
            description="**Use Blended Rates** *(Optional)*\n\nWhether to use blended rates that average costs across different pricing tiers. Blended rates provide a simplified view by averaging tiered pricing.\n\n### Blended vs. Unblended\n\n- **Blended**: Averages costs across pricing tiers\n- **Unblended**: Shows actual per-unit costs for each tier\n\n### When to Use\n\n- **Enable** for simplified cost analysis and reporting\n- **Disable** for detailed cost optimization and tier analysis\n- Consider organizational reporting requirements",
        ),
    ] = False


class CloudWatchLogsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    data_protection: Annotated[
        CloudWatchDataProtectionConfig | None,
        Field(alias="dataProtection", description="**Data Protection** *(Optional)*\n\nConfiguration for CloudWatch Logs data protection"),
    ] = None
    dynamic_partitioning: Annotated[
        str | None,
        Field(
            alias="dynamicPartitioning",
            description='**Dynamic Partitioning for Kinesis Firehose** *(Optional)*\n\nConfigure the prefixes log groups are archived under. The input should be the path to a JSON file containing an array of the log filters.\n\n**Example JSON format** Each item should be of the format: ``` { "logGroupPattern": string, "s3Prefix": string } ```\n\nThe following example will stream any log group with the name "LogGroupName" to `s3://<central-logs-bucket>/CloudWatchLogs/s3-prefix/`. ``` { "logGroupPattern": "LogGroupName", "s3Prefix": "s3-prefix" } ```\n\nYou may use `*` for grouping log groups to the same prefix. In the following example, all log groups with a name starting with "Application" will be streamed to `s3://<central-logs-bucket>/CloudWatchLogs/app/`. ``` [{ "logGroupPattern": "Application*", "s3Prefix": "app" }] ```\n\n**Overlapping Patterns**\n\nPlease ensure that patterns do not overlap. Logs are streamed only to one destination, so logs will not be replicated in the event that the log group name matches multiple patterns.',
            min_length=1,
        ),
    ] = None
    dynamic_partitioning_by_account_id: Annotated[
        bool | None,
        Field(
            alias="dynamicPartitioningByAccountId",
            description='**Dynamic Partitioning by Account ID** *(Optional)*\n\nWhether or not the ID of the account that produced the CloudWatch Logs should be used in the partitioning strategy of the logs. For example: `s3://<central-logs-bucket>/CloudWatchLogs/<account id>/`.\n\n**Use With Dynamic Partitioning** If dynamicPartitioning is also being used, the Account ID will come before the supplied s3 prefix. For example the following would result in `s3://<central-logs-bucket>/CloudWatchLogs/<account id>/s3-prefix/` being used as the partition.\n\n``` { "logGroupPattern": "LogGroupName", "s3Prefix": "s3-prefix" } ```',
        ),
    ] = None
    enable: Annotated[
        bool | None, Field(description="**Enable Replication** *(Optional)*\n\nWhether or not to enable CloudWatch Logs replication.")
    ] = True
    encryption: Annotated[
        ServiceEncryptionConfig | None,
        Field(
            description="**Encryption** *(Optional)*\n\nConfigure encryption for the CloudWatch Logs. If left undefined, an AWS KMS CMK will be used to encrypt the logs."
        ),
    ] = None
    exclusions: Annotated[
        list[CloudWatchLogsExclusionConfig] | None,
        Field(description="**Exclusions** *(Optional)*\n\nConfigure log groups to exclude from replication."),
    ] = None
    firehose: Annotated[
        CloudWatchFirehoseConfig | None, Field(description="**Firehose** *(Optional)*\n\nConfiguration for the CloudWatch logs Firehose.")
    ] = None
    kinesis: Annotated[
        CloudWatchKinesisConfig | None, Field(description="**Kinesis** *(Optional)*\n\nConfiguration for the CloudWatch logs Kinesis.")
    ] = None
    organization_id_condition_supported: Annotated[
        bool | None,
        Field(
            alias="organizationIdConditionSupported",
            description="**Organization ID Condition** *(Optional)*\n\nWhether or not a list of account IDs is used instead of a principal organization condition in the CloudWatch Logs destination access policy. Useful in partitions where the principal organization condition is not supported.",
        ),
    ] = None
    replace_log_destination_arn: Annotated[
        str | None,
        Field(
            alias="replaceLogDestinationArn",
            description="**Replace Log Destination** *(Optional)*\n\nThe ARN of the current log subscription filter destination. LZA needs to disassociate this destination before configuring the LZA defined subscription filter destination.\n\n**Notes**\n- When no value is provided, the solution will not attempt to remove the existing subscription filter destination\n- When existing log group(s) have two subscription filter destinations defined, and none are LZA configured, the solution will fail to configure log replication and the pipeline will fail",
            min_length=1,
        ),
    ] = None
    skip_bulk_update: Annotated[
        CloudWatchLogSkipBulkUpdateConfig | None,
        Field(
            alias="skipBulkUpdate",
            description="**Skip Bulk Update** *(Optional)*\n\nWhether or not the LZA pipeline should skip the bulk update of CloudWatch log groups.\n\n**Warning**: This configuration option could cause CloudWatch log group configurations to become out of sync with the global configuration. Only enable if you fully understand the implications.",
        ),
    ] = None
    subscription: Annotated[
        CloudWatchSubscriptionConfig | None, Field(description="**Subscription** *(Optional)*\n\nConfiguration for the CloudWatch logs subscription.")
    ] = None


class ControlTowerControlConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    deployment_targets: Annotated[
        DeploymentTargets,
        Field(
            alias="deploymentTargets",
            description="**Deployment Targets** *(Required)*\n\nSpecifies the organizational units where this control should be applied. Controls can only be deployed to OUs, not individual accounts.\n\n### Organizational Unit Targeting\n\nControls are applied at the OU level and automatically affect:\n- All current accounts in the target OU\n- All future accounts added to the target OU\n- Child OUs and their accounts (inheritance)\n\n### Usage Examples\n\n```yaml deploymentTargets:   organizationalUnits:     - Production     - Staging     - Development\n\n# Root OU deployment (affects all accounts) deploymentTargets:   organizationalUnits:     - Root ```\n\n### OU Restrictions\n\n**Security OU Limitations:**\n- Some controls cannot be deployed to the Security OU\n- Check AWS documentation for specific control compatibility\n- Alternative controls may be available for Security OU\n\n### Validation Requirements\n\n- OU names must exactly match those defined in organization-config.yaml\n- OUs must exist before control deployment\n- Invalid OU names will cause deployment failures",
        ),
    ]
    enable: Annotated[
        bool,
        Field(
            description='**Enable Control** *(Required)*\n\nControls whether this guardrail should be enabled or disabled for the specified organizational units.\n\n### Control States\n\n**Enabled (`true`):**\n- Control is active and enforcing its policy\n- Resources are monitored for compliance\n- Non-compliant resources are flagged or remediated\n- Control appears as "Enabled" in Control Tower console\n\n**Disabled (`false`):**\n- Control is inactive and not enforcing policy\n- No compliance monitoring occurs\n- Existing violations are not flagged\n- Control appears as "Disabled" in Control Tower console\n\n### Usage Examples\n\n```yaml # Enable a security control\n- identifier: AWS-GR_RDS_INSTANCE_PUBLIC_ACCESS_CHECK   enable: true    # Control will be enabled   deploymentTargets:     organizationalUnits:       - Production\n\n# Disable a control (useful for temporary exceptions)\n- identifier: AWS-GR_EC2_INSTANCE_IMDSv2_CHECK   enable: false   # Control will be disabled   deploymentTargets:     organizationalUnits:       - Development ```'
        ),
    ]
    identifier: Annotated[
        str,
        Field(
            description="**Control Identifier** *(Required)*\n\nUnique identifier for the Control Tower guardrail to be enabled. The identifier format depends on the control type and determines how the control is referenced.\n\n### Identifier Formats\n\n**Standard Controls (AWS-GR_*):**\n- Format: `AWS-GR_<CONTROL_NAME>`\n- Used for strongly recommended and elective controls\n- Human-readable and descriptive of the control's purpose\n\n**Global Controls (Opaque IDs):**\n- Format: Alphanumeric string (e.g., `m7a5gbdf08wg2o0en010mkng`)\n- Used for global controls that span multiple services\n- Requires reference to AWS documentation for mapping",
            min_length=1,
        ),
    ]
    parameters: Annotated[
        list[ControlTowerControlParameter] | None,
        Field(
            description="**Control Parameters** *(Optional)*\n\nA list of key/value pairs forwarded to the AWS Control Tower `EnableControl` API as the `Parameters` argument. This is required for region-aware controls (for example `AWS-GR_REGION_DENY` or `CT.MULTISERVICE.PV.1`), which otherwise fail to deploy with `Parameter AllowedRegions is required`.\n\n### Usage Example\n\n```yaml\n- identifier: CT.MULTISERVICE.PV.1   enable: true   deploymentTargets:     organizationalUnits:       - Root   parameters:     - key: AllowedRegions       value:         - us-east-1         - us-west-2 ```"
        ),
    ] = None
    regions: Annotated[
        list[str] | None,
        Field(
            description="**Regional Scope** *(Optional)*\n\nSpecifies the AWS regions where this control should be enabled. If not specified, the control is enabled in the home region only.\n\n### Regional Deployment\n\n**Global Controls:**\n- Some controls are inherently global (e.g., IAM-related controls)\n- Regional specification is ignored for global controls\n- Applied once per account regardless of region list\n\n**Regional Controls:**\n- Most controls are region-specific (e.g., EC2, VPC controls)\n- Must be explicitly enabled in each target region\n- Each region deployment counts as a separate operation\n\n### Usage Examples\n\n```yaml regions:   - us-east-1   - us-west-2   - eu-west-1 ```\n\n### Important Considerations\n\n- Each region deployment counts toward the 10 concurrent operation limit\n- Regions must be listed in the `enabledRegions` section of global-config.yaml\n- Invalid regions will cause deployment failures"
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


class SessionManagerConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    attach_policy_to_iam_roles: Annotated[
        list[str] | None,
        Field(
            alias="attachPolicyToIamRoles",
            description="**Attach Policy to IAM Roles** *(Optional)*\n\nA list of IAM Ec2 roles that the Session Manager access policy should be attached to.",
        ),
    ] = None
    exclude_accounts: Annotated[
        list[str] | None,
        Field(
            alias="excludeAccounts",
            description="**Excluded Accounts** *(Optional)*\n\nList of AWS Account names to be excluded from this SessionManager configuration",
        ),
    ] = None
    exclude_regions: Annotated[
        list[str] | None,
        Field(
            alias="excludeRegions",
            description="**Excluded Regions** *(Optional)*\n\nList of AWS Region names to be excluded from this SessionManager configuration",
        ),
    ] = None
    lifecycle_rules: Annotated[
        list[LifecycleRule] | None,
        Field(
            alias="lifecycleRules",
            description="**S3 Lifecycle Rules** *(Optional)*\n\nDefines the lifecycle rules for the S3 bucket containing the logs.",
        ),
    ] = None
    send_to_cloud_watch_logs: Annotated[
        bool,
        Field(
            alias="sendToCloudWatchLogs",
            description="**Send to CloudWatch Logs** *(Required)*\n\nDetermines whether sending SessionManager logs to CloudWatch logs is enabled.",
        ),
    ]
    send_to_s3: Annotated[
        bool,
        Field(
            alias="sendToS3",
            description="**Send to S3** *(Required)*\n\nDetermines whether sending SessionManager logs to S3 is enabled. When enabled, the accelerator will send the session manager logs to the central log bucket in the LogArchive account.",
        ),
    ]


class SnsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    deployment_targets: Annotated[
        DeploymentTargets,
        Field(
            alias="deploymentTargets",
            description="**Deployment Targets** *(Required)*\n\nDetermines which accounts the SNS topic will be deployed to.\n\n**Note** SNS topics will always be deployed to the Log Archive Account. All email subscriptions will be created in the Log Archive Account. Member accounts will forward their notifications through the Log Archive Account.",
        ),
    ]
    topics: Annotated[
        list[SnsTopicConfig], Field(description="**SNS Topic Configuration** *(Required)*\n\nList of SNS Topics to be created by the solution.")
    ]


class AccessLogBucketConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    custom_policy_overrides: Annotated[
        CustomS3ResourcePolicyOverridesConfig | None,
        Field(
            alias="customPolicyOverrides",
            description="**Custom Policy Overrides Configuration** *(Optional)*\n\nProvide policy overrides. Policy files must contain a complete policy document.\n\n**Conflicts**\n- When s3Policy is defined, importedBucket.applyAcceleratorManagedBucketPolicy cannot be true\n- When s3Policy is defined, s3ResourcePolicyAttachments cannot be defined\n\n**Example** ```yaml customPolicyOverrides:   s3Policy: path/to/access-log-policy.json ```",
            validate_default=True,
        ),
    ] = None
    deployment_targets: Annotated[
        DeploymentTargets | None,
        Field(
            alias="deploymentTargets",
            description="**Deployment Targets** *(Optional)*\n\nSpecifies which accounts and regions should receive the access log bucket configuration. When undefined, the configuration applies to all accounts and enabled regions.\n\n**Example** ```yaml deploymentTargets:   organizationalUnits:     - Root   excludedRegions:     - us-west-1 ```",
            validate_default=True,
        ),
    ] = None
    enable: Annotated[
        bool | None,
        Field(
            description="**Enable Access Log Bucket** *(Optional)*\n\nControls whether the S3 access logging bucket is created by the solution. When undefined, the solution will create access log buckets automatically.\n\n**Important Notes**\n- Access log buckets are always created for critical solution buckets (installer, pipeline, central logs, assets)\n- Use deploymentTargets to control which accounts and regions receive this configuration\n- This setting primarily affects additional access log buckets beyond the core solution buckets"
        ),
    ] = True
    imported_bucket: Annotated[
        ImportedS3ManagedEncryptionKeyBucketConfig | None,
        Field(
            alias="importedBucket",
            description="**Imported Bucket Configuration** *(Optional)*\n\nWhen set, the accelerator will import an existing access logs bucket.\n\nUse this configuration to import an existing access logs bucket and manage its resource policy through the solution.\n\n**Important Requirements**\n- Both source and destination buckets must be in the same AWS Region and owned by the same account\n- The bucket must be pre-created in each target account and region using a repeatable naming pattern\n- Include ${ACCOUNT_ID} and ${REGION} parameters in your naming pattern for automatic population\n\n**Example** ```yaml importedBucket:   name: existing-access-log-bucket-${ACCOUNT_ID}-${REGION}   applyAcceleratorManagedBucketPolicy: true ```",
            validate_default=True,
        ),
    ] = None
    lifecycle_rules: Annotated[
        list[LifecycleRule] | None,
        Field(
            alias="lifecycleRules",
            description="**S3 Lifecycle Rules** *(Optional)*\n\nConfigure lifecycle rules for the access log bucket to manage log retention and storage costs. Rules can transition logs to different storage classes and set expiration policies.\n\n**Example** ```yaml lifecycleRules:   - enabled: true     id: AccessLifecycle-01     expiration: 365     transitions:       - storageClass: GLACIER         transitionAfter: 30 ```",
        ),
    ] = None
    s3_resource_policy_attachments: Annotated[
        list[ResourcePolicyStatement] | None,
        Field(
            alias="s3ResourcePolicyAttachments",
            description="**S3 Resource Policy Attachments** *(Optional)*\n\nPolicy statements from the listed files will be added to the bucket resource policy. This property cannot be used when customPolicyOverrides.s3Policy property has value.\n\n**Note**: When Block Public Access is enabled for S3 on the AWS account, you can't specify a policy that would make the S3 Bucket public.\n\n**Example** ```yaml s3ResourcePolicyAttachments:   - policy: s3-policies/access-log-policy.json   - policy: s3-policies/cross-account-access.json ```",
        ),
    ] = None


class CentralLogBucketConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    custom_policy_overrides: Annotated[
        CustomS3ResourceAndKmsPolicyOverridesConfig | None,
        Field(
            alias="customPolicyOverrides",
            description="**Custom Policy Overrides Configuration** *(Optional)*\n\nProvide policy overrides. Policy files must contain a complete policy document.\n\n**Conflicts**\n- When s3Policy is defined, importedBucket.applyAcceleratorManagedBucketPolicy cannot be true\n- When s3Policy is defined, s3ResourcePolicyAttachments cannot be defined\n- When kmsPolicy is defined, importedBucket.createAcceleratorManagedKey cannot be true\n- When kmsPolicy is defined, kmsResourcePolicyAttachments cannot be defined\n\n**Example** ```yaml customPolicyOverrides:   s3Policy: path/to/policy.json   kmsPolicy: kms/full-central-logs-bucket-key-policy.json ```",
            validate_default=True,
        ),
    ] = None
    imported_bucket: Annotated[
        ImportedS3ManagedEncryptionKeyBucketConfig | None,
        Field(
            alias="importedBucket",
            description="**Imported Bucket Configuration** *(Optional)*\n\nWhen set, the accelerator will import an existing central logs bucket.\n\nUse this configuration to import an existing central logs bucket, manage bucket resource policy and KMS policy through the solution.\n\n**Example** ```yaml importedBucket:   name: existing-central-log-bucket   applyAcceleratorManagedBucketPolicy: true   createAcceleratorManagedKey: true ```",
            validate_default=True,
        ),
    ] = None
    kms_resource_policy_attachments: Annotated[
        list[ResourcePolicyStatement] | None,
        Field(
            alias="kmsResourcePolicyAttachments",
            description="**KMS Resource Policy Attachments** *(Optional)*\n\nPolicy statements from the listed files will be added to the bucket encryption key policy.\n\n**Notes**\n- Cannot be used when customPolicyOverrides.kmsPolicy property has value\n- When importing a central logs bucket with createAcceleratorManagedKey set to false, this property must be undefined\n- The Central Logs Bucket will allow customers to have SSE-S3 (Amazon S3 managed keys) or SSE-KMS keys. Only SSE-KMS keys can adopt the KMS resource policy files.\n\n**Example** ```yaml kmsResourcePolicyAttachments:   - policy: kms-policies/central-log-key-policy.json ```",
        ),
    ] = None
    lifecycle_rules: Annotated[
        list[LifecycleRule] | None,
        Field(
            alias="lifecycleRules",
            description="**S3 Lifecycle Rules** *(Optional)*\n\nConfigure lifecycle rules for the central log bucket to manage log retention and storage costs. Rules can transition logs to different storage classes and set expiration policies.\n\n**Example** ```yaml lifecycleRules:   - enabled: true     id: CentralLifecycleRule-01     expiration: 365     transitions:       - storageClass: GLACIER         transitionAfter: 30 ```",
        ),
    ] = None
    s3_resource_policy_attachments: Annotated[
        list[ResourcePolicyStatement] | None,
        Field(
            alias="s3ResourcePolicyAttachments",
            description="**S3 Resource Policy Attachments** *(Optional)*\n\nPolicy statements from the listed files will be added to the bucket resource policy. This property cannot be used when customPolicyOverrides.s3Policy property has value.\n\n**Note**: When Block Public Access is enabled for S3 on the AWS account, you can't specify a policy that would make the S3 Bucket public.\n\n**Example** ```yaml s3ResourcePolicyAttachments:   - policy: s3-policies/central-log-policy.json   - policy: s3-policies/cross-account-access.json ```",
        ),
    ] = None


class CloudTrailConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    account_trails: Annotated[
        list[AccountCloudTrailConfig] | None,
        Field(
            alias="accountTrails",
            description="**Account Trails** *(Optional)*\n\nConfigurations for account-level trails to be created by the LZA deployment.",
        ),
    ] = None
    enable: Annotated[
        bool,
        Field(
            description="**Enable** *(Required)*\n\nWhether or not to enable CloudTrail. This setting alone does not create any trails. Enabling  {@link  ICloudTrailConfig.organizationTrail }  will create an organization-level trail. Additionally, you can setup account-level trails."
        ),
    ]
    lifecycle_rules: Annotated[
        list[LifecycleRule] | None,
        Field(alias="lifecycleRules", description="**S3 Log Bucket Lifecycle Rules** *(Optional)*\n\nOptional lifecycle rules for the S3 log bucket"),
    ] = None
    organization_trail: Annotated[
        bool,
        Field(
            alias="organizationTrail",
            description="**Organization Trail** *(Required)*\n\nWhen enabled alongside  {@link  ICloudTrailConfig.enable } , LZA will create an organization-level trail.",
        ),
    ]
    organization_trail_settings: Annotated[
        CloudTrailSettingsConfig | None,
        Field(
            alias="organizationTrailSettings",
            description="**Organization Trail Settings** *(Optional)*\n\nContains optional settings for the organization-level trail.",
        ),
    ] = None


class ControlTowerConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    controls: Annotated[
        list[ControlTowerControlConfig] | None,
        Field(
            description="**Control Tower Guardrails** *(Optional)*\n\nConfiguration for additional Control Tower guardrails (controls) beyond the mandatory ones. Allows enablement of strongly recommended and elective controls across organizational units.\n\n**Control Types**\n\n- **Mandatory**: Automatically enabled by Control Tower (cannot be disabled)\n- **Strongly Recommended**: Best practice controls that should be enabled\n- **Elective**: Additional controls for specific compliance requirements\n\n**Deployment Considerations**\n\n- **Concurrency Limit**: Maximum 10 concurrent control operations\n- **Batch Processing**: Deploy controls in batches to avoid throttling\n- **OU Restrictions**: Some controls cannot be deployed to Security OU\n- **Regional Scope**: Controls can be region-specific or global\n\n**Usage Examples**\n\n```yaml controls:   # Strongly recommended control   - identifier: AWS-GR_RDS_INSTANCE_PUBLIC_ACCESS_CHECK     enable: true     deploymentTargets:       organizationalUnits:         - Workloads         - Sandbox\n\n  # Elective control with regional scope   - identifier: AWS-GR_EC2_INSTANCE_IMDSv2_CHECK     enable: true     regions:       - us-east-1       - us-west-2     deploymentTargets:       organizationalUnits:         - Production\n\n  # Global control using opaque identifier   - identifier: m7a5gbdf08wg2o0en010mkng     enable: true     deploymentTargets:       organizationalUnits:         - Infrastructure ```\n\n**Best Practices**\n\n- Enable controls gradually in batches of 10 or fewer\n- Test controls in non-production OUs first\n- Review control documentation for OU compatibility\n- Monitor control status and compliance in Control Tower console"
        ),
    ] = None
    enable: Annotated[
        bool,
        Field(
            description="**Enable Control Tower** *(Required)*\n\nControls whether AWS Control Tower Landing Zone is enabled for the deployment. When enabled, the accelerator ensures the account configuration includes the three mandatory Control Tower accounts.\n\n**Required Accounts**\n\nWhen Control Tower is enabled, these accounts must be defined in accounts-config.yaml:\n- **Management Account**: Primary account for organizational management and billing\n- **Log Archive Account**: Centralized logging and log retention\n- **Audit Account**: Security auditing and compliance monitoring\n\n**Prerequisites**\n\n- AWS Organizations must be enabled in the management account\n- All features must be enabled in AWS Organizations\n- The management account must have appropriate permissions\n- Required service-linked roles must be created\n\n```yaml # Enable Control Tower integration enable: true\n\n# Disable Control Tower (standalone LZA deployment) enable: false ```"
        ),
    ]
    landing_zone: Annotated[
        ControlTowerLandingZoneConfig | None,
        Field(
            alias="landingZone",
            description="**Control Tower Landing Zone Configuration** *(Optional)*\n\nAdvanced configuration options for the Control Tower Landing Zone, including version management, logging settings, and security configurations.\n\n**Key Configuration Areas**\n\n- **Version Management**: Specify Landing Zone version for updates and resets\n- **Logging Configuration**: Control log retention and CloudTrail settings\n- **Security Settings**: Configure Identity Center access and authentication\n\n\n**Usage Example**\n\n```yaml landingZone:   version: '3.3'  # Must be latest available version   logging:     loggingBucketRetentionDays: 365      # 1 year retention     accessLoggingBucketRetentionDays: 90  # 90 day access logs     organizationTrail: true               # Enable org-wide CloudTrail   security:     enableIdentityCenterAccess: true      # Enable centralized access ```\n\n**Update Considerations**\n\n- Landing Zone updates require the latest version number\n- Configuration changes trigger Landing Zone reset/update\n- Updates may take 60-90 minutes to complete\n- Existing resources and configurations are preserved",
        ),
    ] = None


class CostAndUsageReportConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    additional_artifacts: Annotated[
        list[str] | None,
        Field(
            alias="additionalArtifacts",
            description="**Additional Artifacts** *(Optional)*\n\nA list of manifests that AWS creates for this report to enable integration with other AWS analytics services.\n\n**Available Artifacts**\n- `REDSHIFT`: Creates manifest files for Amazon Redshift integration\n- `QUICKSIGHT`: Creates manifest files for Amazon QuickSight integration\n- `ATHENA`: Creates manifest files for Amazon Athena integration\n\n**Example** ```yaml additionalArtifacts:   - ATHENA   - QUICKSIGHT ```",
        ),
    ] = None
    additional_schema_elements: Annotated[
        list[NonEmptyString] | None,
        Field(
            alias="additionalSchemaElements",
            description="**Additional Schema Elements** *(Optional)*\n\nAdditional content that AWS includes in the report, such as individual resource IDs. These elements provide more granular data for detailed cost analysis.",
        ),
    ] = None
    compression: Annotated[
        str,
        Field(
            description="**Compression Format** *(Required)*\n\nThe compression format that AWS uses for the report files.\n\n**Example** ```yaml compression: Parquet ```"
        ),
    ]
    format: Annotated[
        str,
        Field(description="**Report Format** *(Required)*\n\nThe format that AWS saves the report in.\n\n**Example** ```yaml format: Parquet ```"),
    ]
    lifecycle_rules: Annotated[
        list[LifecycleRule] | None,
        Field(
            alias="lifecycleRules",
            description="**S3 Lifecycle Rules** *(Optional)*\n\nConfiguration for S3 bucket lifecycle rules to manage the cost and storage of your Cost and Usage Reports over time.\n\n**Key Benefits**\n- Automatically transition older reports to cheaper storage classes\n- Set expiration policies to delete old reports\n- Optimize storage costs for long-term report retention\n\n**Example** ```yaml lifecycleRules:   - enabled: true     id: CostAndUsageBucketLifecycleRule-01     expiration: 2555  # 7 years     transitions:       - storageClass: STANDARD_IA         transitionAfter: 30       - storageClass: GLACIER         transitionAfter: 365       - storageClass: DEEP_ARCHIVE         transitionAfter: 1095  # 3 years ```",
        ),
    ] = None
    refresh_closed_reports: Annotated[
        bool,
        Field(
            alias="refreshClosedReports",
            description="**Refresh Closed Reports** *(Required)*\n\nWhether AWS should update your reports after they have been finalized if AWS detects charges related to previous months. These charges can include refunds, credits, or support fees.\n\n**When to Enable**\n- Enable if you need the most accurate historical data\n- Enable if you frequently receive refunds or credits\n- Enable for compliance and auditing requirements\n\n**When to Disable**\n- Disable if you prefer immutable historical reports\n- Disable to reduce processing overhead\n\n**Example** ```yaml refreshClosedReports: true ```",
        ),
    ]
    report_name: Annotated[
        str,
        Field(
            alias="reportName",
            description="**Report Name** *(Required)*\n\nThe name of the report that you want to create\n\n**Naming Requirements**\n- Must be unique within the AWS account\n- Case sensitive\n- Cannot contain spaces\n\n**Example** ```yaml reportName: accelerator-cur ```",
            min_length=1,
        ),
    ]
    report_versioning: Annotated[
        str,
        Field(
            alias="reportVersioning",
            description="**Report Versioning** *(Required)*\n\nWhether AWS should overwrite the previous version of each report or deliver the report in addition to the previous versions.\n\n**Available Options**\n- `CREATE_NEW_REPORT`: Creates a new report file for each delivery (recommended)\n- `OVERWRITE_REPORT`: Overwrites the previous report file\n\n**Considerations**\n- `CREATE_NEW_REPORT` provides better audit trail and version history\n- `OVERWRITE_REPORT` uses less storage but loses historical versions\n\n**Example** ```yaml reportVersioning: CREATE_NEW_REPORT ```",
        ),
    ]
    s3_prefix: Annotated[
        str,
        Field(
            alias="s3Prefix",
            description="**S3 Prefix** *(Required)*\n\nThe prefix that AWS adds to the report name when delivering the report to S3. This helps organize reports within the S3 bucket structure.\n\n**Notes**\n- Cannot include spaces\n- Used to organize reports in S3 bucket\n- Helps with lifecycle management and access control\n\n**Example** ```yaml s3Prefix: cur ```",
            min_length=1,
        ),
    ]
    time_unit: Annotated[
        str,
        Field(
            alias="timeUnit",
            description="**Time Unit** *(Required)*\n\nThe granularity of the line items in the report. This determines how frequently the report data is aggregated.\n\n**Available Options**\n- `HOURLY`: Hourly granularity (most detailed, higher costs)\n- `DAILY`: Daily granularity (recommended for most use cases)\n- `MONTHLY`: Monthly granularity (least detailed, lower costs)\n\n**Cost Considerations**\n- Hourly reports are more expensive but provide the most detail\n- Daily reports offer a good balance of detail and cost\n- Monthly reports are the most cost-effective but least granular\n\n**Example** ```yaml timeUnit: DAILY ```",
        ),
    ]


class ElbLogBucketConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    custom_policy_overrides: Annotated[
        CustomS3ResourcePolicyOverridesConfig | None,
        Field(
            alias="customPolicyOverrides",
            description="**Custom Policy Overrides Configuration** *(Optional)*\n\nProvide policy overrides. Policy files must contain a complete policy document. Custom policy overrides can ONLY be applied to imported buckets.\n\n**Conflicts**\n- When s3Policy is defined, importedBucket.applyAcceleratorManagedBucketPolicy cannot be true\n- When s3Policy is defined, s3ResourcePolicyAttachments cannot be defined\n\n**Example** ```yaml customPolicyOverrides:   s3Policy: path/to/elb-log-policy.json ```",
            validate_default=True,
        ),
    ] = None
    imported_bucket: Annotated[
        ImportedS3ManagedEncryptionKeyBucketConfig | None,
        Field(
            alias="importedBucket",
            description="**Imported Bucket Configuration** *(Optional)*\n\nWhen set, the accelerator will import an existing ELB logs bucket.\n\nUse this configuration to import an existing ELB logs bucket and manage its resource policy through the solution.\n\n**Important Note**: If importing your own ELB Log buckets, be sure to create the buckets in the LogArchive account and a bucket within each operating region that LZA is configured in.\n\n**Example** ```yaml importedBucket:   name: existing-elb-log-bucket   applyAcceleratorManagedBucketPolicy: true ```",
            validate_default=True,
        ),
    ] = None
    lifecycle_rules: Annotated[
        list[LifecycleRule] | None,
        Field(
            alias="lifecycleRules",
            description="**S3 Lifecycle Rules** *(Optional)*\n\nConfigure lifecycle rules for the ELB log bucket to manage log retention and storage costs. Rules can transition logs to different storage classes and set expiration policies.\n\n**Example** ```yaml lifecycleRules:   - enabled: true     id: ElbLifecycleRule-01     expiration: 365     transitions:       - storageClass: GLACIER         transitionAfter: 30 ```",
        ),
    ] = None
    s3_resource_policy_attachments: Annotated[
        list[ResourcePolicyStatement] | None,
        Field(
            alias="s3ResourcePolicyAttachments",
            description="**S3 Resource Policy Attachments** *(Optional)*\n\nPolicy statements from the listed files will be added to the bucket resource policy. This property cannot be used when customPolicyOverrides.s3Policy property has value.\n\n**Note**: When Block Public Access is enabled for S3 on the AWS account, you can't specify a policy that would make the S3 Bucket public.\n\n**Example** ```yaml s3ResourcePolicyAttachments:   - policy: s3-policies/elb-log-policy.json   - policy: s3-policies/cross-account-access.json ```",
        ),
    ] = None


class LoggingConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    access_log_bucket: Annotated[
        AccessLogBucketConfig | None,
        Field(
            alias="accessLogBucket",
            description="**Access Logs Bucket** *(Optional)*\n\nUsed to define and configure the access logs bucket for the solution.",
        ),
    ] = None
    account: Annotated[
        str,
        Field(
            description="**Account Name** *(Required)*\n\nThe name of the account used to store the logs.\n\n**Example ```yaml account: LogArchive ```",
            min_length=1,
        ),
    ]
    asset_bucket: Annotated[
        AssetBucketConfig | None,
        Field(alias="assetBucket", description="**Asset Bucket** *(Optional)*\n\nUsed to define and configure the asset bucket for the solution."),
    ] = None
    central_log_bucket: Annotated[
        CentralLogBucketConfig | None,
        Field(
            alias="centralLogBucket",
            description="**Central Log Bucket** *(Optional)*\n\nUsed to define and configure the central logs bucket for the solution",
        ),
    ] = None
    centralized_logging_region: Annotated[
        str | None,
        Field(
            alias="centralizedLoggingRegion",
            description="**Centralized Logging Region** *(Optional)*\n\nThe region used to store the logs. When not provided, the log bucket will be created in the home region.",
            min_length=1,
        ),
    ] = None
    cloudtrail: Annotated[
        CloudTrailConfig,
        Field(
            description="**CloudTrail Configuration** *(Required)*\n\nMain configuration for CloudTrail\n\n**Key Features**\n- Enable/Disable CloudTrail\n- Setup organization-level trails\n- Setup account-level trails"
        ),
    ]
    cloudwatch_logs: Annotated[
        CloudWatchLogsConfig | None,
        Field(
            alias="cloudwatchLogs",
            description="**CloudWatch Logs Configuration** *(Optional)*\n\nConfigure CloudWatch logs for the solution.\n\n**Key Features**\n- Configure encryption at rest\n- Enable replication\n- Configure CloudWatch logs subscriptions",
        ),
    ] = None
    elb_log_bucket: Annotated[
        ElbLogBucketConfig | None,
        Field(
            alias="elbLogBucket", description="**ELB Log Bucket** *(Optional)*\n\nUsed to define and configure the ELB logs bucket for the solution"
        ),
    ] = None
    session_manager: Annotated[
        SessionManagerConfig,
        Field(
            alias="sessionManager",
            description="**SessionManager Configuration** *(Required)*\n\nAllows for the customization of SessionManager in the environment allowing the modifications such as where to save logs and what accounts to manage.",
        ),
    ]


class ReportConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    budgets: Annotated[
        list[BudgetReportConfig] | None,
        Field(
            description="**Budget Reports** *(Optional)*\n\nConfiguration for budget reports.\n\n**Example** ```yaml budgets:     - name: accel-budget       timeUnit: MONTHLY       type: COST       amount: 2000       includeUpfront: true       includeTax: true       includeSupport: true       includeSubscription: true       includeRecurring: true       includeOtherSubscription: true       includeDiscount: true       includeCredit: false       includeRefund: false       useBlended: false       useAmortized: false       unit: USD       notifications:       - type: ACTUAL         thresholdType: PERCENTAGE         threshold: 90         comparisonOperator: GREATER_THAN         subscriptionType: EMAIL         address: myemail+pa-budg@example.com ```"
        ),
    ] = None
    cost_and_usage_report: Annotated[
        CostAndUsageReportConfig | None,
        Field(
            alias="costAndUsageReport",
            description="**Cost and Usage Report** *(Optional)*\n\nConfiguration for a cost and usage report.\n\n\n**Example** ```yaml costAndUsageReport:     compression: Parquet     format: Parquet     reportName: accelerator-cur     s3Prefix: cur     timeUnit: DAILY     refreshClosedReports: true     reportVersioning: CREATE_NEW_REPORT     lifecycleRules:       storageClass: DEEP_ARCHIVE       enabled: true       multiPart: 1       expiration: 1825       deleteMarker: false       nonCurrentExpiration: 366       transitionAfter: 365 ```",
        ),
    ] = None


class GlobalConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    accelerator_metadata: Annotated[
        AcceleratorMetadataConfig | None,
        Field(
            alias="acceleratorMetadata",
            description="**Accelerator Metadata Configuration** *(Optional)*\n\nEnable and customize the collection of LZA metadata in your environment.\n\n**Key Features**\n- Enable the collection of LZA metadata\n- Specify an account to store the metadata\n- Provision access to IAM roles for the metadata\n\n**Example** ```yaml acceleratorMetadata:   enable: true   account: Logging   readOnlyAccessRoleArns:     - arn:aws:iam::111111111111:role/test-access-role ```",
        ),
    ] = None
    accelerator_settings: Annotated[
        AcceleratorSettingsConfig | None,
        Field(
            alias="acceleratorSettings",
            description="**Accelerator Settings Configuration** *(Optional)*\n\nEnables the modification of additional LZA properties\n\n**Example** ```yaml acceleratorSettings:  maxConcurrentStacks: 100 ```",
        ),
    ] = None
    backup: Annotated[
        BackupConfig | None,
        Field(
            description="**Backup Vaults Configuration** *(Optional)*\n\nUsed to generate Backup Vaults\n\n**Example** ```yaml backup:   vaults:     - name: MyBackUpVault       deploymentTargets:         organizationalUnits:           - Root ```"
        ),
    ] = None
    cdk_options: Annotated[
        CdkOptionsConfig | None,
        Field(
            alias="cdkOptions", description="**AWS CDK Options Configuration**\n\nEnables the customization of the operation of the CDK within LZA"
        ),
    ] = None
    central_root_user_management: Annotated[
        CentralRootUserManagementConfig | None,
        Field(
            alias="centralRootUserManagement",
            description="**Central Root User Configuration** *(Optional)*\n\nCentrally managing root enables the removal of root user credentials from the organization's member accounts. Tasks requiring root access can then be performed by the organization's management account. This configuration dictates whether or not root user management is centralized for the organization.\n\n**Example** ```yaml centralRootUserManagement:   enable: true   capabilities:     rootCredentialsManagement: true     allowRootSessions: true ```",
        ),
    ] = None
    centralize_cdk_buckets: Annotated[
        CentralizeCdkBucketsConfig | None,
        Field(
            alias="centralizeCdkBuckets",
            deprecated="Use {@link IGlobalConfig.cdkOptions }NOTICE: The configuration of CDK buckets is being moved\nto cdkOptions in the Global Config. This block is deprecated and\nwill be removed in a future release\n\nIndicates whether workload accounts should utilize the cdk-assets S3 buckets in the management account\n\n**Example**\n\n```yaml\ncentralizeCdkBuckets:\nenable: true\n```",
        ),
    ] = None
    cloudwatch_log_retention_in_days: Annotated[
        float,
        Field(
            alias="cloudwatchLogRetentionInDays",
            description="**CloudWatch Log Retention** *(Required)*\n\nThe retention period, specified in days, is applied to all CloudWatch log groups created by the LZA. Additionally, this retention period will be applied to any pre-existing CloudWatch log group with a shorter retention period.\n\n**Example Scenarios**\n\nScenario 1: If `cloudWatchRetentionInDays` is set to 365, and create a new CloudWatch log group with a 730-day retention period, the LZA will update the log group to have a 365-day retention period.\n\nScenario 2: If `cloudWatchRetentionInDays` is set to 365, and there is an existing CloudWatch log group with a 730-day retention period, the log group will not be updated by the LZA.\n\nScenario 3: If `cloudWatchRetentionInDays` is set to 365, and there is an existing CloudWatch log group with a 30-day retention period, the LZA will update the log group to have a 365-day retention period.",
        ),
    ]
    control_tower: Annotated[
        ControlTowerConfig,
        Field(
            alias="controlTower",
            description="**AWS Control Tower Configuration** *(Required)*\n\nConfigure Control Tower for the LZA deployment.\n\n**Key Features**\n- Enable/Disable Control Tower\n- Set Control Tower controls\n- Configure Control Tower Landing Zone",
        ),
    ]
    default_event_bus: Annotated[
        DefaultEventBusConfig | None,
        Field(
            alias="defaultEventBus",
            description="**Default Event Bus Configuration** *(Optional)*\n\nDefine a custom policy which the solution will automatically apply to the default event bus within targeted accounts.\n\n\n**Example** ``` defaultEventBus:   policy: path-to-my-policy.json   deploymentTargets:     accounts:       - Management } ```",
        ),
    ] = None
    enable_opt_in_regions: Annotated[
        bool | None,
        Field(
            alias="enableOptInRegions",
            description="**Enable opt-in Regions** *(Optional)*\n\nWhether or not to automatically enable opt-in regions configured for all LZA managed accounts\n\nWhen enableOptInRegions is set to true, it will only enable the opt-in regions that are also listed in the  {@link  IGlobalConfig.enabledRegions enabledRegions }  configuration.",
        ),
    ] = False
    enabled_regions: Annotated[
        list[str],
        Field(
            alias="enabledRegions",
            description="**Enabled Regions** *(Required)*\n\nList of AWS Regions where accelerator will be deployed.  {@link  IGlobalConfig.homeRegion Home region }  must be part of this list.\n\n**Example**\n\n```yaml enabledRegions:   - us-east-1   - us-west-2 ```",
        ),
    ]
    external_landing_zone_resources: Annotated[
        ExternalLandingZoneResourcesConfig | None,
        Field(
            alias="externalLandingZoneResources",
            description="**External Landing Zone Resources Configuration** *(Optional)*\n\nUsed when importing resources from an existing Amazon Secure Environment Accelerator (ASEA) environment.\n\n**Example** ```yaml externalLandingZoneResources:   importExternalLandingZoneResources: false ```",
        ),
    ] = None
    home_region: Annotated[
        str,
        Field(
            alias="homeRegion",
            description="**Accelerator Home Region Name** *(Required)*\n\nThe region where the accelerator pipeline will be deployed\n\n**Example**\n\n```yaml homeRegion: us-east-1 ```",
            min_length=1,
        ),
    ]
    lambda_: Annotated[
        LambdaConfig | None,
        Field(
            alias="lambda",
            description="**Lambda Configuration** *(Optional)*\n\nUsed to configure encryption for Lambda function environment variables across the LZA environment.\n\n\n**Example** ```yaml lambda:   encryption:    useCMK: true    deploymentTargets:      organizationalUnits:        - Root ```",
        ),
    ] = None
    limits: Annotated[
        list[ServiceQuotaLimitsConfig] | None,
        Field(
            description="**AWS Service Quota Limit Configuration**\n\nEnables the creation of service quota increases for accounts within the LZA deployment.\n\n**Considerations** Service quotas define the maximum number of service resources or operations for your AWS account. Service quota increases are processed asynchronously and may require approval. Some quotas require AWS Support cases for increases beyond certain thresholds. Quotas are account-specific and region-specific (where applicable). You can find service and quota codes in the AWS Service Quotas console.\n\nFor more information, see:\n- [AWS Service Quotas User Guide](https://docs.aws.amazon.com/servicequotas/latest/userguide/intro.html)\n- [Requesting a quota increase](https://docs.aws.amazon.com/servicequotas/latest/userguide/request-quota-increase.html)\n\n**Example** ```yaml limits:   # Increase Lambda concurrent executions   - serviceCode: lambda     quotaCode: L-B99A9384     desiredValue: 1000     deploymentTargets:       organizationalUnits:         - Root     regions:       - us-west-2\n\n  # Increase IAM roles per account (global quota - no regions needed)   - serviceCode: iam     quotaCode: L-4019AD8B     desiredValue: 15     deploymentTargets:       accounts:         - SharedServices\n\n  # Increase VPCs per region   - serviceCode: vpc     quotaCode: L-F678F1CE     desiredValue: 20     deploymentTargets:       organizationalUnits:         - Security         - Infrastructure     regions:       - us-east-1       - us-west-2\n\n  # Increase Route 53 Resolver rules per region   - serviceCode: route53resolver     quotaCode: L-4A669CC0     desiredValue: 10     deploymentTargets:       organizationalUnits:         - Infrastructure ```"
        ),
    ] = None
    logging: Annotated[
        LoggingConfig,
        Field(
            description="**Logging Configuration** *(Required)*\n\nUsed to configure logging for the LZA deployment. Enables the configuration of logging for Session Manager, CloudTrail, and CloudWatch."
        ),
    ]
    management_account_access_role: Annotated[
        str,
        Field(
            alias="managementAccountAccessRole",
            description="**Management Account Access Role** *(Required)*\n\nName of the management account access role created in member accounts.\n\n**Example** ```yaml managementAccountAccessRole: AWSControlTowerExecution ```",
            min_length=1,
        ),
    ]
    reports: Annotated[
        ReportConfig | None,
        Field(description="**Report Configuration** *(Optional)*\n\nConfiguration for cost and usage reports as well as budgets."),
    ] = None
    s3: Annotated[
        S3GlobalConfig | None,
        Field(
            description="**AWS S3 Global Configuration** *(Optional)*\n\nUsed to configure AWS S3 server side encryption for S3 buckets across the LZA environment. The configuration is able to target OUs, regions, or accounts. When left undefined, the solution will utilize AWS KMS CMK to encrypt the AWS S3 buckets.\n\n**Notes** This configuration is not applicable to LogArchive's central logging region, because the solution deployed CentralLogs bucket always encrypted with AWS KMS CMK. This configuration is not applicable to the Management account Asset bucket in the home region. This bucket will always have a key generated and applied to the bucket if it is created. This configuration is not applicable to the assets S3 bucket if the bucket is created. This bucket will always have a key generated and applied.\n\n For more information please see [here](https://docs.aws.amazon.com/AmazonS3/latest/userguide/UsingEncryption.html)\n\n**Example** ```yaml s3:   createCMK: true   deploymentTargets:     organizationalUnits:       - Root ```"
        ),
    ] = None
    sns_topics: Annotated[
        SnsConfig | None,
        Field(
            alias="snsTopics",
            description="**SNS Topics Configuration** *(Optional)*\n\nDefine SNS topics to be deployed throughout the LZA environment.\n\nTo send CloudWatch Alarms and SecurityHub notifications, you will need to configure at least one SNS Topic. For SecurityHub notifications, you will need to set the deployment target OU to Root in order to receive notifications from all accounts.\n\n**Example** ```yaml snsTopics:   deploymentTargets:     organizationalUnits:       - Root   topics:     - name: Security       emailAddresses:         - SecurityNotifications@example.com ```",
        ),
    ] = None
    sqs: Annotated[
        SqsConfig | None,
        Field(
            description="**SQS Queue Configuration** *(Optional)*\n\nUsed to configure encryption for SQS queues throughout the LZA environment. The configuration is able to target OUs, regions, or accounts. When left undefined, the solution will utilize AWS KMS CMK to encrypt SQS queues.\n\n**Example** ```yaml sqs:   encryption:    useCMK: true    deploymentTargets:      organizationalUnits:        - Root ```"
        ),
    ] = None
    ssm_inventory: Annotated[
        SsmInventoryConfig | None,
        Field(
            alias="ssmInventory", description="**SSM Inventory Configuration** *(Optional)*\n\nAllows enabling of SSM Inventory in member accounts"
        ),
    ] = None
    ssm_parameters: Annotated[
        list[SsmParametersConfig] | None,
        Field(
            alias="ssmParameters",
            description="**SSM parameter configurations** *(Optional)*\n\nCreate SSM parameters through the LZA. Parameters can be deployed to Organizational Units or Accounts through the use of deployment targets.\n\n**Example** ```yaml ssmParameters:   - deploymentTargets:       organizationalUnits:         - Workloads     parameters:       - name: WorkloadParameter         path: /my/custom/path/variable         value: 'MySSMParameterValue' ```",
        ),
    ] = None
    stack_policy: Annotated[
        StackPolicyConfig | None,
        Field(
            alias="stackPolicy",
            description="**Stack Policy Configuration** *(Optional)*\n\nDefine which resource types should be protected. Defined resource types will be protected for Update:Replace and Update:Delete operation. Protected types need to be AWS:: resource types e.g. AWS::EC2::InternetGateway.\n\n\n**Example** ```yaml stackPolicy:   enable: true   protectedTypes: ['AWS::EC2::InternetGateway'] ```",
        ),
    ] = None
    tags: Annotated[
        list[Tag] | None,
        Field(
            description="**Tags** *(Optional)*\n\nGlobal tags to be applied to all resources created by the solution.\n\n**Note** LZA will not apply the tags to all resource types. Excluded types include Transit Gateway Route Tables and Route53 Resolver Endpoints.\n\n**Example** ```yaml tags:   - key: Environment     value: Dev   - key: ResourceOwner     value: AcmeApp   - key: CostCenter     value: '123' ```"
        ),
    ] = None
    termination_protection: Annotated[
        bool | None,
        Field(
            alias="terminationProtection",
            description="**Termination Protection** *(Optional)*\n\nWhether or not termination protection should be enabled for this stack",
        ),
    ] = None
    use_v2_stacks: Annotated[
        bool | None,
        Field(
            alias="useV2Stacks",
            description="**V2 Stacks** *(Optional)*\n\nWhether or not V2 Stacks should be enabled.\n\nWhen enabled, LZA will place newly defined resources in separate CloudFormation stacks to prevent exceeding the 500 resource per stack limit. Pre-existing resources will be preserved in their original stacks.\n\nNew deployments will have this property set to `true` in the initial config. Once enabled, this property cannot be set back to `false`.",
        ),
    ] = False


type Model = GlobalConfig

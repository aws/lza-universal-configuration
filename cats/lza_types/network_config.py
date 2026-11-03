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

from enum import Enum, StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field


class AlbListenerProtocolEnum(StrEnum):
    http = "HTTP"
    https = "HTTPS"


class AlbListenerTypeEnum(StrEnum):
    fixed_response = "fixed-response"
    forward = "forward"
    redirect = "redirect"


class AlbRoutingHttpConfigMitigationModeEnum(StrEnum):
    monitor = "monitor"
    defensive = "defensive"
    strictest = "strictest"


class AlbSchemeEnum(StrEnum):
    internet_facing = "internet-facing"
    internal = "internal"


class AllowDeny(StrEnum):
    allow = "allow"
    deny = "deny"


class AlpnPolicyEnum(StrEnum):
    http1_only = "HTTP1Only"
    http2_only = "HTTP2Only"
    http2_optional = "HTTP2Optional"
    http2_preferred = "HTTP2Preferred"
    none = "None"


class CertificateConfigType(StrEnum):
    import_ = "import"
    request = "request"


class CertificateValidationType(StrEnum):
    email = "EMAIL"
    dns = "DNS"


class DnsFirewallBlockResponseType(StrEnum):
    nodata = "NODATA"
    nxdomain = "NXDOMAIN"
    override = "OVERRIDE"


class DnsFirewallManagedDomainListsType(StrEnum):
    aws_managed_domains_aggregate_threat_list = "AWSManagedDomainsAggregateThreatList"
    aws_managed_domains_botnet_commandand_control = "AWSManagedDomainsBotnetCommandandControl"
    aws_managed_domains_malware_domain_list = "AWSManagedDomainsMalwareDomainList"


class DnsFirewallRuleActionType(StrEnum):
    allow = "ALLOW"
    alert = "ALERT"
    block = "BLOCK"


class DpdTimeoutActionType(StrEnum):
    clear = "clear"
    none = "none"
    restart = "restart"


class DxVirtualInterfaceType(StrEnum):
    private = "private"
    transit = "transit"


class EnableDisable(StrEnum):
    enable = "enable"
    disable = "disable"


class EncryptionAlgorithmType(StrEnum):
    aes128 = "AES128"
    aes256 = "AES256"
    aes128_gcm_16 = "AES128-GCM-16"
    aes256_gcm_16 = "AES256-GCM-16"


class GatewayEndpointType(StrEnum):
    s3 = "s3"
    dynamodb = "dynamodb"


class GatewayRouteTableType(StrEnum):
    internet_gateway = "internetGateway"
    virtual_private_gateway = "virtualPrivateGateway"


class AlbListenerTargetGroupStickinessConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    duration_seconds: Annotated[
        float | None,
        Field(
            alias="durationSeconds",
            description="The time period, in seconds, during which requests from a client should be routed to the same target group. The range is 1-604800 seconds (7 days).",
        ),
    ] = None
    enabled: Annotated[bool | None, Field(description="Indicates whether target group stickiness is enabled.")] = None


class DefaultVpcsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    delete: Annotated[bool, Field(description="Enable to delete default VPCs.")]
    exclude_accounts: Annotated[
        list[str] | None,
        Field(alias="excludeAccounts", description="(OPTIONAL) Include an array of friendly account names to exclude from default VPC deletion."),
    ] = None
    exclude_regions: Annotated[
        list[str] | None,
        Field(alias="excludeRegions", description="(OPTIONAL) Include an array of AWS regions to exclude from default VPC deletion."),
    ] = None


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


class IcmpRuleConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: Annotated[float, Field(description="The ICMP code number. A value of -1 indicates all types.")]
    type: Annotated[float, Field(description="The ICMP type number. A value of -1 indicates all types.")]


class NfwRuleSourceStatelessPortRangeConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    from_port: Annotated[float, Field(alias="fromPort", description="The port to start from in the range.")]
    to_port: Annotated[float, Field(alias="toPort", description="The port to end with in the range.")]


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


class HostnameType(StrEnum):
    ip_name = "ip-name"
    resource_name = "resource-name"


class SubnetPrivateDnsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enable_dns_aaaa_record: Annotated[
        bool | None,
        Field(
            alias="enableDnsAAAARecord",
            description="(OPTIONAL) Indicates whether to respond to DNS queries for instance hostname with DNS AAAA records.",
        ),
    ] = False
    enable_dns_a_record: Annotated[
        bool | None,
        Field(
            alias="enableDnsARecord", description="(OPTIONAL) Indicates whether to respond to DNS queries for instance hostnames with DNS A records."
        ),
    ] = False
    hostname_type: Annotated[HostnameType | None, Field(alias="hostnameType", description="The type of hostname for EC2 instances.")] = None


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


class TargetGroupThresholdType(BaseModel):
    model_config = ConfigDict(extra="forbid")
    healthy: Annotated[
        float | None,
        Field(
            description="The number of consecutive health check successes required before considering a target healthy. The range is 2-10. If the target group protocol is TCP, TCP_UDP, UDP, TLS, HTTP or HTTPS, the default is 5. For target groups with a protocol of GENEVE, the default is 3."
        ),
    ] = None
    unhealthy: Annotated[
        float | None,
        Field(
            description="The number of consecutive health check failures required before considering a target unhealthy. The range is 2-10. If the target group protocol is TCP, TCP_UDP, UDP, TLS, HTTP or HTTPS, the default is 2. For target groups with a protocol of GENEVE, the default is 3."
        ),
    ] = None


class TransitGatewayAttachmentOptionsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    appliance_mode_support: Annotated[
        EnableDisable | None,
        Field(
            alias="applianceModeSupport",
            description="(OPTIONAL) Enable to configure appliance mode for the attachment. This option is disabled by default.",
        ),
    ] = None
    dns_support: Annotated[
        EnableDisable | None,
        Field(alias="dnsSupport", description="(OPTIONAL) Enable to configure DNS support for the attachment. This option is enabled by default."),
    ] = None
    ipv6_support: Annotated[
        EnableDisable | None,
        Field(alias="ipv6Support", description="(OPTIONAL) Enable to configure IPv6 support for the attachment. This option is disabled by default."),
    ] = None
    security_group_referencing_support: Annotated[
        EnableDisable | None,
        Field(
            alias="securityGroupReferencingSupport",
            description="(OPTIONAL) Enable security group referencing support for the attachment. This option is disabled by default.",
        ),
    ] = None


class VirtualPrivateGatewayConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    asn: Annotated[float, Field(description="Define the ASN (Amazon Side) used for the Virtual Private Gateway")]


class IkeVersionType(Enum):
    number_1 = 1
    number_2 = 2


class InstanceTenancyType(StrEnum):
    default = "default"
    dedicated = "dedicated"


class IntegrityAlgorithmType(StrEnum):
    sha1 = "SHA1"
    sha2_256 = "SHA2-256"
    sha2_384 = "SHA2-384"
    sha2_512 = "SHA2-512"


class IpAddressFamilyType(StrEnum):
    i_pv4 = "IPv4"
    i_pv6 = "IPv6"


class IpVersionType(StrEnum):
    ipv4 = "ipv4"
    ipv6 = "ipv6"


class LoadBalancerSchemeEnum(StrEnum):
    internet_facing = "internet-facing"
    internal = "internal"


class LogDestinationType(StrEnum):
    s3 = "s3"
    cloud_watch_logs = "cloud-watch-logs"


class MutationProtectionType(StrEnum):
    enabled = "ENABLED"
    disabled = "DISABLED"


class NetbiosNodeType(Enum):
    number_1 = 1
    number_2 = 2
    number_4 = 4
    number_8 = 8


class NfwGeneratedRulesType(StrEnum):
    allowlist = "ALLOWLIST"
    denylist = "DENYLIST"


class NfwLogType(StrEnum):
    alert = "ALERT"
    flow = "FLOW"


class NfwRuleType(StrEnum):
    stateful = "STATEFUL"
    stateless = "STATELESS"


class NfwStatefulDefaultActionType(StrEnum):
    aws_drop_strict = "aws:drop_strict"
    aws_drop_established = "aws:drop_established"
    aws_drop_established_app_layer = "aws:drop_established_app_layer"
    aws_alert_strict = "aws:alert_strict"
    aws_alert_established = "aws:alert_established"
    aws_alert_established_app_layer = "aws:alert_established_app_layer"


class NfwStatefulRuleActionType(StrEnum):
    alert = "ALERT"
    drop = "DROP"
    pass_ = "PASS"


class NfwStatefulRuleDirectionType(StrEnum):
    any = "ANY"
    forward = "FORWARD"


class NfwStatefulRuleOptionsType(StrEnum):
    default_action_order = "DEFAULT_ACTION_ORDER"
    strict_order = "STRICT_ORDER"


class NfwStatefulRuleProtocolType(StrEnum):
    dcerpc = "DCERPC"
    dhcp = "DHCP"
    dns = "DNS"
    ftp = "FTP"
    http = "HTTP"
    icmp = "ICMP"
    ikev2 = "IKEV2"
    imap = "IMAP"
    ip = "IP"
    krb5 = "KRB5"
    msn = "MSN"
    ntp = "NTP"
    smb = "SMB"
    smtp = "SMTP"
    ssh = "SSH"
    tcp = "TCP"
    tftp = "TFTP"
    tls = "TLS"
    udp = "UDP"


class NfwStatelessRuleActionType(StrEnum):
    aws_pass = "aws:pass"
    aws_drop = "aws:drop"
    aws_forward_to_sfe = "aws:forward_to_sfe"


class NfwStatelessRuleTcpFlagType(StrEnum):
    fin = "FIN"
    syn = "SYN"
    rst = "RST"
    psh = "PSH"
    ack = "ACK"
    urg = "URG"
    ece = "ECE"
    cwr = "CWR"


class NfwTargetType(StrEnum):
    tls_sni = "TLS_SNI"
    http_host = "HTTP_HOST"


class NlbProtocolEnum(StrEnum):
    tcp = "TCP"
    udp = "UDP"
    tls = "TLS"
    tcp_udp = "TCP_UDP"


type NonEmptyString = Annotated[
    str,
    Field(
        description="## Non-Empty String Type\n\nRepresents a string that must contain at least one character. Used for required text fields throughout the Landing Zone Accelerator configuration where empty values are not permitted.\n\n```",
        min_length=1,
    ),
]


class OutsideIpAddressType(StrEnum):
    public_ipv4 = "PublicIpv4"
    ipv6 = "Ipv6"


class Phase1DhGroupType(Enum):
    number_2 = 2
    number_14 = 14
    number_15 = 15
    number_16 = 16
    number_17 = 17
    number_18 = 18
    number_19 = 19
    number_20 = 20
    number_21 = 21
    number_22 = 22
    number_23 = 23
    number_24 = 24


class Phase2DhGroupType(Enum):
    number_2 = 2
    number_5 = 5
    number_14 = 14
    number_15 = 15
    number_16 = 16
    number_17 = 17
    number_18 = 18
    number_19 = 19
    number_20 = 20
    number_21 = 21
    number_22 = 22
    number_23 = 23
    number_24 = 24


class ResolverEndpointType(StrEnum):
    inbound = "INBOUND"
    outbound = "OUTBOUND"


class ResolverProtocol(StrEnum):
    do_h_fips = "DoH-FIPS"
    do_h = "DoH"
    do53 = "Do53"


class RouteTableEntryType(StrEnum):
    transit_gateway = "transitGateway"
    nat_gateway = "natGateway"
    internet_gateway = "internetGateway"
    egress_only_igw = "egressOnlyIgw"
    local = "local"
    local_gateway = "localGateway"
    gateway_endpoint = "gatewayEndpoint"
    gateway_load_balancer_endpoint = "gatewayLoadBalancerEndpoint"
    network_firewall = "networkFirewall"
    network_interface = "networkInterface"
    virtual_private_gateway = "virtualPrivateGateway"
    vpc_peering = "vpcPeering"


class RoutingHttpXffHeaderProcessingModeEnum(StrEnum):
    append = "append"
    preserve = "preserve"
    remove = "remove"


class RuleType(StrEnum):
    forward = "FORWARD"
    recursive = "RECURSIVE"
    system = "SYSTEM"


class SecurityGroupRuleType(StrEnum):
    rdp = "RDP"
    ssh = "SSH"
    http = "HTTP"
    https = "HTTPS"
    mssql = "MSSQL"
    mysql_aurora = "MYSQL/AURORA"
    redshift = "REDSHIFT"
    postgresql = "POSTGRESQL"
    oracle_rds = "ORACLE-RDS"
    tcp = "TCP"
    udp = "UDP"
    icmp = "ICMP"
    all = "ALL"


class SslPolicyAlbEnum(StrEnum):
    elb_security_policy_tls13_1_2_2021_06 = "ELBSecurityPolicy-TLS13-1-2-2021-06"
    elb_security_policy_tls13_1_2_res_2021_06 = "ELBSecurityPolicy-TLS13-1-2-Res-2021-06"
    elb_security_policy_tls13_1_2_ext1_2021_06 = "ELBSecurityPolicy-TLS13-1-2-Ext1-2021-06"
    elb_security_policy_tls13_1_2_ext2_2021_06 = "ELBSecurityPolicy-TLS13-1-2-Ext2-2021-06"
    elb_security_policy_tls13_1_1_2021_06 = "ELBSecurityPolicy-TLS13-1-1-2021-06"
    elb_security_policy_tls13_1_0_2021_06 = "ELBSecurityPolicy-TLS13-1-0-2021-06"
    elb_security_policy_tls13_1_3_2021_06 = "ELBSecurityPolicy-TLS13-1-3-2021-06"
    elb_security_policy_tls13_1_2_fips_2023_04 = "ELBSecurityPolicy-TLS13-1-2-FIPS-2023-04"
    elb_security_policy_tls13_1_2_res_fips_2023_04 = "ELBSecurityPolicy-TLS13-1-2-Res-FIPS-2023-04"
    elb_security_policy_tls13_1_2_ext0_fips_2023_04 = "ELBSecurityPolicy-TLS13-1-2-Ext0-FIPS-2023-04"
    elb_security_policy_tls13_1_2_ext1_fips_2023_04 = "ELBSecurityPolicy-TLS13-1-2-Ext1-FIPS-2023-04"
    elb_security_policy_tls13_1_2_ext2_fips_2023_04 = "ELBSecurityPolicy-TLS13-1-2-Ext2-FIPS-2023-04"
    elb_security_policy_tls13_1_1_fips_2023_04 = "ELBSecurityPolicy-TLS13-1-1-FIPS-2023-04"
    elb_security_policy_tls13_1_0_fips_2023_04 = "ELBSecurityPolicy-TLS13-1-0-FIPS-2023-04"
    elb_security_policy_tls13_1_3_fips_2023_04 = "ELBSecurityPolicy-TLS13-1-3-FIPS-2023-04"
    elb_security_policy_tls_1_0_2015_04 = "ELBSecurityPolicy-TLS-1-0-2015-04"
    elb_security_policy_tls_1_1_2017_01 = "ELBSecurityPolicy-TLS-1-1-2017-01"
    elb_security_policy_tls_1_2_2017_01 = "ELBSecurityPolicy-TLS-1-2-2017-01"
    elb_security_policy_tls_1_2_ext_2018_06 = "ELBSecurityPolicy-TLS-1-2-Ext-2018-06"
    elb_security_policy_fs_2018_06 = "ELBSecurityPolicy-FS-2018-06"
    elb_security_policy_fs_1_1_2019_08 = "ELBSecurityPolicy-FS-1-1-2019-08"
    elb_security_policy_fs_1_2_2019_08 = "ELBSecurityPolicy-FS-1-2-2019-08"
    elb_security_policy_fs_1_2_res_2019_08 = "ELBSecurityPolicy-FS-1-2-Res-2019-08"
    elb_security_policy_2015_05 = "ELBSecurityPolicy-2015-05"
    elb_security_policy_fs_1_2_res_2020_10 = "ELBSecurityPolicy-FS-1-2-Res-2020-10"
    elb_security_policy_2016_08 = "ELBSecurityPolicy-2016-08"


class SslPolicyNlbEnum(StrEnum):
    elb_security_policy_tls13_1_2_2021_06 = "ELBSecurityPolicy-TLS13-1-2-2021-06"
    elb_security_policy_tls13_1_2_res_2021_06 = "ELBSecurityPolicy-TLS13-1-2-Res-2021-06"
    elb_security_policy_tls13_1_2_ext1_2021_06 = "ELBSecurityPolicy-TLS13-1-2-Ext1-2021-06"
    elb_security_policy_tls13_1_2_ext2_2021_06 = "ELBSecurityPolicy-TLS13-1-2-Ext2-2021-06"
    elb_security_policy_tls13_1_1_2021_06 = "ELBSecurityPolicy-TLS13-1-1-2021-06"
    elb_security_policy_tls13_1_0_2021_06 = "ELBSecurityPolicy-TLS13-1-0-2021-06"
    elb_security_policy_tls13_1_3_2021_06 = "ELBSecurityPolicy-TLS13-1-3-2021-06"
    elb_security_policy_tls13_1_2_fips_2023_04 = "ELBSecurityPolicy-TLS13-1-2-FIPS-2023-04"
    elb_security_policy_tls13_1_2_res_fips_2023_04 = "ELBSecurityPolicy-TLS13-1-2-Res-FIPS-2023-04"
    elb_security_policy_tls13_1_2_ext0_fips_2023_04 = "ELBSecurityPolicy-TLS13-1-2-Ext0-FIPS-2023-04"
    elb_security_policy_tls13_1_2_ext1_fips_2023_04 = "ELBSecurityPolicy-TLS13-1-2-Ext1-FIPS-2023-04"
    elb_security_policy_tls13_1_2_ext2_fips_2023_04 = "ELBSecurityPolicy-TLS13-1-2-Ext2-FIPS-2023-04"
    elb_security_policy_tls13_1_1_fips_2023_04 = "ELBSecurityPolicy-TLS13-1-1-FIPS-2023-04"
    elb_security_policy_tls13_1_0_fips_2023_04 = "ELBSecurityPolicy-TLS13-1-0-FIPS-2023-04"
    elb_security_policy_tls13_1_3_fips_2023_04 = "ELBSecurityPolicy-TLS13-1-3-FIPS-2023-04"
    elb_security_policy_tls_1_0_2015_04 = "ELBSecurityPolicy-TLS-1-0-2015-04"
    elb_security_policy_tls_1_1_2017_01 = "ELBSecurityPolicy-TLS-1-1-2017-01"
    elb_security_policy_tls_1_2_2017_01 = "ELBSecurityPolicy-TLS-1-2-2017-01"
    elb_security_policy_tls_1_2_ext_2018_06 = "ELBSecurityPolicy-TLS-1-2-Ext-2018-06"
    elb_security_policy_fs_2018_06 = "ELBSecurityPolicy-FS-2018-06"
    elb_security_policy_fs_1_1_2019_08 = "ELBSecurityPolicy-FS-1-1-2019-08"
    elb_security_policy_fs_1_2_2019_08 = "ELBSecurityPolicy-FS-1-2-2019-08"
    elb_security_policy_fs_1_2_res_2019_08 = "ELBSecurityPolicy-FS-1-2-Res-2019-08"
    elb_security_policy_2015_05 = "ELBSecurityPolicy-2015-05"
    elb_security_policy_fs_1_2_res_2020_10 = "ELBSecurityPolicy-FS-1-2-Res-2020-10"
    elb_security_policy_2016_08 = "ELBSecurityPolicy-2016-08"


class StartupActionType(StrEnum):
    add = "add"
    start = "start"


class StorageClass(StrEnum):
    deep_archive = "DEEP_ARCHIVE"
    glacier = "GLACIER"
    glacier_ir = "GLACIER_IR"
    standard_ia = "STANDARD_IA"
    intelligent_tiering = "INTELLIGENT_TIERING"
    onezone_ia = "ONEZONE_IA"


class TargetGroupAttributeAlgorithm(StrEnum):
    round_robin = "round_robin"
    least_outstanding_requests = "least_outstanding_requests"


class TargetGroupAttributeStickinessType(StrEnum):
    lb_cookie = "lb_cookie"
    app_cookie = "app_cookie"
    source_ip = "source_ip"
    source_ip_dest_ip = "source_ip_dest_ip"
    source_ip_dest_ip_proto = "source_ip_dest_ip_proto"


class TargetGroupHealthCheckProtocolType(StrEnum):
    http = "HTTP"
    https = "HTTPS"
    tcp = "TCP"


class TargetGroupProtocolType(StrEnum):
    tcp = "TCP"
    tls = "TLS"
    udp = "UDP"
    tcp_udp = "TCP_UDP"
    http = "HTTP"
    https = "HTTPS"
    geneve = "GENEVE"


class TargetGroupProtocolVersionType(StrEnum):
    grpc = "GRPC"
    http1 = "HTTP1"
    http2 = "HTTP2"


class TargetGroupTargetFailoverType(StrEnum):
    no_rebalance = "no_rebalance"
    rebalance = "rebalance"


class TargetGroupType(StrEnum):
    instance = "instance"
    ip = "ip"
    alb = "alb"
    lambda_ = "lambda"


class TrafficType(StrEnum):
    all = "ALL"
    accept = "ACCEPT"
    reject = "REJECT"


class VpnLoggingOutputFormatType(StrEnum):
    json = "json"
    text = "text"


class AlbAttributesConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    deletion_protection: Annotated[bool | None, Field(alias="deletionProtection", description="Enable or disable deletion protection.")] = None
    http2_enabled: Annotated[
        bool | None,
        Field(
            alias="http2Enabled",
            description="Indicates whether HTTP/2 is enabled. The possible values are true and false. The default is true. Elastic Load Balancing requires that message header names contain only alphanumeric characters and hyphens.",
        ),
    ] = None
    idle_timeout: Annotated[
        float | None,
        Field(alias="idleTimeout", description="The idle timeout value, in seconds. The valid range is 1-4000 seconds. The default is 60 seconds."),
    ] = None
    routing_http_desync_mitigation_mode: Annotated[
        AlbRoutingHttpConfigMitigationModeEnum | None,
        Field(
            alias="routingHttpDesyncMitigationMode",
            description="Determines how the load balancer handles requests that might pose a security risk to your application. The possible values are `monitor` , `defensive` , and `strictest` . The default is `defensive`.",
        ),
    ] = None
    routing_http_drop_invalid_header: Annotated[
        bool | None,
        Field(
            alias="routingHttpDropInvalidHeader",
            description="Indicates whether HTTP headers with invalid header fields are removed by the load balancer ( true ) or routed to targets ( false ). The default is false.",
        ),
    ] = None
    routing_http_x_amzn_tls_cipher_enable: Annotated[
        bool | None,
        Field(
            alias="routingHttpXAmznTlsCipherEnable",
            description="Indicates whether the two headers ( x-amzn-tls-version and x-amzn-tls-cipher-suite ), which contain information about the negotiated TLS version and cipher suite, are added to the client request before sending it to the target. The x-amzn-tls-version header has information about the TLS protocol version negotiated with the client, and the x-amzn-tls-cipher-suite header has information about the cipher suite negotiated with the client. Both headers are in OpenSSL format. The possible values for the attribute are true and false . The default is false.",
        ),
    ] = None
    routing_http_xff_client_port: Annotated[
        bool | None,
        Field(
            alias="routingHttpXffClientPort",
            description="Indicates whether the X-Forwarded-For header should preserve the source port that the client used to connect to the load balancer. The possible values are true and false . The default is false.",
        ),
    ] = None
    routing_http_xff_header_processing_mode: Annotated[
        RoutingHttpXffHeaderProcessingModeEnum | None,
        Field(
            alias="routingHttpXffHeaderProcessingMode",
            description="Enables you to modify, preserve, or remove the X-Forwarded-For header in the HTTP request before the Application Load Balancer sends the request to the target. The possible values are append, preserve, and remove. The default is append.",
        ),
    ] = None
    waf_fail_open: Annotated[
        bool | None,
        Field(
            alias="wafFailOpen",
            description="Indicates whether to allow a WAF-enabled load balancer to route requests to targets if it is unable to forward the request to AWS WAF. The possible values are true and false. The default is false.",
        ),
    ] = None


class AlbListenerFixedResponseConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    content_type: Annotated[str | None, Field(alias="contentType", description="The message to send back.", min_length=1)] = None
    message_body: Annotated[str | None, Field(alias="messageBody", description="The HTTP response code (2XX, 4XX, or 5XX).", min_length=1)] = None
    status_code: Annotated[
        str,
        Field(
            alias="statusCode",
            description="The content type. Valid Values: text/plain | text/css | text/html | application/javascript | application/json",
            min_length=1,
        ),
    ]


class AlbListenerForwardConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    target_group_stickiness_config: Annotated[AlbListenerTargetGroupStickinessConfig | None, Field(alias="targetGroupStickinessConfig")] = None


class AlbListenerRedirectConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    host: Annotated[
        str | None,
        Field(
            description="## Non-Empty String Type\n\nRepresents a string that must contain at least one character. Used for required text fields throughout the Landing Zone Accelerator configuration where empty values are not permitted.\n\n```",
            min_length=1,
        ),
    ] = None
    path: Annotated[
        str | None,
        Field(
            description="## Non-Empty String Type\n\nRepresents a string that must contain at least one character. Used for required text fields throughout the Landing Zone Accelerator configuration where empty values are not permitted.\n\n```",
            min_length=1,
        ),
    ] = None
    port: float | None = None
    protocol: Annotated[
        str | None,
        Field(
            description="## Non-Empty String Type\n\nRepresents a string that must contain at least one character. Used for required text fields throughout the Landing Zone Accelerator configuration where empty values are not permitted.\n\n```",
            min_length=1,
        ),
    ] = None
    query: Annotated[
        str | None,
        Field(
            description="## Non-Empty String Type\n\nRepresents a string that must contain at least one character. Used for required text fields throughout the Landing Zone Accelerator configuration where empty values are not permitted.\n\n```",
            min_length=1,
        ),
    ] = None
    status_code: Annotated[
        str | None,
        Field(
            alias="statusCode",
            description="## Non-Empty String Type\n\nRepresents a string that must contain at least one character. Used for required text fields throughout the Landing Zone Accelerator configuration where empty values are not permitted.\n\n```",
            min_length=1,
        ),
    ] = None


class CertificateConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    cert: Annotated[
        str | None,
        Field(
            description="Path to certificate in S3 assets bucket. The bucket value is in the outputs of Pipeline stack in home region. Path should be given relative to the bucket. The certificate to import. This value should be provided when type is set to import or else validation fails.",
            min_length=1,
        ),
    ] = None
    chain: Annotated[
        str | None,
        Field(
            description="Path to the PEM encoded certificate chain in S3 assets bucket. The bucket value is in the outputs of Pipeline stack in home region. Path should be given relative to the bucket. This value is optional when type is set to import.",
            min_length=1,
        ),
    ] = None
    deployment_targets: Annotated[
        DeploymentTargets | None,
        Field(alias="deploymentTargets", description="ACM deployment target. This should be provided to deploy ACM into OUs or account."),
    ] = None
    domain: Annotated[
        str | None,
        Field(
            description="Fully qualified domain name (FQDN), such as www.example.com, that you want to secure with an ACM certificate. Use an asterisk (*) to create a wildcard certificate that protects several sites in the same domain. For example, *.example.com protects www.example.com, site.example.com, and images.example.com. In compliance with RFC 5280, the length of the domain name (technically, the Common Name) that you provide cannot exceed 64 octets (characters), including periods. To add a longer domain name, specify it in the Subject Alternative Name field, which supports names up to 253 octets in length. This value should be provided when type is set to request or else validation fails.",
            min_length=1,
        ),
    ] = None
    name: Annotated[
        str,
        Field(
            description="Name of the certificate. This should be unique in the certificates array. Duplicate names will fail the validation.",
            min_length=1,
        ),
    ]
    priv_key: Annotated[
        str | None,
        Field(
            alias="privKey",
            description="Path to the private key in S3 assets bucket. The bucket value is in the outputs of Pipeline stack in home region. Path should be given relative to the bucket. The private key that matches the public key in the certificate. This value should be provided when type is set to import or else validation fails.",
            min_length=1,
        ),
    ] = None
    san: Annotated[
        list[NonEmptyString] | None,
        Field(
            description="Additional FQDNs to be included in the Subject Alternative Name extension of the ACM certificate. For example, add the name www.example.net to a certificate for which the DomainName field is www.example.com if users can reach your site by using either name."
        ),
    ] = None
    type: Annotated[CertificateConfigType, Field(description="Type of ACM cert. Valid values are `import` or `request`")]
    validation: Annotated[
        CertificateValidationType | None,
        Field(
            description="The method you want to use if you are requesting a public certificate to validate that you own or control domain. You can validate with DNS or validate with email. Valid values are 'DNS' or 'EMAIL'. This value should be provided when type is set to request or else validation fails."
        ),
    ] = None


class DhcpOptsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    accounts: Annotated[list[NonEmptyString], Field(description="An array of friendly account names to deploy the options set.")]
    domain_name: Annotated[
        str | None,
        Field(
            alias="domainName",
            description="(OPTIONAL) A domain name to assign to hosts using the options set. You may specify a single domain name (for example, `example.com`) or multiple domain names separated by spaces (for example, `example.com example.org`). CAUTION: Multiple domain names are only honored by some Linux operating systems. Windows and other Linux operating systems treat the value as a single domain name, which results in unexpected behavior. If the options set is associated with a VPC that has instances running operating systems that treat the value as a single domain, specify only one domain name. See https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_CreateDhcpOptions.html for more information.",
            min_length=1,
        ),
    ] = None
    domain_name_servers: Annotated[
        list[NonEmptyString] | None, Field(alias="domainNameServers", description="(OPTIONAL) An array of IP addresses for domain name servers.")
    ] = None
    name: Annotated[str, Field(description="A friendly name for the DHCP options set.", min_length=1)]
    netbios_name_servers: Annotated[
        list[NonEmptyString] | None, Field(alias="netbiosNameServers", description="(OPTIONAL An array of IP addresses for NetBIOS servers.")
    ] = None
    netbios_node_type: Annotated[NetbiosNodeType | None, Field(alias="netbiosNodeType", description="(OPTIONAL) The NetBIOS node type number.")] = (
        None
    )
    ntp_servers: Annotated[
        list[NonEmptyString] | None, Field(alias="ntpServers", description="(OPTIONAL) An array of IP addresses for NTP servers.")
    ] = None
    regions: Annotated[list[str], Field(description="An array of regions to deploy the options set.")]
    tags: Annotated[list[Tag] | None, Field(description="(OPTIONAL) An array of tags for the options set.")] = None


class DnsFirewallRulesConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: Annotated[DnsFirewallRuleActionType, Field(description="An action for the DNS firewall rule to take on matching requests.")]
    block_override_domain: Annotated[
        str | None,
        Field(
            alias="blockOverrideDomain",
            description="(OPTIONAL) Configure an override domain for BLOCK actions. This is a custom DNS record to send back in response to the query.",
            min_length=1,
        ),
    ] = None
    block_override_ttl: Annotated[
        float | None,
        Field(
            alias="blockOverrideTtl",
            description="(OPTIONAL) Configure a time-to-live (TTL) for the override domain. This is the recommended amount of time for the DNS resolver or web browser to cache the override record and use it in response to this query, if it is received again. By default, this is zero, and the record isn't cached.",
        ),
    ] = None
    block_response: Annotated[
        DnsFirewallBlockResponseType | None,
        Field(
            alias="blockResponse",
            description="Configure a specific response type for BLOCK actions. Block response types are defined here:  {@link  https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/resolver-dns-firewall-rule-actions.html }",
        ),
    ] = None
    custom_domain_list: Annotated[
        str | None, Field(alias="customDomainList", description="A file containing a custom domain list in TXT format.", min_length=1)
    ] = None
    managed_domain_list: Annotated[
        DnsFirewallManagedDomainListsType | None,
        Field(
            alias="managedDomainList",
            description="Configure a rule that uses an AWS-managed domain list. AWS-managed domain lists are defined here:  {@link  https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/resolver-dns-firewall-managed-domain-lists.html } .",
        ),
    ] = None
    name: Annotated[str, Field(description="A friendly name for the DNS firewall rule.", min_length=1)]
    priority: Annotated[float, Field(description="The priority of the DNS firewall rule.")]


class DnsQueryLogsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    destinations: Annotated[list[LogDestinationType], Field(description="An array of destination services used to store the logs.")]
    excluded_regions: Annotated[list[str] | None, Field(alias="excludedRegions")] = None
    name: Annotated[str, Field(description="The friendly name of the query logging config.", min_length=1)]
    share_targets: Annotated[ShareTargets | None, Field(alias="shareTargets", description="Resource Access Manager (RAM) share targets.")] = None


class DxTransitGatewayAssociationConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    account: Annotated[str, Field(description="The friendly name of the account the transit gateway is deployed to.", min_length=1)]
    allowed_prefixes: Annotated[
        list[NonEmptyString],
        Field(alias="allowedPrefixes", description="An array of CIDR prefixes that are allowed to advertise over this transit gateway association."),
    ]
    name: Annotated[str, Field(description="The friendly name of the transit gateway to associate.", min_length=1)]
    route_table_associations: Annotated[
        list[NonEmptyString] | None,
        Field(alias="routeTableAssociations", description="(OPTIONAL) The friendly name of TGW route table(s) to associate with this attachment."),
    ] = None
    route_table_propagations: Annotated[
        list[NonEmptyString] | None,
        Field(
            alias="routeTablePropagations", description="(OPTIONAL) The friendly name of TGW route table(s) to propagate routes from this attachment."
        ),
    ] = None


class DxVirtualInterfaceConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    address_family: Annotated[
        IpVersionType | None,
        Field(alias="addressFamily", description="(OPTIONAL) The address family to use for this virtual interface.\n\nDefault - ipv4"),
    ] = None
    amazon_address: Annotated[
        str | None,
        Field(
            alias="amazonAddress",
            description="(OPTIONAL) The peer IP address to use for Amazon's side of the virtual interface.\n\nDefault - randomly-generated by Amazon",
            min_length=1,
        ),
    ] = None
    auth_key: Annotated[
        str | None,
        Field(
            alias="authKey",
            description="(OPTIONAL): The Secrets Manager name that stores the BGP Authentication Key, that exists in the same account and region that the Direct Connect Virtual Interface will be created in.",
            min_length=1,
        ),
    ] = None
    connection_id: Annotated[
        str,
        Field(
            alias="connectionId",
            description="The resource ID of the  {@link  https://docs.aws.amazon.com/directconnect/latest/UserGuide/Welcome.html#overview-components DX connection }  the virtual interface will be created on",
            min_length=1,
        ),
    ]
    customer_address: Annotated[
        str | None,
        Field(
            alias="customerAddress",
            description="(OPTIONAL) The peer IP address to use for customer's side of the virtual interface.\n\nDefault - randomly-generated by Amazon",
            min_length=1,
        ),
    ] = None
    customer_asn: Annotated[
        float,
        Field(
            alias="customerAsn", description="A Border Gateway Protocol (BGP) Autonomous System Number (ASN) for the customer side of the connection."
        ),
    ]
    enable_site_link: Annotated[
        bool | None, Field(alias="enableSiteLink", description="(OPTIONAL) Enable SiteLink for this virtual interface.\n\nDefault - false")
    ] = None
    interface_name: Annotated[
        str,
        Field(
            alias="interfaceName",
            description="The name of the virtual interface. This name will show as the name of the resource in the AWS console and API.",
            min_length=1,
        ),
    ]
    jumbo_frames: Annotated[
        bool | None,
        Field(alias="jumboFrames", description="(OPTIONAL) Enable jumbo frames for the virtual interface.\n\nDefault - standard 1500 MTU frame size"),
    ] = None
    name: Annotated[
        str,
        Field(
            description="A friendly name for the virtual interface. This name is used as a logical reference for the resource in the accelerator.",
            min_length=1,
        ),
    ]
    owner_account: Annotated[
        str, Field(alias="ownerAccount", description="The friendly name of the owning account of the DX connection.", min_length=1)
    ]
    region: Annotated[str, Field(description="The region of the virtual interface.")]
    tags: Annotated[list[Tag] | None, Field(description="(OPTIONAL) An array of tags to apply to the virtual interface.")] = None
    type: Annotated[DxVirtualInterfaceType, Field(description="The type of the virtual interface")]
    vlan: Annotated[float, Field(description="The virtual local area network (VLAN) tag to use for this virtual interface.")]


class ElbAccountIdsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    account_id: Annotated[
        str,
        Field(
            alias="accountId",
            description="## Non-Empty String Type\n\nRepresents a string that must contain at least one character. Used for required text fields throughout the Landing Zone Accelerator configuration where empty values are not permitted.\n\n```",
            min_length=1,
        ),
    ]
    region: Annotated[
        str,
        Field(
            description="## Non-Empty String Type\n\nRepresents a string that must contain at least one character. Used for required text fields throughout the Landing Zone Accelerator configuration where empty values are not permitted.\n\n```",
            min_length=1,
        ),
    ]


class EndpointPolicyConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    document: Annotated[str, Field(description="A file path for a JSON-formatted policy document.", min_length=1)]
    name: Annotated[str, Field(description="A friendly name for the endpoint policy.", min_length=1)]


class FirewallManagerNotificationChannelConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    region: Annotated[str, Field(description="Enables the FMS notification channel. Defaults to enabled.", min_length=1)]
    sns_topic: Annotated[str, Field(alias="snsTopic", description="The SNS Topic Name to publish to.", min_length=1)]


class FirewallManagerServiceConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    delegated_admin_account: Annotated[
        str, Field(alias="delegatedAdminAccount", description="The friendly account name to deploy the FMS configuration", min_length=1)
    ]
    notification_channels: Annotated[
        list[FirewallManagerNotificationChannelConfig] | None,
        Field(alias="notificationChannels", description="The FMS Notification Channel Configuration"),
    ] = None


class GatewayEndpointServiceConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    apply_policy: Annotated[
        bool | None,
        Field(
            alias="applyPolicy",
            description="(OPTIONAL) Specify whether or not a policy is applied to the endpoint. By default, if no policy is specified in the `policy` property, a default policy is applied. Specifying this option as `false` will ensure no policy is applied to the endpoint. This property defaults to `true` if not specified.",
        ),
    ] = None
    policy: Annotated[
        str | None,
        Field(
            description="(OPTIONAL) The friendly name of a policy for the gateway endpoint. If left undefined, the default policy will be used.",
            min_length=1,
        ),
    ] = None
    service: Annotated[GatewayEndpointType, Field(description="The name of the service to create the endpoint for")]
    service_name: Annotated[
        str | None, Field(alias="serviceName", description="(OPTIONAL) The full name of the service to create the endpoint for.", min_length=1)
    ] = None


class GwlbEndpointConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    account: Annotated[str, Field(description="The friendly name of the account to deploy the endpoint to.", min_length=1)]
    name: Annotated[str, Field(description="The friendly name of the Gateway Load Balancer endpoint.", min_length=1)]
    subnet: Annotated[str, Field(description="The friendly name of the subnet to deploy the Gateway Load Balancer endpoint to.", min_length=1)]
    vpc: Annotated[str, Field(description="The friendly name of the VPC to deploy the Gateway Load Balancer endpoint to.", min_length=1)]


class InterfaceEndpointServiceConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    apply_policy: Annotated[
        bool | None,
        Field(
            alias="applyPolicy",
            description="(OPTIONAL) Specify whether or not a policy is applied to the endpoint. By default, if no policy is specified in the `policy` property, a default policy is applied. Specifying this option as `false` will ensure no policy is applied to the endpoint. This property defaults to `true` if not specified.",
        ),
    ] = None
    hosted_zone_name: Annotated[
        str | None,
        Field(
            alias="hostedZoneName", description="(OPTIONAL) The full private hosted zone name to create for this interface endpoint.", min_length=1
        ),
    ] = None
    policy: Annotated[
        str | None,
        Field(
            description="(OPTIONAL) The friendly name of a policy for the interface endpoint. If left undefined, the default policy will be used.",
            min_length=1,
        ),
    ] = None
    security_group: Annotated[
        str | None,
        Field(alias="securityGroup", description="(OPTIONAL) Apply the provided security group for this interface endpoint.", min_length=1),
    ] = None
    service: Annotated[str, Field(description="The name of the service to create the endpoint for.", min_length=1)]
    service_name: Annotated[
        str | None, Field(alias="serviceName", description="(OPTIONAL) The full name of the service to create the endpoint for.", min_length=1)
    ] = None


class IpamAllocationConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ipam_pool_name: Annotated[str, Field(alias="ipamPoolName", description="The IPAM pool name to request the allocation from.", min_length=1)]
    netmask_length: Annotated[float, Field(alias="netmaskLength", description="The subnet mask length to request.")]


class IpamPoolConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    address_family: Annotated[IpVersionType | None, Field(alias="addressFamily", description="The address family for the IPAM pool.")] = None
    allocation_default_netmask_length: Annotated[
        float | None,
        Field(alias="allocationDefaultNetmaskLength", description="(OPTIONAL) The default netmask length of IPAM allocations for this pool."),
    ] = None
    allocation_max_netmask_length: Annotated[
        float | None,
        Field(alias="allocationMaxNetmaskLength", description="(OPTIONAL) The maximum netmask length of IPAM allocations for this pool."),
    ] = None
    allocation_min_netmask_length: Annotated[
        float | None,
        Field(alias="allocationMinNetmaskLength", description="(OPTIONAL) The minimum netmask length of IPAM allocations for this pool."),
    ] = None
    allocation_resource_tags: Annotated[
        list[Tag] | None,
        Field(
            alias="allocationResourceTags",
            description="(OPTIONAL) An array of tags that are required for resources that use CIDRs from this IPAM pool.",
        ),
    ] = None
    auto_import: Annotated[
        bool | None,
        Field(
            alias="autoImport",
            description="(OPTIONAL) If set to `true`, IPAM will continuously look for resources within the CIDR range of this pool and automatically import them as allocations into your IPAM.",
        ),
    ] = None
    description: Annotated[str | None, Field(description="(OPTIONAL) A description for the IPAM pool.", min_length=1)] = None
    locale: Annotated[str | None, Field(description="(OPTIONAL) The AWS Region where you want to make an IPAM pool available for allocations.")] = (
        None
    )
    name: Annotated[str, Field(description="A friendly name for the IPAM pool.", min_length=1)]
    provisioned_cidrs: Annotated[
        list[NonEmptyString] | None, Field(alias="provisionedCidrs", description="An array of CIDR ranges to provision for the IPAM pool.")
    ] = None
    publicly_advertisable: Annotated[
        bool | None, Field(alias="publiclyAdvertisable", description="(OPTIONAL) Determines if a pool is publicly advertisable.")
    ] = None
    scope: Annotated[str | None, Field(description="(OPTIONAL) The friendly name of the IPAM scope to assign the IPAM pool to.", min_length=1)] = None
    share_targets: Annotated[
        ShareTargets | None, Field(alias="shareTargets", description="(OPTIONAL) Resource Access Manager (RAM) share targets.")
    ] = None
    source_ipam_pool: Annotated[
        str | None,
        Field(
            alias="sourceIpamPool", description="(OPTIONAL) The friendly name of the source IPAM pool to create this IPAM pool from.", min_length=1
        ),
    ] = None
    tags: Annotated[list[Tag] | None, Field(description="(OPTIONAL) An array of tag objects for the IPAM pool.")] = None


class IpamScopeConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    description: Annotated[str | None, Field(description="(OPTIONAL) Description for the IPAM scope.", min_length=1)] = None
    name: Annotated[str, Field(description="A friendly name for the IPAM scope.", min_length=1)]
    tags: Annotated[list[Tag] | None, Field(description="(OPTIONAL) An array of tag objects for the IPAM scope.")] = None


class LocalGatewayRouteTableConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: Annotated[str, Field(description="The id for the Route Table", min_length=1)]
    name: Annotated[str, Field(description="A friendly name for the Route Table", min_length=1)]


class NatGatewayConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    allocation_id: Annotated[
        str | None,
        Field(
            alias="allocationId",
            description="(OPTIONAL) The allocation ID of the Elastic IP address that's associated with the NAT gateway. This allocation ID must exist in the target account the NAT gateway is deployed to.",
            min_length=1,
        ),
    ] = None
    name: Annotated[str, Field(description="A friendly name for the NAT Gateway.", min_length=1)]
    private: Annotated[bool | None, Field(description="(OPTIONAL) Set `true` to define a NAT gateway with private connectivity type")] = None
    subnet: Annotated[str, Field(description="The friendly name of the subnet for the NAT Gateway to be deployed.", min_length=1)]
    tags: Annotated[list[Tag] | None, Field(description="(OPTIONAL) An array of tag objects for the NAT Gateway.")] = None


class NetworkAclSubnetSelection(BaseModel):
    model_config = ConfigDict(extra="forbid")
    account: Annotated[str | None, Field(description="The friendly name of the account of the subnet.", min_length=1)] = None
    ipv6: Annotated[bool | None, Field(description="(OPTIONAL) Indicates whether to target the IPv6 CIDR associated with a subnet.")] = None
    region: Annotated[str | None, Field(description="(OPTIONAL) The region that the subnet is located in.")] = None
    subnet: Annotated[str, Field(description="The friendly name of the subnet.", min_length=1)]
    vpc: Annotated[str, Field(description="The friendly name of the VPC of the subnet.", min_length=1)]


class NfwLoggingConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    destination: Annotated[LogDestinationType, Field(description="The destination service to log to.")]
    type: Annotated[NfwLogType, Field(description="The type of actions to log.")]


class NfwRuleSourceCustomActionDimensionConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    dimensions: Annotated[list[NonEmptyString], Field(description="An array of values of the custom metric dimensions to log.")]


class NfwRuleSourceListConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    generated_rules_type: Annotated[
        NfwGeneratedRulesType, Field(alias="generatedRulesType", description="The type of rules to generate from the source list.")
    ]
    target_types: Annotated[list[NfwTargetType], Field(alias="targetTypes", description="An array of protocol types to inspect.")]
    targets: Annotated[list[NonEmptyString], Field(description="An array of target domain names.")]


class NfwRuleSourceStatefulRuleHeaderConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    destination: Annotated[str, Field(description="The destination CIDR range to inspect for.", min_length=1)]
    destination_port: Annotated[str, Field(alias="destinationPort", description="The destination port or port range to inspect.", min_length=1)]
    direction: Annotated[NfwStatefulRuleDirectionType, Field(description="The direction of the traffic flow to inspect.")]
    protocol: Annotated[NfwStatefulRuleProtocolType, Field(description="The protocol to inspect.")]
    source: Annotated[str, Field(description="The source CIDR range to inspect for.", min_length=1)]
    source_port: Annotated[str, Field(alias="sourcePort", description="The source port or port range to inspect.", min_length=1)]


class NfwRuleSourceStatefulRuleOptionsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    keyword: Annotated[str, Field(description="A Suricata-compatible keyword.", min_length=1)]
    settings: Annotated[list[NonEmptyString] | None, Field(description="An array of values for the keyword.")] = None


class NfwRuleSourceStatelessTcpFlagsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    flags: Annotated[list[NfwStatelessRuleTcpFlagType], Field(description="An array of TCP flags.")]
    masks: Annotated[list[NfwStatelessRuleTcpFlagType], Field(description="The set of flags to consider in the inspection.")]


class NfwRuleVariableDefinitionConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    definition: Annotated[
        list[NonEmptyString],
        Field(
            description="An array of values for the rule variable.\n\nThe accepted value syntax depends on the rule variable type that this definition belongs to. For `ipSets`, each value is an IPv4 address or CIDR range, for example `'10.0.0.0/16'`. For `portSets`, each value is either a single TCP/UDP port (a number between `0` and `65535`, for example `'443'`) or a port range. A port range is two numbers separated by a colon (`:`) in the form `'<fromPort>:<toPort>'`, for example `'1024:2048'`, where the colon denotes an inclusive range from `fromPort` through `toPort`. Both ends must be between `0` and `65535`, and `fromPort` must be less than or equal to `toPort` (`'1024:2048'` is valid; `'2048:1024'` is rejected). Single ports and ranges can be combined in the same array, for example `['80', '443', '1024:2048']`. The colon range notation matches the syntax accepted by the AWS Network Firewall API and console."
        ),
    ]
    name: Annotated[str, Field(description="A name for the rule variable.", min_length=1)]


class NfwStatefulRuleGroupReferenceConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    managed_stateful_rule_group_name: Annotated[
        str | None,
        Field(
            alias="managedStatefulRuleGroupName",
            description="(OPTIONAL) Specifies the name of an AWS Managed Rule Group. AWS Managed Rule Groups are predefined, ready-to-use collections of rules that are written and maintained by AWS.\n\nNote: For each entry, you must specify either this property or the `name` property, which references a custom rule group defined in network-config.yaml.",
            min_length=1,
        ),
    ] = None
    name: Annotated[str | None, Field(description="The friendly name of the rule group.", min_length=1)] = None
    priority: Annotated[float | None, Field(description="(OPTIONAL) If using strict ordering, a priority number for the rule.")] = None


class NfwStatelessRuleGroupReferenceConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: Annotated[str, Field(description="The friendly name of the rule group.", min_length=1)]
    priority: Annotated[float, Field(description="A priority number for the rule.")]


class NlbListenerConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    alpn_policy: Annotated[
        AlpnPolicyEnum | None,
        Field(alias="alpnPolicy", description="Application-Layer Protocol Negotiation (ALPN) policy} for TLS encrypted traffic"),
    ] = None
    certificate: Annotated[str | None, Field(description="ACM ARN of the certificate to be associated with the listener.", min_length=1)] = None
    name: Annotated[str, Field(description="Name for Listener.", min_length=1)]
    port: Annotated[float | None, Field(description="Port where the traffic is directed to.")] = None
    protocol: Annotated[
        NlbProtocolEnum | None, Field(description="Protocol used for the traffic. The supported protocols are TCP, TLS, UDP, or TCP_UDP.")
    ] = None
    ssl_policy: Annotated[SslPolicyNlbEnum | None, Field(alias="sslPolicy", description="SSL policy for TLS encrypted traffic")] = None
    target_group: Annotated[str, Field(alias="targetGroup", description="Target Group to direct the traffic to.", min_length=1)]


class NlbTargetType(BaseModel):
    model_config = ConfigDict(extra="forbid")
    account: Annotated[str, Field(description="Friendly Account Name where the NLB is deployed", min_length=1)]
    nlb_name: Annotated[str, Field(alias="nlbName", description="Friendly name of the NLB", min_length=1)]
    region: Annotated[str, Field(description="Region where the NLB is deployed", min_length=1)]


class Phase1Config(BaseModel):
    model_config = ConfigDict(extra="forbid")
    dh_groups: Annotated[
        list[Phase1DhGroupType] | None,
        Field(
            alias="dhGroups",
            description="(OPTIONAL) An array of permitted Diffie-Hellman group numbers used in the IKE Phase 1 for initial authentication.\n\nDefault - `[2, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24]`",
        ),
    ] = None
    encryption_algorithms: Annotated[
        list[EncryptionAlgorithmType] | None,
        Field(
            alias="encryptionAlgorithms",
            description="(OPTIONAL) An array of encryption algorithms permitted for IKE Phase 1 negotiations.\n\nDefault - `[AES128, AES256, AES128-GCM-16, AES256-GCM-16]`",
        ),
    ] = None
    integrity_algorithms: Annotated[
        list[IntegrityAlgorithmType] | None,
        Field(
            alias="integrityAlgorithms",
            description="(OPTIONAL) An array of integrity algorithms permitted for IKE Phase 1 negotiations.\n\nDefault - `[SHA1, SHA2-256, SHA2-384, SHA2-512]`",
        ),
    ] = None
    lifetime_seconds: Annotated[
        float | None,
        Field(
            alias="lifetimeSeconds", description="(OPTIONAL) The IKE Phase 1 lifetime (in seconds) for the VPN tunnel.\n\nDefault: `28800` (8 hours)"
        ),
    ] = None


class Phase2Config(BaseModel):
    model_config = ConfigDict(extra="forbid")
    dh_groups: Annotated[
        list[Phase2DhGroupType] | None,
        Field(
            alias="dhGroups",
            description="(OPTIONAL) An array of permitted Diffie-Hellman group numbers used in the IKE Phase 2 negotiations.\n\nDefault - `[2, 5, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24]`",
        ),
    ] = None
    encryption_algorithms: Annotated[
        list[EncryptionAlgorithmType] | None,
        Field(
            alias="encryptionAlgorithms",
            description="(OPTIONAL) An array of encryption algorithms permitted for IKE Phase 2 negotiations.\n\nDefault - `[AES128, AES256, AES128-GCM-16, AES256-GCM-16]`",
        ),
    ] = None
    integrity_algorithms: Annotated[
        list[IntegrityAlgorithmType] | None,
        Field(
            alias="integrityAlgorithms",
            description="(OPTIONAL) An array of integrity algorithms permitted for IKE Phase 2 negotiations.\n\nDefault - `[SHA1, SHA2-256, SHA2-384, SHA2-512]`",
        ),
    ] = None
    lifetime_seconds: Annotated[
        float | None,
        Field(
            alias="lifetimeSeconds", description="(OPTIONAL) The IKE Phase 2 lifetime (in seconds) for the VPN tunnel.\n\nDefault: `3600` (1 hour)"
        ),
    ] = None


class PrefixListConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    accounts: Annotated[
        list[NonEmptyString] | None, Field(description="(DEPRECATED) An array of friendly names for the accounts the prefix list is deployed.")
    ] = None
    address_family: Annotated[IpAddressFamilyType, Field(alias="addressFamily", description="The IP address family of the prefix list.")]
    deployment_targets: Annotated[DeploymentTargets | None, Field(alias="deploymentTargets", description="Prefix List deployment targets")] = None
    entries: Annotated[list[NonEmptyString], Field(description="An array of CIDR entries for the prefix list.")]
    max_entries: Annotated[float, Field(alias="maxEntries", description="The maximum allowed entries in the prefix list.")]
    name: Annotated[str, Field(description="A friendly name for the prefix list.", min_length=1)]
    regions: Annotated[list[str] | None, Field(description="(DEPRECATED) An array of region names for the prefix list to be deployed.")] = None
    tags: Annotated[list[Tag] | None, Field(description="(OPTIONAL) An array of tag objects for the prefix list.")] = None


class PrefixListSourceConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    prefix_lists: Annotated[
        list[NonEmptyString], Field(alias="prefixLists", description="An array of the friendly names of prefix lists to reference.")
    ]


class RouteTableEntryConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    destination: Annotated[
        str | None,
        Field(description="(OPTIONAL) The destination IPv4 CIDR block or dynamic subnet reference for the route table entry.", min_length=1),
    ] = None
    destination_prefix_list: Annotated[
        str | None,
        Field(alias="destinationPrefixList", description="The friendly name of the destination prefix list for the route table entry.", min_length=1),
    ] = None
    ipv6_destination: Annotated[
        str | None,
        Field(
            alias="ipv6Destination",
            description="(OPTIONAL) The destination IPv6 CIDR block or dynamic subnet reference for the route table entry.",
            min_length=1,
        ),
    ] = None
    name: Annotated[str, Field(description="A friendly name for the route table.", min_length=1)]
    target: Annotated[str | None, Field(description="The friendly name of the destination target.", min_length=1)] = None
    target_availability_zone: Annotated[
        NonEmptyString | float | None, Field(alias="targetAvailabilityZone", description="The Availability Zone (AZ) the target resides in.")
    ] = None
    type: Annotated[RouteTableEntryType | None, Field(description="The destination type of route table entry.")] = None


class RuleTargetIps(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ip: Annotated[
        str,
        Field(
            description="## Non-Empty String Type\n\nRepresents a string that must contain at least one character. Used for required text fields throughout the Landing Zone Accelerator configuration where empty values are not permitted.\n\n```",
            min_length=1,
        ),
    ]
    port: Annotated[
        str | None,
        Field(
            description="## Non-Empty String Type\n\nRepresents a string that must contain at least one character. Used for required text fields throughout the Landing Zone Accelerator configuration where empty values are not permitted.\n\n```",
            min_length=1,
        ),
    ] = None


class SecurityGroupSourceConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    security_groups: Annotated[
        list[NonEmptyString], Field(alias="securityGroups", description="An array of the friendly names of security group rules to reference.")
    ]


class SubnetConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    assign_ipv6_on_creation: Annotated[
        bool | None,
        Field(
            alias="assignIpv6OnCreation",
            description="(OPTIONAL) Indicates whether a network interface created in this subnet receives an IPv6 address on creation.",
        ),
    ] = None
    availability_zone: Annotated[
        NonEmptyString | float | None, Field(alias="availabilityZone", description="The Availability Zone (AZ) the subnet resides in.")
    ] = None
    enable_dns64: Annotated[
        bool | None,
        Field(
            alias="enableDns64",
            description="(OPTIONAL) Indicates whether DNS queries made to the Amazon-provided DNS Resolver in this subnet should return synthetic IPv6 addresses for IPv4-only destinations.\n\nFor more information, see  {@link  https://docs.aws.amazon.com/vpc/latest/userguide/vpc-nat-gateway.html#nat-gateway-nat64-dns64 DNS64 and NAT64 }  in the Amazon Virtual Private Cloud User Guide.",
        ),
    ] = None
    ipam_allocation: Annotated[
        IpamAllocationConfig | None, Field(alias="ipamAllocation", description="The IPAM pool configuration for the subnet.")
    ] = None
    ipv4_cidr_block: Annotated[
        str | None, Field(alias="ipv4CidrBlock", description="The IPv4 CIDR block to associate with the subnet.", min_length=1)
    ] = None
    ipv6_cidr_block: Annotated[
        str | None, Field(alias="ipv6CidrBlock", description="(OPTIONAL) The IPv6 CIDR block to associate with the subnet.", min_length=1)
    ] = None
    local_zone: Annotated[str | None, Field(alias="localZone", description="The Zone ID of the local zone.", min_length=1)] = None
    map_public_ip_on_launch: Annotated[
        bool | None, Field(alias="mapPublicIpOnLaunch", description="(OPTIONAL) Configure automatic mapping of public IPs.")
    ] = None
    name: Annotated[str, Field(description="A friendly name for the VPC subnet.", min_length=1)]
    outpost: Annotated[str | None, Field(description="(OPTIONAL) The friendly name for the outpost to attach to the subnet", min_length=1)] = None
    private_dns_options: Annotated[
        SubnetPrivateDnsConfig | None, Field(alias="privateDnsOptions", description="(OPTIONAL) Private DNS name options for the subnet.")
    ] = None
    route_table: Annotated[
        str | None, Field(alias="routeTable", description="The friendly name of the route table to associate with the subnet.", min_length=1)
    ] = None
    share_targets: Annotated[
        ShareTargets | None, Field(alias="shareTargets", description="(OPTIONAL) Resource Access Manager (RAM) share targets.")
    ] = None
    tags: Annotated[list[Tag] | None, Field(description="(OPTIONAL) An array of tag objects for the VPC subnet.")] = None


class SubnetSourceConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    account: Annotated[str, Field(description="The friendly name of the account in which the VPC subnet resides.", min_length=1)]
    ipv6: Annotated[bool | None, Field(description="(OPTIONAL) Indicates whether to target the IPv6 CIDR associated with a subnet.")] = None
    subnets: Annotated[list[NonEmptyString], Field(description="An array of the friendly names of subnets to reference.")]
    vpc: Annotated[str, Field(description="The friendly name of the VPC in which the subnet resides.", min_length=1)]


class TargetGroupAttributeTypes(BaseModel):
    model_config = ConfigDict(extra="forbid")
    algorithm: Annotated[
        TargetGroupAttributeAlgorithm | None,
        Field(
            description="The load balancing algorithm determines how the load balancer selects targets when routing requests. The value is round_robin or least_outstanding_requests. The default is round_robin. The following attribute is supported only if the load balancer is an Application Load Balancer and the target is an instance or an IP address."
        ),
    ] = None
    app_cookie_duration: Annotated[
        float | None,
        Field(
            alias="appCookieDuration",
            description="The time period, in seconds, during which requests from a client should be routed to the same target. After this time period expires, the application-based cookie is considered stale. The range is 1 second to 1 week (604800 seconds). The default value is 1 day (86400 seconds). The following attribute is supported only if the load balancer is an Application Load Balancer and the target is an instance or an IP address.",
        ),
    ] = None
    app_cookie_name: Annotated[
        str | None,
        Field(
            alias="appCookieName",
            description="Indicates the name of the application-based cookie. Names that start with the following prefixes are not allowed: AWSALB, AWSALBAPP, and AWSALBTG; they're reserved for use by the load balancer. The following attribute is supported only if the load balancer is an Application Load Balancer and the target is an instance or an IP address.",
            min_length=1,
        ),
    ] = None
    connection_termination: Annotated[
        bool | None,
        Field(
            alias="connectionTermination",
            description="Indicates whether the load balancer terminates connections at the end of the deregistration timeout. The value is true or false. The default is false. The following attribute is supported only by Network Load Balancers.",
        ),
    ] = None
    deregistration_delay: Annotated[
        float | None,
        Field(
            alias="deregistrationDelay",
            description="The amount of time, in seconds, for Elastic Load Balancing to wait before changing the state of a deregistering target from draining to unused. The range is 0-3600 seconds. The default value is 300 seconds.",
        ),
    ] = None
    lb_cookie_duration: Annotated[
        float | None,
        Field(
            alias="lbCookieDuration",
            description="The time period, in seconds, during which requests from a client should be routed to the same target. After this time period expires, the load balancer-generated cookie is considered stale. The range is 1 second to 1 week (604800 seconds). The default value is 1 day (86400 seconds). The following attribute is supported only if the load balancer is an Application Load Balancer and the target is an instance or an IP address.",
        ),
    ] = None
    preserve_client_ip: Annotated[
        bool | None,
        Field(
            alias="preserveClientIp",
            description="Indicates whether client IP preservation is enabled. The value is true or false. The default is disabled if the target group type is IP address and the target group protocol is TCP or TLS. Otherwise, the default is enabled. Client IP preservation cannot be disabled for UDP and TCP_UDP target groups. The following attribute is supported only by Network Load Balancers.",
        ),
    ] = None
    proxy_protocol_v2: Annotated[
        bool | None,
        Field(
            alias="proxyProtocolV2",
            description="Indicates whether Proxy Protocol version 2 is enabled. The value is true or false. The default is false. The following attribute is supported only by Network Load Balancers.",
        ),
    ] = None
    slow_start: Annotated[
        float | None,
        Field(
            alias="slowStart",
            description="The time period, in seconds, during which a newly registered target receives an increasing share of the traffic to the target group. After this time period ends, the target receives its full share of traffic. The range is 30-900 seconds (15 minutes). The default is 0 seconds (disabled). The following attribute is supported only if the load balancer is an Application Load Balancer and the target is an instance or an IP address.",
        ),
    ] = None
    stickiness: Annotated[
        bool | None, Field(description="Indicates whether target stickiness is enabled. The value is true or false. The default is false.")
    ] = None
    stickiness_type: Annotated[
        TargetGroupAttributeStickinessType | None,
        Field(
            alias="stickinessType",
            description="Indicates the type of stickiness. The possible values are:  - lb_cookie and app_cookie for Application Load Balancers.  - source_ip for Network Load Balancers.  - source_ip_dest_ip and source_ip_dest_ip_proto for Gateway Load Balancers",
        ),
    ] = None
    target_failover: Annotated[
        TargetGroupTargetFailoverType | None,
        Field(
            alias="targetFailover",
            description="Indicates how the Gateway Load Balancer handles existing flows when a target is deregistered or becomes unhealthy. The possible values are rebalance and no_rebalance. The default is no_rebalance",
        ),
    ] = None


class TargetGroupHealthCheckType(BaseModel):
    model_config = ConfigDict(extra="forbid")
    interval: Annotated[
        float | None,
        Field(
            description="The approximate amount of time, in seconds, between health checks of an individual target. The range is 5-300. If the target group protocol is TCP, TLS, UDP, TCP_UDP, HTTP or HTTPS, the default is 30 seconds. If the target group protocol is GENEVE, the default is 10 seconds."
        ),
    ] = None
    path: Annotated[
        str | None,
        Field(
            description="[HTTP/HTTPS health checks] The destination for health checks on the targets. [HTTP1 or HTTP2 protocol version] The ping path. The default is /. [GRPC protocol version] The path of a custom health check method with the format /package.service/method. The default is /AWS.ALB/healthcheck.",
            min_length=1,
        ),
    ] = None
    port: Annotated[
        float | None,
        Field(
            description="The port the load balancer uses when performing health checks on targets. If the protocol is HTTP, HTTPS, TCP, TLS, UDP, or TCP_UDP, the default is `traffic-port`, which is the port on which each target receives traffic from the load balancer. If the protocol is GENEVE, the default is port 80."
        ),
    ] = None
    protocol: Annotated[
        TargetGroupHealthCheckProtocolType | None,
        Field(
            description="The protocol the load balancer uses when performing health checks on targets. For Application Load Balancers, the default is HTTP. For Network Load Balancers and Gateway Load Balancers, the default is TCP. The TCP protocol is not supported for health checks if the protocol of the target group is HTTP or HTTPS. GENEVE, TLS, UDP, and TCP_UDP protocols are not supported for health checks."
        ),
    ] = None
    timeout: Annotated[
        float | None,
        Field(
            description="The amount of time, in seconds, during which no response from a target means a failed health check. The range is 2–120 seconds. For target groups with a protocol of HTTP, the default is 6 seconds. For target groups with a protocol of TCP, TLS or HTTPS, the default is 10 seconds. For target groups with a protocol of GENEVE, the default is 5 seconds."
        ),
    ] = None


class TargetGroupMatcherType(BaseModel):
    model_config = ConfigDict(extra="forbid")
    grpc_code: Annotated[
        str | None,
        Field(
            alias="grpcCode",
            description='You can specify values between 0 and 99. You can specify multiple values (for example, "0,1") or a range of values (for example, "0-5"). The default value is 12.',
            min_length=1,
        ),
    ] = None
    http_code: Annotated[
        str | None,
        Field(
            alias="httpCode",
            description='For Application Load Balancers, you can specify values between 200 and 499, with the default value being 200. You can specify multiple values (for example, "200,202") or a range of values (for example, "200-299"). For Network Load Balancers, you can specify values between 200 and 599, with the default value being 200-399. You can specify multiple values (for example, "200,202") or a range of values (for example, "200-299"). Note that when using shorthand syntax, some values such as commas need to be escaped.',
            min_length=1,
        ),
    ] = None


class TransitGatewayAttachmentTargetConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    account: Annotated[str, Field(description="The friendly name of the account for the attachment target Transit Gateway.", min_length=1)]
    name: Annotated[str, Field(description="A friendly name for the attachment target Transit Gateway.", min_length=1)]


class TransitGatewayConnectOptionsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    protocol: Annotated[Literal["gre"], Field(description="The tunnel protocl for the Transit Gateway Connect")]


class TransitGatewayConnectVpcConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    vpc_attachment: Annotated[str, Field(alias="vpcAttachment", description="The name of the VPC attachment", min_length=1)]
    vpc_name: Annotated[str, Field(alias="vpcName", description="The name of the VPC", min_length=1)]


class TransitGatewayPeeringAccepterConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    account: Annotated[str, Field(description="The friendly name of the account of the accepter transit gateway", min_length=1)]
    apply_tags: Annotated[
        bool | None,
        Field(
            alias="applyTags",
            description="(OPTIONAL) Peering request apply tags flag. Note: When this flag is set to `true`, the requester attachment tags are replicated to the accepter attachment.",
        ),
    ] = None
    auto_accept: Annotated[
        bool | None,
        Field(
            alias="autoAccept",
            description="(OPTIONAL) Peering request auto accept flag. Note: When this flag is set to `true`, the peering request will be automatically accepted by the accelerator.",
        ),
    ] = None
    region: Annotated[str, Field(description="The name of the region the accepter transit gateway resides in")]
    route_table_associations: Annotated[
        str,
        Field(
            alias="routeTableAssociations",
            description="The friendly name of TGW route table to associate with this peering attachment.",
            min_length=1,
        ),
    ]
    transit_gateway_name: Annotated[
        str, Field(alias="transitGatewayName", description="The friendly name of the accepter transit gateway", min_length=1)
    ]


class TransitGatewayPeeringRequesterConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    account: Annotated[str, Field(description="The friendly name of the account of the requester transit gateway", min_length=1)]
    region: Annotated[str, Field(description="The name of the region the accepter transit gateway resides in")]
    route_table_associations: Annotated[
        str,
        Field(
            alias="routeTableAssociations",
            description="The friendly name of TGW route table to associate with this peering attachment.",
            min_length=1,
        ),
    ]
    tags: Annotated[list[Tag] | None, Field(description="(OPTIONAL) An array of tag objects for the Transit Gateway Peering.")] = None
    transit_gateway_name: Annotated[
        str, Field(alias="transitGatewayName", description="The friendly name of the requester transit gateway", min_length=1)
    ]


class TransitGatewayRouteTableDxGatewayEntryConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    direct_connect_gateway_name: Annotated[
        str, Field(alias="directConnectGatewayName", description="The name of the Direct Connect Gateway", min_length=1)
    ]


class TransitGatewayRouteTableTgwPeeringEntryConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    transit_gateway_peering_name: Annotated[
        str, Field(alias="transitGatewayPeeringName", description="The name of the Transit Gateway peering connection", min_length=1)
    ]


class TransitGatewayRouteTableVpcEntryConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    account: Annotated[str, Field(description="The friendly name of the account where the VPC resides.", min_length=1)]
    vpc_name: Annotated[str, Field(alias="vpcName", description="The friendly name of the VPC.", min_length=1)]


class TransitGatewayRouteTableVpnEntryConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    vpn_connection_name: Annotated[str, Field(alias="vpnConnectionName", description="The name of the VPN connection", min_length=1)]


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


class VpcDnsFirewallAssociationConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mutation_protection: Annotated[MutationProtectionType | None, Field(alias="mutationProtection")] = None
    name: Annotated[
        str,
        Field(
            description="## Non-Empty String Type\n\nRepresents a string that must contain at least one character. Used for required text fields throughout the Landing Zone Accelerator configuration where empty values are not permitted.\n\n```",
            min_length=1,
        ),
    ]
    priority: float
    tags: list[Tag] | None = None


class VpcFlowLogsCloudWatchLogsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kms: Annotated[
        str | None,
        Field(
            description="**KMS Key** *(Optional)*\n\nName of the KMS key to use for encrypting flow logs in CloudWatch Logs. Provides additional security for sensitive network traffic data.",
            min_length=1,
        ),
    ] = None
    retention_in_days: Annotated[
        float | None,
        Field(
            alias="retentionInDays",
            description="**Retention in Days** *(Optional)*\n\nNumber of days to retain flow logs in CloudWatch Logs. After this period, logs are automatically deleted to control costs.",
        ),
    ] = 365


class VpcIpv6Config(BaseModel):
    model_config = ConfigDict(extra="forbid")
    amazon_provided: Annotated[
        bool | None,
        Field(alias="amazonProvided", description="(OPTIONAL) Indicates whether Amazon automatically provisions a /56 IPv6 CIDR block for the VPC."),
    ] = None
    byoip_pool_id: Annotated[
        str | None,
        Field(
            alias="byoipPoolId",
            description="(OPTIONAL) Used to define the Bring-Your-Own-IP (BYOIP) address pool ID to use for the IPv6 CIDR block.",
            min_length=1,
        ),
    ] = None
    cidr_block: Annotated[
        str | None, Field(alias="cidrBlock", description="(OPTIONAL) Associate an IPv6 CIDR block with your VPC.", min_length=1)
    ] = None


class VpcPeeringConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: Annotated[str, Field(description="A friendly name for the peering connection.", min_length=1)]
    tags: Annotated[list[Tag] | None, Field(description="An array of tags for the peering connection.")] = None
    vpcs: Annotated[list[NonEmptyString], Field(description="The VPCs to peer.\n\nVPC can be from vpc or vpcTemplates configuration.")]


class VpnLoggingConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enable: Annotated[bool | None, Field(description="(OPTIONAL) Enable site-to-site VPN tunnel logging to CloudWatch Logs.")] = None
    log_group_name: Annotated[
        str | None,
        Field(
            alias="logGroupName",
            description="(OPTIONAL) The name of the CloudWatch Logs log group that you would like tunnel logs to be sent to.\n\nDefault - Randomly generated name based on CDK stack and VPN resource name.",
            min_length=1,
        ),
    ] = None
    output_format: Annotated[
        VpnLoggingOutputFormatType | None,
        Field(alias="outputFormat", description="(OPTIONAL) The output format of the VPN tunnel logs.\n\nDefault - `json`"),
    ] = None


class VpnTunnelOptionsSpecificationsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    dpd_timeout_action: Annotated[
        DpdTimeoutActionType | None,
        Field(
            alias="dpdTimeoutAction",
            description="(OPTIONAL) Dead Peer Detection (DPD) timeout action. You can specify the action to take after DPD timeout occurs.\n\nDefault - `clear`",
        ),
    ] = None
    dpd_timeout_seconds: Annotated[
        float | None,
        Field(
            alias="dpdTimeoutSeconds",
            description="(OPTIONAL) The duration, in seconds, after which Dead Peer Detection (DPD) timeout occurs.\n\nDefault - `30`",
        ),
    ] = None
    ike_versions: Annotated[
        list[IkeVersionType] | None,
        Field(
            alias="ikeVersions",
            description="(OPTIONAL) The Internet Key Exchange (IKE) versions that are permitted on the tunnel.\n\nDefault - `ikev1`,`ikev2`",
        ),
    ] = None
    logging: Annotated[VpnLoggingConfig | None, Field(description="(OPTIONAL) Site-to-Site VPN CloudWatch logging configuration.")] = None
    phase1: Annotated[Phase1Config | None, Field(description="(OPTIONAL) Internet Key Exchange (IKE) phase 1 configuration.")] = None
    phase2: Annotated[Phase2Config | None, Field(description="(OPTIONAL) Internet Key Exchange (IKE) phase 2 configuration.")] = None
    pre_shared_key: Annotated[
        str | None,
        Field(
            alias="preSharedKey",
            description="(OPTIONAL): The Secrets Manager name that stores the pre-shared key (PSK), that exists in the same account and region that the VPN Connection will be created in.",
            min_length=1,
        ),
    ] = None
    rekey_fuzz_percentage: Annotated[
        float | None,
        Field(
            alias="rekeyFuzzPercentage",
            description="(OPTIONAL) The percentage of the rekey window (determined by the rekey margin time) within which the rekey time is randomly selected.\n\nDefault - `100`",
        ),
    ] = None
    rekey_margin_time_seconds: Annotated[
        float | None,
        Field(
            alias="rekeyMarginTimeSeconds",
            description="(OPTIONAL) The margin time in seconds before the phase 1 and phase 2 lifetime expires, during which the AWS side of the VPN connection performs an IKE rekey.\n\nDefault - `270` (4.5 minutes)",
        ),
    ] = None
    replay_window_size: Annotated[
        float | None, Field(alias="replayWindowSize", description="(OPTIONAL) The number of packets in an IKE replay window.\n\nDefault - `1024`")
    ] = None
    startup_action: Annotated[
        StartupActionType | None,
        Field(
            alias="startupAction",
            description="(OPTIONAL) The action to take when the establishing the tunnel for the VPN connection. By default, your customer gateway device must initiate the IKE negotiation and bring up the tunnel. Specify `start` for Amazon Web Services to initiate the IKE negotiation.\n\nDefault - `add`",
        ),
    ] = None
    tunnel_inside_cidr: Annotated[
        str | None,
        Field(
            alias="tunnelInsideCidr",
            description="(OPTIONAL): The range of inside IP addresses for the tunnel. Any specified CIDR blocks must be unique across all VPN connections that use the same virtual private gateway.",
            min_length=1,
        ),
    ] = None
    tunnel_inside_ipv6_cidr: Annotated[
        str | None,
        Field(
            alias="tunnelInsideIpv6Cidr",
            description="(OPTIONAL): The range of inside IPv6 addresses for the tunnel. Any specified CIDR blocks must be unique across all VPN connections that use the same virtual private gateway.",
            min_length=1,
        ),
    ] = None
    tunnel_lifecycle_control: Annotated[
        bool | None,
        Field(
            alias="tunnelLifecycleControl",
            description="(OPTIONAL) Enable tunnel endpoint lifecycle control. This feature provides control over the schedule of endpoint replacements. For more information, see  {@link  https://docs.aws.amazon.com/vpn/latest/s2svpn/tunnel-endpoint-lifecycle.html Tunnel Endpoint Lifecycle Control } .",
        ),
    ] = None


class AlbListenerConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    certificate: Annotated[
        str | None,
        Field(
            description="Applies to HTTPS listeners. The default certificate for the listener. You must provide exactly one certificate arn or a certificate name which was created by LZA",
            min_length=1,
        ),
    ] = None
    fixed_response_config: Annotated[
        AlbListenerFixedResponseConfig | None,
        Field(
            alias="fixedResponseConfig",
            description="Information for creating an action that returns a custom HTTP response. Specify only when type is `fixed-response`.",
        ),
    ] = None
    forward_config: Annotated[
        AlbListenerForwardConfig | None,
        Field(
            alias="forwardConfig",
            description="Information for creating an action that distributes requests to targetGroup. Stickiness for targetGroup can be set here.",
        ),
    ] = None
    name: Annotated[str, Field(description="The name of the application load balancer listener", min_length=1)]
    order: Annotated[
        float | None,
        Field(
            description="The order for the action. This value is required for rules with multiple actions. The action with the lowest value for order is performed first"
        ),
    ] = None
    port: Annotated[float, Field(description="Port of the application load balancer listener")]
    protocol: Annotated[
        AlbListenerProtocolEnum, Field(description="Protocol of the application load balancer listener. The supported protocols are HTTP and HTTPS")
    ]
    redirect_config: Annotated[
        AlbListenerRedirectConfig | None,
        Field(alias="redirectConfig", description="Information for creating a redirect action. Specify only when type is `redirect`."),
    ] = None
    ssl_policy: Annotated[
        SslPolicyAlbEnum | None, Field(alias="sslPolicy", description="The security policy that defines which protocols and ciphers are supported.")
    ] = None
    target_group: Annotated[
        str,
        Field(
            alias="targetGroup",
            description="Target Group name to which traffic will be forwarded to. This name should be same as  {@link  ApplicationLoadBalancerTargetGroupConfig targetGroup }  name.",
            min_length=1,
        ),
    ]
    type: Annotated[AlbListenerTypeEnum, Field(description="Type of the application load balancer listener")]


class ApplicationLoadBalancerConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    attributes: Annotated[AlbAttributesConfig | None, Field(description="Attributes for Application Load Balancer.")] = None
    listeners: Annotated[list[AlbListenerConfig] | None, Field(description="Listeners for Application Load Balancer.")] = None
    name: Annotated[str, Field(description="The name of the application load balancer", min_length=1)]
    scheme: Annotated[AlbSchemeEnum | None, Field(description="Internal or internet facing scheme for Application Load Balancer.")] = None
    security_groups: Annotated[
        list[NonEmptyString], Field(alias="securityGroups", description="Security Groups to attach to the Application Load Balancer.")
    ]
    share_targets: Annotated[
        ShareTargets | None, Field(alias="shareTargets", description="The location where the Application Load Balancer(s) will be deployed to.\n*")
    ] = None
    subnets: Annotated[list[NonEmptyString], Field(description="Subnets to launch the Application Load Balancer in.")]


class DnsFirewallRuleGroupConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: Annotated[str, Field(description="A friendly name for the DNS firewall rule group.", min_length=1)]
    regions: Annotated[list[str], Field(description="The regions to deploy the rule group to.")]
    rules: Annotated[list[DnsFirewallRulesConfig], Field(description="An array of DNS firewall rule configurations.")]
    share_targets: Annotated[
        ShareTargets | None, Field(alias="shareTargets", description="(OPTIONAL) Resource Access Manager (RAM) share targets.")
    ] = None
    tags: Annotated[list[Tag] | None, Field(description="An array of tags for the rule group.")] = None


class DxGatewayConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    account: Annotated[str, Field(description="The friendly name of the account to deploy the DX Gateway.", min_length=1)]
    asn: Annotated[float, Field(description="A Border Gateway Protocol (BGP) Autonomous System Number (ASN).")]
    gateway_name: Annotated[
        str,
        Field(
            alias="gatewayName",
            description="The name of the Direct Connect Gateway. This name will show as the name of the resource in the AWS console and API.",
            min_length=1,
        ),
    ]
    name: Annotated[
        str,
        Field(
            description="A friendly name for the DX Gateway. This name is used as a logical reference for the resource in the accelerator.",
            min_length=1,
        ),
    ]
    transit_gateway_associations: Annotated[
        list[DxTransitGatewayAssociationConfig] | None,
        Field(
            alias="transitGatewayAssociations",
            description="(OPTIONAL) An array of transit gateway association configurations. Creates transit gateway attachments for this DX gateway.",
        ),
    ] = None
    virtual_interfaces: Annotated[
        list[DxVirtualInterfaceConfig] | None,
        Field(
            alias="virtualInterfaces",
            description="(OPTIONAL) An array of virtual interface configurations. Creates virtual interfaces on the DX gateway.",
        ),
    ] = None


class GatewayEndpointConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    default_policy: Annotated[
        str, Field(alias="defaultPolicy", description="The friendly name of the default policy for the gateway endpoints.", min_length=1)
    ]
    endpoints: Annotated[list[GatewayEndpointServiceConfig], Field(description="An array of endpoints to create.")]


class GwlbConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    account: Annotated[
        str | None, Field(description="(OPTIONAL) Set an override for the account the Gateway Load Balancer is deployed to.", min_length=1)
    ] = None
    cross_zone_load_balancing: Annotated[
        bool | None, Field(alias="crossZoneLoadBalancing", description="(OPTIONAL) Whether to enable cross-zone load balancing.")
    ] = None
    deletion_protection: Annotated[
        bool | None, Field(alias="deletionProtection", description="(OPTIONAL) Whether to enable deletion protection.")
    ] = None
    endpoints: Annotated[list[GwlbEndpointConfig], Field(description="An array of Gateway Load Balancer endpoint configurations.")]
    name: Annotated[str, Field(description="The friendly name of the Gateway Load Balancer.", min_length=1)]
    subnets: Annotated[list[NonEmptyString], Field(description="An array of friendly names of subnets to deploy the Gateway Load Balancer to.")]
    tags: Annotated[list[Tag] | None, Field(description="(OPTIONAL) An array of CloudFormation tag objects.")] = None
    target_group: Annotated[
        str | None, Field(alias="targetGroup", description="(OPTIONAL) The friendly name of a target group to forward traffic to", min_length=1)
    ] = None
    tcp_idle_timeout: Annotated[
        int | None,
        Field(alias="tcpIdleTimeout", description="(OPTIONAL) The TCP idle timeout value for the Gateway Load Balancer, in seconds.", ge=60, le=6000),
    ] = None
    vpc: Annotated[str, Field(description="The friendly name of the VPC to deploy the Gateway Load Balancer to.", min_length=1)]


class InterfaceEndpointConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    allowed_cidrs: Annotated[
        list[NonEmptyString] | None,
        Field(alias="allowedCidrs", description="(OPTIONAL) An array of source CIDRs allowed to communicate with the endpoints."),
    ] = None
    central: Annotated[bool | None, Field(description="(OPTIONAL) Enable to define interface endpoints as centralized endpoints.")] = None
    default_policy: Annotated[
        str, Field(alias="defaultPolicy", description="The friendly name of the default policy for the interface endpoints.", min_length=1)
    ]
    endpoints: Annotated[list[InterfaceEndpointServiceConfig], Field(description="An array of VPC interface endpoint services to be deployed.")]
    subnets: Annotated[list[NonEmptyString], Field(description="An array of the friendly names of VPC subnets for the endpoints to be deployed.")]
    tags: Annotated[
        list[Tag] | None,
        Field(description="(OPTIONAL) An array of tag objects for the private hosted zones associated with the VPC Interface endpoints."),
    ] = None


class IpamConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    description: Annotated[str | None, Field(description="(OPTIONAL) A description for the IPAM.", min_length=1)] = None
    name: Annotated[str, Field(description="A friendly name for the IPAM.", min_length=1)]
    operating_regions: Annotated[
        list[str] | None, Field(alias="operatingRegions", description="(OPTIONAL) An array of regions that the IPAM will manage.")
    ] = None
    pools: Annotated[list[IpamPoolConfig] | None, Field(description="An optional array of IPAM pool configurations to create under the IPAM.")] = None
    region: Annotated[str, Field(description="The region to deploy the IPAM.")]
    scopes: Annotated[
        list[IpamScopeConfig] | None, Field(description="(OPTIONAL) An array of IPAM scope configurations to create under the IPAM.")
    ] = None
    tags: Annotated[list[Tag] | None, Field(description="(OPTIONAL) An array of tag objects for the IPAM.")] = None


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


class LocalGatewayConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: Annotated[str, Field(description="The id for the Local Gateway", min_length=1)]
    name: Annotated[str, Field(description="A friendly name for the Local Gateway", min_length=1)]
    route_tables: Annotated[list[LocalGatewayRouteTableConfig], Field(alias="routeTables", description="The route tables for the Local Gateway")]


class NetworkAclInboundRuleConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: Annotated[AllowDeny, Field(description="The action for the network ACL rule.")]
    from_port: Annotated[float | None, Field(alias="fromPort", description="The port to start from in the network ACL rule.")] = None
    icmp: Annotated[
        NonEmptyString | IcmpRuleConfig | None,
        Field(
            description="(OPTIONAL) The Internet Control Message Protocol (ICMP) code and type. Required if specifying 1 (ICMP) for the protocol parameter."
        ),
    ] = None
    protocol: Annotated[
        float,
        Field(
            description="The  {@link  https://www.iana.org/assignments/protocol-numbers/protocol-numbers.xhtml IANA protocol number }  for the network ACL rule. You may also specify -1 for all protocols."
        ),
    ]
    rule: Annotated[float, Field(description="The rule ID number for the rule.")]
    source: Annotated[NonEmptyString | NetworkAclSubnetSelection, Field(description="The source of the network ACL rule.")]
    to_port: Annotated[float | None, Field(alias="toPort", description="The port to end with in the network ACL rule.")] = None


class NetworkAclOutboundRuleConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: Annotated[AllowDeny, Field(description="The action for the network ACL rule.")]
    destination: Annotated[NonEmptyString | NetworkAclSubnetSelection, Field(description="The destination of the network ACL rule.")]
    from_port: Annotated[float | None, Field(alias="fromPort", description="The port to start from in the network ACL rule.")] = None
    icmp: Annotated[
        NonEmptyString | IcmpRuleConfig | None,
        Field(
            description="(OPTIONAL) The Internet Control Message Protocol (ICMP) code and type. Required if specifying 1 (ICMP) for the protocol parameter."
        ),
    ] = None
    protocol: Annotated[
        float,
        Field(
            description="The  {@link  https://www.iana.org/assignments/protocol-numbers/protocol-numbers.xhtml IANA protocol number }  for the network ACL rule. You may also specify -1 for all protocols."
        ),
    ]
    rule: Annotated[float, Field(description="The rule ID number for the rule.")]
    to_port: Annotated[float | None, Field(alias="toPort", description="The port to end with in the network ACL rule.")] = None


class NetworkLoadBalancerConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    cross_zone_load_balancing: Annotated[
        bool | None, Field(alias="crossZoneLoadBalancing", description="Cross Zone load balancing for Network Load Balancer.")
    ] = None
    deletion_protection: Annotated[bool | None, Field(alias="deletionProtection", description="Deletion protection for Network Load Balancer.")] = (
        None
    )
    listeners: Annotated[list[NlbListenerConfig] | None, Field(description="Listeners for Network Load Balancer.")] = None
    name: Annotated[str, Field(description="Name for Network Load Balancer.", min_length=1)]
    scheme: Annotated[
        LoadBalancerSchemeEnum | None,
        Field(
            description="Load Balancer scheme. If undefined, the default of  {@link  https://docs.aws.amazon.com/elasticloadbalancing/latest/APIReference/API_CreateLoadBalancer.html ELBv2 CreateLoadBalancer API }  is used."
        ),
    ] = None
    subnets: Annotated[list[NonEmptyString], Field(description="Subnets to launch the Network Load Balancer in.")]


class NfwFirewallConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    delete_protection: Annotated[
        bool | None, Field(alias="deleteProtection", description="(OPTIONAL) Enable for deletion protection on the firewall.")
    ] = None
    description: Annotated[str | None, Field(description="(OPTIONAL) A description for the firewall.", min_length=1)] = None
    firewall_policy: Annotated[
        str,
        Field(
            alias="firewallPolicy",
            description="The friendly name of the Network Firewall policy or ARN for an existing network firewall policy.",
            min_length=1,
        ),
    ]
    firewall_policy_change_protection: Annotated[
        bool | None, Field(alias="firewallPolicyChangeProtection", description="(OPTIONAL) Enable to disallow firewall policy changes.")
    ] = None
    logging_configuration: Annotated[
        list[NfwLoggingConfig] | None,
        Field(alias="loggingConfiguration", description="(OPTIONAL) An array of Network Firewall logging configurations."),
    ] = None
    name: Annotated[str, Field(description="A friendly name for the firewall.", min_length=1)]
    subnet_change_protection: Annotated[
        bool | None, Field(alias="subnetChangeProtection", description="(OPTIONAL) Enable to disallow firewall subnet changes.")
    ] = None
    subnets: Annotated[list[NonEmptyString], Field(description="An array of the friendly names of subnets to deploy Network Firewall to.")]
    tags: Annotated[list[Tag] | None, Field(description="(OPTIONAL) An array of tags for the firewall.")] = None
    vpc: Annotated[str, Field(description="The friendly name of the VPC to deploy Network Firewall to.", min_length=1)]


class NfwRuleSourceCustomActionDefinitionConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    publish_metric_action: Annotated[
        NfwRuleSourceCustomActionDimensionConfig,
        Field(alias="publishMetricAction", description="A Network Firewall custom action dimensions configuration."),
    ]


class NfwRuleSourceStatefulRuleConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action: Annotated[NfwStatefulRuleActionType, Field(description="The action type for the stateful rule.")]
    header: Annotated[NfwRuleSourceStatefulRuleHeaderConfig, Field(description="A Network Firewall stateful rule header configuration.")]
    rule_options: Annotated[
        list[NfwRuleSourceStatefulRuleOptionsConfig],
        Field(alias="ruleOptions", description="An array of Network Firewall stateful rule options configurations."),
    ]


class NfwRuleSourceStatelessMatchAttributesConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    destination_ports: Annotated[
        list[NfwRuleSourceStatelessPortRangeConfig] | None,
        Field(alias="destinationPorts", description="(OPTIONAL) An array of Network Firewall stateless port range configurations."),
    ] = None
    destinations: Annotated[list[NonEmptyString] | None, Field(description="(OPTIONAL) An array of destination CIDR ranges to inspect for.")] = None
    protocols: Annotated[list[float] | None, Field(description="(OPTIONAL) An array of IP protocol numbers to inspect for.")] = None
    source_ports: Annotated[
        list[NfwRuleSourceStatelessPortRangeConfig] | None,
        Field(alias="sourcePorts", description="(OPTIONAL) An array of Network Firewall stateless port range configurations."),
    ] = None
    sources: Annotated[list[NonEmptyString] | None, Field(description="(OPTIONAL) An array of source CIDR ranges to inspect for.")] = None
    tcp_flags: Annotated[
        list[NfwRuleSourceStatelessTcpFlagsConfig] | None,
        Field(alias="tcpFlags", description="(OPTIONAL) An array of Network Firewall stateless TCP flag configurations."),
    ] = None


class NfwRuleSourceStatelessRuleDefinitionConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    actions: Annotated[
        list[NonEmptyString | NfwStatelessRuleActionType], Field(description="An array of actions to take using the stateless rule engine.")
    ]
    match_attributes: Annotated[
        NfwRuleSourceStatelessMatchAttributesConfig,
        Field(alias="matchAttributes", description="A Network Firewall stateless rule match attributes configuration."),
    ]


class NfwRuleVariableConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    ip_sets: Annotated[
        NfwRuleVariableDefinitionConfig | list[NfwRuleVariableDefinitionConfig],
        Field(
            alias="ipSets",
            description="A Network Firewall rule variable definition for IP addresses.\n\nEach `definition` value is an IPv4 address or CIDR range (for example `'10.0.0.0/16'`).",
        ),
    ]
    port_sets: Annotated[
        NfwRuleVariableDefinitionConfig | list[NfwRuleVariableDefinitionConfig],
        Field(
            alias="portSets",
            description="A Network Firewall rule variable definition for TCP/UDP ports.\n\nEach `definition` value is either a single port (`'443'`) or an inclusive port range expressed with a colon separator (`'<fromPort>:<toPort>'`, for example `'1024:2048'`). Single ports and ranges may be combined in the same array (`['80', '443', '1024:2048']`). All port numbers must be between `0` and `65535`, and for ranges `fromPort` must be less than or equal to `toPort`.",
        ),
    ]


class OutpostsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    arn: Annotated[str, Field(description="The ARN for the Outpost", min_length=1)]
    availability_zone: Annotated[
        NonEmptyString | float, Field(alias="availabilityZone", description="The availability zone where the Outpost resides")
    ]
    local_gateway: Annotated[
        LocalGatewayConfig | None, Field(alias="localGateway", description="The Local Gateway configuration for the Outpost")
    ] = None
    name: Annotated[str, Field(description="A friendly name for the Outpost", min_length=1)]


class ResolverRuleConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    domain_name: Annotated[str, Field(alias="domainName", description="The domain name for the resolver rule.", min_length=1)]
    excluded_regions: Annotated[
        list[str] | None, Field(alias="excludedRegions", description="(OPTIONAL) Regions to exclude from SYSTEM rule deployment.")
    ] = None
    inbound_endpoint_target: Annotated[
        str | None,
        Field(
            alias="inboundEndpointTarget",
            description="(OPTIONAL) The friendly name of an inbound endpoint to target.\n\nA FORWARD rule must be created with a target. You must specify exactly one of `inboundEndpointTarget` or `targetIps` on a FORWARD rule. Defining both, or omitting both, fails validation. This property is marked optional only because `targetIps` is the alternative way to supply the rule's target.",
            min_length=1,
        ),
    ] = None
    name: Annotated[str, Field(description="A friendly name for the resolver rule.", min_length=1)]
    rule_type: Annotated[RuleType | None, Field(alias="ruleType", description="(OPTIONAL) The type of rule to create.")] = None
    share_targets: Annotated[
        ShareTargets | None, Field(alias="shareTargets", description="(OPTIONAL) Resource Access Manager (RAM) share targets.")
    ] = None
    tags: Annotated[list[Tag] | None, Field(description="(OPTIONAL) An array of tags for the resolver rule.")] = None
    target_ips: Annotated[
        list[RuleTargetIps] | None,
        Field(
            alias="targetIps",
            description="(OPTIONAL) An array of target IP configurations for the resolver rule.\n\nA FORWARD rule must be created with a target. You must specify exactly one of `targetIps` or `inboundEndpointTarget` on a FORWARD rule. Defining both, or omitting both, fails validation. This property is marked optional only because `inboundEndpointTarget` is the alternative way to supply the rule's target.\n\nWhen this FORWARD rule is referenced by a managed Active Directory's `resolverRuleName` property, you must still seed `targetIps` with at least one placeholder IP address. The managed AD integration updates an existing rule by replacing its target IP addresses with the directory's DNS server IPs (and reads the DNS port from an existing target entry); it cannot populate a rule that has no target.",
        ),
    ] = None


class RouteTableConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enable_route_propagation: Annotated[
        bool | None, Field(alias="enableRoutePropagation", description="(OPTIONAL) Enable VPN Gateway route propagation for this route table.")
    ] = None
    gateway_association: Annotated[
        GatewayRouteTableType | None, Field(alias="gatewayAssociation", description="Designate a gateway to associate this route table with.")
    ] = None
    name: Annotated[str, Field(description="A friendly name for the VPC route table.", min_length=1)]
    routes: Annotated[list[RouteTableEntryConfig] | None, Field(description="An array of VPC route table entry configuration objects.")] = None
    tags: Annotated[list[Tag] | None, Field(description="(OPTIONAL) An array of tag objects for the VPC route table.")] = None


class SecurityGroupRuleConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    description: Annotated[str, Field(description="A description for the security group rule.", min_length=1)]
    from_port: Annotated[float | None, Field(alias="fromPort", description="(OPTIONAL) The port to start from in the security group rule.")] = None
    ip_protocols: Annotated[
        list[str] | None, Field(alias="ipProtocols", description="(OPTIONAL) An array of custom IP Protocols for the security group rule")
    ] = None
    sources: Annotated[
        list[NonEmptyString | SubnetSourceConfig | SecurityGroupSourceConfig | PrefixListSourceConfig],
        Field(description="An array of sources for the security group rule."),
    ]
    tcp_ports: Annotated[
        list[float] | None, Field(alias="tcpPorts", description="(OPTIONAL) An array of TCP ports to include in the security group rule.")
    ] = None
    to_port: Annotated[float | None, Field(alias="toPort", description="(OPTIONAL) The port to end with in the security group rule.")] = None
    types: Annotated[
        list[SecurityGroupRuleType] | None, Field(description="(OPTIONAL) An array of port/protocol types to include in the security group rule.")
    ] = None
    udp_ports: Annotated[
        list[float] | None, Field(alias="udpPorts", description="(OPTIONAL) An array of UDP ports to include in the security group rule.")
    ] = None


class TargetGroupItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    attributes: Annotated[TargetGroupAttributeTypes | None, Field(description="Target Group Attributes.")] = None
    health_check: Annotated[TargetGroupHealthCheckType | None, Field(alias="healthCheck", description="Target Group HealthCheck.")] = None
    matcher: Annotated[
        TargetGroupMatcherType | None,
        Field(
            description="The HTTP or gRPC codes to use when checking for a successful response from a target. For target groups with a protocol of TCP, TCP_UDP, UDP or TLS the range is 200-599. For target groups with a protocol of HTTP or HTTPS, the range is 200-499."
        ),
    ] = None
    name: Annotated[
        str,
        Field(
            description="The name of the target group. This value is used in  {@link  ApplicationLoadBalancerListenerConfig Application Load Balancer listeners } ,  {@link  NetworkLoadBalancerListenerConfig Network Load Balancer listeners } , and  {@link  AutoScalingConfig Autoscaling config } .",
            min_length=1,
        ),
    ]
    port: Annotated[float, Field(description="The port on which the targets receive traffic.")]
    protocol: Annotated[
        TargetGroupProtocolType,
        Field(
            description="Target group protocol version. Should be one of HTTP, HTTPS, GENEVE, TCP, UDP, TCP_UDP or TLS The protocol to use for routing traffic to the targets. For Application Load Balancers, the supported protocols are HTTP and HTTPS. For Network Load Balancers, the supported protocols are TCP, TLS, UDP, or TCP_UDP. A TCP_UDP listener must be associated with a TCP_UDP target group. For Gateway Load Balancers, the supported protocol is GENEVE."
        ),
    ]
    protocol_version: Annotated[
        TargetGroupProtocolVersionType | None,
        Field(
            alias="protocolVersion",
            description="The protocol version. Should be one of 'GRPC', 'HTTP1', 'HTTP2'. Specify GRPC to send requests to targets using gRPC. Specify HTTP2 to send requests to targets using HTTP/2. The default is HTTP1, which sends requests to targets using HTTP/1.1.",
        ),
    ] = None
    share_targets: Annotated[
        ShareTargets | None, Field(alias="shareTargets", description="The accounts/OUs location where the Target Group will be deployed to.")
    ] = None
    targets: Annotated[
        list[NonEmptyString | NlbTargetType] | None,
        Field(description="Target group targets. These targets should be the friendly names assigned to firewall instances."),
    ] = None
    threshold: Annotated[TargetGroupThresholdType | None, Field(description="Target Group Threshold.")] = None
    type: Annotated[
        TargetGroupType,
        Field(
            description="The type of target that you must specify when registering targets with this target group. You can't specify targets for a target group using more than one target type.\n- `instance` - Register targets by instance ID. This is the default value.\n- `ip` - Register targets by IP address. You can specify IP addresses from the subnets of the virtual private cloud (VPC) for the target group, the RFC 1918 range (10.0.0.0/8, 172.16.0.0/12, and 192.168.0.0/16), and the RFC 6598 range (100.64.0.0/10). You can't specify publicly routable IP addresses. `alb` - Register a single Application Load Balancer as a target."
        ),
    ]


class TransitGatewayAttachmentConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: Annotated[str, Field(description="A friendly name for the Transit Gateway attachment.", min_length=1)]
    options: Annotated[
        TransitGatewayAttachmentOptionsConfig | None, Field(description="(OPTIONAL) A Transit Gateway attachment options configuration.")
    ] = None
    route_table_associations: Annotated[
        list[NonEmptyString] | None,
        Field(alias="routeTableAssociations", description="The friendly name of a Transit Gateway route table to associate the attachment to."),
    ] = None
    route_table_propagations: Annotated[
        list[NonEmptyString] | None,
        Field(alias="routeTablePropagations", description="An array of friendly names of Transit Gateway route tables to propagate the attachment."),
    ] = None
    subnets: Annotated[list[NonEmptyString], Field(description="An array of the friendly names of VPC subnets for the attachment to be deployed.")]
    tags: Annotated[list[Tag] | None, Field(description="(OPTIONAL) An array of tag objects for the Transit Gateway attachment.")] = None
    transit_gateway: Annotated[
        TransitGatewayAttachmentTargetConfig, Field(alias="transitGateway", description="A Transit Gateway attachment target configuration object.")
    ]


class TransitGatewayConnectConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    direct_connect: Annotated[
        str | None,
        Field(
            alias="directConnect",
            description="(OPTIONAL) The Direct Connect Gateway Attachment that belongs to the Transit Gateway that a Transit Gateway Connect Attachment is being made for.",
            min_length=1,
        ),
    ] = None
    name: Annotated[str, Field(description="A friendly name for the Transit Gateway Connect attachment.", min_length=1)]
    options: Annotated[TransitGatewayConnectOptionsConfig | None, Field(description="(OPTIONAL) Options around the Transit Gateway Connect")] = None
    region: Annotated[str, Field(description="The AWS Region for the attachment.", min_length=1)]
    route_table_associations: Annotated[
        list[NonEmptyString] | None,
        Field(
            alias="routeTableAssociations",
            description="(OPTIONAL) The friendly name of a Transit Gateway route table to associate the Connect attachment to.",
        ),
    ] = None
    route_table_propagations: Annotated[
        list[NonEmptyString] | None,
        Field(
            alias="routeTablePropagations",
            description="(OPTIONAL) An array of friendly names of Transit Gateway route tables to propagate the Connect attachment.",
        ),
    ] = None
    tags: Annotated[list[Tag] | None, Field(description="(OPTIONAL) An array of tag objects for the Transit Gateway attachment.")] = None
    transit_gateway: Annotated[
        TransitGatewayAttachmentTargetConfig,
        Field(alias="transitGateway", description="The Transit Gateway configuration object to set the Transit Gateway Connect."),
    ]
    vpc: Annotated[
        TransitGatewayConnectVpcConfig | None,
        Field(description="The VPC Attachment that belongs to the Transit Gateway that a Transit Gateway Connect Attachment is being made for."),
    ] = None


class TransitGatewayPeeringConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    accepter: Annotated[TransitGatewayPeeringAccepterConfig, Field(description="Peering attachment accepter configuration")]
    name: Annotated[str, Field(description="The friendly name of TGW peering.", min_length=1)]
    requester: Annotated[TransitGatewayPeeringRequesterConfig, Field(description="Peering attachment requester configuration.")]


class TransitGatewayRouteEntryConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    attachment: Annotated[
        TransitGatewayRouteTableVpcEntryConfig
        | TransitGatewayRouteTableDxGatewayEntryConfig
        | TransitGatewayRouteTableVpnEntryConfig
        | TransitGatewayRouteTableTgwPeeringEntryConfig
        | None,
        Field(
            description="The target  {@link  https://docs.aws.amazon.com/vpc/latest/tgw/working-with-transit-gateways.html Transit Gateway attachment }  for the route table entry. Supported attachment types include:\n\n- VPC\n- Direct Connect Gateway\n- VPN\n- Transit Gateway Peering"
        ),
    ] = None
    blackhole: Annotated[
        bool | None,
        Field(description="(OPTIONAL) Enable to create a blackhole for the destination CIDR. Leave undefined if specifying a VPC destination."),
    ] = None
    destination_cidr_block: Annotated[
        str | None, Field(alias="destinationCidrBlock", description="The destination IPv4/v6 CIDR block for the route table entry.", min_length=1)
    ] = None
    destination_prefix_list: Annotated[
        str | None, Field(alias="destinationPrefixList", description="The friendly name of a prefix list for the route table entry.", min_length=1)
    ] = None


class TransitGatewayRouteTableConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: Annotated[str, Field(description="A friendly name for the Transit Gateway route table.", min_length=1)]
    routes: Annotated[list[TransitGatewayRouteEntryConfig], Field(description="An array of Transit Gateway route entry configuration objects.")]
    tags: Annotated[list[Tag] | None, Field(description="(OPTIONAL) An array of tag objects for the Transit Gateway route table.")] = None


class VpcFlowLogsS3BucketConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    lifecycle_rules: Annotated[
        list[LifecycleRule] | None,
        Field(
            alias="lifecycleRules",
            description="**Lifecycle Rules** *(Optional)*\n\nS3 lifecycle rules to manage flow log files automatically. Controls when logs transition to cheaper storage classes and when they expire.",
        ),
    ] = None
    override_s3_log_path: Annotated[
        str | None,
        Field(
            alias="overrideS3LogPath",
            description="**Override S3 Log Path** *(Optional)*\n\nCustom S3 key prefix for organizing flow log files. Overrides the default LZA path structure for flow logs.",
            min_length=1,
        ),
    ] = None


class VpnConnectionConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    amazon_ipv4_network_cidr: Annotated[
        str | None,
        Field(
            alias="amazonIpv4NetworkCidr",
            description="(OPTIONAL) The Amazon-side IPv4 CIDR range that is allowed through the site-to-site VPN tunnel. Configuring this option restricts the Amazon-side CIDR range that can communicate with your local network.\n\nDefault - `0.0.0.0/0`",
            min_length=1,
        ),
    ] = None
    amazon_ipv6_network_cidr: Annotated[
        str | None,
        Field(
            alias="amazonIpv6NetworkCidr",
            description="(OPTIONAL) The Amazon-side IPv6 CIDR range that is allowed through the site-to-site VPN tunnel. Configuring this option restricts the Amazon-side CIDR range that can communicate with your local network.\n\nDefault - `::/0`",
            min_length=1,
        ),
    ] = None
    customer_ipv4_network_cidr: Annotated[
        str | None,
        Field(
            alias="customerIpv4NetworkCidr",
            description="(OPTIONAL) The customer-side IPv4 CIDR range that is allowed through the site-to-site VPN tunnel. Configuring this option restricts the local CIDR range that can communicate with your AWS environment.\n\nDefault - `0.0.0.0/0`",
            min_length=1,
        ),
    ] = None
    customer_ipv6_network_cidr: Annotated[
        str | None,
        Field(
            alias="customerIpv6NetworkCidr",
            description="(OPTIONAL) The customer-side IPv6 CIDR range that is allowed through the site-to-site VPN tunnel. Configuring this option restricts the local CIDR range that can communicate with your AWS environment.\n\nDefault - `::/0`",
            min_length=1,
        ),
    ] = None
    enable_vpn_acceleration: Annotated[
        bool | None,
        Field(
            alias="enableVpnAcceleration",
            description="(OPTIONAL) Enable Site-to-Site VPN Acceleration. For more information, see  {@link  https://docs.aws.amazon.com/vpn/latest/s2svpn/accelerated-vpn.html Accelerated Site-to-Site VPN connections } .",
        ),
    ] = None
    name: Annotated[
        str,
        Field(
            description="The name of the VPN Connection.\n\nThe value of this property will be utilized as the logical id for this resource. Any references to this object should specify this value.",
            min_length=1,
        ),
    ]
    outside_ip_address_type: Annotated[
        OutsideIpAddressType | None,
        Field(
            alias="outsideIpAddressType",
            description="(OPTIONALThe type of IP address assigned to the outside interface of the customer gateway device. Valid values include `PublicIpv4` or `Ipv6`.",
        ),
    ] = None
    route_table_associations: Annotated[
        list[NonEmptyString] | None,
        Field(
            alias="routeTableAssociations", description="(OPTIONAL) An array of Transit Gateway route table names to associate the VPN attachment to"
        ),
    ] = None
    route_table_propagations: Annotated[
        list[NonEmptyString] | None,
        Field(
            alias="routeTablePropagations", description="(OPTIONAL) An array of Transit Gateway route table names to propagate the VPN attachment to"
        ),
    ] = None
    static_routes_only: Annotated[
        bool | None,
        Field(
            alias="staticRoutesOnly",
            description="(OPTIONAL) If creating a VPN connection for a device that doesn't support Border Gateway Protocol (BGP) declare true as a value, otherwise, use false.",
        ),
    ] = None
    tags: Annotated[list[Tag] | None, Field(description="(OPTIONAL) An array of tags for the VPN Connection.")] = None
    transit_gateway: Annotated[
        str | None,
        Field(
            alias="transitGateway",
            description="The logical name of the Transit Gateway that the customer Gateway is attached to so that a VPN connection is established.",
            min_length=1,
        ),
    ] = None
    tunnel_specifications: Annotated[
        list[VpnTunnelOptionsSpecificationsConfig] | None,
        Field(alias="tunnelSpecifications", description="(OPTIONAL) Define the optional VPN Tunnel configuration"),
    ] = None
    vpc: Annotated[
        str | None, Field(description="The logical name of the Virtual Private Cloud that a Virtual Private Gateway is attached to.", min_length=1)
    ] = None


class CustomerGatewayConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    account: Annotated[
        str,
        Field(
            description="The logical name of the account to deploy the Customer Gateway to. This value should match the name of the account recorded in the accounts-config.yaml file.",
            min_length=1,
        ),
    ]
    asn: Annotated[float, Field(description="Define the ASN used for the Customer Gateway")]
    ip_address: Annotated[str, Field(alias="ipAddress", description="Defines the IP address of the Customer Gateway", min_length=1)]
    name: Annotated[
        str,
        Field(
            description="The name of the CGW.\n\nThe value of this property will be utilized as the logical id for this resource. Any references to this object should specify this value.",
            min_length=1,
        ),
    ]
    region: Annotated[str, Field(description="The AWS region to provision the customer gateway in")]
    tags: Annotated[list[Tag] | None, Field(description="Define tags for the Customer Gateway")] = None
    vpn_connections: Annotated[
        list[VpnConnectionConfig] | None, Field(alias="vpnConnections", description="Define the optional VPN Connection configuration")
    ] = None


class LoadBalancersConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    application_load_balancers: Annotated[
        list[ApplicationLoadBalancerConfig] | None,
        Field(
            alias="applicationLoadBalancers",
            description="(OPTIONAL) An array of Application Load Balancer (ALB) configurations. Use this property to define ALBs to be deployed in the specified VPC subnets.",
        ),
    ] = None
    network_load_balancers: Annotated[
        list[NetworkLoadBalancerConfig] | None,
        Field(
            alias="networkLoadBalancers",
            description="(OPTIONAL) An array of Network Load Balancer (NLB) configurations. Use this property to define NLBs to be deployed in the specified VPC subnets.",
        ),
    ] = None


class NetworkAclConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    inbound_rules: Annotated[
        list[NetworkAclInboundRuleConfig] | None,
        Field(alias="inboundRules", description="(OPTIONAL) A list of inbound rules to define for the Network ACL"),
    ] = None
    name: Annotated[str, Field(description="The name of the Network ACL.", min_length=1)]
    outbound_rules: Annotated[
        list[NetworkAclOutboundRuleConfig] | None,
        Field(alias="outboundRules", description="(OPTIONAL) A list of outbound rules to define for the Network ACL"),
    ] = None
    subnet_associations: Annotated[
        list[NonEmptyString], Field(alias="subnetAssociations", description="A list of subnets to associate with the Network ACL")
    ]
    tags: Annotated[list[Tag] | None, Field(description="(OPTIONAL) A list of tags to attach to the Network ACL")] = None


class NfwRuleSourceCustomActionConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    action_definition: Annotated[
        NfwRuleSourceCustomActionDefinitionConfig,
        Field(alias="actionDefinition", description="A Network Firewall custom action definition configuration."),
    ]
    action_name: Annotated[str, Field(alias="actionName", description="A friendly name for the custom action.", min_length=1)]


class NfwRuleSourceStatelessRuleConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    priority: Annotated[float, Field(description="The priority number for the rule.")]
    rule_definition: Annotated[
        NfwRuleSourceStatelessRuleDefinitionConfig,
        Field(alias="ruleDefinition", description="A Network Firewall stateless rule definition configuration."),
    ]


class NfwStatelessRulesAndCustomActionsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    custom_actions: Annotated[
        list[NfwRuleSourceCustomActionConfig] | None,
        Field(alias="customActions", description="An array of Network Firewall custom action configurations."),
    ] = None
    stateless_rules: Annotated[
        list[NfwRuleSourceStatelessRuleConfig],
        Field(alias="statelessRules", description="An array of Network Firewall stateless rule configurations."),
    ]


class ResolverEndpointConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    allowed_cidrs: Annotated[
        list[NonEmptyString] | None,
        Field(alias="allowedCidrs", description="(OPTIONAL) The allowed ingress/egress CIDRs for the resolver endpoint security group."),
    ] = None
    name: Annotated[str, Field(description="The friendly name of the resolver endpoint.", min_length=1)]
    protocols: Annotated[
        list[ResolverProtocol] | None,
        Field(description="(OPTIONAL) An array of DNS Queries over HTTPS (DoH) Protocols to apply to the Route 53 Resolver Endpoints."),
    ] = None
    rules: Annotated[list[ResolverRuleConfig] | None, Field(description="(OPTIONAL) An array of resolver rule configurations for the endpoint.")] = (
        None
    )
    subnets: Annotated[list[NonEmptyString], Field(description="An array of friendly names for subnets to deploy the resolver endpoint to.")]
    tags: Annotated[list[Tag] | None, Field(description="(OPTIONAL) An array of tags for the resolver endpoint.")] = None
    type: Annotated[
        ResolverEndpointType,
        Field(
            description="The type of resolver endpoint to deploy.\n\nINBOUND: allows DNS queries to your VPC from your network\n\nOUTBOUND: allows DNS queries from your VPC to your network"
        ),
    ]
    vpc: Annotated[str, Field(description="The friendly name of the VPC to deploy the resolver endpoint to.", min_length=1)]


class SecurityGroupConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    description: Annotated[str | None, Field(description="(OPTIONAL) A description for the security group.", min_length=1)] = None
    inbound_rules: Annotated[
        list[SecurityGroupRuleConfig], Field(alias="inboundRules", description="An array of security group rule configurations for ingress rules.")
    ]
    name: Annotated[str, Field(description="The friendly name of the security group.", min_length=1)]
    outbound_rules: Annotated[
        list[SecurityGroupRuleConfig], Field(alias="outboundRules", description="An array of security group rule configurations for egress rules.")
    ]
    tags: Annotated[list[Tag] | None, Field(description="(OPTIONAL) An array of tag objects for the security group.")] = None


class VpcFlowLogsDestinationConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    cloud_watch_logs: Annotated[
        VpcFlowLogsCloudWatchLogsConfig | None,
        Field(
            alias="cloudWatchLogs",
            description="**CloudWatch Logs Configuration** *(Optional)*\n\nConfiguration for CloudWatch Logs destination including retention and encryption. Used when flow logs are sent to CloudWatch Logs for real-time monitoring.",
        ),
    ] = None
    s3: Annotated[
        VpcFlowLogsS3BucketConfig | None,
        Field(
            description="**S3 Configuration** *(Optional)*\n\nConfiguration for S3 destination including lifecycle rules and custom paths. Used when flow logs are sent to Amazon S3 for long-term storage and analysis."
        ),
    ] = None


class VpcResolverConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    endpoints: Annotated[
        list[ResolverEndpointConfig] | None, Field(description="(OPTIONAL) An array of Route 53 resolver endpoint configurations.")
    ] = None
    query_logs: Annotated[
        DnsQueryLogsConfig | None, Field(alias="queryLogs", description="(OPTIONAL) A Route 53 resolver DNS query logging configuration.")
    ] = None


class NfwFirewallPolicyPolicyConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    stateful_default_actions: Annotated[
        list[NfwStatefulDefaultActionType] | None,
        Field(
            alias="statefulDefaultActions", description="(OPTIONAL) An array of default actions to take on packets evaluated by the stateful engine."
        ),
    ] = None
    stateful_engine_options: Annotated[
        NfwStatefulRuleOptionsType | None,
        Field(alias="statefulEngineOptions", description="(OPTIONAL) Define how the stateful engine will evaluate packets."),
    ] = None
    stateful_rule_groups: Annotated[
        list[NfwStatefulRuleGroupReferenceConfig] | None,
        Field(alias="statefulRuleGroups", description="{OPTIONAL) An array of Network Firewall stateful rule group reference configurations."),
    ] = None
    stateless_custom_actions: Annotated[
        list[NfwRuleSourceCustomActionConfig] | None,
        Field(alias="statelessCustomActions", description="(OPTIONAL) An array of Network Firewall custom action configurations."),
    ] = None
    stateless_default_actions: Annotated[
        list[NfwStatelessRuleActionType | NonEmptyString],
        Field(alias="statelessDefaultActions", description="An array of default actions to take on packets evaluated by the stateless engine."),
    ]
    stateless_fragment_default_actions: Annotated[
        list[NfwStatelessRuleActionType | NonEmptyString],
        Field(alias="statelessFragmentDefaultActions", description="An array of default actions to take on fragmented packets."),
    ]
    stateless_rule_groups: Annotated[
        list[NfwStatelessRuleGroupReferenceConfig] | None,
        Field(alias="statelessRuleGroups", description="(OPTIONAL) An array of Network Firewall stateless rule group reference configurations."),
    ] = None


class NfwRuleSourceConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    rules_file: Annotated[
        str | None,
        Field(
            alias="rulesFile",
            description="(OPTIONAL) Suricata rules file. Use this property to define a Suricata-compatible rules file for Network Firewall.",
            min_length=1,
        ),
    ] = None
    rules_source_list: Annotated[
        NfwRuleSourceListConfig | None,
        Field(
            alias="rulesSourceList",
            description="(OPTIONAL) A Network Firewall rule source list configuration. Use this property to define a domain list for Network Firewall.",
        ),
    ] = None
    rules_string: Annotated[
        str | None,
        Field(
            alias="rulesString",
            description="(OPTIONAL) A Suricata-compatible stateful rule string. Use this property to define a single Suricata-compatible rule for Network Firewall.",
            min_length=1,
        ),
    ] = None
    stateful_rules: Annotated[
        list[NfwRuleSourceStatefulRuleConfig] | None,
        Field(
            alias="statefulRules",
            description="(OPTIONAL) An array of Network Firewall stateful rule IP header configurations. Use this property to define a stateful rule in IP header format for Network Firewall.",
        ),
    ] = None
    stateless_rules_and_custom_actions: Annotated[
        NfwStatelessRulesAndCustomActionsConfig | None,
        Field(
            alias="statelessRulesAndCustomActions",
            description="(OPTIONAL) A Network Firewall stateless rules and custom action configuration. Use this property to define stateless rules and custom actions for Network Firewall.",
        ),
    ] = None


class ResolverConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    endpoints: Annotated[
        list[ResolverEndpointConfig] | None, Field(description="(OPTIONAL) An array of Route 53 resolver endpoint configurations.")
    ] = None
    firewall_rule_groups: Annotated[
        list[DnsFirewallRuleGroupConfig] | None,
        Field(alias="firewallRuleGroups", description="(OPTIONAL) An array of Route 53 DNS firewall rule group configurations."),
    ] = None
    query_logs: Annotated[
        DnsQueryLogsConfig | None, Field(alias="queryLogs", description="(OPTIONAL) A Route 53 resolver DNS query logging configuration.")
    ] = None
    rules: Annotated[list[ResolverRuleConfig] | None, Field(description="(OPTIONAL) An array of Route 53 resolver rules.")] = None


class TransitGatewayFlowLogsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    custom_fields: Annotated[
        list[NonEmptyString],
        Field(
            alias="customFields",
            description="**Custom Fields** *(Required when defaultFormat is false)*\n\nArray of specific fields to include in flow log records when using custom format. This allows you to capture exactly the network information needed for your use cases.",
        ),
    ]
    default_format: Annotated[
        bool,
        Field(
            alias="defaultFormat",
            description="**Use Default Format** *(Required)*\n\nControls whether to use the AWS default flow log format or a custom format with specific fields. When false, allows customization of logged fields.",
        ),
    ]
    destinations: Annotated[
        list[LogDestinationType],
        Field(
            description="**Log Destinations** *(Required)*\n\nArray of destination services where Transit Gateway flow logs should be delivered. You can send logs to one or both supported destinations simultaneously."
        ),
    ]
    destinations_config: Annotated[
        VpcFlowLogsDestinationConfig | None,
        Field(
            alias="destinationsConfig",
            description="**Log Destinations** *(Required)*\n\nArray of destination services where VPC flow logs should be delivered. You can send logs to one or both supported destinations simultaneously.",
        ),
    ] = None
    max_aggregation_interval: Annotated[
        float,
        Field(
            alias="maxAggregationInterval",
            description="**Maximum Aggregation Interval** *(Required)*\n\nThe maximum interval in seconds for aggregating flow log records before they are captured and delivered to the destination. This value must be 60 for Transit Gateway Flow Logs",
        ),
    ]


class VpcFlowLogsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    custom_fields: Annotated[
        list[NonEmptyString],
        Field(
            alias="customFields",
            description="**Custom Fields** *(Required when defaultFormat is false)*\n\nArray of specific fields to include in flow log records when using custom format. This allows you to capture exactly the network information needed for your use cases.",
        ),
    ]
    default_format: Annotated[
        bool,
        Field(
            alias="defaultFormat",
            description="**Use Default Format** *(Required)*\n\nControls whether to use the AWS default flow log format or a custom format with specific fields. When false, allows customization of logged fields.",
        ),
    ]
    destinations: Annotated[
        list[LogDestinationType],
        Field(
            description="**Log Destinations** *(Required)*\n\nArray of destination services where VPC flow logs should be delivered. You can send logs to one or both supported destinations simultaneously."
        ),
    ]
    destinations_config: Annotated[
        VpcFlowLogsDestinationConfig | None,
        Field(
            alias="destinationsConfig",
            description="**Destination Configuration** *(Optional)*\n\nAdvanced configuration options for flow log destinations, including S3 lifecycle policies and CloudWatch Logs retention settings.",
        ),
    ] = None
    max_aggregation_interval: Annotated[
        float,
        Field(
            alias="maxAggregationInterval",
            description="**Maximum Aggregation Interval** *(Required)*\n\nThe maximum interval in seconds for aggregating flow log records before they are captured and delivered to the destination.",
        ),
    ]
    traffic_type: Annotated[
        TrafficType,
        Field(
            alias="trafficType",
            description="**Traffic Type** *(Required)*\n\nSpecifies the type of network traffic to capture in VPC flow logs. This determines which traffic flows will be recorded and available for analysis.",
        ),
    ]


class VpcTemplatesConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    cidrs: Annotated[list[NonEmptyString] | None, Field(description="(OPTIONAL) A list of IPv4 CIDRs to associate with the VPC.")] = None
    default_security_group_rules_deletion: Annotated[
        bool | None,
        Field(
            alias="defaultSecurityGroupRulesDeletion",
            description="(OPTIONAL) Determine if the all traffic ingress and egress rules are deleted in the default security group of a VPC.",
        ),
    ] = None
    deployment_targets: Annotated[DeploymentTargets, Field(alias="deploymentTargets", description="VPC deployment targets.")]
    dhcp_options: Annotated[
        str | None, Field(alias="dhcpOptions", description="(OPTIONAL) The friendly name of a custom DHCP options set.", min_length=1)
    ] = None
    dns_firewall_rule_groups: Annotated[
        list[VpcDnsFirewallAssociationConfig] | None,
        Field(
            alias="dnsFirewallRuleGroups",
            description="(OPTIONAL) An array of DNS firewall VPC association configurations. Use this property to associate Route 53 resolver DNS firewall rule groups with the VPC.",
        ),
    ] = None
    egress_only_igw: Annotated[
        bool | None,
        Field(
            alias="egressOnlyIgw",
            description="(OPTIONAL) Create an  {@link  https://docs.aws.amazon.com/vpc/latest/userguide/egress-only-internet-gateway.html Egress-only internet gateway (EIGW) }  for the VPC",
        ),
    ] = None
    enable_dns_hostnames: Annotated[bool | None, Field(alias="enableDnsHostnames", description="Enable DNS hostname support for the VPC.")] = None
    enable_dns_support: Annotated[bool | None, Field(alias="enableDnsSupport", description="Enable DNS support for the VPC.")] = None
    gateway_endpoints: Annotated[
        GatewayEndpointConfig | None,
        Field(
            alias="gatewayEndpoints",
            description="(OPTIONAL) An array of gateway endpoints for the VPC. Use this property to define S3 or DynamoDB gateway endpoints for the VPC.",
        ),
    ] = None
    instance_tenancy: Annotated[
        InstanceTenancyType | None,
        Field(alias="instanceTenancy", description="(OPTIONAL) Define instance tenancy for the VPC. The default value is `default`."),
    ] = None
    interface_endpoints: Annotated[
        InterfaceEndpointConfig | None,
        Field(
            alias="interfaceEndpoints",
            description="(OPTIONAL) A list of VPC interface endpoints. Use this property to define VPC interface endpoints for the VPC.",
        ),
    ] = None
    internet_gateway: Annotated[
        bool | None,
        Field(
            alias="internetGateway",
            description="Defines if an  {@link  https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Internet_Gateway.html internet gateway }  should be added to the VPC",
        ),
    ] = None
    ipam_allocations: Annotated[
        list[IpamAllocationConfig] | None, Field(alias="ipamAllocations", description="(OPTIONAL) An array of IPAM allocation configurations.")
    ] = None
    ipv6_cidrs: Annotated[
        list[VpcIpv6Config] | None, Field(alias="ipv6Cidrs", description="(OPTIONAL) An array of IPv6 CIDR block configurations.")
    ] = None
    load_balancers: Annotated[
        LoadBalancersConfig | None,
        Field(
            alias="loadBalancers",
            description="Elastic Load Balancing configuration. Use this property to define Elastic Load Balancers for this VPC.",
        ),
    ] = None
    name: Annotated[
        str,
        Field(
            description="The friendly name of the VPC.\n\nThe value of this property will be utilized as the logical id for this resource. Any references to this object should specify this value.",
            min_length=1,
        ),
    ]
    nat_gateways: Annotated[
        list[NatGatewayConfig] | None,
        Field(
            alias="natGateways",
            description="(OPTIONAL) An array of NAT gateway configurations for the VPC. Use this property to configure the NAT gateways for the VPC.",
        ),
    ] = None
    network_acls: Annotated[
        list[NetworkAclConfig] | None,
        Field(
            alias="networkAcls", description="(OPTIONAL) A list of Network Access Control Lists (ACLs) to deploy for this VPC", validate_default=True
        ),
    ] = None
    query_logs: Annotated[
        list[NonEmptyString] | None, Field(alias="queryLogs", description="(OPTIONAL) A list of DNS query log configuration names.")
    ] = None
    region: Annotated[str, Field(description="The AWS region to deploy the VPCs to")]
    resolver_rules: Annotated[
        list[NonEmptyString] | None, Field(alias="resolverRules", description="(OPTIONAL) A list of Route 53 resolver rule names.")
    ] = None
    route_tables: Annotated[
        list[RouteTableConfig] | None,
        Field(
            alias="routeTables",
            description="(OPTIONAL) An array of route table configurations for the VPC. Use this property to configure the route tables for the VPC.",
        ),
    ] = None
    security_groups: Annotated[
        list[SecurityGroupConfig] | None,
        Field(alias="securityGroups", description="(OPTIONAL) A list of Security Groups to deploy for this VPC", validate_default=True),
    ] = None
    subnets: Annotated[
        list[SubnetConfig] | None,
        Field(description="(OPTIONAL) An array of subnet configurations for the VPC. Use this property to configure the subnets for the VPC."),
    ] = None
    tags: Annotated[list[Tag] | None, Field(description="(OPTIONAL) A list of tags to apply to this VPC", validate_default=True)] = None
    target_groups: Annotated[
        list[TargetGroupItem] | None,
        Field(alias="targetGroups", description="Target group configuration. Use this property to define target groups for this VPC."),
    ] = None
    transit_gateway_attachments: Annotated[
        list[TransitGatewayAttachmentConfig] | None,
        Field(
            alias="transitGatewayAttachments",
            description="(OPTIONAL) An array of Transit Gateway attachment configurations. Use this property to configure the Transit Gateway attachments for the VPC.",
        ),
    ] = None
    use_central_endpoints: Annotated[
        bool | None,
        Field(
            alias="useCentralEndpoints",
            description="(OPTIONAL) When set to true, this VPC will be configured to utilize centralized endpoints. This includes having the Route 53 Private Hosted Zone associated with this VPC. Centralized endpoints are configured per region, and can span to spoke accounts",
        ),
    ] = False
    virtual_private_gateway: Annotated[
        VirtualPrivateGatewayConfig | None,
        Field(
            alias="virtualPrivateGateway",
            description="(OPTIONAL) Virtual Private Gateway configuration. Use this property to configure a Virtual Private Gateway for the VPC.",
            validate_default=True,
        ),
    ] = None
    vpc_flow_logs: Annotated[
        VpcFlowLogsConfig | None,
        Field(alias="vpcFlowLogs", description="VPC flog log configuration. Use this property to define a VPC-specific VPC flow logs configuration."),
    ] = None


class NfwFirewallPolicyConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    description: Annotated[str | None, Field(description="(OPTIONAL) A description for the policy.", min_length=1)] = None
    firewall_policy: Annotated[
        NfwFirewallPolicyPolicyConfig,
        Field(alias="firewallPolicy", description="Use this property to define specific behaviors and rule groups to associate with the policy."),
    ]
    name: Annotated[str, Field(description="A friendly name for the policy.", min_length=1)]
    regions: Annotated[list[str], Field(description="The regions to deploy the policy to.")]
    share_targets: Annotated[
        ShareTargets | None, Field(alias="shareTargets", description="(OPTIONAL) Resource Access Manager (RAM) share targets.")
    ] = None
    tags: Annotated[list[Tag] | None, Field(description="(OPTIONAL) An array of tags for the policy.")] = None


class NfwRuleGroupRuleConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    rule_variables: Annotated[
        NfwRuleVariableConfig | None, Field(alias="ruleVariables", description="A Network Firewall rule variable configuration.")
    ] = None
    rules_source: Annotated[NfwRuleSourceConfig, Field(alias="rulesSource", description="A Network Firewall rule source configuration.")]
    stateful_rule_options: Annotated[
        NfwStatefulRuleOptionsType | None, Field(alias="statefulRuleOptions", description="A stateful rule option for the rule group.")
    ] = None


class TransitGatewayConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    account: Annotated[str, Field(description="The friendly name of the account to deploy the Transit Gateway.", min_length=1)]
    asn: Annotated[float, Field(description="A Border Gateway Protocol (BGP) Autonomous System Number (ASN).")]
    auto_accept_sharing_attachments: Annotated[
        EnableDisable,
        Field(alias="autoAcceptSharingAttachments", description="Enable this option to automatically accept cross-account attachments."),
    ]
    default_route_table_association: Annotated[
        EnableDisable, Field(alias="defaultRouteTableAssociation", description="Configure default route table association.")
    ]
    default_route_table_propagation: Annotated[
        EnableDisable, Field(alias="defaultRouteTablePropagation", description="Configure default route table propagation.")
    ]
    dns_support: Annotated[EnableDisable, Field(alias="dnsSupport", description="Configure DNS support between VPCs.")]
    multicast_support: Annotated[
        EnableDisable | None,
        Field(alias="multicastSupport", description="(OPTIONAL) Enable this option to turn on multicast on the Transit Gateway."),
    ] = None
    name: Annotated[str, Field(description="A friendly name for the Transit Gateway.", min_length=1)]
    region: Annotated[str, Field(description="The region name to deploy the Transit Gateway.")]
    route_tables: Annotated[
        list[TransitGatewayRouteTableConfig], Field(alias="routeTables", description="An array of Transit Gateway route table configuration objects.")
    ]
    security_group_referencing_support: Annotated[
        EnableDisable | None,
        Field(alias="securityGroupReferencingSupport", description="(OPTIONAL) Enable security group referencing support for the Transit Gateway."),
    ] = None
    share_targets: Annotated[
        ShareTargets | None, Field(alias="shareTargets", description="(OPTIONAL) Resource Access Manager (RAM) share targets.")
    ] = None
    tags: Annotated[list[Tag] | None, Field(description="(OPTIONAL) An array of tag objects for the Transit Gateway.")] = None
    transit_gateway_cidr_blocks: Annotated[
        list[NonEmptyString] | None, Field(alias="transitGatewayCidrBlocks", description="(OPTIONAL) A list of transit gateway IPv4 CIDR blocks.")
    ] = None
    transit_gateway_flow_logs: Annotated[
        TransitGatewayFlowLogsConfig | None, Field(alias="transitGatewayFlowLogs", description="(OPTIONAL) Transit Gateway flow logs configuration.")
    ] = None
    transit_gateway_ipv6_cidr_blocks: Annotated[
        list[NonEmptyString] | None, Field(alias="transitGatewayIpv6CidrBlocks", description="(OPTIONAL) A list of transit gateway IPv6 CIDR blocks.")
    ] = None
    vpn_ecmp_support: Annotated[
        EnableDisable, Field(alias="vpnEcmpSupport", description="Equal Cost Multipath (ECMP) routing support between VPN tunnels.")
    ]


class VpcConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    account: Annotated[str, Field(description="The logical name of the account to deploy the VPC to", min_length=1)]
    cidrs: Annotated[list[NonEmptyString] | None, Field(description="(OPTIONAL) A list of IPv4 CIDRs to associate with the VPC.")] = None
    default_security_group_rules_deletion: Annotated[
        bool | None,
        Field(
            alias="defaultSecurityGroupRulesDeletion",
            description="(OPTIONAL) Determine if the all traffic ingress and egress rules are deleted in the default security group of a VPC.",
        ),
    ] = None
    dhcp_options: Annotated[
        str | None, Field(alias="dhcpOptions", description="(OPTIONAL) The friendly name of a custom DHCP options set.", min_length=1)
    ] = None
    dns_firewall_rule_groups: Annotated[
        list[VpcDnsFirewallAssociationConfig] | None,
        Field(
            alias="dnsFirewallRuleGroups",
            description="(OPTIONAL) An array of DNS firewall VPC association configurations. Use this property to associate Route 53 resolver DNS firewall rule groups with the VPC.",
        ),
    ] = None
    egress_only_igw: Annotated[
        bool | None,
        Field(
            alias="egressOnlyIgw",
            description="(OPTIONAL) Create an  {@link  https://docs.aws.amazon.com/vpc/latest/userguide/egress-only-internet-gateway.html Egress-only internet gateway (EIGW) }  for the VPC",
        ),
    ] = None
    enable_dns_hostnames: Annotated[bool | None, Field(alias="enableDnsHostnames", description="Enable DNS hostname support for the VPC.")] = None
    enable_dns_support: Annotated[bool | None, Field(alias="enableDnsSupport", description="Enable DNS support for the VPC.")] = None
    gateway_endpoints: Annotated[
        GatewayEndpointConfig | None,
        Field(
            alias="gatewayEndpoints",
            description="(OPTIONAL) An array of gateway endpoints for the VPC. Use this property to define S3 or DynamoDB gateway endpoints for the VPC.",
        ),
    ] = None
    instance_tenancy: Annotated[
        InstanceTenancyType | None,
        Field(alias="instanceTenancy", description="(OPTIONAL) Define instance tenancy for the VPC. The default value is `default`."),
    ] = None
    interface_endpoints: Annotated[
        InterfaceEndpointConfig | None,
        Field(
            alias="interfaceEndpoints",
            description="(OPTIONAL) A list of VPC interface endpoints. Use this property to define VPC interface endpoints for the VPC.",
        ),
    ] = None
    internet_gateway: Annotated[
        bool | None,
        Field(
            alias="internetGateway",
            description="Defines if an  {@link  https://docs.aws.amazon.com/vpc/latest/userguide/VPC_Internet_Gateway.html internet gateway }  should be added to the VPC",
        ),
    ] = None
    ipam_allocations: Annotated[
        list[IpamAllocationConfig] | None, Field(alias="ipamAllocations", description="(OPTIONAL) An array of IPAM allocation configurations.")
    ] = None
    ipv6_cidrs: Annotated[
        list[VpcIpv6Config] | None, Field(alias="ipv6Cidrs", description="(OPTIONAL) An array of IPv6 CIDR block configurations.")
    ] = None
    load_balancers: Annotated[
        LoadBalancersConfig | None,
        Field(
            alias="loadBalancers",
            description="Elastic Load Balancing configuration. Use this property to define Elastic Load Balancers for this VPC.",
        ),
    ] = None
    name: Annotated[
        str,
        Field(
            description="The friendly name of the VPC.\n\nThe value of this property will be utilized as the logical id for this resource. Any references to this object should specify this value.",
            min_length=1,
        ),
    ]
    nat_gateways: Annotated[
        list[NatGatewayConfig] | None,
        Field(
            alias="natGateways",
            description="(OPTIONAL) An array of NAT gateway configurations for the VPC. Use this property to configure the NAT gateways for the VPC.",
        ),
    ] = None
    network_acls: Annotated[
        list[NetworkAclConfig] | None,
        Field(
            alias="networkAcls", description="(OPTIONAL) A list of Network Access Control Lists (ACLs) to deploy for this VPC", validate_default=True
        ),
    ] = None
    outposts: Annotated[
        list[OutpostsConfig] | None,
        Field(
            description="(OPTIONAL) An array of Local Gateway Route table configurations. Use this configuration to associate Outposts Local Gateway Route tables with the VPC."
        ),
    ] = None
    query_logs: Annotated[
        list[NonEmptyString] | None, Field(alias="queryLogs", description="(OPTIONAL) A list of DNS query log configuration names.")
    ] = None
    region: Annotated[str, Field(description="The AWS region to deploy the VPC to")]
    resolver_rules: Annotated[
        list[NonEmptyString] | None, Field(alias="resolverRules", description="(OPTIONAL) A list of Route 53 resolver rule names.")
    ] = None
    route_tables: Annotated[
        list[RouteTableConfig] | None,
        Field(
            alias="routeTables",
            description="(OPTIONAL) An array of route table configurations for the VPC. Use this property to configure the route tables for the VPC.",
        ),
    ] = None
    security_groups: Annotated[
        list[SecurityGroupConfig] | None,
        Field(alias="securityGroups", description="(OPTIONAL) A list of Security Groups to deploy for this VPC", validate_default=True),
    ] = None
    subnets: Annotated[
        list[SubnetConfig] | None,
        Field(description="(OPTIONAL) An array of subnet configurations for the VPC. Use this property to configure the subnets for the VPC."),
    ] = None
    tags: Annotated[list[Tag] | None, Field(description="(OPTIONAL) A list of tags to apply to this VPC", validate_default=True)] = None
    target_groups: Annotated[
        list[TargetGroupItem] | None,
        Field(alias="targetGroups", description="Target group configuration. Use this property to define target groups for this VPC."),
    ] = None
    transit_gateway_attachments: Annotated[
        list[TransitGatewayAttachmentConfig] | None,
        Field(
            alias="transitGatewayAttachments",
            description="(OPTIONAL) An array of Transit Gateway attachment configurations. Use this property to configure the Transit Gateway attachments for the VPC.",
        ),
    ] = None
    use_central_endpoints: Annotated[
        bool | None,
        Field(
            alias="useCentralEndpoints",
            description="(OPTIONAL) When set to true, this VPC will be configured to utilize centralized endpoints. This includes having the Route 53 Private Hosted Zone associated with this VPC. Centralized endpoints are configured per region, and can span to spoke accounts.\n\nNOTE: The AWS partition and regions must support the creation of Route 53 private hosted zones and DNS alias records for AWS VPC Endpoint resource types or the pipeline will fail. Ensure your partition and regions will support useCentralEndpoints before enabling it.",
        ),
    ] = False
    virtual_private_gateway: Annotated[
        VirtualPrivateGatewayConfig | None,
        Field(
            alias="virtualPrivateGateway",
            description="(OPTIONAL) Virtual Private Gateway configuration. Use this property to configure a Virtual Private Gateway for the VPC.",
            validate_default=True,
        ),
    ] = None
    vpc_flow_logs: Annotated[
        VpcFlowLogsConfig | None,
        Field(alias="vpcFlowLogs", description="VPC flog log configuration. Use this property to define a VPC-specific VPC flow logs configuration."),
    ] = None
    vpc_route53_resolver: Annotated[
        VpcResolverConfig | None, Field(alias="vpcRoute53Resolver", description="A Route 53 resolver configuration local to the VPC.")
    ] = None


class NfwRuleGroupConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    capacity: Annotated[float, Field(description="The capacity of the rule group.")]
    description: Annotated[str | None, Field(description="(OPTIONAL) A description for the rule group.", min_length=1)] = None
    name: Annotated[str, Field(description="A friendly name for the rule group.", min_length=1)]
    regions: Annotated[list[str], Field(description="The regions to deploy the rule group to.")]
    rule_group: Annotated[
        NfwRuleGroupRuleConfig | None, Field(alias="ruleGroup", description="(OPTIONAL) A Network Firewall rule configuration.")
    ] = None
    share_targets: Annotated[
        ShareTargets | None, Field(alias="shareTargets", description="(OPTIONAL) Resource Access Manager (RAM) share targets.")
    ] = None
    tags: Annotated[list[Tag] | None, Field(description="(OPTIONAL) An array of tags for the rule group.")] = None
    type: Annotated[NfwRuleType, Field(description="The type of rules in the rule group.")]


class NfwConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    firewalls: Annotated[list[NfwFirewallConfig], Field(description="An array of Network Firewall firewall configurations.")]
    policies: Annotated[list[NfwFirewallPolicyConfig], Field(description="An array of Network Firewall policy configurations.")]
    rules: Annotated[list[NfwRuleGroupConfig], Field(description="An array of Network Firewall rule group configurations.")]


class CentralNetworkServicesConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    delegated_admin_account: Annotated[
        str,
        Field(
            alias="delegatedAdminAccount",
            description="The friendly name of the delegated administrator account for network services. Resources configured under `centralNetworkServices` will be created in this account.",
            min_length=1,
        ),
    ]
    gateway_load_balancers: Annotated[
        list[GwlbConfig] | None, Field(alias="gatewayLoadBalancers", description="An array of Gateway Load Balancer configurations.")
    ] = None
    ipams: Annotated[list[IpamConfig] | None, Field(description="An array of IPAM configurations.")] = None
    network_firewall: Annotated[NfwConfig | None, Field(alias="networkFirewall", description="A Network Firewall configuration.")] = None
    route53_resolver: Annotated[ResolverConfig | None, Field(alias="route53Resolver", description="A Route 53 resolver configuration.")] = None


class NetworkConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    account_vpc_endpoint_ids: Annotated[
        dict[str, list[NonEmptyString]] | None,
        Field(
            alias="accountVpcEndpointIds",
            description="A map between account Id and all the VPC Endpoint IDs in the account.\n\nCurrently, the dynamic values will only be loaded in FinalizeStack for SCP finalization. Only the account VPC Endpoints referred by ACCEL_LOOKUP in SCPs will be loaded.",
        ),
    ] = None
    account_vpc_ids: Annotated[
        dict[str, list[NonEmptyString]] | None,
        Field(
            alias="accountVpcIds",
            description="A map between account Id and all the VPC IDs in the account.\n\nCurrently, the dynamic values will only be loaded in FinalizeStack for SCP finalization. Only the account VPCs referred in SCPs by ACCEL_LOOKUP will be loaded.",
        ),
    ] = None
    central_network_services: Annotated[
        CentralNetworkServicesConfig | None, Field(alias="centralNetworkServices", description="An optional Central Network services configuration.")
    ] = None
    certificates: Annotated[list[CertificateConfig] | None, Field(description="Certificate manager configuration")] = None
    customer_gateways: Annotated[
        list[CustomerGatewayConfig] | None, Field(alias="customerGateways", description="An array of Customer Gateway configurations.")
    ] = None
    default_vpc: Annotated[DefaultVpcsConfig, Field(alias="defaultVpc", description="A default VPC configuration.")]
    dhcp_options: Annotated[
        list[DhcpOptsConfig] | None, Field(alias="dhcpOptions", description="An optional list of DHCP options set configurations.")
    ] = None
    direct_connect_gateways: Annotated[
        list[DxGatewayConfig] | None, Field(alias="directConnectGateways", description="An optional array of Direct Connect Gateway configurations.")
    ] = None
    elb_account_ids: Annotated[list[ElbAccountIdsConfig] | None, Field(alias="elbAccountIds", description="An optional ELB root account ID")] = None
    endpoint_policies: Annotated[
        list[EndpointPolicyConfig], Field(alias="endpointPolicies", description="A list of VPC configurations. An array of VPC endpoint policies.")
    ]
    firewall_manager_service: Annotated[
        FirewallManagerServiceConfig | None, Field(alias="firewallManagerService", description="Firewall manager service configuration")
    ] = None
    home_region: Annotated[str | None, Field(alias="homeRegion", description="Accelerator home region name.")] = None
    prefix_lists: Annotated[
        list[PrefixListConfig] | None, Field(alias="prefixLists", description="An optional list of prefix list set configurations.")
    ] = None
    transit_gateway_connects: Annotated[
        list[TransitGatewayConnectConfig] | None,
        Field(alias="transitGatewayConnects", description="An array of Transit Gateway Connect configurations."),
    ] = None
    transit_gateway_peering: Annotated[
        list[TransitGatewayPeeringConfig] | None, Field(alias="transitGatewayPeering", description="Transit Gateway peering configuration.")
    ] = None
    transit_gateways: Annotated[list[TransitGatewayConfig], Field(alias="transitGateways", description="An array of Transit Gateway configurations.")]
    vpc_flow_logs: Annotated[VpcFlowLogsConfig | None, Field(alias="vpcFlowLogs", description="A VPC flow logs configuration.")] = None
    vpc_peering: Annotated[list[VpcPeeringConfig] | None, Field(alias="vpcPeering", description="An optional list of VPC peering configurations")] = (
        None
    )
    vpc_templates: Annotated[
        list[VpcTemplatesConfig] | None, Field(alias="vpcTemplates", description="An optional list of VPC template configurations")
    ] = None
    vpcs: Annotated[list[VpcConfig], Field(description="An array of VPC configurations.")]


type Model = NetworkConfig

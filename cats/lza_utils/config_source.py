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

"""Where the LZA configuration the tests read comes from.

The tests prove controls against the configuration LZA actually deployed, never against the
Universal Configuration template. UC's ``modules/`` tree is not deployable as it stands: UC's
release scripts fill ``replacements-config.yaml`` from environment variables, add workload
accounts and expand ``network-config.yaml`` into per-region ``include/`` fragments before the zip
reaches the installer bucket. That zip is the source of truth, and this module fetches it.

Resolution order:

1. ``LZA_LOCAL_CONFIG_DIR``: a directory holding an unpacked configuration, whatever its origin.
2. The deployed zip in the installer config bucket, read through the deploy role of the account
   that owns it and unpacked once per object version into ``.pytest_cache/lza-config/``.
   ``LZA_CONFIG_BUCKET``, ``LZA_CONFIG_KEY`` and ``LZA_CONFIG_ACCOUNT`` (the account's key under
   ``accounts_under_test`` in cats.yaml) name it; when none is set and the deployment is the CodePipeline installer, the
   bucket is derived from cats.yaml: ``aws-accelerator-config-<management account>-<aws_region>``,
   key ``zipped/aws-accelerator-config.zip``, owned by the account tagged ``management``.

The container installer's bucket is a resource of the InstallerContainerStack whose name depends
on the AcceleratorQualifier, so a container deployment sets the three variables (the CI configs
do). With no source at all the error names both options; there is no built-in fallback.
"""

from __future__ import annotations

import io
import os
import shutil
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING

import boto3
from cats.config import Settings
from cats.exceptions import CatsConfigError

if TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client

LOCAL_CONFIG_DIR_VARIABLE = "LZA_LOCAL_CONFIG_DIR"
CONFIG_BUCKET_VARIABLE = "LZA_CONFIG_BUCKET"
CONFIG_KEY_VARIABLE = "LZA_CONFIG_KEY"
CONFIG_ACCOUNT_VARIABLE = "LZA_CONFIG_ACCOUNT"

MANAGEMENT_TAG = "management"
CONTAINER_DEPLOYMENT_REQUIREMENT = "container-deployment"
CODEPIPELINE_CONFIG_KEY = "zipped/aws-accelerator-config.zip"

_CACHE_ROOT = Path(".pytest_cache/lza-config")


class DeployedConfigLocation:
    """The S3 object holding the deployed configuration zip and the account that owns the bucket."""

    def __init__(self, account_key: str, bucket: str, key: str) -> None:
        self.account_key = account_key
        self.bucket = bucket
        self.key = key

    def __repr__(self) -> str:
        return f"s3://{self.bucket}/{self.key} (via {self.account_key})"


def deployed_config_location() -> DeployedConfigLocation:
    """Where the deployed zip is, from the ``LZA_CONFIG_*`` variables or derived from cats.yaml."""
    bucket = os.environ.get(CONFIG_BUCKET_VARIABLE)
    key = os.environ.get(CONFIG_KEY_VARIABLE)
    account = os.environ.get(CONFIG_ACCOUNT_VARIABLE)
    if bucket or key or account:
        missing = [
            name for name, value in ((CONFIG_BUCKET_VARIABLE, bucket), (CONFIG_KEY_VARIABLE, key), (CONFIG_ACCOUNT_VARIABLE, account)) if not value
        ]
        if missing:
            raise CatsConfigError(f"{', '.join(missing)} must be set alongside the other LZA_CONFIG_* variables")
        assert bucket is not None
        assert key is not None
        assert account is not None
        return DeployedConfigLocation(account, bucket, key)

    settings = Settings()
    if CONTAINER_DEPLOYMENT_REQUIREMENT in settings.test_selection.provides:
        variables = f"{CONFIG_ACCOUNT_VARIABLE}, {CONFIG_BUCKET_VARIABLE} and {CONFIG_KEY_VARIABLE}, or {LOCAL_CONFIG_DIR_VARIABLE}"
        raise CatsConfigError(
            f"A container deployment's config bucket belongs to the InstallerContainerStack and cannot be derived; set {variables}."
        )
    management = sorted(name for name, account in settings.accounts_under_test.items() if MANAGEMENT_TAG in account.tags)
    if len(management) != 1:
        raise CatsConfigError(f"Exactly one account under test must be tagged '{MANAGEMENT_TAG}' to derive the config bucket, found {management}")
    management_account_id = settings.accounts_under_test[management[0]].account_id
    return DeployedConfigLocation(
        management[0],
        f"aws-accelerator-config-{management_account_id}-{settings.cats_deployment_settings.aws_region}",
        CODEPIPELINE_CONFIG_KEY,
    )


def config_bucket_client(location: DeployedConfigLocation) -> S3Client:
    """An S3 client in the bucket owner's account, through the configured deploy role."""
    settings = Settings()
    deploy_role_name = settings.cats_deployment_settings.deploy_role_name
    if deploy_role_name is None:
        raise CatsConfigError("cats_deployment_settings.deploy_role_name must be set to read the deployed configuration")
    account_id = settings.accounts_under_test[location.account_key].account_id
    partition = settings.cats_deployment_settings.partition
    credentials = boto3.client("sts").assume_role(
        RoleArn=f"arn:{partition}:iam::{account_id}:role/{deploy_role_name}",
        RoleSessionName="cats-lza-config",
    )["Credentials"]
    return boto3.Session(
        aws_access_key_id=credentials["AccessKeyId"],
        aws_secret_access_key=credentials["SecretAccessKey"],
        aws_session_token=credentials["SessionToken"],
    ).client("s3")


def unpack_config_zip(archive_bytes: bytes, destination: Path) -> list[str]:
    """Unpack a configuration zip into ``destination``, skipping macOS metadata. Returns the member names.

    A member whose path would land outside ``destination`` (``../`` or absolute) is refused
    before anything is written, as the ``!include`` loader refuses paths outside the config dir.
    """
    archive = zipfile.ZipFile(io.BytesIO(archive_bytes))
    members = [name for name in archive.namelist() if not name.startswith("__MACOSX/")]
    root = destination.resolve()
    escaping = [name for name in members if not (root / name).resolve().is_relative_to(root)]
    if escaping:
        raise CatsConfigError(f"Configuration zip has members outside the archive root: {escaping}")
    destination.mkdir(parents=True, exist_ok=True)
    archive.extractall(destination, members)
    return members


def pull_deployed_config(location: DeployedConfigLocation, cache_root: Path = _CACHE_ROOT) -> Path:
    """The unpacked deployed configuration, fetched once per object version.

    The S3 ETag names the cache directory, so a redeploy is picked up on the next run and every
    xdist worker that sees an existing directory reads it instead of downloading again. The
    directory is written under a temporary name and renamed into place so a worker never reads a
    half-unpacked tree.
    """
    client = config_bucket_client(location)
    etag = client.head_object(Bucket=location.bucket, Key=location.key)["ETag"].strip('"')
    target = cache_root / location.bucket / etag
    if target.is_dir():
        return target
    staging = target.with_name(f"{etag}.{os.getpid()}.partial")
    unpack_config_zip(client.get_object(Bucket=location.bucket, Key=location.key)["Body"].read(), staging)
    try:
        staging.rename(target)
    except OSError:
        if not target.is_dir():
            raise
        shutil.rmtree(staging, ignore_errors=True)  # another worker won the race; drop our copy
    return target


def lza_config_dir() -> Path:
    """Directory containing the LZA configuration files the tests read (module docstring for the order)."""
    local = os.environ.get(LOCAL_CONFIG_DIR_VARIABLE)
    if local:
        path = Path(local)
        if not path.is_dir():
            raise CatsConfigError(f"{LOCAL_CONFIG_DIR_VARIABLE}={local} is not a directory")
        return path
    return pull_deployed_config(deployed_config_location())

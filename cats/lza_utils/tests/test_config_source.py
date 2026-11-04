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

"""Tests for lza_utils.config_source: where the deployed configuration comes from."""

from __future__ import annotations

import io
import zipfile
from typing import TYPE_CHECKING
from unittest.mock import Mock

import pytest
from botocore.exceptions import ClientError
from cats.config import Settings
from cats.exceptions import CatsConfigError

from lza_utils import config_source
from lza_utils.config_source import (
    CODEPIPELINE_CONFIG_KEY,
    CONFIG_ACCOUNT_VARIABLE,
    CONFIG_BUCKET_VARIABLE,
    CONFIG_KEY_VARIABLE,
    LOCAL_CONFIG_DIR_VARIABLE,
    MANAGEMENT_TAG,
    DeployedConfigLocation,
    deployed_config_location,
    lza_config_dir,
    pull_deployed_config,
    unpack_config_zip,
)

if TYPE_CHECKING:
    from pathlib import Path


def _zip_bytes(files: dict[str, str]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    return buffer.getvalue()


def test_local_config_dir_variable_wins(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv(LOCAL_CONFIG_DIR_VARIABLE, str(tmp_path))
    monkeypatch.setenv(CONFIG_BUCKET_VARIABLE, "ignored")

    assert lza_config_dir() == tmp_path


def test_local_config_dir_must_exist(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv(LOCAL_CONFIG_DIR_VARIABLE, str(tmp_path / "missing"))

    with pytest.raises(CatsConfigError, match="is not a directory"):
        lza_config_dir()


def test_explicit_location_from_variables(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(CONFIG_ACCOUNT_VARIABLE, "LzaDeployment")
    monkeypatch.setenv(CONFIG_BUCKET_VARIABLE, "lza1-config-111111111111-us-east-1")
    monkeypatch.setenv(CONFIG_KEY_VARIABLE, "lza/aws-accelerator-config.zip")

    location = deployed_config_location()

    assert (location.account_key, location.bucket, location.key) == (
        "LzaDeployment",
        "lza1-config-111111111111-us-east-1",
        "lza/aws-accelerator-config.zip",
    )


def test_partial_variables_are_an_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(CONFIG_ACCOUNT_VARIABLE, raising=False)
    monkeypatch.delenv(CONFIG_KEY_VARIABLE, raising=False)
    monkeypatch.setenv(CONFIG_BUCKET_VARIABLE, "b")

    with pytest.raises(CatsConfigError, match=f"{CONFIG_KEY_VARIABLE}, {CONFIG_ACCOUNT_VARIABLE} must be set"):
        deployed_config_location()


def test_codepipeline_location_is_derived_from_the_management_account(monkeypatch: pytest.MonkeyPatch) -> None:
    """The loaded cats.yaml is a standard deployment, so the bucket follows LZA's naming."""
    for variable in (CONFIG_ACCOUNT_VARIABLE, CONFIG_BUCKET_VARIABLE, CONFIG_KEY_VARIABLE):
        monkeypatch.delenv(variable, raising=False)
    settings = Settings()
    assert "container-deployment" not in settings.test_selection.provides, "test precondition: the loaded cats.yaml is a standard deployment"
    (management,) = [name for name, account in settings.accounts_under_test.items() if MANAGEMENT_TAG in account.tags]
    management_id = settings.accounts_under_test[management].account_id

    location = deployed_config_location()

    assert (location.account_key, location.bucket, location.key) == (
        management,
        f"aws-accelerator-config-{management_id}-{settings.cats_deployment_settings.aws_region}",
        CODEPIPELINE_CONFIG_KEY,
    )


def test_container_deployment_cannot_derive_the_bucket(monkeypatch: pytest.MonkeyPatch) -> None:
    for variable in (CONFIG_ACCOUNT_VARIABLE, CONFIG_BUCKET_VARIABLE, CONFIG_KEY_VARIABLE):
        monkeypatch.delenv(variable, raising=False)
    settings = Settings()
    container = settings.model_copy(update={"test_selection": settings.test_selection.model_copy(update={"provides": ["container-deployment"]})})
    monkeypatch.setattr(config_source, "Settings", lambda: container)

    with pytest.raises(CatsConfigError, match="InstallerContainerStack"):
        deployed_config_location()


def test_unpack_config_zip_skips_macos_metadata(tmp_path: Path) -> None:
    members = unpack_config_zip(_zip_bytes({"global-config.yaml": "a: 1\n", "__MACOSX/._global-config.yaml": "junk"}), tmp_path)

    assert members == ["global-config.yaml"]
    assert (tmp_path / "global-config.yaml").read_text() == "a: 1\n"
    assert not (tmp_path / "__MACOSX").exists()


def test_unpack_config_zip_refuses_members_outside_the_destination(tmp_path: Path) -> None:
    archive = _zip_bytes({"global-config.yaml": "a: 1\n", "../escape.yaml": "x: 1\n"})

    with pytest.raises(CatsConfigError, match=r"outside the archive root: \['\.\./escape\.yaml'\]"):
        unpack_config_zip(archive, tmp_path / "out")

    assert not (tmp_path / "out").exists()
    assert not (tmp_path / "escape.yaml").exists()


def test_pull_deployed_config_removes_its_staging_dir_when_another_worker_won(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # arrange - the target appears between the is_dir check and the rename, as a faster worker would make it
    client = Mock()
    client.head_object.return_value = {"ETag": '"abc123"'}
    client.get_object.return_value = {"Body": io.BytesIO(_zip_bytes({"global-config.yaml": "a: 1\n"}))}
    monkeypatch.setattr(config_source, "config_bucket_client", lambda location: client)
    target = tmp_path / "bucket" / "abc123"
    original_unpack = config_source.unpack_config_zip

    def unpack_then_lose_race(archive_bytes: bytes, destination: Path) -> list[str]:
        members = original_unpack(archive_bytes, destination)
        target.mkdir(parents=True)
        (target / "global-config.yaml").write_text("a: 1\n")
        return members

    monkeypatch.setattr(config_source, "unpack_config_zip", unpack_then_lose_race)

    # act
    result = pull_deployed_config(DeployedConfigLocation("Management", "bucket", "k"), cache_root=tmp_path)

    # assert
    assert result == target
    assert sorted(p.name for p in (tmp_path / "bucket").iterdir()) == ["abc123"]


def test_pull_deployed_config_names_the_prefix_override_when_the_derived_bucket_is_missing(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """A derived bucket that does not exist is what a non-default AcceleratorPrefix looks like; the error says how to point at the real one."""
    # arrange
    client = Mock()
    client.head_object.side_effect = ClientError({"Error": {"Code": "NoSuchBucket", "Message": "x"}}, "HeadObject")
    monkeypatch.setattr(config_source, "config_bucket_client", lambda location: client)
    location = DeployedConfigLocation("Management", "aws-accelerator-config-111111111111-us-east-1", CODEPIPELINE_CONFIG_KEY)

    # act / assert
    with pytest.raises(CatsConfigError, match=r"non-default AcceleratorPrefix.*LZA_CONFIG_ACCOUNT, LZA_CONFIG_BUCKET and LZA_CONFIG_KEY"):
        pull_deployed_config(location, cache_root=tmp_path)


def test_pull_deployed_config_caches_by_etag(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # arrange
    client = Mock()
    client.head_object.return_value = {"ETag": '"abc123"'}
    client.get_object.return_value = {"Body": io.BytesIO(_zip_bytes({"global-config.yaml": "a: 1\n"}))}
    monkeypatch.setattr(config_source, "config_bucket_client", lambda location: client)
    location = DeployedConfigLocation("Management", "bucket", "zipped/aws-accelerator-config.zip")

    # act
    first = pull_deployed_config(location, cache_root=tmp_path)
    second = pull_deployed_config(location, cache_root=tmp_path)

    # assert - one download, same directory, named by the object version
    assert first == second == tmp_path / "bucket" / "abc123"
    assert (first / "global-config.yaml").read_text() == "a: 1\n"
    assert client.get_object.call_count == 1
    assert client.head_object.call_count == 2

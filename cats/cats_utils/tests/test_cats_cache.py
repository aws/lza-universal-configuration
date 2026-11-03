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

"""Unit tests for cats_utils.cats_cache pagination: each helper is fed two stubbed pages and must return the union."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import botocore.session
import pytest
from botocore.stub import Stubber

from cats_utils import cats_cache
from cats_utils.cats_cache import (
    get_backup_vault_names,
    get_guardduty_detector,
    get_guardduty_detector_id,
    get_organization_root_id,
    get_s3_buckets,
)

if TYPE_CHECKING:
    from cats_types import CatsAccountProtocol

_REGION = "us-east-1"


class _FakeSession:
    """Stands in for boto3.Session: hands back one pre-built, stubbed client."""

    def __init__(self, client: Any) -> None:  # noqa: ANN401
        self._client = client

    def client(self, service_name: str, **_kwargs: Any) -> Any:  # noqa: ANN401
        assert service_name == self._client.meta.service_model.service_name
        return self._client


class _FakeAccount:
    """The three attributes cats_cache reads from a CatsAccountProtocol."""

    def __init__(self, client: Any) -> None:  # noqa: ANN401
        self.name = "Fake_account"
        self.account_id = "111111111111"
        self.session = _FakeSession(client)


def _stubbed_account(service_name: str) -> tuple[CatsAccountProtocol, Stubber]:
    """A fake account whose session returns a stubbed ``service_name`` client; the Stubber is not yet activated."""
    client = botocore.session.get_session().create_client(
        service_name,
        region_name=_REGION,
        aws_access_key_id="testing",
        aws_secret_access_key="testing",  # noqa: S106
    )
    return _FakeAccount(client), Stubber(client)  # type: ignore[return-value]


class _DictCache:
    """The two diskcache.Cache methods ``cached()`` uses, backed by a dict so each test starts empty."""

    def __init__(self) -> None:
        self._entries: dict[str, object] = {}

    def get(self, key: str) -> object | None:
        return self._entries.get(key)

    def set(self, key: str, value: object) -> None:
        self._entries[key] = value


@pytest.fixture(autouse=True)
def _isolated_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cats_cache, "_cache", _DictCache())


def test_get_s3_buckets_merges_all_pages() -> None:
    # arrange
    account, stubber = _stubbed_account("s3")
    stubber.add_response("list_buckets", {"Buckets": [{"Name": "bucket-a"}], "ContinuationToken": "page-2"}, {})
    stubber.add_response("list_buckets", {"Buckets": [{"Name": "bucket-b"}]}, {"ContinuationToken": "page-2"})
    expected = ["bucket-a", "bucket-b"]

    # act
    with stubber:
        buckets = get_s3_buckets(account)

    # assert
    assert buckets == expected
    stubber.assert_no_pending_responses()


def test_get_organization_root_id_merges_all_pages() -> None:
    # arrange
    account, stubber = _stubbed_account("organizations")
    stubber.add_response("list_roots", {"Roots": [{"Id": "r-aaaa"}], "NextToken": "page-2"}, {})
    stubber.add_response("list_roots", {"Roots": [{"Id": "r-bbbb"}]}, {"NextToken": "page-2"})

    # act
    with stubber:
        root_id = get_organization_root_id(account)

    # assert
    assert root_id == "r-aaaa"
    stubber.assert_no_pending_responses()


def test_get_backup_vault_names_merges_all_pages() -> None:
    # arrange
    account, stubber = _stubbed_account("backup")
    stubber.add_response("list_backup_vaults", {"BackupVaultList": [{"BackupVaultName": "vault-a"}], "NextToken": "page-2"}, {})
    stubber.add_response("list_backup_vaults", {"BackupVaultList": [{"BackupVaultName": "vault-b"}]}, {"NextToken": "page-2"})
    expected = ["vault-a", "vault-b"]

    # act
    with stubber:
        vaults = get_backup_vault_names(account)

    # assert
    assert vaults == expected
    stubber.assert_no_pending_responses()


def test_get_guardduty_detector_id_merges_all_pages() -> None:
    # arrange
    account, stubber = _stubbed_account("guardduty")
    stubber.add_response("list_detectors", {"DetectorIds": [], "NextToken": "page-2"}, {})
    stubber.add_response("list_detectors", {"DetectorIds": ["detector-1"]}, {"NextToken": "page-2"})

    # act
    with stubber:
        detector_id = get_guardduty_detector_id(account, _REGION)

    # assert
    assert detector_id == "detector-1"
    stubber.assert_no_pending_responses()


def test_get_guardduty_detector_id_fails_when_no_detector() -> None:
    # arrange
    account, stubber = _stubbed_account("guardduty")
    stubber.add_response("list_detectors", {"DetectorIds": []}, {})

    # act & assert
    with stubber, pytest.raises(AssertionError, match="No GuardDuty detector in Fake_account / us-east-1"):
        get_guardduty_detector_id(account, _REGION)


def test_get_guardduty_detector_reuses_cached_detector_id() -> None:
    # arrange
    account, stubber = _stubbed_account("guardduty")
    stubber.add_response("list_detectors", {"DetectorIds": ["detector-1"]}, {})
    stubber.add_response("get_detector", {"ServiceRole": "arn:aws:iam::111111111111:role/gd", "Status": "ENABLED"}, {"DetectorId": "detector-1"})

    # act
    with stubber:
        detector_id = get_guardduty_detector_id(account, _REGION)
        detector = get_guardduty_detector(account, _REGION)

    # assert
    assert detector_id == "detector-1"
    assert detector["Status"] == "ENABLED"
    stubber.assert_no_pending_responses()

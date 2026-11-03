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

"""
CATS - IAM Password Policy Configuration

This test verifies:
- LZA-SEC-IAM-PW-1: Allow users to change password
- LZA-SEC-IAM-PW-2: Hard expiry disabled
- LZA-SEC-IAM-PW-3: Require uppercase characters
- LZA-SEC-IAM-PW-4: Require lowercase characters
- LZA-SEC-IAM-PW-5: Require numbers
- LZA-SEC-IAM-PW-6: Require symbols
- LZA-SEC-IAM-PW-7: Minimum password length of 14
- LZA-SEC-IAM-PW-8: Password reuse prevention of 24
- LZA-SEC-IAM-PW-9: Max password age of 90 days
"""

from __future__ import annotations

import logging

import pytest
from cats import GetAccountFixture, cats
from cats.constants import get_account_fixture_names

from cats_utils.cats_cache import get_password_policy
from cats_utils.evidence import Evidence
from lza_utils.lza_config import lza_config

logger = logging.getLogger(__name__)


@pytest.mark.parametrize("account_fixture_name", get_account_fixture_names())
@cats(standard_name=["LZA-SEC-IAM-PW-1"], test_suite="iam", test_id="pw-1", evidence=Evidence.CONFIGURATION)
def test_password_policy_allow_users_to_change(account_fixture_name: str, get_account_fixture: GetAccountFixture) -> None:
    """Verify password policy allows users to change their own password."""
    account = get_account_fixture(account_fixture_name)
    policy = get_password_policy(account)
    expected = lza_config().security.iam_password_policy.allow_users_to_change_password
    assert policy["AllowUsersToChangePassword"] is expected, (
        f"AllowUsersToChangePassword is {policy['AllowUsersToChangePassword']}, expected {expected} in {account_fixture_name}"
    )


@pytest.mark.parametrize("account_fixture_name", get_account_fixture_names())
@cats(standard_name=["LZA-SEC-IAM-PW-2"], test_suite="iam", test_id="pw-2", evidence=Evidence.CONFIGURATION)
def test_password_policy_hard_expiry(account_fixture_name: str, get_account_fixture: GetAccountFixture) -> None:
    """Verify password policy hard expiry setting."""
    account = get_account_fixture(account_fixture_name)
    policy = get_password_policy(account)
    expected = lza_config().security.iam_password_policy.hard_expiry
    assert policy["HardExpiry"] is expected, f"HardExpiry is {policy['HardExpiry']}, expected {expected} in {account_fixture_name}"


@pytest.mark.parametrize("account_fixture_name", get_account_fixture_names())
@cats(standard_name=["LZA-SEC-IAM-PW-3"], test_suite="iam", test_id="pw-3", evidence=Evidence.CONFIGURATION)
def test_password_policy_require_uppercase(account_fixture_name: str, get_account_fixture: GetAccountFixture) -> None:
    """Verify password policy requires uppercase characters."""
    account = get_account_fixture(account_fixture_name)
    policy = get_password_policy(account)
    expected = lza_config().security.iam_password_policy.require_uppercase_characters
    assert policy["RequireUppercaseCharacters"] is expected, (
        f"RequireUppercaseCharacters is {policy['RequireUppercaseCharacters']}, expected {expected} in {account_fixture_name}"
    )


@pytest.mark.parametrize("account_fixture_name", get_account_fixture_names())
@cats(standard_name=["LZA-SEC-IAM-PW-4"], test_suite="iam", test_id="pw-4", evidence=Evidence.CONFIGURATION)
def test_password_policy_require_lowercase(account_fixture_name: str, get_account_fixture: GetAccountFixture) -> None:
    """Verify password policy requires lowercase characters."""
    account = get_account_fixture(account_fixture_name)
    policy = get_password_policy(account)
    expected = lza_config().security.iam_password_policy.require_lowercase_characters
    assert policy["RequireLowercaseCharacters"] is expected, (
        f"RequireLowercaseCharacters is {policy['RequireLowercaseCharacters']}, expected {expected} in {account_fixture_name}"
    )


@pytest.mark.parametrize("account_fixture_name", get_account_fixture_names())
@cats(standard_name=["LZA-SEC-IAM-PW-5"], test_suite="iam", test_id="pw-5", evidence=Evidence.CONFIGURATION)
def test_password_policy_require_numbers(account_fixture_name: str, get_account_fixture: GetAccountFixture) -> None:
    """Verify password policy requires numbers."""
    account = get_account_fixture(account_fixture_name)
    policy = get_password_policy(account)
    expected = lza_config().security.iam_password_policy.require_numbers
    assert policy["RequireNumbers"] is expected, f"RequireNumbers is {policy['RequireNumbers']}, expected {expected} in {account_fixture_name}"


@pytest.mark.parametrize("account_fixture_name", get_account_fixture_names())
@cats(standard_name=["LZA-SEC-IAM-PW-6"], test_suite="iam", test_id="pw-6", evidence=Evidence.CONFIGURATION)
def test_password_policy_require_symbols(account_fixture_name: str, get_account_fixture: GetAccountFixture) -> None:
    """Verify password policy requires symbols."""
    account = get_account_fixture(account_fixture_name)
    policy = get_password_policy(account)
    expected = lza_config().security.iam_password_policy.require_symbols
    assert policy["RequireSymbols"] is expected, f"RequireSymbols is {policy['RequireSymbols']}, expected {expected} in {account_fixture_name}"


@pytest.mark.parametrize("account_fixture_name", get_account_fixture_names())
@cats(standard_name=["LZA-SEC-IAM-PW-7"], test_suite="iam", test_id="pw-7", evidence=Evidence.CONFIGURATION)
def test_password_policy_minimum_length(account_fixture_name: str, get_account_fixture: GetAccountFixture) -> None:
    """Verify password policy minimum length."""
    account = get_account_fixture(account_fixture_name)
    policy = get_password_policy(account)
    expected = int(lza_config().security.iam_password_policy.minimum_password_length)
    assert policy["MinimumPasswordLength"] == expected, (
        f"MinimumPasswordLength is {policy['MinimumPasswordLength']}, expected {expected} in {account_fixture_name}"
    )


@pytest.mark.parametrize("account_fixture_name", get_account_fixture_names())
@cats(standard_name=["LZA-SEC-IAM-PW-8"], test_suite="iam", test_id="pw-8", evidence=Evidence.CONFIGURATION)
def test_password_policy_reuse_prevention(account_fixture_name: str, get_account_fixture: GetAccountFixture) -> None:
    """Verify password policy reuse prevention count."""
    account = get_account_fixture(account_fixture_name)
    policy = get_password_policy(account)
    expected = int(lza_config().security.iam_password_policy.password_reuse_prevention)
    assert policy["PasswordReusePrevention"] == expected, (
        f"PasswordReusePrevention is {policy['PasswordReusePrevention']}, expected {expected} in {account_fixture_name}"
    )


@pytest.mark.parametrize("account_fixture_name", get_account_fixture_names())
@cats(standard_name=["LZA-SEC-IAM-PW-9"], test_suite="iam", test_id="pw-9", evidence=Evidence.CONFIGURATION)
def test_password_policy_max_age(account_fixture_name: str, get_account_fixture: GetAccountFixture) -> None:
    """Verify password policy max password age."""
    account = get_account_fixture(account_fixture_name)
    policy = get_password_policy(account)
    expected = int(lza_config().security.iam_password_policy.max_password_age)
    assert policy["MaxPasswordAge"] == expected, f"MaxPasswordAge is {policy['MaxPasswordAge']}, expected {expected} in {account_fixture_name}"

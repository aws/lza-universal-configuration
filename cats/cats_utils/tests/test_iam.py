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

from __future__ import annotations

from urllib.parse import quote

import pytest

from cats_utils.iam import trusted_service_principals


def test_trusted_service_principals_from_decoded_document() -> None:
    document = {
        "Version": "2012-10-17",
        "Statement": [
            {"Effect": "Allow", "Principal": {"Service": "ec2.amazonaws.com"}, "Action": "sts:AssumeRole"},
            {"Effect": "Allow", "Principal": {"Service": ["ssm.amazonaws.com", "lambda.amazonaws.com"]}, "Action": "sts:AssumeRole"},
            {"Effect": "Allow", "Principal": {"AWS": "arn:aws:iam::111111111111:root"}, "Action": "sts:AssumeRole"},
            {"Effect": "Deny", "Principal": {"Service": "denied.amazonaws.com"}, "Action": "sts:AssumeRole"},
        ],
    }

    assert trusted_service_principals(document) == {"ec2.amazonaws.com", "ssm.amazonaws.com", "lambda.amazonaws.com"}


def test_trusted_service_principals_from_url_encoded_string() -> None:
    encoded = quote('{"Version":"2012-10-17","Statement":{"Effect":"Allow","Principal":{"Service":"ec2.amazonaws.com"},"Action":"sts:AssumeRole"}}')

    assert trusted_service_principals(encoded) == {"ec2.amazonaws.com"}


def test_trusted_service_principals_ignores_wildcard_principal() -> None:
    document = {"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": "*", "Action": "sts:AssumeRole"}]}

    assert trusted_service_principals(document) == set()


@pytest.mark.parametrize("document", [{"Version": "2012-10-17"}, {"Statement": [{"Principal": {"Service": "x"}}]}])
def test_trusted_service_principals_raises_on_malformed_document(document: dict[str, object]) -> None:
    with pytest.raises(KeyError):
        trusted_service_principals(document)

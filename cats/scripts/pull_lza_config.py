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

"""Download the deployed LZA configuration zip into a local directory.

The tests do this themselves (``lza_utils.config_source``); this wrapper is for inspecting a
deployment's configuration by hand. Run with the credentials ``cats infra deploy`` uses:

    CATS_CONFIG=cats.yaml uv run python -m scripts.pull_lza_config \\
        LzaDeployment lza1-config-<deployment-account-id>-us-east-1 lza/aws-accelerator-config.zip /tmp/lza-config
"""

from __future__ import annotations

import sys
from pathlib import Path

from lza_utils.config_source import DeployedConfigLocation, config_bucket_client, unpack_config_zip

USAGE = "usage: python -m scripts.pull_lza_config <account_key> <bucket> <key> <destination>"


def main() -> int:
    """CLI entry point: <account_key> <bucket> <key> <destination>."""
    if len(sys.argv) != 5:
        print(USAGE, file=sys.stderr)
        return 2
    account_key, bucket, key, destination = sys.argv[1:5]
    location = DeployedConfigLocation(account_key, bucket, key)
    body = config_bucket_client(location).get_object(Bucket=bucket, Key=key)["Body"].read()
    members = unpack_config_zip(body, Path(destination))
    print(f"{len(members)} files from {location!r} -> {destination}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

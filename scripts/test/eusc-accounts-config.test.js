/**
 *  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 *
 *  Licensed under the Apache License, Version 2.0 (the "License"). You may not use this file except in compliance
 *  with the License. A copy of the License is located at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 *  or in the 'license' file accompanying this file. This file is distributed on an 'AS IS' BASIS, WITHOUT WARRANTIES
 *  OR CONDITIONS OF ANY KIND, express or implied. See the License for the specific language governing permissions
 *  and limitations under the License.
 */

// The EUSC accounts-config.yaml must parse as shipped and after a customer replaces the account ID placeholder.
const fs = require("fs");
const path = require("path");
const test = require("node:test");
const assert = require("node:assert");
const { NETWORKS, renderConfig, loadYaml } = require("./helpers.js");

for (const network of NETWORKS) {
  test(`${network}: EUSC accounts-config.yaml parses and carries the LzaDeploymentAccount accountIds entry`, () => {
    const config = loadYaml(renderConfig("eusc", network), "accounts-config.yaml");
    assert.deepStrictEqual(config.accountIds, [
      { email: "<lzadeployment>@example.com  <----- UPDATE EMAIL ADDRESS", accountId: "111111111111" },
    ]);
  });

  test(`${network}: EUSC accounts-config.yaml still parses after the account ID placeholder is replaced`, () => {
    // Customers replace only the digits; the UPDATE marker must be a comment so the edited line stays valid YAML.
    const dir = renderConfig("eusc", network);
    const file = path.join(dir, "accounts-config.yaml");
    fs.writeFileSync(file, fs.readFileSync(file, "utf8").replace("'111111111111'", "'123456789012'"), "utf8");
    assert.strictEqual(loadYaml(dir, "accounts-config.yaml").accountIds[0].accountId, "123456789012");
  });
}

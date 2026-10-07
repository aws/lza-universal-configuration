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

// Test helpers: build a partition config the way release-package.js does, without zipping it.
const fs = require("fs");
const os = require("os");
const path = require("path");
const yaml = require("js-yaml");
const { loadReplacements, processConfigFile } = require("../config-replacer.js");

const ROOT = path.resolve(__dirname, "..", "..");
const REPLACEMENTS = {
  eusc: path.join(ROOT, "replacements", "replacements-for-aws-european-sovereign-cloud.yaml"),
  govcloud: path.join(ROOT, "replacements", "replacements-for-aws-govcloud-us.yaml"),
  standard: path.join(ROOT, "replacements", "replacements-for-aws-standard.yaml"),
};
const NETWORKS = ["hub-and-spoke", "shared-vpc"];

// Each call gets its own directory, because some tests edit the rendered files; all are removed on exit.
const renderedDirs = [];
process.on("exit", () => {
  for (const dir of renderedDirs) fs.rmSync(dir, { recursive: true, force: true });
});

function renderConfig(partition, network) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), `uc-${partition}-${network}-`));
  renderedDirs.push(dir);
  fs.cpSync(path.join(ROOT, "modules", "base", "default"), dir, { recursive: true });
  fs.cpSync(path.join(ROOT, "modules", "network", network), dir, { recursive: true });
  const replacements = loadReplacements(REPLACEMENTS[partition]);
  for (const fileConfig of replacements) {
    if (fileConfig.postActions) continue;
    fs.writeFileSync(path.join(dir, fileConfig.filename), processConfigFile(dir, fileConfig), "utf8");
  }
  for (const entry of replacements) {
    for (const action of entry.postActions || []) {
      for (const folder of action.folders || []) fs.rmSync(path.join(dir, folder), { recursive: true, force: true });
      for (const file of action.files || []) fs.rmSync(path.join(dir, file), { force: true });
    }
  }
  return dir;
}

// UC files hold unquoted {{ Key }} tokens; turn them into plain scalars before parsing.
function loadYaml(dir, filename) {
  const text = fs.readFileSync(path.join(dir, filename), "utf8").replace(/\{\{\s*(\w+)\s*\}\}/g, "__$1__");
  return yaml.load(text);
}

function loadJson(dir, filename) {
  return JSON.parse(fs.readFileSync(path.join(dir, filename), "utf8"));
}

module.exports = { ROOT, NETWORKS, renderConfig, loadYaml, loadJson };

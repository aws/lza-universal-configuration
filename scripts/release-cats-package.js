#!/usr/bin/env node

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

const fs = require("fs");
const os = require("os");
const path = require("path");
const { CATS_DIR, copyCatsPack } = require("./lib/cats-package");
const { packageUrl, runCommand, uploadFile } = require("./lib/package-utils");

/**
 * Validates and parses command line arguments
 * @param {string[]} args - Command line arguments
 * @returns {{version: string, output: string, upload: boolean}} Parsed arguments
 * @throws {Error} When required arguments are missing
 */
function validateArguments(args) {
  if (args.includes("-h") || args.includes("--help")) {
    showHelp();
    process.exit(0);
  }

  let version;
  const vIndex = args.findIndex((arg) => arg === "-v" || arg === "--version");
  if (vIndex !== -1 && args[vIndex + 1]) {
    version = args[vIndex + 1];
  }

  let output;
  const oIndex = args.findIndex((arg) => arg === "-o" || arg === "--output");
  if (oIndex !== -1 && args[oIndex + 1]) {
    output = args[oIndex + 1];
  }

  const upload = args.includes("-u") || args.includes("--upload");

  if (!version) {
    throw new Error("Version is required (-v or --version)");
  }

  if (!output) {
    throw new Error("Output filename is required (-o or --output)");
  }

  return { version, output, upload };
}

/**
 * Displays help information and usage instructions
 */
function showHelp() {
  console.log(`
Usage: node release-cats-package.js [options]

Builds and uploads the CATS controls test pack release package: the cats/
directory as a zip with cats/ at its top level. One package serves every
partition and network type; the pack reads the deployed LZA configuration at
run time.

Options:
  -v, --version <version>    Release version [required]
  -o, --output <path>        Output file path [required]
  -u, --upload               Upload package to GitLab registry
  -h, --help                 Show this help message`);
}

const args = process.argv.slice(2);
const { version, output, upload } = validateArguments(args);

/**
 * Main function that builds and uploads the package
 * @returns {Promise<void>} Promise that resolves when package is built and uploaded
 */
async function main() {
  const zipFilename = output;
  const zipPath = path.resolve(zipFilename);
  // `zip -r` onto an existing archive updates it in place and keeps entries for files that no
  // longer exist; a package must only ever hold what this run staged.
  fs.rmSync(zipPath, { force: true });

  // Staged outside the repository: staging under cats/ would copy the staging directory into itself.
  const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), "lza-uc-cats-package-"));
  try {
    const catsFiles = copyCatsPack(path.resolve(__dirname, ".."), tempDir);
    console.log(`Packaging CATS test pack: ${catsFiles} files`);
    await runCommand("zip", ["-r", zipPath, CATS_DIR], tempDir);
  } finally {
    fs.rmSync(tempDir, { recursive: true, force: true });
  }

  if (upload) {
    await uploadFile(zipFilename, packageUrl(version, zipFilename), process.env.CI_JOB_TOKEN);
  }
}

main().catch((error) => {
  console.error(`Error: ${error.message}`);
  process.exit(1);
});

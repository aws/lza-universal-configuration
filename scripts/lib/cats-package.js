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

// Copies the CATS controls test pack (cats/) into its release package.
//
// The pack is released as its own zip, one for every partition and network
// type: it reads the deployed LZA configuration at run time and derives the
// partition from it.
// The copy list is `git ls-files cats`, so the package holds exactly the
// committed files whatever else a used working tree has lying about (tool
// caches, virtual environments, CATS run outputs, scratch files).

const fs = require("fs");
const path = require("path");
const { execFileSync } = require("child_process");

const CATS_DIR = "cats";
// What a customer needs for the README's install and first run. The pack ships no cats.yaml:
// the customer copies the example for their deployment shape to that name, so all four must be
// there. It ships no uv.lock either: pyproject.toml pins the engine to a minor and `uv sync`
// writes the lock on the customer's machine.
const REQUIRED_FILES = [
  "pyproject.toml",
  "examples/control-tower-standard.yaml",
  "examples/control-tower-container.yaml",
  "examples/organizations-standard.yaml",
  "examples/organizations-container.yaml",
  "lza-compliance-workbook-1.4.0.csv",
  "tests/conftest.py",
];

/**
 * Lists the files git tracks under cats/, relative to the repository root.
 * @param {string} repoRoot - Repository root holding the cats/ directory
 * @returns {string[]} tracked paths such as "cats/pyproject.toml"
 */
function trackedCatsFiles(repoRoot) {
  // safe.directory: CI checkouts are often owned by a different uid than the job runs as,
  // and git >= 2.35.2 refuses to read such a repository without it.
  const output = execFileSync("git", ["-c", "safe.directory=*", "ls-files", "-z", "--", CATS_DIR], { cwd: repoRoot });
  return output
    .toString("utf8")
    .split("\0")
    .filter((file) => file !== "");
}

/**
 * Copies the test pack from `<repoRoot>/cats` into `<packageDir>/cats`.
 * @param {string} repoRoot - Repository root holding the cats/ directory
 * @param {string} packageDir - Package staging directory
 * @returns {number} number of files copied
 * @throws {Error} when the pack is missing, is not a complete CATS pack, or a tracked file is absent from the working tree
 */
function copyCatsPack(repoRoot, packageDir) {
  const tracked = trackedCatsFiles(repoRoot);
  const missingRequired = REQUIRED_FILES.filter((required) => !tracked.includes(path.posix.join(CATS_DIR, required)));
  if (missingRequired.length > 0) {
    throw new Error(`CATS pack at ${path.join(repoRoot, CATS_DIR)} is missing ${missingRequired.join(", ")}`);
  }
  const missingFromWorktree = tracked.filter((file) => !fs.existsSync(path.join(repoRoot, file)));
  if (missingFromWorktree.length > 0) {
    throw new Error(`tracked but absent from the working tree: ${missingFromWorktree.join(", ")}`);
  }
  for (const file of tracked) {
    const destPath = path.join(packageDir, file);
    fs.mkdirSync(path.dirname(destPath), { recursive: true });
    fs.copyFileSync(path.join(repoRoot, file), destPath);
  }
  return tracked.length;
}

module.exports = { CATS_DIR, REQUIRED_FILES, copyCatsPack, trackedCatsFiles };

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

// The CATS release package holds the committed files under cats/ and nothing else.
const fs = require("fs");
const os = require("os");
const path = require("path");
const { execFileSync } = require("child_process");
const test = require("node:test");
const assert = require("node:assert");
const { ROOT } = require("./helpers.js");
const { REQUIRED_FILES, copyCatsPack, trackedCatsFiles } = require("../lib/cats-package.js");

const stagingDirs = [];
process.on("exit", () => {
  for (const dir of stagingDirs) fs.rmSync(dir, { recursive: true, force: true });
});

function stage() {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "uc-cats-package-"));
  stagingDirs.push(dir);
  return dir;
}

// Isolated from the developer's git configuration: no signing, no hooks, a fixed identity.
const GIT_ENV = {
  ...process.env,
  GIT_CONFIG_GLOBAL: "/dev/null",
  GIT_CONFIG_SYSTEM: "/dev/null",
  GIT_AUTHOR_NAME: "test",
  GIT_AUTHOR_EMAIL: "test@example.com",
  GIT_COMMITTER_NAME: "test",
  GIT_COMMITTER_EMAIL: "test@example.com",
};

function git(cwd, ...args) {
  return execFileSync("git", ["-c", "commit.gpgsign=false", "-c", "core.hooksPath=/dev/null", ...args], {
    cwd,
    env: GIT_ENV,
    encoding: "utf8",
    stdio: ["ignore", "pipe", "ignore"],
  });
}

// A hand-built pack: the required files plus two more, written out in full so the test has
// an oracle independent of trackedCatsFiles.
const FIXTURE_PACK_FILES = [...REQUIRED_FILES, "lza_utils/lza_config.py", "tests/scp/test_scp_core.py"].sort();

/** A throwaway repository with FIXTURE_PACK_FILES committed under cats/. */
function repoWithCommittedPack() {
  const repo = stage();
  git(repo, "init", "-q");
  for (const file of FIXTURE_PACK_FILES) {
    const dest = path.join(repo, "cats", file);
    fs.mkdirSync(path.dirname(dest), { recursive: true });
    fs.writeFileSync(dest, `# ${file}\n`);
  }
  git(repo, "add", "cats");
  git(repo, "commit", "-q", "-m", "pack");
  return repo;
}

function listFiles(dir) {
  const files = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true, recursive: true })) {
    if (entry.isFile()) files.push(path.relative(dir, path.join(entry.parentPath, entry.name)));
  }
  return files.sort();
}

test("the packaged cats/ is exactly the committed files, with their contents", () => {
  // arrange
  const repo = repoWithCommittedPack();
  const packageDir = stage();

  // act
  const copied = copyCatsPack(repo, packageDir);

  // assert
  assert.deepStrictEqual(listFiles(path.join(packageDir, "cats")), FIXTURE_PACK_FILES);
  assert.strictEqual(copied, FIXTURE_PACK_FILES.length);
  assert.strictEqual(
    fs.readFileSync(path.join(packageDir, "cats", "examples", "control-tower-standard.yaml"), "utf8"),
    "# examples/control-tower-standard.yaml\n",
  );
});

test("untracked files in a used working tree are not packaged, whatever their names", () => {
  // arrange - gitignored artifacts and arbitrarily named scratch files, none of them committed
  const repo = repoWithCommittedPack();
  for (const dir of [".venv/lib", "__pycache__", "lza_utils/__pycache__", ".pytest_cache"]) {
    fs.mkdirSync(path.join(repo, "cats", dir), { recursive: true });
    fs.writeFileSync(path.join(repo, "cats", dir, "artifact"), "");
  }
  for (const file of ["report.json", "assessment-results.json", "junit.xml", "scratch-notes.txt", "tests/test_local_experiment.py"]) {
    fs.writeFileSync(path.join(repo, "cats", file), "");
  }
  const packageDir = stage();

  // act
  copyCatsPack(repo, packageDir);

  // assert
  assert.deepStrictEqual(listFiles(path.join(packageDir, "cats")), FIXTURE_PACK_FILES);
});

test("a tracked file deleted from the working tree without git rm is refused, not silently dropped", () => {
  // arrange
  const repo = repoWithCommittedPack();
  fs.rmSync(path.join(repo, "cats", "lza_utils", "lza_config.py"));

  // act / assert
  assert.throws(() => copyCatsPack(repo, stage()), /absent from the working tree: cats\/lza_utils\/lza_config\.py/);
});

test("a committed cats/ that is not a complete pack is refused, naming every missing file", () => {
  // arrange - cats/ holding only a pyproject.toml
  const repo = stage();
  git(repo, "init", "-q");
  fs.mkdirSync(path.join(repo, "cats"));
  fs.writeFileSync(path.join(repo, "cats", "pyproject.toml"), "");
  git(repo, "add", "cats");

  // act / assert
  const expected = REQUIRED_FILES.filter((file) => file !== "pyproject.toml").join(", ");
  assert.throws(() => copyCatsPack(repo, stage()), new RegExp(`is missing ${expected.replaceAll(".", "\\.")}$`));
});

test("a repository without cats/ is refused", () => {
  const repo = stage();
  git(repo, "init", "-q");
  assert.throws(() => copyCatsPack(repo, stage()), /is missing pyproject\.toml, examples\/control-tower-standard\.yaml/);
});

test("this repository's cats/ carries every required file, so the release package is buildable", () => {
  const tracked = trackedCatsFiles(ROOT).map((file) => path.relative("cats", file));
  const missing = REQUIRED_FILES.filter((file) => !tracked.includes(file));
  assert.deepStrictEqual(missing, []);
});

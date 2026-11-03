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

// Process and upload helpers shared by the release packaging scripts.

const fs = require("fs");
const path = require("path");
const { spawn } = require("child_process");
const https = require("https");
const { URL } = require("url");

/**
 * Executes a command with arguments in a specified directory
 * @param {string} cmd - Command to execute
 * @param {string[]} args - Command arguments
 * @param {string} cwd - Working directory
 * @returns {Promise<void>} Promise that resolves when command completes successfully
 */
function runCommand(cmd, args, cwd) {
  return new Promise((resolve, reject) => {
    const child = spawn(cmd, args, { cwd, stdio: "inherit" });
    child.on("close", (code) =>
      code === 0 ? resolve() : reject(new Error(`Command failed: ${code}`))
    );
  });
}

/**
 * Uploads a file to a URL using HTTPS PUT request
 * @param {string} filePath - Path to file to upload
 * @param {string} url - Upload URL
 * @param {string} token - Authentication token
 * @returns {Promise<void>} Promise that resolves when upload completes successfully
 */
function uploadFile(filePath, url, token) {
  return new Promise((resolve, reject) => {
    const fileSize = fs.statSync(filePath).size;
    console.log(`Uploading ${path.basename(filePath)} (${(fileSize / 1024 / 1024).toFixed(2)} MB) to ${url}`);
    const startTime = Date.now();
    const parsedUrl = new URL(url);
    const fileStream = fs.createReadStream(filePath);
    const options = {
      hostname: parsedUrl.hostname,
      port: parsedUrl.port || 443,
      path: parsedUrl.pathname + parsedUrl.search,
      method: "PUT",
      headers: {
        "JOB-TOKEN": token,
        "Content-Length": fileSize,
      },
    };
    const req = https.request(options, (res) => {
      let body = '';
      res.on('data', (chunk) => { body += chunk; });
      res.on('error', (err) => {
        const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
        reject(new Error(`Response stream error after ${elapsed}s: ${err.message}`));
      });
      res.on('end', () => {
        const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
        if (res.statusCode < 400) {
          console.log(`Upload complete: HTTP ${res.statusCode} (${elapsed}s)`);
          resolve();
        } else {
          reject(new Error(`Upload failed: HTTP ${res.statusCode} - ${body} (${elapsed}s)`));
        }
      });
    });
    req.on("error", (err) => {
      const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
      reject(new Error(`Upload error after ${elapsed}s: ${err.message}`));
    });
    fileStream.pipe(req);
  });
}

/**
 * The GitLab generic package registry URL a release asset is uploaded to.
 * @param {string} version - Release version (the tag)
 * @param {string} zipFilename - Path of the zip; only its basename is used
 * @returns {string} Upload URL
 */
function packageUrl(version, zipFilename) {
  return `${process.env.CI_API_V4_URL}/projects/${process.env.CI_PROJECT_ID}/packages/generic/lza-universal-config/${version}/${path.basename(zipFilename)}`;
}

module.exports = { runCommand, uploadFile, packageUrl };

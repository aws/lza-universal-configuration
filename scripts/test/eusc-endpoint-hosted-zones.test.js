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

// EUSC central interface endpoints need private hosted zones under amazonaws.eu, the DNS suffix SDKs use there.
const test = require("node:test");
const assert = require("node:assert");
const { NETWORKS, renderConfig, loadYaml } = require("./helpers.js");

function centralEndpoints(network) {
  const config = loadYaml(renderConfig("eusc", network), "network-config.yaml");
  const vpcs = config.vpcs.filter((vpc) => vpc.interfaceEndpoints && vpc.interfaceEndpoints.central);
  assert.strictEqual(vpcs.length, 1, "expected one central endpoints VPC");
  return vpcs[0].interfaceEndpoints.endpoints;
}

for (const network of NETWORKS) {
  test(`${network}: every EUSC central endpoint has an amazonaws.eu hosted zone in the home region`, () => {
    const endpoints = centralEndpoints(network);
    assert.ok(endpoints.length > 0);
    for (const endpoint of endpoints) {
      // Written exactly as LZA names the zone: dotted service names are reversed (ecr.api -> api.ecr) and end
      // with a trailing dot. A different string would replace the zone again once LZA derives amazonaws.eu itself.
      const dotted = endpoint.service.includes(".");
      const label = endpoint.service.split(".").reverse().join(".");
      const expected = `${label}.__HomeRegion__.amazonaws.eu${dotted ? "." : ""}`;
      assert.strictEqual(endpoint.hostedZoneName, expected, endpoint.service);
    }
  });

  test(`${network}: every EUSC central endpoint sets its service name in the home region`, () => {
    // ECR advertises the eu.amazonaws prefix in EUSC; the other UC endpoints use com.amazonaws.
    for (const endpoint of centralEndpoints(network)) {
      const prefix = endpoint.service.startsWith("ecr.") ? "eu" : "com";
      assert.strictEqual(endpoint.serviceName, `${prefix}.amazonaws.__HomeRegion__.${endpoint.service}`, endpoint.service);
    }
  });
}

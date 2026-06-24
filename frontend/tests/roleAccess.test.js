import assert from "node:assert/strict";
import test from "node:test";

let policy;

try {
  policy = await import("../src/routing/roleAccess.js");
} catch {
  policy = null;
}

test("role access policy is available", () => {
  assert.ok(policy, "role access policy module must exist");
});

test("each role has the expected home page", () => {
  assert.equal(policy?.homeForRole("applicant"), "/applicant");
  assert.equal(policy?.homeForRole("staff"), "/staff");
  assert.equal(policy?.homeForRole("surveyor"), "/surveyor/tasks");
  assert.equal(policy?.homeForRole("manager"), "/analytics");
});

test("applicant cannot open staff, surveyor, map, or analytics routes", () => {
  assert.equal(policy?.isPathAllowed("applicant", "/applicant"), true);
  assert.equal(policy?.isPathAllowed("applicant", "/applicant/track"), true);
  assert.equal(policy?.isPathAllowed("applicant", "/certificate"), true);
  assert.equal(policy?.isPathAllowed("applicant", "/staff/applications"), false);
  assert.equal(policy?.isPathAllowed("applicant", "/surveyor/tasks"), false);
  assert.equal(policy?.isPathAllowed("applicant", "/map"), false);
  assert.equal(policy?.isPathAllowed("applicant", "/analytics"), false);
});

test("staff can manage applications but cannot execute surveyor tasks", () => {
  assert.equal(policy?.isPathAllowed("staff", "/staff"), true);
  assert.equal(policy?.isPathAllowed("staff", "/staff/applications/LRMIS-2026-0001"), true);
  assert.equal(policy?.isPathAllowed("staff", "/analytics"), true);
  assert.equal(policy?.isPathAllowed("staff", "/map"), true);
  assert.equal(policy?.isPathAllowed("staff", "/surveyor/tasks"), false);
});

test("surveyor is limited to survey tasks and the map", () => {
  assert.equal(policy?.isPathAllowed("surveyor", "/surveyor/tasks"), true);
  assert.equal(policy?.isPathAllowed("surveyor", "/surveyor/tasks/LRMIS-2026-0001"), true);
  assert.equal(policy?.isPathAllowed("surveyor", "/map"), true);
  assert.equal(policy?.isPathAllowed("surveyor", "/analytics"), false);
  assert.equal(policy?.isPathAllowed("surveyor", "/staff/applications"), false);
});

test("manager is limited to analytics and map views", () => {
  assert.equal(policy?.isPathAllowed("manager", "/analytics"), true);
  assert.equal(policy?.isPathAllowed("manager", "/map"), true);
  assert.equal(policy?.isPathAllowed("manager", "/staff"), false);
  assert.equal(policy?.isPathAllowed("manager", "/staff/applications"), false);
});

test("only staff can issue certificates", () => {
  assert.equal(policy?.canIssueCertificate("staff"), true);
  assert.equal(policy?.canIssueCertificate("applicant"), false);
  assert.equal(policy?.canIssueCertificate("surveyor"), false);
  assert.equal(policy?.canIssueCertificate("manager"), false);
});

test("dashboard navigation links require exact matching", () => {
  assert.equal(policy?.requiresExactNavMatch("/applicant"), true);
  assert.equal(policy?.requiresExactNavMatch("/staff"), true);
  assert.equal(policy?.requiresExactNavMatch("/applicant/submit"), false);
  assert.equal(policy?.requiresExactNavMatch("/surveyor/tasks"), false);
});

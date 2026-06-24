import assert from "node:assert/strict";
import test from "node:test";

let identity;

try {
  identity = await import("../src/applicants/identity.js");
} catch {
  identity = null;
}

test("company applicants use a company registration number", () => {
  assert.deepEqual(identity?.identityFieldForApplicantType("company"), {
    key: "registration_number",
    label: "Company Registration Number",
    placeholder: "Enter company registration number"
  });
});

test("non-company applicants use a national ID", () => {
  assert.deepEqual(identity?.identityFieldForApplicantType("citizen"), {
    key: "national_id",
    label: "National ID",
    placeholder: "Enter national ID"
  });
});

test("company payload excludes national ID", () => {
  assert.deepEqual(
    identity?.identityValuesForApplicant({
      applicant_type: "company",
      national_id: "400000000",
      registration_number: "COMP-2026-15"
    }),
    {
      national_id: null,
      registration_number: "COMP-2026-15"
    }
  );
});

test("citizen payload excludes company registration number", () => {
  assert.deepEqual(
    identity?.identityValuesForApplicant({
      applicant_type: "citizen",
      national_id: "400000000",
      registration_number: "COMP-2026-15"
    }),
    {
      national_id: "400000000",
      registration_number: null
    }
  );
});

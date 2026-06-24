import assert from "node:assert/strict";
import test from "node:test";

let session;

try {
  session = await import("../src/applicants/session.js");
} catch {
  session = null;
}

function memoryStorage() {
  const values = new Map();
  return {
    getItem: (key) => values.get(key) ?? null,
    setItem: (key, value) => values.set(key, String(value)),
    removeItem: (key) => values.delete(key),
    entries: () => Object.fromEntries(values)
  };
}

test("current applicant session stores only the applicant ID", () => {
  const storage = memoryStorage();

  session?.saveCurrentApplicantId(storage, "applicant-123");

  assert.deepEqual(storage.entries(), {
    "lrmis-applicant-id": "applicant-123"
  });
  assert.equal(session?.loadCurrentApplicantId(storage), "applicant-123");

  session?.clearCurrentApplicantId(storage);
  assert.equal(session?.loadCurrentApplicantId(storage), null);
});

test("applicant profile response restores the form fields", () => {
  const profile = {
    full_name: "Saved Applicant",
    applicant_type: "company",
    verification_state: "verified",
    identity: {
      national_id: null,
      registration_number: "COMP-2026-15"
    },
    contacts: {
      email: "office@example.com",
      phone: "+970599000015"
    },
    address: {
      city: "Ramallah",
      neighborhood: "Al Tireh",
      street: null,
      zone_id: "ZONE-RM-02"
    },
    preferred_language: "ar",
    notification_preferences: {
      preferred_contact: "email",
      on_status_change: true,
      on_missing_documents: true,
      on_certificate_ready: true
    },
    privacy_settings: {
      share_contact_with_staff: true,
      allow_sms_notifications: false,
      allow_email_notifications: true
    }
  };

  assert.deepEqual(session?.applicantFormFromProfile(profile), {
    full_name: "Saved Applicant",
    applicant_type: "company",
    verification_state: "verified",
    national_id: "",
    registration_number: "COMP-2026-15",
    contacts: profile.contacts,
    address: profile.address,
    preferred_language: "ar",
    notification_preferences: profile.notification_preferences,
    privacy_settings: profile.privacy_settings
  });
});

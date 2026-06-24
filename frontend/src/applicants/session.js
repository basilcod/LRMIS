const currentApplicantKey = "lrmis-applicant-id";

export function saveCurrentApplicantId(storage, applicantId) {
  storage.setItem(currentApplicantKey, applicantId);
}

export function loadCurrentApplicantId(storage) {
  return storage.getItem(currentApplicantKey);
}

export function clearCurrentApplicantId(storage) {
  storage.removeItem(currentApplicantKey);
}

export function applicantFormFromProfile(profile) {
  return {
    full_name: profile.full_name,
    applicant_type: profile.applicant_type,
    verification_state: profile.verification_state,
    national_id: profile.identity?.national_id || "",
    registration_number: profile.identity?.registration_number || "",
    contacts: profile.contacts,
    address: profile.address,
    preferred_language: profile.preferred_language,
    notification_preferences: profile.notification_preferences,
    privacy_settings: profile.privacy_settings
  };
}

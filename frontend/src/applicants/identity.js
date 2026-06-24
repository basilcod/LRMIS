const nationalIdField = {
  key: "national_id",
  label: "National ID",
  placeholder: "Enter national ID"
};

const companyRegistrationField = {
  key: "registration_number",
  label: "Company Registration Number",
  placeholder: "Enter company registration number"
};

export function identityFieldForApplicantType(applicantType) {
  return applicantType === "company"
    ? companyRegistrationField
    : nationalIdField;
}

export function identityValuesForApplicant(applicant) {
  if (applicant.applicant_type === "company") {
    return {
      national_id: null,
      registration_number: applicant.registration_number.trim() || null
    };
  }

  return {
    national_id: applicant.national_id.trim() || null,
    registration_number: null
  };
}

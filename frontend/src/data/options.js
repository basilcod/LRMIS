export const applicationStatuses = [
  "submitted",
  "pre_checked",
  "survey_required",
  "surveyed",
  "legal_review",
  "approved",
  "certificate_issued",
  "closed",
  "rejected",
  "on_hold",
  "missing_documents",
  "under_objection"
];

export const applicationTypeOptions = [
  { value: "first_registration", label: "First Registration" },
  { value: "ownership_transfer", label: "Ownership Transfer" },
  { value: "parcel_subdivision", label: "Parcel Subdivision" },
  { value: "parcel_merge", label: "Parcel Merge" },
  { value: "boundary_correction", label: "Boundary Correction" },
  { value: "certificate_request", label: "Certificate Request" }
];

export const parcelFieldOptions = [
  { key: "parcel_number", label: "Parcel Number" },
  { key: "block_number", label: "Block Number" },
  { key: "basin_number", label: "Basin Number" },
  { key: "area_sqm", label: "Area (Square Meters)", inputMode: "decimal" }
];

export const zoneOptions = [
  { value: "ZONE-RM-01", label: "Ramallah Zone 1" },
  { value: "ZONE-RM-02", label: "Ramallah Zone 2" }
];

export const applicantTypes = [
  "citizen",
  "lawyer",
  "company",
  "surveyor",
  "authorized_representative"
];

export const surveyMilestones = [
  "visit_scheduled",
  "arrived_on_site",
  "survey_started",
  "survey_completed"
];

import { useEffect, useState } from "react";

import { applicantsApi, applicationsApi, errorMessage } from "../api/client";
import {
  identityFieldForApplicantType,
  identityValuesForApplicant
} from "../applicants/identity";
import {
  applicantFormFromProfile,
  clearCurrentApplicantId,
  loadCurrentApplicantId,
  saveCurrentApplicantId
} from "../applicants/session";
import {
  applicantTypes,
  applicationTypeOptions,
  parcelFieldOptions,
  zoneOptions
} from "../data/options";

const defaultApplicant = {
  full_name: "Nour Ahmad",
  applicant_type: "citizen",
  verification_state: "unverified",
  national_id: "400000000",
  registration_number: "",
  contacts: {
    email: "nour@example.com",
    phone: "+970599000000"
  },
  address: {
    city: "Ramallah",
    neighborhood: "Al Tireh",
    zone_id: "ZONE-RM-01"
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
    allow_sms_notifications: true,
    allow_email_notifications: true
  }
};

const defaultApplication = {
  application_type: "ownership_transfer",
  priority: "normal",
  description: "Ownership transfer application for parcel 145.",
  parcel_ref: {
    parcel_number: "145",
    block_number: "12",
    basin_number: "3",
    zone_id: "ZONE-RM-01",
    area_sqm: 840.5,
    land_use: "residential"
  }
};

export function SubmitApplicationPage() {
  const [applicant, setApplicant] = useState(defaultApplicant);
  const [application, setApplication] = useState(defaultApplication);
  const [applicantId, setApplicantId] = useState(
    () => loadCurrentApplicantId(localStorage) || ""
  );
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const identityField = identityFieldForApplicantType(applicant.applicant_type);

  useEffect(() => {
    const savedApplicantId = loadCurrentApplicantId(localStorage);
    if (!savedApplicantId) {
      return undefined;
    }

    let cancelled = false;
    setLoading(true);
    setError("");

    applicantsApi
      .get(savedApplicantId)
      .then((profile) => {
        if (cancelled) {
          return;
        }
        setApplicant(applicantFormFromProfile(profile));
        setApplicantId(savedApplicantId);
        setResult({ type: "Applicant profile loaded", id: savedApplicantId });
      })
      .catch(() => {
        if (cancelled) {
          return;
        }
        clearCurrentApplicantId(localStorage);
        setApplicantId("");
        setError("Saved applicant profile could not be loaded.");
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  function useDifferentProfile() {
    clearCurrentApplicantId(localStorage);
    setApplicant(defaultApplicant);
    setApplicantId("");
    setResult(null);
    setError("");
  }

  async function createApplicant(event) {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const payload = {
        ...applicant,
        ...identityValuesForApplicant(applicant)
      };
      const created = await applicantsApi.create(payload);
      saveCurrentApplicantId(localStorage, created.applicant_id);
      setApplicantId(created.applicant_id);
      setResult({ type: "Applicant created", id: created.applicant_id });
    } catch (requestError) {
      setError(errorMessage(requestError));
    } finally {
      setLoading(false);
    }
  }

  async function submitApplication(event) {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const created = await applicationsApi.create({
        ...application,
        applicant_ref: {
          applicant_id: applicantId,
          applicant_type: applicant.applicant_type,
          submitted_by_representative: false
        },
        parcel_ref: {
          ...application.parcel_ref,
          area_sqm: Number(application.parcel_ref.area_sqm),
          geometry: {
            type: "Polygon",
            coordinates: [
              [
                [35.2001, 31.9001],
                [35.2008, 31.9001],
                [35.2008, 31.9008],
                [35.2001, 31.9001]
              ]
            ]
          }
        },
        required_documents: [
          {
            document_type: "ownership_deed",
            required: true,
            status: "uploaded"
          }
        ],
        tags: ["demo"]
      });
      setResult({ type: "Application submitted", id: created.application_id });
    } catch (requestError) {
      setError(errorMessage(requestError));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="two-column">
      <form className="panel form-panel" onSubmit={createApplicant}>
        <h2>Create applicant profile</h2>
        {applicantId && (
          <div className="notice">
            <strong>Current applicant profile</strong>
            <span>{applicantId}</span>
            <button type="button" onClick={useDifferentProfile}>
              Use a different profile
            </button>
          </div>
        )}
        <label>
          Full name
          <input
            value={applicant.full_name}
            onChange={(event) => setApplicant({ ...applicant, full_name: event.target.value })}
          />
        </label>
        <label>
          Applicant type
          <select
            value={applicant.applicant_type}
            onChange={(event) => {
              const applicantType = event.target.value;
              setApplicant({
                ...applicant,
                applicant_type: applicantType,
                national_id: applicantType === "company" ? "" : applicant.national_id,
                registration_number:
                  applicantType === "company" ? applicant.registration_number : ""
              });
            }}
          >
            {applicantTypes.map((type) => (
              <option key={type}>{type}</option>
            ))}
          </select>
        </label>
        <label>
          {identityField.label}
          <input
            value={applicant[identityField.key]}
            placeholder={identityField.placeholder}
            required
            onChange={(event) =>
              setApplicant({
                ...applicant,
                [identityField.key]: event.target.value
              })
            }
          />
        </label>
        <label>
          Email
          <input
            value={applicant.contacts.email}
            onChange={(event) =>
              setApplicant({
                ...applicant,
                contacts: { ...applicant.contacts, email: event.target.value }
              })
            }
          />
        </label>
        <label>
          Phone
          <input
            value={applicant.contacts.phone}
            onChange={(event) =>
              setApplicant({
                ...applicant,
                contacts: { ...applicant.contacts, phone: event.target.value }
              })
            }
          />
        </label>
        <button type="submit" disabled={loading}>
          Create applicant
        </button>
      </form>

      <form className="panel form-panel" onSubmit={submitApplication}>
        <h2>Submit land application</h2>
        <label>
          Applicant ID
          <input
            value={applicantId}
            onChange={(event) => setApplicantId(event.target.value)}
            placeholder="Create applicant first or paste ID"
          />
        </label>
        <label>
          Application type
          <select
            value={application.application_type}
            onChange={(event) =>
              setApplication({ ...application, application_type: event.target.value })
            }
          >
            {applicationTypeOptions.map((type) => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
        </label>
        {parcelFieldOptions.map((field) => (
          <label key={field.key}>
            {field.label}
            <input
              value={application.parcel_ref[field.key]}
              inputMode={field.inputMode}
              required
              onChange={(event) =>
                setApplication({
                  ...application,
                  parcel_ref: {
                    ...application.parcel_ref,
                    [field.key]: event.target.value
                  }
                })
              }
            />
          </label>
        ))}
        <label>
          Zone
          <select
            value={application.parcel_ref.zone_id}
            onChange={(event) =>
              setApplication({
                ...application,
                parcel_ref: {
                  ...application.parcel_ref,
                  zone_id: event.target.value
                }
              })
            }
          >
            {zoneOptions.map((zone) => (
              <option key={zone.value} value={zone.value}>
                {zone.label}
              </option>
            ))}
          </select>
        </label>
        <label>
          Description
          <textarea
            value={application.description}
            onChange={(event) =>
              setApplication({ ...application, description: event.target.value })
            }
          />
        </label>
        <button type="submit" disabled={loading || !applicantId}>
          Submit application
        </button>
      </form>
      {(error || result) && (
        <div className={`notice ${error ? "error" : "success"}`}>
          {error || `${result.type}: ${result.id}`}
        </div>
      )}
    </div>
  );
}

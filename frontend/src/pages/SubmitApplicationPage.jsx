import { useState } from "react";

import { applicantsApi, applicationsApi, errorMessage } from "../api/client";
import { applicantTypes, applicationTypes } from "../data/options";

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
  const [applicantId, setApplicantId] = useState("");
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function createApplicant(event) {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const payload = {
        ...applicant,
        registration_number: applicant.registration_number || null
      };
      const created = await applicantsApi.create(payload);
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
            onChange={(event) =>
              setApplicant({ ...applicant, applicant_type: event.target.value })
            }
          >
            {applicantTypes.map((type) => (
              <option key={type}>{type}</option>
            ))}
          </select>
        </label>
        <label>
          National ID
          <input
            value={applicant.national_id}
            onChange={(event) => setApplicant({ ...applicant, national_id: event.target.value })}
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
            {applicationTypes.map((type) => (
              <option key={type}>{type}</option>
            ))}
          </select>
        </label>
        {["parcel_number", "block_number", "basin_number", "zone_id", "area_sqm"].map((field) => (
          <label key={field}>
            {field}
            <input
              value={application.parcel_ref[field]}
              onChange={(event) =>
                setApplication({
                  ...application,
                  parcel_ref: {
                    ...application.parcel_ref,
                    [field]: event.target.value
                  }
                })
              }
            />
          </label>
        ))}
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

import { useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";

import { applicationsApi, errorMessage } from "../api/client";
import { DataState } from "../components/DataState";
import { StatusBadge } from "../components/StatusBadge";

export function CertificateViewPage({ canIssue = false }) {
  const [searchParams] = useSearchParams();
  const initialId = useMemo(() => searchParams.get("applicationId") || "LRMIS-2026-0001", [searchParams]);
  const [applicationId, setApplicationId] = useState(initialId);
  const [application, setApplication] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  async function loadCertificate(event) {
    event.preventDefault();
    setLoading(true);
    setError("");
    setNotice("");
    try {
      setApplication(await applicationsApi.get(applicationId));
    } catch (requestError) {
      setApplication(null);
      setError(errorMessage(requestError));
    } finally {
      setLoading(false);
    }
  }

  async function issueCertificate() {
    setNotice("");
    try {
      await applicationsApi.certificate(applicationId, {
        certificate_type: "ownership_certificate",
        issued_by: "registrar_09",
        issued_to_name: "Applicant"
      });
      setApplication(await applicationsApi.get(applicationId));
      setNotice("Certificate issued.");
    } catch (requestError) {
      setNotice(errorMessage(requestError));
    }
  }

  return (
    <section className="stack">
      <form className="panel inline-form" onSubmit={loadCertificate}>
        <label>
          Application ID
          <input value={applicationId} onChange={(event) => setApplicationId(event.target.value)} />
        </label>
        <button type="submit">Load certificate</button>
      </form>
      <DataState loading={loading} error={error} empty={!application && !loading}>
        {application && (
          <div className="certificate-card">
            <span className="eyebrow">Official certificate metadata</span>
            <h2>{application.certificate_state?.certificate_id || "Certificate not issued"}</h2>
            <StatusBadge status={application.status} />
            <dl className="details-list">
              <div>
                <dt>Application</dt>
                <dd>{application.application_id}</dd>
              </div>
              <div>
                <dt>Parcel</dt>
                <dd>{application.parcel_ref?.parcel_code || application.parcel_ref?.parcel_number}</dd>
              </div>
              <div>
                <dt>Zone</dt>
                <dd>{application.parcel_ref?.zone_id}</dd>
              </div>
              <div>
                <dt>Certificate state</dt>
                <dd>{application.certificate_state?.certificate_issued ? "Issued" : "Pending"}</dd>
              </div>
            </dl>
            {canIssue && application.status === "approved" && (
              <button type="button" onClick={issueCertificate}>
                Issue certificate metadata
              </button>
            )}
            {notice && <div className="notice">{notice}</div>}
          </div>
        )}
      </DataState>
    </section>
  );
}

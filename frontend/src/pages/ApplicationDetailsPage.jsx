import { useState } from "react";
import { useParams } from "react-router-dom";

import { applicationsApi, errorMessage, staffApi } from "../api/client";
import { DataState } from "../components/DataState";
import { StatusBadge } from "../components/StatusBadge";
import { applicationStatuses } from "../data/options";
import { useAsyncData } from "../hooks/useAsyncData";

export function ApplicationDetailsPage() {
  const { applicationId } = useParams();
  const { data, loading, error, setData } = useAsyncData(
    () => applicationsApi.get(applicationId),
    [applicationId]
  );
  const [targetState, setTargetState] = useState("pre_checked");
  const [actorId, setActorId] = useState("registrar_09");
  const [reason, setReason] = useState("");
  const [notice, setNotice] = useState("");

  async function runAction(action) {
    setNotice("");
    try {
      let updated;
      if (action === "transition") {
        updated = await applicationsApi.transition(applicationId, {
          target_state: targetState,
          actor_type: "registrar",
          actor_id: actorId,
          note: `Moved to ${targetState}`,
          survey_report_exists: targetState === "surveyed",
          legal_review_completed: targetState === "approved"
        });
      }
      if (action === "hold") {
        updated = await applicationsApi.hold(applicationId, {
          actor_id: actorId,
          reason: reason || "Waiting for missing field information."
        });
      }
      if (action === "reject") {
        updated = await applicationsApi.reject(applicationId, {
          actor_id: actorId,
          reason: reason || "Application did not satisfy registration rules."
        });
      }
      if (action === "certificate") {
        await applicationsApi.certificate(applicationId, {
          certificate_type: "ownership_certificate",
          issued_by: actorId,
          issued_to_name: "Applicant"
        });
        updated = await applicationsApi.get(applicationId);
      }
      if (action === "review") {
        await staffApi.registrarReview(applicationId, {
          reviewer_id: actorId,
          decision: "approved",
          notes: "Survey report accepted.",
          actor_role: "registrar"
        });
        updated = await applicationsApi.get(applicationId);
      }
      setData(updated);
      setNotice("Action completed.");
    } catch (requestError) {
      setNotice(errorMessage(requestError));
    }
  }

  return (
    <DataState loading={loading} error={error}>
      {data && (
        <div className="two-column">
          <section className="panel">
            <h2>{data.application_id}</h2>
            <StatusBadge status={data.status} />
            <dl className="details-list">
              <div>
                <dt>Application type</dt>
                <dd>{data.application_type}</dd>
              </div>
              <div>
                <dt>Priority</dt>
                <dd>{data.priority}</dd>
              </div>
              <div>
                <dt>Zone</dt>
                <dd>{data.parcel_ref?.zone_id}</dd>
              </div>
              <div>
                <dt>Parcel code</dt>
                <dd>{data.parcel_ref?.parcel_code || data.parcel_ref?.parcel_number}</dd>
              </div>
              <div>
                <dt>Certificate</dt>
                <dd>{data.certificate_state?.certificate_id || "Not issued"}</dd>
              </div>
            </dl>
          </section>
          <section className="panel form-panel">
            <h2>Workflow actions</h2>
            <label>
              Actor / registrar ID
              <input value={actorId} onChange={(event) => setActorId(event.target.value)} />
            </label>
            <label>
              Target state
              <select value={targetState} onChange={(event) => setTargetState(event.target.value)}>
                {applicationStatuses.map((status) => (
                  <option key={status}>{status}</option>
                ))}
              </select>
            </label>
            <label>
              Hold / reject reason
              <textarea value={reason} onChange={(event) => setReason(event.target.value)} />
            </label>
            <div className="button-grid">
              <button type="button" onClick={() => runAction("transition")}>
                Transition
              </button>
              <button type="button" onClick={() => runAction("hold")}>
                Hold
              </button>
              <button type="button" onClick={() => runAction("reject")}>
                Reject
              </button>
              <button type="button" onClick={() => runAction("certificate")}>
                Issue certificate
              </button>
            </div>
            {notice && <div className="notice">{notice}</div>}
          </section>
        </div>
      )}
    </DataState>
  );
}

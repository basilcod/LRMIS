import { useState } from "react";
import { Link } from "react-router-dom";

import { applicationsApi, errorMessage } from "../api/client";
import { DataState } from "../components/DataState";
import { StatusBadge } from "../components/StatusBadge";

export function TrackApplicationPage() {
  const [applicationId, setApplicationId] = useState("LRMIS-2026-0001");
  const [application, setApplication] = useState(null);
  const [timeline, setTimeline] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function track(event) {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const details = await applicationsApi.get(applicationId);
      setApplication(details);
      try {
        setTimeline(await applicationsApi.timeline(applicationId));
      } catch {
        setTimeline([]);
      }
    } catch (requestError) {
      setApplication(null);
      setError(errorMessage(requestError));
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="stack">
      <form className="panel inline-form" onSubmit={track}>
        <label>
          Application ID
          <input
            value={applicationId}
            onChange={(event) => setApplicationId(event.target.value)}
          />
        </label>
        <button type="submit">Track</button>
      </form>
      <DataState loading={loading} error={error} empty={!application && !loading}>
        {application && (
          <div className="two-column">
            <div className="panel">
              <h2>{application.application_id}</h2>
              <StatusBadge status={application.status} />
              <dl className="details-list">
                <div>
                  <dt>Type</dt>
                  <dd>{application.application_type}</dd>
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
                  <dt>Certificate</dt>
                  <dd>{application.certificate_state?.certificate_id || "Not issued yet"}</dd>
                </div>
              </dl>
              <Link className="secondary-action" to={`/certificate?applicationId=${application.application_id}`}>
                Open certificate view
              </Link>
            </div>
            <div className="panel">
              <h2>Timeline</h2>
              <ol className="timeline">
                {timeline.length === 0 && <li>No timeline events yet.</li>}
                {timeline.map((event, index) => (
                  <li key={`${event.type}-${index}`}>
                    <strong>{event.type}</strong>
                    <span>{event.next_state || event.meta?.milestone || event.meta?.note || ""}</span>
                  </li>
                ))}
              </ol>
            </div>
          </div>
        )}
      </DataState>
    </section>
  );
}

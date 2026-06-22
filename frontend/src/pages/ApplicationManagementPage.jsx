import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { applicationsApi, errorMessage, staffApi } from "../api/client";
import { DataState } from "../components/DataState";
import { StatusBadge } from "../components/StatusBadge";
import { applicationStatuses } from "../data/options";

export function ApplicationManagementPage() {
  const [applications, setApplications] = useState([]);
  const [status, setStatus] = useState("");
  const [zoneId, setZoneId] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  useEffect(() => {
    loadApplications();
  }, []);

  async function loadApplications(filters = {}) {
    setLoading(true);
    setError("");
    try {
      setApplications(await applicationsApi.list(filters));
    } catch (requestError) {
      setError(errorMessage(requestError));
    } finally {
      setLoading(false);
    }
  }

  function applyFilters(event) {
    event.preventDefault();
    loadApplications({
      status: status || undefined,
      zone_id: zoneId || undefined
    });
  }

  async function autoAssign(applicationId) {
    setNotice("");
    try {
      await staffApi.autoAssign(applicationId);
      setNotice(`Surveyor assigned for ${applicationId}.`);
      loadApplications({ status: status || undefined, zone_id: zoneId || undefined });
    } catch (requestError) {
      setNotice(errorMessage(requestError));
    }
  }

  return (
    <section className="stack">
      <form className="panel inline-form" onSubmit={applyFilters}>
        <label>
          Status
          <select value={status} onChange={(event) => setStatus(event.target.value)}>
            <option value="">All</option>
            {applicationStatuses.map((item) => (
              <option key={item}>{item}</option>
            ))}
          </select>
        </label>
        <label>
          Zone
          <input value={zoneId} onChange={(event) => setZoneId(event.target.value)} placeholder="ZONE-RM-01" />
        </label>
        <button type="submit">Apply filters</button>
      </form>
      {notice && <div className="notice">{notice}</div>}
      <DataState loading={loading} error={error} empty={applications.length === 0}>
        <div className="panel table-panel">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Type</th>
                <th>Status</th>
                <th>Zone</th>
                <th>Parcel</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {applications.map((application) => (
                <tr key={application.application_id}>
                  <td>{application.application_id}</td>
                  <td>{application.application_type}</td>
                  <td><StatusBadge status={application.status} /></td>
                  <td>{application.parcel_ref?.zone_id}</td>
                  <td>{application.parcel_ref?.parcel_number}</td>
                  <td className="table-actions">
                    <Link to={`/staff/applications/${application.application_id}`}>Open</Link>
                    {application.status === "survey_required" && (
                      <button type="button" onClick={() => autoAssign(application.application_id)}>
                        Auto assign
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </DataState>
    </section>
  );
}

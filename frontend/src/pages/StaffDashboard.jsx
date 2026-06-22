import { Link } from "react-router-dom";

import { analyticsApi } from "../api/client";
import { DataState } from "../components/DataState";
import { StatCard } from "../components/StatCard";
import { useAsyncData } from "../hooks/useAsyncData";

export function StaffDashboard() {
  const { data, loading, error } = useAsyncData(() => analyticsApi.kpis(), []);

  return (
    <DataState loading={loading} error={error}>
      <section className="page-grid">
        <div className="panel wide">
          <h2>Registrar Operations</h2>
          <p>Review applications, assign surveys, issue certificates, and monitor delayed cases.</p>
          <div className="actions-row">
            <Link className="primary-action" to="/staff/applications">
              Manage applications
            </Link>
            <Link className="secondary-action" to="/analytics">
              View analytics
            </Link>
          </div>
        </div>
        <StatCard label="Pending" value={data?.pending_applications} tone="warn" />
        <StatCard label="Approved" value={data?.approved_applications} tone="good" />
        <StatCard label="Rejected" value={data?.rejected_applications} tone="bad" />
        <StatCard label="Certificates" value={data?.certificates_issued_total} />
      </section>
    </DataState>
  );
}

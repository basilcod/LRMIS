import { Link } from "react-router-dom";

import { analyticsApi } from "../api/client";
import { DataState } from "../components/DataState";
import { StatCard } from "../components/StatCard";
import { useAsyncData } from "../hooks/useAsyncData";

export function ApplicantDashboard() {
  const { data, loading, error } = useAsyncData(() => analyticsApi.kpis(), []);

  return (
    <DataState loading={loading} error={error}>
      <section className="page-grid">
        <div className="panel wide">
          <h2>Applicant Portal</h2>
          <p>
            Start with an applicant profile, submit a land application, then track the
            workflow until certificate issuance.
          </p>
          <div className="actions-row">
            <Link className="primary-action" to="/applicant/submit">
              Submit application
            </Link>
            <Link className="secondary-action" to="/applicant/track">
              Track application
            </Link>
          </div>
        </div>
        <StatCard label="Total applications" value={data?.total_applications} />
        <StatCard label="Pending applications" value={data?.pending_applications} tone="warn" />
        <StatCard label="Approved" value={data?.approved_applications} tone="good" />
        <StatCard label="Under objection" value={data?.under_objection_applications} tone="bad" />
      </section>
    </DataState>
  );
}

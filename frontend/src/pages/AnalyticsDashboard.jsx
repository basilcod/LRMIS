import { analyticsApi } from "../api/client";
import { DataState } from "../components/DataState";
import { MiniBarChart } from "../components/MiniBarChart";
import { StatCard } from "../components/StatCard";
import { useAsyncData } from "../hooks/useAsyncData";

export function AnalyticsDashboard() {
  const { data, loading, error } = useAsyncData(
    async () => {
      const [kpis, byStatus, byZone, processing, surveyors, registrars] = await Promise.all([
        analyticsApi.kpis(),
        analyticsApi.byStatus(),
        analyticsApi.byZone(),
        analyticsApi.processingTime(),
        analyticsApi.surveyors(),
        analyticsApi.registrars()
      ]);
      return { kpis, byStatus, byZone, processing, surveyors, registrars };
    },
    []
  );

  return (
    <DataState loading={loading} error={error}>
      {data && (
        <section className="stack">
          <div className="page-grid">
            <StatCard label="Total applications" value={data.kpis.total_applications} />
            <StatCard label="Pending" value={data.kpis.pending_applications} tone="warn" />
            <StatCard label="Approved" value={data.kpis.approved_applications} tone="good" />
            <StatCard label="Rejected" value={data.kpis.rejected_applications} tone="bad" />
            <StatCard label="Avg processing days" value={data.kpis.average_processing_time_days} />
            <StatCard label="Certificates issued" value={data.kpis.certificates_issued_total} />
          </div>

          <div className="two-column">
            <section className="panel">
              <h2>Applications by status</h2>
              <MiniBarChart items={data.byStatus} labelKey="status" />
            </section>
            <section className="panel">
              <h2>Hotspot zones</h2>
              <MiniBarChart items={data.byZone} labelKey="zone_id" valueKey="total" />
            </section>
          </div>

          <div className="two-column">
            <section className="panel table-panel">
              <h2>Surveyor workload</h2>
              <table>
                <thead>
                  <tr>
                    <th>Surveyor</th>
                    <th>Assigned</th>
                    <th>Completed</th>
                    <th>Workload</th>
                  </tr>
                </thead>
                <tbody>
                  {data.surveyors.map((item) => (
                    <tr key={item.staff_id}>
                      <td>{item.staff_code}</td>
                      <td>{item.assigned_tasks}</td>
                      <td>{item.completed_tasks}</td>
                      <td>{item.active_tasks}/{item.max_tasks}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>
            <section className="panel table-panel">
              <h2>Registrar workload</h2>
              <table>
                <thead>
                  <tr>
                    <th>Registrar</th>
                    <th>Reviews</th>
                    <th>Approved</th>
                    <th>Rejected</th>
                  </tr>
                </thead>
                <tbody>
                  {data.registrars.map((item) => (
                    <tr key={item.staff_id}>
                      <td>{item.staff_code}</td>
                      <td>{item.reviewed_reports}</td>
                      <td>{item.approved_reports}</td>
                      <td>{item.rejected_reports}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>
          </div>

          <section className="panel">
            <h2>Processing time by application type</h2>
            <MiniBarChart items={data.processing} labelKey="application_type" valueKey="average_days" />
          </section>
        </section>
      )}
    </DataState>
  );
}

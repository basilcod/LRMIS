import { Link } from "react-router-dom";

import { applicationsApi } from "../api/client";
import { DataState } from "../components/DataState";
import { StatusBadge } from "../components/StatusBadge";
import { useAsyncData } from "../hooks/useAsyncData";

export function SurveyorTaskListPage() {
  const { data, loading, error } = useAsyncData(
    () => applicationsApi.list({ status: "survey_required" }),
    []
  );
  const tasks = data || [];

  return (
    <DataState loading={loading} error={error} empty={tasks.length === 0}>
      <div className="panel table-panel">
        <table>
          <thead>
            <tr>
              <th>Application</th>
              <th>Status</th>
              <th>Zone</th>
              <th>Parcel</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {tasks.map((task) => (
              <tr key={task.application_id}>
                <td>{task.application_id}</td>
                <td><StatusBadge status={task.status} /></td>
                <td>{task.parcel_ref?.zone_id}</td>
                <td>{task.parcel_ref?.parcel_number}</td>
                <td>
                  <Link to={`/surveyor/tasks/${task.application_id}`}>Execute</Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </DataState>
  );
}

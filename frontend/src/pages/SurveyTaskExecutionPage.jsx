import { useState } from "react";
import { useParams } from "react-router-dom";

import { applicationsApi, errorMessage } from "../api/client";
import { DataState } from "../components/DataState";
import { StatusBadge } from "../components/StatusBadge";
import { surveyMilestones } from "../data/options";
import { useAsyncData } from "../hooks/useAsyncData";

export function SurveyTaskExecutionPage() {
  const { applicationId } = useParams();
  const { data, loading, error } = useAsyncData(() => applicationsApi.get(applicationId), [applicationId]);
  const [staffId, setStaffId] = useState("675100000000000000000301");
  const [notice, setNotice] = useState("");

  async function addMilestone(milestone) {
    setNotice("");
    try {
      await applicationsApi.surveyMilestone(applicationId, {
        milestone,
        by_staff_id: staffId,
        actor_role: "surveyor",
        notes: `${milestone} completed from frontend demo.`,
        meta: {}
      });
      setNotice(`${milestone} recorded.`);
    } catch (requestError) {
      setNotice(errorMessage(requestError));
    }
  }

  async function uploadReport() {
    setNotice("");
    try {
      await applicationsApi.surveyReport(applicationId, {
        surveyor_id: staffId,
        file_name: "survey_report.pdf",
        storage_ref: "frontend-demo/survey_report.pdf",
        summary: "Boundary points verified from field visit.",
        actor_role: "surveyor"
      });
      setNotice("Survey report metadata registered.");
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
            <p>{data.description}</p>
            <dl className="details-list">
              <div>
                <dt>Zone</dt>
                <dd>{data.parcel_ref?.zone_id}</dd>
              </div>
              <div>
                <dt>Parcel</dt>
                <dd>{data.parcel_ref?.parcel_number}</dd>
              </div>
            </dl>
          </section>
          <section className="panel form-panel">
            <h2>Survey actions</h2>
            <label>
              Surveyor staff ID
              <input value={staffId} onChange={(event) => setStaffId(event.target.value)} />
            </label>
            <div className="button-grid">
              {surveyMilestones.map((milestone) => (
                <button key={milestone} type="button" onClick={() => addMilestone(milestone)}>
                  {milestone}
                </button>
              ))}
              <button type="button" onClick={uploadReport}>
                Upload report metadata
              </button>
            </div>
            {notice && <div className="notice">{notice}</div>}
          </section>
        </div>
      )}
    </DataState>
  );
}

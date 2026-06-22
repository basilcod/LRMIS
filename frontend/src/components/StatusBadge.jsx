const tones = {
  submitted: "blue",
  pre_checked: "blue",
  survey_required: "orange",
  surveyed: "orange",
  legal_review: "purple",
  approved: "green",
  certificate_issued: "green",
  closed: "neutral",
  rejected: "red",
  on_hold: "orange",
  missing_documents: "orange",
  under_objection: "red"
};

export function StatusBadge({ status }) {
  return <span className={`status-badge ${tones[status] || "neutral"}`}>{status}</span>;
}

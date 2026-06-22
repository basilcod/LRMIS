import axios from "axios";

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000
});

export function unwrap(response) {
  return response.data?.data ?? response.data;
}

export function errorMessage(error) {
  return (
    error.response?.data?.detail ||
    error.response?.data?.error?.message ||
    error.message ||
    "Request failed."
  );
}

export const applicationsApi = {
  list: (params = {}) => api.get("/applications/", { params }).then(unwrap),
  get: (applicationId) => api.get(`/applications/${applicationId}`).then(unwrap),
  create: (payload) => api.post("/applications/", payload).then(unwrap),
  transition: (applicationId, payload) =>
    api.patch(`/applications/${applicationId}/transition`, payload).then(unwrap),
  hold: (applicationId, payload) =>
    api.post(`/applications/${applicationId}/hold`, payload).then(unwrap),
  reject: (applicationId, payload) =>
    api.post(`/applications/${applicationId}/reject`, payload).then(unwrap),
  certificate: (applicationId, payload) =>
    api.post(`/applications/${applicationId}/certificate`, payload).then(unwrap),
  timeline: (applicationId) =>
    api.get(`/applications/${applicationId}/timeline`).then(unwrap),
  surveyMilestone: (applicationId, payload) =>
    api.patch(`/applications/${applicationId}/survey-milestone`, payload).then(unwrap),
  surveyReport: (applicationId, payload) =>
    api.post(`/applications/${applicationId}/survey-report`, payload).then(unwrap)
};

export const applicantsApi = {
  create: (payload) => api.post("/applicants/", payload).then(unwrap),
  get: (applicantId) => api.get(`/applicants/${applicantId}`).then(unwrap),
  applications: (applicantId) =>
    api.get(`/applicants/${applicantId}/applications`).then(unwrap)
};

export const staffApi = {
  create: (payload) => api.post("/staff/", payload).then(unwrap),
  get: (staffId) => api.get(`/staff/${staffId}`).then(unwrap),
  autoAssign: (applicationId) =>
    api.post(`/applications/${applicationId}/auto-assign-surveyor`).then(unwrap),
  registrarReview: (applicationId, payload) =>
    api.patch(`/applications/${applicationId}/registrar-review`, payload).then(unwrap)
};

export const analyticsApi = {
  kpis: () => api.get("/analytics/kpis").then(unwrap),
  byStatus: () => api.get("/analytics/applications-by-status").then(unwrap),
  byZone: () => api.get("/analytics/applications-by-zone").then(unwrap),
  processingTime: () => api.get("/analytics/processing-time").then(unwrap),
  surveyors: () => api.get("/analytics/surveyors").then(unwrap),
  registrars: () => api.get("/analytics/registrars").then(unwrap),
  parcelsFeed: () => api.get("/analytics/geofeeds/parcels").then(unwrap),
  pendingHeatmap: () =>
    api.get("/analytics/geofeeds/pending-heatmap").then(unwrap)
};

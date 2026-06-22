import { useEffect, useState } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { AppShell } from "./components/AppShell";
import { AnalyticsDashboard } from "./pages/AnalyticsDashboard";
import { ApplicantDashboard } from "./pages/ApplicantDashboard";
import { ApplicationDetailsPage } from "./pages/ApplicationDetailsPage";
import { ApplicationManagementPage } from "./pages/ApplicationManagementPage";
import { CertificateViewPage } from "./pages/CertificateViewPage";
import { LiveMapPage } from "./pages/LiveMapPage";
import { RoleSelectionPage } from "./pages/RoleSelectionPage";
import { StaffDashboard } from "./pages/StaffDashboard";
import { SubmitApplicationPage } from "./pages/SubmitApplicationPage";
import { SurveyTaskExecutionPage } from "./pages/SurveyTaskExecutionPage";
import { SurveyorTaskListPage } from "./pages/SurveyorTaskListPage";
import { TrackApplicationPage } from "./pages/TrackApplicationPage";

const homeByRole = {
  applicant: "/applicant",
  staff: "/staff",
  surveyor: "/surveyor/tasks",
  manager: "/analytics"
};

export function App() {
  const [role, setRoleState] = useState(() => localStorage.getItem("lrmis-role"));

  function setRole(nextRole) {
    if (nextRole) {
      localStorage.setItem("lrmis-role", nextRole);
    } else {
      localStorage.removeItem("lrmis-role");
    }
    setRoleState(nextRole);
  }

  useEffect(() => {
    document.title = "LRMIS";
  }, []);

  return (
    <BrowserRouter>
      <Routes>
        {!role ? (
          <Route path="*" element={<RoleSelectionPage setRole={setRole} />} />
        ) : (
          <Route path="/" element={<AppShell role={role} setRole={setRole} />}>
            <Route index element={<Navigate to={homeByRole[role] || "/applicant"} replace />} />
            <Route path="applicant" element={<ApplicantDashboard />} />
            <Route path="applicant/submit" element={<SubmitApplicationPage />} />
            <Route path="applicant/track" element={<TrackApplicationPage />} />
            <Route path="staff" element={<StaffDashboard />} />
            <Route path="staff/applications" element={<ApplicationManagementPage />} />
            <Route path="staff/applications/:applicationId" element={<ApplicationDetailsPage />} />
            <Route path="surveyor/tasks" element={<SurveyorTaskListPage />} />
            <Route path="surveyor/tasks/:applicationId" element={<SurveyTaskExecutionPage />} />
            <Route path="map" element={<LiveMapPage />} />
            <Route path="analytics" element={<AnalyticsDashboard />} />
            <Route path="certificate" element={<CertificateViewPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        )}
      </Routes>
    </BrowserRouter>
  );
}

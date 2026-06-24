import { useEffect, useState } from "react";
import {
  BrowserRouter,
  Navigate,
  Route,
  Routes,
  useLocation
} from "react-router-dom";

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
import {
  canIssueCertificate,
  homeForRole,
  isKnownRole,
  isPathAllowed
} from "./routing/roleAccess";

const routerBasename =
  import.meta.env.BASE_URL === "/" ? undefined : import.meta.env.BASE_URL.replace(/\/$/, "");

export function App() {
  const [role, setRoleState] = useState(() => {
    const storedRole = localStorage.getItem("lrmis-role");
    return isKnownRole(storedRole) ? storedRole : null;
  });

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
    <BrowserRouter basename={routerBasename}>
      <Routes>
        {!role ? (
          <Route path="*" element={<RoleSelectionPage setRole={setRole} />} />
        ) : (
          <Route
            path="/"
            element={
              <RoleRouteGuard role={role}>
                <AppShell role={role} setRole={setRole} />
              </RoleRouteGuard>
            }
          >
            <Route index element={<Navigate to={homeForRole(role)} replace />} />
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
            <Route
              path="certificate"
              element={<CertificateViewPage canIssue={canIssueCertificate(role)} />}
            />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        )}
      </Routes>
    </BrowserRouter>
  );
}

function RoleRouteGuard({ role, children }) {
  const location = useLocation();

  if (!isPathAllowed(role, location.pathname)) {
    return <Navigate to={homeForRole(role)} replace />;
  }

  return children;
}

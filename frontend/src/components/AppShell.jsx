import { Link, NavLink, Outlet, useLocation } from "react-router-dom";

import {
  requiresExactNavMatch,
  roleNavigation
} from "../routing/roleAccess";

export function AppShell({ role, setRole }) {
  const location = useLocation();
  const links = roleNavigation[role] || [];

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <Link to="/" className="brand">
          <span className="brand-mark">LR</span>
          <span>
            <strong>LRMIS</strong>
            <small>Land Registration</small>
          </span>
        </Link>
        <nav>
          {links.map(([label, href]) => (
            <NavLink key={href} to={href} end={requiresExactNavMatch(href)}>
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="role-card">
          <span>Current role</span>
          <strong>{role}</strong>
          <button type="button" onClick={() => setRole(null)}>
            Change role
          </button>
        </div>
      </aside>
      <main className="main-panel">
        <header className="topbar">
          <div>
            <span className="eyebrow">LRMIS Demo</span>
            <h1>{titleFromPath(location.pathname)}</h1>
          </div>
          <span className="api-pill">FastAPI backend</span>
        </header>
        <Outlet />
      </main>
    </div>
  );
}

function titleFromPath(pathname) {
  if (pathname.includes("submit")) return "Submit Application";
  if (pathname.includes("track")) return "Track Application";
  if (pathname.includes("applications")) return "Application Management";
  if (pathname.includes("surveyor/tasks/")) return "Survey Task Execution";
  if (pathname.includes("surveyor/tasks")) return "Surveyor Tasks";
  if (pathname.includes("analytics")) return "Analytics Dashboard";
  if (pathname.includes("map")) return "Live Map";
  if (pathname.includes("certificate")) return "Certificate View";
  if (pathname.includes("staff")) return "Staff Dashboard";
  if (pathname.includes("applicant")) return "Applicant Dashboard";
  return "Role Selection";
}

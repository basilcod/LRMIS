import { useNavigate } from "react-router-dom";

import { homeForRole } from "../routing/roleAccess";

const roles = [
  {
    id: "applicant",
    title: "Applicant",
    description: "Create profile, submit application, track status, view certificate."
  },
  {
    id: "staff",
    title: "Staff / Registrar",
    description: "Manage applications, workflow transitions, holds, rejections, certificates."
  },
  {
    id: "surveyor",
    title: "Surveyor",
    description: "View assigned survey work and register field milestones."
  },
  {
    id: "manager",
    title: "Manager",
    description: "Review analytics, map feeds, delayed cases, and workloads."
  }
];

export function RoleSelectionPage({ setRole }) {
  const navigate = useNavigate();

  function selectRole(role) {
    setRole(role);
    navigate(homeForRole(role), { replace: true });
  }

  return (
    <section className="role-selection">
      <div className="hero-panel">
        <span className="eyebrow">University demo</span>
        <h1>LRMIS Land Registration Management</h1>
        <p>
          Select a role to open the matching workflow. This is a simple demo role switcher,
          not production authentication.
        </p>
      </div>
      <div className="role-grid">
        {roles.map((role) => (
          <button key={role.id} type="button" onClick={() => selectRole(role.id)}>
            <strong>{role.title}</strong>
            <span>{role.description}</span>
          </button>
        ))}
      </div>
    </section>
  );
}

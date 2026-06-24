const routeAccess = {
  applicant: {
    prefixes: ["/applicant"],
    exact: ["/certificate"]
  },
  staff: {
    prefixes: ["/staff"],
    exact: ["/analytics", "/map", "/certificate"]
  },
  surveyor: {
    prefixes: ["/surveyor"],
    exact: ["/map"]
  },
  manager: {
    prefixes: [],
    exact: ["/analytics", "/map"]
  }
};

const roleHomes = {
  applicant: "/applicant",
  staff: "/staff",
  surveyor: "/surveyor/tasks",
  manager: "/analytics"
};

export const roleNavigation = {
  applicant: [
    ["Applicant Dashboard", "/applicant"],
    ["Submit Application", "/applicant/submit"],
    ["Track Application", "/applicant/track"],
    ["Certificate", "/certificate"]
  ],
  staff: [
    ["Staff Dashboard", "/staff"],
    ["Applications", "/staff/applications"],
    ["Map", "/map"],
    ["Analytics", "/analytics"]
  ],
  surveyor: [
    ["Survey Tasks", "/surveyor/tasks"],
    ["Map", "/map"]
  ],
  manager: [
    ["Analytics", "/analytics"],
    ["Map", "/map"]
  ]
};

export function homeForRole(role) {
  return roleHomes[role] || "/";
}

export function isKnownRole(role) {
  return Object.hasOwn(routeAccess, role);
}

export function isPathAllowed(role, pathname) {
  const access = routeAccess[role];
  if (!access) {
    return false;
  }

  if (pathname === "/") {
    return true;
  }

  return (
    access.exact.includes(pathname) ||
    access.prefixes.some(
      (prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`)
    )
  );
}

export function canIssueCertificate(role) {
  return role === "staff";
}

export function requiresExactNavMatch(pathname) {
  return pathname === "/applicant" || pathname === "/staff";
}

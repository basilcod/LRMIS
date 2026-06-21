# GitHub Workflow

## Branches

- `main`: stable submission branch.
- `dev`: integration branch for team work.
- `feature/applications`: Student 1 branch.
- `feature/applicants`: Student 2 branch.
- `feature/staff-survey`: Student 3 branch.
- `feature/analytics-map`: group analytics and map branch.

## Team Rules

- Pull latest `dev` before starting work.
- Commit small, single-purpose changes.
- Open pull requests from feature branches into `dev`.
- Merge `dev` into `main` only after the demo workflow works.
- Do not rename shared API fields without updating `docs/API_CONTRACT.md`.
- Keep `.env` local. Commit `.env.example` only.

## Pull Request Checklist

- The branch runs locally.
- API contract changes are documented.
- Database schema changes are documented.
- Postman examples are updated when endpoints change.
- Screenshots or short demo notes are added when UI changes.

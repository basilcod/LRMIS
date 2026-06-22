# LRMIS - Land Registration Management Information System

LRMIS is a university final project for a workflow-driven land registration system. It manages land registration applications, applicant profiles, parcels, field survey tasks, registrar review, official certificate metadata, analytics, and map visualization.

The project is intentionally organized around the required modules from the final project guidelines. The first delivery goal is a clean GitHub-ready structure, clear API contract, database design, workflow rules, sample requests, and a demo plan.

## Team Module Distribution

| Student | Module | Main Responsibility |
| --- | --- | --- |
| Student 1 | Land Application Management | Applications, parcels, workflow transitions, certificates, audit logs. |
| Student 2 | Applicant Portal and Profiles | Applicant profiles, documents, comments, objections, timeline. |
| Student 3 | Surveyors, Registrar, and Assignment | Staff, surveyor assignment, survey tasks, survey reports, registrar review. |
| Group | Analytics, Map, and Visualization | KPIs, dashboards, GeoJSON feeds, Leaflet map, reports. |

## Tech Stack

- Backend: FastAPI, PyMongo, Pydantic, MongoDB.
- Frontend: React.
- Map: OpenStreetMap, Leaflet, GeoJSON.
- Documentation: README, docs, OpenAPI, Postman.
- Collaboration: GitHub issues, pull requests, branches, GitHub Actions.

## Project Structure

```text
LRMIS/
  backend/
    app/
      routers/
      schemas/
      services/
      models/
      utils/
      main.py
      database.py
      config.py
    requirements.txt
    .env.example
  frontend/
  docs/
  postman/
  .github/
  README.md
  .gitignore
```

## Backend Setup

Use Python 3.11, 3.12, or 3.13. Avoid Python 3.14 for this pinned dependency set.

From the project root:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

On Windows PowerShell:

```powershell
cd backend
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

OpenAPI documentation will be available at:

```text
http://127.0.0.1:8000/docs
```

## Frontend Setup

The frontend will use React with Leaflet for the map screens.

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

On Windows PowerShell:

```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```

## MongoDB Setup

Use either local MongoDB or MongoDB Atlas.

Default local connection:

```text
mongodb://localhost:27017
```

Default database name:

```text
lrmis
```

## Environment Variables

Create `backend/.env` from `backend/.env.example`.

| Variable | Example | Purpose |
| --- | --- | --- |
| `APP_NAME` | `LRMIS` | Application name. |
| `ENVIRONMENT` | `development` | Runtime environment. |
| `MONGODB_URI` | `mongodb://localhost:27017` | MongoDB connection string. |
| `MONGODB_DB_NAME` | `lrmis` | MongoDB database name. |
| `MONGODB_TIMEOUT_MS` | `5000` | MongoDB connection timeout. |
| `CORS_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | Frontend origins allowed by FastAPI. |
| `API_HOST` | `127.0.0.1` | Local API host. |
| `API_PORT` | `8000` | Local API port. |

Do not commit real `.env` files.

## Required MongoDB Indexes

Run these indexes in MongoDB Compass, mongosh, or a setup script:

```javascript
db.land_applications.createIndex({ application_id: 1 }, { unique: true })
db.land_applications.createIndex({ status: 1 })
db.land_applications.createIndex({ application_type: 1 })
db.land_applications.createIndex({ "parcel_ref.parcel_number": 1 })
db.land_applications.createIndex({ "parcel_ref.zone_id": 1 })
db.land_applications.createIndex({ "timestamps.submitted_at": 1 })

db.parcels.createIndex({ parcel_code: 1 }, { unique: true })
db.parcels.createIndex({ geometry: "2dsphere" })
db.parcels.createIndex({ zone_id: 1 })

db.applicants.createIndex({ "identity.national_id": 1 }, { unique: true })
db.staff_members.createIndex({ staff_code: 1 }, { unique: true })
db.survey_tasks.createIndex({ application_id: 1 })
db.certificates.createIndex({ certificate_id: 1 }, { unique: true })
```

## How to Run

Backend:

```bash
cd backend
uvicorn app.main:app --reload
```

Health check:

```text
GET http://127.0.0.1:8000/health
```

Postman collection:

```text
postman/LRMIS.postman_collection.json
```

Seed demo data:

```bash
cd backend
python seed_data.py
```

The seed script creates an applicant, parcels with GeoJSON, surveyor, registrar, assigned survey task, an approved certificate-ready application, and an issued certificate sample.

## Sample Users

| Role | Name | Example ID | Purpose |
| --- | --- | --- | --- |
| Applicant | Nour Ahmad | `675100000000000000000101` | Submit and track ownership transfer application. |
| Surveyor | Survey Team A / `SURV-RM-04` | `675100000000000000000301` | Receive field survey assignment and upload report metadata. |
| Registrar | Registrar 01 / `REG-RM-01` | `675100000000000000000302` | Review documents, approve, reject, and issue certificate metadata. |
| Manager | Manager User | `manager_01` | View dashboards, KPIs, and map. |

Seeded applications:

| Application | Status | Purpose |
| --- | --- | --- |
| `LRMIS-2026-0001` | `survey_required` | Surveyor task and field milestone demo. |
| `LRMIS-2026-0002` | `approved` | Certificate issuance demo. |
| `LRMIS-2026-0003` | `certificate_issued` | Issued certificate and analytics demo. |

## Main API Endpoints

### Land Application Management

- `POST /applications/`
- `GET /applications/`
- `GET /applications/{application_id}`
- `PATCH /applications/{application_id}/transition`
- `POST /applications/{application_id}/hold`
- `POST /applications/{application_id}/reject`
- `POST /applications/{application_id}/certificate`

### Applicant Portal and Profiles

- `POST /applicants/`
- `GET /applicants/{applicant_id}`
- `GET /applicants/{applicant_id}/applications`
- `POST /applications/{application_id}/documents`
- `POST /applications/{application_id}/comments`
- `POST /applications/{application_id}/objections`
- `GET /applications/{application_id}/timeline`

### Surveyors, Registrar, and Assignment

- `POST /staff/`
- `GET /staff/{staff_id}`
- `POST /applications/{application_id}/auto-assign-surveyor`
- `PATCH /applications/{application_id}/survey-milestone`
- `POST /applications/{application_id}/survey-report`
- `PATCH /applications/{application_id}/registrar-review`

### Analytics, Map, and Visualization

- `GET /analytics/kpis`
- `GET /analytics/applications-by-status`
- `GET /analytics/applications-by-zone`
- `GET /analytics/processing-time`
- `GET /analytics/surveyors`
- `GET /analytics/registrars`
- `GET /analytics/geofeeds/parcels`
- `GET /analytics/geofeeds/pending-heatmap`

## Demo Workflow

1. Applicant creates a profile.
2. Applicant submits an ownership transfer application for parcel 145.
3. Application starts as `submitted`.
4. Staff pre-checks the application.
5. Application moves to `pre_checked`.
6. Staff marks survey as required.
7. Application moves to `survey_required`.
8. System auto-assigns a surveyor using zone, availability, workload, skills, priority, and existing tasks.
9. Surveyor updates milestones and uploads survey report metadata.
10. Application moves to `surveyed`.
11. Registrar performs legal review.
12. Application moves to `legal_review`.
13. Registrar approves the application.
14. Application moves to `approved`.
15. System generates certificate metadata.
16. Application moves to `certificate_issued`.
17. Staff closes the application.
18. Application moves to `closed`.
19. Analytics and map views update from database data.

## Documentation

- API contract: `docs/API_CONTRACT.md`
- Database schema: `docs/DATABASE_SCHEMA.md`
- Workflow rules: `docs/WORKFLOW_RULES.md`
- Team tasks: `docs/TEAM_TASKS.md`
- Demo scenario: `docs/DEMO_SCENARIO.md`
- GitHub workflow: `docs/GITHUB_WORKFLOW.md`
- Backend foundation: `docs/BACKEND_FOUNDATION.md`

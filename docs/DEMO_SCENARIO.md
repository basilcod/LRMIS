# Demo Scenario

This is the main end-to-end story for the final presentation. It is designed to work with the React frontend, FastAPI backend, MongoDB, and the sample data from `backend/seed_data.py`.

## Before the Demo

1. Start MongoDB locally or connect to MongoDB Atlas.
2. Start the backend:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

3. Seed demo data:

```powershell
python seed_data.py
```

4. Start the frontend:

```powershell
cd ..\frontend
npm install
npm run dev
```

5. Open:

```text
http://127.0.0.1:5173
```

## Seeded Demo Records

| Record | Value | Purpose |
| --- | --- | --- |
| Applicant | `675100000000000000000101` / Nour Ahmad | Applicant profile and portal tracking. |
| Surveyor | `675100000000000000000301` / `SURV-RM-04` | Receives survey work. |
| Registrar | `675100000000000000000302` / `REG-RM-01` | Reviews and issues certificate metadata. |
| Survey application | `LRMIS-2026-0001` | Starts at `survey_required` with an assigned survey task. |
| Certificate-ready application | `LRMIS-2026-0002` | Starts at `approved`; use it to issue a certificate. |
| Issued certificate sample | `LRMIS-2026-0003` / `CERT-2026-0001` | Shows issued certificate and analytics count. |

## Main Presentation Flow

1. Select the `Applicant` role.
2. Open Applicant Dashboard and show summary cards from `/analytics/kpis`.
3. Open Submit Application and create a new applicant or use seeded applicant ID `675100000000000000000101`.
4. Submit an ownership transfer application with parcel geometry.
5. Open Track Application and search for `LRMIS-2026-0001` or the newly created application.
6. Show current status, parcel details, and timeline events.
7. Switch to `Staff / Registrar`.
8. Open Application Management and filter by `survey_required`.
9. Open `LRMIS-2026-0001` details and show workflow controls.
10. Use Auto Assign Surveyor from the application table if demonstrating assignment on a new application.
11. Switch to `Surveyor`.
12. Open Survey Tasks and select `LRMIS-2026-0001`.
13. Add survey milestones in order:
    - `visit_scheduled`
    - `arrived_on_site`
    - `survey_started`
    - `survey_completed`
14. Register survey report metadata.
15. Switch back to `Staff / Registrar`.
16. Open the approved sample `LRMIS-2026-0002` or transition a completed application through legal review.
17. Open Certificate View with `LRMIS-2026-0002` and issue certificate metadata.
18. Open Live Map and show:
    - parcel polygons from `/analytics/geofeeds/parcels`
    - pending application heatmap points from `/analytics/geofeeds/pending-heatmap`
19. Open Analytics Dashboard and show:
    - total applications
    - pending / approved / rejected / under objection
    - applications by status and zone
    - processing time
    - surveyor and registrar workload
    - certificates issued per month

## Postman Backup Flow

If the frontend is unavailable, import `postman/LRMIS.postman_collection.json` and run:

1. `Health`
2. `Applicants / Get Applicant`
3. `Applications / List Applications`
4. `Applications / Get Application`
5. `Staff Survey Registrar / Add Survey Milestone`
6. `Staff Survey Registrar / Register Survey Report`
7. `Applications / Issue Certificate`
8. `Analytics and Map / KPIs`
9. `Analytics and Map / Parcel GeoJSON`
10. `Analytics and Map / Pending Heatmap`

## Demo Proof Points

- Workflow transitions reject invalid moves.
- Required documents affect progress.
- Surveyor assignment uses zone, workload, availability, skills, priority, and existing tasks.
- Survey milestones and survey report metadata update the workflow.
- Registrar review and certificate generation are separated.
- Certificate metadata is generated only for approved applications.
- Analytics and map screens are based on MongoDB data, not static screenshots.
- Postman, OpenAPI docs, README files, and seed data are ready for grading review.

# LRMIS React Frontend

React + Vite frontend for the LRMIS university demo. It connects to the FastAPI backend and covers applicant, staff, surveyor, manager, analytics, map, and certificate workflows.

## Setup

```bash
cd frontend
npm install
```

## Backend URL

The default API URL is:

```text
http://127.0.0.1:8000
```

To override it, create `.env` from `.env.example`:

```bash
cp .env.example .env
```

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## Run

Start the FastAPI backend first:

```bash
cd ../backend
uvicorn app.main:app --reload
```

Then start the frontend:

```bash
cd ../frontend
npm run dev
```

Open:

```text
http://127.0.0.1:5173
```

## Build

```bash
npm run build
```

## Demo Flow

1. Select a role from the role selection page.
2. As Applicant, create an applicant profile and submit a land application.
3. Track the application using its `LRMIS-YYYY-0001` application ID.
4. As Staff, manage application workflow, hold/reject applications, assign surveyors, and issue certificates.
5. As Surveyor, view survey-required applications and record milestones/report metadata.
6. Open Live Map to view parcel GeoJSON and pending heatmap points.
7. Open Analytics to review KPIs, status counts, zone hotspots, workloads, and processing time.
8. Open Certificate View to inspect certificate metadata for issued applications.

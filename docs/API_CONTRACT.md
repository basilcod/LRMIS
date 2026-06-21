# API Contract

This file is the shared agreement between the three students. Do not rename fields or endpoints without updating this document and notifying the team.

Base URL for local development:

```text
http://127.0.0.1:8000
```

## Applications

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `POST` | `/applications/` | Create a new land registration application. Supports an `Idempotency-Key` header. |
| `GET` | `/applications/` | List applications with pagination, filtering, and sorting. |
| `GET` | `/applications/{application_id}` | Retrieve full application details. |
| `PATCH` | `/applications/{application_id}/transition` | Move an application to another workflow state. |
| `POST` | `/applications/{application_id}/hold` | Place an application on hold with a required reason. |
| `POST` | `/applications/{application_id}/reject` | Reject an application with a required legal or administrative reason. |
| `POST` | `/applications/{application_id}/certificate` | Generate certificate metadata for an approved application. |

Example create request:

```json
{
  "application_type": "ownership_transfer",
  "priority": "normal",
  "applicant_id": "675100000000000000000101",
  "parcel_number": "145",
  "block_number": "12",
  "basin_number": "3",
  "zone_id": "ZONE-RM-01",
  "description": "Ownership transfer application for parcel 145, block 12."
}
```

## Applicants

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `POST` | `/applicants/` | Create an applicant profile. |
| `GET` | `/applicants/{applicant_id}` | Retrieve applicant profile with restricted public fields. |
| `GET` | `/applicants/{applicant_id}/applications` | Show all applications submitted by the applicant. |

Example create request:

```json
{
  "full_name": "Nour Ahmad",
  "applicant_type": "citizen",
  "national_id": "400000000",
  "email": "nour@example.com",
  "phone": "+970599000000",
  "city": "Ramallah",
  "zone_id": "ZONE-RM-01",
  "preferred_language": "ar"
}
```

## Documents, Comments, Objections, Timeline

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `POST` | `/applications/{application_id}/documents` | Add document metadata or upload supporting document metadata. |
| `POST` | `/applications/{application_id}/comments` | Add applicant comment or response. |
| `POST` | `/applications/{application_id}/objections` | Submit an objection. |
| `GET` | `/applications/{application_id}/timeline` | View status timeline and audit history. |

Document metadata example:

```json
{
  "document_type": "ownership_deed",
  "file_name": "ownership_deed.pdf",
  "storage_ref": "local-demo/ownership_deed.pdf",
  "verification_status": "pending_review"
}
```

## Staff, Surveyors, Registrar

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `POST` | `/staff/` | Create surveyor or registrar staff account. |
| `GET` | `/staff/{staff_id}` | Retrieve staff profile, workload, and performance summary. |
| `POST` | `/applications/{application_id}/auto-assign-surveyor` | Automatically assign surveyor based on policy. |
| `PATCH` | `/applications/{application_id}/survey-milestone` | Add or update survey milestone. |
| `POST` | `/applications/{application_id}/survey-report` | Upload or register survey report metadata. |
| `PATCH` | `/applications/{application_id}/registrar-review` | Submit registrar legal review decision. |

Assignment policy:

```text
zone match + availability + workload balancing + skill match + priority + existing assigned tasks
```

## Analytics and Geofeeds

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/analytics/kpis` | Return main KPIs. |
| `GET` | `/analytics/applications-by-status` | Return number of applications grouped by status. |
| `GET` | `/analytics/applications-by-zone` | Return applications grouped by zone. |
| `GET` | `/analytics/processing-time` | Return average processing time by application type. |
| `GET` | `/analytics/surveyors` | Return surveyor productivity and workload analytics. |
| `GET` | `/analytics/registrars` | Return registrar review workload. |
| `GET` | `/analytics/geofeeds/parcels` | Return parcel GeoJSON feed. |
| `GET` | `/analytics/geofeeds/pending-heatmap` | Return pending application heat-map GeoJSON. |

GeoJSON response shape:

```json
{
  "type": "FeatureCollection",
  "features": []
}
```

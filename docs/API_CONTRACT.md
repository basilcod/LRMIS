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
  "applicant_ref": {
    "applicant_id": "675100000000000000000101",
    "applicant_type": "citizen",
    "submitted_by_representative": false
  },
  "parcel_ref": {
    "parcel_number": "145",
    "block_number": "12",
    "basin_number": "3",
    "zone_id": "ZONE-RM-01",
    "geometry": {
      "type": "Polygon",
      "coordinates": [
        [
          [35.2001, 31.9001],
          [35.2008, 31.9001],
          [35.2008, 31.9008],
          [35.2001, 31.9001]
        ]
      ]
    },
    "area_sqm": 840.5,
    "land_use": "residential"
  },
  "description": "Ownership transfer application for parcel 145, block 12.",
  "required_documents": [
    {
      "document_type": "ownership_deed",
      "required": true,
      "status": "uploaded"
    }
  ]
}
```

Transition example:

```json
{
  "target_state": "pre_checked",
  "actor_type": "registrar",
  "actor_id": "registrar_09",
  "note": "Initial staff pre-check completed.",
  "has_objection": false,
  "survey_report_exists": false,
  "legal_review_completed": false
}
```

Certificate issue example:

```json
{
  "certificate_type": "ownership_certificate",
  "issued_by": "registrar_09",
  "issued_to_name": "Nour Ahmad"
}
```

Rules:

- Applications start in `submitted` and store a parcel snapshot in `parcels`.
- `applicant_ref.applicant_id` must reference an applicant ObjectId string.
- `pre_checked` requires complete applicant and parcel data.
- `survey_required` requires parcel GeoJSON coordinates.
- `surveyed` requires survey report metadata or `survey_report_exists: true`.
- `legal_review` requires at least one uploaded ownership document such as `ownership_deed` or `sale_contract`.
- `approved` requires `legal_review_completed: true`.
- Certificate generation is only allowed for `approved` applications and moves the application to `certificate_issued`.

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
  "verification_state": "unverified",
  "national_id": "400000000",
  "registration_number": null,
  "contacts": {
    "email": "nour@example.com",
    "phone": "+970599000000"
  },
  "address": {
    "city": "Ramallah",
    "neighborhood": "Al Tireh",
    "zone_id": "ZONE-RM-01"
  },
  "preferred_language": "ar",
  "notification_preferences": {
    "preferred_contact": "email",
    "on_status_change": true,
    "on_missing_documents": true,
    "on_certificate_ready": true
  },
  "privacy_settings": {
    "share_contact_with_staff": true,
    "allow_sms_notifications": true,
    "allow_email_notifications": true
  }
}
```

Rules:

- `full_name`, contact details, address, applicant type, verification state, preferred language, notification preferences, and privacy settings are required.
- Either `national_id` or `registration_number` is required.
- Company applicants must provide `registration_number`; their `national_id` is stored as `null`.
- Duplicate `national_id` or duplicate `registration_number` is rejected.
- Supported applicant types: `citizen`, `lawyer`, `company`, `surveyor`, `authorized_representative`.
- Supported verification states: `unverified`, `verified`, `suspended`.

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
  "applicant_id": "675100000000000000000101",
  "document_type": "ownership_deed",
  "file_name": "ownership_deed.pdf",
  "storage_ref": "local-demo/ownership_deed.pdf",
  "verification_status": "pending_review"
}
```

Comment example:

```json
{
  "applicant_id": "675100000000000000000101",
  "message": "I uploaded the requested ownership deed."
}
```

Objection example:

```json
{
  "applicant_id": "675100000000000000000101",
  "reason": "Boundary information needs registrar review.",
  "supporting_document_ids": [
    "675100000000000000000701"
  ]
}
```

Rules:

- Suspended applicants cannot submit documents, comments, or objections.
- Documents store metadata and review status only; no binary file storage is implemented yet.
- Comments are recorded as audit timeline events in `performance_logs`.
- Objections are stored in `objections` and update `land_applications.objection.has_objection` when the application exists.

## Staff, Surveyors, Registrar

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `POST` | `/staff/` | Create surveyor or registrar staff account. |
| `GET` | `/staff/{staff_id}` | Retrieve staff profile, workload, and performance summary. |
| `POST` | `/applications/{application_id}/auto-assign-surveyor` | Automatically assign surveyor based on policy. |
| `PATCH` | `/applications/{application_id}/survey-milestone` | Add or update survey milestone. |
| `POST` | `/applications/{application_id}/survey-report` | Upload or register survey report metadata. |
| `PATCH` | `/applications/{application_id}/registrar-review` | Submit registrar legal review decision. |

Create staff example:

```json
{
  "staff_code": "SURV-RM-04",
  "name": "Survey Team A",
  "role": "surveyor",
  "department": "Cadastral Survey",
  "skills": [
    "boundary_survey",
    "gps_mapping"
  ],
  "coverage": {
    "zone_ids": [
      "ZONE-RM-01",
      "ZONE-RM-02"
    ],
    "geo_fence": null
  },
  "schedule": {
    "timezone": "Asia/Jerusalem",
    "shifts": [
      {
        "day": "Mon",
        "start": "08:00",
        "end": "16:00"
      }
    ],
    "on_call": false
  },
  "workload": {
    "active_tasks": 0,
    "max_tasks": 10
  },
  "contacts": {
    "email": "survey_a@example.com"
  },
  "active": true
}
```

Assignment policy:

```text
zone match + availability + workload balancing + skill match + priority + existing assigned tasks
```

Rules:

- Only active surveyors can be assigned.
- Surveyor coverage must include the application parcel zone.
- `workload.active_tasks` must be lower than `workload.max_tasks`.
- Among matching surveyors, assignment prefers the lowest current workload and existing assigned tasks.
- Assignment creates a `survey_tasks` record and stores the selected surveyor on the application.

Survey milestone example:

```json
{
  "milestone": "visit_scheduled",
  "by_staff_id": "675100000000000000000301",
  "actor_role": "surveyor",
  "notes": "Visit scheduled for Thursday.",
  "meta": {}
}
```

Survey report example:

```json
{
  "surveyor_id": "675100000000000000000301",
  "file_name": "survey_report.pdf",
  "storage_ref": "local-demo/survey_report.pdf",
  "summary": "Boundary points verified.",
  "actor_role": "surveyor"
}
```

Registrar review example:

```json
{
  "reviewer_id": "675100000000000000000302",
  "decision": "approved",
  "notes": "Survey report accepted.",
  "actor_role": "registrar"
}
```

Survey milestones:

```text
assigned -> visit_scheduled -> arrived_on_site -> survey_started -> survey_completed -> report_uploaded -> registrar_reviewed
```

Registrar review rules:

- Survey report metadata is required before registrar review.
- Registrar review stores decision, reviewer, notes, and timestamp.
- Staff-only actions validate that the referenced staff member exists, is active, and has an allowed role.

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

KPI response includes:

```json
{
  "total_applications": 5,
  "applications_by_status": {
    "submitted": 1,
    "approved": 1
  },
  "applications_by_type": {
    "ownership_transfer": 3
  },
  "pending_applications": 2,
  "approved_applications": 1,
  "rejected_applications": 1,
  "under_objection_applications": 1,
  "average_processing_time_days": 10.0,
  "certificates_issued_total": 2,
  "certificates_issued_per_month": [
    {
      "month": "2026-06",
      "count": 1
    }
  ],
  "delayed_applications": [],
  "hotspot_zones": []
}
```

Grouping endpoints return lists:

```json
[
  {
    "status": "submitted",
    "count": 3
  }
]
```

Zone analytics response:

```json
[
  {
    "zone_id": "ZONE-RM-01",
    "total": 4,
    "pending": 2,
    "approved": 1,
    "rejected": 0,
    "under_objection": 1
  }
]
```

GeoJSON response shape:

```json
{
  "type": "FeatureCollection",
  "features": []
}
```

Rules:

- Analytics are read-only and use MongoDB aggregation from existing collections.
- Pending application counts include `submitted`, `pre_checked`, `survey_required`, `surveyed`, `legal_review`, `missing_documents`, `on_hold`, and `under_objection`.
- Delayed applications default to pending applications older than 30 days; `/analytics/kpis?delayed_after_days=45` can adjust the threshold.
- Parcel geofeed features use parcel geometries from `parcels.geometry`.
- Pending heatmap features are GeoJSON `Point` features derived from pending application parcel geometry centroids.

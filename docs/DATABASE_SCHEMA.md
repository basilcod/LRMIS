# Database Schema

Database: `lrmis`

The project uses MongoDB collections with ObjectId references. Field names should stay stable across modules.

## land_applications

Stores the main registration request and workflow state.

Important fields:

- `application_id`: public unique ID, for example `LRMIS-2026-0001`.
- `application_type`: `first_registration`, `ownership_transfer`, `parcel_subdivision`, `parcel_merge`, `boundary_correction`, `certificate_request`.
- `status`: current workflow state.
- `priority`: `low`, `normal`, `high`, `urgent`.
- `applicant_ref`: applicant ObjectId, applicant type, and representative flag.
- `parcel_ref`: parcel ObjectId, parcel code, parcel number, block number, basin number, zone, area, land use, and optional GeoJSON geometry snapshot.
- `workflow`: current state, allowed next states, rules version.
- `required_documents`: document requirements and verification status.
- `timestamps`: submitted, pre-checked, surveyed, approved, issued, closed, updated.
- `assignment`: assigned surveyor and registrar references.
- `objection`: objection flag and linked objection IDs.
- `certificate_state`: certificate issued flag and linked certificate ID.
- `internal`: staff-only notes.
- `hold`: hold reason, staff actor, and timestamp when the application is on hold.
- `rejection`: rejection reason, staff actor, and timestamp when rejected.

## parcels

Stores land parcel records and GeoJSON geometry.

Important fields:

- `parcel_code`: unique parcel code.
- `parcel_number`, `block_number`, `basin_number`, `zone_id`.
- `current_owner_refs`.
- `area_sqm`.
- `land_use`.
- `registration_status`.
- `geometry`: GeoJSON `Polygon` or `MultiPolygon`.
- `dispute_state`.
- `application_id`: latest application that created or refreshed the parcel snapshot.

## applicants

Stores citizen, lawyer, company, surveyor, or representative profiles.

Important fields:

- `full_name`.
- `applicant_type`.
- `verification_state`: `unverified`, `verified`, `suspended`.
- `identity.national_id` or `identity.registration_number`.
- `identity.verified`.
- `contacts.email`, `contacts.phone`.
- `address`.
- `preferred_language`.
- `notification_preferences`.
- `privacy_settings`.
- `linked_applications`.
- `created_at`, `updated_at`.

## application_documents

Stores metadata for uploaded or registered documents.

Important fields:

- `application_id`.
- `application_object_id`.
- `applicant_id`.
- `document_type`.
- `file_name`.
- `storage_ref`.
- `verification_status`: `pending_review`, `verified`, `rejected`.
- `reviewed_by`.
- `review_notes`.
- `created_at`, `updated_at`.

## objections

Stores objections submitted against applications or parcels.

Important fields:

- `application_id`.
- `application_object_id`.
- `parcel_id`.
- `submitted_by`.
- `reason`.
- `status`: `submitted`, `under_review`, `accepted`, `rejected`, `resolved`.
- `supporting_document_ids`.
- `decision_notes`.
- `created_at`, `updated_at`.

## staff_members

Stores surveyor and registrar staff accounts.

Important fields:

- `staff_code`.
- `name`.
- `role`: `surveyor`, `registrar`, `manager`.
- `department`.
- `skills`.
- `coverage.zone_ids`.
- `coverage.geo_fence`.
- `schedule`.
- `workload.active_tasks`.
- `workload.max_tasks`.
- `active`.
- `contacts`.
- `created_at`, `updated_at`.

## survey_tasks

Stores assigned survey work.

Important fields:

- `task_id`.
- `application_id`: public application ID, for example `LRMIS-2026-0001`.
- `application_object_id`.
- `parcel_id`.
- `assigned_surveyor_id`.
- `status`.
- `milestones`.
- `field_notes`.
- `report_uploaded`.
- `created_at`, `updated_at`.

Valid milestone flow:

```text
assigned -> visit_scheduled -> arrived_on_site -> survey_started -> survey_completed -> report_uploaded -> registrar_reviewed
```

## survey_reports

Stores survey report metadata.

Important fields:

- `report_id`.
- `application_id`: public application ID.
- `application_object_id`.
- `survey_task_id`.
- `surveyor_id`.
- `file_name`.
- `storage_ref`.
- `summary`.
- `submitted_at`.
- `registrar_review_status`.
- `reviewed_by`.
- `reviewed_at`.
- `review_notes`.

## performance_logs

Stores immutable audit and workflow events.

Important fields:

- `application_id`.
- `event_stream`.
- `event_stream.type`.
- `event_stream.by`.
- `event_stream.at`.
- `event_stream.meta`.
- `computed_kpis`.

Application management events:

- `application_submitted`.
- `workflow_transition`.
- `certificate_issued`.

Applicant portal events:

- `document_added`.
- `comment_added`.
- `objection_submitted`.

Staff/survey events:

- `survey_assigned`.
- `survey_milestone_added`.
- `survey_report_uploaded`.
- `registrar_reviewed_survey`.

## certificates

Stores generated certificate metadata.

Important fields:

- `certificate_id`.
- `application_id`.
- `parcel_id`.
- `certificate_type`.
- `status`.
- `issued_to`.
- `issued_at`.
- `issued_by`.
- `verification.qr_code_url`.
- `verification.digital_signature_stub`.

## Required MongoDB Indexes

```python
db.land_applications.create_index("application_id", unique=True)
db.land_applications.create_index("status")
db.land_applications.create_index("application_type")
db.land_applications.create_index("parcel_ref.parcel_number")
db.land_applications.create_index("parcel_ref.zone_id")
db.land_applications.create_index("timestamps.submitted_at")

db.parcels.create_index("parcel_code", unique=True)
db.parcels.create_index("geometry", "2dsphere")
db.parcels.create_index("zone_id")

db.applicants.create_index("identity.national_id", unique=True)
db.staff_members.create_index("staff_code", unique=True)
db.survey_tasks.create_index("application_id")
db.certificates.create_index("certificate_id", unique=True)
```

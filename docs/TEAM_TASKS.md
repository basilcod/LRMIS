# Team Tasks

Use this checklist to divide work cleanly. Every student must also understand the group analytics and map module.

## Student 1: Land Application Management

- [ ] Define land application Pydantic schemas.
- [ ] Implement `POST /applications/` with idempotency key support.
- [ ] Implement `GET /applications/`.
- [ ] Implement `GET /applications/{application_id}`.
- [ ] Implement filtering, sorting, and pagination.
- [ ] Implement workflow transition service.
- [ ] Implement hold and reject actions with required reasons.
- [ ] Implement certificate metadata generation.
- [ ] Store parcel references and GeoJSON parcel information.
- [ ] Write audit events to `performance_logs`.
- [ ] Prepare Postman examples for application flow.

## Student 2: Applicant Portal and Profiles

- [ ] Define applicant Pydantic schemas.
- [ ] Implement `POST /applicants/`.
- [ ] Implement `GET /applicants/{applicant_id}` with restricted fields.
- [ ] Implement `GET /applicants/{applicant_id}/applications`.
- [ ] Implement document metadata endpoint.
- [ ] Implement comments endpoint.
- [ ] Implement objections endpoint.
- [ ] Implement application timeline endpoint.
- [ ] Add notification stub fields for email/SMS.
- [ ] Prepare Postman examples for applicant flow.

## Student 3: Surveyors, Registrar, and Assignment

- [ ] Define staff, survey task, and survey report schemas.
- [ ] Implement `POST /staff/`.
- [ ] Implement `GET /staff/{staff_id}`.
- [ ] Implement automatic surveyor assignment.
- [ ] Implement manual reassignment if time allows.
- [ ] Implement survey milestone updates.
- [ ] Implement survey report metadata upload.
- [ ] Implement registrar review endpoint.
- [ ] Add basic staff-only access control.
- [ ] Prepare Postman examples for survey and registrar flow.

## Group: Analytics, Map, and Visualization

- [ ] Implement `GET /analytics/kpis`.
- [ ] Implement `GET /analytics/applications-by-status`.
- [ ] Implement `GET /analytics/applications-by-zone`.
- [ ] Implement `GET /analytics/processing-time`.
- [ ] Implement `GET /analytics/surveyors`.
- [ ] Implement `GET /analytics/registrars`.
- [ ] Implement `GET /analytics/geofeeds/parcels`.
- [ ] Implement `GET /analytics/geofeeds/pending-heatmap`.
- [ ] Add Leaflet map with OpenStreetMap tiles.
- [ ] Add filters by zone, application type, and status.
- [ ] Prepare final demo script and screenshots.

# Demo Scenario

This is the main end-to-end story for the final presentation.

## Scenario: Ownership Transfer for Parcel 145

Applicant: Nour Ahmad  
Parcel: 145, Block 12, Basin 3, Zone `ZONE-RM-01`  
Application type: `ownership_transfer`

## Flow

1. Applicant creates a profile.
2. Applicant submits a land registration application.
3. System stores the application with status `submitted`.
4. Staff opens the staff console and pre-checks the application.
5. Application moves to `pre_checked`.
6. Staff determines that field verification is needed.
7. Application moves to `survey_required`.
8. System automatically assigns the best surveyor based on zone, availability, skills, workload, priority, and existing tasks.
9. Surveyor opens task list and schedules the field visit.
10. Surveyor updates milestones:
    - `assigned`
    - `visit_scheduled`
    - `arrived_on_site`
    - `survey_started`
    - `survey_completed`
    - `report_uploaded`
11. Surveyor uploads survey report metadata.
12. Application moves to `surveyed`.
13. Registrar reviews ownership documents, parcel data, survey report, and objections.
14. Application moves to `legal_review`.
15. Registrar approves the application.
16. Application moves to `approved`.
17. System generates certificate metadata.
18. Application moves to `certificate_issued`.
19. Staff closes the application.
20. Application moves to `closed`.
21. Analytics dashboard updates totals, processing time, certificate count, and workload.
22. Map shows parcel and application status through GeoJSON feed.

## Demo Proof Points

- Workflow transitions reject invalid moves.
- Required documents affect progress.
- Surveyor assignment uses a visible policy.
- Audit timeline records each important event.
- Certificate metadata is generated only after approval.
- Analytics and map are based on database data, not static screenshots.

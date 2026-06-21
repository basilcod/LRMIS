# Backend Foundation

This foundation is shared by all three backend modules. It does not implement the full project features yet.

## Files

| File | Purpose |
| --- | --- |
| `backend/app/config.py` | Loads `.env` values with `python-dotenv` and exposes cached settings. |
| `backend/app/database.py` | Creates the shared PyMongo client, returns the configured database, closes the client, and creates required indexes. |
| `backend/app/schemas/common.py` | Shared Pydantic base model and enums for application statuses, application types, applicant types, staff roles, document statuses, and survey milestones. |
| `backend/app/schemas/workflow.py` | Pydantic context/result models for workflow validation. |
| `backend/app/utils/objectid.py` | ObjectId validation, conversion, and MongoDB serialization helpers. |
| `backend/app/utils/responses.py` | Common API response helpers. |
| `backend/app/services/workflow_service.py` | Shared workflow state machine and modular transition validation functions. |
| `backend/app/services/audit_service.py` | Skeleton service for building and appending audit/performance log events. |
| `backend/app/routers/*.py` | Placeholder routers for applications, applicants, staff, and analytics. |
| `backend/seed_data.py` | Optional local seed script for sample demo data. |

## Workflow Service

Main workflow:

```text
submitted -> pre_checked -> survey_required -> surveyed -> legal_review -> approved -> certificate_issued -> closed
```

Alternative states:

```text
rejected, on_hold, missing_documents, under_objection
```

Use `validate_transition(current_status, next_status, context)` before changing application state. The context object keeps business checks modular, so each team member can pass the facts from their module without rewriting the state machine.

Example:

```python
from app.services.workflow_service import validate_transition

result = validate_transition(
    "submitted",
    "pre_checked",
    {
        "has_complete_applicant": True,
        "has_complete_parcel": True,
    },
)
```

## Placeholder Routers

Registered routers:

- `/applications`
- `/applicants`
- `/staff`
- `/analytics`

These endpoints only prove route ownership and shared app registration. The module owners should replace placeholders with real endpoints incrementally.

## Local Seed Data

The seed script is optional and writes only to the configured MongoDB database:

```bash
cd backend
python seed_data.py
```

It creates:

- one sample applicant.
- one sample parcel with GeoJSON.
- one sample surveyor staff member.
- one sample land application.

## Verification

Run from `backend/`:

```bash
python -m compileall app seed_data.py
python -c "from app.main import app; print(app.title)"
python -c "from app.services.workflow_service import validate_transition; print(validate_transition('submitted', 'pre_checked', {'has_complete_applicant': True, 'has_complete_parcel': True}).is_valid)"
```

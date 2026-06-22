from datetime import datetime, timezone
from typing import Any

from pymongo.database import Database

from app.schemas.common import StaffRole, SurveyMilestone
from app.schemas.survey import RegistrarReviewRequest
from app.services.assignment_service import get_assignment_task
from app.services.audit_service import append_audit_event, build_audit_event
from app.services.staff_service import require_staff_role
from app.utils.objectid import serialize_mongo_document, to_object_id


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _latest_report(database: Database, application_id: str) -> dict:
    reports = list(database.survey_reports.find({"application_id": application_id}))
    if not reports:
        raise ValueError("Survey report metadata is required before registrar review.")
    return reports[-1]


def submit_registrar_review(
    database: Database,
    application_id: str,
    payload: RegistrarReviewRequest,
) -> dict[str, Any]:
    require_staff_role(database, payload.reviewer_id, {StaffRole.REGISTRAR})
    task = get_assignment_task(database, application_id)
    report = _latest_report(database, application_id)
    reviewer_id = to_object_id(payload.reviewer_id)
    timestamp = utc_now()
    review = {
        "decision": payload.decision,
        "reviewer_id": payload.reviewer_id,
        "notes": payload.notes,
        "reviewed_at": timestamp,
    }
    database.survey_reports.update_one(
        {"_id": report["_id"]},
        {
            "$set": {
                "registrar_review_status": payload.decision,
                "reviewed_by": reviewer_id,
                "reviewed_at": timestamp,
                "review_notes": payload.notes,
            }
        },
    )
    milestone = {
        "type": SurveyMilestone.REGISTRAR_REVIEWED.value,
        "at": timestamp,
        "by": payload.reviewer_id,
        "meta": review,
    }
    database.survey_tasks.update_one(
        {"_id": task["_id"]},
        {
            "$set": {
                "status": SurveyMilestone.REGISTRAR_REVIEWED.value,
                "updated_at": timestamp,
            },
            "$push": {"milestones": milestone},
        },
    )
    database.land_applications.update_one(
        {"application_id": application_id},
        {
            "$set": {
                "assignment.assigned_registrar_id": reviewer_id,
                "timestamps.updated_at": timestamp,
            }
        },
    )
    append_audit_event(
        database,
        application_id,
        build_audit_event(
            event_type="registrar_reviewed_survey",
            actor_type="registrar",
            actor_id=payload.reviewer_id,
            meta={"decision": payload.decision, "notes": payload.notes},
        ),
    )
    return serialize_mongo_document(review)

from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from pymongo.database import Database

from app.schemas.common import StaffRole, SurveyMilestone
from app.schemas.survey import SurveyMilestoneRequest, SurveyReportRequest
from app.services.assignment_service import get_assignment_task
from app.services.audit_service import append_audit_event, build_audit_event
from app.services.staff_service import require_staff_role
from app.utils.objectid import serialize_mongo_document, to_object_id


SURVEY_MILESTONE_ORDER = [
    SurveyMilestone.ASSIGNED,
    SurveyMilestone.VISIT_SCHEDULED,
    SurveyMilestone.ARRIVED_ON_SITE,
    SurveyMilestone.SURVEY_STARTED,
    SurveyMilestone.SURVEY_COMPLETED,
    SurveyMilestone.REPORT_UPLOADED,
    SurveyMilestone.REGISTRAR_REVIEWED,
]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _enum_value(value: Any) -> Any:
    return value.value if hasattr(value, "value") else value


def _next_milestones(current_status: str) -> set[str]:
    current = SurveyMilestone(current_status)
    index = SURVEY_MILESTONE_ORDER.index(current)
    if index + 1 >= len(SURVEY_MILESTONE_ORDER):
        return set()
    return {SURVEY_MILESTONE_ORDER[index + 1].value}


def add_survey_milestone(
    database: Database,
    application_id: str,
    payload: SurveyMilestoneRequest,
) -> dict[str, Any]:
    require_staff_role(database, payload.by_staff_id, {StaffRole.SURVEYOR, StaffRole.REGISTRAR})
    task = get_assignment_task(database, application_id)
    target = _enum_value(payload.milestone)
    if target not in _next_milestones(task["status"]):
        raise ValueError(f"Survey milestone {target} is not allowed after {task['status']}.")

    timestamp = utc_now()
    milestone = {
        "type": target,
        "at": timestamp,
        "by": payload.by_staff_id,
        "meta": {
            "notes": payload.notes,
            **payload.meta,
        },
    }
    database.survey_tasks.update_one(
        {"_id": task["_id"]},
        {
            "$set": {"status": target, "updated_at": timestamp},
            "$push": {"milestones": milestone},
        },
    )
    append_audit_event(
        database,
        application_id,
        build_audit_event(
            event_type="survey_milestone_added",
            actor_type="staff",
            actor_id=payload.by_staff_id,
            meta={"milestone": target, "notes": payload.notes},
        ),
    )
    return {
        "application_id": application_id,
        "survey_task_id": task["task_id"],
        "status": target,
        "milestone": serialize_mongo_document(milestone),
    }


def register_survey_report(
    database: Database,
    application_id: str,
    payload: SurveyReportRequest,
) -> dict[str, Any]:
    require_staff_role(database, payload.surveyor_id, {StaffRole.SURVEYOR})
    task = get_assignment_task(database, application_id)
    if task.get("status") != SurveyMilestone.SURVEY_COMPLETED.value:
        raise ValueError("Survey report requires survey_completed milestone first.")
    surveyor_id = to_object_id(payload.surveyor_id)
    if task.get("assigned_surveyor_id") != surveyor_id:
        raise PermissionError("Only the assigned surveyor can register the survey report.")

    timestamp = utc_now()
    report = {
        "_id": ObjectId(),
        "report_id": f"REP-{application_id}",
        "application_id": application_id,
        "application_object_id": task.get("application_object_id"),
        "survey_task_id": task["_id"],
        "surveyor_id": surveyor_id,
        "file_name": payload.file_name,
        "storage_ref": payload.storage_ref,
        "summary": payload.summary,
        "submitted_at": timestamp,
        "registrar_review_status": "pending_review",
        "reviewed_by": None,
        "reviewed_at": None,
        "review_notes": None,
    }
    database.survey_reports.insert_one(report)
    report_milestone = {
        "type": SurveyMilestone.REPORT_UPLOADED.value,
        "at": timestamp,
        "by": payload.surveyor_id,
        "meta": {
            "report_id": report["report_id"],
            "file_name": payload.file_name,
        },
    }
    database.survey_tasks.update_one(
        {"_id": task["_id"]},
        {
            "$set": {
                "status": SurveyMilestone.REPORT_UPLOADED.value,
                "report_uploaded": True,
                "updated_at": timestamp,
            },
            "$push": {"milestones": report_milestone},
        },
    )
    database.land_applications.update_one(
        {"application_id": application_id},
        {
            "$set": {
                "status": "surveyed",
                "timestamps.surveyed_at": timestamp,
                "timestamps.updated_at": timestamp,
            }
        },
    )
    append_audit_event(
        database,
        application_id,
        build_audit_event(
            event_type="survey_report_uploaded",
            actor_type="surveyor",
            actor_id=payload.surveyor_id,
            meta={"report_id": report["report_id"], "file_name": payload.file_name},
        ),
    )
    response = serialize_mongo_document(report)
    response["survey_report_id"] = response["_id"]
    return response

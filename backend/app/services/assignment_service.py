from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from pymongo.database import Database

from app.schemas.common import StaffRole, SurveyMilestone
from app.schemas.survey import AutoAssignResponse
from app.services.audit_service import append_audit_event, build_audit_event
from app.utils.objectid import serialize_mongo_document


ASSIGNMENT_POLICY = "zone+workload+availability+skill+priority+existing_tasks"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _get_application(database: Database, application_id: str) -> dict:
    application = database.land_applications.find_one({"application_id": application_id})
    if not application:
        raise LookupError("Application not found.")
    return application


def _active_task_count(database: Database, surveyor_id: ObjectId) -> int:
    tasks = database.survey_tasks.find({"assigned_surveyor_id": surveyor_id})
    return len(
        [
            task
            for task in tasks
            if task.get("status") != SurveyMilestone.REGISTRAR_REVIEWED.value
        ]
    )


def _surveyor_score(database: Database, surveyor: dict) -> dict[str, Any]:
    workload = surveyor.get("workload", {})
    active_tasks = workload.get("active_tasks", 0)
    max_tasks = workload.get("max_tasks", 1)
    existing_tasks = _active_task_count(database, surveyor["_id"])
    return {
        "active_tasks": active_tasks,
        "max_tasks": max_tasks,
        "existing_assigned_tasks": existing_tasks,
        "workload_ratio": active_tasks / max_tasks,
        "total_pressure": active_tasks + existing_tasks,
    }


def _matches_assignment_policy(
    database: Database,
    surveyor: dict,
    zone_id: str,
    required_skill: str | None,
) -> tuple[bool, dict[str, Any]]:
    workload = surveyor.get("workload", {})
    score = _surveyor_score(database, surveyor)
    if surveyor.get("role") != StaffRole.SURVEYOR.value:
        return False, score
    if not surveyor.get("active", True):
        return False, score
    if zone_id not in surveyor.get("coverage", {}).get("zone_ids", []):
        return False, score
    if workload.get("active_tasks", 0) >= workload.get("max_tasks", 0):
        return False, score
    if required_skill and required_skill not in surveyor.get("skills", []):
        return False, score
    return True, score


def auto_assign_surveyor(
    database: Database,
    application_id: str,
    required_skill: str | None = None,
) -> dict[str, Any]:
    application = _get_application(database, application_id)
    zone_id = application.get("parcel_ref", {}).get("zone_id")
    if not zone_id:
        raise ValueError("Application parcel zone is required for assignment.")

    candidates = []
    for surveyor in database.staff_members.find({"role": StaffRole.SURVEYOR.value}):
        matches_policy, score = _matches_assignment_policy(
            database,
            surveyor,
            zone_id,
            required_skill,
        )
        if matches_policy:
            candidates.append((surveyor, score))

    if not candidates:
        raise LookupError("No available surveyor matches the assignment policy.")

    candidates.sort(
        key=lambda item: (
            item[1]["total_pressure"],
            item[1]["workload_ratio"],
            item[0]["staff_code"],
        )
    )
    surveyor, score = candidates[0]
    timestamp = utc_now()
    task_id = f"SURV-{application_id}"
    task = {
        "_id": ObjectId(),
        "task_id": task_id,
        "application_id": application_id,
        "application_object_id": application["_id"],
        "parcel_id": application.get("parcel_ref", {}).get("parcel_id"),
        "assigned_surveyor_id": surveyor["_id"],
        "status": SurveyMilestone.ASSIGNED.value,
        "milestones": [
            {
                "type": SurveyMilestone.ASSIGNED.value,
                "at": timestamp,
                "by": "assignment_engine",
                "meta": {
                    "policy": ASSIGNMENT_POLICY,
                    "score": score,
                },
            }
        ],
        "field_notes": [],
        "report_uploaded": False,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    database.survey_tasks.insert_one(task)
    database.staff_members.update_one(
        {"_id": surveyor["_id"]},
        {"$inc": {"workload.active_tasks": 1}, "$set": {"updated_at": timestamp}},
    )
    database.land_applications.update_one(
        {"application_id": application_id},
        {
            "$set": {
                "assignment.assigned_surveyor_id": surveyor["_id"],
                "assignment.assignment_policy": ASSIGNMENT_POLICY,
                "timestamps.updated_at": timestamp,
            }
        },
    )
    append_audit_event(
        database,
        application_id,
        build_audit_event(
            event_type="survey_assigned",
            actor_type="system",
            actor_id="assignment_engine",
            meta={
                "survey_task_id": task_id,
                "assigned_surveyor_id": str(surveyor["_id"]),
                "assigned_surveyor_code": surveyor["staff_code"],
                "policy": ASSIGNMENT_POLICY,
            },
        ),
    )
    response = AutoAssignResponse(
        application_id=application_id,
        survey_task_id=task_id,
        assigned_surveyor_id=str(surveyor["_id"]),
        assigned_surveyor_code=surveyor["staff_code"],
        policy=ASSIGNMENT_POLICY,
        score=score,
    )
    return response.model_dump()


def get_assignment_task(database: Database, application_id: str) -> dict:
    task = database.survey_tasks.find_one({"application_id": application_id})
    if not task:
        raise LookupError("Survey task not found.")
    return task

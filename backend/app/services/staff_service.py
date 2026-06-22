from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from pymongo.database import Database

from app.schemas.common import StaffRole
from app.schemas.staff import CreateStaffRequest, StaffResponse
from app.utils.objectid import serialize_mongo_document, to_object_id


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _enum_value(value: Any) -> Any:
    return value.value if hasattr(value, "value") else value


def _performance_summary(database: Database, staff_id: ObjectId, role: str) -> dict[str, int]:
    if role == StaffRole.SURVEYOR.value:
        assigned_tasks = len(list(database.survey_tasks.find({"assigned_surveyor_id": staff_id})))
        uploaded_reports = len(list(database.survey_reports.find({"surveyor_id": staff_id})))
        return {
            "assigned_tasks": assigned_tasks,
            "uploaded_reports": uploaded_reports,
        }
    reviewed_reports = len(list(database.survey_reports.find({"reviewed_by": staff_id})))
    return {
        "reviewed_reports": reviewed_reports,
    }


def _to_response(database: Database, document: dict) -> dict[str, Any]:
    serialized = serialize_mongo_document(document)
    response = StaffResponse(
        staff_id=serialized["_id"],
        staff_code=serialized["staff_code"],
        name=serialized["name"],
        role=serialized["role"],
        department=serialized["department"],
        skills=serialized.get("skills", []),
        coverage=serialized["coverage"],
        schedule=serialized["schedule"],
        workload=serialized["workload"],
        contacts=serialized.get("contacts", {}),
        active=serialized.get("active", True),
        performance_summary=_performance_summary(
            database,
            document["_id"],
            document["role"],
        ),
    )
    return response.model_dump()


def create_staff_member(database: Database, payload: CreateStaffRequest) -> dict[str, Any]:
    existing = database.staff_members.find_one({"staff_code": payload.staff_code})
    if existing:
        raise ValueError("Staff code already exists.")

    timestamp = utc_now()
    document = {
        "_id": ObjectId(),
        "staff_code": payload.staff_code,
        "name": payload.name,
        "role": _enum_value(payload.role),
        "department": payload.department,
        "skills": payload.skills,
        "coverage": payload.coverage.model_dump(),
        "schedule": payload.schedule.model_dump(),
        "workload": payload.workload.model_dump(),
        "contacts": payload.contacts,
        "active": payload.active,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    database.staff_members.insert_one(document)
    return _to_response(database, document)


def get_staff_profile(database: Database, staff_id: str) -> dict[str, Any]:
    document = database.staff_members.find_one({"_id": to_object_id(staff_id)})
    if not document:
        raise LookupError("Staff member not found.")
    return _to_response(database, document)


def require_staff_role(
    database: Database,
    staff_id: str,
    allowed_roles: set[StaffRole],
) -> dict:
    document = database.staff_members.find_one({"_id": to_object_id(staff_id)})
    if not document:
        raise LookupError("Staff member not found.")
    allowed = {_enum_value(role) for role in allowed_roles}
    if document.get("role") not in allowed:
        raise PermissionError("Staff role is not allowed for this action.")
    if not document.get("active", True):
        raise PermissionError("Inactive staff member is not allowed for this action.")
    return document

from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from pymongo.database import Database

from app.schemas.applicant import VerificationState
from app.schemas.portal import (
    AddCommentRequest,
    AddDocumentRequest,
    SubmitObjectionRequest,
)
from app.services.audit_service import append_audit_event, build_audit_event
from app.utils.objectid import serialize_mongo_document, to_object_id


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _enum_value(value: Any) -> Any:
    return value.value if hasattr(value, "value") else value


def _get_applicant_for_portal_action(database: Database, applicant_id: str) -> dict:
    applicant = database.applicants.find_one({"_id": to_object_id(applicant_id)})
    if not applicant:
        raise LookupError("Applicant not found.")
    if applicant.get("verification_state") == VerificationState.SUSPENDED.value:
        raise PermissionError("Suspended applicants cannot submit portal actions.")
    return applicant


def _get_application(database: Database, application_id: str) -> dict:
    application = database.land_applications.find_one({"application_id": application_id})
    if not application:
        raise LookupError("Application not found.")
    return application


def _audit(
    database: Database,
    application_id: str,
    event_type: str,
    applicant_id: str,
    meta: dict[str, Any],
) -> None:
    event = build_audit_event(
        event_type=event_type,
        actor_type="applicant",
        actor_id=applicant_id,
        meta=meta,
    )
    append_audit_event(database, application_id, event)


def add_document_metadata(
    database: Database,
    application_id: str,
    payload: AddDocumentRequest,
) -> dict[str, Any]:
    applicant = _get_applicant_for_portal_action(database, payload.applicant_id)
    application = _get_application(database, application_id)
    timestamp = utc_now()
    document = {
        "_id": ObjectId(),
        "application_id": application_id,
        "application_object_id": application["_id"],
        "applicant_id": applicant["_id"],
        "document_type": payload.document_type,
        "file_name": payload.file_name,
        "storage_ref": payload.storage_ref,
        "verification_status": _enum_value(payload.verification_status),
        "reviewed_by": None,
        "review_notes": None,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    database.application_documents.insert_one(document)
    _audit(
        database,
        application_id,
        "document_added",
        payload.applicant_id,
        {
            "document_id": str(document["_id"]),
            "document_type": payload.document_type,
            "file_name": payload.file_name,
        },
    )
    response = serialize_mongo_document(document)
    response["document_id"] = response["_id"]
    return response


def add_applicant_comment(
    database: Database,
    application_id: str,
    payload: AddCommentRequest,
) -> dict[str, Any]:
    _get_applicant_for_portal_action(database, payload.applicant_id)
    _get_application(database, application_id)
    comment_id = ObjectId()
    comment = {
        "comment_id": str(comment_id),
        "application_id": application_id,
        "applicant_id": payload.applicant_id,
        "message": payload.message,
        "created_at": utc_now(),
    }
    _audit(
        database,
        application_id,
        "comment_added",
        payload.applicant_id,
        {
            "comment_id": comment["comment_id"],
            "message": payload.message,
        },
    )
    return serialize_mongo_document(comment)


def submit_objection(
    database: Database,
    application_id: str,
    payload: SubmitObjectionRequest,
) -> dict[str, Any]:
    applicant = _get_applicant_for_portal_action(database, payload.applicant_id)
    application = _get_application(database, application_id)
    timestamp = utc_now()
    objection = {
        "_id": ObjectId(),
        "application_id": application_id,
        "application_object_id": application["_id"],
        "parcel_id": application.get("parcel_ref", {}).get("parcel_id"),
        "submitted_by": applicant["_id"],
        "reason": payload.reason,
        "status": "submitted",
        "supporting_document_ids": payload.supporting_document_ids,
        "decision_notes": None,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    database.objections.insert_one(objection)
    database.land_applications.update_one(
        {"application_id": application_id},
        {
            "$set": {"objection.has_objection": True},
            "$push": {"objection.objection_ids": objection["_id"]},
        },
    )
    _audit(
        database,
        application_id,
        "objection_submitted",
        payload.applicant_id,
        {
            "objection_id": str(objection["_id"]),
            "reason": payload.reason,
        },
    )
    response = serialize_mongo_document(objection)
    response["objection_id"] = response["_id"]
    return response


def get_application_timeline(
    database: Database,
    application_id: str,
) -> list[dict[str, Any]]:
    log = database.performance_logs.find_one({"application_id": application_id})
    if not log:
        return []
    events = log.get("event_stream", [])
    events = sorted(events, key=lambda event: event.get("at") or datetime.min)
    return [serialize_mongo_document(event) for event in events]

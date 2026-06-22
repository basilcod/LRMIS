from datetime import datetime, timezone
from typing import Any, Mapping

from bson import ObjectId
from pymongo.database import Database

from app.schemas.application import (
    ApplicationCreateRequest,
    ApplicationTransitionRequest,
    CertificateCreateRequest,
    HoldApplicationRequest,
    RejectApplicationRequest,
)
from app.schemas.common import ApplicationStatus, DocumentStatus
from app.schemas.workflow import WorkflowValidationContext
from app.services.audit_service import append_audit_event, build_audit_event
from app.services.workflow_service import get_allowed_next_statuses, validate_transition
from app.utils.objectid import serialize_mongo_document, to_object_id


WORKFLOW_RULES_VERSION = "v1.0"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _enum_value(value: Any) -> Any:
    return value.value if hasattr(value, "value") else value


def _allowed_values(status: ApplicationStatus | str) -> list[str]:
    return [next_status.value for next_status in get_allowed_next_statuses(status)]


def _timestamp_field_for_status(status: ApplicationStatus) -> str | None:
    fields = {
        ApplicationStatus.PRE_CHECKED: "pre_checked_at",
        ApplicationStatus.SURVEY_REQUIRED: "survey_required_at",
        ApplicationStatus.SURVEYED: "surveyed_at",
        ApplicationStatus.LEGAL_REVIEW: "legal_review_at",
        ApplicationStatus.APPROVED: "approved_at",
        ApplicationStatus.CERTIFICATE_ISSUED: "certificate_issued_at",
        ApplicationStatus.CLOSED: "closed_at",
    }
    return fields.get(status)


def _build_timestamps(timestamp: datetime) -> dict[str, datetime | None]:
    return {
        "submitted_at": timestamp,
        "pre_checked_at": None,
        "survey_required_at": None,
        "surveyed_at": None,
        "legal_review_at": None,
        "approved_at": None,
        "certificate_issued_at": None,
        "closed_at": None,
        "updated_at": timestamp,
    }


def _next_public_id(database: Database, collection_name: str, prefix: str) -> str:
    year = utc_now().year
    collection = getattr(database, collection_name)
    count = collection.count_documents({}) + 1
    return f"{prefix}-{year}-{count:04d}"


def _next_application_id(database: Database) -> str:
    return _next_public_id(database, "land_applications", "LRMIS")


def _next_certificate_id(database: Database) -> str:
    return _next_public_id(database, "certificates", "CERT")


def _parcel_code(parcel: Mapping[str, Any]) -> str:
    if parcel.get("parcel_code"):
        return str(parcel["parcel_code"])
    return (
        f"{parcel['zone_id']}-B{parcel['block_number']}-"
        f"BA{parcel['basin_number']}-P{parcel['parcel_number']}"
    )


def _save_parcel_snapshot(
    database: Database,
    application_id: str,
    payload: ApplicationCreateRequest,
    timestamp: datetime,
) -> dict[str, Any]:
    parcel = payload.parcel_ref.model_dump(exclude_none=True)
    parcel.pop("parcel_id", None)
    parcel["parcel_code"] = _parcel_code(parcel)
    existing = database.parcels.find_one({"parcel_code": parcel["parcel_code"]})
    parcel_object_id = existing["_id"] if existing else ObjectId()
    parcel["parcel_id"] = parcel_object_id

    database.parcels.update_one(
        {"parcel_code": parcel["parcel_code"]},
        {
            "$set": {
                **{key: value for key, value in parcel.items() if key != "parcel_id"},
                "updated_at": timestamp,
            },
            "$setOnInsert": {
                "_id": parcel_object_id,
                "created_at": timestamp,
                "registration_status": "pending_application",
                "dispute_state": "none",
                "application_id": application_id,
            },
        },
        upsert=True,
    )
    return parcel


def _has_complete_applicant(application: Mapping[str, Any]) -> bool:
    applicant = application.get("applicant_ref") or {}
    return bool(applicant.get("applicant_id") and applicant.get("applicant_type"))


def _has_complete_parcel(application: Mapping[str, Any]) -> bool:
    parcel = application.get("parcel_ref") or {}
    required_fields = ["parcel_number", "block_number", "basin_number", "zone_id"]
    return all(parcel.get(field) for field in required_fields)


def _has_valid_parcel_location(application: Mapping[str, Any]) -> bool:
    parcel = application.get("parcel_ref") or {}
    geometry = parcel.get("geometry") or {}
    return bool(geometry.get("type") and geometry.get("coordinates"))


def _has_ownership_documents(application: Mapping[str, Any]) -> bool:
    uploaded_statuses = {
        DocumentStatus.UPLOADED.value,
        DocumentStatus.PENDING_REVIEW.value,
        DocumentStatus.VERIFIED.value,
    }
    for document in application.get("required_documents", []):
        if document.get("document_type") not in {"ownership_deed", "sale_contract"}:
            continue
        if document.get("status") in uploaded_statuses:
            return True
    return False


def _has_survey_report(
    database: Database,
    application: Mapping[str, Any],
    request_value: bool,
) -> bool:
    if request_value:
        return True
    if application.get("survey_status", {}).get("report_exists"):
        return True
    report = database.survey_reports.find_one({"application_id": application["application_id"]}) if hasattr(database, "survey_reports") else None
    return report is not None


def _legal_review_completed(application: Mapping[str, Any], request_value: bool) -> bool:
    return bool(request_value or application.get("legal_review", {}).get("completed"))


def _transition_context(
    database: Database,
    application: Mapping[str, Any],
    request: ApplicationTransitionRequest,
) -> WorkflowValidationContext:
    return WorkflowValidationContext(
        has_complete_applicant=_has_complete_applicant(application),
        has_complete_parcel=_has_complete_parcel(application),
        has_valid_parcel_location=_has_valid_parcel_location(application),
        has_survey_report=_has_survey_report(
            database,
            application,
            request.survey_report_exists,
        ),
        has_ownership_documents=_has_ownership_documents(application),
        legal_review_completed=_legal_review_completed(
            application,
            request.legal_review_completed,
        ),
        has_objection=bool(
            request.has_objection or application.get("objection", {}).get("has_objection")
        ),
    )


def _find_application(database: Database, application_id: str) -> dict[str, Any]:
    application = database.land_applications.find_one({"application_id": application_id})
    if not application:
        raise LookupError("Application not found.")
    return application


def _serialize(document: dict[str, Any]) -> dict[str, Any]:
    return serialize_mongo_document(document)


def create_application(
    database: Database,
    payload: ApplicationCreateRequest,
    idempotency_key: str | None = None,
) -> dict[str, Any]:
    if idempotency_key:
        existing = database.land_applications.find_one({"idempotency_key": idempotency_key})
        if existing:
            return _serialize(existing)

    timestamp = utc_now()
    application_id = _next_application_id(database)
    parcel_ref = _save_parcel_snapshot(database, application_id, payload, timestamp)
    applicant_ref = payload.applicant_ref.model_dump()
    applicant_ref["applicant_id"] = to_object_id(applicant_ref["applicant_id"])

    document = {
        "_id": ObjectId(),
        "application_id": application_id,
        "application_type": _enum_value(payload.application_type),
        "status": ApplicationStatus.SUBMITTED.value,
        "priority": _enum_value(payload.priority),
        "applicant_ref": applicant_ref,
        "parcel_ref": parcel_ref,
        "description": payload.description,
        "tags": payload.tags,
        "workflow": {
            "current_state": ApplicationStatus.SUBMITTED.value,
            "allowed_next": _allowed_values(ApplicationStatus.SUBMITTED),
            "transition_rules_version": WORKFLOW_RULES_VERSION,
        },
        "required_documents": [
            document_item.model_dump() for document_item in payload.required_documents
        ],
        "timestamps": _build_timestamps(timestamp),
        "assignment": {
            "assigned_surveyor_id": None,
            "assigned_registrar_id": None,
            "assignment_policy": None,
        },
        "objection": {
            "has_objection": False,
            "objection_ids": [],
        },
        "certificate_state": {
            "certificate_issued": False,
            "certificate_id": None,
        },
        "internal": payload.internal.model_dump(),
    }
    if idempotency_key:
        document["idempotency_key"] = idempotency_key

    database.land_applications.insert_one(document)
    append_audit_event(
        database,
        application_id,
        build_audit_event(
            event_type="application_submitted",
            actor_type="applicant",
            actor_id=str(applicant_ref["applicant_id"]),
            meta={"idempotency_key": idempotency_key},
        ),
    )
    return _serialize(document)


def get_application(database: Database, application_id: str) -> dict[str, Any]:
    return _serialize(_find_application(database, application_id))


def list_applications(
    database: Database,
    page: int = 1,
    page_size: int = 20,
    filters: Mapping[str, Any] | None = None,
    sort_by: str = "timestamps.submitted_at",
    sort_order: str = "desc",
) -> dict[str, Any]:
    query = {
        key: _enum_value(value)
        for key, value in dict(filters or {}).items()
        if value is not None
    }
    direction = -1 if sort_order == "desc" else 1
    skip = (page - 1) * page_size
    cursor = (
        database.land_applications.find(query)
        .sort(sort_by, direction)
        .skip(skip)
        .limit(page_size)
    )
    return {
        "items": [_serialize(application) for application in cursor],
        "total": database.land_applications.count_documents(query),
        "page": page,
        "page_size": page_size,
    }


def _apply_transition_update(
    database: Database,
    application: Mapping[str, Any],
    target_status: ApplicationStatus,
    actor_type: str,
    actor_id: str,
    note: str | None,
    extra_set: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    application_id = str(application["application_id"])
    timestamp = utc_now()
    current_status = ApplicationStatus(application["status"])
    update_data: dict[str, Any] = {
        "status": target_status.value,
        "workflow.current_state": target_status.value,
        "workflow.allowed_next": _allowed_values(target_status),
        "timestamps.updated_at": timestamp,
    }
    timestamp_field = _timestamp_field_for_status(target_status)
    if timestamp_field:
        update_data[f"timestamps.{timestamp_field}"] = timestamp
    update_data.update(dict(extra_set or {}))

    update: dict[str, Any] = {"$set": update_data}
    if note:
        update["$push"] = {"internal.notes": note}
    database.land_applications.update_one({"application_id": application_id}, update)
    append_audit_event(
        database,
        application_id,
        build_audit_event(
            event_type="workflow_transition",
            actor_type=actor_type,
            actor_id=actor_id,
            meta={"note": note},
            previous_state=current_status.value,
            next_state=target_status.value,
        ),
    )
    return get_application(database, application_id)


def transition_application(
    database: Database,
    application_id: str,
    payload: ApplicationTransitionRequest,
) -> dict[str, Any]:
    application = _find_application(database, application_id)
    target_status = ApplicationStatus(payload.target_state)
    if target_status == ApplicationStatus.CERTIFICATE_ISSUED:
        raise ValueError("Use POST /applications/{application_id}/certificate to issue a certificate.")
    if payload.has_objection and target_status != ApplicationStatus.UNDER_OBJECTION:
        raise ValueError("Applications with objections must move to under_objection.")

    validation = validate_transition(
        application["status"],
        target_status,
        _transition_context(database, application, payload),
    )
    if not validation.is_valid:
        raise ValueError("; ".join(validation.errors))

    extra_set: dict[str, Any] = {}
    if target_status == ApplicationStatus.UNDER_OBJECTION or payload.has_objection:
        extra_set["objection.has_objection"] = True
    if target_status == ApplicationStatus.SURVEYED:
        extra_set["survey_status.report_exists"] = True
    if target_status == ApplicationStatus.APPROVED:
        extra_set["legal_review.completed"] = True
        extra_set["legal_review.completed_at"] = utc_now()

    return _apply_transition_update(
        database,
        application,
        target_status,
        payload.actor_type,
        payload.actor_id,
        payload.note,
        extra_set,
    )


def hold_application(
    database: Database,
    application_id: str,
    payload: HoldApplicationRequest,
) -> dict[str, Any]:
    application = _find_application(database, application_id)
    context = WorkflowValidationContext(hold_reason=payload.reason)
    validation = validate_transition(
        application["status"],
        ApplicationStatus.ON_HOLD,
        context,
    )
    if not validation.is_valid:
        raise ValueError("; ".join(validation.errors))
    timestamp = utc_now()
    return _apply_transition_update(
        database,
        application,
        ApplicationStatus.ON_HOLD,
        payload.actor_type,
        payload.actor_id,
        f"On hold: {payload.reason}",
        {
            "hold.reason": payload.reason,
            "hold.held_at": timestamp,
            "hold.held_by": payload.actor_id,
        },
    )


def reject_application(
    database: Database,
    application_id: str,
    payload: RejectApplicationRequest,
) -> dict[str, Any]:
    application = _find_application(database, application_id)
    context = WorkflowValidationContext(rejection_reason=payload.reason)
    validation = validate_transition(
        application["status"],
        ApplicationStatus.REJECTED,
        context,
    )
    if not validation.is_valid:
        raise ValueError("; ".join(validation.errors))
    timestamp = utc_now()
    return _apply_transition_update(
        database,
        application,
        ApplicationStatus.REJECTED,
        payload.actor_type,
        payload.actor_id,
        f"Rejected: {payload.reason}",
        {
            "rejection.reason": payload.reason,
            "rejection.rejected_at": timestamp,
            "rejection.rejected_by": payload.actor_id,
        },
    )


def _mark_certificate_issued(
    database: Database,
    application: dict[str, Any],
    certificate_id: str,
    issued_by: str,
) -> None:
    if application["status"] == ApplicationStatus.CERTIFICATE_ISSUED.value:
        return

    if application["status"] != ApplicationStatus.APPROVED.value:
        raise ValueError("A certificate can only be issued for an approved application.")

    timestamp = utc_now()
    database.land_applications.update_one(
        {"application_id": application["application_id"]},
        {
            "$set": {
                "status": ApplicationStatus.CERTIFICATE_ISSUED.value,
                "workflow.current_state": ApplicationStatus.CERTIFICATE_ISSUED.value,
                "workflow.allowed_next": _allowed_values(
                    ApplicationStatus.CERTIFICATE_ISSUED
                ),
                "timestamps.certificate_issued_at": timestamp,
                "timestamps.updated_at": timestamp,
                "certificate_state.certificate_issued": True,
                "certificate_state.certificate_id": certificate_id,
            }
        },
    )
    append_audit_event(
        database,
        application["application_id"],
        build_audit_event(
            event_type="certificate_issued",
            actor_type="registrar",
            actor_id=issued_by,
            meta={"certificate_id": certificate_id},
            previous_state=ApplicationStatus.APPROVED.value,
            next_state=ApplicationStatus.CERTIFICATE_ISSUED.value,
        ),
    )


def issue_certificate(
    database: Database,
    application_id: str,
    payload: CertificateCreateRequest,
) -> dict[str, Any]:
    application = _find_application(database, application_id)
    existing = database.certificates.find_one({"application_id": application_id})
    if existing:
        _mark_certificate_issued(
            database,
            application,
            str(existing["certificate_id"]),
            payload.issued_by,
        )
        return _serialize(existing)

    if application["status"] != ApplicationStatus.APPROVED.value:
        raise ValueError("A certificate can only be issued for an approved application.")

    certificate_request = ApplicationTransitionRequest(
        target_state=ApplicationStatus.CERTIFICATE_ISSUED,
        actor_type="registrar",
        actor_id=payload.issued_by,
    )
    validation = validate_transition(
        application["status"],
        ApplicationStatus.CERTIFICATE_ISSUED,
        _transition_context(database, application, certificate_request),
    )
    if not validation.is_valid:
        raise ValueError("; ".join(validation.errors))

    timestamp = utc_now()
    certificate_id = _next_certificate_id(database)
    certificate = {
        "_id": ObjectId(),
        "certificate_id": certificate_id,
        "application_id": application_id,
        "parcel_id": application.get("parcel_ref", {}).get("parcel_id"),
        "parcel_ref": application.get("parcel_ref", {}),
        "certificate_type": payload.certificate_type,
        "status": "issued",
        "issued_to": {
            "applicant_id": str(application["applicant_ref"]["applicant_id"]),
            "full_name": payload.issued_to_name,
        },
        "issued_at": timestamp,
        "issued_by": payload.issued_by,
        "verification": {
            "qr_code_url": f"/certificates/{certificate_id}/verify",
            "digital_signature_stub": f"signed_hash_{certificate_id}",
        },
    }
    database.certificates.insert_one(certificate)
    _mark_certificate_issued(database, application, certificate_id, payload.issued_by)
    return _serialize(certificate)

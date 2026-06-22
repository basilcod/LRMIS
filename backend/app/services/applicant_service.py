from datetime import datetime, timezone
from typing import Any

from bson import ObjectId
from pymongo.database import Database

from app.schemas.applicant import (
    ApplicantResponse,
    CreateApplicantRequest,
    VerificationState,
)
from app.utils.objectid import serialize_mongo_document, to_object_id


def _enum_value(value: Any) -> Any:
    return value.value if hasattr(value, "value") else value


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _identity_query(payload: CreateApplicantRequest) -> dict[str, str]:
    if payload.national_id:
        return {"identity.national_id": payload.national_id}
    return {"identity.registration_number": payload.registration_number}


def validate_identity_uniqueness(
    database: Database,
    payload: CreateApplicantRequest,
) -> None:
    existing = database.applicants.find_one(_identity_query(payload))
    if existing and payload.national_id:
        raise ValueError("Applicant with this national ID already exists.")
    if existing:
        raise ValueError("Applicant with this registration number already exists.")


def _to_response(document: dict) -> dict[str, Any]:
    serialized = serialize_mongo_document(document)
    response = ApplicantResponse(
        applicant_id=serialized["_id"],
        full_name=serialized["full_name"],
        applicant_type=serialized["applicant_type"],
        verification_state=serialized["verification_state"],
        identity=serialized["identity"],
        contacts=serialized["contacts"],
        address=serialized["address"],
        preferred_language=serialized["preferred_language"],
        notification_preferences=serialized["notification_preferences"],
        privacy_settings=serialized["privacy_settings"],
        linked_applications=serialized.get("linked_applications", []),
    )
    return response.model_dump()


def create_applicant_profile(
    database: Database,
    payload: CreateApplicantRequest,
) -> dict[str, Any]:
    validate_identity_uniqueness(database, payload)
    timestamp = utc_now()
    document = {
        "_id": ObjectId(),
        "full_name": payload.full_name,
        "applicant_type": _enum_value(payload.applicant_type),
        "verification_state": _enum_value(payload.verification_state),
        "identity": {
            "national_id": payload.national_id,
            "registration_number": payload.registration_number,
            "verified": payload.verification_state == VerificationState.VERIFIED,
        },
        "contacts": payload.contacts.model_dump(),
        "address": payload.address.model_dump(),
        "preferred_language": payload.preferred_language,
        "notification_preferences": payload.notification_preferences.model_dump(),
        "privacy_settings": payload.privacy_settings.model_dump(),
        "linked_applications": [],
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    database.applicants.insert_one(document)
    return _to_response(document)


def get_applicant_profile(database: Database, applicant_id: str) -> dict[str, Any]:
    document = database.applicants.find_one({"_id": to_object_id(applicant_id)})
    if not document:
        raise LookupError("Applicant not found.")
    return _to_response(document)


def list_applications_submitted_by_applicant(
    database: Database,
    applicant_id: str,
) -> list[dict[str, Any]]:
    applicant_object_id = to_object_id(applicant_id)
    applications = database.land_applications.find(
        {"applicant_ref.applicant_id": applicant_object_id}
    )
    return [serialize_mongo_document(application) for application in applications]

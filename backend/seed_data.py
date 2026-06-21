from datetime import datetime, timezone

from bson import ObjectId

from app.database import close_mongo_client, ensure_indexes, get_database
from app.schemas.common import ApplicationStatus, ApplicationType, ApplicantType, StaffRole
from app.services.workflow_service import get_allowed_next_statuses


APPLICANT_ID = ObjectId("675100000000000000000101")
PARCEL_ID = ObjectId("675100000000000000000201")
STAFF_ID = ObjectId("675100000000000000000301")
APPLICATION_ID = ObjectId("675100000000000000000001")


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def upsert_by_id(collection, document: dict) -> None:
    document_id = document["_id"]
    fields = {key: value for key, value in document.items() if key != "_id"}
    collection.update_one(
        {"_id": document_id},
        {
            "$set": fields,
            "$setOnInsert": {"_id": document_id},
        },
        upsert=True,
    )


def seed() -> None:
    db = get_database()
    ensure_indexes(db)
    timestamp = now_utc()

    upsert_by_id(
        db.applicants,
        {
            "_id": APPLICANT_ID,
            "full_name": "Nour Ahmad",
            "applicant_type": ApplicantType.CITIZEN.value,
            "identity": {
                "national_id": "400000000",
                "verified": True,
                "verification_method": "otp_stub",
                "verified_at": timestamp,
            },
            "contacts": {
                "email": "nour@example.com",
                "phone": "+970599000000",
            },
            "address": {
                "city": "Ramallah",
                "neighborhood": "Al Tireh",
                "zone_id": "ZONE-RM-01",
            },
            "preferences": {
                "preferred_contact": "email",
                "language": "ar",
                "notifications": {
                    "on_status_change": True,
                    "on_missing_documents": True,
                    "on_certificate_ready": True,
                },
            },
            "stats": {
                "total_applications": 1,
                "approved_applications": 0,
                "pending_applications": 1,
            },
            "created_at": timestamp,
        },
    )

    upsert_by_id(
        db.parcels,
        {
            "_id": PARCEL_ID,
            "parcel_code": "RM-Z01-B12-P145",
            "parcel_number": "145",
            "block_number": "12",
            "basin_number": "3",
            "zone_id": "ZONE-RM-01",
            "current_owner_refs": [
                {
                    "applicant_id": APPLICANT_ID,
                    "share": "1/1",
                }
            ],
            "area_sqm": 850.5,
            "land_use": "residential",
            "registration_status": "registered",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [35.2001, 31.9021],
                        [35.2015, 31.9021],
                        [35.2015, 31.9030],
                        [35.2001, 31.9030],
                        [35.2001, 31.9021],
                    ]
                ],
            },
            "address_hint": "Ramallah - Al Tireh",
            "dispute_state": "none",
            "created_at": timestamp,
            "updated_at": timestamp,
        },
    )

    upsert_by_id(
        db.staff_members,
        {
            "_id": STAFF_ID,
            "staff_code": "SURV-RM-04",
            "name": "Survey Team A",
            "role": StaffRole.SURVEYOR.value,
            "department": "Cadastral Survey",
            "skills": ["boundary_survey", "parcel_subdivision", "gps_mapping"],
            "coverage": {
                "zone_ids": ["ZONE-RM-01", "ZONE-RM-02"],
                "geo_fence": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [35.19, 31.89],
                            [35.22, 31.89],
                            [35.22, 31.92],
                            [35.19, 31.92],
                            [35.19, 31.89],
                        ]
                    ],
                },
            },
            "schedule": {
                "timezone": "Asia/Jerusalem",
                "shifts": [
                    {"day": "Mon", "start": "08:00", "end": "16:00"},
                    {"day": "Tue", "start": "08:00", "end": "16:00"},
                    {"day": "Wed", "start": "08:00", "end": "16:00"},
                ],
                "on_call": False,
            },
            "workload": {
                "active_tasks": 0,
                "max_tasks": 10,
            },
            "contacts": {
                "phone": "+970599111111",
                "email": "survey_a@example.com",
            },
            "active": True,
            "created_at": timestamp,
        },
    )

    upsert_by_id(
        db.land_applications,
        {
            "_id": APPLICATION_ID,
            "application_id": "LRMIS-2026-0001",
            "application_type": ApplicationType.OWNERSHIP_TRANSFER.value,
            "status": ApplicationStatus.SUBMITTED.value,
            "priority": "normal",
            "applicant_ref": {
                "applicant_id": APPLICANT_ID,
                "applicant_type": ApplicantType.CITIZEN.value,
                "submitted_by_representative": False,
            },
            "parcel_ref": {
                "parcel_id": PARCEL_ID,
                "parcel_number": "145",
                "block_number": "12",
                "basin_number": "3",
                "zone_id": "ZONE-RM-01",
            },
            "description": "Ownership transfer application for parcel 145, block 12.",
            "tags": ["ownership_transfer", "requires_legal_review"],
            "workflow": {
                "current_state": ApplicationStatus.SUBMITTED.value,
                "allowed_next": [
                    status.value
                    for status in get_allowed_next_statuses(ApplicationStatus.SUBMITTED)
                ],
                "transition_rules_version": "v1.0",
            },
            "required_documents": [
                {
                    "document_type": "ownership_deed",
                    "required": True,
                    "status": "pending_review",
                },
                {
                    "document_type": "id_copy",
                    "required": True,
                    "status": "pending_review",
                },
            ],
            "timestamps": {
                "submitted_at": timestamp,
                "pre_checked_at": None,
                "survey_required_at": None,
                "surveyed_at": None,
                "legal_review_at": None,
                "approved_at": None,
                "certificate_issued_at": None,
                "closed_at": None,
                "updated_at": timestamp,
            },
            "assignment": {
                "assigned_surveyor_id": None,
                "assigned_registrar_id": None,
                "assignment_policy": None,
            },
            "objection": {
                "has_objection": False,
                "objection_ids": [],
            },
            "internal": {
                "notes": ["Seed application for the final demo workflow."],
                "visibility": "staff_only",
            },
        },
    )

    print("Seeded LRMIS sample applicant, parcel, staff member, and application.")


if __name__ == "__main__":
    try:
        seed()
    finally:
        close_mongo_client()

from datetime import datetime, timedelta, timezone
from typing import Any

from bson import ObjectId

from app.database import close_mongo_client, ensure_indexes, get_database
from app.schemas.common import (
    ApplicantType,
    ApplicationStatus,
    ApplicationType,
    StaffRole,
    SurveyMilestone,
)
from app.services.workflow_service import get_allowed_next_statuses


APPLICANT_ID = ObjectId("675100000000000000000101")
SURVEYOR_ID = ObjectId("675100000000000000000301")
REGISTRAR_ID = ObjectId("675100000000000000000302")

PARCEL_145_ID = ObjectId("675100000000000000000201")
PARCEL_146_ID = ObjectId("675100000000000000000202")
PARCEL_147_ID = ObjectId("675100000000000000000203")

SURVEY_APPLICATION_OBJECT_ID = ObjectId("675100000000000000000001")
APPROVED_APPLICATION_OBJECT_ID = ObjectId("675100000000000000000002")
ISSUED_APPLICATION_OBJECT_ID = ObjectId("675100000000000000000003")

SURVEY_TASK_OBJECT_ID = ObjectId("675100000000000000000401")
APPROVED_TASK_OBJECT_ID = ObjectId("675100000000000000000402")
APPROVED_REPORT_OBJECT_ID = ObjectId("675100000000000000000501")
ISSUED_CERTIFICATE_OBJECT_ID = ObjectId("675100000000000000000601")


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def polygon(min_lng: float, min_lat: float, max_lng: float, max_lat: float) -> dict[str, Any]:
    return {
        "type": "Polygon",
        "coordinates": [
            [
                [min_lng, min_lat],
                [max_lng, min_lat],
                [max_lng, max_lat],
                [min_lng, max_lat],
                [min_lng, min_lat],
            ]
        ],
    }


def upsert_by_id(collection, document: dict[str, Any]) -> None:
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


def upsert_one(collection, query: dict[str, Any], document: dict[str, Any]) -> None:
    fields = {key: value for key, value in document.items() if key not in query}
    collection.update_one(
        query,
        {
            "$set": fields,
            "$setOnInsert": query,
        },
        upsert=True,
    )


def workflow(status: ApplicationStatus) -> dict[str, Any]:
    return {
        "current_state": status.value,
        "allowed_next": [next_status.value for next_status in get_allowed_next_statuses(status)],
        "transition_rules_version": "v1.0",
    }


def timestamps(submitted_days_ago: int, status_dates: dict[str, datetime | None]) -> dict[str, datetime | None]:
    submitted_at = now_utc() - timedelta(days=submitted_days_ago)
    return {
        "submitted_at": submitted_at,
        "pre_checked_at": status_dates.get("pre_checked_at"),
        "survey_required_at": status_dates.get("survey_required_at"),
        "surveyed_at": status_dates.get("surveyed_at"),
        "legal_review_at": status_dates.get("legal_review_at"),
        "approved_at": status_dates.get("approved_at"),
        "certificate_issued_at": status_dates.get("certificate_issued_at"),
        "closed_at": status_dates.get("closed_at"),
        "updated_at": status_dates.get("updated_at") or now_utc(),
    }


def base_parcel(parcel_id: ObjectId, parcel_number: str, parcel_code: str, geometry: dict[str, Any]) -> dict[str, Any]:
    timestamp = now_utc()
    return {
        "_id": parcel_id,
        "parcel_code": parcel_code,
        "parcel_number": parcel_number,
        "block_number": "12",
        "basin_number": "3",
        "zone_id": "ZONE-RM-01",
        "current_owner_refs": [{"applicant_id": APPLICANT_ID, "share": "1/1"}],
        "area_sqm": 840.5,
        "land_use": "residential",
        "registration_status": "registered",
        "geometry": geometry,
        "address_hint": "Ramallah - Al Tireh",
        "dispute_state": "none",
        "created_at": timestamp,
        "updated_at": timestamp,
    }


def parcel_ref(parcel: dict[str, Any]) -> dict[str, Any]:
    return {
        "parcel_id": parcel["_id"],
        "parcel_code": parcel["parcel_code"],
        "parcel_number": parcel["parcel_number"],
        "block_number": parcel["block_number"],
        "basin_number": parcel["basin_number"],
        "zone_id": parcel["zone_id"],
        "geometry": parcel["geometry"],
        "area_sqm": parcel["area_sqm"],
        "land_use": parcel["land_use"],
    }


def seed() -> None:
    db = get_database()
    ensure_indexes(db)
    timestamp = now_utc()

    parcel_145 = base_parcel(
        PARCEL_145_ID,
        "145",
        "ZONE-RM-01-B12-BA3-P145",
        polygon(35.2001, 31.9021, 35.2015, 31.9030),
    )
    parcel_146 = base_parcel(
        PARCEL_146_ID,
        "146",
        "ZONE-RM-01-B12-BA3-P146",
        polygon(35.2018, 31.9022, 35.2032, 31.9031),
    )
    parcel_147 = base_parcel(
        PARCEL_147_ID,
        "147",
        "ZONE-RM-01-B12-BA3-P147",
        polygon(35.2035, 31.9024, 35.2049, 31.9033),
    )

    upsert_by_id(
        db.applicants,
        {
            "_id": APPLICANT_ID,
            "full_name": "Nour Ahmad",
            "applicant_type": ApplicantType.CITIZEN.value,
            "verification_state": "verified",
            "identity": {
                "national_id": "400000000",
                "registration_number": None,
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
            "preferred_language": "ar",
            "notification_preferences": {
                "preferred_contact": "email",
                "on_status_change": True,
                "on_missing_documents": True,
                "on_certificate_ready": True,
            },
            "privacy_settings": {
                "share_contact_with_staff": True,
                "allow_sms_notifications": True,
                "allow_email_notifications": True,
            },
            "linked_applications": [
                "LRMIS-2026-0001",
                "LRMIS-2026-0002",
                "LRMIS-2026-0003",
            ],
            "created_at": timestamp,
            "updated_at": timestamp,
        },
    )

    for parcel in [parcel_145, parcel_146, parcel_147]:
        upsert_by_id(db.parcels, parcel)

    upsert_by_id(
        db.staff_members,
        {
            "_id": SURVEYOR_ID,
            "staff_code": "SURV-RM-04",
            "name": "Survey Team A",
            "role": StaffRole.SURVEYOR.value,
            "department": "Cadastral Survey",
            "skills": ["boundary_survey", "parcel_subdivision", "gps_mapping"],
            "coverage": {
                "zone_ids": ["ZONE-RM-01", "ZONE-RM-02"],
                "geo_fence": polygon(35.19, 31.89, 35.22, 31.92),
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
            "workload": {"active_tasks": 1, "max_tasks": 10},
            "contacts": {
                "phone": "+970599111111",
                "email": "survey_a@example.com",
            },
            "active": True,
            "created_at": timestamp,
            "updated_at": timestamp,
        },
    )

    upsert_by_id(
        db.staff_members,
        {
            "_id": REGISTRAR_ID,
            "staff_code": "REG-RM-01",
            "name": "Registrar 01",
            "role": StaffRole.REGISTRAR.value,
            "department": "Land Registry",
            "skills": ["legal_review", "certificate_issuance"],
            "coverage": {"zone_ids": ["ZONE-RM-01"], "geo_fence": None},
            "schedule": {
                "timezone": "Asia/Jerusalem",
                "shifts": [{"day": "Sun", "start": "08:00", "end": "16:00"}],
                "on_call": False,
            },
            "workload": {"active_tasks": 1, "max_tasks": 8},
            "contacts": {
                "phone": "+970599222222",
                "email": "registrar@example.com",
            },
            "active": True,
            "created_at": timestamp,
            "updated_at": timestamp,
        },
    )

    survey_submitted = timestamp - timedelta(days=6)
    approved_submitted = timestamp - timedelta(days=18)
    issued_submitted = timestamp - timedelta(days=28)

    applications = [
        {
            "_id": SURVEY_APPLICATION_OBJECT_ID,
            "application_id": "LRMIS-2026-0001",
            "application_type": ApplicationType.OWNERSHIP_TRANSFER.value,
            "status": ApplicationStatus.SURVEY_REQUIRED.value,
            "priority": "normal",
            "applicant_ref": {
                "applicant_id": APPLICANT_ID,
                "applicant_type": ApplicantType.CITIZEN.value,
                "submitted_by_representative": False,
            },
            "parcel_ref": parcel_ref(parcel_145),
            "description": "Ownership transfer application ready for survey task demo.",
            "tags": ["demo", "survey_required"],
            "workflow": workflow(ApplicationStatus.SURVEY_REQUIRED),
            "required_documents": [
                {"document_type": "ownership_deed", "required": True, "status": "uploaded"},
                {"document_type": "id_copy", "required": True, "status": "verified"},
            ],
            "timestamps": {
                "submitted_at": survey_submitted,
                "pre_checked_at": survey_submitted + timedelta(days=1),
                "survey_required_at": survey_submitted + timedelta(days=2),
                "surveyed_at": None,
                "legal_review_at": None,
                "approved_at": None,
                "certificate_issued_at": None,
                "closed_at": None,
                "updated_at": timestamp,
            },
            "assignment": {
                "assigned_surveyor_id": SURVEYOR_ID,
                "assigned_registrar_id": None,
                "assignment_policy": "zone+workload+availability+skill+priority+existing_tasks",
            },
            "objection": {"has_objection": False, "objection_ids": []},
            "certificate_state": {"certificate_issued": False, "certificate_id": None},
            "internal": {
                "notes": ["Seed survey task for the final demo workflow."],
                "visibility": "staff_only",
            },
        },
        {
            "_id": APPROVED_APPLICATION_OBJECT_ID,
            "application_id": "LRMIS-2026-0002",
            "application_type": ApplicationType.OWNERSHIP_TRANSFER.value,
            "status": ApplicationStatus.APPROVED.value,
            "priority": "high",
            "applicant_ref": {
                "applicant_id": APPLICANT_ID,
                "applicant_type": ApplicantType.CITIZEN.value,
                "submitted_by_representative": False,
            },
            "parcel_ref": parcel_ref(parcel_146),
            "description": "Approved ownership transfer ready for certificate issuance.",
            "tags": ["demo", "certificate_ready"],
            "workflow": workflow(ApplicationStatus.APPROVED),
            "required_documents": [
                {"document_type": "ownership_deed", "required": True, "status": "verified"},
                {"document_type": "sale_contract", "required": True, "status": "verified"},
            ],
            "timestamps": timestamps(
                18,
                {
                    "pre_checked_at": approved_submitted + timedelta(days=1),
                    "survey_required_at": approved_submitted + timedelta(days=2),
                    "surveyed_at": approved_submitted + timedelta(days=7),
                    "legal_review_at": approved_submitted + timedelta(days=10),
                    "approved_at": approved_submitted + timedelta(days=12),
                    "updated_at": timestamp,
                },
            ),
            "assignment": {
                "assigned_surveyor_id": SURVEYOR_ID,
                "assigned_registrar_id": REGISTRAR_ID,
                "assignment_policy": "zone+workload+availability+skill+priority+existing_tasks",
            },
            "survey_status": {"report_exists": True},
            "legal_review": {"completed": True, "completed_at": approved_submitted + timedelta(days=12)},
            "objection": {"has_objection": False, "objection_ids": []},
            "certificate_state": {"certificate_issued": False, "certificate_id": None},
            "internal": {
                "notes": ["Use this application in the frontend Certificate View."],
                "visibility": "staff_only",
            },
        },
        {
            "_id": ISSUED_APPLICATION_OBJECT_ID,
            "application_id": "LRMIS-2026-0003",
            "application_type": ApplicationType.FIRST_REGISTRATION.value,
            "status": ApplicationStatus.CERTIFICATE_ISSUED.value,
            "priority": "normal",
            "applicant_ref": {
                "applicant_id": APPLICANT_ID,
                "applicant_type": ApplicantType.CITIZEN.value,
                "submitted_by_representative": False,
            },
            "parcel_ref": parcel_ref(parcel_147),
            "description": "Certificate issued sample for analytics and demo proof.",
            "tags": ["demo", "certificate_issued"],
            "workflow": workflow(ApplicationStatus.CERTIFICATE_ISSUED),
            "required_documents": [
                {"document_type": "ownership_deed", "required": True, "status": "verified"},
            ],
            "timestamps": timestamps(
                28,
                {
                    "pre_checked_at": issued_submitted + timedelta(days=1),
                    "survey_required_at": issued_submitted + timedelta(days=2),
                    "surveyed_at": issued_submitted + timedelta(days=8),
                    "legal_review_at": issued_submitted + timedelta(days=11),
                    "approved_at": issued_submitted + timedelta(days=15),
                    "certificate_issued_at": issued_submitted + timedelta(days=17),
                    "updated_at": timestamp,
                },
            ),
            "assignment": {
                "assigned_surveyor_id": SURVEYOR_ID,
                "assigned_registrar_id": REGISTRAR_ID,
                "assignment_policy": "zone+workload+availability+skill+priority+existing_tasks",
            },
            "survey_status": {"report_exists": True},
            "legal_review": {"completed": True, "completed_at": issued_submitted + timedelta(days=15)},
            "objection": {"has_objection": False, "objection_ids": []},
            "certificate_state": {
                "certificate_issued": True,
                "certificate_id": "CERT-2026-0001",
            },
            "internal": {
                "notes": ["Issued certificate sample for analytics dashboard."],
                "visibility": "staff_only",
            },
        },
    ]

    for application in applications:
        upsert_by_id(db.land_applications, application)

    upsert_by_id(
        db.survey_tasks,
        {
            "_id": SURVEY_TASK_OBJECT_ID,
            "task_id": "SURV-LRMIS-2026-0001",
            "application_id": "LRMIS-2026-0001",
            "application_object_id": SURVEY_APPLICATION_OBJECT_ID,
            "parcel_id": PARCEL_145_ID,
            "assigned_surveyor_id": SURVEYOR_ID,
            "status": SurveyMilestone.ASSIGNED.value,
            "milestones": [
                {
                    "type": SurveyMilestone.ASSIGNED.value,
                    "at": timestamp,
                    "by": "assignment_engine",
                    "meta": {"policy": "seeded_demo_assignment"},
                }
            ],
            "field_notes": [],
            "report_uploaded": False,
            "created_at": timestamp,
            "updated_at": timestamp,
        },
    )

    upsert_by_id(
        db.survey_tasks,
        {
            "_id": APPROVED_TASK_OBJECT_ID,
            "task_id": "SURV-LRMIS-2026-0002",
            "application_id": "LRMIS-2026-0002",
            "application_object_id": APPROVED_APPLICATION_OBJECT_ID,
            "parcel_id": PARCEL_146_ID,
            "assigned_surveyor_id": SURVEYOR_ID,
            "status": SurveyMilestone.REGISTRAR_REVIEWED.value,
            "milestones": [
                {"type": SurveyMilestone.ASSIGNED.value, "at": approved_submitted, "by": "assignment_engine", "meta": {}},
                {"type": SurveyMilestone.SURVEY_COMPLETED.value, "at": approved_submitted + timedelta(days=7), "by": str(SURVEYOR_ID), "meta": {}},
                {"type": SurveyMilestone.REPORT_UPLOADED.value, "at": approved_submitted + timedelta(days=8), "by": str(SURVEYOR_ID), "meta": {}},
                {"type": SurveyMilestone.REGISTRAR_REVIEWED.value, "at": approved_submitted + timedelta(days=11), "by": str(REGISTRAR_ID), "meta": {"decision": "approved"}},
            ],
            "field_notes": ["Boundary points verified."],
            "report_uploaded": True,
            "created_at": approved_submitted,
            "updated_at": timestamp,
        },
    )

    upsert_by_id(
        db.survey_reports,
        {
            "_id": APPROVED_REPORT_OBJECT_ID,
            "report_id": "REP-LRMIS-2026-0002",
            "application_id": "LRMIS-2026-0002",
            "application_object_id": APPROVED_APPLICATION_OBJECT_ID,
            "survey_task_id": APPROVED_TASK_OBJECT_ID,
            "surveyor_id": SURVEYOR_ID,
            "file_name": "survey_report_0002.pdf",
            "storage_ref": "demo/survey_report_0002.pdf",
            "summary": "Boundary points verified and parcel geometry accepted.",
            "submitted_at": approved_submitted + timedelta(days=8),
            "registrar_review_status": "approved",
            "reviewed_by": REGISTRAR_ID,
            "reviewed_at": approved_submitted + timedelta(days=11),
            "review_notes": "Survey report accepted for legal approval.",
        },
    )

    upsert_by_id(
        db.certificates,
        {
            "_id": ISSUED_CERTIFICATE_OBJECT_ID,
            "certificate_id": "CERT-2026-0001",
            "application_id": "LRMIS-2026-0003",
            "parcel_id": PARCEL_147_ID,
            "parcel_ref": parcel_ref(parcel_147),
            "certificate_type": "ownership_certificate",
            "status": "issued",
            "issued_to": {
                "applicant_id": str(APPLICANT_ID),
                "full_name": "Nour Ahmad",
            },
            "issued_at": timestamp - timedelta(days=10),
            "issued_by": str(REGISTRAR_ID),
            "verification": {
                "qr_code_url": "/certificates/CERT-2026-0001/verify",
                "digital_signature_stub": "signed_hash_CERT-2026-0001",
            },
        },
    )

    for app_id, events in {
        "LRMIS-2026-0001": [
            {"type": "application_submitted", "previous_state": None, "next_state": "submitted"},
            {"type": "workflow_transition", "previous_state": "submitted", "next_state": "pre_checked"},
            {"type": "workflow_transition", "previous_state": "pre_checked", "next_state": "survey_required"},
            {"type": "survey_assigned", "previous_state": None, "next_state": None},
        ],
        "LRMIS-2026-0002": [
            {"type": "survey_report_uploaded", "previous_state": None, "next_state": "surveyed"},
            {"type": "registrar_reviewed_survey", "previous_state": None, "next_state": None},
            {"type": "workflow_transition", "previous_state": "legal_review", "next_state": "approved"},
        ],
        "LRMIS-2026-0003": [
            {"type": "certificate_issued", "previous_state": "approved", "next_state": "certificate_issued"},
        ],
    }.items():
        upsert_one(
            db.performance_logs,
            {"application_id": app_id},
            {
                "application_id": app_id,
                "event_stream": [
                    {
                        "type": event["type"],
                        "by": {"actor_type": "seed", "actor_id": "seed_data"},
                        "at": timestamp,
                        "meta": {"source": "demo_seed"},
                        **({"previous_state": event["previous_state"]} if event["previous_state"] else {}),
                        **({"next_state": event["next_state"]} if event["next_state"] else {}),
                    }
                    for event in events
                ],
                "computed_kpis": {},
            },
        )

    print(
        "Seeded demo data: applicant, parcels, surveyor, registrar, survey task, "
        "approved certificate-ready application, issued certificate, and analytics records."
    )


if __name__ == "__main__":
    try:
        seed()
    finally:
        close_mongo_client()

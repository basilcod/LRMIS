from copy import deepcopy

import pytest
from bson import ObjectId

from app.schemas.application import (
    ApplicantRef,
    ApplicationCreateRequest,
    ApplicationTransitionRequest,
    CertificateCreateRequest,
    DocumentItem,
    GeoJSONGeometry,
    HoldApplicationRequest,
    ParcelRef,
    RejectApplicationRequest,
)
from app.schemas.common import ApplicantType, ApplicationStatus, ApplicationType, DocumentStatus
from app.services.application_service import (
    create_application,
    get_application,
    hold_application,
    issue_certificate,
    list_applications,
    reject_application,
    transition_application,
)


class InsertOneResult:
    def __init__(self, inserted_id):
        self.inserted_id = inserted_id


class UpdateResult:
    def __init__(self, matched_count=0, modified_count=0, upserted_id=None):
        self.matched_count = matched_count
        self.modified_count = modified_count
        self.upserted_id = upserted_id


def get_path(document, path):
    value = document
    for part in path.split("."):
        if not isinstance(value, dict) or part not in value:
            return None
        value = value[part]
    return value


def set_path(document, path, value):
    target = document
    parts = path.split(".")
    for part in parts[:-1]:
        target = target.setdefault(part, {})
    target[parts[-1]] = value


def push_path(document, path, value):
    target = document
    parts = path.split(".")
    for part in parts[:-1]:
        target = target.setdefault(part, {})
    target.setdefault(parts[-1], []).append(value)


def matches(document, query):
    return all(get_path(document, key) == value for key, value in query.items())


class FakeCursor:
    def __init__(self, documents):
        self.documents = documents

    def sort(self, key, direction):
        self.documents.sort(
            key=lambda document: get_path(document, key) or "",
            reverse=direction == -1,
        )
        return self

    def skip(self, count):
        self.documents = self.documents[count:]
        return self

    def limit(self, count):
        self.documents = self.documents[:count]
        return self

    def __iter__(self):
        return iter(deepcopy(self.documents))


class FakeCollection:
    def __init__(self):
        self.documents = []

    def insert_one(self, document):
        stored = deepcopy(document)
        stored.setdefault("_id", ObjectId())
        self.documents.append(stored)
        return InsertOneResult(stored["_id"])

    def find_one(self, query):
        for document in self.documents:
            if matches(document, query):
                return deepcopy(document)
        return None

    def find(self, query=None):
        query = query or {}
        return FakeCursor(
            [deepcopy(document) for document in self.documents if matches(document, query)]
        )

    def count_documents(self, query):
        return len([document for document in self.documents if matches(document, query)])

    def update_one(self, query, update, upsert=False):
        for document in self.documents:
            if matches(document, query):
                for key, value in update.get("$set", {}).items():
                    set_path(document, key, value)
                for key, value in update.get("$setOnInsert", {}).items():
                    if get_path(document, key) is None:
                        set_path(document, key, value)
                for key, value in update.get("$push", {}).items():
                    push_path(document, key, value)
                return UpdateResult(matched_count=1, modified_count=1)

        if not upsert:
            return UpdateResult()

        new_document = deepcopy(query)
        for key, value in update.get("$setOnInsert", {}).items():
            set_path(new_document, key, value)
        for key, value in update.get("$set", {}).items():
            set_path(new_document, key, value)
        for key, value in update.get("$push", {}).items():
            push_path(new_document, key, value)
        new_document.setdefault("_id", ObjectId())
        self.documents.append(new_document)
        return UpdateResult(upserted_id=new_document["_id"])


class FakeDatabase:
    def __init__(self):
        self.land_applications = FakeCollection()
        self.parcels = FakeCollection()
        self.certificates = FakeCollection()
        self.performance_logs = FakeCollection()


def application_payload(
    parcel_number="145",
    geometry=None,
    documents=None,
):
    return ApplicationCreateRequest(
        application_type=ApplicationType.OWNERSHIP_TRANSFER,
        applicant_ref=ApplicantRef(
            applicant_id="675100000000000000000101",
            applicant_type=ApplicantType.CITIZEN,
        ),
        parcel_ref=ParcelRef(
            parcel_number=parcel_number,
            block_number="12",
            basin_number="3",
            zone_id="ZONE-RM-01",
            geometry=geometry,
            area_sqm=840.5,
            land_use="residential",
        ),
        description="Ownership transfer for parcel 145.",
        required_documents=documents or [],
    )


def polygon_geometry():
    return GeoJSONGeometry(
        type="Polygon",
        coordinates=[
            [
                [35.2001, 31.9001],
                [35.2008, 31.9001],
                [35.2008, 31.9008],
                [35.2001, 31.9001],
            ]
        ],
    )


def ownership_documents():
    return [
        DocumentItem(
            document_type="ownership_deed",
            status=DocumentStatus.UPLOADED,
        )
    ]


def create_ready_application(db):
    return create_application(
        db,
        application_payload(
            geometry=polygon_geometry(),
            documents=ownership_documents(),
        ),
    )


def test_create_application_saves_parcel_snapshot_and_is_idempotent():
    db = FakeDatabase()
    payload = application_payload(geometry=polygon_geometry())

    created = create_application(db, payload, idempotency_key="student-demo-1")
    repeated = create_application(db, payload, idempotency_key="student-demo-1")

    assert created["application_id"] == "LRMIS-2026-0001"
    assert repeated["application_id"] == created["application_id"]
    assert created["status"] == "submitted"
    assert created["workflow"]["allowed_next"] == [
        "pre_checked",
        "missing_documents",
        "rejected",
    ]
    assert db.parcels.documents[0]["parcel_code"] == "ZONE-RM-01-B12-BA3-P145"
    assert db.performance_logs.documents[0]["event_stream"][0]["type"] == "application_submitted"


def test_list_and_get_application_return_serialized_documents():
    db = FakeDatabase()
    create_application(db, application_payload(parcel_number="145"))
    create_application(db, application_payload(parcel_number="146"))

    listed = list_applications(db, page=1, page_size=10, filters={"status": "submitted"})
    fetched = get_application(db, "LRMIS-2026-0002")

    assert listed["total"] == 2
    assert [item["application_id"] for item in listed["items"]] == [
        "LRMIS-2026-0002",
        "LRMIS-2026-0001",
    ]
    assert fetched["parcel_ref"]["parcel_number"] == "146"
    assert isinstance(fetched["_id"], str)


def test_workflow_transition_validates_required_context_and_updates_audit_log():
    db = FakeDatabase()
    create_application(db, application_payload(documents=ownership_documents()))

    with pytest.raises(ValueError, match="Parcel location"):
        transition_application(
            db,
            "LRMIS-2026-0001",
            ApplicationTransitionRequest(
                target_state=ApplicationStatus.SURVEY_REQUIRED,
                actor_id="registrar_09",
            ),
        )

    db.land_applications.documents[0]["parcel_ref"]["geometry"] = polygon_geometry().model_dump()
    pre_checked = transition_application(
        db,
        "LRMIS-2026-0001",
        ApplicationTransitionRequest(
            target_state=ApplicationStatus.PRE_CHECKED,
            actor_id="registrar_09",
            note="Initial check completed.",
        ),
    )
    survey_required = transition_application(
        db,
        "LRMIS-2026-0001",
        ApplicationTransitionRequest(
            target_state=ApplicationStatus.SURVEY_REQUIRED,
            actor_id="registrar_09",
        ),
    )

    assert pre_checked["status"] == "pre_checked"
    assert survey_required["status"] == "survey_required"
    assert "Initial check completed." in survey_required["internal"]["notes"]
    assert db.performance_logs.documents[0]["event_stream"][-1]["type"] == "workflow_transition"


def test_full_approval_certificate_and_close_flow():
    db = FakeDatabase()
    create_ready_application(db)

    for target_state, extra in [
        (ApplicationStatus.PRE_CHECKED, {}),
        (ApplicationStatus.SURVEY_REQUIRED, {}),
        (ApplicationStatus.SURVEYED, {"survey_report_exists": True}),
        (ApplicationStatus.LEGAL_REVIEW, {}),
        (ApplicationStatus.APPROVED, {"legal_review_completed": True}),
    ]:
        transition_application(
            db,
            "LRMIS-2026-0001",
            ApplicationTransitionRequest(
                target_state=target_state,
                actor_id="registrar_09",
                **extra,
            ),
        )

    certificate = issue_certificate(
        db,
        "LRMIS-2026-0001",
        CertificateCreateRequest(
            issued_by="registrar_09",
            issued_to_name="Nour Ahmad",
        ),
    )
    duplicate = issue_certificate(
        db,
        "LRMIS-2026-0001",
        CertificateCreateRequest(
            issued_by="registrar_09",
            issued_to_name="Nour Ahmad",
        ),
    )
    closed = transition_application(
        db,
        "LRMIS-2026-0001",
        ApplicationTransitionRequest(
            target_state=ApplicationStatus.CLOSED,
            actor_id="registrar_09",
        ),
    )

    assert certificate["certificate_id"] == "CERT-2026-0001"
    assert duplicate["certificate_id"] == certificate["certificate_id"]
    assert closed["status"] == "closed"
    assert db.land_applications.documents[0]["certificate_state"]["certificate_issued"] is True


def test_certificate_requires_approved_application():
    db = FakeDatabase()
    create_application(db, application_payload())

    with pytest.raises(ValueError, match="approved application"):
        issue_certificate(
            db,
            "LRMIS-2026-0001",
            CertificateCreateRequest(
                issued_by="registrar_09",
                issued_to_name="Nour Ahmad",
            ),
        )


def test_hold_and_reject_use_workflow_validation_reasons():
    db = FakeDatabase()
    create_ready_application(db)
    transition_application(
        db,
        "LRMIS-2026-0001",
        ApplicationTransitionRequest(
            target_state=ApplicationStatus.PRE_CHECKED,
            actor_id="registrar_09",
        ),
    )
    transition_application(
        db,
        "LRMIS-2026-0001",
        ApplicationTransitionRequest(
            target_state=ApplicationStatus.SURVEY_REQUIRED,
            actor_id="registrar_09",
        ),
    )

    held = hold_application(
        db,
        "LRMIS-2026-0001",
        HoldApplicationRequest(reason="Waiting for field visit access.", actor_id="registrar_09"),
    )
    rejected = reject_application(
        db,
        "LRMIS-2026-0001",
        RejectApplicationRequest(reason="Applicant did not resolve survey conflict.", actor_id="registrar_09"),
    )

    assert held["status"] == "on_hold"
    assert held["hold"]["reason"] == "Waiting for field visit access."
    assert rejected["status"] == "rejected"
    assert rejected["rejection"]["reason"] == "Applicant did not resolve survey conflict."

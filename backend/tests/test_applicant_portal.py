from copy import deepcopy

import pytest
from bson import ObjectId

from app.schemas.applicant import (
    Address,
    ContactDetails,
    CreateApplicantRequest,
    NotificationPreferences,
    PrivacySettings,
    VerificationState,
)
from app.schemas.common import ApplicantType
from app.schemas.portal import (
    AddCommentRequest,
    AddDocumentRequest,
    SubmitObjectionRequest,
)
from app.services.applicant_service import (
    create_applicant_profile,
    get_applicant_profile,
    list_applications_submitted_by_applicant,
)
from app.services.portal_service import (
    add_applicant_comment,
    add_document_metadata,
    get_application_timeline,
    submit_objection,
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

    def find(self, query):
        return [deepcopy(document) for document in self.documents if matches(document, query)]

    def update_one(self, query, update, upsert=False):
        for document in self.documents:
            if matches(document, query):
                for key, value in update.get("$set", {}).items():
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
        self.applicants = FakeCollection()
        self.land_applications = FakeCollection()
        self.application_documents = FakeCollection()
        self.objections = FakeCollection()
        self.performance_logs = FakeCollection()


def applicant_request(
    national_id="400000000",
    verification_state=VerificationState.UNVERIFIED,
):
    return CreateApplicantRequest(
        full_name="Nour Ahmad",
        applicant_type=ApplicantType.CITIZEN,
        verification_state=verification_state,
        national_id=national_id,
        contacts=ContactDetails(
            email="nour@example.com",
            phone="+970599000000",
        ),
        address=Address(
            city="Ramallah",
            neighborhood="Al Tireh",
            zone_id="ZONE-RM-01",
        ),
        preferred_language="ar",
        notification_preferences=NotificationPreferences(),
        privacy_settings=PrivacySettings(),
    )


def test_create_applicant_rejects_duplicate_national_id():
    db = FakeDatabase()
    create_applicant_profile(db, applicant_request())

    with pytest.raises(ValueError, match="national ID"):
        create_applicant_profile(db, applicant_request())


def test_company_applicant_requires_registration_number():
    with pytest.raises(ValueError, match="registration_number"):
        CreateApplicantRequest(
            full_name="Land Holdings Company",
            applicant_type=ApplicantType.COMPANY,
            national_id="400000099",
            contacts=ContactDetails(
                email="office@landholdings.example",
                phone="+970599000099",
            ),
            address=Address(
                city="Ramallah",
                zone_id="ZONE-RM-01",
            ),
            notification_preferences=NotificationPreferences(),
            privacy_settings=PrivacySettings(),
        )


def test_verified_applicant_sets_identity_verified_flag():
    db = FakeDatabase()

    applicant = create_applicant_profile(
        db,
        applicant_request(
            national_id="400000002",
            verification_state=VerificationState.VERIFIED,
        ),
    )

    assert applicant["verification_state"] == "verified"
    assert applicant["identity"]["verified"] is True


def test_applicant_portal_flow_writes_metadata_objection_and_timeline():
    db = FakeDatabase()
    applicant = create_applicant_profile(db, applicant_request())
    application_id = "LRMIS-2026-0001"

    db.land_applications.insert_one(
        {
            "_id": ObjectId("675100000000000000000001"),
            "application_id": application_id,
            "applicant_ref": {"applicant_id": ObjectId(applicant["applicant_id"])},
            "objection": {"has_objection": False, "objection_ids": []},
        }
    )

    profile = get_applicant_profile(db, applicant["applicant_id"])
    assert profile["full_name"] == "Nour Ahmad"
    assert profile["identity"]["national_id"] == "400000000"
    applications = list_applications_submitted_by_applicant(db, applicant["applicant_id"])
    assert applications[0]["application_id"] == application_id

    document = add_document_metadata(
        db,
        application_id,
        AddDocumentRequest(
            applicant_id=applicant["applicant_id"],
            document_type="ownership_deed",
            file_name="ownership_deed.pdf",
            storage_ref="local-demo/ownership_deed.pdf",
        ),
    )
    comment = add_applicant_comment(
        db,
        application_id,
        AddCommentRequest(
            applicant_id=applicant["applicant_id"],
            message="I uploaded the requested ownership deed.",
        ),
    )
    objection = submit_objection(
        db,
        application_id,
        SubmitObjectionRequest(
            applicant_id=applicant["applicant_id"],
            reason="Boundary information needs registrar review.",
            supporting_document_ids=[document["document_id"]],
        ),
    )
    timeline = get_application_timeline(db, application_id)

    assert document["verification_status"] == "pending_review"
    assert comment["message"] == "I uploaded the requested ownership deed."
    assert objection["status"] == "submitted"
    assert db.land_applications.documents[0]["objection"]["has_objection"] is True
    assert [event["type"] for event in timeline] == [
        "document_added",
        "comment_added",
        "objection_submitted",
    ]


def test_suspended_applicant_cannot_submit_portal_actions():
    db = FakeDatabase()
    applicant = create_applicant_profile(
        db,
        applicant_request(
            national_id="400000001",
            verification_state=VerificationState.SUSPENDED,
        ),
    )

    with pytest.raises(PermissionError, match="Suspended applicants"):
        add_applicant_comment(
            db,
            "LRMIS-2026-0001",
            AddCommentRequest(
                applicant_id=applicant["applicant_id"],
                message="This should not be accepted.",
            ),
        )

from copy import deepcopy

import pytest
from bson import ObjectId

from app.schemas.common import StaffRole, SurveyMilestone
from app.schemas.staff import (
    CoverageZone,
    CreateStaffRequest,
    StaffSchedule,
    Workload,
)
from app.schemas.survey import (
    RegistrarReviewRequest,
    SurveyMilestoneRequest,
    SurveyReportRequest,
)
from app.services.assignment_service import auto_assign_surveyor
from app.services.registrar_service import submit_registrar_review
from app.services.staff_service import create_staff_member, get_staff_profile
from app.services.survey_service import add_survey_milestone, register_survey_report


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


def matches_value(actual, expected):
    if isinstance(actual, list):
        return expected in actual
    return actual == expected


def matches(document, query):
    return all(matches_value(get_path(document, key), value) for key, value in query.items())


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
        return [deepcopy(document) for document in self.documents if matches(document, query)]

    def update_one(self, query, update, upsert=False):
        for document in self.documents:
            if matches(document, query):
                for key, value in update.get("$set", {}).items():
                    set_path(document, key, value)
                for key, value in update.get("$inc", {}).items():
                    current = get_path(document, key) or 0
                    set_path(document, key, current + value)
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
        self.staff_members = FakeCollection()
        self.land_applications = FakeCollection()
        self.survey_tasks = FakeCollection()
        self.survey_reports = FakeCollection()
        self.performance_logs = FakeCollection()


def staff_request(code, role=StaffRole.SURVEYOR, active_tasks=0, zones=None, active=True):
    return CreateStaffRequest(
        staff_code=code,
        name=f"{code} Name",
        role=role,
        department="Cadastral Survey",
        skills=["boundary_survey", "gps_mapping"],
        coverage=CoverageZone(zone_ids=zones or ["ZONE-RM-01"]),
        schedule=StaffSchedule(
            timezone="Asia/Jerusalem",
            shifts=[{"day": "Mon", "start": "08:00", "end": "16:00"}],
            on_call=False,
        ),
        workload=Workload(active_tasks=active_tasks, max_tasks=10),
        contacts={"email": f"{code.lower()}@example.com"},
        active=active,
    )


def insert_application(db, application_id="LRMIS-2026-0001"):
    db.land_applications.insert_one(
        {
            "_id": ObjectId("675100000000000000000001"),
            "application_id": application_id,
            "priority": "normal",
            "status": "survey_required",
            "parcel_ref": {
                "parcel_id": ObjectId("675100000000000000000201"),
                "zone_id": "ZONE-RM-01",
            },
            "assignment": {
                "assigned_surveyor_id": None,
                "assigned_registrar_id": None,
                "assignment_policy": None,
            },
        }
    )


def test_create_staff_and_get_profile_summary():
    db = FakeDatabase()
    staff = create_staff_member(db, staff_request("SURV-RM-04"))

    profile = get_staff_profile(db, staff["staff_id"])

    assert profile["staff_code"] == "SURV-RM-04"
    assert profile["role"] == "surveyor"
    assert profile["workload"]["active_tasks"] == 0
    assert profile["performance_summary"]["assigned_tasks"] == 0


def test_auto_assign_prefers_matching_active_surveyor_with_lowest_workload():
    db = FakeDatabase()
    insert_application(db)
    busy = create_staff_member(db, staff_request("SURV-RM-09", active_tasks=5))
    best = create_staff_member(db, staff_request("SURV-RM-04", active_tasks=1))
    create_staff_member(db, staff_request("SURV-NB-01", zones=["ZONE-NB-01"]))

    assignment = auto_assign_surveyor(db, "LRMIS-2026-0001")

    assert assignment["assigned_surveyor_id"] == best["staff_id"]
    assert assignment["assigned_surveyor_id"] != busy["staff_id"]
    assert assignment["policy"] == "zone+workload+availability+skill+priority+existing_tasks"
    assert db.land_applications.documents[0]["assignment"]["assigned_surveyor_id"] == ObjectId(best["staff_id"])
    assert db.staff_members.documents[1]["workload"]["active_tasks"] == 2


def test_auto_assign_rejects_when_no_available_surveyor():
    db = FakeDatabase()
    insert_application(db)
    create_staff_member(db, staff_request("SURV-RM-10", active_tasks=10))
    create_staff_member(db, staff_request("SURV-NB-01", zones=["ZONE-NB-01"]))

    with pytest.raises(LookupError, match="No available surveyor"):
        auto_assign_surveyor(db, "LRMIS-2026-0001")


def test_survey_milestone_report_and_registrar_review_flow():
    db = FakeDatabase()
    insert_application(db)
    surveyor = create_staff_member(db, staff_request("SURV-RM-04"))
    registrar = create_staff_member(db, staff_request("REG-RM-01", role=StaffRole.REGISTRAR))
    auto_assign_surveyor(db, "LRMIS-2026-0001")

    milestone = None
    for next_milestone in [
        SurveyMilestone.VISIT_SCHEDULED,
        SurveyMilestone.ARRIVED_ON_SITE,
        SurveyMilestone.SURVEY_STARTED,
        SurveyMilestone.SURVEY_COMPLETED,
    ]:
        milestone = add_survey_milestone(
            db,
            "LRMIS-2026-0001",
            SurveyMilestoneRequest(
                milestone=next_milestone,
                by_staff_id=surveyor["staff_id"],
                notes=f"{next_milestone.value} done.",
            ),
        )
    report = register_survey_report(
        db,
        "LRMIS-2026-0001",
        SurveyReportRequest(
            surveyor_id=surveyor["staff_id"],
            file_name="survey_report.pdf",
            storage_ref="local-demo/survey_report.pdf",
            summary="Boundary points verified.",
        ),
    )
    review = submit_registrar_review(
        db,
        "LRMIS-2026-0001",
        RegistrarReviewRequest(
            reviewer_id=registrar["staff_id"],
            decision="approved",
            notes="Survey report accepted.",
        ),
    )

    assert milestone["status"] == "survey_completed"
    assert report["registrar_review_status"] == "pending_review"
    assert db.land_applications.documents[0]["status"] == "surveyed"
    assert review["decision"] == "approved"
    assert db.survey_tasks.documents[0]["status"] == "registrar_reviewed"


def test_survey_report_requires_completed_survey_milestone():
    db = FakeDatabase()
    insert_application(db)
    surveyor = create_staff_member(db, staff_request("SURV-RM-04"))
    auto_assign_surveyor(db, "LRMIS-2026-0001")

    with pytest.raises(ValueError, match="survey_completed"):
        register_survey_report(
            db,
            "LRMIS-2026-0001",
            SurveyReportRequest(
                surveyor_id=surveyor["staff_id"],
                file_name="survey_report.pdf",
                storage_ref="local-demo/survey_report.pdf",
                summary="Boundary points verified.",
            ),
        )

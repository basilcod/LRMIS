from copy import deepcopy
from datetime import datetime, timedelta, timezone

from bson import ObjectId

from app.services.analytics_service import (
    get_applications_by_status,
    get_applications_by_zone,
    get_kpis,
    get_parcels_geofeed,
    get_pending_heatmap,
    get_processing_time,
    get_registrar_workload,
    get_surveyor_workload,
)


NOW = datetime(2026, 6, 22, tzinfo=timezone.utc)


def get_path(document, path):
    value = document
    for part in path.split("."):
        if not isinstance(value, dict) or part not in value:
            return None
        value = value[part]
    return value


def matches(document, query):
    for key, expected in query.items():
        actual = get_path(document, key)
        if isinstance(expected, dict):
            if "$in" in expected and actual not in expected["$in"]:
                return False
            if "$nin" in expected and actual in expected["$nin"]:
                return False
            if "$lt" in expected and not actual < expected["$lt"]:
                return False
            continue
        if actual != expected:
            return False
    return True


class FakeCollection:
    def __init__(self, name, documents, database=None):
        self.name = name
        self.documents = documents
        self.database = database
        self.aggregate_pipelines = []

    def find(self, query=None, projection=None):
        query = query or {}
        return [deepcopy(document) for document in self.documents if matches(document, query)]

    def aggregate(self, pipeline):
        self.aggregate_pipelines.append(deepcopy(pipeline))
        if self.name == "land_applications" and pipeline and "$facet" in pipeline[0]:
            return [self._kpi_facet(pipeline[0]["$facet"])]
        if self.name == "land_applications" and self._has_date_diff(pipeline):
            return self._processing_time()
        if self.name == "land_applications" and self._groups_by(pipeline, "$status"):
            return self._group_count("status", "status")
        if self.name == "land_applications" and self._groups_by(pipeline, "$application_type"):
            return self._group_count("application_type", "application_type")
        if self.name == "land_applications" and self._groups_by(pipeline, "$parcel_ref.zone_id"):
            return self._zone_groups()
        if self.name == "certificates":
            return self._certificates_per_month()
        if self.name == "survey_tasks":
            return self._surveyor_workload()
        if self.name == "survey_reports":
            return self._registrar_workload()
        return []

    def _groups_by(self, pipeline, field):
        return any(stage.get("$group", {}).get("_id") == field for stage in pipeline)

    def _has_date_diff(self, pipeline):
        return "$dateDiff" in str(pipeline)

    def _group_count(self, field, output_key):
        counts = {}
        for document in self.documents:
            key = get_path(document, field)
            counts[key] = counts.get(key, 0) + 1
        return [
            {output_key: key, "count": count}
            for key, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
        ]

    def _zone_groups(self):
        pending_statuses = {
            "submitted",
            "pre_checked",
            "survey_required",
            "surveyed",
            "legal_review",
            "missing_documents",
            "on_hold",
            "under_objection",
        }
        zones = {}
        for document in self.documents:
            zone_id = get_path(document, "parcel_ref.zone_id") or "unknown"
            bucket = zones.setdefault(
                zone_id,
                {
                    "zone_id": zone_id,
                    "total": 0,
                    "pending": 0,
                    "approved": 0,
                    "rejected": 0,
                    "under_objection": 0,
                },
            )
            bucket["total"] += 1
            status = document["status"]
            if status in pending_statuses:
                bucket["pending"] += 1
            if status == "approved":
                bucket["approved"] += 1
            if status == "rejected":
                bucket["rejected"] += 1
            if status == "under_objection":
                bucket["under_objection"] += 1
        return sorted(zones.values(), key=lambda item: (-item["total"], item["zone_id"]))

    def _processing_time(self):
        groups = {}
        for document in self.documents:
            submitted_at = get_path(document, "timestamps.submitted_at")
            closed_at = get_path(document, "timestamps.closed_at")
            if not submitted_at or not closed_at:
                continue
            days = (closed_at - submitted_at).total_seconds() / 86400
            group = groups.setdefault(document["application_type"], [])
            group.append(days)
        return [
            {
                "application_type": application_type,
                "average_days": round(sum(days) / len(days), 2),
                "count": len(days),
            }
            for application_type, days in sorted(groups.items())
        ]

    def _certificates_per_month(self):
        counts = {}
        for document in self.documents:
            month = document["issued_at"].strftime("%Y-%m")
            counts[month] = counts.get(month, 0) + 1
        return [
            {"month": month, "count": count}
            for month, count in sorted(counts.items())
        ]

    def _surveyor_workload(self):
        staff_by_id = {
            document["_id"]: document
            for document in self.database.staff_members.documents
        }
        groups = {}
        for task in self.documents:
            surveyor_id = task["assigned_surveyor_id"]
            staff = staff_by_id[surveyor_id]
            bucket = groups.setdefault(
                surveyor_id,
                {
                    "staff_id": str(surveyor_id),
                    "staff_code": staff["staff_code"],
                    "name": staff["name"],
                    "assigned_tasks": 0,
                    "completed_tasks": 0,
                    "active_tasks": staff["workload"]["active_tasks"],
                    "max_tasks": staff["workload"]["max_tasks"],
                },
            )
            bucket["assigned_tasks"] += 1
            if task["status"] in {"report_uploaded", "registrar_reviewed"}:
                bucket["completed_tasks"] += 1
        return list(groups.values())

    def _registrar_workload(self):
        staff_by_id = {
            document["_id"]: document
            for document in self.database.staff_members.documents
        }
        groups = {}
        for report in self.documents:
            reviewer_id = report.get("reviewed_by")
            if reviewer_id is None:
                continue
            staff = staff_by_id[reviewer_id]
            bucket = groups.setdefault(
                reviewer_id,
                {
                    "staff_id": str(reviewer_id),
                    "staff_code": staff["staff_code"],
                    "name": staff["name"],
                    "reviewed_reports": 0,
                    "approved_reports": 0,
                    "rejected_reports": 0,
                },
            )
            bucket["reviewed_reports"] += 1
            if report["registrar_review_status"] == "approved":
                bucket["approved_reports"] += 1
            if report["registrar_review_status"] == "rejected":
                bucket["rejected_reports"] += 1
        return list(groups.values())

    def _kpi_facet(self, _facet):
        by_status = self._group_count("status", "status")
        by_type = self._group_count("application_type", "application_type")
        zone_groups = self._zone_groups()
        pending_statuses = {
            "submitted",
            "pre_checked",
            "survey_required",
            "surveyed",
            "legal_review",
            "missing_documents",
            "on_hold",
            "under_objection",
        }
        delayed = [
            {
                "application_id": document["application_id"],
                "status": document["status"],
                "zone_id": get_path(document, "parcel_ref.zone_id"),
                "submitted_at": get_path(document, "timestamps.submitted_at"),
            }
            for document in self.documents
            if document["status"] in pending_statuses
            and get_path(document, "timestamps.submitted_at") < NOW - timedelta(days=30)
        ]
        return {
            "total": [{"count": len(self.documents)}],
            "by_status": by_status,
            "by_type": by_type,
            "state_counts": [
                {
                    "pending": sum(1 for item in self.documents if item["status"] in pending_statuses),
                    "approved": sum(1 for item in self.documents if item["status"] == "approved"),
                    "rejected": sum(1 for item in self.documents if item["status"] == "rejected"),
                    "under_objection": sum(1 for item in self.documents if item["status"] == "under_objection"),
                }
            ],
            "delayed": delayed,
            "hotspot_zones": zone_groups[:10],
        }


class FakeDatabase:
    def __init__(self):
        surveyor_id = ObjectId("675100000000000000000301")
        registrar_id = ObjectId("675100000000000000000302")
        self.staff_members = FakeCollection(
            "staff_members",
            [
                {
                    "_id": surveyor_id,
                    "staff_code": "SURV-RM-04",
                    "name": "Survey Team A",
                    "role": "surveyor",
                    "workload": {"active_tasks": 2, "max_tasks": 10},
                },
                {
                    "_id": registrar_id,
                    "staff_code": "REG-RM-01",
                    "name": "Registrar 01",
                    "role": "registrar",
                    "workload": {"active_tasks": 1, "max_tasks": 8},
                },
            ],
            self,
        )
        self.land_applications = FakeCollection(
            "land_applications",
            [
                application("LRMIS-2026-0001", "submitted", "ownership_transfer", "ZONE-RM-01", 40),
                application("LRMIS-2026-0002", "approved", "first_registration", "ZONE-RM-01", 20),
                application("LRMIS-2026-0003", "rejected", "ownership_transfer", "ZONE-NB-01", 10),
                application("LRMIS-2026-0004", "under_objection", "boundary_correction", "ZONE-RM-01", 35),
                application(
                    "LRMIS-2026-0005",
                    "closed",
                    "ownership_transfer",
                    "ZONE-HB-01",
                    20,
                    closed_after_days=10,
                ),
            ],
            self,
        )
        self.parcels = FakeCollection(
            "parcels",
            [
                {
                    "parcel_code": "ZONE-RM-01-B12-BA3-P145",
                    "zone_id": "ZONE-RM-01",
                    "parcel_number": "145",
                    "geometry": polygon_geometry(),
                    "area_sqm": 840.5,
                    "land_use": "residential",
                }
            ],
            self,
        )
        self.certificates = FakeCollection(
            "certificates",
            [
                {"certificate_id": "CERT-2026-0001", "issued_at": datetime(2026, 6, 5, tzinfo=timezone.utc)},
                {"certificate_id": "CERT-2026-0002", "issued_at": datetime(2026, 5, 1, tzinfo=timezone.utc)},
            ],
            self,
        )
        self.survey_tasks = FakeCollection(
            "survey_tasks",
            [
                {"assigned_surveyor_id": surveyor_id, "status": "assigned"},
                {"assigned_surveyor_id": surveyor_id, "status": "report_uploaded"},
            ],
            self,
        )
        self.survey_reports = FakeCollection(
            "survey_reports",
            [
                {"reviewed_by": registrar_id, "registrar_review_status": "approved"},
                {"reviewed_by": registrar_id, "registrar_review_status": "rejected"},
                {"reviewed_by": None, "registrar_review_status": "pending_review"},
            ],
            self,
        )


def polygon_geometry():
    return {
        "type": "Polygon",
        "coordinates": [
            [
                [35.2001, 31.9001],
                [35.2008, 31.9001],
                [35.2008, 31.9008],
                [35.2001, 31.9001],
            ]
        ],
    }


def application(application_id, status, application_type, zone_id, submitted_days_ago, closed_after_days=None):
    submitted_at = NOW - timedelta(days=submitted_days_ago)
    closed_at = submitted_at + timedelta(days=closed_after_days) if closed_after_days else None
    return {
        "application_id": application_id,
        "status": status,
        "application_type": application_type,
        "parcel_ref": {
            "zone_id": zone_id,
            "parcel_number": "145",
            "geometry": polygon_geometry(),
        },
        "timestamps": {
            "submitted_at": submitted_at,
            "closed_at": closed_at,
        },
    }


def test_kpis_include_required_counts_and_aggregation_pipeline():
    db = FakeDatabase()

    kpis = get_kpis(db, now=NOW)

    assert kpis["total_applications"] == 5
    assert kpis["applications_by_status"]["submitted"] == 1
    assert kpis["applications_by_type"]["ownership_transfer"] == 3
    assert kpis["pending_applications"] == 2
    assert kpis["approved_applications"] == 1
    assert kpis["rejected_applications"] == 1
    assert kpis["under_objection_applications"] == 1
    assert kpis["certificates_issued_total"] == 2
    assert kpis["certificates_issued_per_month"] == [
        {"month": "2026-05", "count": 1},
        {"month": "2026-06", "count": 1},
    ]
    assert [item["application_id"] for item in kpis["delayed_applications"]] == [
        "LRMIS-2026-0001",
        "LRMIS-2026-0004",
    ]
    assert db.land_applications.aggregate_pipelines
    assert any("$facet" in stage for stage in db.land_applications.aggregate_pipelines[0])


def test_status_zone_and_processing_time_analytics():
    db = FakeDatabase()

    by_status = get_applications_by_status(db)
    by_zone = get_applications_by_zone(db)
    processing = get_processing_time(db)

    status_counts = {item["status"]: item["count"] for item in by_status}
    assert status_counts == {
        "approved": 1,
        "closed": 1,
        "rejected": 1,
        "submitted": 1,
        "under_objection": 1,
    }
    assert by_zone[0]["zone_id"] == "ZONE-RM-01"
    assert by_zone[0]["total"] == 3
    assert processing == [
        {
            "application_type": "ownership_transfer",
            "average_days": 10.0,
            "count": 1,
        }
    ]


def test_staff_workload_analytics_use_lookup_and_unwind():
    db = FakeDatabase()

    surveyors = get_surveyor_workload(db)
    registrars = get_registrar_workload(db)

    assert surveyors == [
        {
            "staff_id": "675100000000000000000301",
            "staff_code": "SURV-RM-04",
            "name": "Survey Team A",
            "assigned_tasks": 2,
            "completed_tasks": 1,
            "active_tasks": 2,
            "max_tasks": 10,
        }
    ]
    assert registrars[0]["reviewed_reports"] == 2
    assert registrars[0]["approved_reports"] == 1
    assert any("$lookup" in stage for stage in db.survey_tasks.aggregate_pipelines[0])
    assert any("$unwind" in stage for stage in db.survey_reports.aggregate_pipelines[0])


def test_geofeeds_return_feature_collections():
    db = FakeDatabase()

    parcels = get_parcels_geofeed(db)
    heatmap = get_pending_heatmap(db)

    assert parcels["type"] == "FeatureCollection"
    assert parcels["features"][0]["geometry"]["type"] == "Polygon"
    assert parcels["features"][0]["properties"]["parcel_code"] == "ZONE-RM-01-B12-BA3-P145"
    assert heatmap["type"] == "FeatureCollection"
    assert {feature["geometry"]["type"] for feature in heatmap["features"]} == {"Point"}
    assert {feature["properties"]["application_id"] for feature in heatmap["features"]} == {
        "LRMIS-2026-0001",
        "LRMIS-2026-0004",
    }

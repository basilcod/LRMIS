from datetime import datetime, timedelta, timezone
from typing import Any, Iterable, Mapping

from pymongo.database import Database

from app.schemas.common import ApplicationStatus, StaffRole
from app.utils.objectid import serialize_mongo_value


PENDING_STATUSES = [
    ApplicationStatus.SUBMITTED.value,
    ApplicationStatus.PRE_CHECKED.value,
    ApplicationStatus.SURVEY_REQUIRED.value,
    ApplicationStatus.SURVEYED.value,
    ApplicationStatus.LEGAL_REVIEW.value,
    ApplicationStatus.MISSING_DOCUMENTS.value,
    ApplicationStatus.ON_HOLD.value,
    ApplicationStatus.UNDER_OBJECTION.value,
]

HOTSPOT_STATUSES = [
    ApplicationStatus.UNDER_OBJECTION.value,
    ApplicationStatus.ON_HOLD.value,
    ApplicationStatus.MISSING_DOCUMENTS.value,
    ApplicationStatus.REJECTED.value,
]

COMPLETED_SURVEY_STATUSES = [
    "report_uploaded",
    "registrar_reviewed",
]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _aggregate(collection: Any, pipeline: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [serialize_mongo_value(item) for item in collection.aggregate(pipeline)]


def _count_map(items: Iterable[Mapping[str, Any]], key: str) -> dict[str, int]:
    return {str(item[key]): int(item.get("count", 0)) for item in items if item.get(key) is not None}


def _first_count(items: list[Mapping[str, Any]]) -> int:
    if not items:
        return 0
    return int(items[0].get("count", 0))


def _round_days(value: Any) -> float:
    if value is None:
        return 0
    return round(float(value), 2)


def get_applications_by_status(database: Database) -> list[dict[str, Any]]:
    pipeline = [
        {"$group": {"_id": "$status", "count": {"$sum": 1}}},
        {"$project": {"_id": 0, "status": "$_id", "count": 1}},
        {"$sort": {"count": -1, "status": 1}},
    ]
    return _aggregate(database.land_applications, pipeline)


def get_applications_by_type(database: Database) -> list[dict[str, Any]]:
    pipeline = [
        {"$group": {"_id": "$application_type", "count": {"$sum": 1}}},
        {"$project": {"_id": 0, "application_type": "$_id", "count": 1}},
        {"$sort": {"count": -1, "application_type": 1}},
    ]
    return _aggregate(database.land_applications, pipeline)


def get_applications_by_zone(database: Database) -> list[dict[str, Any]]:
    pipeline = [
        {
            "$group": {
                "_id": "$parcel_ref.zone_id",
                "total": {"$sum": 1},
                "pending": {
                    "$sum": {
                        "$cond": [{"$in": ["$status", PENDING_STATUSES]}, 1, 0]
                    }
                },
                "approved": {
                    "$sum": {
                        "$cond": [
                            {"$eq": ["$status", ApplicationStatus.APPROVED.value]},
                            1,
                            0,
                        ]
                    }
                },
                "rejected": {
                    "$sum": {
                        "$cond": [
                            {"$eq": ["$status", ApplicationStatus.REJECTED.value]},
                            1,
                            0,
                        ]
                    }
                },
                "under_objection": {
                    "$sum": {
                        "$cond": [
                            {
                                "$eq": [
                                    "$status",
                                    ApplicationStatus.UNDER_OBJECTION.value,
                                ]
                            },
                            1,
                            0,
                        ]
                    }
                },
            }
        },
        {
            "$project": {
                "_id": 0,
                "zone_id": {"$ifNull": ["$_id", "unknown"]},
                "total": 1,
                "pending": 1,
                "approved": 1,
                "rejected": 1,
                "under_objection": 1,
            }
        },
        {"$sort": {"total": -1, "zone_id": 1}},
    ]
    return _aggregate(database.land_applications, pipeline)


def get_processing_time(database: Database) -> list[dict[str, Any]]:
    pipeline = [
        {
            "$match": {
                "timestamps.submitted_at": {"$ne": None},
                "timestamps.closed_at": {"$ne": None},
            }
        },
        {
            "$project": {
                "_id": 0,
                "application_type": 1,
                "processing_days": {
                    "$dateDiff": {
                        "startDate": "$timestamps.submitted_at",
                        "endDate": "$timestamps.closed_at",
                        "unit": "day",
                    }
                },
            }
        },
        {
            "$group": {
                "_id": "$application_type",
                "average_days": {"$avg": "$processing_days"},
                "count": {"$sum": 1},
            }
        },
        {
            "$project": {
                "_id": 0,
                "application_type": "$_id",
                "average_days": {"$round": ["$average_days", 2]},
                "count": 1,
            }
        },
        {"$sort": {"application_type": 1}},
    ]
    results = _aggregate(database.land_applications, pipeline)
    for item in results:
        item["average_days"] = _round_days(item.get("average_days"))
    return results


def get_certificates_issued_per_month(database: Database) -> list[dict[str, Any]]:
    pipeline = [
        {"$match": {"issued_at": {"$ne": None}}},
        {
            "$project": {
                "_id": 0,
                "month": {"$dateToString": {"format": "%Y-%m", "date": "$issued_at"}},
            }
        },
        {"$group": {"_id": "$month", "count": {"$sum": 1}}},
        {"$project": {"_id": 0, "month": "$_id", "count": 1}},
        {"$sort": {"month": 1}},
    ]
    return _aggregate(database.certificates, pipeline)


def get_delayed_applications(
    database: Database,
    delayed_after_days: int = 30,
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    cutoff = (now or utc_now()) - timedelta(days=delayed_after_days)
    pipeline = [
        {
            "$match": {
                "status": {"$in": PENDING_STATUSES},
                "timestamps.submitted_at": {"$lt": cutoff},
            }
        },
        {
            "$project": {
                "_id": 0,
                "application_id": 1,
                "status": 1,
                "zone_id": "$parcel_ref.zone_id",
                "submitted_at": "$timestamps.submitted_at",
            }
        },
        {"$sort": {"submitted_at": 1}},
    ]
    return _aggregate(database.land_applications, pipeline)


def get_hotspot_zones(database: Database) -> list[dict[str, Any]]:
    pipeline = [
        {"$match": {"status": {"$in": HOTSPOT_STATUSES}}},
        {
            "$group": {
                "_id": "$parcel_ref.zone_id",
                "count": {"$sum": 1},
                "under_objection": {
                    "$sum": {
                        "$cond": [
                            {
                                "$eq": [
                                    "$status",
                                    ApplicationStatus.UNDER_OBJECTION.value,
                                ]
                            },
                            1,
                            0,
                        ]
                    }
                },
                "rejected": {
                    "$sum": {
                        "$cond": [
                            {"$eq": ["$status", ApplicationStatus.REJECTED.value]},
                            1,
                            0,
                        ]
                    }
                },
            }
        },
        {
            "$project": {
                "_id": 0,
                "zone_id": {"$ifNull": ["$_id", "unknown"]},
                "count": 1,
                "under_objection": 1,
                "rejected": 1,
            }
        },
        {"$sort": {"count": -1, "zone_id": 1}},
        {"$limit": 10},
    ]
    return _aggregate(database.land_applications, pipeline)


def get_surveyor_workload(database: Database) -> list[dict[str, Any]]:
    pipeline = [
        {
            "$lookup": {
                "from": "staff_members",
                "localField": "assigned_surveyor_id",
                "foreignField": "_id",
                "as": "surveyor",
            }
        },
        {"$unwind": "$surveyor"},
        {"$match": {"surveyor.role": StaffRole.SURVEYOR.value}},
        {
            "$group": {
                "_id": "$assigned_surveyor_id",
                "staff_code": {"$first": "$surveyor.staff_code"},
                "name": {"$first": "$surveyor.name"},
                "assigned_tasks": {"$sum": 1},
                "completed_tasks": {
                    "$sum": {
                        "$cond": [{"$in": ["$status", COMPLETED_SURVEY_STATUSES]}, 1, 0]
                    }
                },
                "active_tasks": {"$first": "$surveyor.workload.active_tasks"},
                "max_tasks": {"$first": "$surveyor.workload.max_tasks"},
            }
        },
        {
            "$project": {
                "_id": 0,
                "staff_id": {"$toString": "$_id"},
                "staff_code": 1,
                "name": 1,
                "assigned_tasks": 1,
                "completed_tasks": 1,
                "active_tasks": 1,
                "max_tasks": 1,
            }
        },
        {"$sort": {"assigned_tasks": -1, "staff_code": 1}},
    ]
    return _aggregate(database.survey_tasks, pipeline)


def get_registrar_workload(database: Database) -> list[dict[str, Any]]:
    pipeline = [
        {"$match": {"reviewed_by": {"$ne": None}}},
        {
            "$lookup": {
                "from": "staff_members",
                "localField": "reviewed_by",
                "foreignField": "_id",
                "as": "registrar",
            }
        },
        {"$unwind": "$registrar"},
        {"$match": {"registrar.role": StaffRole.REGISTRAR.value}},
        {
            "$group": {
                "_id": "$reviewed_by",
                "staff_code": {"$first": "$registrar.staff_code"},
                "name": {"$first": "$registrar.name"},
                "reviewed_reports": {"$sum": 1},
                "approved_reports": {
                    "$sum": {
                        "$cond": [
                            {"$eq": ["$registrar_review_status", "approved"]},
                            1,
                            0,
                        ]
                    }
                },
                "rejected_reports": {
                    "$sum": {
                        "$cond": [
                            {"$eq": ["$registrar_review_status", "rejected"]},
                            1,
                            0,
                        ]
                    }
                },
            }
        },
        {
            "$project": {
                "_id": 0,
                "staff_id": {"$toString": "$_id"},
                "staff_code": 1,
                "name": 1,
                "reviewed_reports": 1,
                "approved_reports": 1,
                "rejected_reports": 1,
            }
        },
        {"$sort": {"reviewed_reports": -1, "staff_code": 1}},
    ]
    return _aggregate(database.survey_reports, pipeline)


def _centroid_from_geometry(geometry: Mapping[str, Any]) -> list[float] | None:
    coordinates = geometry.get("coordinates")
    if not coordinates:
        return None
    if geometry.get("type") == "Point" and len(coordinates) >= 2:
        return [float(coordinates[0]), float(coordinates[1])]
    ring = coordinates[0] if geometry.get("type") == "Polygon" else coordinates[0][0]
    if not ring:
        return None
    longitudes = [float(point[0]) for point in ring if len(point) >= 2]
    latitudes = [float(point[1]) for point in ring if len(point) >= 2]
    if not longitudes or not latitudes:
        return None
    return [
        round(sum(longitudes) / len(longitudes), 6),
        round(sum(latitudes) / len(latitudes), 6),
    ]


def _feature(geometry: Mapping[str, Any], properties: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "type": "Feature",
        "geometry": serialize_mongo_value(dict(geometry)),
        "properties": serialize_mongo_value(dict(properties)),
    }


def get_parcels_geofeed(database: Database) -> dict[str, Any]:
    features = []
    for parcel in database.parcels.find({"geometry": {"$ne": None}}):
        geometry = parcel.get("geometry")
        if not geometry:
            continue
        features.append(
            _feature(
                geometry,
                {
                    "parcel_code": parcel.get("parcel_code"),
                    "parcel_number": parcel.get("parcel_number"),
                    "zone_id": parcel.get("zone_id"),
                    "area_sqm": parcel.get("area_sqm"),
                    "land_use": parcel.get("land_use"),
                    "registration_status": parcel.get("registration_status"),
                },
            )
        )
    return {"type": "FeatureCollection", "features": features}


def get_pending_heatmap(database: Database) -> dict[str, Any]:
    query = {
        "status": {"$in": PENDING_STATUSES},
        "parcel_ref.geometry": {"$ne": None},
    }
    features = []
    for application in database.land_applications.find(query):
        geometry = application.get("parcel_ref", {}).get("geometry")
        centroid = _centroid_from_geometry(geometry or {})
        if centroid is None:
            continue
        features.append(
            _feature(
                {"type": "Point", "coordinates": centroid},
                {
                    "application_id": application.get("application_id"),
                    "status": application.get("status"),
                    "application_type": application.get("application_type"),
                    "zone_id": application.get("parcel_ref", {}).get("zone_id"),
                },
            )
        )
    return {"type": "FeatureCollection", "features": features}


def get_kpis(
    database: Database,
    delayed_after_days: int = 30,
    now: datetime | None = None,
) -> dict[str, Any]:
    cutoff = (now or utc_now()) - timedelta(days=delayed_after_days)
    pipeline = [
        {
            "$facet": {
                "total": [{"$count": "count"}],
                "by_status": [
                    {"$group": {"_id": "$status", "count": {"$sum": 1}}},
                    {"$project": {"_id": 0, "status": "$_id", "count": 1}},
                    {"$sort": {"count": -1, "status": 1}},
                ],
                "by_type": [
                    {"$group": {"_id": "$application_type", "count": {"$sum": 1}}},
                    {
                        "$project": {
                            "_id": 0,
                            "application_type": "$_id",
                            "count": 1,
                        }
                    },
                    {"$sort": {"count": -1, "application_type": 1}},
                ],
                "state_counts": [
                    {
                        "$group": {
                            "_id": None,
                            "pending": {
                                "$sum": {
                                    "$cond": [
                                        {"$in": ["$status", PENDING_STATUSES]},
                                        1,
                                        0,
                                    ]
                                }
                            },
                            "approved": {
                                "$sum": {
                                    "$cond": [
                                        {
                                            "$eq": [
                                                "$status",
                                                ApplicationStatus.APPROVED.value,
                                            ]
                                        },
                                        1,
                                        0,
                                    ]
                                }
                            },
                            "rejected": {
                                "$sum": {
                                    "$cond": [
                                        {
                                            "$eq": [
                                                "$status",
                                                ApplicationStatus.REJECTED.value,
                                            ]
                                        },
                                        1,
                                        0,
                                    ]
                                }
                            },
                            "under_objection": {
                                "$sum": {
                                    "$cond": [
                                        {
                                            "$eq": [
                                                "$status",
                                                ApplicationStatus.UNDER_OBJECTION.value,
                                            ]
                                        },
                                        1,
                                        0,
                                    ]
                                }
                            },
                        }
                    },
                    {"$project": {"_id": 0}},
                ],
                "delayed": [
                    {
                        "$match": {
                            "status": {"$in": PENDING_STATUSES},
                            "timestamps.submitted_at": {"$lt": cutoff},
                        }
                    },
                    {
                        "$project": {
                            "_id": 0,
                            "application_id": 1,
                            "status": 1,
                            "zone_id": "$parcel_ref.zone_id",
                            "submitted_at": "$timestamps.submitted_at",
                        }
                    },
                    {"$sort": {"submitted_at": 1}},
                ],
                "hotspot_zones": [
                    {"$match": {"status": {"$in": HOTSPOT_STATUSES}}},
                    {
                        "$group": {
                            "_id": "$parcel_ref.zone_id",
                            "count": {"$sum": 1},
                        }
                    },
                    {
                        "$project": {
                            "_id": 0,
                            "zone_id": {"$ifNull": ["$_id", "unknown"]},
                            "count": 1,
                        }
                    },
                    {"$sort": {"count": -1, "zone_id": 1}},
                    {"$limit": 10},
                ],
            }
        }
    ]
    result = _aggregate(database.land_applications, pipeline)
    facet = result[0] if result else {}
    state_counts = facet.get("state_counts") or [{}]
    processing_time = get_processing_time(database)
    average_processing_time = 0
    if processing_time:
        total_count = sum(item["count"] for item in processing_time)
        weighted_days = sum(item["average_days"] * item["count"] for item in processing_time)
        average_processing_time = round(weighted_days / total_count, 2)

    certificates_per_month = get_certificates_issued_per_month(database)
    return {
        "total_applications": _first_count(facet.get("total", [])),
        "applications_by_status": _count_map(facet.get("by_status", []), "status"),
        "applications_by_type": _count_map(facet.get("by_type", []), "application_type"),
        "pending_applications": int(state_counts[0].get("pending", 0)),
        "approved_applications": int(state_counts[0].get("approved", 0)),
        "rejected_applications": int(state_counts[0].get("rejected", 0)),
        "under_objection_applications": int(state_counts[0].get("under_objection", 0)),
        "average_processing_time_days": average_processing_time,
        "certificates_issued_total": sum(item["count"] for item in certificates_per_month),
        "certificates_issued_per_month": certificates_per_month,
        "delayed_applications": facet.get("delayed", []),
        "hotspot_zones": facet.get("hotspot_zones", []),
    }

from pymongo import ASCENDING, GEOSPHERE, MongoClient
from pymongo.database import Database

from app.config import get_settings


_client: MongoClient | None = None


def get_mongo_client() -> MongoClient:
    global _client
    if _client is None:
        settings = get_settings()
        _client = MongoClient(
            settings.mongodb_uri,
            serverSelectionTimeoutMS=settings.mongodb_timeout_ms,
        )
    return _client


def get_database() -> Database:
    settings = get_settings()
    return get_mongo_client()[settings.mongodb_db_name]


def close_mongo_client() -> None:
    global _client
    if _client is not None:
        _client.close()
        _client = None


def ensure_indexes(database: Database | None = None) -> None:
    db = database if database is not None else get_database()

    db.land_applications.create_index([("application_id", ASCENDING)], unique=True)
    db.land_applications.create_index([("status", ASCENDING)])
    db.land_applications.create_index([("application_type", ASCENDING)])
    db.land_applications.create_index([("parcel_ref.parcel_number", ASCENDING)])
    db.land_applications.create_index([("parcel_ref.zone_id", ASCENDING)])
    db.land_applications.create_index([("timestamps.submitted_at", ASCENDING)])

    db.parcels.create_index([("parcel_code", ASCENDING)], unique=True)
    db.parcels.create_index([("geometry", GEOSPHERE)])
    db.parcels.create_index([("zone_id", ASCENDING)])

    db.applicants.create_index([("identity.national_id", ASCENDING)], unique=True)
    db.staff_members.create_index([("staff_code", ASCENDING)], unique=True)
    db.survey_tasks.create_index([("application_id", ASCENDING)])
    db.certificates.create_index([("certificate_id", ASCENDING)], unique=True)

from datetime import date, datetime
from typing import Any

from bson import ObjectId


def is_valid_object_id(value: str) -> bool:
    return ObjectId.is_valid(value)


def to_object_id(value: str | ObjectId) -> ObjectId:
    if isinstance(value, ObjectId):
        return value
    if not ObjectId.is_valid(value):
        raise ValueError(f"Invalid ObjectId: {value}")
    return ObjectId(value)


def serialize_mongo_value(value: Any) -> Any:
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, list):
        return [serialize_mongo_value(item) for item in value]
    if isinstance(value, tuple):
        return [serialize_mongo_value(item) for item in value]
    if isinstance(value, dict):
        return {key: serialize_mongo_value(item) for key, item in value.items()}
    return value


def serialize_mongo_document(document: dict[str, Any] | None) -> dict[str, Any] | None:
    if document is None:
        return None
    return serialize_mongo_value(document)

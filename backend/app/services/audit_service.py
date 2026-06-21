from datetime import datetime, timezone
from typing import Any, Mapping

from pymongo.database import Database


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def build_audit_event(
    event_type: str,
    actor_type: str,
    actor_id: str,
    meta: Mapping[str, Any] | None = None,
    previous_state: str | None = None,
    next_state: str | None = None,
) -> dict[str, Any]:
    event: dict[str, Any] = {
        "type": event_type,
        "by": {
            "actor_type": actor_type,
            "actor_id": actor_id,
        },
        "at": utc_now(),
        "meta": dict(meta or {}),
    }
    if previous_state is not None:
        event["previous_state"] = previous_state
    if next_state is not None:
        event["next_state"] = next_state
    return event


def append_audit_event(
    database: Database,
    application_id: Any,
    event: Mapping[str, Any],
) -> dict[str, int]:
    result = database.performance_logs.update_one(
        {"application_id": application_id},
        {
            "$push": {"event_stream": dict(event)},
            "$setOnInsert": {
                "application_id": application_id,
                "computed_kpis": {},
            },
        },
        upsert=True,
    )
    return {
        "matched_count": result.matched_count,
        "modified_count": result.modified_count,
        "upserted_count": 1 if result.upserted_id is not None else 0,
    }

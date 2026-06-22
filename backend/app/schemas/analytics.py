from typing import Any

from pydantic import Field

from app.schemas.common import LRMISBaseModel


class CountBucket(LRMISBaseModel):
    label: str
    count: int = 0


class StatusCount(LRMISBaseModel):
    status: str
    count: int = 0


class TypeCount(LRMISBaseModel):
    application_type: str
    count: int = 0


class ZoneAnalytics(LRMISBaseModel):
    zone_id: str
    total: int = 0
    pending: int = 0
    approved: int = 0
    rejected: int = 0
    under_objection: int = 0


class ProcessingTimeAnalytics(LRMISBaseModel):
    application_type: str
    average_days: float = 0
    count: int = 0


class SurveyorAnalytics(LRMISBaseModel):
    staff_id: str
    staff_code: str
    name: str
    assigned_tasks: int = 0
    completed_tasks: int = 0
    active_tasks: int = 0
    max_tasks: int = 0


class RegistrarAnalytics(LRMISBaseModel):
    staff_id: str
    staff_code: str
    name: str
    reviewed_reports: int = 0
    approved_reports: int = 0
    rejected_reports: int = 0


class DelayedApplication(LRMISBaseModel):
    application_id: str
    status: str
    zone_id: str | None = None
    submitted_at: str | None = None


class GeoJSONFeature(LRMISBaseModel):
    type: str = "Feature"
    geometry: dict[str, Any]
    properties: dict[str, Any] = Field(default_factory=dict)


class GeoJSONFeatureCollection(LRMISBaseModel):
    type: str = "FeatureCollection"
    features: list[GeoJSONFeature] = Field(default_factory=list)


class KPISummary(LRMISBaseModel):
    total_applications: int = 0
    applications_by_status: dict[str, int] = Field(default_factory=dict)
    applications_by_type: dict[str, int] = Field(default_factory=dict)
    pending_applications: int = 0
    approved_applications: int = 0
    rejected_applications: int = 0
    under_objection_applications: int = 0
    average_processing_time_days: float = 0
    certificates_issued_total: int = 0
    certificates_issued_per_month: list[dict[str, Any]] = Field(default_factory=list)
    delayed_applications: list[dict[str, Any]] = Field(default_factory=list)
    hotspot_zones: list[dict[str, Any]] = Field(default_factory=list)

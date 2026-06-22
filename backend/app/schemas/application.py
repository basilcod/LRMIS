from enum import Enum
from typing import Any

from pydantic import Field, field_validator

from app.schemas.common import (
    ApplicantType,
    ApplicationStatus,
    ApplicationType,
    DocumentStatus,
    LRMISBaseModel,
)


class Priority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class ApplicantRef(LRMISBaseModel):
    applicant_id: str = Field(min_length=1)
    applicant_type: ApplicantType
    submitted_by_representative: bool = False


class GeoJSONGeometry(LRMISBaseModel):
    type: str = Field(default="Polygon", pattern="^(Polygon|MultiPolygon|Point)$")
    coordinates: list[Any] = Field(min_length=1)


class ParcelRef(LRMISBaseModel):
    parcel_number: str = Field(min_length=1)
    block_number: str = Field(min_length=1)
    basin_number: str = Field(min_length=1)
    zone_id: str = Field(min_length=1)
    parcel_code: str | None = None
    parcel_id: str | None = None
    geometry: GeoJSONGeometry | None = None
    area_sqm: float | None = Field(default=None, gt=0)
    land_use: str | None = None


class DocumentItem(LRMISBaseModel):
    document_type: str = Field(min_length=1)
    required: bool = True
    status: DocumentStatus = DocumentStatus.MISSING


class InternalInfo(LRMISBaseModel):
    notes: list[str] = Field(default_factory=list)
    registrar_remarks: str | None = None
    visibility: str = "staff_only"


class ApplicationCreateRequest(LRMISBaseModel):
    application_type: ApplicationType
    priority: Priority = Priority.NORMAL
    applicant_ref: ApplicantRef
    parcel_ref: ParcelRef
    description: str | None = None
    tags: list[str] = Field(default_factory=list)
    required_documents: list[DocumentItem] = Field(default_factory=list)
    internal: InternalInfo = Field(default_factory=InternalInfo)

    @field_validator("tags")
    @classmethod
    def clean_tags(cls, value: list[str]) -> list[str]:
        return [tag.strip() for tag in value if tag.strip()]


class ApplicationTransitionRequest(LRMISBaseModel):
    target_state: ApplicationStatus
    actor_type: str = "registrar"
    actor_id: str = Field(min_length=1)
    note: str | None = None
    has_objection: bool = False
    survey_report_exists: bool = False
    legal_review_completed: bool = False


class HoldApplicationRequest(LRMISBaseModel):
    reason: str = Field(min_length=3)
    actor_id: str = Field(min_length=1)
    actor_type: str = "registrar"


class RejectApplicationRequest(LRMISBaseModel):
    reason: str = Field(min_length=3)
    actor_id: str = Field(min_length=1)
    actor_type: str = "registrar"


class CertificateCreateRequest(LRMISBaseModel):
    certificate_type: str = "ownership_certificate"
    issued_by: str = Field(min_length=1)
    issued_to_name: str = Field(min_length=1)


class ApplicationResponse(LRMISBaseModel):
    application_id: str
    application_type: ApplicationType
    status: ApplicationStatus
    priority: Priority
    applicant_ref: dict[str, Any]
    parcel_ref: dict[str, Any]
    workflow: dict[str, Any]
    required_documents: list[dict[str, Any]] = Field(default_factory=list)
    timestamps: dict[str, Any]
    description: str | None = None
    tags: list[str] = Field(default_factory=list)
    objection: dict[str, Any] = Field(default_factory=dict)
    certificate_state: dict[str, Any] = Field(default_factory=dict)
    internal: dict[str, Any] = Field(default_factory=dict)


class CertificateResponse(LRMISBaseModel):
    certificate_id: str
    application_id: str
    parcel_ref: dict[str, Any]
    certificate_type: str
    status: str = "issued"
    issued_to: dict[str, str]
    issued_at: str
    issued_by: str
    verification: dict[str, str]

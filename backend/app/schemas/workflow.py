from pydantic import Field

from app.schemas.common import ApplicationStatus, LRMISBaseModel


class WorkflowValidationContext(LRMISBaseModel):
    has_complete_applicant: bool = False
    has_complete_parcel: bool = False
    has_valid_parcel_location: bool = False
    has_survey_report: bool = False
    has_ownership_documents: bool = False
    legal_review_completed: bool = False
    has_objection: bool = False
    rejection_reason: str | None = None
    hold_reason: str | None = None


class WorkflowValidationResult(LRMISBaseModel):
    is_valid: bool
    current_status: ApplicationStatus
    next_status: ApplicationStatus
    errors: list[str] = Field(default_factory=list)
    allowed_next: list[ApplicationStatus] = Field(default_factory=list)

from pydantic import Field

from app.schemas.common import DocumentStatus, LRMISBaseModel


class AddDocumentRequest(LRMISBaseModel):
    applicant_id: str
    document_type: str = Field(min_length=1)
    file_name: str = Field(min_length=1)
    storage_ref: str = Field(min_length=1)
    verification_status: DocumentStatus = DocumentStatus.PENDING_REVIEW


class AddCommentRequest(LRMISBaseModel):
    applicant_id: str
    message: str = Field(min_length=1)


class SubmitObjectionRequest(LRMISBaseModel):
    applicant_id: str
    reason: str = Field(min_length=1)
    supporting_document_ids: list[str] = Field(default_factory=list)


class TimelineEventResponse(LRMISBaseModel):
    type: str
    by: dict
    at: str
    meta: dict = Field(default_factory=dict)
    previous_state: str | None = None
    next_state: str | None = None

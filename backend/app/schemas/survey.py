from pydantic import Field

from app.schemas.common import LRMISBaseModel, StaffRole, SurveyMilestone


class AutoAssignResponse(LRMISBaseModel):
    application_id: str
    survey_task_id: str
    assigned_surveyor_id: str
    assigned_surveyor_code: str
    policy: str
    score: dict = Field(default_factory=dict)


class SurveyMilestoneRequest(LRMISBaseModel):
    milestone: SurveyMilestone
    by_staff_id: str
    actor_role: StaffRole = StaffRole.SURVEYOR
    notes: str | None = None
    meta: dict = Field(default_factory=dict)


class SurveyReportRequest(LRMISBaseModel):
    surveyor_id: str
    file_name: str = Field(min_length=1)
    storage_ref: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    actor_role: StaffRole = StaffRole.SURVEYOR


class RegistrarReviewRequest(LRMISBaseModel):
    reviewer_id: str
    decision: str = Field(pattern="^(approved|rejected|needs_revision)$")
    notes: str = Field(min_length=1)
    actor_role: StaffRole = StaffRole.REGISTRAR

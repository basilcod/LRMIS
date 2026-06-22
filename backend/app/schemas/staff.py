from pydantic import Field

from app.schemas.common import LRMISBaseModel, StaffRole


class CoverageZone(LRMISBaseModel):
    zone_ids: list[str] = Field(default_factory=list)
    geo_fence: dict | None = None


class StaffSchedule(LRMISBaseModel):
    timezone: str = "Asia/Jerusalem"
    shifts: list[dict[str, str]] = Field(default_factory=list)
    on_call: bool = False


class Workload(LRMISBaseModel):
    active_tasks: int = Field(default=0, ge=0)
    max_tasks: int = Field(default=10, ge=1)


class CreateStaffRequest(LRMISBaseModel):
    staff_code: str = Field(min_length=1)
    name: str = Field(min_length=1)
    role: StaffRole
    department: str = Field(min_length=1)
    skills: list[str] = Field(default_factory=list)
    coverage: CoverageZone
    schedule: StaffSchedule
    workload: Workload = Field(default_factory=Workload)
    contacts: dict = Field(default_factory=dict)
    active: bool = True


class StaffResponse(LRMISBaseModel):
    staff_id: str
    staff_code: str
    name: str
    role: StaffRole
    department: str
    skills: list[str]
    coverage: CoverageZone
    schedule: StaffSchedule
    workload: Workload
    contacts: dict = Field(default_factory=dict)
    active: bool
    performance_summary: dict = Field(default_factory=dict)

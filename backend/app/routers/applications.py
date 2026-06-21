from fastapi import APIRouter

from app.schemas.common import ApplicationStatus
from app.services.workflow_service import get_allowed_next_statuses
from app.utils.responses import success_response

router = APIRouter(prefix="/applications", tags=["applications"])


@router.get("/")
def applications_placeholder():
    return success_response(
        data=[],
        message="Land Application Management endpoints will be implemented here.",
        meta={"module": "land_application_management"},
    )


@router.get("/workflow")
def workflow_placeholder():
    return success_response(
        data={
            status.value: [
                next_status.value for next_status in get_allowed_next_statuses(status)
            ]
            for status in ApplicationStatus
        },
        message="Shared workflow state machine.",
    )

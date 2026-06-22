from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from pymongo.database import Database

from app.database import get_database
from app.schemas.application import (
    ApplicationCreateRequest,
    ApplicationTransitionRequest,
    CertificateCreateRequest,
    HoldApplicationRequest,
    Priority,
    RejectApplicationRequest,
)
from app.schemas.common import ApplicationStatus, ApplicationType
from app.services.application_service import (
    create_application,
    get_application,
    hold_application,
    issue_certificate,
    list_applications,
    reject_application,
    transition_application,
)
from app.services.workflow_service import get_allowed_next_statuses
from app.utils.responses import success_response

router = APIRouter(prefix="/applications", tags=["applications"])


def _handle_application_error(error: Exception) -> HTTPException:
    if isinstance(error, LookupError):
        return HTTPException(status_code=404, detail=str(error))
    if isinstance(error, PermissionError):
        return HTTPException(status_code=403, detail=str(error))
    if isinstance(error, ValueError):
        return HTTPException(status_code=400, detail=str(error))
    return HTTPException(status_code=400, detail=str(error))


@router.post("/", status_code=status.HTTP_201_CREATED)
def submit_application(
    payload: ApplicationCreateRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    database: Database = Depends(get_database),
):
    try:
        application = create_application(database, payload, idempotency_key)
    except Exception as error:
        raise _handle_application_error(error) from error
    return success_response(
        data=application,
        message="Application submitted.",
    )


@router.get("/")
def list_land_applications(
    status_filter: ApplicationStatus | None = Query(default=None, alias="status"),
    application_type: ApplicationType | None = None,
    priority: Priority | None = None,
    zone_id: str | None = None,
    parcel_number: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    sort_by: str = "timestamps.submitted_at",
    sort_order: str = Query(default="desc", pattern="^(asc|desc)$"),
    database: Database = Depends(get_database),
):
    filters = {
        "status": status_filter,
        "application_type": application_type,
        "priority": priority,
        "parcel_ref.zone_id": zone_id,
        "parcel_ref.parcel_number": parcel_number,
    }
    try:
        result = list_applications(
            database,
            page=page,
            page_size=page_size,
            filters=filters,
            sort_by=sort_by,
            sort_order=sort_order,
        )
    except Exception as error:
        raise _handle_application_error(error) from error
    return success_response(
        data=result["items"],
        message="Applications retrieved.",
        meta={
            "total": result["total"],
            "page": result["page"],
            "page_size": result["page_size"],
        },
    )


@router.get("/workflow")
def get_workflow_matrix():
    return success_response(
        data={
            status_value.value: [
                next_status.value
                for next_status in get_allowed_next_statuses(status_value)
            ]
            for status_value in ApplicationStatus
        },
        message="Shared workflow state machine.",
    )


@router.get("/{application_id}")
def get_land_application(
    application_id: str,
    database: Database = Depends(get_database),
):
    try:
        application = get_application(database, application_id)
    except Exception as error:
        raise _handle_application_error(error) from error
    return success_response(
        data=application,
        message="Application retrieved.",
    )


@router.patch("/{application_id}/transition")
def update_application_transition(
    application_id: str,
    payload: ApplicationTransitionRequest,
    database: Database = Depends(get_database),
):
    try:
        application = transition_application(database, application_id, payload)
    except Exception as error:
        raise _handle_application_error(error) from error
    return success_response(
        data=application,
        message="Application workflow updated.",
    )


@router.post("/{application_id}/hold")
def place_application_on_hold(
    application_id: str,
    payload: HoldApplicationRequest,
    database: Database = Depends(get_database),
):
    try:
        application = hold_application(database, application_id, payload)
    except Exception as error:
        raise _handle_application_error(error) from error
    return success_response(
        data=application,
        message="Application placed on hold.",
    )


@router.post("/{application_id}/reject")
def reject_land_application(
    application_id: str,
    payload: RejectApplicationRequest,
    database: Database = Depends(get_database),
):
    try:
        application = reject_application(database, application_id, payload)
    except Exception as error:
        raise _handle_application_error(error) from error
    return success_response(
        data=application,
        message="Application rejected.",
    )


@router.post("/{application_id}/certificate")
def generate_application_certificate(
    application_id: str,
    payload: CertificateCreateRequest,
    database: Database = Depends(get_database),
):
    try:
        certificate = issue_certificate(database, application_id, payload)
    except Exception as error:
        raise _handle_application_error(error) from error
    return success_response(
        data=certificate,
        message="Certificate metadata issued.",
    )

from fastapi import APIRouter
from fastapi import Depends, HTTPException
from pymongo.database import Database

from app.database import get_database
from app.schemas.applicant import CreateApplicantRequest
from app.services.applicant_service import (
    create_applicant_profile,
    get_applicant_profile,
    list_applications_submitted_by_applicant,
)
from app.utils.responses import success_response

router = APIRouter(prefix="/applicants", tags=["applicants"])


def _handle_service_error(error: Exception) -> HTTPException:
    if isinstance(error, LookupError):
        return HTTPException(status_code=404, detail=str(error))
    if isinstance(error, ValueError):
        return HTTPException(status_code=409, detail=str(error))
    return HTTPException(status_code=400, detail=str(error))


@router.post("/")
def create_applicant(
    payload: CreateApplicantRequest,
    database: Database = Depends(get_database),
):
    try:
        applicant = create_applicant_profile(database, payload)
    except Exception as error:
        raise _handle_service_error(error) from error
    return success_response(
        data=applicant,
        message="Applicant profile created.",
    )


@router.get("/{applicant_id}")
def get_applicant(
    applicant_id: str,
    database: Database = Depends(get_database),
):
    try:
        applicant = get_applicant_profile(database, applicant_id)
    except Exception as error:
        raise _handle_service_error(error) from error
    return success_response(
        data=applicant,
        message="Applicant profile retrieved.",
    )


@router.get("/{applicant_id}/applications")
def get_applicant_applications(
    applicant_id: str,
    database: Database = Depends(get_database),
):
    try:
        applications = list_applications_submitted_by_applicant(database, applicant_id)
    except Exception as error:
        raise _handle_service_error(error) from error
    return success_response(
        data=applications,
        message="Applicant applications retrieved.",
    )

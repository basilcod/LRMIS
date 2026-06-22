from fastapi import APIRouter, Depends, HTTPException
from pymongo.database import Database

from app.database import get_database
from app.schemas.survey import RegistrarReviewRequest, SurveyMilestoneRequest, SurveyReportRequest
from app.services.assignment_service import auto_assign_surveyor
from app.services.registrar_service import submit_registrar_review
from app.services.survey_service import add_survey_milestone, register_survey_report
from app.utils.responses import success_response

router = APIRouter(prefix="/applications", tags=["survey and registrar"])


def _handle_survey_error(error: Exception) -> HTTPException:
    if isinstance(error, LookupError):
        return HTTPException(status_code=404, detail=str(error))
    if isinstance(error, PermissionError):
        return HTTPException(status_code=403, detail=str(error))
    if isinstance(error, ValueError):
        return HTTPException(status_code=400, detail=str(error))
    return HTTPException(status_code=400, detail=str(error))


@router.post("/{application_id}/auto-assign-surveyor")
def auto_assign_application_surveyor(
    application_id: str,
    database: Database = Depends(get_database),
):
    try:
        assignment = auto_assign_surveyor(database, application_id)
    except Exception as error:
        raise _handle_survey_error(error) from error
    return success_response(
        data=assignment,
        message="Surveyor assigned.",
    )


@router.patch("/{application_id}/survey-milestone")
def update_survey_milestone(
    application_id: str,
    payload: SurveyMilestoneRequest,
    database: Database = Depends(get_database),
):
    try:
        milestone = add_survey_milestone(database, application_id, payload)
    except Exception as error:
        raise _handle_survey_error(error) from error
    return success_response(
        data=milestone,
        message="Survey milestone added.",
    )


@router.post("/{application_id}/survey-report")
def upload_survey_report(
    application_id: str,
    payload: SurveyReportRequest,
    database: Database = Depends(get_database),
):
    try:
        report = register_survey_report(database, application_id, payload)
    except Exception as error:
        raise _handle_survey_error(error) from error
    return success_response(
        data=report,
        message="Survey report metadata registered.",
    )


@router.patch("/{application_id}/registrar-review")
def registrar_review(
    application_id: str,
    payload: RegistrarReviewRequest,
    database: Database = Depends(get_database),
):
    try:
        review = submit_registrar_review(database, application_id, payload)
    except Exception as error:
        raise _handle_survey_error(error) from error
    return success_response(
        data=review,
        message="Registrar review submitted.",
    )

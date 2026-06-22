from fastapi import APIRouter, Depends, HTTPException
from pymongo.database import Database

from app.database import get_database
from app.schemas.portal import (
    AddCommentRequest,
    AddDocumentRequest,
    SubmitObjectionRequest,
)
from app.services.portal_service import (
    add_applicant_comment,
    add_document_metadata,
    get_application_timeline,
    submit_objection,
)
from app.utils.responses import success_response

router = APIRouter(prefix="/applications", tags=["applicant portal"])


def _handle_portal_error(error: Exception) -> HTTPException:
    if isinstance(error, LookupError):
        return HTTPException(status_code=404, detail=str(error))
    if isinstance(error, PermissionError):
        return HTTPException(status_code=403, detail=str(error))
    if isinstance(error, ValueError):
        return HTTPException(status_code=400, detail=str(error))
    return HTTPException(status_code=400, detail=str(error))


@router.post("/{application_id}/documents")
def add_application_document(
    application_id: str,
    payload: AddDocumentRequest,
    database: Database = Depends(get_database),
):
    try:
        document = add_document_metadata(database, application_id, payload)
    except Exception as error:
        raise _handle_portal_error(error) from error
    return success_response(
        data=document,
        message="Document metadata added.",
    )


@router.post("/{application_id}/comments")
def add_application_comment(
    application_id: str,
    payload: AddCommentRequest,
    database: Database = Depends(get_database),
):
    try:
        comment = add_applicant_comment(database, application_id, payload)
    except Exception as error:
        raise _handle_portal_error(error) from error
    return success_response(
        data=comment,
        message="Applicant comment added.",
    )


@router.post("/{application_id}/objections")
def submit_application_objection(
    application_id: str,
    payload: SubmitObjectionRequest,
    database: Database = Depends(get_database),
):
    try:
        objection = submit_objection(database, application_id, payload)
    except Exception as error:
        raise _handle_portal_error(error) from error
    return success_response(
        data=objection,
        message="Objection submitted.",
    )


@router.get("/{application_id}/timeline")
def get_timeline(
    application_id: str,
    database: Database = Depends(get_database),
):
    timeline = get_application_timeline(database, application_id)
    return success_response(
        data=timeline,
        message="Application timeline retrieved.",
    )

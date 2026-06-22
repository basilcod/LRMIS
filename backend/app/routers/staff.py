from fastapi import APIRouter, Depends, HTTPException
from pymongo.database import Database

from app.database import get_database
from app.schemas.staff import CreateStaffRequest
from app.services.staff_service import create_staff_member, get_staff_profile
from app.utils.responses import success_response

router = APIRouter(prefix="/staff", tags=["staff"])


def _handle_staff_error(error: Exception) -> HTTPException:
    if isinstance(error, LookupError):
        return HTTPException(status_code=404, detail=str(error))
    if isinstance(error, PermissionError):
        return HTTPException(status_code=403, detail=str(error))
    if isinstance(error, ValueError):
        return HTTPException(status_code=409, detail=str(error))
    return HTTPException(status_code=400, detail=str(error))


@router.post("/")
def create_staff(
    payload: CreateStaffRequest,
    database: Database = Depends(get_database),
):
    try:
        staff = create_staff_member(database, payload)
    except Exception as error:
        raise _handle_staff_error(error) from error
    return success_response(
        data=staff,
        message="Staff member created.",
    )


@router.get("/{staff_id}")
def get_staff(
    staff_id: str,
    database: Database = Depends(get_database),
):
    try:
        staff = get_staff_profile(database, staff_id)
    except Exception as error:
        raise _handle_staff_error(error) from error
    return success_response(
        data=staff,
        message="Staff profile retrieved.",
    )

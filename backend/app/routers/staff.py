from fastapi import APIRouter

from app.utils.responses import success_response

router = APIRouter(prefix="/staff", tags=["staff"])


@router.get("/")
def staff_placeholder():
    return success_response(
        data=[],
        message="Surveyors, Registrar, and Assignment endpoints will be implemented here.",
        meta={"module": "surveyors_registrar_assignment"},
    )

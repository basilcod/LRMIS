from fastapi import APIRouter

from app.utils.responses import success_response

router = APIRouter(prefix="/applicants", tags=["applicants"])


@router.get("/")
def applicants_placeholder():
    return success_response(
        data=[],
        message="Applicant Portal and Profiles endpoints will be implemented here.",
        meta={"module": "applicant_portal_profiles"},
    )

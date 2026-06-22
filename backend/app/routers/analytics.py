from fastapi import APIRouter, Depends, HTTPException, Query
from pymongo.database import Database

from app.database import get_database
from app.services.analytics_service import (
    get_applications_by_status,
    get_applications_by_zone,
    get_kpis,
    get_parcels_geofeed,
    get_pending_heatmap,
    get_processing_time,
    get_registrar_workload,
    get_surveyor_workload,
)
from app.utils.responses import success_response

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _handle_analytics_error(error: Exception) -> HTTPException:
    return HTTPException(status_code=400, detail=str(error))


@router.get("/kpis")
def analytics_kpis(
    delayed_after_days: int = Query(default=30, ge=1, le=365),
    database: Database = Depends(get_database),
):
    try:
        data = get_kpis(database, delayed_after_days=delayed_after_days)
    except Exception as error:
        raise _handle_analytics_error(error) from error
    return success_response(data=data, message="Analytics KPIs retrieved.")


@router.get("/applications-by-status")
def applications_by_status(database: Database = Depends(get_database)):
    try:
        data = get_applications_by_status(database)
    except Exception as error:
        raise _handle_analytics_error(error) from error
    return success_response(
        data=data,
        message="Applications grouped by status.",
    )


@router.get("/applications-by-zone")
def applications_by_zone(database: Database = Depends(get_database)):
    try:
        data = get_applications_by_zone(database)
    except Exception as error:
        raise _handle_analytics_error(error) from error
    return success_response(
        data=data,
        message="Applications grouped by zone.",
    )


@router.get("/processing-time")
def processing_time(database: Database = Depends(get_database)):
    try:
        data = get_processing_time(database)
    except Exception as error:
        raise _handle_analytics_error(error) from error
    return success_response(
        data=data,
        message="Average processing time by application type.",
    )


@router.get("/surveyors")
def surveyor_analytics(database: Database = Depends(get_database)):
    try:
        data = get_surveyor_workload(database)
    except Exception as error:
        raise _handle_analytics_error(error) from error
    return success_response(
        data=data,
        message="Surveyor workload analytics.",
    )


@router.get("/registrars")
def registrar_analytics(database: Database = Depends(get_database)):
    try:
        data = get_registrar_workload(database)
    except Exception as error:
        raise _handle_analytics_error(error) from error
    return success_response(
        data=data,
        message="Registrar workload analytics.",
    )


@router.get("/geofeeds/parcels")
def parcel_geofeed(database: Database = Depends(get_database)):
    try:
        data = get_parcels_geofeed(database)
    except Exception as error:
        raise _handle_analytics_error(error) from error
    return success_response(
        data=data,
        message="Parcel GeoJSON feed retrieved.",
    )


@router.get("/geofeeds/pending-heatmap")
def pending_heatmap(database: Database = Depends(get_database)):
    try:
        data = get_pending_heatmap(database)
    except Exception as error:
        raise _handle_analytics_error(error) from error
    return success_response(
        data=data,
        message="Pending application heatmap retrieved.",
    )

from fastapi import APIRouter

from app.utils.responses import success_response

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/")
def analytics_placeholder():
    return success_response(
        data={},
        message="Analytics, Map, and Visualization endpoints will be implemented here.",
        meta={"module": "analytics_map_visualization"},
    )


@router.get("/kpis")
def kpis_placeholder():
    return success_response(
        data={
            "total_applications": 0,
            "pending_applications": 0,
            "approved_applications": 0,
            "certificates_issued": 0,
        },
        message="Placeholder KPIs until analytics aggregation is implemented.",
    )


@router.get("/geofeeds/parcels")
def parcel_geofeed_placeholder():
    return success_response(
        data={
            "type": "FeatureCollection",
            "features": [],
        },
        message="Placeholder GeoJSON feed until parcel queries are implemented.",
    )

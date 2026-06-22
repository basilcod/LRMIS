from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import close_mongo_client
from app.routers import analytics, applicants, applications, portal, staff, survey


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    close_mongo_client()


settings = get_settings()

app = FastAPI(
    title=f"{settings.app_name} API",
    description="Land Registration Management Information System backend.",
    version=settings.app_version,
    lifespan=lifespan,
)

if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(applications.router)
app.include_router(portal.router)
app.include_router(survey.router)
app.include_router(applicants.router)
app.include_router(staff.router)
app.include_router(analytics.router)


@app.get("/")
def root():
    return {
        "name": settings.app_name,
        "status": "ready",
        "docs": "/docs",
    }


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.environment,
    }

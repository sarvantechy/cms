from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.domains.academics.router import router as academics_router
from app.domains.activities.router import router as activities_router
from app.domains.admissions.router import router as admissions_router
from app.domains.attendance.router import router as attendance_router
from app.domains.communications.router import router as communications_router
from app.domains.delivery.router import router as delivery_router
from app.domains.examinations.router import router as examinations_router
from app.domains.fees.router import router as fees_router
from app.domains.identity.account_router import router as identity_router
from app.domains.identity.platform_router import router as platform_router
from app.domains.identity.role_router import router as identity_role_router
from app.domains.identity.router import router as authentication_router
from app.domains.reporting.router import router as reporting_router
from app.domains.students.router import router as students_router

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Multi-tenant API for INDUS college operations.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["Authorization", "Content-Type"],
)
app.include_router(authentication_router)
app.include_router(identity_router)
app.include_router(identity_role_router)
app.include_router(platform_router)
app.include_router(academics_router)
app.include_router(admissions_router)
app.include_router(communications_router)
app.include_router(students_router)
app.include_router(delivery_router)
app.include_router(attendance_router)
app.include_router(fees_router)
app.include_router(examinations_router)
app.include_router(activities_router)
app.include_router(reporting_router)


@app.get("/health/live", tags=["Health"])
def health_live() -> dict[str, str]:
    """Return a process-level liveness response without database access."""

    return {"status": "ok", "service": "4by4-cms-api"}

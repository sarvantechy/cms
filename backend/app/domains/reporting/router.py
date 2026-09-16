"""FastAPI routes for tenant-scoped source-backed operational reports."""

from collections.abc import Generator
from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from app.db.session import runtime_session_factory
from app.domains.identity.router import require_permission
from app.domains.reporting.schemas import (
    OverviewReport,
    PaginatedReportRows,
    ReportExportCreate,
    ReportFilters,
    ReportScheduleCreate,
    ReportScheduleSummary,
    SavedReportCreate,
    SavedReportSummary,
)
from app.domains.reporting.service import ReportingService
from app.security_context import ActorContext

router = APIRouter(prefix="/api/v1/reports", tags=["Reporting"])


def get_runtime_session() -> Generator[Session, None, None]:
    """Yield a restricted runtime session with explicit route-level commit control."""

    with runtime_session_factory()() as session:
        try:
            yield session
        except Exception:
            session.rollback()
            raise


@router.get("/overview", response_model=OverviewReport)
def reports_overview(
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("reports.management.read"))],
    start_date: date | None = None,
    end_date: date | None = None,
    academic_year_id: UUID | None = None,
) -> OverviewReport:
    """Return source-backed tenant operational totals across key platform domains."""

    if start_date and end_date and start_date > end_date:
        raise HTTPException(status_code=422, detail="Start date must not be after end date")
    return ReportingService(session, actor).get_overview(
        ReportFilters(start_date=start_date, end_date=end_date, academic_year_id=academic_year_id)
    )


@router.get("/metrics/{metric_key}", response_model=PaginatedReportRows)
def report_drill_down(
    metric_key: str,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("reports.management.read"))],
    start_date: date | None = None,
    end_date: date | None = None,
    academic_year_id: UUID | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
) -> PaginatedReportRows:
    """Return source rows that reconcile one management dashboard metric."""

    try:
        return ReportingService(session, actor).get_drill_down(
            metric_key,
            ReportFilters(start_date=start_date, end_date=end_date, academic_year_id=academic_year_id),
            skip,
            limit,
        )
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/saved", response_model=list[SavedReportSummary])
def list_saved_reports(
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("reports.management.read"))],
) -> list[SavedReportSummary]:
    """Return report views saved by the current membership."""

    return [SavedReportSummary.model_validate(item) for item in ReportingService(session, actor).list_saved_reports()]


@router.post("/saved", response_model=SavedReportSummary, status_code=201)
def save_report(
    payload: SavedReportCreate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("reports.management.read"))],
) -> SavedReportSummary:
    """Create or update one actor-owned named report view."""

    item = ReportingService(session, actor).save_report(payload)
    response = SavedReportSummary.model_validate(item)
    session.commit()
    return response


@router.post("/exports", status_code=201)
def export_report(
    payload: ReportExportCreate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("reports.management.read"))],
) -> Response:
    """Generate a CSV from the same scoped rows used by dashboard drill-down."""

    try:
        item, content = ReportingService(session, actor).create_export(payload)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    export_id = str(item.id)
    session.commit()
    return Response(
        content=content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{payload.metric_key}-report.csv"',
            "X-Report-Export-ID": export_id,
        },
    )


@router.get("/schedules", response_model=list[ReportScheduleSummary])
def list_report_schedules(
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("reports.management.read"))],
) -> list[ReportScheduleSummary]:
    """Return recurring report configurations owned by the current membership."""

    return [ReportScheduleSummary.model_validate(item) for item in ReportingService(session, actor).list_schedules()]


@router.post("/schedules", response_model=ReportScheduleSummary, status_code=201)
def create_report_schedule(
    payload: ReportScheduleCreate,
    session: Annotated[Session, Depends(get_runtime_session)],
    actor: Annotated[ActorContext, Depends(require_permission("reports.management.read"))],
) -> ReportScheduleSummary:
    """Create one actor-owned recurring report delivery configuration."""

    try:
        item = ReportingService(session, actor).create_schedule(payload)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    response = ReportScheduleSummary.model_validate(item)
    session.commit()
    return response

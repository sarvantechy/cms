"""Pydantic schemas for source-backed operational reports."""

from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ReportFilters(BaseModel):
    """Constrain report calculations to an optional date and academic context."""

    start_date: date | None = None
    end_date: date | None = None
    academic_year_id: UUID | None = None


class MetricDefinition(BaseModel):
    """Explain one dashboard metric and its authoritative source."""

    key: str
    label: str
    calculation: str
    source: str


class ReportRow(BaseModel):
    """Represent one source record in a metric drill-down."""

    id: UUID
    label: str
    detail: str
    occurred_on: date | None = None


class PaginatedReportRows(BaseModel):
    """Return one bounded page of report source rows."""

    items: list[ReportRow]
    total: int = Field(ge=0)


class SavedReportCreate(BaseModel):
    """Capture an actor-owned named report filter."""

    name: str = Field(min_length=1, max_length=120)
    filters: ReportFilters


class SavedReportSummary(SavedReportCreate):
    """Return one persisted actor-owned report filter."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime


class ReportExportCreate(BaseModel):
    """Request one immediately generated permission-scoped report export."""

    metric_key: str
    filters: ReportFilters
    export_format: Literal["csv"] = "csv"


class ReportExportSummary(ReportExportCreate):
    """Describe one completed report export audit record."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    state: Literal["completed", "failed"]
    row_count: int = Field(ge=0)
    created_at: datetime


class ReportScheduleCreate(BaseModel):
    """Configure recurring delivery metadata for one report export."""

    name: str = Field(min_length=1, max_length=120)
    metric_key: str
    export_format: Literal["csv"] = "csv"
    frequency: Literal["daily", "weekly", "monthly"]
    recipient_email: str = Field(min_length=3, max_length=320)
    filters: ReportFilters


class ReportScheduleSummary(ReportScheduleCreate):
    """Return one actor-owned recurring report configuration."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    enabled: bool
    created_at: datetime


class StudentsOverview(BaseModel):
    """Summarize student counts by operational lifecycle state."""

    total: int = Field(ge=0)
    active: int = Field(ge=0)


class AttendanceOverview(BaseModel):
    """Summarize attendance record and status counts."""

    total_records: int = Field(ge=0)
    present_records: int = Field(ge=0)
    absent_records: int = Field(ge=0)


class FeesOverview(BaseModel):
    """Summarize fee invoice and collection financial totals."""

    total_invoiced: float = Field(ge=0)
    total_collected: float
    outstanding: float


class ExaminationsOverview(BaseModel):
    """Summarize published examination outcome counts."""

    published_results: int = Field(ge=0)
    passed_results: int = Field(ge=0)


class ActivitiesOverview(BaseModel):
    """Summarize events, registrations, and achievements issued."""

    total_events: int = Field(ge=0)
    published_events: int = Field(ge=0)
    registrations: int = Field(ge=0)
    achievements: int = Field(ge=0)


class CommunicationsOverview(BaseModel):
    """Summarize notices and delivery engagement metrics."""

    total_notices: int = Field(ge=0)
    published_notices: int = Field(ge=0)
    deliveries: int = Field(ge=0)
    read_deliveries: int = Field(ge=0)


class OverviewReport(BaseModel):
    """Response shape for the operational overview report endpoint."""

    calculated_at: datetime
    filters: ReportFilters
    definitions: list[MetricDefinition]
    students: StudentsOverview
    attendance: AttendanceOverview
    fees: FeesOverview
    examinations: ExaminationsOverview
    activities: ActivitiesOverview
    communications: CommunicationsOverview

"""Business logic for tenant-scoped source-backed operational report aggregates."""

from __future__ import annotations

import csv
from datetime import UTC, datetime
from decimal import Decimal
from io import StringIO
from typing import Any

from sqlalchemy import case, func, select, text
from sqlalchemy.orm import Session

from app.domains.activities.models import Achievement, Activity, EventRegistration
from app.domains.attendance.models import AttendanceRecord
from app.domains.communications.models import Notice, NoticeDelivery
from app.domains.examinations.models import PublishedResult
from app.domains.fees.models import InvoiceLine, Payment, PaymentAllocation, StudentInvoice
from app.domains.reporting.models import ReportExport, ReportSchedule, SavedReport
from app.domains.reporting.schemas import (
    ActivitiesOverview,
    AttendanceOverview,
    CommunicationsOverview,
    ExaminationsOverview,
    FeesOverview,
    MetricDefinition,
    OverviewReport,
    PaginatedReportRows,
    ReportExportCreate,
    ReportFilters,
    ReportRow,
    ReportScheduleCreate,
    SavedReportCreate,
    StudentsOverview,
)
from app.domains.students.models import Person, Student, StudentEnrollment
from app.security_context import ActorContext

REPORT_DEFINITIONS = (
    MetricDefinition(key="students", label="Students", calculation="Count of student records; active is status = active.", source="students"),
    MetricDefinition(key="attendance", label="Attendance", calculation="Count of attendance records grouped by attendance status.", source="attendance_records"),
    MetricDefinition(key="fees", label="Fees", calculation="Invoice lines less discounts, minus allocations on posted payments.", source="student_invoices, invoice_lines, payments, payment_allocations"),
    MetricDefinition(key="examinations", label="Examinations", calculation="Count of published results; passed is result = pass.", source="published_results"),
    MetricDefinition(key="activities", label="Activities", calculation="Events, registrations, and achievement source counts.", source="activities, event_registrations, achievements"),
    MetricDefinition(key="communications", label="Communications", calculation="Notice and recipient delivery source counts.", source="notices, notice_deliveries"),
)
VALID_METRICS = frozenset(definition.key for definition in REPORT_DEFINITIONS)


class ReportingService:
    """Build source-backed operational report totals without synthetic records."""

    def __init__(self, session: Session, actor: ActorContext) -> None:
        """Initialize reporting with a tenant-scoped database session."""

        self.session = session
        self.actor = actor
        self.session.execute(
            text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
            {"tenant_id": str(actor.tenant_id)},
        )

    @staticmethod
    def _to_float(value: Decimal | float | None) -> float:
        """Convert an optional numeric aggregate to a JSON-safe float."""

        if value is None:
            return 0.0
        return float(value)

    @staticmethod
    def _date_conditions(column: Any, filters: ReportFilters) -> list[Any]:
        """Build inclusive date predicates for a dated source column."""

        conditions: list[Any] = []
        if filters.start_date:
            conditions.append(func.date(column) >= filters.start_date)
        if filters.end_date:
            conditions.append(func.date(column) <= filters.end_date)
        return conditions

    def _student_ids(self, filters: ReportFilters) -> Any | None:
        """Return student IDs in the selected academic year, when supplied."""

        if not filters.academic_year_id:
            return None
        return select(StudentEnrollment.student_id).where(
            StudentEnrollment.tenant_id == self.actor.tenant_id,
            StudentEnrollment.academic_year_id == filters.academic_year_id,
        )

    def get_overview(self, filters: ReportFilters | None = None) -> OverviewReport:
        """Return source-backed aggregate totals for the actor's tenant."""

        filters = filters or ReportFilters()
        student_ids = self._student_ids(filters)
        student_conditions = [Student.tenant_id == self.actor.tenant_id, *self._date_conditions(Student.created_at, filters)]
        if student_ids is not None:
            student_conditions.append(Student.id.in_(student_ids))
        students_total, students_active = self.session.execute(
            select(
                func.count(Student.id),
                func.sum(case((Student.status == "active", 1), else_=0)),
            ).where(*student_conditions)
        ).one()

        attendance_conditions = [AttendanceRecord.tenant_id == self.actor.tenant_id, *self._date_conditions(AttendanceRecord.created_at, filters)]
        if student_ids is not None:
            attendance_conditions.append(AttendanceRecord.student_id.in_(student_ids))
        attendance_total, attendance_present, attendance_absent = self.session.execute(
            select(
                func.count(AttendanceRecord.id),
                func.sum(case((AttendanceRecord.status == "present", 1), else_=0)),
                func.sum(case((AttendanceRecord.status == "absent", 1), else_=0)),
            ).where(*attendance_conditions)
        ).one()

        invoice_conditions = [InvoiceLine.tenant_id == self.actor.tenant_id, StudentInvoice.state != "cancelled", *self._date_conditions(StudentInvoice.issued_on, filters)]
        if filters.academic_year_id:
            invoice_conditions.append(StudentInvoice.enrollment_id.in_(select(StudentEnrollment.id).where(StudentEnrollment.tenant_id == self.actor.tenant_id, StudentEnrollment.academic_year_id == filters.academic_year_id)))
        fees_invoiced = self.session.scalar(
            select(func.coalesce(func.sum(InvoiceLine.amount - InvoiceLine.discount), 0))
            .select_from(InvoiceLine)
            .join(
                StudentInvoice,
                (StudentInvoice.tenant_id == InvoiceLine.tenant_id)
                & (StudentInvoice.id == InvoiceLine.invoice_id),
            )
            .where(*invoice_conditions)
        )

        payment_conditions = [PaymentAllocation.tenant_id == self.actor.tenant_id, Payment.state == "posted", *self._date_conditions(Payment.created_at, filters)]
        fees_collected = self.session.scalar(
            select(func.coalesce(func.sum(PaymentAllocation.amount), 0))
            .select_from(PaymentAllocation)
            .join(
                Payment,
                (Payment.tenant_id == PaymentAllocation.tenant_id)
                & (Payment.id == PaymentAllocation.payment_id),
            )
            .where(*payment_conditions)
        )

        exam_conditions = [PublishedResult.tenant_id == self.actor.tenant_id, *self._date_conditions(PublishedResult.created_at, filters)]
        if student_ids is not None:
            exam_conditions.append(PublishedResult.student_id.in_(student_ids))
        exams_published, exams_passed = self.session.execute(
            select(
                func.count(PublishedResult.id),
                func.sum(case((PublishedResult.result == "pass", 1), else_=0)),
            ).where(*exam_conditions)
        ).one()

        activity_conditions = [Activity.tenant_id == self.actor.tenant_id, *self._date_conditions(Activity.activity_date, filters)]
        activities_total, activities_published = self.session.execute(
            select(
                func.count(Activity.id),
                func.sum(case((Activity.state == "published", 1), else_=0)),
            ).where(*activity_conditions)
        ).one()

        registration_conditions = [EventRegistration.tenant_id == self.actor.tenant_id]
        achievement_conditions = [Achievement.tenant_id == self.actor.tenant_id]
        if student_ids is not None:
            registration_conditions.append(EventRegistration.student_id.in_(student_ids))
            achievement_conditions.append(Achievement.student_id.in_(student_ids))
        activities_registrations = self.session.scalar(
            select(func.count(EventRegistration.id)).where(*registration_conditions)
        )
        activities_achievements = self.session.scalar(
            select(func.count(Achievement.id)).where(*achievement_conditions)
        )

        notice_conditions = [Notice.tenant_id == self.actor.tenant_id, *self._date_conditions(Notice.created_at, filters)]
        notices_total, notices_published = self.session.execute(
            select(
                func.count(Notice.id),
                func.sum(case((Notice.state == "published", 1), else_=0)),
            ).where(*notice_conditions)
        ).one()

        delivery_conditions = [NoticeDelivery.tenant_id == self.actor.tenant_id, *self._date_conditions(NoticeDelivery.created_at, filters)]
        deliveries_total, deliveries_read = self.session.execute(
            select(
                func.count(NoticeDelivery.id),
                func.sum(case((NoticeDelivery.state == "read", 1), else_=0)),
            ).where(*delivery_conditions)
        ).one()

        invoiced_value = self._to_float(fees_invoiced)
        collected_value = self._to_float(fees_collected)

        return OverviewReport(
            calculated_at=datetime.now(UTC),
            filters=filters,
            definitions=list(REPORT_DEFINITIONS),
            students=StudentsOverview(
                total=students_total or 0,
                active=students_active or 0,
            ),
            attendance=AttendanceOverview(
                total_records=attendance_total or 0,
                present_records=attendance_present or 0,
                absent_records=attendance_absent or 0,
            ),
            fees=FeesOverview(
                total_invoiced=invoiced_value,
                total_collected=collected_value,
                outstanding=invoiced_value - collected_value,
            ),
            examinations=ExaminationsOverview(
                published_results=exams_published or 0,
                passed_results=exams_passed or 0,
            ),
            activities=ActivitiesOverview(
                total_events=activities_total or 0,
                published_events=activities_published or 0,
                registrations=activities_registrations or 0,
                achievements=activities_achievements or 0,
            ),
            communications=CommunicationsOverview(
                total_notices=notices_total or 0,
                published_notices=notices_published or 0,
                deliveries=deliveries_total or 0,
                read_deliveries=deliveries_read or 0,
            ),
        )

    def get_drill_down(
        self,
        metric_key: str,
        filters: ReportFilters,
        skip: int,
        limit: int,
    ) -> PaginatedReportRows:
        """Return source records underlying one supported dashboard metric."""

        if metric_key not in VALID_METRICS:
            raise ValueError("Unsupported report metric")
        student_ids = self._student_ids(filters)
        if metric_key == "students":
            conditions = [Student.tenant_id == self.actor.tenant_id, *self._date_conditions(Student.created_at, filters)]
            if student_ids is not None:
                conditions.append(Student.id.in_(student_ids))
            query = select(Student.id, Person.full_name, Student.status, Student.created_at).join(
                Person,
                (Person.tenant_id == Student.tenant_id) & (Person.id == Student.person_id),
            ).where(*conditions)
            values = [(row.id, row.full_name, row.status, row.created_at.date()) for row in self.session.execute(query.offset(skip).limit(limit)).all()]
        elif metric_key == "attendance":
            conditions = [AttendanceRecord.tenant_id == self.actor.tenant_id, *self._date_conditions(AttendanceRecord.created_at, filters)]
            if student_ids is not None:
                conditions.append(AttendanceRecord.student_id.in_(student_ids))
            query = select(AttendanceRecord.id, AttendanceRecord.status, AttendanceRecord.state, AttendanceRecord.created_at).where(*conditions)
            values = [(row.id, row.status.title(), row.state, row.created_at.date()) for row in self.session.execute(query.offset(skip).limit(limit)).all()]
        elif metric_key == "fees":
            conditions = [StudentInvoice.tenant_id == self.actor.tenant_id, StudentInvoice.state != "cancelled", *self._date_conditions(StudentInvoice.issued_on, filters)]
            if filters.academic_year_id:
                conditions.append(StudentInvoice.enrollment_id.in_(select(StudentEnrollment.id).where(StudentEnrollment.tenant_id == self.actor.tenant_id, StudentEnrollment.academic_year_id == filters.academic_year_id)))
            query = select(StudentInvoice.id, StudentInvoice.invoice_number, StudentInvoice.state, StudentInvoice.issued_on).where(*conditions)
            values = [(row.id, row.invoice_number, row.state, row.issued_on) for row in self.session.execute(query.offset(skip).limit(limit)).all()]
        elif metric_key == "examinations":
            conditions = [PublishedResult.tenant_id == self.actor.tenant_id, *self._date_conditions(PublishedResult.created_at, filters)]
            if student_ids is not None:
                conditions.append(PublishedResult.student_id.in_(student_ids))
            query = select(PublishedResult.id, PublishedResult.grade, PublishedResult.result, PublishedResult.created_at).where(*conditions)
            values = [(row.id, f"Grade {row.grade}", row.result, row.created_at.date()) for row in self.session.execute(query.offset(skip).limit(limit)).all()]
        elif metric_key == "activities":
            query = select(Activity.id, Activity.title, Activity.state, Activity.activity_date).where(
                Activity.tenant_id == self.actor.tenant_id,
                *self._date_conditions(Activity.activity_date, filters),
            )
            values = [(row.id, row.title, row.state, row.activity_date) for row in self.session.execute(query.offset(skip).limit(limit)).all()]
        else:
            query = select(Notice.id, Notice.title, Notice.state, Notice.created_at).where(
                Notice.tenant_id == self.actor.tenant_id,
                *self._date_conditions(Notice.created_at, filters),
            )
            values = [(row.id, row.title, row.state, row.created_at.date()) for row in self.session.execute(query.offset(skip).limit(limit)).all()]
        total = self.session.scalar(select(func.count()).select_from(query.subquery())) or 0
        items = [ReportRow(id=row[0], label=row[1], detail=row[2], occurred_on=row[3]) for row in values]
        return PaginatedReportRows(items=items, total=total)

    def save_report(self, payload: SavedReportCreate) -> SavedReport:
        """Create or update one named report filter owned by the actor."""

        item = self.session.scalar(select(SavedReport).where(SavedReport.tenant_id == self.actor.tenant_id, SavedReport.owner_membership_id == self.actor.membership_id, SavedReport.name == payload.name))
        if item is None:
            item = SavedReport(tenant_id=self.actor.tenant_id, owner_membership_id=self.actor.membership_id, name=payload.name, filters=payload.filters.model_dump(mode="json"))
            self.session.add(item)
        else:
            item.filters = payload.filters.model_dump(mode="json")
        self.session.flush()
        return item

    def list_saved_reports(self) -> list[SavedReport]:
        """Return report filters owned by the current membership."""

        return list(self.session.scalars(select(SavedReport).where(SavedReport.tenant_id == self.actor.tenant_id, SavedReport.owner_membership_id == self.actor.membership_id).order_by(SavedReport.name)))

    def create_export(self, payload: ReportExportCreate) -> tuple[ReportExport, str]:
        """Generate CSV content and persist its permission-scoped audit record."""

        rows = self.get_drill_down(payload.metric_key, payload.filters, 0, 10000)
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(("id", "label", "detail", "occurred_on"))
        for row in rows.items:
            writer.writerow((row.id, row.label, row.detail, row.occurred_on or ""))
        item = ReportExport(tenant_id=self.actor.tenant_id, requested_by_membership_id=self.actor.membership_id, metric_key=payload.metric_key, filters=payload.filters.model_dump(mode="json"), export_format=payload.export_format, state="completed", row_count=len(rows.items))
        self.session.add(item)
        self.session.flush()
        return item, output.getvalue()

    def create_schedule(self, payload: ReportScheduleCreate) -> ReportSchedule:
        """Persist one actor-owned recurring report delivery configuration."""

        if payload.metric_key not in VALID_METRICS:
            raise ValueError("Unsupported report metric")
        item = ReportSchedule(tenant_id=self.actor.tenant_id, owner_membership_id=self.actor.membership_id, name=payload.name, metric_key=payload.metric_key, filters=payload.filters.model_dump(mode="json"), export_format=payload.export_format, frequency=payload.frequency, recipient_email=payload.recipient_email, enabled=True)
        self.session.add(item)
        self.session.flush()
        return item

    def list_schedules(self) -> list[ReportSchedule]:
        """Return recurring report configurations owned by the actor."""

        return list(self.session.scalars(select(ReportSchedule).where(ReportSchedule.tenant_id == self.actor.tenant_id, ReportSchedule.owner_membership_id == self.actor.membership_id).order_by(ReportSchedule.name)))

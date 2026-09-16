"""SQLAlchemy models for tenant-scoped students, guardians, and lifecycle history."""

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKeyConstraint,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin

TENANT_ID_REFERENCE = "tenants.id"
STUDENTS_TENANT_ID_REFERENCE = "students.tenant_id"
STUDENTS_ID_REFERENCE = "students.id"


class Person(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Persist one tenant-scoped person identity that can be reused by students and guardians."""

    __tablename__ = "people"
    __table_args__ = (
        CheckConstraint(
            "email IS NOT NULL OR mobile_number IS NOT NULL",
            name="ck_people_contact_present",
        ),
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "email"),
        UniqueConstraint("tenant_id", "mobile_number"),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    full_name: Mapped[str] = mapped_column(String(240), nullable=False)
    email: Mapped[str | None] = mapped_column(String(320))
    mobile_number: Mapped[str | None] = mapped_column(String(24))
    date_of_birth: Mapped[date | None] = mapped_column(Date)


class Student(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Store one tenant student record linked to a canonical person identity."""

    __tablename__ = "students"
    __table_args__ = (
        CheckConstraint(
            "status IN ('prospective', 'active', 'on_hold', 'graduated', 'discontinued')",
            name="ck_students_status",
        ),
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "person_id"),
        UniqueConstraint("tenant_id", "registration_number"),
        UniqueConstraint("tenant_id", "source_application_id"),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        ForeignKeyConstraint(
            ["tenant_id", "person_id"],
            ["people.tenant_id", "people.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "source_application_id"],
            ["applications.tenant_id", "applications.id"],
            ondelete="RESTRICT",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    person_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    source_application_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    registration_number: Mapped[str] = mapped_column(String(48), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")


class Guardian(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Store one tenant guardian profile linked to a canonical person identity."""

    __tablename__ = "guardians"
    __table_args__ = (
        CheckConstraint(
            "email IS NOT NULL OR mobile_number IS NOT NULL",
            name="ck_guardians_contact_present",
        ),
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "person_id"),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        ForeignKeyConstraint(
            ["tenant_id", "person_id"],
            ["people.tenant_id", "people.id"],
            ondelete="RESTRICT",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    person_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    email: Mapped[str | None] = mapped_column(String(320))
    mobile_number: Mapped[str | None] = mapped_column(String(24))


class StudentGuardian(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Link one student and guardian with relationship metadata for portal visibility."""

    __tablename__ = "student_guardians"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "student_id", "guardian_id"),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        ForeignKeyConstraint(
            ["tenant_id", "student_id"],
            [STUDENTS_TENANT_ID_REFERENCE, STUDENTS_ID_REFERENCE],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "guardian_id"],
            ["guardians.tenant_id", "guardians.id"],
            ondelete="RESTRICT",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    student_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    guardian_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    relationship: Mapped[str] = mapped_column(String(32), nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class StudentEnrollment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Track student program placement for one academic year and section."""

    __tablename__ = "student_enrollments"
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'completed', 'cancelled', 'transferred')",
            name="ck_student_enrollments_status",
        ),
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "student_id", "academic_year_id"),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        ForeignKeyConstraint(
            ["tenant_id", "student_id"],
            [STUDENTS_TENANT_ID_REFERENCE, STUDENTS_ID_REFERENCE],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "academic_year_id"],
            ["academic_years.tenant_id", "academic_years.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "program_id"],
            ["programs.tenant_id", "programs.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "batch_id"],
            ["batches.tenant_id", "batches.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "section_id"],
            ["sections.tenant_id", "sections.id"],
            ondelete="RESTRICT",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    student_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    academic_year_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    program_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    batch_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    section_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")


class StudentStatusHistory(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Persist auditable status transitions for each student lifecycle movement."""

    __tablename__ = "student_status_history"
    __table_args__ = (
        CheckConstraint(
            "from_status IN ('prospective', 'active', 'on_hold', 'graduated', 'discontinued')",
            name="ck_student_status_history_from_status",
        ),
        CheckConstraint(
            "to_status IN ('prospective', 'active', 'on_hold', 'graduated', 'discontinued')",
            name="ck_student_status_history_to_status",
        ),
        UniqueConstraint("tenant_id", "id"),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        ForeignKeyConstraint(
            ["tenant_id", "student_id"],
            [STUDENTS_TENANT_ID_REFERENCE, STUDENTS_ID_REFERENCE],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "changed_by_membership_id"],
            ["tenant_memberships.tenant_id", "tenant_memberships.id"],
            ondelete="RESTRICT",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    student_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    from_status: Mapped[str] = mapped_column(String(16), nullable=False)
    to_status: Mapped[str] = mapped_column(String(16), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    changed_by_membership_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)


class StudentDocument(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Track student document metadata and staff verification without storing binary content."""

    __tablename__ = "student_documents"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'verified', 'rejected')", name="ck_student_documents_status"
        ),
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "student_id", "category", "document_number"),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        ForeignKeyConstraint(
            ["tenant_id", "student_id"],
            [STUDENTS_TENANT_ID_REFERENCE, STUDENTS_ID_REFERENCE],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "media_object_id"],
            ["tenant_media_objects.tenant_id", "tenant_media_objects.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "verified_by_membership_id"],
            ["tenant_memberships.tenant_id", "tenant_memberships.id"],
            ondelete="RESTRICT",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    student_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    category: Mapped[str] = mapped_column(String(48), nullable=False)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    document_number: Mapped[str | None] = mapped_column(String(80))
    media_object_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    reference_url: Mapped[str | None] = mapped_column(String(500))
    issued_on: Mapped[date | None] = mapped_column(Date)
    expires_on: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    notes: Mapped[str | None] = mapped_column(Text)
    verified_by_membership_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class StudentSubjectRegistration(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Register one enrollment into one tenant-safe subject offering."""

    __tablename__ = "student_subject_registrations"
    __table_args__ = (
        CheckConstraint(
            "status IN ('registered', 'dropped', 'completed')",
            name="ck_student_subject_registrations_status",
        ),
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "enrollment_id", "subject_offering_id"),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        ForeignKeyConstraint(
            ["tenant_id", "student_id"],
            [STUDENTS_TENANT_ID_REFERENCE, STUDENTS_ID_REFERENCE],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "enrollment_id"],
            ["student_enrollments.tenant_id", "student_enrollments.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "subject_offering_id"],
            ["subject_offerings.tenant_id", "subject_offerings.id"],
            ondelete="RESTRICT",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    student_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    enrollment_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    subject_offering_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="registered")
    registered_on: Mapped[date] = mapped_column(Date, nullable=False)


class StudentProgression(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Prepare and decide one effective next-enrollment progression outcome."""

    __tablename__ = "student_progressions"
    __table_args__ = (
        CheckConstraint(
            "state IN ('prepared', 'approved', 'rejected', 'applied')",
            name="ck_student_progressions_state",
        ),
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "student_id", "from_enrollment_id"),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        ForeignKeyConstraint(
            ["tenant_id", "student_id"],
            [STUDENTS_TENANT_ID_REFERENCE, STUDENTS_ID_REFERENCE],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "from_enrollment_id"],
            ["student_enrollments.tenant_id", "student_enrollments.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "target_academic_year_id"],
            ["academic_years.tenant_id", "academic_years.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "target_program_id"],
            ["programs.tenant_id", "programs.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "target_batch_id"],
            ["batches.tenant_id", "batches.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "target_section_id"],
            ["sections.tenant_id", "sections.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "applied_enrollment_id"],
            ["student_enrollments.tenant_id", "student_enrollments.id"],
            ondelete="RESTRICT",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    student_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    from_enrollment_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    target_academic_year_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    target_program_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    target_batch_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    target_section_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    state: Mapped[str] = mapped_column(String(16), nullable=False, default="prepared")
    decision_reason: Mapped[str | None] = mapped_column(Text)
    applied_enrollment_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))


class StudentLifecycleRequest(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Control one transfer or readmission request through explicit reviewed states."""

    __tablename__ = "student_lifecycle_requests"
    __table_args__ = (
        CheckConstraint(
            "request_type IN ('transfer', 'readmission')", name="ck_student_lifecycle_requests_type"
        ),
        CheckConstraint(
            "state IN ('requested', 'approved', 'rejected', 'completed')",
            name="ck_student_lifecycle_requests_state",
        ),
        UniqueConstraint("tenant_id", "id"),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        ForeignKeyConstraint(
            ["tenant_id", "student_id"],
            [STUDENTS_TENANT_ID_REFERENCE, STUDENTS_ID_REFERENCE],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "from_enrollment_id"],
            ["student_enrollments.tenant_id", "student_enrollments.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "target_academic_year_id"],
            ["academic_years.tenant_id", "academic_years.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "target_program_id"],
            ["programs.tenant_id", "programs.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "target_batch_id"],
            ["batches.tenant_id", "batches.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "target_section_id"],
            ["sections.tenant_id", "sections.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "reviewed_by_membership_id"],
            ["tenant_memberships.tenant_id", "tenant_memberships.id"],
            ondelete="RESTRICT",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    student_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    request_type: Mapped[str] = mapped_column(String(16), nullable=False)
    from_enrollment_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    target_academic_year_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    target_program_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    target_batch_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    target_section_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    state: Mapped[str] = mapped_column(String(16), nullable=False, default="requested")
    decision_reason: Mapped[str | None] = mapped_column(Text)
    reviewed_by_membership_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class StudentCertificateRequest(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Track a student certificate request from submission through issuance."""

    __tablename__ = "student_certificate_requests"
    __table_args__ = (
        CheckConstraint(
            "state IN ('requested', 'approved', 'rejected', 'issued')",
            name="ck_student_certificate_requests_state",
        ),
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "issued_reference"),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        ForeignKeyConstraint(
            ["tenant_id", "student_id"],
            [STUDENTS_TENANT_ID_REFERENCE, STUDENTS_ID_REFERENCE],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "reviewed_by_membership_id"],
            ["tenant_memberships.tenant_id", "tenant_memberships.id"],
            ondelete="RESTRICT",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    student_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    certificate_type: Mapped[str] = mapped_column(String(48), nullable=False)
    purpose: Mapped[str] = mapped_column(Text, nullable=False)
    state: Mapped[str] = mapped_column(String(16), nullable=False, default="requested")
    decision_reason: Mapped[str | None] = mapped_column(Text)
    issued_reference: Mapped[str | None] = mapped_column(String(80))
    reviewed_by_membership_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

"""SQLAlchemy models for tenant-scoped admissions campaigns and application lifecycle."""

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKeyConstraint,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin

TENANT_ID_REFERENCE = "tenants.id"


class AdmissionCampaign(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Define one tenant admission intake cycle mapped to an academic year and program."""

    __tablename__ = "admission_campaigns"
    __table_args__ = (
        CheckConstraint(
            "state IN ('draft', 'published', 'closed', 'archived')",
            name="ck_admission_campaigns_state",
        ),
        CheckConstraint("starts_on <= ends_on", name="ck_admission_campaigns_date_window"),
        UniqueConstraint("tenant_id", "code"),
        UniqueConstraint("tenant_id", "id"),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
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
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    academic_year_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    program_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    code: Mapped[str] = mapped_column(String(40), nullable=False)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    starts_on: Mapped[date] = mapped_column(Date, nullable=False)
    ends_on: Mapped[date] = mapped_column(Date, nullable=False)
    state: Mapped[str] = mapped_column(String(16), nullable=False, default="draft")


class AdmissionEnquiry(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Track a prospective applicant from initial contact through qualification."""

    __tablename__ = "admission_enquiries"
    __table_args__ = (
        CheckConstraint(
            "email IS NOT NULL OR mobile_number IS NOT NULL",
            name="ck_admission_enquiries_contact_present",
        ),
        CheckConstraint(
            "state IN ('new', 'contacted', 'qualified', 'converted', 'closed')",
            name="ck_admission_enquiries_state",
        ),
        UniqueConstraint("tenant_id", "id"),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        ForeignKeyConstraint(
            ["tenant_id", "campaign_id"],
            ["admission_campaigns.tenant_id", "admission_campaigns.id"],
            ondelete="RESTRICT",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    campaign_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    first_name: Mapped[str] = mapped_column(String(120), nullable=False)
    last_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str | None] = mapped_column(String(320))
    mobile_number: Mapped[str | None] = mapped_column(String(24))
    source: Mapped[str] = mapped_column(String(80), nullable=False, default="direct")
    state: Mapped[str] = mapped_column(String(16), nullable=False, default="new")
    notes: Mapped[str | None] = mapped_column(Text)
    next_follow_up_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Applicant(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Persist tenant applicant identity and contact data for admissions workflows."""

    __tablename__ = "applicants"
    __table_args__ = (
        CheckConstraint(
            "email IS NOT NULL OR mobile_number IS NOT NULL",
            name="ck_applicants_contact_present",
        ),
        UniqueConstraint("tenant_id", "id"),
        UniqueConstraint("tenant_id", "email"),
        UniqueConstraint("tenant_id", "mobile_number"),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    first_name: Mapped[str] = mapped_column(String(120), nullable=False)
    last_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str | None] = mapped_column(String(320))
    mobile_number: Mapped[str | None] = mapped_column(String(24))
    date_of_birth: Mapped[date | None] = mapped_column(Date)


class ApplicantAccess(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Bind one tenant membership to the applicant record it may access."""

    __tablename__ = "applicant_access"
    __table_args__ = (
        UniqueConstraint("tenant_id", "applicant_id"),
        UniqueConstraint("tenant_id", "membership_id"),
        UniqueConstraint("tenant_id", "id"),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        ForeignKeyConstraint(
            ["tenant_id", "applicant_id"],
            ["applicants.tenant_id", "applicants.id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "membership_id"],
            ["tenant_memberships.tenant_id", "tenant_memberships.id"],
            ondelete="CASCADE",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    applicant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    membership_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)


class TenantMediaObject(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Store authorization-safe metadata for one tenant-owned binary object."""

    __tablename__ = "tenant_media_objects"
    __table_args__ = (
        CheckConstraint(
            "state IN ('pending', 'available', 'quarantined', 'deleted')",
            name="ck_tenant_media_objects_state",
        ),
        CheckConstraint("size_bytes > 0", name="ck_tenant_media_objects_positive_size"),
        UniqueConstraint("tenant_id", "object_key"),
        UniqueConstraint("tenant_id", "id"),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        ForeignKeyConstraint(
            ["tenant_id", "uploaded_by_membership_id"],
            ["tenant_memberships.tenant_id", "tenant_memberships.id"],
            ondelete="RESTRICT",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    uploaded_by_membership_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    object_key: Mapped[str] = mapped_column(String(512), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(120), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    checksum_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    state: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    retention_until: Mapped[date | None] = mapped_column(Date)


class Application(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Store one applicant submission under a campaign with generated application number."""

    __tablename__ = "applications"
    __table_args__ = (
        CheckConstraint(
            "state IN ('draft', 'submitted', 'under_review', 'verified', 'selected', "
            "'offered', 'accepted', 'rejected', 'waitlisted', 'withdrawn', 'cancelled')",
            name="ck_applications_state",
        ),
        UniqueConstraint("tenant_id", "application_number"),
        UniqueConstraint("tenant_id", "id"),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        ForeignKeyConstraint(
            ["tenant_id", "campaign_id"],
            ["admission_campaigns.tenant_id", "admission_campaigns.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "applicant_id"],
            ["applicants.tenant_id", "applicants.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "program_id"],
            ["programs.tenant_id", "programs.id"],
            ondelete="RESTRICT",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    campaign_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    applicant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    program_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    application_number: Mapped[str] = mapped_column(String(48), nullable=False)
    state: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    remarks: Mapped[str | None] = mapped_column(Text)


class ApplicationDocument(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Track submitted document metadata and verification decisions per application."""

    __tablename__ = "application_documents"
    __table_args__ = (
        CheckConstraint(
            "verification_state IN ('pending', 'verified', 'rejected')",
            name="ck_application_documents_verification_state",
        ),
        UniqueConstraint("tenant_id", "application_id", "document_type"),
        UniqueConstraint("tenant_id", "id"),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        ForeignKeyConstraint(
            ["tenant_id", "application_id"],
            ["applications.tenant_id", "applications.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "media_object_id"],
            ["tenant_media_objects.tenant_id", "tenant_media_objects.id"],
            ondelete="RESTRICT",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    application_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    document_type: Mapped[str] = mapped_column(String(48), nullable=False)
    document_number: Mapped[str | None] = mapped_column(String(80))
    media_object_id: Mapped[UUID | None] = mapped_column(Uuid(as_uuid=True))
    file_url: Mapped[str | None] = mapped_column(String(2048))
    verification_state: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    verified_by: Mapped[str | None] = mapped_column(String(240))
    verification_notes: Mapped[str | None] = mapped_column(Text)


class SeatPool(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Define category-wise seat capacity for one campaign under tenant constraints."""

    __tablename__ = "seat_pools"
    __table_args__ = (
        CheckConstraint("seat_capacity >= 0", name="ck_seat_pools_capacity_non_negative"),
        CheckConstraint("filled_seats >= 0", name="ck_seat_pools_filled_non_negative"),
        CheckConstraint("filled_seats <= seat_capacity", name="ck_seat_pools_filled_le_capacity"),
        UniqueConstraint("tenant_id", "campaign_id", "category_code"),
        UniqueConstraint("tenant_id", "id"),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        ForeignKeyConstraint(
            ["tenant_id", "campaign_id"],
            ["admission_campaigns.tenant_id", "admission_campaigns.id"],
            ondelete="RESTRICT",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    campaign_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    category_code: Mapped[str] = mapped_column(String(24), nullable=False)
    category_name: Mapped[str] = mapped_column(String(120), nullable=False)
    seat_capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    filled_seats: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class AdmissionOffer(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Persist offer issuance outcomes tied to applications and category seat pools."""

    __tablename__ = "admission_offers"
    __table_args__ = (
        CheckConstraint(
            "state IN ('issued', 'accepted', 'declined', 'expired', 'cancelled')",
            name="ck_admission_offers_state",
        ),
        UniqueConstraint("tenant_id", "offer_number"),
        UniqueConstraint("tenant_id", "application_id"),
        UniqueConstraint("tenant_id", "id"),
        ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        ForeignKeyConstraint(
            ["tenant_id", "application_id"],
            ["applications.tenant_id", "applications.id"],
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "seat_pool_id"],
            ["seat_pools.tenant_id", "seat_pools.id"],
            ondelete="RESTRICT",
        ),
    )

    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    application_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    seat_pool_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    offer_number: Mapped[str] = mapped_column(String(48), nullable=False)
    offered_on: Mapped[date] = mapped_column(Date, nullable=False)
    expires_on: Mapped[date] = mapped_column(Date, nullable=False)
    state: Mapped[str] = mapped_column(String(16), nullable=False, default="issued")
    notes: Mapped[str | None] = mapped_column(Text)

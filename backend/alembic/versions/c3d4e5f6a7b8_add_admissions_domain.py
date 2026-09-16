"""add admissions domain

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-08-29 18:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "c3d4e5f6a7b8"
down_revision: str | None = "b2c3d4e5f6a7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None
TENANT_ID_REFERENCE = "tenants.id"


def _timestamp_columns() -> tuple[sa.Column, sa.Column]:
    """Return standard creation and update timestamp columns for tenant tables."""

    return (
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )


def _apply_tenant_rls(table_names: list[str]) -> None:
    """Enable RLS and apply null-safe tenant policies scoped to all roles."""

    for table_name in table_names:
        op.execute(f"ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table_name} FORCE ROW LEVEL SECURITY")
        op.execute(
            sa.text(
                f"""
                CREATE POLICY tenant_isolation ON {table_name}
                AS PERMISSIVE
                FOR ALL
                TO PUBLIC
                USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid)
                WITH CHECK (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid)
                """
            )
        )


def upgrade() -> None:
    """Create admissions persistence tables with tenant-safe constraints and RLS."""

    op.create_table(
        "admission_campaigns",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("academic_year_id", sa.Uuid(), nullable=False),
        sa.Column("program_id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(length=40), nullable=False),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("starts_on", sa.Date(), nullable=False),
        sa.Column("ends_on", sa.Date(), nullable=False),
        sa.Column("state", sa.String(length=16), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        *_timestamp_columns(),
        sa.CheckConstraint(
            "state IN ('draft', 'published', 'closed', 'archived')",
            name="ck_admission_campaigns_state",
        ),
        sa.CheckConstraint("starts_on <= ends_on", name="ck_admission_campaigns_date_window"),
        sa.ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "academic_year_id"],
            ["academic_years.tenant_id", "academic_years.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "program_id"],
            ["programs.tenant_id", "programs.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "code"),
        sa.UniqueConstraint("tenant_id", "id"),
    )

    op.create_table(
        "applicants",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("first_name", sa.String(length=120), nullable=False),
        sa.Column("last_name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("mobile_number", sa.String(length=24), nullable=True),
        sa.Column("date_of_birth", sa.Date(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        *_timestamp_columns(),
        sa.CheckConstraint(
            "email IS NOT NULL OR mobile_number IS NOT NULL",
            name="ck_applicants_contact_present",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id"),
        sa.UniqueConstraint("tenant_id", "email"),
        sa.UniqueConstraint("tenant_id", "mobile_number"),
    )

    op.create_table(
        "applications",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("campaign_id", sa.Uuid(), nullable=False),
        sa.Column("applicant_id", sa.Uuid(), nullable=False),
        sa.Column("program_id", sa.Uuid(), nullable=False),
        sa.Column("application_number", sa.String(length=48), nullable=False),
        sa.Column("state", sa.String(length=20), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        *_timestamp_columns(),
        sa.CheckConstraint(
            "state IN ('draft', 'submitted', 'under_review', 'verified', 'selected', "
            "'offered', 'accepted', 'rejected', 'waitlisted', 'withdrawn', 'cancelled')",
            name="ck_applications_state",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "campaign_id"],
            ["admission_campaigns.tenant_id", "admission_campaigns.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "applicant_id"],
            ["applicants.tenant_id", "applicants.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "program_id"],
            ["programs.tenant_id", "programs.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "application_number"),
        sa.UniqueConstraint("tenant_id", "id"),
    )

    op.create_table(
        "application_documents",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("application_id", sa.Uuid(), nullable=False),
        sa.Column("document_type", sa.String(length=48), nullable=False),
        sa.Column("document_number", sa.String(length=80), nullable=True),
        sa.Column("file_url", sa.String(length=2048), nullable=True),
        sa.Column("verification_state", sa.String(length=16), nullable=False),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verified_by", sa.String(length=240), nullable=True),
        sa.Column("verification_notes", sa.Text(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        *_timestamp_columns(),
        sa.CheckConstraint(
            "verification_state IN ('pending', 'verified', 'rejected')",
            name="ck_application_documents_verification_state",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "application_id"],
            ["applications.tenant_id", "applications.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "application_id", "document_type"),
        sa.UniqueConstraint("tenant_id", "id"),
    )

    op.create_table(
        "seat_pools",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("campaign_id", sa.Uuid(), nullable=False),
        sa.Column("category_code", sa.String(length=24), nullable=False),
        sa.Column("category_name", sa.String(length=120), nullable=False),
        sa.Column("seat_capacity", sa.Integer(), nullable=False),
        sa.Column("filled_seats", sa.Integer(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        *_timestamp_columns(),
        sa.CheckConstraint("seat_capacity >= 0", name="ck_seat_pools_capacity_non_negative"),
        sa.CheckConstraint("filled_seats >= 0", name="ck_seat_pools_filled_non_negative"),
        sa.CheckConstraint("filled_seats <= seat_capacity", name="ck_seat_pools_filled_le_capacity"),
        sa.ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "campaign_id"],
            ["admission_campaigns.tenant_id", "admission_campaigns.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "campaign_id", "category_code"),
        sa.UniqueConstraint("tenant_id", "id"),
    )

    op.create_table(
        "admission_offers",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("application_id", sa.Uuid(), nullable=False),
        sa.Column("seat_pool_id", sa.Uuid(), nullable=False),
        sa.Column("offer_number", sa.String(length=48), nullable=False),
        sa.Column("offered_on", sa.Date(), nullable=False),
        sa.Column("expires_on", sa.Date(), nullable=False),
        sa.Column("state", sa.String(length=16), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        *_timestamp_columns(),
        sa.CheckConstraint(
            "state IN ('issued', 'accepted', 'declined', 'expired', 'cancelled')",
            name="ck_admission_offers_state",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], [TENANT_ID_REFERENCE], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "application_id"],
            ["applications.tenant_id", "applications.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "seat_pool_id"],
            ["seat_pools.tenant_id", "seat_pools.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "offer_number"),
        sa.UniqueConstraint("tenant_id", "application_id"),
        sa.UniqueConstraint("tenant_id", "id"),
    )

    tenant_tables = [
        "admission_campaigns",
        "applicants",
        "applications",
        "application_documents",
        "seat_pools",
        "admission_offers",
    ]
    _apply_tenant_rls(tenant_tables)

    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'cms_runtime') THEN
                GRANT SELECT, INSERT, UPDATE ON
                    admission_campaigns,
                    applicants,
                    applications,
                    application_documents,
                    seat_pools,
                    admission_offers
                TO cms_runtime;
            END IF;
        END
        $$
        """
    )


def downgrade() -> None:
    """Drop admissions domain tables created by this revision."""

    op.drop_table("admission_offers")
    op.drop_table("seat_pools")
    op.drop_table("application_documents")
    op.drop_table("applications")
    op.drop_table("applicants")
    op.drop_table("admission_campaigns")

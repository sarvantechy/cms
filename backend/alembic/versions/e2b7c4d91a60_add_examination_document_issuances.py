"""Add immutable examination document issuance metadata.

Revision ID: e2b7c4d91a60
Revises: c91e4a7d2b60
Create Date: 2026-09-17
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "e2b7c4d91a60"
down_revision: str | None = "c91e4a7d2b60"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TABLES = ("hall_ticket_issuances", "grade_card_issuances", "transcript_issuances")
SERVER_NOW = sa.text("now()")


def _secure_table(table_name: str) -> None:
    """Enable forced tenant RLS and grant only required runtime privileges."""

    op.execute(sa.text(f"ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY"))
    op.execute(sa.text(f"ALTER TABLE {table_name} FORCE ROW LEVEL SECURITY"))
    op.execute(
        sa.text(
            f"CREATE POLICY {table_name}_tenant_isolation ON {table_name} "
            "USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid) "
            "WITH CHECK (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid)"
        )
    )
    op.execute(sa.text(f"GRANT SELECT, INSERT ON {table_name} TO cms_runtime"))


def _timestamps() -> tuple[sa.Column, sa.Column]:
    """Return standard immutable-record timestamp columns."""

    return (
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=SERVER_NOW, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=SERVER_NOW, nullable=False),
    )


def upgrade() -> None:
    """Create hall-ticket, grade-card, and transcript issuance metadata."""

    created_at, updated_at = _timestamps()
    op.create_table(
        "hall_ticket_issuances",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("ticket_number", sa.String(length=64), nullable=False),
        sa.Column("registration_ids", sa.JSON(), nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("issued_by_membership_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        created_at,
        updated_at,
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "student_id"],
            ["students.tenant_id", "students.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "session_id"],
            ["exam_sessions.tenant_id", "exam_sessions.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "issued_by_membership_id"],
            ["tenant_memberships.tenant_id", "tenant_memberships.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id"),
        sa.UniqueConstraint("tenant_id", "ticket_number"),
        sa.UniqueConstraint("tenant_id", "student_id", "session_id"),
    )
    op.create_index(
        "ix_hall_ticket_issuances_student",
        "hall_ticket_issuances",
        ["tenant_id", "student_id", "issued_at"],
    )

    created_at, updated_at = _timestamps()
    op.create_table(
        "grade_card_issuances",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("result_id", sa.Uuid(), nullable=False),
        sa.Column("publication_version", sa.Integer(), nullable=False),
        sa.Column("card_number", sa.String(length=64), nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("issued_by_membership_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        created_at,
        updated_at,
        sa.CheckConstraint("publication_version > 0", name="ck_grade_card_issuances_version"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "result_id"],
            ["published_results.tenant_id", "published_results.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "issued_by_membership_id"],
            ["tenant_memberships.tenant_id", "tenant_memberships.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id"),
        sa.UniqueConstraint("tenant_id", "card_number"),
        sa.UniqueConstraint("tenant_id", "result_id", "publication_version"),
    )
    op.create_index(
        "ix_grade_card_issuances_result",
        "grade_card_issuances",
        ["tenant_id", "result_id", "publication_version"],
    )

    created_at, updated_at = _timestamps()
    op.create_table(
        "transcript_issuances",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("student_id", sa.Uuid(), nullable=False),
        sa.Column("transcript_number", sa.String(length=64), nullable=False),
        sa.Column("version_hash", sa.String(length=64), nullable=False),
        sa.Column("result_versions", sa.JSON(), nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("issued_by_membership_id", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        created_at,
        updated_at,
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "student_id"],
            ["students.tenant_id", "students.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "issued_by_membership_id"],
            ["tenant_memberships.tenant_id", "tenant_memberships.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id"),
        sa.UniqueConstraint("tenant_id", "transcript_number"),
        sa.UniqueConstraint("tenant_id", "student_id", "version_hash"),
    )
    op.create_index(
        "ix_transcript_issuances_student",
        "transcript_issuances",
        ["tenant_id", "student_id", "issued_at"],
    )

    for table_name in TABLES:
        _secure_table(table_name)


def downgrade() -> None:
    """Drop examination document issuance metadata."""

    for table_name in reversed(TABLES):
        op.execute(sa.text(f"REVOKE ALL PRIVILEGES ON {table_name} FROM cms_runtime"))
        op.execute(sa.text(f"DROP POLICY IF EXISTS {table_name}_tenant_isolation ON {table_name}"))
    op.drop_index("ix_transcript_issuances_student", table_name="transcript_issuances")
    op.drop_table("transcript_issuances")
    op.drop_index("ix_grade_card_issuances_result", table_name="grade_card_issuances")
    op.drop_table("grade_card_issuances")
    op.drop_index("ix_hall_ticket_issuances_student", table_name="hall_ticket_issuances")
    op.drop_table("hall_ticket_issuances")
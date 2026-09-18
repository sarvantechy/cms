"""Add versioned timetable publication snapshots.

Revision ID: c91e4a7d2b60
Revises: f8cd51ae2d03
Create Date: 2026-09-17
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "c91e4a7d2b60"
down_revision: str | None = "f8cd51ae2d03"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TABLES = ("timetable_publications", "timetable_publication_lines")
SERVER_NOW = sa.text("now()")


def _secure_table(table_name: str) -> None:
    """Enable forced tenant RLS and grant restricted runtime access."""

    op.execute(sa.text(f"ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY"))
    op.execute(sa.text(f"ALTER TABLE {table_name} FORCE ROW LEVEL SECURITY"))
    op.execute(
        sa.text(
            f"CREATE POLICY {table_name}_tenant_isolation ON {table_name} "
            "USING (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid) "
            "WITH CHECK (tenant_id = NULLIF(current_setting('app.tenant_id', true), '')::uuid)"
        )
    )
    op.execute(sa.text(f"GRANT SELECT, INSERT, UPDATE ON {table_name} TO cms_runtime"))


def upgrade() -> None:
    """Create versioned timetable publication metadata and immutable snapshot lines."""

    op.create_table(
        "timetable_publications",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("term_id", sa.Uuid(), nullable=False),
        sa.Column("scope_type", sa.String(length=24), nullable=False),
        sa.Column("scope_reference_id", sa.Uuid(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("state", sa.String(length=16), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("published_by_membership_id", sa.Uuid(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=SERVER_NOW,
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=SERVER_NOW,
            nullable=False,
        ),
        sa.CheckConstraint(
            "scope_type IN ('institution', 'department')",
            name="ck_timetable_publications_scope_type",
        ),
        sa.CheckConstraint(
            "state IN ('published', 'superseded')",
            name="ck_timetable_publications_state",
        ),
        sa.CheckConstraint(
            "version > 0",
            name="ck_timetable_publications_positive_version",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "term_id"],
            ["terms.tenant_id", "terms.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "published_by_membership_id"],
            ["tenant_memberships.tenant_id", "tenant_memberships.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id"),
        sa.UniqueConstraint(
            "tenant_id",
            "term_id",
            "scope_type",
            "scope_reference_id",
            "version",
            name="uq_timetable_publications_scope_version",
            postgresql_nulls_not_distinct=True,
        ),
    )
    op.create_index(
        "ix_timetable_publications_scope_history",
        "timetable_publications",
        ["tenant_id", "term_id", "scope_type", "scope_reference_id", "version"],
    )
    op.create_table(
        "timetable_publication_lines",
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("publication_id", sa.Uuid(), nullable=False),
        sa.Column("source_period_id", sa.Uuid(), nullable=False),
        sa.Column("offering_id", sa.Uuid(), nullable=False),
        sa.Column("subject_id", sa.Uuid(), nullable=False),
        sa.Column("section_id", sa.Uuid(), nullable=False),
        sa.Column("faculty_id", sa.Uuid(), nullable=False),
        sa.Column("room_id", sa.Uuid(), nullable=True),
        sa.Column("subject_code", sa.String(length=32), nullable=False),
        sa.Column("subject_name", sa.String(length=240), nullable=False),
        sa.Column("section_code", sa.String(length=16), nullable=False),
        sa.Column("section_name", sa.String(length=120), nullable=False),
        sa.Column("faculty_employee_code", sa.String(length=48), nullable=False),
        sa.Column("room_code", sa.String(length=32), nullable=True),
        sa.Column("room_name", sa.String(length=240), nullable=True),
        sa.Column("day_of_week", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=SERVER_NOW,
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=SERVER_NOW,
            nullable=False,
        ),
        sa.CheckConstraint(
            "day_of_week BETWEEN 1 AND 7",
            name="ck_timetable_publication_lines_day_of_week",
        ),
        sa.CheckConstraint(
            "start_time < end_time",
            name="ck_timetable_publication_lines_time_range",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "publication_id"],
            ["timetable_publications.tenant_id", "timetable_publications.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id"),
        sa.UniqueConstraint(
            "tenant_id",
            "publication_id",
            "source_period_id",
            name="uq_timetable_publication_lines_source_period",
        ),
    )
    op.create_index(
        "ix_timetable_publication_lines_publication",
        "timetable_publication_lines",
        ["tenant_id", "publication_id", "day_of_week", "start_time"],
    )
    for table_name in TABLES:
        _secure_table(table_name)


def downgrade() -> None:
    """Drop timetable publication snapshot storage."""

    for table_name in reversed(TABLES):
        op.execute(sa.text(f"REVOKE ALL PRIVILEGES ON {table_name} FROM cms_runtime"))
        op.execute(sa.text(f"DROP POLICY IF EXISTS {table_name}_tenant_isolation ON {table_name}"))
    op.drop_index(
        "ix_timetable_publication_lines_publication",
        table_name="timetable_publication_lines",
    )
    op.drop_table("timetable_publication_lines")
    op.drop_index(
        "ix_timetable_publications_scope_history",
        table_name="timetable_publications",
    )
    op.drop_table("timetable_publications")

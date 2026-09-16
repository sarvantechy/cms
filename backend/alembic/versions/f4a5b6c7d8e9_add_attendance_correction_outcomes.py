"""Add requested outcomes to attendance corrections.

Revision ID: f4a5b6c7d8e9
Revises: e3f4a5b6c7d8
Create Date: 2026-08-29
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "f4a5b6c7d8e9"
down_revision: str | None = "e3f4a5b6c7d8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

ATTENDANCE_STATUS_SQL = "'present', 'absent', 'late', 'excused'"


def upgrade() -> None:
    """Persist original and requested statuses for every correction request."""

    op.add_column(
        "attendance_corrections",
        sa.Column("original_status", sa.String(length=16), nullable=True),
    )
    op.add_column(
        "attendance_corrections",
        sa.Column("requested_status", sa.String(length=16), nullable=True),
    )
    op.execute(
        """
        UPDATE attendance_corrections AS correction
        SET original_status = record.status,
            requested_status = record.status
        FROM attendance_records AS record
        WHERE record.tenant_id = correction.tenant_id
          AND record.id = correction.record_id
        """
    )
    op.create_check_constraint(
        "ck_attendance_corrections_original_status",
        "attendance_corrections",
        f"original_status IN ({ATTENDANCE_STATUS_SQL})",
    )
    op.create_check_constraint(
        "ck_attendance_corrections_requested_status",
        "attendance_corrections",
        f"requested_status IN ({ATTENDANCE_STATUS_SQL})",
    )


def downgrade() -> None:
    """Remove correction outcome fields while preserving correction history rows."""

    op.drop_constraint(
        "ck_attendance_corrections_requested_status",
        "attendance_corrections",
        type_="check",
    )
    op.drop_constraint(
        "ck_attendance_corrections_original_status",
        "attendance_corrections",
        type_="check",
    )
    op.drop_column("attendance_corrections", "requested_status")
    op.drop_column("attendance_corrections", "original_status")

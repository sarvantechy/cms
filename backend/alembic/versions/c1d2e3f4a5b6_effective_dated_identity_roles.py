"""Support effective-dated tenant role administration.

Revision ID: c1d2e3f4a5b6
Revises: b8c9d0e1f2a3
Create Date: 2026-08-29
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c1d2e3f4a5b6"
down_revision: str | None = "b8c9d0e1f2a3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Enable append-only role assignments and deactivatable role permissions."""

    op.drop_constraint(
        "membership_role_assignments_tenant_id_membership_id_role_id_key",
        "membership_role_assignments",
        type_="unique",
    )
    op.create_index(
        "uq_membership_role_assignments_active",
        "membership_role_assignments",
        ["tenant_id", "membership_id", "role_id"],
        unique=True,
        postgresql_where=sa.text("ends_at IS NULL"),
    )
    op.add_column(
        "tenant_role_permissions",
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
    )


def downgrade() -> None:
    """Restore lifetime assignment uniqueness and immutable role permissions."""

    op.drop_column("tenant_role_permissions", "is_active")
    op.drop_index("uq_membership_role_assignments_active", table_name="membership_role_assignments")
    op.create_unique_constraint(
        "membership_role_assignments_tenant_id_membership_id_role_id_key",
        "membership_role_assignments",
        ["tenant_id", "membership_id", "role_id"],
    )
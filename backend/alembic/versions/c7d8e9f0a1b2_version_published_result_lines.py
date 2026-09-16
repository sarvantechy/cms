"""Version published result line snapshots.

Revision ID: c7d8e9f0a1b2
Revises: b6c7d8e9f0a1
Create Date: 2026-08-29
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "c7d8e9f0a1b2"
down_revision: str | None = "b6c7d8e9f0a1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add publication version to immutable result line snapshots."""

    op.add_column(
        "published_result_lines",
        sa.Column("publication_version", sa.Integer(), nullable=False, server_default="1"),
    )
    op.drop_constraint(
        "published_result_lines_tenant_id_result_id_registration_id_key",
        "published_result_lines",
        type_="unique",
    )
    op.create_unique_constraint(
        "uq_published_result_lines_result_version_registration",
        "published_result_lines",
        ["tenant_id", "result_id", "publication_version", "registration_id"],
    )


def downgrade() -> None:
    """Restore one unversioned line per result registration."""

    op.drop_constraint(
        "uq_published_result_lines_result_version_registration",
        "published_result_lines",
        type_="unique",
    )
    op.create_unique_constraint(
        "published_result_lines_tenant_id_result_id_registration_id_key",
        "published_result_lines",
        ["tenant_id", "result_id", "registration_id"],
    )
    op.drop_column("published_result_lines", "publication_version")
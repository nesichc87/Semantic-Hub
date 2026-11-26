"""Create catalog tables sources and source_loads."""

import sqlalchemy as sa
from alembic import op


revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sources",
        sa.Column("id", sa.String(100), primary_key=True),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("config", sa.JSON(), nullable=False),
        sa.Column("prefixes", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("status_reason", sa.Text(), nullable=True),
        sa.Column("license", sa.String(200), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "source_loads",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "source_id",
            sa.String(100),
            sa.ForeignKey("sources.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("outcome", sa.String(10), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("from_cache", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index("ix_source_loads_source_id", "source_loads", ["source_id"])


def downgrade() -> None:
    op.drop_index("ix_source_loads_source_id", table_name="source_loads")
    op.drop_table("source_loads")
    op.drop_table("sources")
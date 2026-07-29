"""add_smlmv_parametros_table

Revision ID: e8f9a0b1c2d3
Revises: dd865bb526a6
Create Date: 2026-07-29 17:00:00.000000

Create smlmv_parametros table to store the yearly SMLMV (Salario Mínimo Legal
Mensual Vigente) values used as floor in pension liquidation calculations.
Seeds the table with known values for years 2024, 2025, and 2026.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "e8f9a0b1c2d3"
down_revision: Union[str, None] = "dd865bb526a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create the smlmv_parametros table
    op.create_table(
        "smlmv_parametros",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("ano", sa.Integer(), nullable=False),
        sa.Column("valor", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column("vigente_desde", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_smlmv_parametros")),
        sa.UniqueConstraint("ano", name=op.f("uq_smlmv_parametros_ano")),
    )

    # Seed the table with known SMLMV values
    op.execute(
        "INSERT INTO smlmv_parametros (id, ano, valor, vigente_desde, created_at, updated_at, metadata) VALUES "
        "('550e8400-e29b-41d4-a716-446655440001', 2024, 1300000.00, '2024-01-01', NOW(), NOW(), NULL), "
        "('550e8400-e29b-41d4-a716-446655440002', 2025, 1423500.00, '2025-01-01', NOW(), NOW(), NULL), "
        "('550e8400-e29b-41d4-a716-446655440003', 2026, 1750905.00, '2026-01-01', NOW(), NOW(), NULL)"
    )


def downgrade() -> None:
    op.drop_table("smlmv_parametros")

"""add_smlmv_parametros_table

Revision ID: eaa9c065c2ae
Revises: dd865bb526a6
Create Date: 2026-07-29 17:45:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "eaa9c065c2ae"
down_revision: Union[str, None] = "dd865bb526a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "smlmv_parametros",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "ano",
            sa.Integer(),
            nullable=False,
            comment="Año calendario al que aplica este SMLMV",
        ),
        sa.Column(
            "valor",
            sa.Numeric(15, 2),
            nullable=False,
            comment="Valor del SMLMV en pesos colombianos, p.ej. 1750905.00",
        ),
        sa.Column(
            "vigente_desde",
            sa.Date(),
            nullable=False,
            comment="Fecha desde la cual es vigente este valor del SMLMV",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "metadata_",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.UniqueConstraint("ano", name="uq_smlmv_parametros_ano"),
    )

    op.create_index(
        "ix_smlmv_parametros_ano",
        "smlmv_parametros",
        ["ano"],
        unique=True,
    )

    # Seed: valores históricos de SMLMV para los años 2024-2026
    op.execute("""
        INSERT INTO smlmv_parametros
          (id, ano, valor, vigente_desde, created_at, updated_at)
        VALUES
          (gen_random_uuid(), 2024, 1300000.00, '2024-01-01', NOW(), NOW()),
          (gen_random_uuid(), 2025, 1423500.00, '2025-01-01', NOW(), NOW()),
          (gen_random_uuid(), 2026, 1750905.00, '2026-01-01', NOW(), NOW())
    """)


def downgrade() -> None:
    op.drop_index("ix_smlmv_parametros_ano", table_name="smlmv_parametros")
    op.drop_table("smlmv_parametros")

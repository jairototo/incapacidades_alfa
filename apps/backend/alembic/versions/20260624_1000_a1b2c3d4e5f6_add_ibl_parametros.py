"""add_ibl_parametros

Revision ID: a1b2c3d4e5f6
Revises: f3a8b2c1d4e5
Create Date: 2026-06-24 10:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "f3a8b2c1d4e5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ibl_parametros",
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
            comment="Año calendario al que aplican estos porcentajes de aporte",
        ),
        sa.Column(
            "aporte_patronal_pension",
            sa.Numeric(5, 2),
            nullable=False,
            comment="Porcentaje aporte patronal pensión, e.g. 12.00",
        ),
        sa.Column(
            "aporte_patronal_salud",
            sa.Numeric(5, 2),
            nullable=False,
            comment="Porcentaje aporte patronal salud, e.g. 8.50",
        ),
        sa.Column(
            "aporte_trabajador_pension",
            sa.Numeric(5, 2),
            nullable=False,
            comment="Porcentaje aporte trabajador pensión, e.g. 4.00",
        ),
        sa.Column(
            "aporte_trabajador_salud",
            sa.Numeric(5, 2),
            nullable=False,
            comment="Porcentaje aporte trabajador salud, e.g. 4.00",
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
        sa.UniqueConstraint("ano", name="uq_ibl_parametros_ano"),
    )

    op.create_index(
        "ix_ibl_parametros_ano",
        "ibl_parametros",
        ["ano"],
        unique=True,
    )

    # Seed: parámetros vigentes para el año 2026
    op.execute("""
        INSERT INTO ibl_parametros
          (id, ano, aporte_patronal_pension, aporte_patronal_salud,
           aporte_trabajador_pension, aporte_trabajador_salud)
        VALUES
          (gen_random_uuid(), 2026, 12.00, 8.50, 4.00, 4.00)
    """)


def downgrade() -> None:
    op.drop_index("ix_ibl_parametros_ano", table_name="ibl_parametros")
    op.drop_table("ibl_parametros")

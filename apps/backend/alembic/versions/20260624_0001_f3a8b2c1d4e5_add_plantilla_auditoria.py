"""add_plantilla_auditoria

Revision ID: f3a8b2c1d4e5
Revises: e9c646ca7c0c
Create Date: 2026-06-24 00:01:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "f3a8b2c1d4e5"
down_revision: Union[str, None] = "e9c646ca7c0c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "plantilla_auditoria",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "incapacidad_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("incapacidad.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "canal_recepcion",
            sa.String(100),
            nullable=False,
            comment="Canal por el que se recibió la incapacidad: Portal / Imaginex / Onbase",
        ),
        sa.Column("nombre_ips", sa.String(255), nullable=True),
        sa.Column("fecha_emision_incapacidad", sa.Date(), nullable=True),
        sa.Column("dias_autorizados", sa.Integer(), nullable=False),
        sa.Column("fecha_inicio_autorizada", sa.Date(), nullable=False),
        sa.Column("fecha_fin_autorizada", sa.Date(), nullable=False),
        sa.Column("diagnostico_cie10", sa.String(10), nullable=True),
        sa.Column("descripcion_cie10", sa.Text(), nullable=True),
        sa.Column("nombre_medico", sa.String(200), nullable=True),
        sa.Column("especialidad_medico", sa.String(100), nullable=True),
        sa.Column(
            "linea_autorizacion",
            sa.Text(),
            nullable=True,
            comment="Auto-generado: Se autoriza pago por X días desde ... hasta ...",
        ),
        sa.Column(
            "dias_documento",
            sa.Integer(),
            nullable=True,
            comment="Total días en el documento físico (para aprobación parcial)",
        ),
        sa.Column("rango_pagado_inicio", sa.Date(), nullable=True),
        sa.Column("rango_pagado_fin", sa.Date(), nullable=True),
        sa.Column(
            "auditado_por_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("usuario.id"),
            nullable=True,
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
        sa.Column("metadata", sa.JSON(), nullable=True),
    )

    # Index on incapacidad_id (already unique, but also for faster lookups)
    op.create_index(
        "ix_plantilla_auditoria_incapacidad_id",
        "plantilla_auditoria",
        ["incapacidad_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_plantilla_auditoria_incapacidad_id",
        table_name="plantilla_auditoria",
    )
    op.drop_table("plantilla_auditoria")

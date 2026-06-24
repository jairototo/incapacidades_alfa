"""add_liquidacion_table

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-06-24 11:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create the PostgreSQL enum type for metodo_pago
    op.execute(
        "CREATE TYPE metodopagoliquidacion AS ENUM ('CHEQUE', 'OXIRRE')"
    )

    op.create_table(
        "liquidacion",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        # FK → incapacidad (ONE-TO-ONE, CASCADE DELETE)
        sa.Column(
            "incapacidad_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("incapacidad.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
            comment="ID de la incapacidad a la que pertenece esta liquidación",
        ),
        # IBL (Ingreso Base de Liquidación)
        sa.Column(
            "ibl",
            sa.Numeric(15, 2),
            nullable=True,
            comment="Ingreso Base de Liquidación — promedio IBC 6 meses previos",
        ),
        sa.Column(
            "periodo_ibl_inicio",
            sa.Date,
            nullable=True,
            comment="Inicio del período de cálculo del IBL (6 meses previos)",
        ),
        sa.Column(
            "periodo_ibl_fin",
            sa.Date,
            nullable=True,
            comment="Fin del período de cálculo del IBL",
        ),
        # Período autorizado (desde plantilla_auditoria)
        sa.Column(
            "dias_autorizados",
            sa.Integer,
            nullable=False,
            comment="Número de días autorizados por el auditor",
        ),
        sa.Column(
            "fecha_inicio_autorizada",
            sa.Date,
            nullable=False,
            comment="Fecha de inicio del período autorizado",
        ),
        sa.Column(
            "fecha_fin_autorizada",
            sa.Date,
            nullable=False,
            comment="Fecha de fin del período autorizado",
        ),
        # Desglose de valores
        sa.Column(
            "valor_incapacidad_temporal",
            sa.Numeric(15, 2),
            nullable=True,
            comment="Valor de la incapacidad temporal calculada",
        ),
        sa.Column(
            "valor_aporte_patronal_pension",
            sa.Numeric(15, 2),
            nullable=True,
            comment="Valor del aporte patronal a pensión",
        ),
        sa.Column(
            "valor_aporte_trabajador_pension",
            sa.Numeric(15, 2),
            nullable=True,
            comment="Valor del aporte del trabajador a pensión",
        ),
        sa.Column(
            "valor_aporte_adicional_trabajador_pension",
            sa.Numeric(15, 2),
            nullable=True,
            comment="Valor del aporte adicional del trabajador a pensión (si aplica)",
        ),
        sa.Column(
            "valor_aporte_patronal_salud",
            sa.Numeric(15, 2),
            nullable=True,
            comment="Valor del aporte patronal a salud",
        ),
        sa.Column(
            "valor_aporte_trabajador_salud",
            sa.Numeric(15, 2),
            nullable=True,
            comment="Valor del aporte del trabajador a salud",
        ),
        sa.Column(
            "valor_total",
            sa.Numeric(15, 2),
            nullable=True,
            comment="Valor total a pagar (suma de todos los componentes)",
        ),
        # Pago
        sa.Column(
            "metodo_pago",
            postgresql.ENUM("CHEQUE", "OXIRRE", name="metodopagoliquidacion", create_type=False),
            nullable=True,
            comment="Método de pago (C2: pendiente lista de entidades por método del cliente)",
        ),
        sa.Column(
            "notas_liquidador",
            sa.Text,
            nullable=True,
            comment="Observaciones libres del liquidador",
        ),
        # FK → usuario (liquidador)
        sa.Column(
            "liquidador_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("usuario.id"),
            nullable=True,
            comment="ID del usuario que realizó la liquidación",
        ),
        # Timestamps
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
            "metadata",
            postgresql.JSONB(),
            nullable=True,
        ),
    )

    op.create_index(
        "ix_liquidacion_incapacidad_id",
        "liquidacion",
        ["incapacidad_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_liquidacion_incapacidad_id", table_name="liquidacion")
    op.drop_table("liquidacion")
    op.execute("DROP TYPE metodopagoliquidacion")

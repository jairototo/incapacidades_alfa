"""update_chk_incapacidad_estado_constraint

Revision ID: cf0a432a3aa8
Revises: 566c94df42fa
Create Date: 2026-02-02 21:36:49.427544

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cf0a432a3aa8'
down_revision: Union[str, None] = '566c94df42fa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Eliminar el constraint antiguo
    op.drop_constraint('chk_incapacidad_estado', 'incapacidad', type_='check')
    
    # Crear el nuevo constraint con los 11 estados (8 anteriores + 3 nuevos)
    op.create_check_constraint(
        'chk_incapacidad_estado',
        'incapacidad',
        sa.text(
            "estado::text = ANY (ARRAY["
            "'RADICADA'::character varying::text, "
            "'EN_AUDITORIA'::character varying::text, "
            "'OBSERVADA'::character varying::text, "
            "'APROBADA'::character varying::text, "
            "'APROBADA_PARCIALMENTE'::character varying::text, "  # NUEVO
            "'RECHAZADA'::character varying::text, "
            "'EN_PAGO'::character varying::text, "
            "'EN_PAGO_PARCIAL'::character varying::text, "  # NUEVO
            "'PAGADA'::character varying::text, "
            "'PAGADA_PARCIALMENTE'::character varying::text, "  # NUEVO
            "'CANCELADA'::character varying::text])"
        )
    )


def downgrade() -> None:
    # Revertir: eliminar el constraint nuevo y restaurar el antiguo (solo 8 estados)
    op.drop_constraint('chk_incapacidad_estado', 'incapacidad', type_='check')
    
    op.create_check_constraint(
        'chk_incapacidad_estado',
        'incapacidad',
        sa.text(
            "estado::text = ANY (ARRAY["
            "'RADICADA'::character varying::text, "
            "'EN_AUDITORIA'::character varying::text, "
            "'OBSERVADA'::character varying::text, "
            "'APROBADA'::character varying::text, "
            "'RECHAZADA'::character varying::text, "
            "'EN_PAGO'::character varying::text, "
            "'PAGADA'::character varying::text, "
            "'CANCELADA'::character varying::text])"
        )
    )

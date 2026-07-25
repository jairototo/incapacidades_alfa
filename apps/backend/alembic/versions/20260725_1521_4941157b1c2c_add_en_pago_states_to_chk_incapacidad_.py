"""add en_pago states to chk_incapacidad_estado constraint

Revision ID: 4941157b1c2c
Revises: 66b93c4029d8
Create Date: 2026-07-25 15:21:18.738717

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4941157b1c2c'
down_revision: Union[str, None] = '66b93c4029d8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # The Task 1.1 migration (add_en_pago_and_en_pago_parcial_to_estadoincapacidad
    # enum) added EN_PAGO/EN_PAGO_PARCIAL to the estadoincapacidad PG enum type,
    # but chk_incapacidad_estado is a separate CHECK constraint with its own
    # hardcoded value list — it was not updated then, so any write of
    # estado='EN_PAGO'/'EN_PAGO_PARCIAL' fails with CheckViolationError even
    # though the enum type itself accepts those values.
    op.execute("ALTER TABLE incapacidad DROP CONSTRAINT IF EXISTS chk_incapacidad_estado")
    op.execute(
        "ALTER TABLE incapacidad ADD CONSTRAINT chk_incapacidad_estado "
        "CHECK (estado::text = ANY (ARRAY["
        "'RADICADA','EN_AUDITORIA','PENDIENTE','CREACION_SINIESTRO',"
        "'LIQUIDACION','LIQUIDACION_PARCIAL','GLOSADA','EN_PAGO','EN_PAGO_PARCIAL',"
        "'PAGADA','PAGADA_PARCIAL'"
        "]))"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE incapacidad DROP CONSTRAINT IF EXISTS chk_incapacidad_estado")
    op.execute(
        "ALTER TABLE incapacidad ADD CONSTRAINT chk_incapacidad_estado "
        "CHECK (estado::text = ANY (ARRAY["
        "'RADICADA','EN_AUDITORIA','PENDIENTE','CREACION_SINIESTRO',"
        "'LIQUIDACION','LIQUIDACION_PARCIAL','GLOSADA','PAGADA','PAGADA_PARCIAL'"
        "]))"
    )

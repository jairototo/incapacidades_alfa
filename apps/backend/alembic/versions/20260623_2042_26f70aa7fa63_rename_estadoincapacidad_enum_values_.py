"""rename estadoincapacidad enum values for new workflow

Revision ID: 26f70aa7fa63
Revises: 07881f00b038
Create Date: 2026-06-23 20:42:40.487731

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '26f70aa7fa63'
down_revision: Union[str, None] = '07881f00b038'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

old_values = (
    'RADICADA', 'EN_AUDITORIA', 'OBSERVADA', 'APROBADA', 'APROBADA_PARCIALMENTE',
    'RECHAZADA', 'EN_PAGO', 'EN_PAGO_PARCIAL', 'PAGADA', 'PAGADA_PARCIALMENTE', 'CANCELADA'
)
new_values = (
    'RADICADA', 'EN_AUDITORIA', 'PENDIENTE', 'CREACION_SINIESTRO',
    'LIQUIDACION', 'LIQUIDACION_PARCIAL', 'GLOSADA', 'PAGADA', 'PAGADA_PARCIAL'
)

# Mapping of old values to new values (only those that change)
mapping = {
    'OBSERVADA': 'PENDIENTE',
    'APROBADA': 'LIQUIDACION',
    'APROBADA_PARCIALMENTE': 'LIQUIDACION_PARCIAL',
    'EN_PAGO': 'LIQUIDACION',
    'EN_PAGO_PARCIAL': 'LIQUIDACION_PARCIAL',
    'RECHAZADA': 'GLOSADA',
    'PAGADA_PARCIALMENTE': 'PAGADA_PARCIAL',
    'CANCELADA': 'GLOSADA',
}


def upgrade() -> None:
    # Step 1: Fix unrelated pre_incapacidad drift (idempotent — use raw SQL IF EXISTS)
    op.execute(
        "ALTER TABLE pre_incapacidad "
        "ALTER COLUMN estado SET DATA TYPE character varying(20)"
    )
    op.execute(
        "ALTER TABLE pre_incapacidad DROP CONSTRAINT IF EXISTS uq_pre_incapacidad_incapacidad_id"
    )
    op.execute(
        "DROP INDEX IF EXISTS ix_pre_incapacidad_incapacidad_id"
    )
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_pre_incapacidad_incapacidad_id "
        "ON pre_incapacidad (incapacidad_id)"
    )

    # Step 2: Add new enum values (PostgreSQL allows adding, not renaming)
    for v in ('PENDIENTE', 'CREACION_SINIESTRO', 'LIQUIDACION', 'LIQUIDACION_PARCIAL', 'GLOSADA', 'PAGADA_PARCIAL'):
        op.execute(f"ALTER TYPE estadoincapacidad ADD VALUE IF NOT EXISTS '{v}'")
    op.execute("COMMIT")

    # Step 3: Drop the check constraint that references old enum values
    op.execute("ALTER TABLE incapacidad DROP CONSTRAINT IF EXISTS chk_incapacidad_estado")

    # Step 4: Migrate data in incapacidad table
    for old, new in mapping.items():
        op.execute(f"UPDATE incapacidad SET estado = '{new}' WHERE estado = '{old}'")

    # Step 5: Migrate historial_estado string values (stored as VARCHAR, not enum)
    for old, new in mapping.items():
        op.execute(f"UPDATE historial_estado SET estado_anterior = '{new}' WHERE estado_anterior = '{old}'")
        op.execute(f"UPDATE historial_estado SET estado_nuevo = '{new}' WHERE estado_nuevo = '{old}'")

    # Step 6: Recreate enum with only new values (cycle via TEXT)
    op.execute("ALTER TABLE incapacidad ALTER COLUMN estado TYPE TEXT")
    op.execute("DROP TYPE estadoincapacidad")
    op.execute(
        "CREATE TYPE estadoincapacidad AS ENUM "
        "('RADICADA','EN_AUDITORIA','PENDIENTE','CREACION_SINIESTRO',"
        "'LIQUIDACION','LIQUIDACION_PARCIAL','GLOSADA','PAGADA','PAGADA_PARCIAL')"
    )
    op.execute(
        "ALTER TABLE incapacidad ALTER COLUMN estado TYPE estadoincapacidad "
        "USING estado::estadoincapacidad"
    )

    # Step 7: Recreate check constraint with new enum values
    op.execute(
        "ALTER TABLE incapacidad ADD CONSTRAINT chk_incapacidad_estado "
        "CHECK (estado::text = ANY (ARRAY["
        "'RADICADA','EN_AUDITORIA','PENDIENTE','CREACION_SINIESTRO',"
        "'LIQUIDACION','LIQUIDACION_PARCIAL','GLOSADA','PAGADA','PAGADA_PARCIAL'"
        "]))"
    )


def downgrade() -> None:
    # Reverse pre_incapacidad drift changes
    op.drop_index(op.f('ix_pre_incapacidad_incapacidad_id'), table_name='pre_incapacidad')
    op.create_index('ix_pre_incapacidad_incapacidad_id', 'pre_incapacidad', ['incapacidad_id'], unique=False)
    op.create_unique_constraint('uq_pre_incapacidad_incapacidad_id', 'pre_incapacidad', ['incapacidad_id'])
    op.alter_column('pre_incapacidad', 'estado',
               existing_type=sa.VARCHAR(length=20),
               comment='PENDIENTE | PROCESADA | RECHAZADA | ERROR',
               existing_comment='PENDIENTE | PROCESADA | RECHAZADA | ERROR | DEVUELTA',
               existing_nullable=False)

    # Drop new check constraint
    op.execute("ALTER TABLE incapacidad DROP CONSTRAINT IF EXISTS chk_incapacidad_estado")

    # Recreate old enum (cycle via TEXT)
    op.execute("ALTER TABLE incapacidad ALTER COLUMN estado TYPE TEXT")
    op.execute("DROP TYPE estadoincapacidad")
    op.execute(
        "CREATE TYPE estadoincapacidad AS ENUM "
        "('RADICADA','EN_AUDITORIA','OBSERVADA','APROBADA','APROBADA_PARCIALMENTE',"
        "'RECHAZADA','EN_PAGO','EN_PAGO_PARCIAL','PAGADA','PAGADA_PARCIALMENTE','CANCELADA')"
    )
    op.execute(
        "ALTER TABLE incapacidad ALTER COLUMN estado TYPE estadoincapacidad "
        "USING estado::estadoincapacidad"
    )

    # Recreate old check constraint
    op.execute(
        "ALTER TABLE incapacidad ADD CONSTRAINT chk_incapacidad_estado "
        "CHECK (estado::text = ANY (ARRAY["
        "'RADICADA','EN_AUDITORIA','OBSERVADA','APROBADA','APROBADA_PARCIALMENTE',"
        "'RECHAZADA','EN_PAGO','EN_PAGO_PARCIAL','PAGADA','PAGADA_PARCIALMENTE','CANCELADA'"
        "]))"
    )

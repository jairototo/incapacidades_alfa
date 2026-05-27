"""update_estadoincapacidad_enum_add_partial_states

Revision ID: 566c94df42fa
Revises: 5f0125256440
Create Date: 2026-02-02 19:23:22.152564

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '566c94df42fa'
down_revision: Union[str, None] = '5f0125256440'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Agregar nuevos valores al enum estadoincapacidad en PostgreSQL
    # Nota: ALTER TYPE ADD VALUE no se puede ejecutar en un bloque de transacción
    # por lo que usamos execute() individual para cada valor
    
    # Agregar APROBADA_PARCIALMENTE después de APROBADA
    op.execute("ALTER TYPE estadoincapacidad ADD VALUE IF NOT EXISTS 'APROBADA_PARCIALMENTE' AFTER 'APROBADA'")
    
    # Agregar EN_PAGO_PARCIAL después de EN_PAGO
    op.execute("ALTER TYPE estadoincapacidad ADD VALUE IF NOT EXISTS 'EN_PAGO_PARCIAL' AFTER 'EN_PAGO'")
    
    # Agregar PAGADA_PARCIALMENTE después de PAGADA
    op.execute("ALTER TYPE estadoincapacidad ADD VALUE IF NOT EXISTS 'PAGADA_PARCIALMENTE' AFTER 'PAGADA'")


def downgrade() -> None:
    # No se pueden eliminar valores de un enum en PostgreSQL sin recrear el tipo completo
    # En producción, esto requeriría:
    # 1. Crear un nuevo enum sin los valores
    # 2. Cambiar todas las columnas al nuevo tipo
    # 3. Eliminar el enum viejo
    # 4. Renombrar el nuevo enum
    
    # Por simplicidad, dejamos un comentario indicando que es difícil revertir
    pass  # Los valores del enum permanecen, no afecta funcionamiento


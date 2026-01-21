"""add_trigger_registro_radicacion

Revision ID: 34cf625b8606
Revises: 541a0b02d056
Create Date: 2026-01-21 02:02:27.592652

Crea trigger para registrar automáticamente el estado inicial de una incapacidad
en el historial_estado cuando se inserta un nuevo registro.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '34cf625b8606'
down_revision: Union[str, None] = '541a0b02d056'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Crear función y trigger para registro automático de radicación."""
    
    # Crear función PL/pgSQL
    op.execute("""
        CREATE OR REPLACE FUNCTION registrar_radicacion_incapacidad()
        RETURNS TRIGGER AS $$
        BEGIN
            -- Insertar registro inicial en historial_estado
            INSERT INTO historial_estado (
                id,
                entity_type,
                entity_id,
                estado_anterior,
                estado_nuevo,
                cambiado_por_id,
                observacion,
                fecha_cambio,
                created_at,
                updated_at
            ) VALUES (
                gen_random_uuid(),
                'incapacidad',
                NEW.id,
                NULL,
                NEW.estado,
                NEW.radicado_por_id,
                'Estado inicial al radicar la incapacidad',
                NOW(),
                NOW(),
                NOW()
            );
            
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # Crear trigger
    op.execute("""
        CREATE TRIGGER trigger_registrar_radicacion_incapacidad
            AFTER INSERT ON incapacidad
            FOR EACH ROW
            EXECUTE FUNCTION registrar_radicacion_incapacidad();
    """)


def downgrade() -> None:
    """Eliminar trigger y función."""
    
    # Eliminar trigger
    op.execute("DROP TRIGGER IF EXISTS trigger_registrar_radicacion_incapacidad ON incapacidad;")
    
    # Eliminar función
    op.execute("DROP FUNCTION IF EXISTS registrar_radicacion_incapacidad();")

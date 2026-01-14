"""convert_historial_estado_to_polymorphic

Revision ID: 2329c303f650
Revises: c7b1fe8abcae
Create Date: 2026-01-09 13:10:04.418717

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2329c303f650'
down_revision: Union[str, None] = 'c7b1fe8abcae'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Crear tabla historial_estado con estructura polimórfica."""
    
    # Eliminar tabla si existe (simplifica la migración)
    op.execute("DROP TABLE IF EXISTS historial_estado CASCADE")
    
    # Crear tabla con estructura polimórfica
    op.create_table(
        'historial_estado',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('entity_type', sa.String(50), nullable=False, comment='Tipo de entidad: incapacidad, siniestro, etc.'),
        sa.Column('entity_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False, comment='ID de la entidad relacionada'),
        sa.Column('estado_anterior', sa.String(50), nullable=True, comment='Estado previo al cambio'),
        sa.Column('estado_nuevo', sa.String(50), nullable=False, comment='Nuevo estado después del cambio'),
        sa.Column('observacion', sa.Text(), nullable=True),
        sa.Column('fecha_cambio', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('cambiado_por_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('metadata', sa.dialects.postgresql.JSONB(), nullable=True),
        sa.ForeignKeyConstraint(['cambiado_por_id'], ['usuario.id'], name='historial_estado_cambiado_por_id_fkey')
    )
    
    # Crear índices
    op.create_index('ix_historial_entity', 'historial_estado', ['entity_type', 'entity_id'])
    op.create_index('ix_historial_estado_entity_type', 'historial_estado', ['entity_type'])
    op.create_index('ix_historial_estado_entity_id', 'historial_estado', ['entity_id'])
    op.create_index('ix_historial_estado_fecha_cambio', 'historial_estado', ['fecha_cambio'])


def downgrade() -> None:
    """No se permite revertir - requiere recrear tabla desde cero."""
    raise Exception(
        "Downgrade no soportado. Esta migración elimina y recrea la tabla historial_estado. "
        "Para revertir, ejecute las migraciones anteriores desde cero."
    )

    op.create_index('ix_historial_estado_incapacidad_id', 'historial_estado', ['incapacidad_id'])
    
    # 5. Eliminar índices polimórficos
    op.drop_index('ix_historial_estado_fecha_cambio', 'historial_estado')
    op.drop_index('ix_historial_estado_entity_id', 'historial_estado')
    op.drop_index('ix_historial_estado_entity_type', 'historial_estado')
    op.drop_index('ix_historial_entity', 'historial_estado')
    
    # 6. Eliminar columnas polimórficas
    op.drop_column('historial_estado', 'entity_id')
    op.drop_column('historial_estado', 'entity_type')
    
    # 7. Revertir tipos de columnas
    op.alter_column('historial_estado', 'estado_anterior',
                    type_=sa.String(30),
                    existing_type=sa.String(50))
    op.alter_column('historial_estado', 'estado_nuevo',
                    type_=sa.String(30),
                    existing_type=sa.String(50))

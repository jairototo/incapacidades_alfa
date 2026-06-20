"""add numero_radicacion_servialfa and communication_log

Revision ID: c671c2abc417
Revises: 743db1cdeec3
Create Date: 2026-06-20 03:07:28.540113

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c671c2abc417'
down_revision: Union[str, None] = '743db1cdeec3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('communication_log',
    sa.Column('incapacidad_id', sa.UUID(), nullable=False),
    sa.Column('sistema', sa.String(length=20), nullable=False, comment='SERVIALFA | SICAT'),
    sa.Column('estado', sa.String(length=20), nullable=False, comment='SUCCESS | FAILURE | PENDING'),
    sa.Column('payload_resumen', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('respuesta', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('mensaje', sa.Text(), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.ForeignKeyConstraint(['incapacidad_id'], ['incapacidad.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_communication_log_incapacidad_id'), 'communication_log', ['incapacidad_id'], unique=False)
    op.add_column('incapacidad', sa.Column('numero_radicacion_servialfa', sa.String(length=100), nullable=True, comment='Número de radicación definitivo retornado por ServiAlfa (llega vía integración)'))


def downgrade() -> None:
    op.drop_column('incapacidad', 'numero_radicacion_servialfa')
    op.drop_index(op.f('ix_communication_log_incapacidad_id'), table_name='communication_log')
    op.drop_table('communication_log')

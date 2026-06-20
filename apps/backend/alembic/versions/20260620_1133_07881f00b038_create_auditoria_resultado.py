"""create auditoria_resultado

Revision ID: 07881f00b038
Revises: c671c2abc417
Create Date: 2026-06-20 11:33:26.056878

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '07881f00b038'
down_revision: Union[str, None] = 'c671c2abc417'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('auditoria_resultado',
    sa.Column('incapacidad_id', sa.UUID(), nullable=False),
    sa.Column('regla', sa.String(length=100), nullable=False, comment='Código de la regla evaluada'),
    sa.Column('categoria', sa.String(length=50), nullable=False),
    sa.Column('aprobado', sa.Boolean(), nullable=False),
    sa.Column('severidad', sa.String(length=20), nullable=False),
    sa.Column('detalle', sa.Text(), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.ForeignKeyConstraint(['incapacidad_id'], ['incapacidad.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_auditoria_resultado_incapacidad_id'), 'auditoria_resultado', ['incapacidad_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_auditoria_resultado_incapacidad_id'), table_name='auditoria_resultado')
    op.drop_table('auditoria_resultado')

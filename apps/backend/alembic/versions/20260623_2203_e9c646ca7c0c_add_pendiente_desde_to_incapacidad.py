"""add_pendiente_desde_to_incapacidad

Revision ID: e9c646ca7c0c
Revises: 26f70aa7fa63
Create Date: 2026-06-23 22:03:25.716456

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e9c646ca7c0c'
down_revision: Union[str, None] = '26f70aa7fa63'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('incapacidad', sa.Column('pendiente_desde', sa.DateTime(timezone=True), nullable=True,
                  comment='Timestamp de cuando la incapacidad entró en estado PENDIENTE (para cálculo de alerta de 8 días)'))


def downgrade() -> None:
    op.drop_column('incapacidad', 'pendiente_desde')

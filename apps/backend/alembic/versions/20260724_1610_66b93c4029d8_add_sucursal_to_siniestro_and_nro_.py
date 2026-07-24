"""add sucursal to siniestro and nro_contrato to empresa

Revision ID: 66b93c4029d8
Revises: a3d7573eccaa
Create Date: 2026-07-24 16:10:10.992222

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '66b93c4029d8'
down_revision: Union[str, None] = 'a3d7573eccaa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'siniestro',
        sa.Column('sucursal', sa.String(length=50), nullable=True,
                  comment="Sucursal giradora (Cali/Medellín/Cartagena/Bogotá)"),
    )
    op.add_column(
        'empresa',
        sa.Column('nro_contrato', sa.String(length=100), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('empresa', 'nro_contrato')
    op.drop_column('siniestro', 'sucursal')

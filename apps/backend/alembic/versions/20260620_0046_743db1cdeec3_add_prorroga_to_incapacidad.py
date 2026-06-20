"""add prorroga to incapacidad

Revision ID: 743db1cdeec3
Revises: e6ca0672c310
Create Date: 2026-06-20 00:46:15.363306

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '743db1cdeec3'
down_revision: Union[str, None] = 'e6ca0672c310'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('incapacidad', sa.Column('prorroga', sa.Boolean(), server_default='false', nullable=False, comment='Indica si la incapacidad es una prórroga/renovación'))


def downgrade() -> None:
    op.drop_column('incapacidad', 'prorroga')

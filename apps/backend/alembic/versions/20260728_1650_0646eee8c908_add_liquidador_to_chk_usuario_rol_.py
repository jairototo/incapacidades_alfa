"""add LIQUIDADOR to chk_usuario_rol constraint

Revision ID: 0646eee8c908
Revises: bc5e57b5c255
Create Date: 2026-07-28 16:50:24.769982

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0646eee8c908'
down_revision: Union[str, None] = 'bc5e57b5c255'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint("chk_usuario_rol", "usuario", type_="check")
    op.create_check_constraint(
        "chk_usuario_rol",
        "usuario",
        "rol IN ('ADMIN', 'AUDITOR', 'APROBADOR', 'EMPRESA', 'EMPLEADO', 'READONLY', 'LIQUIDADOR')",
    )


def downgrade() -> None:
    op.drop_constraint("chk_usuario_rol", "usuario", type_="check")
    op.create_check_constraint(
        "chk_usuario_rol",
        "usuario",
        "rol IN ('ADMIN', 'AUDITOR', 'APROBADOR', 'EMPRESA', 'EMPLEADO', 'READONLY')",
    )

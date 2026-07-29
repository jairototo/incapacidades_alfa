"""add previsionales roles to chk_usuario_rol

Revision ID: dd865bb526a6
Revises: 0646eee8c908
Create Date: 2026-07-29 15:42:15.827601

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dd865bb526a6'
down_revision: Union[str, None] = '0646eee8c908'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint("chk_usuario_rol", "usuario", type_="check")
    op.create_check_constraint(
        "chk_usuario_rol",
        "usuario",
        "rol IN ('ADMIN', 'AUDITOR', 'APROBADOR', 'EMPRESA', 'EMPLEADO', 'READONLY', 'LIQUIDADOR', 'AUDITOR_PREVISIONALES', 'AUDITOR_JURIDICO')",
    )


def downgrade() -> None:
    op.drop_constraint("chk_usuario_rol", "usuario", type_="check")
    op.create_check_constraint(
        "chk_usuario_rol",
        "usuario",
        "rol IN ('ADMIN', 'AUDITOR', 'APROBADOR', 'EMPRESA', 'EMPLEADO', 'READONLY', 'LIQUIDADOR')",
    )

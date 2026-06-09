"""unified_flow_relax_arl_constraint_add_incapacidad_fk

Revision ID: e6ca0672c310
Revises: 58016e3f2c11
Create Date: 2026-06-09 21:23:58.339445

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'e6ca0672c310'
down_revision: Union[str, None] = '58016e3f2c11'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Drop old strict ARL constraint (DB uses chk_incapacidad_tipo_relacion)
    op.drop_constraint("chk_incapacidad_tipo_relacion", "incapacidad", type_="check")

    # 2. Add relaxed constraint (ARL no longer requires empleado_id / empresa_id NOT NULL)
    op.create_check_constraint(
        "chk_incapacidad_tipo_relacion",
        "incapacidad",
        "(tipo = 'ARL' AND afiliado_id IS NULL) OR "
        "(tipo = 'SALUD' AND afiliado_id IS NOT NULL AND empleado_id IS NULL AND empresa_id IS NULL)",
    )

    # 3. Add incapacidad_id FK column to pre_incapacidad
    op.add_column(
        "pre_incapacidad",
        sa.Column("incapacidad_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_pre_incapacidad_incapacidad_id",
        "pre_incapacidad",
        "incapacidad",
        ["incapacidad_id"],
        ["id"],
    )
    op.create_unique_constraint(
        "uq_pre_incapacidad_incapacidad_id",
        "pre_incapacidad",
        ["incapacidad_id"],
    )
    op.create_index(
        "ix_pre_incapacidad_incapacidad_id",
        "pre_incapacidad",
        ["incapacidad_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_pre_incapacidad_incapacidad_id", table_name="pre_incapacidad")
    op.drop_constraint("uq_pre_incapacidad_incapacidad_id", "pre_incapacidad", type_="unique")
    op.drop_constraint("fk_pre_incapacidad_incapacidad_id", "pre_incapacidad", type_="foreignkey")
    op.drop_column("pre_incapacidad", "incapacidad_id")

    op.drop_constraint("chk_incapacidad_tipo_relacion", "incapacidad", type_="check")
    op.create_check_constraint(
        "chk_incapacidad_tipo_relacion",
        "incapacidad",
        "(tipo = 'ARL' AND empleado_id IS NOT NULL AND empresa_id IS NOT NULL AND afiliado_id IS NULL) OR "
        "(tipo = 'SALUD' AND afiliado_id IS NOT NULL AND empleado_id IS NULL AND empresa_id IS NULL)",
    )

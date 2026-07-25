"""add auditor sucursal assignment columns

Revision ID: 4d58280019e6
Revises: 4941157b1c2c
Create Date: 2026-07-25 17:33:36.192737

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4d58280019e6'
down_revision: Union[str, None] = '4941157b1c2c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("usuario", sa.Column("sucursal", sa.String(length=50), nullable=True, comment="Código de sucursal/regional asignada al auditor"))
    op.add_column(
        "usuario",
        sa.Column("incapacidades_asignadas_activas", sa.Integer(), nullable=False, server_default="0", comment="Contador de incapacidades asignadas al auditor en estados EN_AUDITORIA/PENDIENTE"),
    )
    op.add_column(
        "incapacidad",
        sa.Column("auditor_asignado_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True, comment="Auditor asignado automáticamente al entrar a EN_AUDITORIA, según sucursal del siniestro y balanceo de carga"),
    )
    op.create_foreign_key(
        "incapacidad_auditor_asignado_id_fkey",
        "incapacidad", "usuario",
        ["auditor_asignado_id"], ["id"],
        ondelete="SET NULL"
    )


def downgrade() -> None:
    op.drop_constraint("incapacidad_auditor_asignado_id_fkey", "incapacidad", type_="foreignkey")
    op.drop_column("incapacidad", "auditor_asignado_id")
    op.drop_column("usuario", "incapacidades_asignadas_activas")
    op.drop_column("usuario", "sucursal")

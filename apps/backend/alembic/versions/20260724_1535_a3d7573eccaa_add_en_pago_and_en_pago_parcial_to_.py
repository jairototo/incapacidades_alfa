"""add en_pago and en_pago_parcial to estadoincapacidad enum

Revision ID: a3d7573eccaa
Revises: c3d4e5f6a7b8
Create Date: 2026-07-24 15:35:53.194433

"""
from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'a3d7573eccaa'
down_revision: str = 'c3d4e5f6a7b8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE estadoincapacidad ADD VALUE IF NOT EXISTS 'EN_PAGO'")
    op.execute("ALTER TYPE estadoincapacidad ADD VALUE IF NOT EXISTS 'EN_PAGO_PARCIAL'")
    op.execute("COMMIT")


def downgrade() -> None:
    # PostgreSQL cannot drop enum values. No-op — matches the precedent set by
    # the original estadoincapacidad rename migration (2026-06-23 plan, Task 1.1).
    pass

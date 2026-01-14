"""add_missing_enums_siniestro

Revision ID: c7b1fe8abcae
Revises: 8034ee9c36ba
Create Date: 2026-01-08 15:16:24.180597

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c7b1fe8abcae'
down_revision: Union[str, None] = '8034ee9c36ba'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Crear ENUMs faltantes para Siniestro."""
    
    # GravedadSiniestro
    op.execute("""
        CREATE TYPE gravedadsiniestro AS ENUM (
            'LEVE',
            'MODERADA',
            'GRAVE',
            'MORTAL'
        )
    """)
    
    # SyncSource
    op.execute("""
        CREATE TYPE syncsource AS ENUM (
            'MANUAL',
            'API_EXTERNA',
            'IMPORTACION'
        )
    """)
    
    # Convertir columnas de siniestro a ENUMs
    # tipo_siniestro
    op.execute("ALTER TABLE siniestro ALTER COLUMN tipo_siniestro TYPE tiposiniestro USING tipo_siniestro::tiposiniestro")
    
    # estado (con default)
    op.execute("ALTER TABLE siniestro ALTER COLUMN estado DROP DEFAULT")
    op.execute("ALTER TABLE siniestro ALTER COLUMN estado TYPE estadosiniestro USING estado::estadosiniestro")
    op.execute("ALTER TABLE siniestro ALTER COLUMN estado SET DEFAULT 'REPORTADO'::estadosiniestro")
    
    # gravedad (con default)
    op.execute("ALTER TABLE siniestro ALTER COLUMN gravedad DROP DEFAULT")
    op.execute("ALTER TABLE siniestro ALTER COLUMN gravedad TYPE gravedadsiniestro USING gravedad::gravedadsiniestro")
    op.execute("ALTER TABLE siniestro ALTER COLUMN gravedad SET DEFAULT 'LEVE'::gravedadsiniestro")
    
    # sync_source (puede ser NULL)
    op.execute("ALTER TABLE siniestro ALTER COLUMN sync_source TYPE syncsource USING sync_source::syncsource")


def downgrade() -> None:
    """Revertir ENUMs a VARCHAR."""
    
    # Revertir columnas siniestro
    op.execute("ALTER TABLE siniestro ALTER COLUMN tipo_siniestro TYPE VARCHAR(50)")
    op.execute("ALTER TABLE siniestro ALTER COLUMN estado DROP DEFAULT")
    op.execute("ALTER TABLE siniestro ALTER COLUMN estado TYPE VARCHAR(20)")
    op.execute("ALTER TABLE siniestro ALTER COLUMN estado SET DEFAULT 'REPORTADO'")
    op.execute("ALTER TABLE siniestro ALTER COLUMN gravedad DROP DEFAULT")
    op.execute("ALTER TABLE siniestro ALTER COLUMN gravedad TYPE VARCHAR(20)")
    op.execute("ALTER TABLE siniestro ALTER COLUMN gravedad SET DEFAULT 'LEVE'")
    op.execute("ALTER TABLE siniestro ALTER COLUMN sync_source TYPE VARCHAR(20)")
    
    # Eliminar tipos ENUM
    op.execute("DROP TYPE IF EXISTS syncsource")
    op.execute("DROP TYPE IF EXISTS gravedadsiniestro")

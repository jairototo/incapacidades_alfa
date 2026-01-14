"""convert_columns_to_postgres_enums

Revision ID: 8034ee9c36ba
Revises: 9768ed75d50f
Create Date: 2026-01-08 14:51:42.164506

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8034ee9c36ba'
down_revision: Union[str, None] = '9768ed75d50f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Convertir columnas VARCHAR a tipos ENUM de PostgreSQL."""
    
    # INCAPACIDAD
    # Convertir tipo (sin default)
    op.execute("ALTER TABLE incapacidad ALTER COLUMN tipo TYPE tipoincapacidad USING tipo::tipoincapacidad")
    
    # Convertir estado (tiene default, hay que manejarlo)
    op.execute("ALTER TABLE incapacidad ALTER COLUMN estado DROP DEFAULT")
    op.execute("ALTER TABLE incapacidad ALTER COLUMN estado TYPE estadoincapacidad USING estado::estadoincapacidad")
    op.execute("ALTER TABLE incapacidad ALTER COLUMN estado SET DEFAULT 'RADICADA'::estadoincapacidad")
    
    # Convertir prioridad (tiene default)
    op.execute("ALTER TABLE incapacidad ALTER COLUMN prioridad DROP DEFAULT")
    op.execute("ALTER TABLE incapacidad ALTER COLUMN prioridad TYPE prioridad USING prioridad::prioridad")
    op.execute("ALTER TABLE incapacidad ALTER COLUMN prioridad SET DEFAULT 'NORMAL'::prioridad")
    
    # EMPLEADO
    # Convertir estado (tiene default)
    op.execute("ALTER TABLE empleado ALTER COLUMN estado DROP DEFAULT")
    op.execute("ALTER TABLE empleado ALTER COLUMN estado TYPE estadoempleado USING estado::estadoempleado")
    op.execute("ALTER TABLE empleado ALTER COLUMN estado SET DEFAULT 'ACTIVO'::estadoempleado")
    
    # Convertir tipo_documento (sin default)
    op.execute("ALTER TABLE empleado ALTER COLUMN tipo_documento TYPE tipodocumento USING tipo_documento::tipodocumento")
    
    # Convertir genero (si existe, sin default)
    try:
        op.execute("ALTER TABLE empleado ALTER COLUMN genero TYPE genero USING genero::genero")
    except:
        pass  # Si no existe la columna, continuar
    
    # EMPRESA
    # Convertir estado (tiene default)
    op.execute("ALTER TABLE empresa ALTER COLUMN estado DROP DEFAULT")
    op.execute("ALTER TABLE empresa ALTER COLUMN estado TYPE estadoempresa USING estado::estadoempresa")
    op.execute("ALTER TABLE empresa ALTER COLUMN estado SET DEFAULT 'ACTIVA'::estadoempresa")
    
    # AFILIADO
    # Convertir estado (tiene default)
    op.execute("ALTER TABLE afiliado ALTER COLUMN estado DROP DEFAULT")
    op.execute("ALTER TABLE afiliado ALTER COLUMN estado TYPE estadoafiliado USING estado::estadoafiliado")
    op.execute("ALTER TABLE afiliado ALTER COLUMN estado SET DEFAULT 'ACTIVO'::estadoafiliado")


def downgrade() -> None:
    """Revertir ENUMs a VARCHAR."""
    
    # INCAPACIDAD
    op.execute("ALTER TABLE incapacidad ALTER COLUMN tipo TYPE VARCHAR(20)")
    op.execute("ALTER TABLE incapacidad ALTER COLUMN estado DROP DEFAULT")
    op.execute("ALTER TABLE incapacidad ALTER COLUMN estado TYPE VARCHAR(20)")
    op.execute("ALTER TABLE incapacidad ALTER COLUMN estado SET DEFAULT 'RADICADA'")
    op.execute("ALTER TABLE incapacidad ALTER COLUMN prioridad DROP DEFAULT")
    op.execute("ALTER TABLE incapacidad ALTER COLUMN prioridad TYPE VARCHAR(20)")
    op.execute("ALTER TABLE incapacidad ALTER COLUMN prioridad SET DEFAULT 'NORMAL'")
    
    # EMPLEADO
    op.execute("ALTER TABLE empleado ALTER COLUMN estado DROP DEFAULT")
    op.execute("ALTER TABLE empleado ALTER COLUMN estado TYPE VARCHAR(20)")
    op.execute("ALTER TABLE empleado ALTER COLUMN estado SET DEFAULT 'ACTIVO'")
    op.execute("ALTER TABLE empleado ALTER COLUMN tipo_documento TYPE VARCHAR(20)")
    try:
        op.execute("ALTER TABLE empleado ALTER COLUMN genero TYPE VARCHAR(1)")
    except:
        pass
    
    # EMPRESA
    op.execute("ALTER TABLE empresa ALTER COLUMN estado DROP DEFAULT")
    op.execute("ALTER TABLE empresa ALTER COLUMN estado TYPE VARCHAR(20)")
    op.execute("ALTER TABLE empresa ALTER COLUMN estado SET DEFAULT 'ACTIVA'")
    
    # AFILIADO
    op.execute("ALTER TABLE afiliado ALTER COLUMN estado DROP DEFAULT")
    op.execute("ALTER TABLE afiliado ALTER COLUMN estado TYPE VARCHAR(20)")
    op.execute("ALTER TABLE afiliado ALTER COLUMN estado SET DEFAULT 'ACTIVO'")

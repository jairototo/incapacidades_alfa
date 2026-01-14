"""add_postgresql_enums

Revision ID: 9768ed75d50f
Revises: 001_initial_schema
Create Date: 2026-01-08 13:35:22.858708

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9768ed75d50f'
down_revision: Union[str, None] = '001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Crear tipos ENUM en PostgreSQL
    
    # EstadoIncapacidad
    op.execute("""
        CREATE TYPE estadoincapacidad AS ENUM (
            'RADICADA',
            'EN_AUDITORIA',
            'OBSERVADA',
            'APROBADA',
            'RECHAZADA',
            'EN_PAGO',
            'PAGADA',
            'CANCELADA'
        )
    """)
    
    # TipoIncapacidad
    op.execute("""
        CREATE TYPE tipoincapacidad AS ENUM (
            'ARL',
            'SALUD'
        )
    """)
    
    # Prioridad
    op.execute("""
        CREATE TYPE prioridad AS ENUM (
            'BAJA',
            'NORMAL',
            'ALTA',
            'URGENTE'
        )
    """)
    
    # TipoDocumento
    op.execute("""
        CREATE TYPE tipodocumento AS ENUM (
            'CC',
            'CE',
            'TI',
            'PASAPORTE',
            'PEP'
        )
    """)
    
    # Genero
    op.execute("""
        CREATE TYPE genero AS ENUM (
            'M',
            'F',
            'O'
        )
    """)
    
    # EstadoEmpresa
    op.execute("""
        CREATE TYPE estadoempresa AS ENUM (
            'ACTIVA',
            'INACTIVA',
            'SUSPENDIDA'
        )
    """)
    
    # EstadoEmpleado
    op.execute("""
        CREATE TYPE estadoempleado AS ENUM (
            'ACTIVO',
            'INACTIVO',
            'RETIRADO'
        )
    """)
    
    # EstadoAfiliado
    op.execute("""
        CREATE TYPE estadoafiliado AS ENUM (
            'ACTIVO',
            'INACTIVO',
            'SUSPENDIDO'
        )
    """)
    
    # TipoSiniestro
    op.execute("""
        CREATE TYPE tiposiniestro AS ENUM (
            'ACCIDENTE_TRABAJO',
            'ENFERMEDAD_LABORAL',
            'ACCIDENTE_TRAYECTO'
        )
    """)
    
    # EstadoSiniestro
    op.execute("""
        CREATE TYPE estadosiniestro AS ENUM (
            'REPORTADO',
            'EN_INVESTIGACION',
            'CERRADO',
            'ANULADO'
        )
    """)


def downgrade() -> None:
    # Eliminar tipos ENUM en orden inverso
    op.execute("DROP TYPE IF EXISTS estadosiniestro")
    op.execute("DROP TYPE IF EXISTS tiposiniestro")
    op.execute("DROP TYPE IF EXISTS estadoafiliado")
    op.execute("DROP TYPE IF EXISTS estadoempleado")
    op.execute("DROP TYPE IF EXISTS estadoempresa")
    op.execute("DROP TYPE IF EXISTS genero")
    op.execute("DROP TYPE IF EXISTS tipodocumento")
    op.execute("DROP TYPE IF EXISTS prioridad")
    op.execute("DROP TYPE IF EXISTS tipoincapacidad")
    op.execute("DROP TYPE IF EXISTS estadoincapacidad")

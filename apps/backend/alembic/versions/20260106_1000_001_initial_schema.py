"""Add afiliado table and update incapacidad for ARL/SALUD support

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-01-06 10:00:00.000000

This migration creates the complete database schema for the incapacidades system
including support for both ARL (employee-based) and SALUD (affiliate-based) incapacidades.

Changes:
- Create empresa table
- Create empleado table  
- Create afiliado table (NEW for SALUD support)
- Create usuario table
- Create siniestro table
- Create incapacidad table (with polymorphic support for ARL/SALUD)
- Create documento table
- Create historial_estado table
- Create orden_pago table
- Create auditoria_log table
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all tables."""
    
    # Enable UUID extension
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    
    # 1. Create empresa table
    op.create_table(
        'empresa',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('nit', sa.String(20), nullable=False),
        sa.Column('razon_social', sa.String(255), nullable=False),
        sa.Column('estado', sa.String(20), nullable=False, server_default='ACTIVA'),
        sa.Column('email_contacto', sa.String(255), nullable=True),
        sa.Column('telefono', sa.String(20), nullable=True),
        sa.Column('direccion', sa.Text(), nullable=True),
        sa.Column('ciudad', sa.String(100), nullable=True),
        sa.Column('departamento', sa.String(100), nullable=True),
        sa.Column('tipo_empresa', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('sync_source', sa.String(50), nullable=True),
        sa.Column('external_id', sa.String(100), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('nit'),
        sa.CheckConstraint("estado IN ('ACTIVA', 'INACTIVA', 'SUSPENDIDA')", name='chk_empresa_estado')
    )
    op.create_index('idx_empresa_nit', 'empresa', ['nit'])
    op.create_index('idx_empresa_estado', 'empresa', ['estado'])
    op.create_index('idx_empresa_sync', 'empresa', ['sync_source', 'external_id'])
    
    # 2. Create empleado table
    op.create_table(
        'empleado',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('empresa_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('numero_documento', sa.String(20), nullable=False),
        sa.Column('tipo_documento', sa.String(20), nullable=False),
        sa.Column('nombres', sa.String(100), nullable=False),
        sa.Column('apellidos', sa.String(100), nullable=False),
        sa.Column('email', sa.String(100), nullable=True),
        sa.Column('telefono', sa.String(20), nullable=True),
        sa.Column('fecha_nacimiento', sa.Date(), nullable=True),
        sa.Column('genero', sa.String(1), nullable=True),
        sa.Column('cargo', sa.String(100), nullable=True),
        sa.Column('area', sa.String(100), nullable=True),
        sa.Column('fecha_ingreso', sa.Date(), nullable=False),
        sa.Column('fecha_retiro', sa.Date(), nullable=True),
        sa.Column('salario_base', sa.Numeric(15, 2), nullable=True),
        sa.Column('cuenta_bancaria', sa.String(50), nullable=True),
        sa.Column('banco', sa.String(100), nullable=True),
        sa.Column('tipo_cuenta', sa.String(20), nullable=True),
        sa.Column('estado', sa.String(20), nullable=False, server_default='ACTIVO'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('sync_source', sa.String(50), nullable=True),
        sa.Column('external_id', sa.String(100), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['empresa_id'], ['empresa.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('empresa_id', 'tipo_documento', 'numero_documento', name='uq_empleado_doc_empresa'),
        sa.CheckConstraint("estado IN ('ACTIVO', 'INACTIVO', 'RETIRADO')", name='chk_empleado_estado'),
        sa.CheckConstraint("tipo_documento IN ('CC', 'CE', 'TI', 'PASAPORTE', 'PEP')", name='chk_empleado_tipo_doc'),
        sa.CheckConstraint("genero IN ('M', 'F', 'O')", name='chk_empleado_genero'),
        sa.CheckConstraint("tipo_cuenta IN ('AHORROS', 'CORRIENTE')", name='chk_empleado_tipo_cuenta')
    )
    op.create_index('idx_empleado_empresa', 'empleado', ['empresa_id'])
    op.create_index('idx_empleado_documento', 'empleado', ['tipo_documento', 'numero_documento'])
    op.create_index('idx_empleado_estado', 'empleado', ['estado'])
    op.create_index('idx_empleado_nombre', 'empleado', ['nombres', 'apellidos'])
    op.create_index('idx_empleado_sync', 'empleado', ['sync_source', 'external_id'])
    
    # 3. Create afiliado table (NEW for SALUD support)
    op.create_table(
        'afiliado',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('numero_poliza', sa.String(50), nullable=False),
        sa.Column('tipo_poliza', sa.String(50), nullable=False),
        sa.Column('tipo_documento', sa.String(20), nullable=False),
        sa.Column('numero_documento', sa.String(20), nullable=False),
        sa.Column('nombres', sa.String(100), nullable=False),
        sa.Column('apellidos', sa.String(100), nullable=False),
        sa.Column('email', sa.String(100), nullable=True),
        sa.Column('telefono', sa.String(20), nullable=True),
        sa.Column('fecha_nacimiento', sa.Date(), nullable=True),
        sa.Column('genero', sa.String(1), nullable=True),
        sa.Column('direccion', sa.String(200), nullable=True),
        sa.Column('ciudad', sa.String(100), nullable=True),
        sa.Column('departamento', sa.String(100), nullable=True),
        sa.Column('fecha_inicio_poliza', sa.Date(), nullable=False),
        sa.Column('fecha_fin_poliza', sa.Date(), nullable=True),
        sa.Column('cuenta_bancaria', sa.String(50), nullable=True),
        sa.Column('banco', sa.String(100), nullable=True),
        sa.Column('tipo_cuenta', sa.String(20), nullable=True),
        sa.Column('estado', sa.String(20), nullable=False, server_default='ACTIVO'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('sync_source', sa.String(50), nullable=True),
        sa.Column('external_id', sa.String(100), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('numero_poliza'),
        sa.CheckConstraint("estado IN ('ACTIVO', 'INACTIVO', 'SUSPENDIDO')", name='chk_afiliado_estado'),
        sa.CheckConstraint("tipo_documento IN ('CC', 'CE', 'TI', 'PASAPORTE', 'PEP')", name='chk_afiliado_tipo_doc'),
        sa.CheckConstraint("tipo_poliza IN ('INDIVIDUAL', 'FAMILIAR', 'COLECTIVA')", name='chk_afiliado_tipo_poliza'),
        sa.CheckConstraint("genero IN ('M', 'F', 'O')", name='chk_afiliado_genero'),
        sa.CheckConstraint("tipo_cuenta IN ('AHORROS', 'CORRIENTE')", name='chk_afiliado_tipo_cuenta')
    )
    op.create_index('idx_afiliado_poliza', 'afiliado', ['numero_poliza'])
    op.create_index('idx_afiliado_documento', 'afiliado', ['tipo_documento', 'numero_documento'])
    op.create_index('idx_afiliado_estado', 'afiliado', ['estado'])
    op.create_index('idx_afiliado_nombre', 'afiliado', ['nombres', 'apellidos'])
    op.create_index('idx_afiliado_sync', 'afiliado', ['sync_source', 'external_id'])
    
    # 4. Create usuario table
    op.create_table(
        'usuario',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('username', sa.String(50), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('nombre_completo', sa.String(255), nullable=False),
        sa.Column('rol', sa.String(50), nullable=False),
        sa.Column('estado', sa.String(20), nullable=False, server_default='ACTIVO'),
        sa.Column('empleado_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('empresa_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('ultimo_acceso', sa.DateTime(timezone=True), nullable=True),
        sa.Column('intentos_fallidos', sa.Integer(), server_default='0', nullable=False),
        sa.Column('bloqueado_hasta', sa.DateTime(timezone=True), nullable=True),
        sa.Column('token_version', sa.Integer(), server_default='0', nullable=False),
        sa.Column('must_change_password', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['empleado_id'], ['empleado.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['empresa_id'], ['empresa.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
        sa.UniqueConstraint('email'),
        sa.CheckConstraint("estado IN ('ACTIVO', 'INACTIVO', 'BLOQUEADO')", name='chk_usuario_estado'),
        sa.CheckConstraint("rol IN ('ADMIN', 'AUDITOR', 'APROBADOR', 'EMPRESA', 'EMPLEADO', 'READONLY')", name='chk_usuario_rol')
    )
    op.create_index('idx_usuario_username', 'usuario', ['username'])
    op.create_index('idx_usuario_email', 'usuario', ['email'])
    op.create_index('idx_usuario_rol', 'usuario', ['rol'])
    op.create_index('idx_usuario_empresa', 'usuario', ['empresa_id'])
    
    # 5. Create siniestro table
    op.create_table(
        'siniestro',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('numero_siniestro', sa.String(50), nullable=False),
        sa.Column('empleado_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('empresa_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('fecha_siniestro', sa.Date(), nullable=False),
        sa.Column('hora_siniestro', sa.Time(), nullable=True),
        sa.Column('tipo_siniestro', sa.String(50), nullable=False),
        sa.Column('descripcion', sa.Text(), nullable=False),
        sa.Column('lugar_ocurrencia', sa.String(255), nullable=True),
        sa.Column('parte_cuerpo_afectada', sa.String(100), nullable=True),
        sa.Column('naturaleza_lesion', sa.String(100), nullable=True),
        sa.Column('agente_causante', sa.String(255), nullable=True),
        sa.Column('gravedad', sa.String(20), server_default='LEVE', nullable=False),
        sa.Column('testigos', sa.Text(), nullable=True),
        sa.Column('requirio_hospitalizacion', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('dias_estimados_incapacidad', sa.Integer(), nullable=True),
        sa.Column('estado', sa.String(20), nullable=False, server_default='REPORTADO'),
        sa.Column('fecha_reporte', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('reportado_por', sa.String(255), nullable=True),
        sa.Column('observaciones', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('sync_source', sa.String(50), nullable=True),
        sa.Column('external_id', sa.String(100), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['empleado_id'], ['empleado.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['empresa_id'], ['empresa.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('numero_siniestro'),
        sa.CheckConstraint("tipo_siniestro IN ('ACCIDENTE_TRABAJO', 'ENFERMEDAD_LABORAL', 'ACCIDENTE_TRAYECTO')", name='chk_siniestro_tipo'),
        sa.CheckConstraint("gravedad IN ('LEVE', 'MODERADO', 'GRAVE', 'MORTAL')", name='chk_siniestro_gravedad'),
        sa.CheckConstraint("estado IN ('REPORTADO', 'EN_INVESTIGACION', 'CERRADO', 'ANULADO')", name='chk_siniestro_estado')
    )
    op.create_index('idx_siniestro_numero', 'siniestro', ['numero_siniestro'])
    op.create_index('idx_siniestro_empleado', 'siniestro', ['empleado_id'])
    op.create_index('idx_siniestro_empresa', 'siniestro', ['empresa_id'])
    op.create_index('idx_siniestro_fecha', 'siniestro', ['fecha_siniestro'])
    op.create_index('idx_siniestro_tipo', 'siniestro', ['tipo_siniestro'])
    op.create_index('idx_siniestro_estado', 'siniestro', ['estado'])
    op.create_index('idx_siniestro_sync', 'siniestro', ['sync_source', 'external_id'])
    
    # 6. Create incapacidad table (with polymorphic ARL/SALUD support)
    op.create_table(
        'incapacidad',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('numero', sa.String(50), nullable=False),
        # Polymorphic relationships: empleado+empresa for ARL, afiliado for SALUD
        sa.Column('empleado_id', postgresql.UUID(as_uuid=True), nullable=True),  # Required for ARL, NULL for SALUD
        sa.Column('empresa_id', postgresql.UUID(as_uuid=True), nullable=True),   # Required for ARL, NULL for SALUD
        sa.Column('afiliado_id', postgresql.UUID(as_uuid=True), nullable=True),  # Required for SALUD, NULL for ARL
        sa.Column('siniestro_id', postgresql.UUID(as_uuid=True), nullable=True), # Only for ARL
        sa.Column('numero_siniestro', sa.String(50), nullable=True),             # Only for ARL
        sa.Column('tipo', sa.String(20), nullable=False),
        sa.Column('subtipo', sa.String(50), nullable=True),
        sa.Column('fecha_inicio', sa.Date(), nullable=False),
        sa.Column('fecha_fin', sa.Date(), nullable=False),
        sa.Column('dias_totales', sa.Integer(), nullable=False),
        sa.Column('diagnostico_cie10', sa.String(10), nullable=True),
        sa.Column('descripcion_diagnostico', sa.Text(), nullable=True),
        sa.Column('eps', sa.String(255), nullable=True),
        sa.Column('ips', sa.String(255), nullable=True),
        sa.Column('valor_dia', sa.Numeric(15, 2), nullable=True),
        sa.Column('valor_total', sa.Numeric(15, 2), nullable=True),
        sa.Column('estado', sa.String(30), nullable=False, server_default='RADICADA'),
        sa.Column('observaciones', sa.Text(), nullable=True),
        sa.Column('motivo_rechazo', sa.Text(), nullable=True),
        sa.Column('radicado_por_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('auditado_por_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('aprobado_por_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('fecha_radicacion', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('fecha_auditoria', sa.DateTime(timezone=True), nullable=True),
        sa.Column('fecha_aprobacion', sa.DateTime(timezone=True), nullable=True),
        sa.Column('fecha_rechazo', sa.DateTime(timezone=True), nullable=True),
        sa.Column('prioridad', sa.String(20), server_default='NORMAL', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['empleado_id'], ['empleado.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['empresa_id'], ['empresa.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['afiliado_id'], ['afiliado.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['siniestro_id'], ['siniestro.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['radicado_por_id'], ['usuario.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['auditado_por_id'], ['usuario.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['aprobado_por_id'], ['usuario.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('numero'),
        sa.CheckConstraint("tipo IN ('ARL', 'SALUD')", name='chk_incapacidad_tipo'),
        sa.CheckConstraint(
            "estado IN ('RADICADA', 'EN_AUDITORIA', 'OBSERVADA', 'APROBADA', 'RECHAZADA', 'EN_PAGO', 'PAGADA', 'CANCELADA')", 
            name='chk_incapacidad_estado'
        ),
        sa.CheckConstraint("prioridad IN ('BAJA', 'NORMAL', 'ALTA', 'URGENTE')", name='chk_incapacidad_prioridad'),
        sa.CheckConstraint("fecha_fin >= fecha_inicio", name='chk_incapacidad_fechas'),
        # Critical constraint: enforce correct relationships based on tipo
        sa.CheckConstraint(
            "(tipo = 'ARL' AND empleado_id IS NOT NULL AND empresa_id IS NOT NULL AND afiliado_id IS NULL) OR "
            "(tipo = 'SALUD' AND afiliado_id IS NOT NULL AND empleado_id IS NULL AND empresa_id IS NULL)",
            name='chk_incapacidad_tipo_relacion'
        )
    )
    op.create_index('idx_incapacidad_numero', 'incapacidad', ['numero'])
    op.create_index('idx_incapacidad_empleado', 'incapacidad', ['empleado_id'])
    op.create_index('idx_incapacidad_empresa', 'incapacidad', ['empresa_id'])
    op.create_index('idx_incapacidad_afiliado', 'incapacidad', ['afiliado_id'])
    op.create_index('idx_incapacidad_siniestro', 'incapacidad', ['siniestro_id'])
    op.create_index('idx_incapacidad_numero_siniestro', 'incapacidad', ['numero_siniestro'])
    op.create_index('idx_incapacidad_estado', 'incapacidad', ['estado'])
    op.create_index('idx_incapacidad_tipo', 'incapacidad', ['tipo'])
    op.create_index('idx_incapacidad_fecha_radicacion', 'incapacidad', ['fecha_radicacion'])
    op.create_index('idx_incapacidad_fecha_inicio', 'incapacidad', ['fecha_inicio'])
    op.create_index('idx_incapacidad_auditado_por', 'incapacidad', ['auditado_por_id'])
    
    # 7. Create documento table
    op.create_table(
        'documento',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('incapacidad_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tipo_documento', sa.String(50), nullable=False),
        sa.Column('nombre_archivo', sa.String(255), nullable=False),
        sa.Column('nombre_original', sa.String(255), nullable=False),
        sa.Column('ruta_storage', sa.String(500), nullable=False),
        sa.Column('bucket', sa.String(100), nullable=False),
        sa.Column('mime_type', sa.String(100), nullable=False),
        sa.Column('tamanio_bytes', sa.BigInteger(), nullable=False),
        sa.Column('hash_md5', sa.String(32), nullable=True),
        sa.Column('hash_sha256', sa.String(64), nullable=True),
        sa.Column('uploaded_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('validado', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('observacion_validacion', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['incapacidad_id'], ['incapacidad.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['uploaded_by_id'], ['usuario.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint(
            "tipo_documento IN ('INCAPACIDAD_MEDICA', 'CEDULA', 'HISTORIA_CLINICA', 'SOPORTE_PAGO', 'OTROS')",
            name='chk_documento_tipo'
        )
    )
    op.create_index('idx_documento_incapacidad', 'documento', ['incapacidad_id'])
    op.create_index('idx_documento_tipo', 'documento', ['tipo_documento'])
    op.create_index('idx_documento_hash', 'documento', ['hash_sha256'])
    
    # 8. Create historial_estado table
    op.create_table(
        'historial_estado',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('incapacidad_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('estado_anterior', sa.String(30), nullable=True),
        sa.Column('estado_nuevo', sa.String(30), nullable=False),
        sa.Column('observacion', sa.Text(), nullable=True),
        sa.Column('cambiado_por_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('ip_address', postgresql.INET(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['incapacidad_id'], ['incapacidad.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['cambiado_por_id'], ['usuario.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_historial_incapacidad', 'historial_estado', ['incapacidad_id'])
    op.create_index('idx_historial_created_at', 'historial_estado', [sa.text('created_at DESC')])
    
    # 9. Create orden_pago table
    op.create_table(
        'orden_pago',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('numero_orden', sa.String(50), nullable=False),
        sa.Column('incapacidad_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('beneficiario_tipo', sa.String(20), nullable=False),
        sa.Column('beneficiario_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('beneficiario_nombre', sa.String(255), nullable=False),
        sa.Column('beneficiario_documento', sa.String(50), nullable=False),
        sa.Column('cuenta_bancaria', sa.String(50), nullable=True),
        sa.Column('banco', sa.String(100), nullable=True),
        sa.Column('tipo_cuenta', sa.String(20), nullable=True),
        sa.Column('valor_pagar', sa.Numeric(15, 2), nullable=False),
        sa.Column('estado_pago', sa.String(30), nullable=False, server_default='GENERADA'),
        sa.Column('fecha_generacion', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('fecha_pago', sa.DateTime(timezone=True), nullable=True),
        sa.Column('fecha_anulacion', sa.DateTime(timezone=True), nullable=True),
        sa.Column('metodo_pago', sa.String(50), nullable=True),
        sa.Column('referencia_pago', sa.String(100), nullable=True),
        sa.Column('comprobante_ruta', sa.String(500), nullable=True),
        sa.Column('motivo_anulacion', sa.Text(), nullable=True),
        sa.Column('creado_por_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('aprobado_por_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['incapacidad_id'], ['incapacidad.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['creado_por_id'], ['usuario.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['aprobado_por_id'], ['usuario.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('numero_orden'),
        sa.CheckConstraint("beneficiario_tipo IN ('EMPLEADO', 'EMPRESA', 'IPS', 'AFILIADO')", name='chk_orden_beneficiario_tipo'),
        sa.CheckConstraint(
            "estado_pago IN ('GENERADA', 'APROBADA', 'EN_PROCESO', 'PAGADA', 'RECHAZADA', 'ANULADA')",
            name='chk_orden_estado'
        )
    )
    op.create_index('idx_orden_numero', 'orden_pago', ['numero_orden'])
    op.create_index('idx_orden_incapacidad', 'orden_pago', ['incapacidad_id'])
    op.create_index('idx_orden_estado', 'orden_pago', ['estado_pago'])
    op.create_index('idx_orden_beneficiario', 'orden_pago', ['beneficiario_id'])
    op.create_index('idx_orden_fecha_generacion', 'orden_pago', ['fecha_generacion'])
    
    # 10. Create auditoria_log table
    op.create_table(
        'auditoria_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), nullable=False),
        sa.Column('usuario_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('accion', sa.String(50), nullable=False),
        sa.Column('entidad', sa.String(50), nullable=False),
        sa.Column('entidad_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('detalles', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('ip_address', postgresql.INET(), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('request_id', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuario.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_auditoria_usuario', 'auditoria_log', ['usuario_id'])
    op.create_index('idx_auditoria_entidad', 'auditoria_log', ['entidad', 'entidad_id'])
    op.create_index('idx_auditoria_accion', 'auditoria_log', ['accion'])
    op.create_index('idx_auditoria_created_at', 'auditoria_log', [sa.text('created_at DESC')])
    op.create_index('idx_auditoria_detalles', 'auditoria_log', ['detalles'], postgresql_using='gin')


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table('auditoria_log')
    op.drop_table('orden_pago')
    op.drop_table('historial_estado')
    op.drop_table('documento')
    op.drop_table('incapacidad')
    op.drop_table('siniestro')
    op.drop_table('usuario')
    op.drop_table('afiliado')
    op.drop_table('empleado')
    op.drop_table('empresa')
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')

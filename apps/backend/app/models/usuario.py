"""
Modelo SQLAlchemy para Usuario.
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from sqlalchemy import String, Integer, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID, TIMESTAMP

from app.models.base import BaseModel
from app.utils.enums import RolUsuario, EstadoUsuario, SucursalSiniestro


class Usuario(BaseModel):
    """Modelo de Usuario del sistema."""
    
    __tablename__ = "usuario"
    
    # Credenciales
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Información personal
    nombre_completo: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Rol y estado
    rol: Mapped[RolUsuario] = mapped_column(String(50), nullable=False, index=True)
    estado: Mapped[EstadoUsuario] = mapped_column(
        String(20),
        nullable=False,
        default=EstadoUsuario.ACTIVO
    )
    
    # Relaciones opcionales con empleado y empresa
    empleado_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("empleado.id", ondelete="SET NULL")
    )
    empresa_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("empresa.id", ondelete="SET NULL"),
        index=True
    )
    
    # Seguridad y control de acceso
    ultimo_acceso: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True))
    intentos_fallidos: Mapped[int] = mapped_column(Integer, default=0)
    bloqueado_hasta: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True))
    token_version: Mapped[int] = mapped_column(Integer, default=0)
    must_change_password: Mapped[bool] = mapped_column(Boolean, default=False)

    # Auditoría por sucursal
    sucursal: Mapped[Optional[SucursalSiniestro]] = mapped_column(
        String(50),
        nullable=True,
        comment="Sucursal asignada (solo aplica a rol=AUDITOR); determina qué incapacidades ARL puede recibir",
    )
    incapacidades_asignadas_activas: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0",
        comment="Contador de incapacidades actualmente asignadas y abiertas (balanceo de carga); no es acumulado histórico",
    )

    # Relaciones
    empleado: Mapped[Optional["Empleado"]] = relationship(
        "Empleado",
        back_populates="usuario",
        lazy="selectin"
    )
    empresa: Mapped[Optional["Empresa"]] = relationship(
        "Empresa",
        back_populates="usuarios",
        lazy="selectin"
    )
    
    # Incapacidades relacionadas (como radicador, auditor, aprobador)
    incapacidades_radicadas: Mapped[List["Incapacidad"]] = relationship(
        "Incapacidad",
        foreign_keys="[Incapacidad.radicado_por_id]",
        back_populates="radicado_por",
        lazy="selectin"
    )
    incapacidades_auditadas: Mapped[List["Incapacidad"]] = relationship(
        "Incapacidad",
        foreign_keys="[Incapacidad.auditado_por_id]",
        back_populates="auditado_por",
        lazy="selectin"
    )
    incapacidades_aprobadas: Mapped[List["Incapacidad"]] = relationship(
        "Incapacidad",
        foreign_keys="[Incapacidad.aprobado_por_id]",
        back_populates="aprobado_por",
        lazy="selectin"
    )
    
    # Historial de cambios de estado
    cambios_estado: Mapped[List["HistorialEstado"]] = relationship(
        "HistorialEstado",
        back_populates="cambiado_por",
        lazy="selectin"
    )
    
    # Documentos subidos
    documentos_subidos: Mapped[List["Documento"]] = relationship(
        "Documento",
        back_populates="uploaded_by",
        lazy="selectin"
    )
    
    # Órdenes de pago creadas
    ordenes_pago_creadas: Mapped[List["OrdenPago"]] = relationship(
        "OrdenPago",
        foreign_keys="[OrdenPago.creado_por_id]",
        back_populates="creado_por",
        lazy="noload"
    )
    
    # Logs de auditoría
    auditoria_logs: Mapped[List["AuditoriaLog"]] = relationship(
        "AuditoriaLog",
        back_populates="usuario",
        lazy="selectin"
    )
    
    # Refresh tokens
    refresh_tokens: Mapped[List["RefreshToken"]] = relationship(
        "RefreshToken",
        back_populates="usuario",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    def __repr__(self) -> str:
        return f"<Usuario {self.username} - {self.rol}>"
    
    @property
    def is_active(self) -> bool:
        """Verifica si el usuario está activo y no bloqueado."""
        if self.estado != EstadoUsuario.ACTIVO:
            return False
        if self.bloqueado_hasta and self.bloqueado_hasta > datetime.utcnow():
            return False
        return True
    
    def increment_failed_attempts(self) -> None:
        """Incrementa los intentos fallidos de login."""
        self.intentos_fallidos += 1
        if self.intentos_fallidos >= 5:
            # Bloquear usuario por 30 minutos
            from datetime import timedelta
            self.bloqueado_hasta = datetime.utcnow() + timedelta(minutes=30)
    
    def reset_failed_attempts(self) -> None:
        """Resetea los intentos fallidos después de login exitoso."""
        self.intentos_fallidos = 0
        self.bloqueado_hasta = None
        self.ultimo_acceso = datetime.utcnow()

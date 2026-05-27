"""
Models package.
Import all models here to make them available for Alembic migrations.
"""
from apps.backend.app.models.base import Base, BaseModel
from apps.backend.app.models.empresa import Empresa
from apps.backend.app.models.empleado import Empleado
from apps.backend.app.models.afiliado import Afiliado
from apps.backend.app.models.usuario import Usuario
from apps.backend.app.models.solicitante import Solicitante
from apps.backend.app.models.siniestro import Siniestro
from apps.backend.app.models.incapacidad import Incapacidad
from apps.backend.app.models.documento import Documento
from apps.backend.app.models.historial_estado import HistorialEstado
from apps.backend.app.models.orden_pago import OrdenPago
from apps.backend.app.models.auditoria_log import AuditoriaLog
from apps.backend.app.models.refresh_token import RefreshToken
from apps.backend.app.models.catalogo_cie10 import CatalogoCIE10
from apps.backend.app.models.auditoria_datos_aprobados import AuditoriaDatosAprobados

__all__ = [
    "Base",
    "BaseModel",
    "Empresa",
    "Empleado",
    "Afiliado",
    "Usuario",
    "Solicitante",
    "Siniestro",
    "Incapacidad",
    "Documento",
    "HistorialEstado",
    "OrdenPago",
    "AuditoriaLog",
    "RefreshToken",
    "CatalogoCIE10",
    "AuditoriaDatosAprobados",
]

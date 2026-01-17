"""
Models package.
Import all models here to make them available for Alembic migrations.
"""
from app.models.base import Base, BaseModel
from app.models.empresa import Empresa
from app.models.empleado import Empleado
from app.models.afiliado import Afiliado
from app.models.usuario import Usuario
from app.models.solicitante import Solicitante
from app.models.siniestro import Siniestro
from app.models.incapacidad import Incapacidad
from app.models.documento import Documento
from app.models.historial_estado import HistorialEstado
from app.models.orden_pago import OrdenPago
from app.models.auditoria_log import AuditoriaLog
from app.models.refresh_token import RefreshToken
from app.models.catalogo_cie10 import CatalogoCIE10

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
]

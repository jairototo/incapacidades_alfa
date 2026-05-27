"""
Services package.

Expone los servicios de lógica de negocio.
"""
from apps.backend.app.services.afiliado_service import AfiliadoService, afiliado_service
from apps.backend.app.services.empresa_service import EmpresaService, empresa_service
from apps.backend.app.services.empleado_service import EmpleadoService, empleado_service
from apps.backend.app.services.incapacidad_service import IncapacidadService, incapacidad_service
from apps.backend.app.services.siniestro_service import SiniestroService, siniestro_service
from apps.backend.app.services.historial_estado_service import HistorialEstadoService, historial_estado_service

__all__ = [
    "AfiliadoService",
    "afiliado_service",
    "EmpresaService",
    "empresa_service",
    "EmpleadoService",
    "empleado_service",
    "IncapacidadService",
    "incapacidad_service",
    "SiniestroService",
    "siniestro_service",
    "HistorialEstadoService",
    "historial_estado_service",
]

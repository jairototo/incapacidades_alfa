"""
Repositories package.

Expone los repositorios disponibles para acceso a datos.
"""
from apps.backend.app.db.repositories.base_repository import BaseRepository
from apps.backend.app.db.repositories.afiliado_repository import (
    AfiliadoRepository,
    afiliado_repository
)
from apps.backend.app.db.repositories.empresa_repository import (
    EmpresaRepository,
    empresa_repository
)
from apps.backend.app.db.repositories.empleado_repository import (
    EmpleadoRepository,
    empleado_repository
)
from apps.backend.app.db.repositories.incapacidad_repository import (
    IncapacidadRepository,
    incapacidad_repository
)
from apps.backend.app.db.repositories.siniestro_repository import (
    SiniestroRepository,
    siniestro_repository
)
from apps.backend.app.db.repositories.historial_estado_repository import (
    HistorialEstadoRepository,
    historial_estado_repository
)

__all__ = [
    "BaseRepository",
    "AfiliadoRepository",
    "afiliado_repository",
    "EmpresaRepository",
    "empresa_repository",
    "EmpleadoRepository",
    "empleado_repository",
    "IncapacidadRepository",
    "incapacidad_repository",
    "SiniestroRepository",
    "siniestro_repository",
    "HistorialEstadoRepository",
    "historial_estado_repository",
]

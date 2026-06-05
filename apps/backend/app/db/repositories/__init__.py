"""
Repositories package.

Expone los repositorios disponibles para acceso a datos.
"""
from app.db.repositories.base_repository import BaseRepository
from app.db.repositories.afiliado_repository import (
    AfiliadoRepository,
    afiliado_repository
)
from app.db.repositories.empresa_repository import (
    EmpresaRepository,
    empresa_repository
)
from app.db.repositories.empleado_repository import (
    EmpleadoRepository,
    empleado_repository
)
from app.db.repositories.incapacidad_repository import (
    IncapacidadRepository,
    incapacidad_repository
)
from app.db.repositories.siniestro_repository import (
    SiniestroRepository,
    siniestro_repository
)
from app.db.repositories.historial_estado_repository import (
    HistorialEstadoRepository,
    historial_estado_repository
)
from app.db.repositories.pre_incapacidad_repository import (
    PreIncapacidadRepository
)
from app.db.repositories.validation_inconsistencia_repository import (
    ValidationInconsistenciaRepository
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
    "PreIncapacidadRepository",
    "ValidationInconsistenciaRepository",
]

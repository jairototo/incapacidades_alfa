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
from app.db.repositories.smlmv_parametros_repository import (
    SmlmvParametrosRepository,
    smlmv_parametros_repository
)
from app.db.repositories.previsionales import (
    LotePrevisionalRepository,
    lote_previsional_repository,
    IncapacidadPrevisionalRepository,
    incapacidad_previsional_repository,
    PeriodoPrevisionalRepository,
    periodo_previsional_repository,
    SiniestroPrevisionalRepository,
    siniestro_previsional_repository,
    SolicitudPrevisionalRepository,
    solicitud_previsional_repository,
    IteHistoricoRepository,
    ite_historico_repository,
    SenalAuditoriaPrevisionalRepository,
    senal_auditoria_previsional_repository,
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
    "SmlmvParametrosRepository",
    "smlmv_parametros_repository",
    "LotePrevisionalRepository",
    "lote_previsional_repository",
    "IncapacidadPrevisionalRepository",
    "incapacidad_previsional_repository",
    "PeriodoPrevisionalRepository",
    "periodo_previsional_repository",
    "SiniestroPrevisionalRepository",
    "siniestro_previsional_repository",
    "SolicitudPrevisionalRepository",
    "solicitud_previsional_repository",
    "IteHistoricoRepository",
    "ite_historico_repository",
    "SenalAuditoriaPrevisionalRepository",
    "senal_auditoria_previsional_repository",
]

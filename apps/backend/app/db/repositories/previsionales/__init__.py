"""
Repositories for previsionales (pension) domain.

Este paquete espeja `app/models/previsionales/` — un repositorio por
modelo, cada uno subclase de `BaseRepository` con su instancia singleton al
final del módulo (mismo patrón que el resto de `app/db/repositories/`).

`SmlmvParametrosRepository` (Task 0.2) vive en
`app/db/repositories/smlmv_parametros_repository.py`, un nivel arriba —
no se recrea aquí.
"""
from app.db.repositories.previsionales.lote_previsional_repository import (
    LotePrevisionalRepository,
    lote_previsional_repository,
)
from app.db.repositories.previsionales.incapacidad_previsional_repository import (
    IncapacidadPrevisionalRepository,
    incapacidad_previsional_repository,
)
from app.db.repositories.previsionales.periodo_previsional_repository import (
    PeriodoPrevisionalRepository,
    periodo_previsional_repository,
)
from app.db.repositories.previsionales.siniestro_previsional_repository import (
    SiniestroPrevisionalRepository,
    siniestro_previsional_repository,
)
from app.db.repositories.previsionales.solicitud_previsional_repository import (
    SolicitudPrevisionalRepository,
    solicitud_previsional_repository,
)
from app.db.repositories.previsionales.ite_historico_repository import (
    IteHistoricoRepository,
    ite_historico_repository,
)
from app.db.repositories.previsionales.senal_auditoria_previsional_repository import (
    SenalAuditoriaPrevisionalRepository,
    senal_auditoria_previsional_repository,
)

__all__ = [
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

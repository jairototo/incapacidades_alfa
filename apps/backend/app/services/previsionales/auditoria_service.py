"""
Servicio de orquestación de auditoría previsional (Task 3.3).

Conecta el motor puro de 19 reglas AB-AT (Task 1.4, `auditoria_rules.py`) con
la persistencia (`SenalAuditoriaPrevisional`, Tasks 2.1/2.2) y las
referencias externas ya importadas por Task 3.2
(`siniestros_previsionales`/`solicitudes_previsionales`/`ite_historico`).
Es el primer llamador REAL de `evaluar_todas`/`agrupar_repetidas` fuera de
sus propios tests — `lote_service.py` (Task 3.1) ya usa
`agrupar_repetidas`/`encadenar_prorrogas` en tiempo de carga para poblar
`es_duplicado_interno`/`prorroga_de_id`, pero eso es un problema DISTINTO
(deduplicación/encadenamiento estructural) del que resuelve este módulo
(evaluación de las 19 señales AB-AT y su persistencia).

Diferencia deliberada con `app/services/auditoria_service.py` (el
orquestador ARL/SALUD, línea ~109 en la versión revisada para este brief):
ese servicio hace un `db.commit()` por incapacidad dentro de un loop. Aquí
se seleccionó el patrón "caller-managed transaction" que ya usan
`lote_service.py`/los repositorios previsionales: `flush()`s internos por
escritura y UN SOLO `commit()` en el punto de entrada público
(`auditar_lote`, `auditar_incapacidad`, `registrar_aval`, `duplicar`).

Contratos heredados de `auditoria_rules.py` que este módulo respeta sin
"arreglar" con heurísticas (ver docstring de ese módulo para el detalle
completo):
- AC (aval) nunca se autocalcula — `registrar_aval` es la ÚNICA vía para
  cambiarlo, y siempre requiere una acción humana explícita.
- AM-AP (selección de siniestro): si `ContextoAuditoria.siniestros_por_id`
  trae 2+ candidatos para una identificación, las reglas ya devuelven
  PENDIENTE con el payload de ambigüedad — este servicio no interviene ahí,
  solo construye el contexto y serializa lo que las reglas devuelven.
"""
from dataclasses import asdict, is_dataclass
from datetime import date, datetime, timezone
from typing import Any, Literal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, NotFoundException
from app.db.repositories.previsionales import (
    incapacidad_previsional_repository,
    ite_historico_repository,
    senal_auditoria_previsional_repository,
    siniestro_previsional_repository,
    solicitud_previsional_repository,
)
from app.models.previsionales.incapacidad_previsional import IncapacidadPrevisional
from app.services.previsionales.auditoria_rules import (
    ContextoAuditoria,
    Senal,
    SiniestroRef,
    SolicitudRef,
    agrupar_repetidas,
    evaluar_todas,
)
from app.utils.enums import AvalPrevisional, EstadoIncapacidadPrevisional

# ---------------------------------------------------------------------------
# Campos que SÍ se copian del registro origen al duplicar (Task 3.3,
# `AuditoriaPrevisionalService.duplicar`). La AFP reportó varias
# incapacidades reales en una sola fila del excel; el auditor las separa
# manualmente en filas con fechas propias. Todo lo que sigue abajo de esta
# lista queda EXCLUIDO deliberadamente, por columna:
#
# - fecha_inicial/fecha_final: son justamente lo que `fechas` reemplaza —
#   todo el propósito de `duplicar` es darle a la copia SUS PROPIAS fechas.
# - dia_181_alfa/dia_181_arpis/fecha_crie: dependen del rango de fechas
#   específico (cómputo de auditor / cruce con ARPIS), no tiene sentido
#   heredarlos de un rango de fechas distinto — deben recalcularse para el
#   nuevo rango en un paso posterior (re-auditoría de la nueva fila).
# - aval/motivo_no_aval/usuario_auditoria_id/fecha_auditoria: la copia es
#   una incapacidad NUEVA que necesita su propia decisión humana — heredar
#   un aval del origen sería autocalcularlo por la puerta trasera,
#   violando el contrato de la regla AC (nunca se autocalcula).
# - estado: se deja en el default del modelo (SIN_SINIESTRO) — la copia
#   empieza su propio ciclo de vida, no hereda el estado a medio camino
#   del origen.
# - valor_auditado/diferencia_valor_afp: dependen de la liquidación del
#   NUEVO rango de fechas (`liquidacion_previsional.calcular_valor`), no
#   se copian sin recalcular — copiar el valor del origen sería un valor
#   distinto y falso para el rango nuevo.
# - errores_carga: la copia no vino de un parseo de excel: empieza limpia.
# - prorroga_de_id: cadena de prórrogas específica del origen y de SU
#   rango de fechas; no se asume que la copia herede la misma cadena.
# - es_duplicado_interno/incapacidad_origen_id: se fijan explícitamente
#   aparte (`True` / `origen.id`), no vienen de esta lista.
# - metadata_: se copia por separado (merge, no overwrite) para preservar
#   contexto del origen (aseguradora, estado_afiliado, etc. — ver
#   `lote_service._construir_metadata`) mientras se agrega la marca de
#   quién duplicó — ver `AuditoriaPrevisionalService.duplicar`.
# ---------------------------------------------------------------------------
_CAMPOS_COPIABLES_EN_DUPLICADO: tuple[str, ...] = (
    "lote_id",
    "tipo_identificacion",
    "identificacion",
    "radicado",
    "radicado_normalizado",
    "tipo_ingreso",
    "dia_181_afp",
    "fecha_radicacion_afp",
    "fecha_radicacion_alfa",
    "numero_siniestro",
    "valor_afp",
    "cie10",
    "observacion",
    "observacion_causal",
)


def _row_from_incapacidad(inc: IncapacidadPrevisional) -> dict:
    """
    Traduce una `IncapacidadPrevisional` ORM al `dict` que
    `evaluar_todas`/`agrupar_repetidas` (`auditoria_rules.py`) esperan leer
    con `.get(...)` — mismo principio que `lote_service.cargar_lote` ya
    aplica al construir `filas_para_reglas`: solo las claves que las 19
    reglas realmente leen (ver el docstring de cada `regla_xx_*`), nunca el
    objeto ORM completo.

    Claves incluidas y qué regla(s) las leen:
        id              -> agrupar_repetidas (AD)
        identificacion  -> AD, AE, AF, AG, AH, AI, AM-AP, AT
        fecha_inicial   -> AD, AH, AQ, AT
        fecha_final     -> AI, AQ
        tipo_ingreso    -> (no lo lee ninguna regla_xx_ directamente, pero
                            se incluye por si una fila se reutiliza también
                            para encadenar_prorrogas en el futuro)
        dia_181_alfa    -> AB
        dia_181_afp     -> AL
        dia_181_arpis   -> AL
        aval            -> AC
        numero_siniestro-> AR
        valor_afp       -> AR
    """
    return {
        "id": str(inc.id),
        "identificacion": inc.identificacion,
        "fecha_inicial": inc.fecha_inicial,
        "fecha_final": inc.fecha_final,
        "tipo_ingreso": inc.tipo_ingreso,
        "dia_181_alfa": inc.dia_181_alfa,
        "dia_181_afp": inc.dia_181_afp,
        "dia_181_arpis": inc.dia_181_arpis,
        "aval": inc.aval,
        "numero_siniestro": inc.numero_siniestro,
        "valor_afp": inc.valor_afp,
    }


def _a_jsonable(valor: Any) -> Any:
    """
    Convierte un `Senal.valor` (`date | dict | bool | str | list | None`, y
    en AM-AP también `SiniestroRef` o listas de `SiniestroRef` anidadas
    dentro del payload de ambigüedad `{"candidatos": [...], "seleccionado":
    None}`) a algo JSON-serializable para la columna JSONB de
    `SenalAuditoriaPrevisional.valor`. Recursivo por la anidación de AM-AP.
    """
    if valor is None or isinstance(valor, (bool, str, int, float)):
        return valor
    if isinstance(valor, date):
        return valor.isoformat()
    if is_dataclass(valor) and not isinstance(valor, type):
        return _a_jsonable(asdict(valor))
    if isinstance(valor, dict):
        return {k: _a_jsonable(v) for k, v in valor.items()}
    if isinstance(valor, (list, tuple)):
        return [_a_jsonable(v) for v in valor]
    # Fallback defensivo (p.ej. Decimal) -- no debería alcanzarse con las
    # 19 reglas actuales, ninguna devuelve un tipo fuera de los de arriba.
    return str(valor)


def _senal_a_dict(incapacidad_id: UUID, senal: Senal) -> dict[str, Any]:
    return {
        "incapacidad_previsional_id": incapacidad_id,
        "codigo": senal.codigo,
        "nombre": senal.nombre,
        "estado": senal.estado,
        "valor": _a_jsonable(senal.valor),
        "detalle": senal.detalle,
    }


def _agrupar_siniestros(siniestros: list) -> dict[str, list[SiniestroRef]]:
    agrupados: dict[str, list[SiniestroRef]] = {}
    for s in siniestros:
        agrupados.setdefault(s.identificacion, []).append(
            SiniestroRef(
                numero_siniestro=s.numero_siniestro,
                origen=s.origen,
                estado=s.estado,
                fecha_aviso=s.fecha_aviso,
                fecha_siniestro=s.fecha_siniestro,
            )
        )
    return agrupados


def _elegir_solicitudes(solicitudes: list) -> dict[str, SolicitudRef]:
    """
    `SolicitudPrevisionalRepository.get_by_identificacion(es)` devuelve una
    LISTA por diseño (puede haber varias solicitudes históricas por
    afiliado — ver docstring de ese repositorio). `ContextoAuditoria.
    solicitudes_por_id` en cambio es `dict[str, SolicitudRef]` (Task 1.4:
    un solo valor por afiliado para las reglas AE/AF/AG). Judgment call de
    esta tarea: se resuelve tomando la PRIMERA de la lista ya ordenada por
    el repositorio (`fecha_inicial` descendente, `created_at` descendente
    como desempate) — "la solicitud vigente más probable primero", tal
    como el propio repositorio documenta. A diferencia de la selección de
    siniestro (AM, que expone la ambigüedad como PENDIENTE cuando hay 2+
    candidatos), aquí no hay una `SolicitudRef` con "candidatos" en su
    forma — el dataclass es demasiado angosto (solo `dia_181`/`fecha_crie`)
    para cargar una lista de ambigüedad sin tocar `auditoria_rules.py`
    (Task 1.4, fuera de alcance de esta tarea).
    """
    elegidas: dict[str, SolicitudRef] = {}
    for sol in solicitudes:
        if sol.identificacion in elegidas:
            continue
        elegidas[sol.identificacion] = SolicitudRef(
            dia_181=sol.dia_181, fecha_crie=sol.fecha_crie
        )
    return elegidas


class AuditoriaPrevisionalService:
    """Orquesta la evaluación y persistencia de señales AB-AT para incapacidades previsionales."""

    async def _cargar_incapacidades_y_contexto(
        self, db: AsyncSession, lote_id: UUID
    ) -> tuple[list[IncapacidadPrevisional], ContextoAuditoria]:
        """
        Construye el `ContextoAuditoria` completo de un lote en 4 queries
        totales — nunca N+1:

          1. `incapacidad_previsional_repository.get_by_lote` — TODAS las
             incapacidades del lote. También respalda
             `repetidas_por_clave` (regla AD): es lote-interno y no
             requiere query aparte, se deriva en memoria con
             `agrupar_repetidas` sobre estas mismas filas — mismo dato
             fuente que `lote_service.cargar_lote` ya usa para poblar
             `es_duplicado_interno` en tiempo de carga, pero aquí NO se
             reescribe esa columna (ver el docstring del módulo): esta
             tarea solo produce la SEÑAL AD, no toca el campo estructural.
          2. `siniestro_previsional_repository.get_by_identificaciones`
          3. `solicitud_previsional_repository.get_by_identificaciones`
          4. `ite_historico_repository.get_existentes`

        Factorizado como método privado — separado de `construir_contexto`
        (que expone solo el `ContextoAuditoria`, firma pactada en el
        brief) porque `auditar_lote` necesita TAMBIÉN la lista de
        incapacidades y no debe pagar una query adicional para conseguirla.
        """
        incapacidades = await incapacidad_previsional_repository.get_by_lote(db, lote_id)

        identificaciones = sorted(
            {inc.identificacion for inc in incapacidades if inc.identificacion}
        )
        siniestros = await siniestro_previsional_repository.get_by_identificaciones(
            db, identificaciones
        )
        solicitudes = await solicitud_previsional_repository.get_by_identificaciones(
            db, identificaciones
        )
        claves = [
            (inc.identificacion, inc.fecha_inicial)
            for inc in incapacidades
            if inc.identificacion and inc.fecha_inicial
        ]
        ite_por_clave = await ite_historico_repository.get_existentes(db, claves)

        rows = [_row_from_incapacidad(inc) for inc in incapacidades]

        ctx = ContextoAuditoria(
            solicitudes_por_id=_elegir_solicitudes(solicitudes),
            siniestros_por_id=_agrupar_siniestros(siniestros),
            ite_por_clave=ite_por_clave,
            repetidas_por_clave=agrupar_repetidas(rows),
        )
        return incapacidades, ctx

    async def construir_contexto(self, db: AsyncSession, lote_id: UUID) -> ContextoAuditoria:
        """UNA query por fuente (siniestros, solicitudes, ite_historico) para todo el lote — nunca N+1."""
        _incapacidades, ctx = await self._cargar_incapacidades_y_contexto(db, lote_id)
        return ctx

    async def _contexto_minimo(
        self, db: AsyncSession, inc: IncapacidadPrevisional
    ) -> ContextoAuditoria:
        """Contexto de UNA sola incapacidad — ver limitación documentada en `auditar_incapacidad`."""
        identificaciones = [inc.identificacion] if inc.identificacion else []
        siniestros = await siniestro_previsional_repository.get_by_identificaciones(
            db, identificaciones
        )
        solicitudes = await solicitud_previsional_repository.get_by_identificaciones(
            db, identificaciones
        )
        claves = (
            [(inc.identificacion, inc.fecha_inicial)]
            if inc.identificacion and inc.fecha_inicial
            else []
        )
        ite_por_clave = await ite_historico_repository.get_existentes(db, claves)
        return ContextoAuditoria(
            solicitudes_por_id=_elegir_solicitudes(solicitudes),
            siniestros_por_id=_agrupar_siniestros(siniestros),
            ite_por_clave=ite_por_clave,
            repetidas_por_clave=agrupar_repetidas([_row_from_incapacidad(inc)]),
        )

    async def auditar_lote(self, db: AsyncSession, lote_id: UUID) -> int:
        """
        Construye el contexto una vez, evalúa las 19 reglas para cada
        incapacidad del lote y persiste sus señales.

        Estrategia de re-auditoría (llamar dos veces sobre el mismo lote,
        p.ej. tras "Actualizar lote" recruzando siniestros): BORRA-E-INSERTA
        por incapacidad, no upsert. `evaluar_todas` siempre corre las 19
        reglas completas (nunca un subconjunto), así que no hay "señales
        parciales" que preservar entre corridas — borrar todas las previas
        de esa incapacidad (`SenalAuditoriaPrevisionalRepository.
        delete_by_incapacidad`, añadido en esta tarea) y volver a insertar
        las 19 nuevas es más simple que diffear código por código, y evita
        arrastrar señales obsoletas si Task 1.4 cambia el set de reglas en
        el futuro.

        UN SOLO `db.commit()` al final — todas las incapacidades del lote
        viven en la misma transacción.
        """
        incapacidades, ctx = await self._cargar_incapacidades_y_contexto(db, lote_id)

        for inc in incapacidades:
            senales = evaluar_todas(_row_from_incapacidad(inc), ctx)
            await senal_auditoria_previsional_repository.delete_by_incapacidad(db, inc.id)
            await senal_auditoria_previsional_repository.bulk_create_flushed(
                db, [_senal_a_dict(inc.id, s) for s in senales]
            )

        await db.commit()
        return len(incapacidades)

    async def auditar_incapacidad(
        self,
        db: AsyncSession,
        incapacidad_id: UUID,
        ctx: ContextoAuditoria | None = None,
    ) -> list[Senal]:
        """
        Audita una sola incapacidad. Si `ctx` es `None`, construye un
        contexto MÍNIMO (solo la identificación de esta fila) — más barato
        que reconstruir el lote completo, pero con una limitación
        documentada: `repetidas_por_clave` (regla AD) en ese camino solo
        puede ver ESTA fila, así que nunca detectará repetidas contra otras
        filas del mismo lote. Para AD confiable, pasar un `ctx` ya
        construido con `construir_contexto`/`auditar_lote`.

        Mismo borra-e-inserta que `auditar_lote` (ver ahí el porqué), con
        su propio `commit()` al final.
        """
        inc = await incapacidad_previsional_repository.get_by_id(db, incapacidad_id)
        if inc is None:
            raise NotFoundException(f"IncapacidadPrevisional {incapacidad_id} no encontrada")

        if ctx is None:
            ctx = await self._contexto_minimo(db, inc)

        senales = evaluar_todas(_row_from_incapacidad(inc), ctx)
        await senal_auditoria_previsional_repository.delete_by_incapacidad(db, inc.id)
        await senal_auditoria_previsional_repository.bulk_create_flushed(
            db, [_senal_a_dict(inc.id, s) for s in senales]
        )
        await db.commit()
        return senales

    async def registrar_aval(
        self,
        db: AsyncSession,
        incapacidad_id: UUID,
        aval: Literal["SI", "NO"],
        motivo: str | None,
        usuario_id: UUID,
    ) -> IncapacidadPrevisional:
        """
        Decisión humana de aval (regla AC de `auditoria_rules.py`: "jamás
        se autocalcula"). Valida ANTES de tocar la BD — ni siquiera un
        `get_by_id` corre si la validación falla, así que `aval='NO'` sin
        `motivo` no dispara ninguna consulta, mucho menos una escritura.
        """
        if aval not in (AvalPrevisional.SI, AvalPrevisional.NO):
            raise BadRequestException("aval debe ser 'SI' o 'NO'")
        if aval == AvalPrevisional.NO and not motivo:
            raise BadRequestException(
                "motivo_no_aval es obligatorio cuando aval='NO' -- un 'NO' "
                "siempre necesita una razón declarada"
            )

        inc = await incapacidad_previsional_repository.get_by_id(db, incapacidad_id)
        if inc is None:
            raise NotFoundException(f"IncapacidadPrevisional {incapacidad_id} no encontrada")

        inc.aval = aval
        # Judgment call: si el aval pasa a 'SI', se limpia cualquier
        # motivo_no_aval previo -- un motivo de rechazo obsoleto no debe
        # sobrevivir a un cambio de decisión del auditor.
        inc.motivo_no_aval = motivo if aval == AvalPrevisional.NO else None
        inc.usuario_auditoria_id = usuario_id
        inc.fecha_auditoria = datetime.now(timezone.utc)
        # Judgment call: el modelo define los estados AVALADO/NO_AVALADO
        # explícitamente para este resultado (ver CheckConstraint del
        # modelo y EstadoIncapacidadPrevisional en app/utils/enums.py) --
        # transicionar aquí es la lectura más directa del nombre de esos
        # dos estados, aunque la firma pactada en el brief no lo pide
        # explícitamente. Si una tarea futura de flujo de estados necesita
        # una máquina de estados más elaborada (p.ej. validar transición
        # solo desde CON_SINIESTRO/EN_AUDITORIA), este es el punto a
        # ajustar.
        inc.estado = (
            EstadoIncapacidadPrevisional.AVALADO
            if aval == AvalPrevisional.SI
            else EstadoIncapacidadPrevisional.NO_AVALADO
        ).value

        db.add(inc)
        await db.flush()
        await db.commit()
        await db.refresh(inc)
        return inc

    async def duplicar(
        self,
        db: AsyncSession,
        incapacidad_id: UUID,
        fechas: dict,
        usuario_id: UUID,
    ) -> IncapacidadPrevisional:
        """
        Crea un nuevo `IncapacidadPrevisional` con `es_duplicado_interno=
        True` apuntando a `incapacidad_id` como `incapacidad_origen_id`,
        con las fechas propias que el auditor especifica — la AFP reportó
        varias incapacidades reales en una sola fila del excel, y el
        auditor las separa manualmente (nunca se infiere silenciosamente,
        mismo principio que el resto del motor). El registro duplicado
        queda excluido de cualquier futura exportación de respuesta al
        fondo vía ese mismo flag (consumidor de `es_duplicado_interno` es
        una tarea posterior, no esta).

        `fechas` requiere `fecha_inicial`/`fecha_final` (`BadRequestException`
        si falta cualquiera de las dos); cualquier otra clave se ignora.

        Ver `_CAMPOS_COPIABLES_EN_DUPLICADO` para la lista exacta de campos
        que se copian del origen (documentado ahí el porqué de cada
        exclusión). `metadata_` se copia por separado, mezclada con una
        marca de quién duplicó (`usuario_id`) -- el modelo no tiene una
        columna dedicada "duplicado_por", así que se usa el mismo JSONB
        heredado de `BaseModel` que `lote_service._construir_metadata` ya
        usa para campos sin columna propia.
        """
        origen = await incapacidad_previsional_repository.get_by_id(db, incapacidad_id)
        if origen is None:
            raise NotFoundException(f"IncapacidadPrevisional {incapacidad_id} no encontrada")

        fecha_inicial = fechas.get("fecha_inicial")
        fecha_final = fechas.get("fecha_final")
        if fecha_inicial is None or fecha_final is None:
            raise BadRequestException(
                "fecha_inicial y fecha_final son obligatorias para duplicar una incapacidad"
            )

        campos: dict[str, Any] = {
            nombre: getattr(origen, nombre) for nombre in _CAMPOS_COPIABLES_EN_DUPLICADO
        }
        campos["fecha_inicial"] = fecha_inicial
        campos["fecha_final"] = fecha_final
        campos["es_duplicado_interno"] = True
        campos["incapacidad_origen_id"] = origen.id

        metadata_nueva = dict(origen.metadata_) if origen.metadata_ else {}
        metadata_nueva["duplicado_por_usuario_id"] = str(usuario_id)
        metadata_nueva["duplicado_de_incapacidad_id"] = str(origen.id)
        campos["metadata_"] = metadata_nueva

        nueva = await incapacidad_previsional_repository.create_flushed(db, campos)
        await db.commit()
        return nueva


auditoria_previsional_service = AuditoriaPrevisionalService()

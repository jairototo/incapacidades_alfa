"""
Servicio de persistencia de liquidación previsional (Task 3.4, primera
mitad).

Archivo separado de `auditoria_service.py` a propósito (esa opción estaba
explícitamente abierta en el brief): ese módulo orquesta las 19 señales
AB-AT (evaluación de reglas + su persistencia); este módulo orquesta un
concern totalmente distinto — recalcular el VALOR monetario liquidado
(`valor_auditado`/`diferencia_valor_afp` de la incapacidad,
`valor_segmento`/`smlmv_aplicado`/`base_diaria` de cada periodo) — y no
comparte estado ni tipos con el motor de reglas. Mantenerlos separados evita
que `auditoria_service.py` (ya ~550 líneas) crezca con un segundo concern,
y dado que Task 4.x probablemente expone un endpoint de liquidación aparte
del de auditoría, un servicio propio mapea 1:1 con esa futura ruta.

-----------------------------------------------------------------------
DECISIÓN DE ALCANCE DELIBERADA (leer antes de tocar este archivo)
-----------------------------------------------------------------------
El spec (`docs/especificaciones/modulo_previsionales.md`, §4, "Pendientes
que siguen abiertos") deja abierta la pregunta: "¿se debe automatizar
`max(día_181, fecha_CRIE)` como límite [de la ventana de pago], o se deja
siempre a criterio del auditor humano?". `auditoria_rules.py` (Task 1.4)
deliberadamente NO codificó esa regla (la AL de ese motor solo COMPARA
día 181 AFP vs ARPIS, no recorta ninguna ventana).

Este módulo NO resuelve esa pregunta tampoco. "Liquidar" aquí se define
como: recalcular `valor_auditado`/`diferencia_valor_afp` y el detalle por
periodo usando los SEGMENTOS YA PERSISTIDOS por `lote_service.cargar_lote`
(Task 3.1) — el rango de fechas completo tal como lo reportó la AFP, sin
recortar por `dia_181_alfa`/`fecha_crie_alfa` — y los valores de
`SmlmvParametros` VIGENTES en el momento de la llamada (pueden haber
cambiado desde la carga si alguien corrigió la tabla). Esto hace que
`liquidar_incapacidad`/`liquidar_lote` sean idempotentes y útiles para
re-disparar la liquidación tras una corrección de datos (p.ej. un SMLMV mal
sembrado), sin inventar silenciosamente la regla de ventana pendiente. Si
una tarea futura resuelve esa pregunta de negocio, el recorte de ventana
debe agregarse aquí explícitamente (probablemente filtrando/acortando los
`Segmento` reconstruidos antes de llamar a `calcular_valor`) — no antes.

Reutiliza el mismo patrón "caller-managed transaction" que
`lote_service.py`/`auditoria_service.py`: `flush()`s internos, un solo
`commit()` en cada punto de entrada público.
"""
from decimal import Decimal
from uuid import UUID

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, NotFoundException
from app.db.repositories.previsionales import (
    incapacidad_previsional_repository,
    periodo_previsional_repository,
)
from app.db.repositories.smlmv_parametros_repository import smlmv_parametros_repository
from app.models.previsionales.incapacidad_previsional import IncapacidadPrevisional
from app.models.previsionales.periodo_previsional import PeriodoPrevisional
from app.services.previsionales.liquidacion_previsional import calcular_valor
from app.services.previsionales.segmentacion import Segmento

_TREINTA = Decimal(30)


class LiquidacionPrevisionalService:
    """Orquesta el recálculo/persistencia de la liquidación previsional."""

    async def _liquidar_incapacidad_obj(
        self,
        db: AsyncSession,
        inc: IncapacidadPrevisional,
        periodos: list[PeriodoPrevisional],
        smlmv_cache: dict[int, Decimal],
    ) -> IncapacidadPrevisional:
        """
        Núcleo compartido por `liquidar_incapacidad`/`liquidar_lote`:
        recalcula y persiste `valor_segmento`/`smlmv_aplicado`/`base_diaria`
        por periodo y `valor_auditado`/`diferencia_valor_afp` en `inc`.

        `smlmv_cache` se pasa por referencia y se comparte entre llamadas
        sucesivas dentro de un mismo `liquidar_lote` — mismo patrón que
        `lote_service.cargar_lote` usa para no repetir una query de SMLMV
        por cada incapacidad que caiga en un año ya resuelto.

        No hace `flush`/`commit` de `inc` fuera de lo necesario para que
        `update_flushed` (periodos) vea las filas — el `commit()` final es
        responsabilidad del llamador público.

        Raises:
            ValueError: si falta el SMLMV configurado para algún año de los
                periodos, o si algún periodo no tiene IBC persistido (no se
                puede liquidar sin la base de cálculo). El llamador decide
                si eso aborta una sola incapacidad (`liquidar_incapacidad`)
                o se salta esa fila sin abortar el lote (`liquidar_lote`,
                mismo espíritu tolerante-por-fila que `lote_service`).
        """
        anos = {p.fecha_inicio.year for p in periodos}
        for ano in anos:
            if ano not in smlmv_cache:
                params = await smlmv_parametros_repository.get_by_ano(db, ano)
                if params is None:
                    raise ValueError(f"SMLMV no configurado para el año {ano}")
                smlmv_cache[ano] = params.valor

        periodos_sin_ibc = [p.orden for p in periodos if p.ibc is None]
        if periodos_sin_ibc:
            raise ValueError(
                f"Periodo(s) sin IBC persistido (orden {periodos_sin_ibc}) -- "
                "no se puede liquidar sin la base de cálculo"
            )

        pares = [
            (Segmento(orden=p.orden, fecha_inicio=p.fecha_inicio, fecha_fin=p.fecha_fin, dias=p.dias), p.ibc)
            for p in periodos
        ]
        valor_total, detalle = calcular_valor(pares, smlmv_cache)

        for periodo, det in zip(periodos, detalle):
            await periodo_previsional_repository.update_flushed(
                db,
                periodo.id,
                {
                    "smlmv_aplicado": det.smlmv_aplicado,
                    "base_diaria": det.base_mensual / _TREINTA,
                    "valor_segmento": det.valor_segmento,
                },
            )

        inc.valor_auditado = valor_total
        inc.diferencia_valor_afp = valor_total - inc.valor_afp if inc.valor_afp is not None else None
        db.add(inc)
        await db.flush()
        return inc

    async def liquidar_incapacidad(self, db: AsyncSession, incapacidad_id: UUID) -> IncapacidadPrevisional:
        """Recalcula valor_auditado/diferencia_valor_afp usando los periodos ya persistidos
        (segmentos completos reportados por la AFP) y los valores SMLMV vigentes. Idempotente
        y re-ejecutable. NO recorta la ventana por dia_181_alfa/fecha_crie_alfa — ver nota
        de alcance arriba, es una decisión de negocio pendiente.

        Raises:
            NotFoundException: la incapacidad no existe.
            BadRequestException: no tiene periodos persistidos, falta SMLMV
                para algún año de sus periodos, o algún periodo no tiene IBC.
        """
        inc = await incapacidad_previsional_repository.get_by_id(db, incapacidad_id)
        if inc is None:
            raise NotFoundException(f"IncapacidadPrevisional {incapacidad_id} no encontrada")

        periodos = await periodo_previsional_repository.get_by_incapacidad(db, incapacidad_id)
        if not periodos:
            raise BadRequestException(
                f"IncapacidadPrevisional {incapacidad_id} no tiene periodos persistidos -- "
                "nada que liquidar (¿el lote se cargó correctamente?)"
            )

        try:
            resultado = await self._liquidar_incapacidad_obj(db, inc, periodos, smlmv_cache={})
        except ValueError as exc:
            raise BadRequestException(str(exc)) from exc

        await db.commit()
        await db.refresh(resultado)
        return resultado

    async def liquidar_lote(self, db: AsyncSession, lote_id: UUID) -> int:
        """
        Re-liquida todas las incapacidades NO duplicadas internamente de un
        lote (mismo filtro `{"repetidas": False}` que ya usa
        `IncapacidadPrevisionalRepository.get_by_lote` -- un duplicado
        interno no tiene su propia liquidación, hereda el destino que un
        auditor humano decida para el grupo).

        N+1-safe: UNA query para las incapacidades del lote, UNA query
        batch para TODOS sus periodos (`get_by_incapacidades`), y el SMLMV
        se cachea por año una sola vez para todo el lote (no por
        incapacidad) -- mismo patrón que `lote_service.cargar_lote`.

        Tolerante por fila (mismo espíritu que `lote_service.cargar_lote`):
        una incapacidad sin periodos, sin SMLMV configurado para su año, o
        con algún periodo sin IBC, se omite (se loguea) sin abortar el
        resto del lote.

        Returns:
            Número de incapacidades efectivamente liquidadas (excluye
            duplicados internos y filas omitidas por error).
        """
        incapacidades = await incapacidad_previsional_repository.get_by_lote(
            db, lote_id, {"repetidas": False}
        )
        if not incapacidades:
            return 0

        periodos_por_incapacidad = await periodo_previsional_repository.get_by_incapacidades(
            db, [inc.id for inc in incapacidades]
        )

        smlmv_cache: dict[int, Decimal] = {}
        liquidadas = 0
        for inc in incapacidades:
            periodos = periodos_por_incapacidad.get(inc.id, [])
            if not periodos:
                logger.warning(
                    f"IncapacidadPrevisional {inc.id} sin periodos persistidos -- "
                    "omitida de la liquidación del lote"
                )
                continue
            try:
                await self._liquidar_incapacidad_obj(db, inc, periodos, smlmv_cache)
            except ValueError as exc:
                logger.warning(
                    f"No se pudo liquidar la incapacidad {inc.id}: {exc} -- "
                    "omitida, el lote continúa con las demás"
                )
                continue
            liquidadas += 1

        await db.commit()
        return liquidadas


liquidacion_previsional_service = LiquidacionPrevisionalService()

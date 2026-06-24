"""
Servicio de Liquidación de Incapacidades.

Gestiona la creación, actualización y consulta de la liquidación económica
de una incapacidad aprobada (LIQUIDACION o LIQUIDACION_PARCIAL).

IBL note: El IBL viene de Imaginex (sistema externo). Hasta que esté
disponible la especificación de integración, el IBL es un valor
ingresado manualmente. El endpoint POST calcular-ibl es un stub.

Fórmulas: Los porcentajes de desglose están en _PORCENTAJES_PLACEHOLDER.
TODO(C1): Confirmar todos los porcentajes con Helen antes de habilitar
el cálculo automático.
"""
from __future__ import annotations

import logging
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, InvalidStateException, NotFoundException
from app.db.repositories.ibl_parametros_repository import ibl_parametros_repository
from app.db.repositories.liquidacion_repository import liquidacion_repository
from app.db.repositories.incapacidad_repository import incapacidad_repository
from app.models.incapacidad import Incapacidad
from app.models.liquidacion import Liquidacion
from app.schemas.liquidacion import LiquidacionGuardar
from app.services.historial_estado_service import historial_estado_service
from app.utils.enums import EstadoIncapacidad

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# TODO(C1): Confirm all percentages with Helen before enabling formula
# ---------------------------------------------------------------------------
_PORCENTAJES_PLACEHOLDER: dict = {
    "incapacidad_temporal_pct": None,        # e.g. 1.0 (100% IBC) — pending
    "aporte_patronal_pension_pct": None,     # pending
    "aporte_trabajador_pension_pct": None,   # pending
    "aporte_adicional_trabajador_pension_pct": None,  # pending
    "aporte_patronal_salud_pct": None,       # pending
    "aporte_trabajador_salud_pct": None,     # pending
}


def _calcular_breakdown(ibl: Decimal, dias: int) -> dict:
    """
    Placeholder formula. All values return None until C1 confirmed.

    When percentages are confirmed, replace None values in
    _PORCENTAJES_PLACEHOLDER and uncomment the calculation lines below.

    Args:
        ibl: Ingreso Base de Liquidación
        dias: Días autorizados

    Returns:
        Dict with breakdown values (all None until C1 confirmed)
    """
    if any(v is None for v in _PORCENTAJES_PLACEHOLDER.values()):
        return {k.replace("_pct", ""): None for k in _PORCENTAJES_PLACEHOLDER}

    # When percentages are confirmed, uncomment:
    # d = Decimal(str(dias))
    # valor_it = ibl * d * Decimal(str(_PORCENTAJES_PLACEHOLDER["incapacidad_temporal_pct"]))
    # aporte_patronal_pension = ibl * d * (Decimal(str(_PORCENTAJES_PLACEHOLDER["aporte_patronal_pension_pct"])) / 100)
    # aporte_trabajador_pension = ibl * d * (Decimal(str(_PORCENTAJES_PLACEHOLDER["aporte_trabajador_pension_pct"])) / 100)
    # aporte_adicional_trabajador_pension = ibl * d * (Decimal(str(_PORCENTAJES_PLACEHOLDER["aporte_adicional_trabajador_pension_pct"])) / 100)
    # aporte_patronal_salud = ibl * d * (Decimal(str(_PORCENTAJES_PLACEHOLDER["aporte_patronal_salud_pct"])) / 100)
    # aporte_trabajador_salud = ibl * d * (Decimal(str(_PORCENTAJES_PLACEHOLDER["aporte_trabajador_salud_pct"])) / 100)
    # valor_total = valor_it + aporte_patronal_pension + aporte_trabajador_pension + aporte_adicional_trabajador_pension + aporte_patronal_salud + aporte_trabajador_salud
    # return {
    #     "incapacidad_temporal": valor_it,
    #     "aporte_patronal_pension": aporte_patronal_pension,
    #     "aporte_trabajador_pension": aporte_trabajador_pension,
    #     "aporte_adicional_trabajador_pension": aporte_adicional_trabajador_pension,
    #     "aporte_patronal_salud": aporte_patronal_salud,
    #     "aporte_trabajador_salud": aporte_trabajador_salud,
    #     "valor_total": valor_total,
    # }
    return {}


class LiquidacionService:
    """Servicio de liquidación de incapacidades."""

    # ------------------------------------------------------------------
    # Recuperar
    # ------------------------------------------------------------------

    async def get_liquidacion(
        self,
        db: AsyncSession,
        incapacidad_id: UUID,
    ) -> Liquidacion:
        """
        Obtener la liquidación de una incapacidad.

        Raises:
            NotFoundException: si no existe liquidación para esta incapacidad
        """
        liquidacion = await liquidacion_repository.get_by_incapacidad(db, incapacidad_id)
        if liquidacion is None:
            raise NotFoundException(
                f"No se encontró liquidación para la incapacidad {incapacidad_id}"
            )
        return liquidacion

    # ------------------------------------------------------------------
    # Guardar (crear o actualizar)
    # ------------------------------------------------------------------

    async def guardar_liquidacion(
        self,
        db: AsyncSession,
        incapacidad_id: UUID,
        data: LiquidacionGuardar,
        liquidador_id: UUID,
    ) -> Liquidacion:
        """
        Crea o actualiza la liquidación de una incapacidad.

        Si ya existe una liquidación para la incapacidad, la actualiza.
        Después de guardar transiciona la incapacidad al estado correcto
        (LIQUIDACION o LIQUIDACION_PARCIAL) según su estado actual.

        Args:
            db: Sesión de base de datos
            incapacidad_id: ID de la incapacidad
            data: Datos de la liquidación
            liquidador_id: ID del usuario que liquida

        Returns:
            Liquidacion guardada

        Raises:
            NotFoundException: si la incapacidad no existe
            InvalidStateException: si la incapacidad no está en LIQUIDACION o LIQUIDACION_PARCIAL
        """
        from app.services.incapacidad_service import incapacidad_service

        incapacidad = await incapacidad_service.get_incapacidad(db, incapacidad_id)

        if incapacidad.estado not in (
            EstadoIncapacidad.LIQUIDACION,
            EstadoIncapacidad.LIQUIDACION_PARCIAL,
        ):
            raise InvalidStateException(
                "Solo se puede liquidar una incapacidad en estado LIQUIDACION o LIQUIDACION_PARCIAL"
            )

        liquidacion = await liquidacion_repository.get_by_incapacidad(db, incapacidad_id)

        obj_data = {
            "incapacidad_id": incapacidad_id,
            "liquidador_id": liquidador_id,
            "dias_autorizados": data.dias_autorizados,
            "fecha_inicio_autorizada": data.fecha_inicio_autorizada,
            "fecha_fin_autorizada": data.fecha_fin_autorizada,
            "ibl": data.ibl,
            "periodo_ibl_inicio": data.periodo_ibl_inicio,
            "periodo_ibl_fin": data.periodo_ibl_fin,
            "valor_incapacidad_temporal": data.valor_incapacidad_temporal,
            "valor_aporte_patronal_pension": data.valor_aporte_patronal_pension,
            "valor_aporte_trabajador_pension": data.valor_aporte_trabajador_pension,
            "valor_aporte_adicional_trabajador_pension": data.valor_aporte_adicional_trabajador_pension,
            "valor_aporte_patronal_salud": data.valor_aporte_patronal_salud,
            "valor_aporte_trabajador_salud": data.valor_aporte_trabajador_salud,
            "valor_total": data.valor_total,
            "metodo_pago": data.metodo_pago,
            "notas_liquidador": data.notas_liquidador,
        }

        if liquidacion is None:
            liquidacion = await liquidacion_repository.create_flushed(db, obj_data)
        else:
            await liquidacion_repository.update(db, id=liquidacion.id, obj_in=obj_data)
            await db.flush()
            liquidacion = await liquidacion_repository.get_by_incapacidad(db, incapacidad_id)

        await db.commit()
        logger.info(
            "Liquidación guardada para incapacidad %s por liquidador %s",
            incapacidad_id,
            liquidador_id,
        )
        return liquidacion

    # ------------------------------------------------------------------
    # Stub cálculo IBL
    # ------------------------------------------------------------------

    async def calcular_ibl_stub(
        self,
        db: AsyncSession,
        incapacidad_id: UUID,
    ) -> dict:
        """
        Stub para calcular el IBL desde Imaginex.

        La integración real con Imaginex está pendiente de especificación.
        Por ahora retorna ibl=None con una nota informativa.

        Args:
            db: Sesión de base de datos (para validar que la incapacidad exista)
            incapacidad_id: ID de la incapacidad

        Returns:
            dict con ibl=None y nota informativa
        """
        from app.services.incapacidad_service import incapacidad_service

        # Validar que la incapacidad existe
        await incapacidad_service.get_incapacidad(db, incapacidad_id)

        logger.info(
            "IBL stub llamado para incapacidad %s — integración Imaginex pendiente",
            incapacidad_id,
        )
        return {
            "ibl": None,
            "nota": "Integración con Imaginex pendiente de especificación",
        }

    # ------------------------------------------------------------------
    # Calcular breakdown (GET — sin efecto en DB)
    # ------------------------------------------------------------------

    async def calcular_breakdown(
        self,
        db: AsyncSession,
        incapacidad_id: UUID,
        ibl: Optional[Decimal],
        dias: int,
    ) -> dict:
        """
        Calcula el desglose de la liquidación sin guardar en DB.

        Los valores retornan None hasta confirmar porcentajes con Helen (C1).
        Cuando ibl es None, también retorna None en todos los campos del desglose.

        Args:
            db: Sesión de base de datos (para validar que la incapacidad exista)
            incapacidad_id: ID de la incapacidad
            ibl: Ingreso Base de Liquidación (puede ser None)
            dias: Días autorizados

        Returns:
            Dict con el desglose calculado
        """
        from app.services.incapacidad_service import incapacidad_service

        await incapacidad_service.get_incapacidad(db, incapacidad_id)

        if ibl is None:
            return {
                "ibl": None,
                "dias": dias,
                "incapacidad_temporal": None,
                "aporte_patronal_pension": None,
                "aporte_trabajador_pension": None,
                "aporte_adicional_trabajador_pension": None,
                "aporte_patronal_salud": None,
                "aporte_trabajador_salud": None,
                "valor_total": None,
                "nota": "IBL no disponible — ingrese el IBL para calcular el desglose",
            }

        breakdown = _calcular_breakdown(ibl, dias)
        return {
            "ibl": ibl,
            "dias": dias,
            **breakdown,
            "valor_total": None,  # Siempre None hasta C1
            "nota": "Porcentajes pendientes de confirmación (C1 — Helen)",
        }

    # ------------------------------------------------------------------
    # Devolver a EN_AUDITORIA
    # ------------------------------------------------------------------

    async def devolver_a_auditoria(
        self,
        db: AsyncSession,
        incapacidad_id: UUID,
        observacion: str,
        liquidador_id: UUID,
    ) -> Incapacidad:
        """
        Devuelve una incapacidad desde LIQUIDACION/LIQUIDACION_PARCIAL a EN_AUDITORIA.

        Args:
            db: Sesión de base de datos
            incapacidad_id: ID de la incapacidad
            observacion: Observación obligatoria del liquidador
            liquidador_id: ID del usuario que realiza la devolución

        Returns:
            Incapacidad en estado EN_AUDITORIA

        Raises:
            BadRequestException: si la observación está vacía
            InvalidStateException: si la incapacidad no está en LIQUIDACION o LIQUIDACION_PARCIAL
        """
        from app.services.incapacidad_service import incapacidad_service

        if not observacion or not observacion.strip():
            raise BadRequestException("La observación es obligatoria para la devolución")

        incapacidad = await incapacidad_service.get_incapacidad(db, incapacidad_id)

        if incapacidad.estado not in (
            EstadoIncapacidad.LIQUIDACION,
            EstadoIncapacidad.LIQUIDACION_PARCIAL,
        ):
            raise InvalidStateException(
                "Solo se puede devolver desde LIQUIDACION o LIQUIDACION_PARCIAL"
            )

        await incapacidad_service._validate_state_transition(
            incapacidad.estado, EstadoIncapacidad.EN_AUDITORIA
        )

        await incapacidad_repository.update(
            db,
            id=incapacidad_id,
            obj_in={"estado": EstadoIncapacidad.EN_AUDITORIA},
        )

        await historial_estado_service.create_historial_entry(
            db=db,
            entity_type="incapacidad",
            entity_id=incapacidad_id,
            estado_anterior=incapacidad.estado.value,
            estado_nuevo=EstadoIncapacidad.EN_AUDITORIA.value,
            observacion=f"Devolución por liquidador: {observacion}",
            cambiado_por_id=liquidador_id,
            flush_only=True,
        )

        await db.commit()

        return await incapacidad_service.get_incapacidad(db, incapacidad_id)

    # ------------------------------------------------------------------
    # Completar (LIQUIDACION/LIQUIDACION_PARCIAL → PAGADA/PAGADA_PARCIAL)
    # ------------------------------------------------------------------

    async def completar_liquidacion(
        self,
        db: AsyncSession,
        incapacidad_id: UUID,
        liquidador_id: UUID,
    ) -> Incapacidad:
        """
        Completa la liquidación y transiciona la incapacidad a PAGADA o PAGADA_PARCIAL.

        LIQUIDACION → PAGADA
        LIQUIDACION_PARCIAL → PAGADA_PARCIAL

        Args:
            db: Sesión de base de datos
            incapacidad_id: ID de la incapacidad
            liquidador_id: ID del usuario que completa

        Returns:
            Incapacidad en estado PAGADA o PAGADA_PARCIAL

        Raises:
            NotFoundException: si no existe liquidación para esta incapacidad
            InvalidStateException: si la incapacidad no está en LIQUIDACION o LIQUIDACION_PARCIAL
        """
        from app.services.incapacidad_service import incapacidad_service

        incapacidad = await incapacidad_service.get_incapacidad(db, incapacidad_id)

        if incapacidad.estado not in (
            EstadoIncapacidad.LIQUIDACION,
            EstadoIncapacidad.LIQUIDACION_PARCIAL,
        ):
            raise InvalidStateException(
                "Solo se puede completar una liquidación en estado LIQUIDACION o LIQUIDACION_PARCIAL"
            )

        # Validar que existe una liquidación guardada
        liq = await liquidacion_repository.get_by_incapacidad(db, incapacidad_id)
        if liq is None:
            raise NotFoundException(
                "Debe guardar la liquidación antes de completarla"
            )

        nuevo_estado = (
            EstadoIncapacidad.PAGADA
            if incapacidad.estado == EstadoIncapacidad.LIQUIDACION
            else EstadoIncapacidad.PAGADA_PARCIAL
        )

        await incapacidad_repository.update(
            db,
            id=incapacidad_id,
            obj_in={"estado": nuevo_estado},
        )

        await historial_estado_service.create_historial_entry(
            db=db,
            entity_type="incapacidad",
            entity_id=incapacidad_id,
            estado_anterior=incapacidad.estado.value,
            estado_nuevo=nuevo_estado.value,
            observacion="Liquidación completada",
            cambiado_por_id=liquidador_id,
            flush_only=True,
        )

        await db.commit()

        return await incapacidad_service.get_incapacidad(db, incapacidad_id)


# Instancia global del servicio
liquidacion_service = LiquidacionService()

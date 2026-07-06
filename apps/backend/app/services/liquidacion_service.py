"""
Servicio de Liquidación de Incapacidades.

Gestiona la creación, actualización y consulta de la liquidación económica
de una incapacidad aprobada (LIQUIDACION o LIQUIDACION_PARCIAL).

IBL note: El IBL viene de Imaginex (sistema externo). Hasta que esté
disponible la especificación de integración, el IBL es un valor
ingresado manualmente. El endpoint POST calcular-ibl es un stub.

Fórmulas (C1 resuelto): Los porcentajes se leen de la tabla ibl_parametros
para el año de la fecha de inicio autorizada.
    valor = ibl * dias * (porcentaje / 100)  — redondeado a 2 decimales ROUND_HALF_UP
    incapacidad_temporal = ibl * dias  (100% IBC, RN-010)
    aporte_adicional_trabajador_pension: pendiente de revisión legal (siempre None)
"""
from __future__ import annotations

import logging
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, InvalidStateException, NotFoundException
from app.db.repositories.ibl_parametros_repository import ibl_parametros_repository
from app.db.repositories.liquidacion_repository import liquidacion_repository
from app.models.ibl_parametros import IblParametros
from app.models.incapacidad import Incapacidad
from app.models.liquidacion import Liquidacion
from app.schemas.liquidacion import LiquidacionGuardar
from app.utils.enums import EstadoIncapacidad

logger = logging.getLogger(__name__)

_QUANT = Decimal("0.01")


# ---------------------------------------------------------------------------
# Internal helpers — IBL breakdown calculation
# ---------------------------------------------------------------------------

async def _get_parametros(db: AsyncSession, ano: int) -> IblParametros:
    """
    Obtiene los parámetros IBL para el año dado.

    Raises:
        BadRequestException: si no existe fila en ibl_parametros para ese año
    """
    params = await ibl_parametros_repository.get_by_ano(db, ano)
    if not params:
        raise BadRequestException(
            f"No hay parámetros IBL configurados para el año {ano}"
        )
    return params


async def _calcular_breakdown_real(
    db: AsyncSession,
    ibl: Decimal,
    dias: int,
    ano: int,
) -> dict:
    """
    Calcula el desglose de liquidación usando los parámetros IBL del año dado.

    Fórmula: valor = ibl * dias * (porcentaje / 100), redondeado a 2 decimales.
    incapacidad_temporal = ibl * dias (100% IBC, RN-010).
    aporte_adicional_trabajador_pension siempre None (fórmula pendiente de revisión legal).

    Raises:
        BadRequestException: si no hay parámetros para el año dado
    """
    params = await _get_parametros(db, ano)
    d = Decimal(dias)

    def calc(pct: Decimal) -> Decimal:
        return (ibl * d * pct / Decimal("100")).quantize(_QUANT, rounding=ROUND_HALF_UP)

    valor_incapacidad_temporal = (ibl * d).quantize(_QUANT, rounding=ROUND_HALF_UP)
    valor_patronal_pension = calc(params.aporte_patronal_pension)
    valor_trabajador_pension = calc(params.aporte_trabajador_pension)
    valor_patronal_salud = calc(params.aporte_patronal_salud)
    valor_trabajador_salud = calc(params.aporte_trabajador_salud)

    valor_total = (
        valor_incapacidad_temporal
        + valor_patronal_pension
        + valor_trabajador_pension
        + valor_patronal_salud
        + valor_trabajador_salud
    ).quantize(_QUANT, rounding=ROUND_HALF_UP)

    return {
        "incapacidad_temporal": valor_incapacidad_temporal,
        "aporte_patronal_pension": valor_patronal_pension,
        "aporte_trabajador_pension": valor_trabajador_pension,
        "aporte_adicional_trabajador_pension": None,  # fórmula TBD, revisión legal pendiente
        "aporte_patronal_salud": valor_patronal_salud,
        "aporte_trabajador_salud": valor_trabajador_salud,
        "valor_total": valor_total,
    }


# ---------------------------------------------------------------------------
# Service class
# ---------------------------------------------------------------------------

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

        Si el IBL está disponible, calcula el desglose y lo persiste en las
        columnas valor_* de la tabla liquidacion. Si no hay parámetros IBL
        para el año en curso, los valores de desglose quedan en None.

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

        # Compute breakdown if IBL is provided; graceful fallback if no params for the year
        breakdown_valores: dict = {}
        if data.ibl is not None:
            try:
                ano = data.fecha_inicio_autorizada.year
                bd = await _calcular_breakdown_real(db, data.ibl, data.dias_autorizados, ano)
                breakdown_valores = {
                    "valor_incapacidad_temporal": bd["incapacidad_temporal"],
                    "valor_aporte_patronal_pension": bd["aporte_patronal_pension"],
                    "valor_aporte_trabajador_pension": bd["aporte_trabajador_pension"],
                    "valor_aporte_adicional_trabajador_pension": bd["aporte_adicional_trabajador_pension"],
                    "valor_aporte_patronal_salud": bd["aporte_patronal_salud"],
                    "valor_aporte_trabajador_salud": bd["aporte_trabajador_salud"],
                    "valor_total": bd["valor_total"],
                }
            except BadRequestException:
                logger.warning(
                    "No hay parámetros IBL para el año %s — desglose no calculado para incapacidad %s",
                    data.fecha_inicio_autorizada.year,
                    incapacidad_id,
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
            # Use computed breakdown values; fall back to what the caller sent if no params
            "valor_incapacidad_temporal": breakdown_valores.get(
                "valor_incapacidad_temporal", data.valor_incapacidad_temporal
            ),
            "valor_aporte_patronal_pension": breakdown_valores.get(
                "valor_aporte_patronal_pension", data.valor_aporte_patronal_pension
            ),
            "valor_aporte_trabajador_pension": breakdown_valores.get(
                "valor_aporte_trabajador_pension", data.valor_aporte_trabajador_pension
            ),
            "valor_aporte_adicional_trabajador_pension": breakdown_valores.get(
                "valor_aporte_adicional_trabajador_pension",
                data.valor_aporte_adicional_trabajador_pension,
            ),
            "valor_aporte_patronal_salud": breakdown_valores.get(
                "valor_aporte_patronal_salud", data.valor_aporte_patronal_salud
            ),
            "valor_aporte_trabajador_salud": breakdown_valores.get(
                "valor_aporte_trabajador_salud", data.valor_aporte_trabajador_salud
            ),
            "valor_total": breakdown_valores.get("valor_total", data.valor_total),
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

        El año de parámetros se deriva de incapacidad.fecha_inicio.
        Si ibl es None, retorna None en todos los campos de desglose.

        Args:
            db: Sesión de base de datos
            incapacidad_id: ID de la incapacidad
            ibl: Ingreso Base de Liquidación (puede ser None)
            dias: Días autorizados

        Returns:
            Dict con el desglose calculado

        Raises:
            BadRequestException: si ibl no es None y no hay parámetros para el año
        """
        from app.services.incapacidad_service import incapacidad_service

        incapacidad = await incapacidad_service.get_incapacidad(db, incapacidad_id)

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

        ano = incapacidad.fecha_inicio.year
        breakdown = await _calcular_breakdown_real(db, ibl, dias, ano)
        return {
            "ibl": ibl,
            "dias": dias,
            **breakdown,
            "nota": (
                f"Desglose calculado con parámetros IBL {ano}. "
                "Aporte adicional trabajador pensión pendiente de definición legal."
            ),
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

        await incapacidad_service._cambiar_estado(
            db=db,
            incapacidad=incapacidad,
            nuevo_estado=EstadoIncapacidad.EN_AUDITORIA,
            observacion=f"Devolución por liquidador: {observacion}",
            usuario_id=liquidador_id,
        )

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

        await incapacidad_service._cambiar_estado(
            db=db,
            incapacidad=incapacidad,
            nuevo_estado=nuevo_estado,
            observacion="Liquidación completada — transición a PAGADA",
            usuario_id=liquidador_id,
        )

        return await incapacidad_service.get_incapacidad(db, incapacidad_id)


# Instancia global del servicio
liquidacion_service = LiquidacionService()

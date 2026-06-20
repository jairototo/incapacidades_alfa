"""Pipeline compartido de radicación (individual = N=1, masiva = N filas).

Crea Incapacidad directamente (sin pre_incapacidad), resuelve solicitante desde la
empresa, y expone hooks inyectables para auditoría (Phase 4) e integración externa
(Phase 3.6). Sus defaults son no-op para que esta fase sea testeable de forma aislada.
"""
from __future__ import annotations
from datetime import date, datetime
from typing import Callable, Optional, Protocol
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.models.empresa import Empresa
from app.models.empleado import Empleado
from app.models.incapacidad import Incapacidad
from app.schemas.radicacion import RadicacionRowInput, RadicacionResultItem, RadicacionResponse
from app.services.solicitante_resolver import resolve_solicitante_for_empresa
from app.utils.enums import TipoIncapacidad, EstadoIncapacidad


class IntegracionHook(Protocol):
    async def __call__(self, db: AsyncSession, incapacidad: Incapacidad) -> None: ...


async def _noop_integracion(db: AsyncSession, incapacidad: Incapacidad) -> None:
    return None


class RadicacionPipelineService:
    def __init__(
        self,
        db: AsyncSession,
        enqueue_auditoria: Callable[[UUID], None],
        integracion: IntegracionHook = _noop_integracion,
    ):
        self.db = db
        self.enqueue_auditoria = enqueue_auditoria
        self.integracion = integracion

    async def _generar_numero(self, tipo: str) -> str:
        prefix = "ARL" if tipo == "ARL" else "SAL"
        fecha_str = date.today().strftime("%Y%m%d")
        like = f"{prefix}-{fecha_str}-%"
        count = (
            await self.db.execute(select(Incapacidad).where(Incapacidad.numero.like(like)))
        ).scalars().all()
        return f"{prefix}-{fecha_str}-{len(count) + 1:04d}"

    async def radicar(
        self,
        rows: list[RadicacionRowInput],
        empresa: Empresa,
        radicado_por_id: Optional[UUID],
    ) -> RadicacionResponse:
        solicitante = await resolve_solicitante_for_empresa(self.db, empresa)
        items: list[RadicacionResultItem] = []
        created: list[Incapacidad] = []

        for row in rows:
            empleado = (
                await self.db.execute(select(Empleado).where(Empleado.id == row.empleado_id))
            ).scalar_one_or_none()
            if empleado is None:
                items.append(RadicacionResultItem(empleado_id=row.empleado_id, success=False, error="Empleado no encontrado"))
                continue
            if empleado.empresa_id != empresa.id:
                items.append(RadicacionResultItem(empleado_id=row.empleado_id, success=False, error="El empleado no pertenece a su empresa"))
                continue

            numero = await self._generar_numero("ARL")
            inc = Incapacidad(
                numero=numero,
                tipo=TipoIncapacidad.ARL,
                empleado_id=empleado.id,
                empresa_id=empresa.id,
                solicitante_id=solicitante.id,
                fecha_inicio=row.fecha_inicio,
                fecha_fin=row.fecha_fin,
                dias_totales=row.dias_totales,
                diagnostico_cie10=row.diagnostico_cie10,
                descripcion_diagnostico=row.descripcion_diagnostico,
                nombre_medico=row.nombre_medico,
                registro_medico=row.registro_medico,
                ips=row.ips,
                valor_dia=row.valor_dia,
                prorroga=row.prorroga,
                observaciones=row.observaciones,
                subtipo=row.tipo_enfermedad,
                estado=EstadoIncapacidad.RADICADA,
                fecha_radicacion=datetime.utcnow(),
                radicado_por_id=radicado_por_id,
            )
            self.db.add(inc)
            await self.db.flush()

            await self.integracion(self.db, inc)

            created.append(inc)
            items.append(RadicacionResultItem(
                empleado_id=row.empleado_id, incapacidad_id=inc.id, numero=inc.numero, success=True,
            ))

        await self.db.commit()

        for inc in created:
            try:
                self.enqueue_auditoria(inc.id)
            except Exception as exc:
                logger.error(f"No se pudo encolar auditoría para {inc.id}: {exc}")

        logger.info(f"Radicación: {len(created)}/{len(rows)} incapacidades creadas")
        return RadicacionResponse(items=items, total_radicadas=len(created))

"""
Asignación automática de auditor a una incapacidad, según la sucursal del
siniestro activo y el balanceo de carga entre auditores de esa sucursal.

Ver docs/superpowers/specs/2026-07-25-asignacion-auditoria-sucursal-design.md
"""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.incapacidad import Incapacidad
from app.models.siniestro import Siniestro
from app.models.usuario import Usuario
from app.db.repositories.siniestro_repository import siniestro_repository
from app.utils.enums import TipoIncapacidad, RolUsuario, EstadoUsuario, SucursalSiniestro


async def asignar_auditor(db: AsyncSession, incapacidad: Incapacidad) -> Usuario:
    """
    Asigna un auditor a `incapacidad` (ya en estado EN_AUDITORIA) y persiste
    tanto `incapacidad.auditor_asignado_id` como el incremento de carga del
    auditor elegido. No hace commit — el caller controla la transacción.
    """
    siniestro = await _resolver_siniestro(db, incapacidad)

    auditor: Optional[Usuario] = None
    if siniestro is not None and siniestro.sucursal is not None:
        auditor = await _pick_by_sucursal(db, siniestro.sucursal)

    if auditor is None:
        auditor = await _get_auditor_default(db)

    incapacidad.auditor_asignado_id = auditor.id
    auditor.incapacidades_asignadas_activas += 1
    db.add(incapacidad)
    db.add(auditor)
    await db.flush()
    return auditor


async def _resolver_siniestro(db: AsyncSession, incapacidad: Incapacidad) -> Optional[Siniestro]:
    """Usa el siniestro ya vinculado si existe; si no, busca uno activo por fecha."""
    if incapacidad.siniestro_id is not None:
        result = await db.execute(select(Siniestro).where(Siniestro.id == incapacidad.siniestro_id))
        return result.scalars().first()

    if incapacidad.tipo != TipoIncapacidad.ARL or not incapacidad.empleado_id:
        return None

    return await siniestro_repository.get_activo_para_incapacidad(
        db, incapacidad.empleado_id, incapacidad.fecha_inicio
    )


async def _pick_by_sucursal(db: AsyncSession, sucursal: SucursalSiniestro) -> Optional[Usuario]:
    """Auditor ACTIVO de esa sucursal con menor carga activa (empate: id menor)."""
    query = (
        select(Usuario)
        .where(
            Usuario.rol == RolUsuario.AUDITOR,
            Usuario.estado == EstadoUsuario.ACTIVO,
            Usuario.sucursal == sucursal,
        )
        .order_by(Usuario.incapacidades_asignadas_activas.asc(), Usuario.id.asc())
        .limit(1)
    )
    result = await db.execute(query)
    return result.scalars().first()


async def _get_auditor_default(db: AsyncSession) -> Usuario:
    result = await db.execute(select(Usuario).where(Usuario.username == "auditor_default"))
    auditor = result.scalars().first()
    if auditor is None:
        raise RuntimeError(
            "El usuario 'auditor_default' no existe. Ejecuta scripts/seed_auditores.py "
            "antes de procesar auditorías."
        )
    return auditor

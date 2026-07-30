"""
Repositorio para Siniestro Previsional.

Decisión de diseño deliberada heredada de Task 1.4 (motor de auditoría,
`auditoria_rules.py`): puede haber MÚLTIPLES siniestros para la misma
`identificacion`. La regla AM trata eso como ambigüedad que exige selección
manual (`_seleccionar_siniestro`), nunca "el primero" o "el más reciente"
elegido silenciosamente por la capa de datos.

Por eso `get_by_identificacion` SIEMPRE devuelve una lista ordenada —
jamás `.first()` / `.scalar_one_or_none()` — dejando la decisión de cuál
usar (o si hay ambigüedad) a la capa de servicio/reglas de negocio.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.base_repository import BaseRepository
from app.models.previsionales.siniestro_previsional import SiniestroPrevisional


class SiniestroPrevisionalRepository(BaseRepository[SiniestroPrevisional]):
    """Repositorio para operaciones con SiniestroPrevisional."""

    def __init__(self) -> None:
        super().__init__(SiniestroPrevisional)

    async def get_by_identificacion(
        self,
        db: AsyncSession,
        identificacion: str,
    ) -> list[SiniestroPrevisional]:
        """
        Listar TODOS los siniestros de una identificación, ordenados por
        `fecha_siniestro` descendente (más reciente primero; nulos al
        final) y luego por `created_at` descendente como desempate.

        Deliberadamente devuelve una lista, nunca un único valor: si hay
        más de un siniestro para la misma identificación, es la regla de
        negocio (AM, Task 1.4) la que decide qué hacer con la ambigüedad,
        no el repositorio.

        Args:
            db: Sesión de base de datos
            identificacion: Número de documento del afiliado

        Returns:
            Lista ordenada de SiniestroPrevisional (puede tener 0, 1 o N)
        """
        query = (
            select(SiniestroPrevisional)
            .where(SiniestroPrevisional.identificacion == identificacion)
            .order_by(
                SiniestroPrevisional.fecha_siniestro.desc().nullslast(),
                SiniestroPrevisional.created_at.desc(),
            )
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_by_identificaciones(
        self,
        db: AsyncSession,
        identificaciones: list[str],
    ) -> list[SiniestroPrevisional]:
        """
        Carga masiva: obtener TODOS los siniestros de un conjunto de
        identificaciones (p.ej. las de un lote completo) en UNA sola
        consulta, para evitar N+1 al construir el `ContextoAuditoria` de
        un lote (Task 3.3, `construir_contexto`).

        Args:
            db: Sesión de base de datos
            identificaciones: Lista de números de documento

        Returns:
            Lista de SiniestroPrevisional de todas las identificaciones
            pedidas (sin agrupar — el llamador agrupa por identificación
            si lo necesita, igual que con `get_by_identificacion`)
        """
        if not identificaciones:
            return []

        query = (
            select(SiniestroPrevisional)
            .where(SiniestroPrevisional.identificacion.in_(identificaciones))
            .order_by(
                SiniestroPrevisional.identificacion,
                SiniestroPrevisional.fecha_siniestro.desc().nullslast(),
                SiniestroPrevisional.created_at.desc(),
            )
        )
        result = await db.execute(query)
        return list(result.scalars().all())


# Instancia global del repositorio
siniestro_previsional_repository = SiniestroPrevisionalRepository()

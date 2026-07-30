"""
Repositorio para Solicitud Previsional.

Decisión de cardinalidad (no estaba explícita en el brief de Task 2.2):
el modelo `SolicitudPrevisional` (Task 2.1) no tiene ninguna restricción
UNIQUE ni columna "es la más reciente" sobre `identificacion` — es un
histórico de solicitudes ya radicadas en ARPIS/AFP, y nada impide que un
mismo afiliado tenga varias solicitudes históricas. Por eso, siguiendo la
misma filosofía que `SiniestroPrevisionalRepository` (Task 1.4: no colapsar
silenciosamente a un solo valor cuando el modelo no lo garantiza),
`get_by_identificacion` también devuelve una LISTA ordenada, no un único
`Optional[SolicitudPrevisional]`. Se ordena por `fecha_inicial` descendente
(la solicitud vigente más probable primero) con `created_at` como
desempate; la capa de reglas de negocio (Task 3.x) decide cuál usar para
`SolicitudRef` si hay más de una.
"""
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.base_repository import BaseRepository
from app.models.previsionales.solicitud_previsional import SolicitudPrevisional


class SolicitudPrevisionalRepository(BaseRepository[SolicitudPrevisional]):
    """Repositorio para operaciones con SolicitudPrevisional."""

    def __init__(self) -> None:
        super().__init__(SolicitudPrevisional)

    async def get_by_identificacion(
        self,
        db: AsyncSession,
        identificacion: str,
    ) -> list[SolicitudPrevisional]:
        """
        Listar TODAS las solicitudes históricas de una identificación,
        ordenadas por `fecha_inicial` descendente (nulos al final) y
        `created_at` descendente como desempate.

        Ver nota de módulo sobre la decisión de devolver lista en vez de
        un único valor.

        Args:
            db: Sesión de base de datos
            identificacion: Número de documento del afiliado

        Returns:
            Lista ordenada de SolicitudPrevisional (puede tener 0, 1 o N)
        """
        query = (
            select(SolicitudPrevisional)
            .where(SolicitudPrevisional.identificacion == identificacion)
            .order_by(
                SolicitudPrevisional.fecha_inicial.desc().nullslast(),
                SolicitudPrevisional.created_at.desc(),
            )
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_by_identificaciones(
        self,
        db: AsyncSession,
        identificaciones: list[str],
    ) -> list[SolicitudPrevisional]:
        """
        Carga masiva: obtener TODAS las solicitudes de un conjunto de
        identificaciones en UNA sola consulta, para evitar N+1 al construir
        el `ContextoAuditoria` de un lote completo (Task 3.3).

        Args:
            db: Sesión de base de datos
            identificaciones: Lista de números de documento

        Returns:
            Lista de SolicitudPrevisional de todas las identificaciones
            pedidas
        """
        if not identificaciones:
            return []

        query = (
            select(SolicitudPrevisional)
            .where(SolicitudPrevisional.identificacion.in_(identificaciones))
            .order_by(
                SolicitudPrevisional.identificacion,
                SolicitudPrevisional.fecha_inicial.desc().nullslast(),
                SolicitudPrevisional.created_at.desc(),
            )
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    async def bulk_create_flushed(
        self,
        db: AsyncSession,
        solicitudes: list[dict[str, Any]],
    ) -> list[SolicitudPrevisional]:
        """
        Crear en lote solicitudes previsionales (Task 3.2,
        `referencia_adapter.ExcelReferenciaAdapter.importar_solicitudes`),
        usando `db.add_all()` + un único `flush()` — no hace `commit()`,
        mismo patrón que
        `SenalAuditoriaPrevisionalRepository.bulk_create_flushed`. Evita
        N+1 en el lado de ESCRITURA al importar el archivo de referencia
        completo del asegurador en vez de un `create()` por fila.

        Args:
            db: Sesión de base de datos
            solicitudes: Lista de diccionarios con los datos de cada
                solicitud (mismas claves que las columnas del modelo)

        Returns:
            Lista de SolicitudPrevisional creadas (con id asignado)
        """
        if not solicitudes:
            return []

        db_objs = [SolicitudPrevisional(**s) for s in solicitudes]
        db.add_all(db_objs)
        await db.flush()
        return db_objs


# Instancia global del repositorio
solicitud_previsional_repository = SolicitudPrevisionalRepository()

"""
Repositorio para Señal de Auditoría Previsional.

`get_by_incapacidad` lista las señales (una por regla AB-AT evaluada, ver
`auditoria_rules.Senal`) de una incapacidad. `bulk_create_flushed` persiste
de una sola vez el resultado completo de `evaluar_todas()` (Task 1.4) para
una incapacidad — construye todas las instancias del modelo, las agrega con
`db.add_all()` y hace un único `flush()`, siguiendo el patrón
"caller-managed transaction" de `create_flushed`/`update_flushed` en
`base_repository.py` (el `commit()` final queda a cargo del orquestador,
p.ej. Task 3.x, que puede estar persistiendo varias incapacidades del mismo
lote en una sola transacción).
"""
from typing import Any
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.base_repository import BaseRepository
from app.models.previsionales.senal_auditoria_previsional import (
    SenalAuditoriaPrevisional,
)


class SenalAuditoriaPrevisionalRepository(BaseRepository[SenalAuditoriaPrevisional]):
    """Repositorio para operaciones con SenalAuditoriaPrevisional."""

    def __init__(self) -> None:
        super().__init__(SenalAuditoriaPrevisional)

    async def get_by_incapacidad(
        self,
        db: AsyncSession,
        incapacidad_id: UUID,
    ) -> list[SenalAuditoriaPrevisional]:
        """
        Listar todas las señales de auditoría de una incapacidad
        previsional.

        Args:
            db: Sesión de base de datos
            incapacidad_id: UUID de la IncapacidadPrevisional

        Returns:
            Lista de SenalAuditoriaPrevisional de esa incapacidad
        """
        query = select(SenalAuditoriaPrevisional).where(
            SenalAuditoriaPrevisional.incapacidad_previsional_id == incapacidad_id
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    async def delete_by_incapacidad(
        self,
        db: AsyncSession,
        incapacidad_id: UUID,
    ) -> int:
        """
        Borrar todas las señales previas de una incapacidad (Task 3.3,
        `AuditoriaPrevisionalService.auditar_lote`/`auditar_incapacidad`).

        Añadido en Task 3.3 para respaldar la estrategia de re-auditoría
        borra-e-inserta: `evaluar_todas()` siempre corre las 19 reglas
        completas (nunca un subconjunto), así que no hay "señales
        parciales" que preservar entre corridas de auditoría — borrar todo
        lo previo de esa incapacidad y volver a insertar es más simple que
        un upsert campo por campo, y evita arrastrar señales obsoletas de
        una regla que Task 1.4 haya podido cambiar. No hace `commit()`,
        mismo patrón "caller-managed transaction" que el resto del
        repositorio.

        Args:
            db: Sesión de base de datos
            incapacidad_id: UUID de la IncapacidadPrevisional

        Returns:
            Número de señales borradas (0 si no había ninguna, p.ej. la
            primera vez que se audita esa incapacidad)
        """
        stmt = delete(SenalAuditoriaPrevisional).where(
            SenalAuditoriaPrevisional.incapacidad_previsional_id == incapacidad_id
        )
        result = await db.execute(stmt)
        return result.rowcount or 0

    async def bulk_create_flushed(
        self,
        db: AsyncSession,
        senales: list[dict[str, Any]],
    ) -> list[SenalAuditoriaPrevisional]:
        """
        Crear en lote las señales de auditoría de UNA incapacidad
        (típicamente el output completo de `evaluar_todas()` de Task 1.4),
        usando `db.add_all()` + un único `flush()` — no hace `commit()`,
        para que el llamador controle la transacción (igual que
        `create_flushed`/`update_flushed` en `base_repository.py`).

        Args:
            db: Sesión de base de datos
            senales: Lista de diccionarios con los datos de cada señal
                (mismas claves que las columnas del modelo, p.ej. codigo,
                nombre, estado, valor, detalle, incapacidad_previsional_id)

        Returns:
            Lista de SenalAuditoriaPrevisional creadas (con id asignado)

        Nota: no se llama a `db.refresh()` por objeto tras el `flush()`.
        `id` (`default=uuid4`), `created_at` y `updated_at`
        (`default=datetime.utcnow`) son defaults del lado de Python en
        `BaseModel` (`app/models/base.py`), no `server_default` — ya están
        completamente poblados en memoria justo después del `flush()`. Un
        `refresh()` por objeto aquí solo agregaría un SELECT extra por
        señal (N+1) sin sincronizar nada que la base de datos genere del
        lado del servidor.
        """
        if not senales:
            return []

        db_objs = [SenalAuditoriaPrevisional(**s) for s in senales]
        db.add_all(db_objs)
        await db.flush()
        return db_objs


# Instancia global del repositorio
senal_auditoria_previsional_repository = SenalAuditoriaPrevisionalRepository()

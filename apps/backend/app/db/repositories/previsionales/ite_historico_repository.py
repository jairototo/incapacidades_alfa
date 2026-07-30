"""
Repositorio para ITE Histórico.

Respalda la regla AT (doble pago) del motor de auditoría de Task 1.4
(`auditoria_rules.regla_at_doble_pago`, `ContextoAuditoria.ite_por_clave`):
`ALERTA` si `(identificacion, fecha_inicial)` ya existe en el histórico de
pagos de ITE.

`exists_by_identificacion_fecha` es un existence-check puro (no trae filas
completas) para el caso de una sola clave; `get_existentes` es la variante
de carga masiva (Task 3.3, `construir_contexto`) — UNA sola consulta con
`IN` sobre tuplas `(identificacion, fecha_inicial)` en vez de N consultas.
"""
from datetime import date
from typing import Any

from sqlalchemy import exists, select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.base_repository import BaseRepository
from app.models.previsionales.ite_historico import IteHistorico


class IteHistoricoRepository(BaseRepository[IteHistorico]):
    """Repositorio para operaciones con IteHistorico."""

    def __init__(self) -> None:
        super().__init__(IteHistorico)

    async def exists_by_identificacion_fecha(
        self,
        db: AsyncSession,
        identificacion: str,
        fecha_inicial: date,
    ) -> bool:
        """
        Verificar de forma eficiente si ya existe un pago de ITE registrado
        para `(identificacion, fecha_inicial)` — respalda la regla AT
        (doble pago).

        Usa `select(exists().where(...))` en vez de traer filas completas.

        Args:
            db: Sesión de base de datos
            identificacion: Número de documento del afiliado
            fecha_inicial: Fecha inicial del periodo de ITE a verificar

        Returns:
            True si ya existe un registro con esa clave, False si no
        """
        query = select(
            exists().where(
                IteHistorico.identificacion == identificacion,
                IteHistorico.fecha_inicial == fecha_inicial,
            )
        )
        result = await db.execute(query)
        return bool(result.scalar())

    async def get_existentes(
        self,
        db: AsyncSession,
        claves: list[tuple[str, date]],
    ) -> set[tuple[str, date]]:
        """
        Carga masiva: dado un conjunto de claves `(identificacion,
        fecha_inicial)` (p.ej. las de un lote completo), devolver el
        subconjunto que YA existe en el histórico de ITE, en UNA sola
        consulta — evita N consultas de existencia (una por fila del lote)
        al construir el `ContextoAuditoria` (Task 3.3).

        Args:
            db: Sesión de base de datos
            claves: Lista de tuplas (identificacion, fecha_inicial) a
                verificar

        Returns:
            Set de las tuplas (identificacion, fecha_inicial) que sí
            existen en `ite_historico`
        """
        if not claves:
            return set()

        query = select(
            IteHistorico.identificacion, IteHistorico.fecha_inicial
        ).where(
            tuple_(IteHistorico.identificacion, IteHistorico.fecha_inicial).in_(
                claves
            )
        )
        result = await db.execute(query)
        return {(row.identificacion, row.fecha_inicial) for row in result.all()}

    async def bulk_create_flushed(
        self,
        db: AsyncSession,
        registros: list[dict[str, Any]],
    ) -> list[IteHistorico]:
        """
        Crear en lote registros de histórico de ITE (Task 3.2,
        `referencia_adapter.ExcelReferenciaAdapter.importar_ite_historico`),
        usando `db.add_all()` + un único `flush()` — no hace `commit()`,
        mismo patrón que
        `SenalAuditoriaPrevisionalRepository.bulk_create_flushed`. Evita
        N+1 en el lado de ESCRITURA al importar el archivo de referencia
        completo del asegurador (hoja "LISTADO ITE DIA") en vez de un
        `create()` por fila.

        Args:
            db: Sesión de base de datos
            registros: Lista de diccionarios con los datos de cada
                registro (mismas claves que las columnas del modelo)

        Returns:
            Lista de IteHistorico creados (con id asignado)
        """
        if not registros:
            return []

        db_objs = [IteHistorico(**r) for r in registros]
        db.add_all(db_objs)
        await db.flush()
        return db_objs


# Instancia global del repositorio
ite_historico_repository = IteHistoricoRepository()

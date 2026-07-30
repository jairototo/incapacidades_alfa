"""
Repositorio para Incapacidad Previsional.

Consultas no triviales requeridas por Task 2.2:
- `get_by_lote`: listado de un lote con filtros dinámicos opcionales
  (sin_siniestro, repetidas, errores, dif_valor).
- `get_previa_del_afiliado`: busca la incapacidad inmediatamente anterior
  de la misma identificación (por fecha_final < fecha_inicial), respaldando
  el encadenamiento de prórrogas de Task 1.4 (`encadenar_prorrogas`) contra
  datos ya persistidos, no solo en memoria.

Decisiones de mapeo de filtros (el modelo de Task 2.1 no trae columnas
`siniestro_id` ni `es_repetida` literales — ver `incapacidad_previsional.py`):
- `sin_siniestro`: se mapea a `numero_siniestro IS NULL` (el modelo no tiene
  FK `siniestro_id`; el campo crudo que indica "sin siniestro asociado" es
  `numero_siniestro`, coherente con el estado `SIN_SINIESTRO`).
- `repetidas`: se mapea a la columna `es_duplicado_interno` (booleana), que
  es el campo más cercano semánticamente a "repetida" que existe en el
  modelo — no existe una columna `es_repetida` separada.
- `errores`: se mapea a `errores_carga IS NOT NULL` (JSONB; se guarda como
  `None` cuando no hubo errores de parseo — ver `errores_carga` en el
  modelo).
- `dif_valor`: se mapea a `diferencia_valor_afp IS NOT NULL AND != 0`.
"""
from datetime import date
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.base_repository import BaseRepository
from app.models.previsionales.incapacidad_previsional import IncapacidadPrevisional


class IncapacidadPrevisionalRepository(BaseRepository[IncapacidadPrevisional]):
    """Repositorio para operaciones con IncapacidadPrevisional."""

    def __init__(self) -> None:
        super().__init__(IncapacidadPrevisional)

    async def get_by_lote(
        self,
        db: AsyncSession,
        lote_id: UUID,
        filtros: Optional[dict[str, Any]] = None,
    ) -> list[IncapacidadPrevisional]:
        """
        Listar las incapacidades de un lote, con filtros opcionales.

        Los filtros se aplican dinámicamente según las claves presentes en
        `filtros` — ninguna es obligatoria. Claves soportadas:

        - `sin_siniestro` (bool): True -> `numero_siniestro IS NULL`;
          False -> `numero_siniestro IS NOT NULL`.
        - `repetidas` (bool): filtra por `es_duplicado_interno == valor`.
        - `errores` (bool): True -> `errores_carga IS NOT NULL`;
          False -> `errores_carga IS NULL`.
        - `dif_valor` (bool): True -> `diferencia_valor_afp` no nulo y
          distinto de cero; False -> nulo o igual a cero.

        Args:
            db: Sesión de base de datos
            lote_id: UUID del lote
            filtros: Diccionario opcional de filtros (ver arriba)

        Returns:
            Lista de IncapacidadPrevisional que cumplen los filtros
        """
        query = select(IncapacidadPrevisional).where(
            IncapacidadPrevisional.lote_id == lote_id
        )

        if filtros:
            if "sin_siniestro" in filtros and filtros["sin_siniestro"] is not None:
                if filtros["sin_siniestro"]:
                    query = query.where(IncapacidadPrevisional.numero_siniestro.is_(None))
                else:
                    query = query.where(IncapacidadPrevisional.numero_siniestro.isnot(None))

            if "repetidas" in filtros and filtros["repetidas"] is not None:
                query = query.where(
                    IncapacidadPrevisional.es_duplicado_interno == filtros["repetidas"]
                )

            if "errores" in filtros and filtros["errores"] is not None:
                if filtros["errores"]:
                    query = query.where(IncapacidadPrevisional.errores_carga.isnot(None))
                else:
                    query = query.where(IncapacidadPrevisional.errores_carga.is_(None))

            if "dif_valor" in filtros and filtros["dif_valor"] is not None:
                if filtros["dif_valor"]:
                    query = query.where(
                        and_(
                            IncapacidadPrevisional.diferencia_valor_afp.isnot(None),
                            IncapacidadPrevisional.diferencia_valor_afp != 0,
                        )
                    )
                else:
                    query = query.where(
                        (IncapacidadPrevisional.diferencia_valor_afp.is_(None))
                        | (IncapacidadPrevisional.diferencia_valor_afp == 0)
                    )

        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_previa_del_afiliado(
        self,
        db: AsyncSession,
        identificacion: str,
        fecha_inicial: date,
    ) -> Optional[IncapacidadPrevisional]:
        """
        Buscar la incapacidad previsional inmediatamente anterior de la
        misma identificación (misma persona), es decir, la de
        `fecha_final` más reciente que sea estrictamente anterior a
        `fecha_inicial`.

        Respalda el encadenamiento de prórrogas de Task 1.4
        (`encadenar_prorrogas`) contra el histórico persistido, no solo
        contra las filas del lote en memoria.

        Args:
            db: Sesión de base de datos
            identificacion: Número de documento del afiliado
            fecha_inicial: Fecha inicial de la incapacidad "nueva" a la que
                se le busca una posible incapacidad previa

        Returns:
            La IncapacidadPrevisional previa más reciente, o None
        """
        query = (
            select(IncapacidadPrevisional)
            .where(
                IncapacidadPrevisional.identificacion == identificacion,
                IncapacidadPrevisional.fecha_final.isnot(None),
                IncapacidadPrevisional.fecha_final < fecha_inicial,
            )
            .order_by(IncapacidadPrevisional.fecha_final.desc())
            .limit(1)
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()


# Instancia global del repositorio
incapacidad_previsional_repository = IncapacidadPrevisionalRepository()

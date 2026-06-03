"""
Repositorio para PreIncapacidad y PreDocumento.
"""
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.repositories.base_repository import BaseRepository
from app.models.pre_incapacidad import PreIncapacidad
from app.models.pre_documento import PreDocumento


class PreIncapacidadRepository(BaseRepository[PreIncapacidad]):
    """Repositorio para operaciones con PreIncapacidad."""

    def __init__(self) -> None:
        super().__init__(PreIncapacidad)

    async def get_next_numero_radicacion(self, db: AsyncSession) -> int:
        """
        Obtiene el siguiente número de radicación desde la sequence de PostgreSQL.
        Garantiza unicidad incluso con concurrencia.
        """
        result = await db.execute(
            text("SELECT nextval('pre_incapacidad_numero_seq')")
        )
        return result.scalar_one()

    async def create_with_numero(
        self, db: AsyncSession, obj_in: dict
    ) -> PreIncapacidad:
        """Crea una pre-incapacidad obteniendo primero el número de la sequence."""
        numero = await self.get_next_numero_radicacion(db)
        obj_in["numero_radicacion"] = numero
        db_obj = PreIncapacidad(**obj_in)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        # Recargar con documentos (vacío en creación, pero consistente)
        return await self.get_by_id_with_documentos(db, db_obj.id)  # type: ignore

    async def get_by_id_with_documentos(
        self, db: AsyncSession, id: UUID
    ) -> Optional[PreIncapacidad]:
        """Obtiene una pre-incapacidad con sus documentos cargados."""
        result = await db.execute(
            select(PreIncapacidad)
            .options(selectinload(PreIncapacidad.documentos))
            .where(PreIncapacidad.id == id)
        )
        return result.scalar_one_or_none()

    async def get_by_numero_radicacion(
        self, db: AsyncSession, numero: int
    ) -> Optional[PreIncapacidad]:
        result = await db.execute(
            select(PreIncapacidad)
            .options(selectinload(PreIncapacidad.documentos))
            .where(PreIncapacidad.numero_radicacion == numero)
        )
        return result.scalar_one_or_none()

    async def list_pendientes(
        self, db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> List[PreIncapacidad]:
        result = await db.execute(
            select(PreIncapacidad)
            .options(selectinload(PreIncapacidad.documentos))
            .where(PreIncapacidad.estado == "PENDIENTE")
            .order_by(PreIncapacidad.created_at.asc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())


class PreDocumentoRepository(BaseRepository[PreDocumento]):
    """Repositorio para operaciones con PreDocumento."""

    def __init__(self) -> None:
        super().__init__(PreDocumento)

    async def list_by_pre_incapacidad(
        self, db: AsyncSession, pre_incapacidad_id: UUID
    ) -> List[PreDocumento]:
        result = await db.execute(
            select(PreDocumento)
            .where(PreDocumento.pre_incapacidad_id == pre_incapacidad_id)
            .order_by(PreDocumento.created_at.asc())
        )
        return list(result.scalars().all())

    async def count_by_pre_incapacidad(
        self, db: AsyncSession, pre_incapacidad_id: UUID
    ) -> int:
        result = await db.execute(
            select(func.count()).select_from(PreDocumento)
            .where(PreDocumento.pre_incapacidad_id == pre_incapacidad_id)
        )
        return result.scalar_one()

"""
Repository para Pre-Incapacidades con métodos para promoción.
"""
from uuid import UUID
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.pre_incapacidad import PreIncapacidad
from app.core.exceptions import NotFoundException


class PreIncapacidadRepository:
    """Repository para Pre-Incapacidades."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, id: UUID) -> Optional[PreIncapacidad]:
        """Obtener pre-incapacidad por ID con relationships."""
        query = select(PreIncapacidad).where(PreIncapacidad.id == id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_numero_radicacion(self, numero: int) -> Optional[PreIncapacidad]:
        """Obtener pre-incapacidad por número de radicación."""
        query = select(PreIncapacidad).where(PreIncapacidad.numero_radicacion == numero)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update_estado(self, id: UUID, nuevo_estado: str) -> PreIncapacidad:
        """Actualizar estado de pre-incapacidad."""
        pre_inc = await self.get_by_id(id)
        if not pre_inc:
            raise NotFoundException(f"PreIncapacidad {id} not found")

        pre_inc.estado = nuevo_estado
        self.db.add(pre_inc)
        await self.db.flush()
        return pre_inc

    async def update_error(self, id: UUID, error_msg: str) -> PreIncapacidad:
        """Registrar error de procesamiento."""
        pre_inc = await self.get_by_id(id)
        if not pre_inc:
            raise NotFoundException(f"PreIncapacidad {id} not found")

        pre_inc.error_procesamiento = error_msg
        self.db.add(pre_inc)
        await self.db.flush()
        return pre_inc

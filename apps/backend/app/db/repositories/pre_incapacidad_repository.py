"""
Repository para Pre-Incapacidades y Pre-Documentos con métodos para promoción.
"""
from uuid import UUID
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.pre_incapacidad import PreIncapacidad
from app.models.pre_documento import PreDocumento
from app.core.exceptions import NotFoundException


class PreIncapacidadRepository:
    """Repository para Pre-Incapacidades."""

    def __init__(self):
        """Constructor sin db — compatible con servicio."""
        pass

    async def get_by_id(self, db: AsyncSession, id: UUID) -> Optional[PreIncapacidad]:
        """Obtener pre-incapacidad por ID con relationships."""
        query = select(PreIncapacidad).where(PreIncapacidad.id == id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_id_with_documentos(
        self, db: AsyncSession, id: UUID
    ) -> Optional[PreIncapacidad]:
        """Obtener pre-incapacidad por ID con documentos cargados."""
        query = select(PreIncapacidad).where(PreIncapacidad.id == id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_numero_radicacion(
        self, db: AsyncSession, numero: int
    ) -> Optional[PreIncapacidad]:
        """Obtener pre-incapacidad por número de radicación."""
        query = select(PreIncapacidad).where(PreIncapacidad.numero_radicacion == numero)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def create_with_numero(
        self, db: AsyncSession, data: dict
    ) -> PreIncapacidad:
        """Crear nueva pre-incapacidad con número secuencial."""
        pre_inc = PreIncapacidad(**data)
        db.add(pre_inc)
        await db.flush()
        await db.refresh(pre_inc)
        return pre_inc

    async def update_estado(
        self, db: AsyncSession, id: UUID, nuevo_estado: str
    ) -> PreIncapacidad:
        """Actualizar estado de pre-incapacidad."""
        pre_inc = await self.get_by_id(db, id)
        if not pre_inc:
            raise NotFoundException(f"PreIncapacidad {id} not found")

        pre_inc.estado = nuevo_estado
        db.add(pre_inc)
        await db.flush()
        return pre_inc

    async def update_error(
        self, db: AsyncSession, id: UUID, error_msg: str
    ) -> PreIncapacidad:
        """Registrar error de procesamiento."""
        pre_inc = await self.get_by_id(db, id)
        if not pre_inc:
            raise NotFoundException(f"PreIncapacidad {id} not found")

        pre_inc.error_procesamiento = error_msg
        db.add(pre_inc)
        await db.flush()
        return pre_inc


class PreDocumentoRepository:
    """Repository para Pre-Documentos (documentos de pre-incapacidades)."""

    def __init__(self):
        """Constructor sin db — compatible con servicio legacy."""
        pass

    async def get_by_id(self, db: AsyncSession, id: UUID) -> Optional[PreDocumento]:
        """Obtener pre-documento por ID."""
        query = select(PreDocumento).where(PreDocumento.id == id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_pre_incapacidad(
        self, db: AsyncSession, pre_incapacidad_id: UUID
    ) -> List[PreDocumento]:
        """Obtener todos los documentos de una pre-incapacidad."""
        query = select(PreDocumento).where(
            PreDocumento.pre_incapacidad_id == pre_incapacidad_id
        )
        result = await db.execute(query)
        return result.scalars().all()

    async def create(
        self,
        db: AsyncSession,
        data: dict,
    ) -> PreDocumento:
        """Crear nuevo pre-documento desde diccionario."""
        doc = PreDocumento(**data)
        db.add(doc)
        await db.flush()
        await db.refresh(doc)
        return doc

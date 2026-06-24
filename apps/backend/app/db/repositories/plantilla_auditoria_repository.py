"""
Repositorio para Plantilla de Auditoría.

Maneja operaciones CRUD y la lógica de upsert por incapacidad_id.
"""
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.base_repository import BaseRepository
from app.models.plantilla_auditoria import PlantillaAuditoria


class PlantillaAuditoriaRepository(BaseRepository[PlantillaAuditoria]):
    """Repositorio para operaciones con PlantillaAuditoria."""

    def __init__(self) -> None:
        super().__init__(PlantillaAuditoria)

    async def get_by_incapacidad(
        self,
        db: AsyncSession,
        incapacidad_id: UUID,
    ) -> Optional[PlantillaAuditoria]:
        """
        Obtener la plantilla de una incapacidad específica.

        Args:
            db: Sesión de base de datos
            incapacidad_id: ID de la incapacidad

        Returns:
            Plantilla si existe, None en caso contrario
        """
        result = await db.execute(
            select(PlantillaAuditoria).where(
                PlantillaAuditoria.incapacidad_id == incapacidad_id
            )
        )
        return result.scalar_one_or_none()

    async def upsert(
        self,
        db: AsyncSession,
        incapacidad_id: UUID,
        data: dict,
    ) -> PlantillaAuditoria:
        """
        Crear o actualizar la plantilla para una incapacidad.

        Si ya existe una plantilla para esa incapacidad, la actualiza.
        Si no existe, la crea.

        Args:
            db: Sesión de base de datos
            incapacidad_id: ID de la incapacidad
            data: Diccionario con los datos de la plantilla

        Returns:
            Plantilla creada o actualizada
        """
        existing = await self.get_by_incapacidad(db, incapacidad_id)

        if existing is not None:
            # Actualizar todos los campos del dict
            for key, value in data.items():
                setattr(existing, key, value)
            db.add(existing)
            await db.commit()
            await db.refresh(existing)
            return existing

        # Crear nueva plantilla
        data["incapacidad_id"] = incapacidad_id
        return await self.create(db, data)


# Instancia global del repositorio
plantilla_auditoria_repository = PlantillaAuditoriaRepository()

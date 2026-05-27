"""
Repositorio para Auditoría Datos Aprobados.

Maneja las operaciones CRUD y consultas específicas para
los datos aprobados durante la auditoría.
"""
from typing import Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.backend.app.db.repositories.base_repository import BaseRepository
from apps.backend.app.models.auditoria_datos_aprobados import AuditoriaDatosAprobados


class AuditoriaDatosRepository(BaseRepository[AuditoriaDatosAprobados]):
    """
    Repositorio para operaciones con AuditoriaDatosAprobados.
    
    Maneja la persistencia de los datos modificados/aprobados
    por el auditor durante la auditoría parcial.
    """
    
    def __init__(self):
        """Inicializar repositorio."""
        super().__init__(AuditoriaDatosAprobados)
    
    async def get_by_incapacidad(
        self, 
        db: AsyncSession, 
        incapacidad_id: UUID
    ) -> Optional[AuditoriaDatosAprobados]:
        """
        Obtener datos aprobados de una incapacidad específica.
        
        Args:
            db: Sesión de base de datos
            incapacidad_id: ID de la incapacidad
            
        Returns:
            Datos aprobados si existen, None en caso contrario
        """
        query = select(AuditoriaDatosAprobados).where(
            AuditoriaDatosAprobados.incapacidad_id == incapacidad_id
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    async def delete_by_incapacidad(
        self,
        db: AsyncSession,
        incapacidad_id: UUID
    ) -> bool:
        """
        Eliminar datos aprobados de una incapacidad.
        
        Útil cuando se necesita re-auditar o cancelar una aprobación parcial.
        
        Args:
            db: Sesión de base de datos
            incapacidad_id: ID de la incapacidad
            
        Returns:
            True si se eliminó, False si no existía
        """
        datos = await self.get_by_incapacidad(db, incapacidad_id)
        
        if datos:
            await db.delete(datos)
            await db.commit()
            return True
        
        return False
    
    async def exists_for_incapacidad(
        self,
        db: AsyncSession,
        incapacidad_id: UUID
    ) -> bool:
        """
        Verificar si existen datos aprobados para una incapacidad.
        
        Args:
            db: Sesión de base de datos
            incapacidad_id: ID de la incapacidad
            
        Returns:
            True si existen datos aprobados, False en caso contrario
        """
        datos = await self.get_by_incapacidad(db, incapacidad_id)
        return datos is not None


# Instancia global del repositorio
auditoria_datos_repository = AuditoriaDatosRepository()

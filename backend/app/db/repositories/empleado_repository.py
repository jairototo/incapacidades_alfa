"""
Repository para operaciones de base de datos de Empleado.
"""
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.base_repository import BaseRepository
from app.models.empleado import Empleado
from app.utils.enums import EstadoEmpleado


class EmpleadoRepository(BaseRepository[Empleado]):
    """Repository para Empleado con operaciones específicas."""

    def __init__(self):
        """Inicializa el repository con el modelo Empleado."""
        super().__init__(Empleado)

    async def get_by_documento(
        self,
        db: AsyncSession,
        documento: str,
        empresa_id: UUID
    ) -> Optional[Empleado]:
        """
        Obtiene un empleado por número de documento y empresa.
        
        Args:
            db: Sesión de base de datos
            documento: Número de documento
            empresa_id: ID de la empresa
            
        Returns:
            Empleado si existe, None si no
        """
        query = select(Empleado).where(
            and_(
                Empleado.numero_documento == documento,
                Empleado.empresa_id == empresa_id
            )
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_empresa(
        self,
        db: AsyncSession,
        empresa_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Empleado]:
        """
        Obtiene todos los empleados de una empresa.
        
        Args:
            db: Sesión de base de datos
            empresa_id: ID de la empresa
            skip: Número de registros a saltar
            limit: Número máximo de registros a retornar
            
        Returns:
            Lista de empleados de la empresa
        """
        query = select(Empleado).where(
            Empleado.empresa_id == empresa_id
        ).offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_activos(
        self,
        db: AsyncSession,
        empresa_id: Optional[UUID] = None
    ) -> List[Empleado]:
        """
        Obtiene empleados activos, opcionalmente filtrados por empresa.
        
        Args:
            db: Sesión de base de datos
            empresa_id: ID de la empresa (opcional)
            
        Returns:
            Lista de empleados activos
        """
        query = select(Empleado).where(Empleado.estado == EstadoEmpleado.ACTIVO)
        
        if empresa_id:
            query = query.where(Empleado.empresa_id == empresa_id)
        
        result = await db.execute(query)
        return list(result.scalars().all())

    async def search(
        self,
        db: AsyncSession,
        empresa_id: Optional[UUID] = None,
        estado: Optional[EstadoEmpleado] = None,
        documento: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Empleado]:
        """
        Busca empleados con múltiples filtros.
        
        Args:
            db: Sesión de base de datos
            empresa_id: Filtrar por empresa
            estado: Filtrar por estado
            documento: Filtrar por número de documento
            search: Búsqueda en nombres, apellidos o documento
            skip: Número de registros a saltar
            limit: Número máximo de registros a retornar
            
        Returns:
            Lista de empleados que cumplen los criterios
        """
        query = select(Empleado)
        
        # Aplicar filtros
        if empresa_id:
            query = query.where(Empleado.empresa_id == empresa_id)
        
        if estado:
            query = query.where(Empleado.estado == estado)
        
        if documento:
            query = query.where(Empleado.numero_documento.ilike(f"%{documento}%"))
        
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                or_(
                    Empleado.nombres.ilike(search_pattern),
                    Empleado.apellidos.ilike(search_pattern),
                    Empleado.numero_documento.ilike(search_pattern),
                    Empleado.email.ilike(search_pattern)
                )
            )
        
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_by_external_id(
        self,
        db: AsyncSession,
        external_id: str,
        sync_source: str
    ) -> Optional[Empleado]:
        """
        Obtiene un empleado por su ID externo y fuente de sincronización.
        
        Args:
            db: Sesión de base de datos
            external_id: ID en el sistema externo
            sync_source: Fuente de sincronización
            
        Returns:
            Empleado si existe, None si no
        """
        query = select(Empleado).where(
            and_(
                Empleado.external_id == external_id,
                Empleado.sync_source == sync_source
            )
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def count_incapacidades_activas(
        self,
        db: AsyncSession,
        empleado_id: UUID
    ) -> int:
        """
        Cuenta las incapacidades activas de un empleado.
        
        Args:
            db: Sesión de base de datos
            empleado_id: ID del empleado
            
        Returns:
            Número de incapacidades activas
        """
        # TODO: Implementar cuando esté disponible el módulo de incapacidades
        # Por ahora retorna 0 para permitir las operaciones
        return 0
        
        # from app.models.incapacidad import Incapacidad
        # from app.utils.enums import EstadoIncapacidad
        # 
        # # Estados considerados "activos" (no finalizados)
        # estados_activos = [
        #     EstadoIncapacidad.RADICADA,
        #     EstadoIncapacidad.EN_AUDITORIA,
        #     EstadoIncapacidad.OBSERVADA,
        #     EstadoIncapacidad.APROBADA,
        #     EstadoIncapacidad.EN_PAGO
        # ]
        # 
        # query = select(Incapacidad).where(
        #     and_(
        #         Incapacidad.empleado_id == empleado_id,
        #         Incapacidad.estado.in_(estados_activos)
        #     )
        # )
        # result = await db.execute(query)
        # return len(result.scalars().all())


# Singleton instance
empleado_repository = EmpleadoRepository()

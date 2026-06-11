"""
Repositorio base genérico para operaciones CRUD.
"""
from typing import Generic, TypeVar, Type, Optional, List, Any, Dict
from uuid import UUID

from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import BaseModel

ModelType = TypeVar("ModelType", bound=BaseModel)


class BaseRepository(Generic[ModelType]):
    """
    Repositorio base con operaciones CRUD genéricas.
    
    Implementa el patrón Repository para abstraer el acceso a datos.
    
    Attributes:
        model: Modelo SQLAlchemy asociado al repositorio
    """
    
    def __init__(self, model: Type[ModelType]):
        """
        Inicializar repositorio.
        
        Args:
            model: Clase del modelo SQLAlchemy
        """
        self.model = model
    
    async def create(self, db: AsyncSession, obj_in: Dict[str, Any]) -> ModelType:
        """
        Crear un nuevo registro.
        
        Args:
            db: Sesión de base de datos
            obj_in: Diccionario con datos del objeto
            
        Returns:
            Objeto creado
        """
        db_obj = self.model(**obj_in)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def create_flushed(self, db: AsyncSession, obj_in: Dict[str, Any]) -> ModelType:
        """Like create() but flushes instead of committing — for caller-managed transactions."""
        db_obj = self.model(**obj_in)
        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj

    async def get_by_id(self, db: AsyncSession, id: UUID) -> Optional[ModelType]:
        """
        Obtener registro por ID.
        
        Args:
            db: Sesión de base de datos
            id: UUID del registro
            
        Returns:
            Objeto encontrado o None
        """
        result = await db.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()
    
    async def get_multi(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[List[Any]] = None
    ) -> List[ModelType]:
        """
        Obtener múltiples registros con filtros opcionales.
        
        Args:
            db: Sesión de base de datos
            skip: Número de registros a saltar
            limit: Número máximo de registros a retornar
            filters: Filtros a aplicar (campo: valor)
            order_by: Lista de campos para ordenar
            
        Returns:
            Lista de objetos
        """
        query = select(self.model)
        
        # Aplicar filtros
        if filters:
            for field, value in filters.items():
                if value is not None:
                    query = query.where(getattr(self.model, field) == value)
        
        # Aplicar ordenamiento
        if order_by:
            query = query.order_by(*order_by)
        else:
            query = query.order_by(self.model.created_at.desc())
        
        # Aplicar paginación
        query = query.offset(skip).limit(limit)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def count(
        self,
        db: AsyncSession,
        filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Contar registros con filtros opcionales.
        
        Args:
            db: Sesión de base de datos
            filters: Filtros a aplicar (campo: valor)
            
        Returns:
            Número total de registros
        """
        query = select(func.count()).select_from(self.model)
        
        if filters:
            for field, value in filters.items():
                if value is not None:
                    query = query.where(getattr(self.model, field) == value)
        
        result = await db.execute(query)
        return result.scalar_one()
    
    async def update(
        self,
        db: AsyncSession,
        *,
        id: UUID,
        obj_in: Dict[str, Any]
    ) -> Optional[ModelType]:
        """
        Actualizar un registro.
        
        Args:
            db: Sesión de base de datos
            id: UUID del registro
            obj_in: Diccionario con datos a actualizar
            
        Returns:
            Objeto actualizado o None si no existe
        """
        # Filtrar campos None para actualización parcial
        update_data = {k: v for k, v in obj_in.items() if v is not None}
        
        if not update_data:
            return await self.get_by_id(db, id)
        
        stmt = (
            update(self.model)
            .where(self.model.id == id)
            .values(**update_data)
            .returning(self.model)
        )
        
        result = await db.execute(stmt)
        await db.commit()
        
        updated_obj = result.scalar_one_or_none()
        if updated_obj:
            await db.refresh(updated_obj)
        
        return updated_obj

    async def update_flushed(
        self,
        db: AsyncSession,
        id: UUID,
        obj_in: Dict[str, Any],
    ) -> Optional[ModelType]:
        """Like update() but does not commit — for caller-managed transactions."""
        update_data = {k: v for k, v in obj_in.items() if v is not None}
        if not update_data:
            return await self.get_by_id(db, id)
        stmt = (
            update(self.model)
            .where(self.model.id == id)
            .values(**update_data)
            .returning(self.model)
        )
        result = await db.execute(stmt)
        updated_obj = result.scalar_one_or_none()
        if updated_obj:
            await db.refresh(updated_obj)
        return updated_obj

    async def delete(self, db: AsyncSession, id: UUID) -> bool:
        """
        Eliminar un registro.
        
        Args:
            db: Sesión de base de datos
            id: UUID del registro
            
        Returns:
            True si se eliminó, False si no existía
        """
        stmt = delete(self.model).where(self.model.id == id)
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount > 0
    
    async def exists(self, db: AsyncSession, id: UUID) -> bool:
        """
        Verificar si existe un registro.
        
        Args:
            db: Sesión de base de datos
            id: UUID del registro
            
        Returns:
            True si existe, False en caso contrario
        """
        result = await db.execute(
            select(self.model.id).where(self.model.id == id)
        )
        return result.scalar_one_or_none() is not None

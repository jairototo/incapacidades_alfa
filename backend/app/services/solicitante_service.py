"""
Service para Solicitante.
"""

from typing import List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.solicitante_repository import solicitante_repository
from app.schemas.solicitante import SolicitanteCreate, SolicitanteUpdate
from app.models.solicitante import Solicitante
from app.core.exceptions import NotFoundException, ValidationException
from app.core.logging import logger


class SolicitanteService:
    """Service para lógica de negocio de Solicitante."""
    
    def __init__(self):
        """Inicializa el service con el repositorio global."""
        self.repository = solicitante_repository
    
    async def create_solicitante(
        self,
        db: AsyncSession,
        data: SolicitanteCreate
    ) -> Solicitante:
        """
        Crear nuevo solicitante.
        
        Args:
            db: Sesión de base de datos
            data: Datos del solicitante a crear
            
        Returns:
            Solicitante creado
            
        Raises:
            ValidationException: Si el correo ya existe
        """
        # Verificar si el correo ya existe
        correo_normalizado = data.correo.lower().strip()
        existing = await self.repository.get_by_correo(db, correo_normalizado)
        
        if existing:
            logger.warning(
                f"Intento de crear solicitante con correo duplicado: {correo_normalizado}"
            )
            raise ValidationException(
                f"Ya existe un solicitante registrado con el correo {data.correo}"
            )
        
        # Crear solicitante
        solicitante_dict = {
            "correo": correo_normalizado,
            "nombres": data.nombres.strip(),
            "apellidos": data.apellidos.strip(),
            "telefono": data.telefono
        }
        
        created = await self.repository.create(db, solicitante_dict)
        
        logger.info(
            f"Solicitante creado exitosamente",
            extra={
                "solicitante_id": str(created.id),
                "correo": created.correo
            }
        )
        
        return created
    
    async def get_solicitante(
        self,
        db: AsyncSession,
        solicitante_id: UUID
    ) -> Solicitante:
        """
        Obtener solicitante por ID.
        
        Args:
            db: Sesión de base de datos
            solicitante_id: ID del solicitante
            
        Returns:
            Solicitante encontrado
            
        Raises:
            NotFoundException: Si el solicitante no existe
        """
        solicitante = await self.repository.get_by_id(db, solicitante_id)
        
        if not solicitante:
            raise NotFoundException(
                f"Solicitante con ID {solicitante_id} no encontrado"
            )
        
        return solicitante
    
    async def get_by_correo(
        self,
        db: AsyncSession,
        correo: str
    ) -> Solicitante | None:
        """
        Buscar solicitante por correo exacto.
        
        Args:
            db: Sesión de base de datos
            correo: Email del solicitante
            
        Returns:
            Solicitante si existe, None en caso contrario
        """
        return await self.repository.get_by_correo(db, correo)
    
    async def search_by_correo(
        self,
        db: AsyncSession,
        correo: str,
        limit: int = 10
    ) -> List[Solicitante]:
        """
        Buscar solicitantes por correo (búsqueda parcial).
        
        Args:
            db: Sesión de base de datos
            correo: Texto a buscar en el correo
            limit: Número máximo de resultados
            
        Returns:
            Lista de solicitantes que coinciden
            
        Raises:
            ValidationException: Si el término de búsqueda es muy corto
        """
        if not correo or len(correo.strip()) < 3:
            raise ValidationException(
                "El término de búsqueda debe tener al menos 3 caracteres"
            )
        
        return await self.repository.search_by_correo(db, correo, limit)
    
    async def search_by_nombre(
        self,
        db: AsyncSession,
        nombre: str,
        limit: int = 10
    ) -> List[Solicitante]:
        """
        Buscar solicitantes por nombre o apellido.
        
        Args:
            db: Sesión de base de datos
            nombre: Texto a buscar
            limit: Número máximo de resultados
            
        Returns:
            Lista de solicitantes que coinciden
            
        Raises:
            ValidationException: Si el término de búsqueda es muy corto
        """
        if not nombre or len(nombre.strip()) < 3:
            raise ValidationException(
                "El término de búsqueda debe tener al menos 3 caracteres"
            )
        
        return await self.repository.search_by_nombre(db, nombre, limit)
    
    async def list_solicitantes(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100
    ) -> List[Solicitante]:
        """
        Listar solicitantes con paginación.
        
        Args:
            db: Sesión de base de datos
            skip: Número de registros a saltar
            limit: Número máximo de resultros
            
        Returns:
            Lista de solicitantes
        """
        return await self.repository.get_multi(db, skip=skip, limit=limit)
    
    async def update_solicitante(
        self,
        db: AsyncSession,
        solicitante_id: UUID,
        data: SolicitanteUpdate
    ) -> Solicitante:
        """
        Actualizar solicitante.
        
        Args:
            db: Sesión de base de datos
            solicitante_id: ID del solicitante
            data: Datos a actualizar
            
        Returns:
            Solicitante actualizado
            
        Raises:
            NotFoundException: Si el solicitante no existe
            ValidationException: Si el nuevo correo ya existe
        """
        solicitante = await self.get_solicitante(db, solicitante_id)
        
        # Verificar correo duplicado si se está cambiando
        if data.correo and data.correo.lower().strip() != solicitante.correo:
            correo_normalizado = data.correo.lower().strip()
            existing = await self.repository.get_by_correo(db, correo_normalizado)
            if existing:
                raise ValidationException(
                    f"Ya existe un solicitante con el correo {data.correo}"
                )
        
        # Aplicar cambios
        update_data = data.model_dump(exclude_unset=True)
        
        if "correo" in update_data:
            update_data["correo"] = update_data["correo"].lower().strip()
        if "nombres" in update_data:
            update_data["nombres"] = update_data["nombres"].strip()
        if "apellidos" in update_data:
            update_data["apellidos"] = update_data["apellidos"].strip()
        
        updated = await self.repository.update(db, id=solicitante_id, obj_in=update_data)
        
        logger.info(
            f"Solicitante actualizado",
            extra={
                "solicitante_id": str(updated.id),
                "campos_actualizados": list(update_data.keys())
            }
        )
        
        return updated
    
    async def delete_solicitante(
        self,
        db: AsyncSession,
        solicitante_id: UUID
    ) -> None:
        """
        Eliminar solicitante.
        
        Args:
            db: Sesión de base de datos
            solicitante_id: ID del solicitante
            
        Raises:
            NotFoundException: Si el solicitante no existe
        """
        solicitante = await self.get_solicitante(db, solicitante_id)
        
        await self.repository.delete(db, solicitante_id)
        
        logger.info(
            f"Solicitante eliminado",
            extra={"solicitante_id": str(solicitante_id)}
        )


# Instancia global del servicio
solicitante_service = SolicitanteService()

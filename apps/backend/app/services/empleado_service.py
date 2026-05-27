"""
Service para lógica de negocio de Empleado.
"""
from datetime import date
from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from apps.backend.app.core.exceptions import (
    NotFoundException,
    BadRequestException,
    ConflictException
)
from apps.backend.app.db.repositories.empleado_repository import empleado_repository
from apps.backend.app.db.repositories.empresa_repository import empresa_repository
from apps.backend.app.models.empleado import Empleado
from apps.backend.app.schemas.empleado import EmpleadoCreate, EmpleadoUpdate
from apps.backend.app.utils.enums import EstadoEmpleado, EstadoEmpresa


class EmpleadoService:
    """Service para operaciones de negocio de Empleado."""

    def __init__(self):
        """Inicializa el service con los repositories necesarios."""
        self.repository = empleado_repository
        self.empresa_repository = empresa_repository

    async def create_empleado(
        self,
        db: AsyncSession,
        empleado_data: EmpleadoCreate
    ) -> Empleado:
        """
        Crea un nuevo empleado con validaciones.
        
        Args:
            db: Sesión de base de datos
            empleado_data: Datos del empleado a crear
            
        Returns:
            Empleado creado
            
        Raises:
            NotFoundException: Si la empresa no existe
            BadRequestException: Si la empresa está inactiva o las fechas son inválidas
            ConflictException: Si ya existe un empleado con ese documento en la empresa
        """
        # Validar que la empresa existe y está activa
        empresa = await self.empresa_repository.get_by_id(
            db,
            empleado_data.empresa_id
        )
        if not empresa:
            raise NotFoundException(
                f"Empresa con ID {empleado_data.empresa_id} no encontrada"
            )
        
        if empresa.estado != EstadoEmpresa.ACTIVA:
            raise BadRequestException(
                f"No se pueden crear empleados para una empresa en estado {empresa.estado}"
            )
        
        # Validar que no exista empleado con mismo documento en la empresa
        existing = await self.repository.get_by_documento(
            db,
            empleado_data.numero_documento,
            empleado_data.empresa_id
        )
        if existing:
            raise ConflictException(
                f"Ya existe un empleado con documento {empleado_data.numero_documento} "
                f"en la empresa {empresa.razon_social}"
            )
        
        # Validar fechas
        self._validate_fechas(
            empleado_data.fecha_ingreso,
            empleado_data.fecha_retiro,
            empleado_data.fecha_nacimiento
        )
        
        # Crear empleado
        empleado_dict = empleado_data.model_dump()
        return await self.repository.create(db, empleado_dict)

    async def get_empleado(
        self,
        db: AsyncSession,
        empleado_id: UUID
    ) -> Empleado:
        """
        Obtiene un empleado por ID.
        
        Args:
            db: Sesión de base de datos
            empleado_id: ID del empleado
            
        Returns:
            Empleado encontrado
            
        Raises:
            NotFoundException: Si el empleado no existe
        """
        empleado = await self.repository.get_by_id(db, empleado_id)
        if not empleado:
            raise NotFoundException(f"Empleado con ID {empleado_id} no encontrado")
        return empleado

    async def list_empleados(
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
        Lista empleados con filtros opcionales.
        
        Args:
            db: Sesión de base de datos
            empresa_id: Filtrar por empresa
            estado: Filtrar por estado
            documento: Filtrar por documento
            search: Búsqueda en nombres/apellidos/documento
            skip: Número de registros a saltar
            limit: Número máximo de registros
            
        Returns:
            Lista de empleados
        """
        return await self.repository.search(
            db,
            empresa_id=empresa_id,
            estado=estado,
            documento=documento,
            search=search,
            skip=skip,
            limit=limit
        )

    async def update_empleado(
        self,
        db: AsyncSession,
        empleado_id: UUID,
        empleado_data: EmpleadoUpdate
    ) -> Empleado:
        """
        Actualiza un empleado con validaciones.
        
        Args:
            db: Sesión de base de datos
            empleado_id: ID del empleado a actualizar
            empleado_data: Datos a actualizar
            
        Returns:
            Empleado actualizado
            
        Raises:
            NotFoundException: Si el empleado no existe
            BadRequestException: Si las fechas son inválidas
        """
        empleado = await self.get_empleado(db, empleado_id)
        
        # Validar fechas si se están actualizando
        fecha_ingreso = empleado_data.fecha_ingreso or empleado.fecha_ingreso
        fecha_retiro = empleado_data.fecha_retiro
        if fecha_retiro is None and empleado_data.fecha_retiro is not None:
            fecha_retiro = empleado_data.fecha_retiro
        elif fecha_retiro is None:
            fecha_retiro = empleado.fecha_retiro
        
        fecha_nacimiento = empleado_data.fecha_nacimiento or empleado.fecha_nacimiento
        
        self._validate_fechas(fecha_ingreso, fecha_retiro, fecha_nacimiento)
        
        # Actualizar empleado
        update_data = empleado_data.model_dump(exclude_unset=True)
        return await self.repository.update(db, id=empleado_id, obj_in=update_data)

    async def delete_empleado(
        self,
        db: AsyncSession,
        empleado_id: UUID
    ) -> bool:
        """
        Elimina un empleado (soft delete).
        
        Args:
            db: Sesión de base de datos
            empleado_id: ID del empleado
            
        Returns:
            True si se eliminó correctamente
            
        Raises:
            NotFoundException: Si el empleado no existe
            BadRequestException: Si tiene incapacidades activas
        """
        empleado = await self.get_empleado(db, empleado_id)
        
        # Verificar que no tenga incapacidades activas
        count_activas = await self.repository.count_incapacidades_activas(
            db,
            empleado_id
        )
        if count_activas > 0:
            raise BadRequestException(
                f"No se puede eliminar el empleado porque tiene {count_activas} "
                "incapacidades activas. Primero finalice o cancele las incapacidades."
            )
        
        return await self.repository.delete(db, empleado_id)

    async def activate_empleado(
        self,
        db: AsyncSession,
        empleado_id: UUID
    ) -> Empleado:
        """
        Activa un empleado.
        
        Args:
            db: Sesión de base de datos
            empleado_id: ID del empleado
            
        Returns:
            Empleado activado
            
        Raises:
            NotFoundException: Si el empleado no existe
            BadRequestException: Si ya está activo
        """
        empleado = await self.get_empleado(db, empleado_id)
        
        if empleado.estado == EstadoEmpleado.ACTIVO:
            raise BadRequestException("El empleado ya está activo")
        
        return await self.repository.update(
            db, 
            id=empleado_id, 
            obj_in={'estado': EstadoEmpleado.ACTIVO}
        )

    async def deactivate_empleado(
        self,
        db: AsyncSession,
        empleado_id: UUID
    ) -> Empleado:
        """
        Desactiva un empleado.
        
        Args:
            db: Sesión de base de datos
            empleado_id: ID del empleado
            
        Returns:
            Empleado desactivado
            
        Raises:
            NotFoundException: Si el empleado no existe
            BadRequestException: Si ya está inactivo o tiene incapacidades activas
        """
        empleado = await self.get_empleado(db, empleado_id)
        
        if empleado.estado == EstadoEmpleado.INACTIVO:
            raise BadRequestException("El empleado ya está inactivo")
        
        # Verificar que no tenga incapacidades activas
        count_activas = await self.repository.count_incapacidades_activas(
            db,
            empleado_id
        )
        if count_activas > 0:
            raise BadRequestException(
                f"No se puede desactivar el empleado porque tiene {count_activas} "
                "incapacidades activas"
            )
        
        return await self.repository.update(
            db,
            id=empleado_id,
            obj_in={'estado': EstadoEmpleado.INACTIVO}
        )

    async def get_empleados_by_empresa(
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
            limit: Número máximo de registros
            
        Returns:
            Lista de empleados de la empresa
            
        Raises:
            NotFoundException: Si la empresa no existe
        """
        # Validar que la empresa existe
        empresa = await self.empresa_repository.get_by_id(db, empresa_id)
        if not empresa:
            raise NotFoundException(f"Empresa con ID {empresa_id} no encontrada")
        
        return await self.repository.get_by_empresa(
            db,
            empresa_id,
            skip=skip,
            limit=limit
        )

    async def get_incapacidades_empleado(
        self,
        db: AsyncSession,
        empleado_id: UUID
    ) -> List[dict]:
        """
        Obtiene las incapacidades de un empleado.
        
        Args:
            db: Sesión de base de datos
            empleado_id: ID del empleado
            
        Returns:
            Lista de incapacidades del empleado
            
        Raises:
            NotFoundException: Si el empleado no existe
        """
        # Validar que el empleado existe
        empleado = await self.get_empleado(db, empleado_id)
        
        # TODO: Cuando esté implementado el módulo de incapacidades,
        # retornar las incapacidades reales del empleado
        # Por ahora retornamos lista vacía
        return []

    def _validate_fechas(
        self,
        fecha_ingreso: Optional[date],
        fecha_retiro: Optional[date],
        fecha_nacimiento: Optional[date]
    ) -> None:
        """
        Valida la coherencia de las fechas.
        
        Args:
            fecha_ingreso: Fecha de ingreso
            fecha_retiro: Fecha de retiro (opcional)
            fecha_nacimiento: Fecha de nacimiento (opcional)
            
        Raises:
            BadRequestException: Si las fechas son inválidas
        """
        today = date.today()
        
        # Validar fecha de ingreso
        if fecha_ingreso and fecha_ingreso > today:
            raise BadRequestException(
                "La fecha de ingreso no puede ser futura"
            )
        
        # Validar fecha de retiro
        if fecha_retiro:
            if fecha_ingreso and fecha_retiro <= fecha_ingreso:
                raise BadRequestException(
                    "La fecha de retiro debe ser posterior a la fecha de ingreso"
                )
            if fecha_retiro > today:
                raise BadRequestException(
                    "La fecha de retiro no puede ser futura"
                )
        
        # Validar fecha de nacimiento
        if fecha_nacimiento:
            if fecha_nacimiento >= today:
                raise BadRequestException(
                    "La fecha de nacimiento debe ser anterior a hoy"
                )
            if fecha_ingreso:
                # Validar edad mínima de 18 años al ingreso
                edad_ingreso = fecha_ingreso.year - fecha_nacimiento.year
                if edad_ingreso < 14:  # Edad mínima laboral en Colombia
                    raise BadRequestException(
                        "El empleado debe tener al menos 14 años a la fecha de ingreso"
                    )


# Singleton instance
empleado_service = EmpleadoService()

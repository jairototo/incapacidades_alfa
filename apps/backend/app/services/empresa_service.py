"""
Servicio de lógica de negocio para Empresas.
"""
from typing import Optional, List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    NotFoundException,
    ValidationException,
    BusinessRuleException,
    DuplicateException
)
from app.core.logging import logger
from app.core.security import get_password_hash
from app.db.repositories.empresa_repository import empresa_repository
from app.db.repositories.usuario_repository import usuario_repository
from app.models.empresa import Empresa
from app.schemas.empresa import EmpresaCreate, EmpresaUpdate
from app.services.usuario_service import usuario_service
from app.utils.enums import RolUsuario, EstadoUsuario


class EmpresaService:
    """
    Servicio de lógica de negocio para gestión de empresas.
    
    Implementa validaciones de negocio y orquesta operaciones
    del repositorio.
    """
    
    def __init__(self):
        """Inicializar servicio."""
        self.repository = empresa_repository
    
    async def create_empresa(
        self,
        db: AsyncSession,
        empresa_in: EmpresaCreate
    ) -> tuple[Empresa, dict]:
        """
        Crear una nueva empresa junto con su usuario de login (transacción única).

        Valida:
        - NIT único
        - Razón social única
        - Tipo de empresa válido
        - email_contacto no está en uso por otro Usuario

        Returns:
            Tupla (Empresa creada, {"username": ..., "password": ...})

        Raises:
            DuplicateException: Si NIT, razón social o email ya existen
            ValidationException: Si los datos son inválidos
        """
        # Validar NIT único
        existing_nit = await self.repository.get_by_nit(db, empresa_in.nit)
        if existing_nit:
            logger.warning(f"Intento de crear empresa con NIT duplicado: {empresa_in.nit}")
            raise DuplicateException(
                f"Ya existe una empresa con NIT {empresa_in.nit}"
            )

        # Validar razón social única
        existing_razon = await self.repository.get_by_razon_social(
            db, empresa_in.razon_social
        )
        if existing_razon:
            logger.warning(
                f"Intento de crear empresa con razón social duplicada: {empresa_in.razon_social}"
            )
            raise DuplicateException(
                f"Ya existe una empresa con razón social '{empresa_in.razon_social}'"
            )

        # Validar que el email de contacto no esté en uso por otro usuario
        existing_user = await usuario_repository.get_by_email(db, empresa_in.email_contacto)
        if existing_user:
            raise DuplicateException(
                f"El correo '{empresa_in.email_contacto}' ya está en uso por otro usuario"
            )

        # Validar formato de NIT (debe ser numérico con dígito de verificación)
        self._validate_nit_format(empresa_in.nit)

        # Validar tipo de empresa si se proporciona
        if empresa_in.tipo_empresa:
            self._validate_tipo_empresa(empresa_in.tipo_empresa)

        # Crear empresa (flush, no commit todavía: transacción única con el Usuario)
        empresa_data = empresa_in.model_dump()
        empresa = await self.repository.create_flushed(db, empresa_data)

        # Crear el usuario de login vinculado a la empresa
        temp_password = usuario_service._generate_temp_password()
        usuario_dict = {
            "username": empresa.nit,
            "email": empresa.email_contacto,
            "password_hash": get_password_hash(temp_password),
            "nombre_completo": empresa.razon_social,
            "rol": RolUsuario.EMPRESA,
            "estado": EstadoUsuario.ACTIVO,
            "empresa_id": empresa.id,
            "must_change_password": False,
        }
        await usuario_repository.create_flushed(db, usuario_dict)

        await db.commit()
        await db.refresh(empresa)

        logger.info(
            f"Empresa creada exitosamente: {empresa.id} - "
            f"NIT: {empresa.nit}, Razón Social: {empresa.razon_social}"
        )

        return empresa, {"username": empresa.nit, "password": temp_password}
    
    async def get_empresa(self, db: AsyncSession, empresa_id: UUID) -> Empresa:
        """
        Obtener empresa por ID.
        
        Args:
            db: Sesión de base de datos
            empresa_id: UUID de la empresa
            
        Returns:
            Empresa encontrada
            
        Raises:
            NotFoundException: Si la empresa no existe
        """
        empresa = await self.repository.get_by_id(db, empresa_id)
        
        if not empresa:
            logger.warning(f"Empresa no encontrada: {empresa_id}")
            raise NotFoundException(f"Empresa con ID {empresa_id} no encontrada")
        
        return empresa
    
    async def update_empresa(
        self,
        db: AsyncSession,
        empresa_id: UUID,
        empresa_in: EmpresaUpdate
    ) -> Empresa:
        """
        Actualizar una empresa existente.
        
        Valida:
        - Empresa existe
        - Razón social única si se actualiza
        - Tipo de empresa válido si se actualiza
        - Transiciones de estado válidas
        
        Args:
            db: Sesión de base de datos
            empresa_id: UUID de la empresa
            empresa_in: Datos a actualizar
            
        Returns:
            Empresa actualizada
            
        Raises:
            NotFoundException: Si la empresa no existe
            ValidationException: Si las validaciones fallan
            DuplicateException: Si razón social ya existe
        """
        # Verificar que existe
        empresa = await self.get_empresa(db, empresa_id)
        
        # Preparar datos de actualización
        update_data = empresa_in.model_dump(exclude_unset=True)
        
        # Validar razón social única si se está actualizando
        if 'razon_social' in update_data and update_data['razon_social'] != empresa.razon_social:
            existing = await self.repository.get_by_razon_social(
                db, update_data['razon_social']
            )
            if existing and existing.id != empresa_id:
                raise DuplicateException(
                    f"Ya existe una empresa con razón social '{update_data['razon_social']}'"
                )

        # Validar email único (contra Usuario.email) si se está actualizando
        if 'email_contacto' in update_data and update_data['email_contacto'] != empresa.email_contacto:
            existing_user = await usuario_repository.get_by_email(db, update_data['email_contacto'])
            if existing_user and existing_user.empresa_id != empresa_id:
                raise DuplicateException(
                    f"El correo '{update_data['email_contacto']}' ya está en uso por otro usuario"
                )

        # Validar tipo de empresa si se está actualizando
        if 'tipo_empresa' in update_data and update_data['tipo_empresa']:
            self._validate_tipo_empresa(update_data['tipo_empresa'])
        
        # Validar transición de estado si se está actualizando
        if 'estado' in update_data and update_data['estado'] != empresa.estado:
            self._validate_estado_transition(empresa.estado, update_data['estado'])
        
        # Actualizar
        updated_empresa = await self.repository.update(
            db, id=empresa_id, obj_in=update_data
        )

        if 'email_contacto' in update_data:
            linked_user = await usuario_repository.get_by_empresa_id(db, empresa_id)
            if linked_user:
                await usuario_repository.update(
                    db, id=linked_user.id, obj_in={'email': update_data['email_contacto']}
                )

        logger.info(
            f"Empresa actualizada: {empresa_id} - "
            f"NIT: {updated_empresa.nit}"
        )
        
        return updated_empresa
    
    async def delete_empresa(self, db: AsyncSession, empresa_id: UUID) -> None:
        """
        Eliminar una empresa (soft delete cambiando estado a INACTIVA).
        
        Args:
            db: Sesión de base de datos
            empresa_id: UUID de la empresa
            
        Raises:
            NotFoundException: Si la empresa no existe
            BusinessRuleException: Si tiene empleados activos
        """
        empresa = await self.get_empresa(db, empresa_id)
        
        # Verificar que no tenga empleados activos
        empleados_activos = [e for e in empresa.empleados if e.estado == "ACTIVO"]
        if empleados_activos:
            raise BusinessRuleException(
                f"No se puede desactivar la empresa porque tiene {len(empleados_activos)} "
                f"empleados activos. Desactive primero los empleados."
            )
        
        # Soft delete: cambiar estado a INACTIVA
        await self.repository.update(
            db, id=empresa_id, obj_in={'estado': 'INACTIVA'}
        )
        
        logger.info(f"Empresa desactivada: {empresa_id} - NIT: {empresa.nit}")
    
    async def list_empresas(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        nit: Optional[str] = None,
        tipo_empresa: Optional[str] = None,
        estado: Optional[str] = None,
        ciudad: Optional[str] = None,
        departamento: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[Empresa]:
        """
        Listar empresas con filtros opcionales.
        
        Args:
            db: Sesión de base de datos
            skip: Número de registros a saltar
            limit: Número máximo de registros
            nit: Filtrar por NIT (parcial)
            tipo_empresa: Filtrar por tipo de empresa
            estado: Filtrar por estado
            ciudad: Filtrar por ciudad
            departamento: Filtrar por departamento
            search: Búsqueda por NIT o razón social
            
        Returns:
            Lista de empresas
        """
        empresas = await self.repository.search(
            db,
            skip=skip,
            limit=limit,
            nit=nit,
            tipo_empresa=tipo_empresa,
            estado=estado,
            ciudad=ciudad,
            departamento=departamento,
            search_text=search
        )
        
        logger.debug(f"Listado de empresas: {len(empresas)} registros encontrados")
        
        return empresas
    
    async def activate_empresa(self, db: AsyncSession, empresa_id: UUID) -> Empresa:
        """
        Activar una empresa.
        
        Args:
            db: Sesión de base de datos
            empresa_id: UUID de la empresa
            
        Returns:
            Empresa activada
            
        Raises:
            NotFoundException: Si la empresa no existe
        """
        await self.get_empresa(db, empresa_id)  # Validar existencia
        
        updated = await self.repository.update(
            db, id=empresa_id, obj_in={'estado': 'ACTIVA'}
        )
        
        logger.info(f"Empresa activada: {empresa_id}")
        
        return updated
    
    async def deactivate_empresa(self, db: AsyncSession, empresa_id: UUID) -> Empresa:
        """
        Desactivar una empresa.
        
        Args:
            db: Sesión de base de datos
            empresa_id: UUID de la empresa
            
        Returns:
            Empresa desactivada
            
        Raises:
            NotFoundException: Si la empresa no existe
            BusinessRuleException: Si tiene empleados activos
        """
        # Usar el método delete que ya valida empleados activos
        await self.delete_empresa(db, empresa_id)
        
        # Obtener la empresa actualizada
        empresa = await self.get_empresa(db, empresa_id)
        
        return empresa
    
    # Métodos de validación privados
    
    def _validate_nit_format(self, nit: str) -> None:
        """
        Validar formato básico de NIT colombiano.
        
        Args:
            nit: NIT a validar
            
        Raises:
            ValidationException: Si el formato es inválido
        """
        # Remover guiones y espacios
        nit_clean = nit.replace("-", "").replace(" ", "")
        
        # Debe tener al menos 9 dígitos (8 + dígito verificación)
        if len(nit_clean) < 9:
            raise ValidationException(
                f"NIT '{nit}' debe tener al menos 9 dígitos"
            )
        
        # Debe ser numérico
        if not nit_clean.isdigit():
            raise ValidationException(
                f"NIT '{nit}' debe contener solo números"
            )
        
        logger.debug(f"NIT validado: {nit}")
    
    def _validate_tipo_empresa(self, tipo: str) -> None:
        """
        Validar que el tipo de empresa sea válido.
        
        Args:
            tipo: Tipo de empresa a validar
            
        Raises:
            ValidationException: Si el tipo no es válido
        """
        tipos_validos = [
            'PEQUEÑA',
            'MEDIANA',
            'GRANDE',
            'MICROEMPRESA',
            'CORPORACION',
            'MULTINACIONAL'
        ]
        
        if tipo.upper() not in tipos_validos:
            raise ValidationException(
                f"Tipo de empresa '{tipo}' no es válido. "
                f"Tipos válidos: {', '.join(tipos_validos)}"
            )
    
    def _validate_estado_transition(
        self,
        estado_actual: str,
        estado_nuevo: str
    ) -> None:
        """
        Validar que la transición de estado sea válida.
        
        Args:
            estado_actual: Estado actual de la empresa
            estado_nuevo: Estado nuevo solicitado
            
        Raises:
            BusinessRuleException: Si la transición no es válida
        """
        # Definir transiciones válidas
        transiciones_validas = {
            'ACTIVA': ['INACTIVA', 'SUSPENDIDA'],
            'INACTIVA': ['ACTIVA'],
            'SUSPENDIDA': ['ACTIVA', 'INACTIVA'],
        }
        
        estados_validos = transiciones_validas.get(estado_actual, [])
        
        if estado_nuevo not in estados_validos:
            raise BusinessRuleException(
                f"Transición de estado no válida: {estado_actual} -> {estado_nuevo}. "
                f"Transiciones válidas desde {estado_actual}: {', '.join(estados_validos)}"
            )


# Instancia singleton del servicio
empresa_service = EmpresaService()

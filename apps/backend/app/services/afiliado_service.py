"""
Servicio de lógica de negocio para Afiliados.
"""
from datetime import date
from typing import Optional, List, Dict, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from apps.backend.app.core.exceptions import (
    NotFoundException,
    ValidationException,
    BusinessRuleException,
    DuplicateException
)
from apps.backend.app.core.logging import logger
from apps.backend.app.db.repositories.afiliado_repository import afiliado_repository
from apps.backend.app.models.afiliado import Afiliado
from apps.backend.app.schemas.afiliado import AfiliadoCreate, AfiliadoUpdate


class AfiliadoService:
    """
    Servicio de lógica de negocio para gestión de afiliados.
    
    Implementa validaciones de negocio y orquesta operaciones
    del repositorio.
    """
    
    def __init__(self):
        """Inicializar servicio."""
        self.repository = afiliado_repository
    
    async def create_afiliado(
        self,
        db: AsyncSession,
        afiliado_in: AfiliadoCreate
    ) -> Afiliado:
        """
        Crear un nuevo afiliado.
        
        Valida:
        - Número de póliza único
        - Documento único
        - Fechas de póliza coherentes
        - Estado válido
        
        Args:
            db: Sesión de base de datos
            afiliado_in: Datos del afiliado a crear
            
        Returns:
            Afiliado creado
            
        Raises:
            DuplicateException: Si número de póliza o documento ya existe
            ValidationException: Si las fechas son incoherentes
        """
        # Validar número de póliza único
        existing_poliza = await self.repository.get_by_numero_poliza(
            db, afiliado_in.numero_poliza
        )
        if existing_poliza:
            logger.warning(f"Intento de crear afiliado con póliza duplicada: {afiliado_in.numero_poliza}")
            raise DuplicateException(
                f"Ya existe un afiliado con número de póliza {afiliado_in.numero_poliza}"
            )
        
        # Validar documento único
        existing_documento = await self.repository.get_by_documento(
            db, afiliado_in.tipo_documento, afiliado_in.numero_documento
        )
        if existing_documento:
            logger.warning(
                f"Intento de crear afiliado con documento duplicado: "
                f"{afiliado_in.tipo_documento} {afiliado_in.numero_documento}"
            )
            raise DuplicateException(
                f"Ya existe un afiliado con documento {afiliado_in.tipo_documento} "
                f"{afiliado_in.numero_documento}"
            )
        
        # Validar fechas de póliza
        self._validate_poliza_dates(
            afiliado_in.fecha_inicio_poliza,
            afiliado_in.fecha_fin_poliza
        )
        
        # Crear afiliado
        afiliado_data = afiliado_in.model_dump()
        afiliado = await self.repository.create(db, afiliado_data)
        
        logger.info(
            f"Afiliado creado exitosamente: {afiliado.id} - "
            f"Póliza: {afiliado.numero_poliza}"
        )
        
        return afiliado
    
    async def get_afiliado(self, db: AsyncSession, afiliado_id: UUID) -> Afiliado:
        """
        Obtener afiliado por ID.
        
        Args:
            db: Sesión de base de datos
            afiliado_id: UUID del afiliado
            
        Returns:
            Afiliado encontrado
            
        Raises:
            NotFoundException: Si el afiliado no existe
        """
        afiliado = await self.repository.get_by_id(db, afiliado_id)
        
        if not afiliado:
            logger.warning(f"Afiliado no encontrado: {afiliado_id}")
            raise NotFoundException(f"Afiliado con ID {afiliado_id} no encontrado")
        
        return afiliado
    
    async def update_afiliado(
        self,
        db: AsyncSession,
        afiliado_id: UUID,
        afiliado_in: AfiliadoUpdate
    ) -> Afiliado:
        """
        Actualizar un afiliado existente.
        
        Valida:
        - Afiliado existe
        - Fechas de póliza coherentes si se actualizan
        - Transiciones de estado válidas
        
        Args:
            db: Sesión de base de datos
            afiliado_id: UUID del afiliado
            afiliado_in: Datos a actualizar
            
        Returns:
            Afiliado actualizado
            
        Raises:
            NotFoundException: Si el afiliado no existe
            ValidationException: Si las validaciones fallan
        """
        # Verificar que existe
        afiliado = await self.get_afiliado(db, afiliado_id)
        
        # Preparar datos de actualización
        update_data = afiliado_in.model_dump(exclude_unset=True)
        
        # Validar fechas si se están actualizando
        if 'fecha_inicio_poliza' in update_data or 'fecha_fin_poliza' in update_data:
            inicio = update_data.get('fecha_inicio_poliza', afiliado.fecha_inicio_poliza)
            fin = update_data.get('fecha_fin_poliza', afiliado.fecha_fin_poliza)
            self._validate_poliza_dates(inicio, fin)
        
        # Validar transición de estado si se está actualizando
        if 'estado' in update_data and update_data['estado'] != afiliado.estado:
            self._validate_estado_transition(afiliado.estado, update_data['estado'])
        
        # Actualizar
        updated_afiliado = await self.repository.update(
            db, id=afiliado_id, obj_in=update_data
        )
        
        logger.info(
            f"Afiliado actualizado: {afiliado_id} - "
            f"Póliza: {updated_afiliado.numero_poliza}"
        )
        
        return updated_afiliado
    
    async def delete_afiliado(self, db: AsyncSession, afiliado_id: UUID) -> None:
        """
        Eliminar un afiliado (soft delete cambiando estado a INACTIVO).
        
        Args:
            db: Sesión de base de datos
            afiliado_id: UUID del afiliado
            
        Raises:
            NotFoundException: Si el afiliado no existe
        """
        afiliado = await self.get_afiliado(db, afiliado_id)
        
        # Soft delete: cambiar estado a INACTIVO
        await self.repository.update(
            db, id=afiliado_id, obj_in={'estado': 'INACTIVO'}
        )
        
        logger.info(f"Afiliado desactivado: {afiliado_id} - Póliza: {afiliado.numero_poliza}")
    
    async def list_afiliados(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        numero_poliza: Optional[str] = None,
        tipo_poliza: Optional[str] = None,
        estado: Optional[str] = None,
        tipo_documento: Optional[str] = None,
        numero_documento: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[Afiliado]:
        """
        Listar afiliados con filtros opcionales.
        
        Args:
            db: Sesión de base de datos
            skip: Número de registros a saltar
            limit: Número máximo de registros
            numero_poliza: Filtrar por número de póliza
            tipo_poliza: Filtrar por tipo de póliza
            estado: Filtrar por estado
            tipo_documento: Filtrar por tipo de documento
            numero_documento: Filtrar por número de documento
            search: Búsqueda por nombre o apellido
            
        Returns:
            Lista de afiliados
        """
        afiliados = await self.repository.search(
            db,
            skip=skip,
            limit=limit,
            numero_poliza=numero_poliza,
            tipo_poliza=tipo_poliza,
            estado=estado,
            tipo_documento=tipo_documento,
            numero_documento=numero_documento,
            search_text=search
        )
        
        logger.debug(f"Listado de afiliados: {len(afiliados)} registros encontrados")
        
        return afiliados
    
    async def activate_afiliado(self, db: AsyncSession, afiliado_id: UUID) -> Afiliado:
        """
        Activar un afiliado.
        
        Args:
            db: Sesión de base de datos
            afiliado_id: UUID del afiliado
            
        Returns:
            Afiliado activado
            
        Raises:
            NotFoundException: Si el afiliado no existe
            BusinessRuleException: Si la póliza no está vigente
        """
        afiliado = await self.get_afiliado(db, afiliado_id)
        
        # Validar que la póliza esté vigente
        if not self._is_poliza_vigente(afiliado.fecha_inicio_poliza, afiliado.fecha_fin_poliza):
            raise BusinessRuleException(
                f"No se puede activar afiliado con póliza vencida. "
                f"Vigencia: {afiliado.fecha_inicio_poliza} - {afiliado.fecha_fin_poliza}"
            )
        
        updated = await self.repository.update(
            db, id=afiliado_id, obj_in={'estado': 'ACTIVO'}
        )
        
        logger.info(f"Afiliado activado: {afiliado_id}")
        
        return updated
    
    async def deactivate_afiliado(self, db: AsyncSession, afiliado_id: UUID) -> Afiliado:
        """
        Desactivar un afiliado.
        
        Args:
            db: Sesión de base de datos
            afiliado_id: UUID del afiliado
            
        Returns:
            Afiliado desactivado
            
        Raises:
            NotFoundException: Si el afiliado no existe
        """
        await self.get_afiliado(db, afiliado_id)  # Validar existencia
        
        updated = await self.repository.update(
            db, id=afiliado_id, obj_in={'estado': 'INACTIVO'}
        )
        
        logger.info(f"Afiliado desactivado: {afiliado_id}")
        
        return updated
    
    # Métodos de validación privados
    
    def _validate_poliza_dates(
        self,
        fecha_inicio: date,
        fecha_fin: Optional[date]
    ) -> None:
        """
        Validar coherencia de fechas de póliza.
        
        Args:
            fecha_inicio: Fecha de inicio de póliza
            fecha_fin: Fecha de fin de póliza
            
        Raises:
            ValidationException: Si las fechas son incoherentes
        """
        if fecha_fin and fecha_fin < fecha_inicio:
            raise ValidationException(
                "La fecha de fin de póliza no puede ser anterior a la fecha de inicio"
            )
        
        # La fecha de inicio no puede ser muy antigua (ej: más de 5 años atrás)
        from datetime import timedelta
        cinco_anios_atras = date.today() - timedelta(days=365*5)
        
        if fecha_inicio < cinco_anios_atras:
            logger.warning(f"Póliza con fecha de inicio antigua: {fecha_inicio}")
    
    def _is_poliza_vigente(
        self,
        fecha_inicio: date,
        fecha_fin: Optional[date]
    ) -> bool:
        """
        Verificar si una póliza está vigente.
        
        Args:
            fecha_inicio: Fecha de inicio de póliza
            fecha_fin: Fecha de fin de póliza
            
        Returns:
            True si la póliza está vigente
        """
        hoy = date.today()
        
        # La póliza debe haber iniciado
        if fecha_inicio > hoy:
            return False
        
        # Si tiene fecha de fin, no debe haber expirado
        if fecha_fin and fecha_fin < hoy:
            return False
        
        return True
    
    def _validate_estado_transition(
        self,
        estado_actual: str,
        estado_nuevo: str
    ) -> None:
        """
        Validar que la transición de estado sea válida.
        
        Args:
            estado_actual: Estado actual del afiliado
            estado_nuevo: Estado nuevo solicitado
            
        Raises:
            BusinessRuleException: Si la transición no es válida
        """
        # Definir transiciones válidas
        transiciones_validas = {
            'ACTIVO': ['INACTIVO', 'SUSPENDIDO'],
            'INACTIVO': ['ACTIVO'],
            'SUSPENDIDO': ['ACTIVO', 'INACTIVO'],
        }
        
        estados_validos = transiciones_validas.get(estado_actual, [])
        
        if estado_nuevo not in estados_validos:
            raise BusinessRuleException(
                f"Transición de estado no válida: {estado_actual} -> {estado_nuevo}. "
                f"Transiciones válidas desde {estado_actual}: {', '.join(estados_validos)}"
            )


# Instancia singleton del servicio
afiliado_service = AfiliadoService()

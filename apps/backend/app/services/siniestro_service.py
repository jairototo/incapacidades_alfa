"""
Servicio de lógica de negocio para Siniestros.
"""
from datetime import date, datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.repositories.siniestro_repository import siniestro_repository
from app.db.repositories.empleado_repository import empleado_repository
from app.db.repositories.empresa_repository import empresa_repository
from app.services.historial_estado_service import historial_estado_service
from app.schemas.siniestro import SiniestroCreate, SiniestroUpdate
from app.models.siniestro import Siniestro
from app.models.empleado import Empleado
from app.models.empresa import Empresa
from app.utils.enums import (
    TipoSiniestro,
    EstadoSiniestro,
    EstadoEmpleado,
    EstadoEmpresa
)
from app.core.exceptions import (
    NotFoundException,
    ValidationException,
    BusinessRuleException
)


class SiniestroService:
    """Servicio para gestión de siniestros con workflow de estados."""
    
    # Estados permitidos para transiciones
    ALLOWED_TRANSITIONS = {
        EstadoSiniestro.REPORTADO: [EstadoSiniestro.EN_INVESTIGACION, EstadoSiniestro.ANULADO],
        EstadoSiniestro.EN_INVESTIGACION: [EstadoSiniestro.CERRADO, EstadoSiniestro.ANULADO],
        EstadoSiniestro.CERRADO: [],  # Estado final, no hay transiciones
        EstadoSiniestro.ANULADO: []   # Estado final, no hay transiciones
    }
    
    def __init__(self):
        self.repository = siniestro_repository
        self.empleado_repository = empleado_repository
        self.empresa_repository = empresa_repository
    
    async def create_siniestro(
        self,
        db: AsyncSession,
        siniestro_data: SiniestroCreate
    ) -> Siniestro:
        """
        Crear un nuevo siniestro con validaciones de negocio.
        
        Validaciones:
        - El empleado debe existir y estar ACTIVO
        - La empresa debe existir y estar ACTIVA
        - El empleado debe pertenecer a la empresa
        - La fecha del siniestro no puede ser futura
        - Genera número único automáticamente
        
        Args:
            db: Sesión de base de datos
            siniestro_data: Datos del siniestro a crear
            
        Returns:
            Siniestro creado
            
        Raises:
            NotFoundException: Si empleado o empresa no existen
            ValidationException: Si las validaciones fallan
        """
        # Validar empleado
        empleado = await self.empleado_repository.get_by_id(db, siniestro_data.empleado_id)
        if not empleado:
            raise NotFoundException(f"Empleado con ID {siniestro_data.empleado_id} no encontrado")
        
        if empleado.estado != EstadoEmpleado.ACTIVO:
            raise ValidationException(
                f"El empleado {empleado.nombres} {empleado.apellidos} no está ACTIVO. "
                f"Estado actual: {empleado.estado.value}"
            )
        
        # Validar empresa
        empresa = await self.empresa_repository.get_by_id(db, siniestro_data.empresa_id)
        if not empresa:
            raise NotFoundException(f"Empresa con ID {siniestro_data.empresa_id} no encontrada")
        
        if empresa.estado != EstadoEmpresa.ACTIVA:
            raise ValidationException(
                f"La empresa {empresa.razon_social} no está ACTIVA. "
                f"Estado actual: {empresa.estado.value}"
            )
        
        # Validar que el empleado pertenece a la empresa
        if empleado.empresa_id != siniestro_data.empresa_id:
            raise ValidationException(
                f"El empleado {empleado.nombres} {empleado.apellidos} no pertenece a la empresa {empresa.razon_social}"
            )
        
        # Validar fecha del siniestro
        if siniestro_data.fecha_siniestro > date.today():
            raise ValidationException("La fecha del siniestro no puede ser futura")
        
        # Generar número único
        numero_siniestro = await self._generar_numero_siniestro(db, siniestro_data.fecha_siniestro)
        
        # Crear siniestro
        siniestro_dict = siniestro_data.model_dump(exclude_unset=True)
        siniestro_dict["numero_siniestro"] = numero_siniestro
        siniestro_dict["estado"] = EstadoSiniestro.REPORTADO
        siniestro_dict["fecha_reporte"] = datetime.utcnow()
        
        return await self.repository.create(db, siniestro_dict)
    
    async def update_siniestro(
        self,
        db: AsyncSession,
        siniestro_id: UUID,
        siniestro_data: SiniestroUpdate
    ) -> Siniestro:
        """
        Actualizar un siniestro existente.
        
        Restricciones:
        - No se pueden modificar siniestros CERRADOS o ANULADOS
        - No se puede cambiar empleado o empresa
        
        Args:
            db: Sesión de base de datos
            siniestro_id: ID del siniestro
            siniestro_data: Datos a actualizar
            
        Returns:
            Siniestro actualizado
            
        Raises:
            NotFoundException: Si el siniestro no existe
            BusinessRuleException: Si el siniestro no se puede modificar
        """
        siniestro = await self.repository.get_by_id(db, siniestro_id)
        if not siniestro:
            raise NotFoundException(f"Siniestro con ID {siniestro_id} no encontrado")
        
        # Validar que no esté en estado final
        if siniestro.estado in [EstadoSiniestro.CERRADO, EstadoSiniestro.ANULADO]:
            raise BusinessRuleException(
                f"No se puede modificar un siniestro en estado {siniestro.estado.value}"
            )
        
        # No permitir cambiar empleado o empresa
        update_data = siniestro_data.model_dump(exclude_unset=True)
        if "empleado_id" in update_data or "empresa_id" in update_data:
            raise BusinessRuleException("No se puede cambiar el empleado o empresa de un siniestro")
        
        return await self.repository.update(db, id=siniestro_id, obj_in=update_data)
    
    async def get_siniestro(
        self,
        db: AsyncSession,
        siniestro_id: UUID
    ) -> Siniestro:
        """
        Obtener un siniestro por ID.
        
        Args:
            db: Sesión de base de datos
            siniestro_id: ID del siniestro
            
        Returns:
            Siniestro encontrado
            
        Raises:
            NotFoundException: Si el siniestro no existe
        """
        siniestro = await self.repository.get_by_id(db, siniestro_id)
        if not siniestro:
            raise NotFoundException(f"Siniestro con ID {siniestro_id} no encontrado")
        return siniestro
    
    async def list_siniestros(
        self,
        db: AsyncSession,
        tipo: Optional[TipoSiniestro] = None,
        estado: Optional[EstadoSiniestro] = None,
        empresa_id: Optional[UUID] = None,
        empleado_id: Optional[UUID] = None,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
        numero: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Siniestro]:
        """
        Listar siniestros con filtros opcionales.
        
        Args:
            db: Sesión de base de datos
            tipo: Filtrar por tipo
            estado: Filtrar por estado
            empresa_id: Filtrar por empresa
            empleado_id: Filtrar por empleado
            fecha_desde: Fecha mínima
            fecha_hasta: Fecha máxima
            numero: Búsqueda en número
            skip: Registros a saltar
            limit: Máximo de registros
            
        Returns:
            Lista de siniestros
        """
        return await self.repository.search(
            db,
            tipo=tipo,
            estado=estado,
            empresa_id=empresa_id,
            empleado_id=empleado_id,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            numero=numero,
            skip=skip,
            limit=limit
        )
    
    async def reportar_siniestro(
        self,
        db: AsyncSession,
        siniestro_id: UUID,
        usuario_id: Optional[UUID] = None
    ) -> Siniestro:
        """
        Cambiar siniestro de REPORTADO a EN_INVESTIGACION.
        
        Args:
            db: Sesión de base de datos
            siniestro_id: ID del siniestro
            usuario_id: ID del usuario que reporta (opcional)
            
        Returns:
            Siniestro actualizado
            
        Raises:
            NotFoundException: Si el siniestro no existe
            BusinessRuleException: Si la transición no es válida
        """
        siniestro = await self.repository.get_by_id(db, siniestro_id)
        if not siniestro:
            raise NotFoundException(f"Siniestro con ID {siniestro_id} no encontrado")
        
        # Validar transición de estado
        self._validate_state_transition(
            siniestro.estado,
            EstadoSiniestro.EN_INVESTIGACION
        )
        
        # Actualizar siniestro
        estado_anterior = siniestro.estado
        siniestro_actualizado = await self.repository.update(
            db,
            id=siniestro_id,
            obj_in={"estado": EstadoSiniestro.EN_INVESTIGACION}
        )
        
        # Registrar en historial
        await historial_estado_service.create_historial_entry(
            db=db,
            entity_type="siniestro",
            entity_id=siniestro_id,
            estado_anterior=estado_anterior.value,
            estado_nuevo=EstadoSiniestro.EN_INVESTIGACION.value,
            observacion="Siniestro enviado a investigación",
            cambiado_por_id=usuario_id
        )
        
        return siniestro_actualizado
    
    async def cerrar_siniestro(
        self,
        db: AsyncSession,
        siniestro_id: UUID,
        observaciones: Optional[str] = None,
        usuario_id: Optional[UUID] = None
    ) -> Siniestro:
        """
        Cerrar un siniestro (estado final).
        
        Args:
            db: Sesión de base de datos
            siniestro_id: ID del siniestro
            observaciones: Observaciones de cierre
            usuario_id: ID del usuario que cierra (opcional)
            
        Returns:
            Siniestro actualizado
            
        Raises:
            NotFoundException: Si el siniestro no existe
            BusinessRuleException: Si la transición no es válida
        """
        siniestro = await self.repository.get_by_id(db, siniestro_id)
        if not siniestro:
            raise NotFoundException(f"Siniestro con ID {siniestro_id} no encontrado")
        
        # Validar transición de estado
        self._validate_state_transition(
            siniestro.estado,
            EstadoSiniestro.CERRADO
        )
        
        update_data = {"estado": EstadoSiniestro.CERRADO}
        if observaciones:
            update_data["observaciones"] = observaciones
        
        # Actualizar siniestro
        estado_anterior = siniestro.estado
        siniestro_actualizado = await self.repository.update(db, id=siniestro_id, obj_in=update_data)
        
        # Registrar en historial
        await historial_estado_service.create_historial_entry(
            db=db,
            entity_type="siniestro",
            entity_id=siniestro_id,
            estado_anterior=estado_anterior.value,
            estado_nuevo=EstadoSiniestro.CERRADO.value,
            observacion=f"Siniestro cerrado{': ' + observaciones if observaciones else ''}",
            cambiado_por_id=usuario_id
        )
        
        return siniestro_actualizado
    
    async def anular_siniestro(
        self,
        db: AsyncSession,
        siniestro_id: UUID,
        motivo: str,
        usuario_id: Optional[UUID] = None
    ) -> Siniestro:
        """
        Anular un siniestro (estado final).
        
        Args:
            db: Sesión de base de datos
            siniestro_id: ID del siniestro
            motivo: Motivo de la anulación (requerido)
            usuario_id: ID del usuario que anula (opcional)
            
        Returns:
            Siniestro actualizado
            
        Raises:
            NotFoundException: Si el siniestro no existe
            ValidationException: Si no se proporciona motivo
            BusinessRuleException: Si la transición no es válida
        """
        if not motivo or len(motivo.strip()) < 10:
            raise ValidationException("El motivo de anulación debe tener al menos 10 caracteres")
        
        siniestro = await self.repository.get_by_id(db, siniestro_id)
        if not siniestro:
            raise NotFoundException(f"Siniestro con ID {siniestro_id} no encontrado")
        
        # Validar que no esté ya cerrado
        if siniestro.estado == EstadoSiniestro.CERRADO:
            raise BusinessRuleException("No se puede anular un siniestro ya CERRADO")
        
        # Validar transición de estado
        self._validate_state_transition(
            siniestro.estado,
            EstadoSiniestro.ANULADO
        )
        
        # Actualizar siniestro
        estado_anterior = siniestro.estado
        siniestro_actualizado = await self.repository.update(
            db,
            id=siniestro_id,
            obj_in={
                "estado": EstadoSiniestro.ANULADO,
                "observaciones": f"ANULADO: {motivo}"
            }
        )
        
        # Registrar en historial
        await historial_estado_service.create_historial_entry(
            db=db,
            entity_type="siniestro",
            entity_id=siniestro_id,
            estado_anterior=estado_anterior.value,
            estado_nuevo=EstadoSiniestro.ANULADO.value,
            observacion=f"Siniestro anulado: {motivo}",
            cambiado_por_id=usuario_id
        )
        
        return siniestro_actualizado
    
    async def get_incapacidades_siniestro(
        self,
        db: AsyncSession,
        siniestro_id: UUID
    ) -> List[Any]:
        """
        Obtener todas las incapacidades asociadas a un siniestro.
        
        Args:
            db: Sesión de base de datos
            siniestro_id: ID del siniestro
            
        Returns:
            Lista de incapacidades del siniestro
            
        Raises:
            NotFoundException: Si el siniestro no existe
        """
        siniestro = await self.repository.get_by_id(db, siniestro_id)
        if not siniestro:
            raise NotFoundException(f"Siniestro con ID {siniestro_id} no encontrado")
        
        # La relación ya está cargada con lazy="selectin"
        return siniestro.incapacidades
    
    def _validate_state_transition(
        self,
        current_state: EstadoSiniestro,
        new_state: EstadoSiniestro
    ) -> None:
        """
        Validar que la transición de estado sea válida.
        
        Args:
            current_state: Estado actual
            new_state: Estado deseado
            
        Raises:
            BusinessRuleException: Si la transición no es permitida
        """
        allowed_states = self.ALLOWED_TRANSITIONS.get(current_state, [])
        
        if new_state not in allowed_states:
            raise BusinessRuleException(
                f"No se puede cambiar de {current_state.value} a {new_state.value}. "
                f"Transiciones permitidas: {[s.value for s in allowed_states]}"
            )
    
    async def _generar_numero_siniestro(
        self,
        db: AsyncSession,
        fecha_siniestro: date
    ) -> str:
        """
        Generar número único de siniestro con formato SIN-YYYYMMDD-NNNN.
        
        Args:
            db: Sesión de base de datos
            fecha_siniestro: Fecha del siniestro
            
        Returns:
            Número de siniestro generado
        """
        # Formato: SIN-YYYYMMDD-NNNN
        fecha_str = fecha_siniestro.strftime("%Y%m%d")
        prefijo = f"SIN-{fecha_str}"
        
        # Buscar el último número del día
        query = select(func.max(Siniestro.numero_siniestro)).where(
            Siniestro.numero_siniestro.like(f"{prefijo}%")
        )
        result = await db.execute(query)
        ultimo_numero = result.scalar()
        
        if ultimo_numero:
            # Extraer el número secuencial y sumar 1
            secuencial = int(ultimo_numero.split("-")[-1]) + 1
        else:
            # Primer siniestro del día
            secuencial = 1
        
        return f"{prefijo}-{secuencial:04d}"


# Singleton instance
siniestro_service = SiniestroService()

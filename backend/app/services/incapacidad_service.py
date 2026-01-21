"""
Service para lógica de negocio de Incapacidad con workflow de estados.
"""
from datetime import date, datetime
from typing import List, Optional, Dict
from uuid import UUID
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    NotFoundException,
    BadRequestException,
    InvalidStateException,
    ConflictException
)
from app.db.repositories.incapacidad_repository import incapacidad_repository
from app.db.repositories.empleado_repository import empleado_repository
from app.db.repositories.afiliado_repository import afiliado_repository
from app.db.repositories.empresa_repository import empresa_repository
from app.services.historial_estado_service import historial_estado_service
from app.models.incapacidad import Incapacidad
from app.schemas.incapacidad import IncapacidadCreate, IncapacidadUpdate
from app.utils.enums import (
    EstadoIncapacidad,
    TipoIncapacidad,
    EstadoEmpleado,
    EstadoAfiliado,
    EstadoEmpresa,
    Prioridad
)


# Matriz de transiciones de estados permitidas
ALLOWED_TRANSITIONS: Dict[EstadoIncapacidad, List[EstadoIncapacidad]] = {
    EstadoIncapacidad.RADICADA: [
        EstadoIncapacidad.EN_AUDITORIA,
        EstadoIncapacidad.CANCELADA
    ],
    EstadoIncapacidad.EN_AUDITORIA: [
        EstadoIncapacidad.OBSERVADA,
        EstadoIncapacidad.APROBADA,
        EstadoIncapacidad.RECHAZADA,
        EstadoIncapacidad.CANCELADA
    ],
    EstadoIncapacidad.OBSERVADA: [
        EstadoIncapacidad.EN_AUDITORIA,
        EstadoIncapacidad.RECHAZADA,
        EstadoIncapacidad.CANCELADA
    ],
    EstadoIncapacidad.APROBADA: [
        EstadoIncapacidad.EN_PAGO,
        EstadoIncapacidad.CANCELADA
    ],
    EstadoIncapacidad.RECHAZADA: [
        EstadoIncapacidad.CANCELADA
    ],
    EstadoIncapacidad.EN_PAGO: [
        EstadoIncapacidad.PAGADA,
        EstadoIncapacidad.CANCELADA
    ],
    EstadoIncapacidad.PAGADA: [
        EstadoIncapacidad.CANCELADA
    ],
    EstadoIncapacidad.CANCELADA: []
}


class IncapacidadService:
    """Service para operaciones de negocio de Incapacidad."""

    def __init__(self):
        """Inicializa el service con los repositories necesarios."""
        self.repository = incapacidad_repository
        self.empleado_repository = empleado_repository
        self.afiliado_repository = afiliado_repository
        self.empresa_repository = empresa_repository

    async def create_incapacidad(
        self,
        db: AsyncSession,
        incapacidad_data: IncapacidadCreate,
        usuario_id: Optional[UUID] = None
    ) -> Incapacidad:
        """
        Crea una nueva incapacidad con validaciones.
        
        Args:
            db: Sesión de base de datos
            incapacidad_data: Datos de la incapacidad
            usuario_id: ID del usuario que radica (opcional por ahora)
            
        Returns:
            Incapacidad creada
            
        Raises:
            NotFoundException: Si empleado/afiliado/empresa no existe
            BadRequestException: Si las validaciones fallan
            ConflictException: Si el número ya existe
        """
        # Validar tipo y relaciones
        if incapacidad_data.tipo == TipoIncapacidad.ARL:
            await self._validate_incapacidad_arl(
                db,
                incapacidad_data.empleado_id,
                incapacidad_data.empresa_id
            )
        elif incapacidad_data.tipo == TipoIncapacidad.SALUD:
            await self._validate_incapacidad_salud(
                db,
                incapacidad_data.afiliado_id
            )
        
        # Validar fechas
        self._validate_fechas(
            incapacidad_data.fecha_inicio,
            incapacidad_data.fecha_fin
        )
        
        # Generar número único de incapacidad
        numero = await self._generar_numero_incapacidad(db, incapacidad_data.tipo)
        
        # Calcular días totales
        dias_totales = (incapacidad_data.fecha_fin - incapacidad_data.fecha_inicio).days + 1
        
        # Preparar datos
        incapacidad_dict = incapacidad_data.model_dump(exclude_unset=True)
        incapacidad_dict['numero'] = numero
        incapacidad_dict['dias_totales'] = dias_totales
        incapacidad_dict['estado'] = EstadoIncapacidad.RADICADA
        incapacidad_dict['fecha_radicacion'] = datetime.utcnow()
        
        if usuario_id:
            incapacidad_dict['radicado_por_id'] = usuario_id
        
        # Crear incapacidad
        return await self.repository.create(db, incapacidad_dict)

    async def get_incapacidad(
        self,
        db: AsyncSession,
        incapacidad_id: UUID
    ) -> Incapacidad:
        """
        Obtiene una incapacidad por ID.
        
        Args:
            db: Sesión de base de datos
            incapacidad_id: ID de la incapacidad
            
        Returns:
            Incapacidad encontrada
            
        Raises:
            NotFoundException: Si la incapacidad no existe
        """
        incapacidad = await self.repository.get_by_id(db, incapacidad_id)
        if not incapacidad:
            raise NotFoundException(f"Incapacidad con ID {incapacidad_id} no encontrada")
        return incapacidad

    async def list_incapacidades(
        self,
        db: AsyncSession,
        tipo: Optional[TipoIncapacidad] = None,
        estado: Optional[EstadoIncapacidad] = None,
        numero: Optional[str] = None,
        empleado_id: Optional[UUID] = None,
        afiliado_id: Optional[UUID] = None,
        empresa_id: Optional[UUID] = None,
        fecha_inicio_desde: Optional[date] = None,
        fecha_inicio_hasta: Optional[date] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Incapacidad]:
        """
        Lista incapacidades con filtros opcionales.
        
        Args:
            db: Sesión de base de datos
            tipo: Filtrar por tipo
            estado: Filtrar por estado
            numero: Filtrar por número de incapacidad
            afiliado_id: Filtrar por afiliado
            empresa_id: Filtrar por empresa
            fecha_inicio_desde: Fecha mínima
            fecha_inicio_hasta: Fecha máxima
            skip: Registros a saltar
            limit: Máximo de registros
            
        Returns:
            Lista de incapacidades
        """
        return await self.repository.search(
            db,
            tipo=tipo,
            estado=estado,
            numero=numero,
            empleado_id=empleado_id,
            afiliado_id=afiliado_id,
            empresa_id=empresa_id,
            fecha_inicio_desde=fecha_inicio_desde,
            fecha_inicio_hasta=fecha_inicio_hasta,
            skip=skip,
            limit=limit
        )

    async def update_incapacidad(
        self,
        db: AsyncSession,
        incapacidad_id: UUID,
        incapacidad_data: IncapacidadUpdate
    ) -> Incapacidad:
        """
        Actualiza una incapacidad.
        
        Args:
            db: Sesión de base de datos
            incapacidad_id: ID de la incapacidad
            incapacidad_data: Datos a actualizar
            
        Returns:
            Incapacidad actualizada
            
        Raises:
            NotFoundException: Si la incapacidad no existe
            InvalidStateException: Si el estado no permite actualizaciones
        """
        incapacidad = await self.get_incapacidad(db, incapacidad_id)
        
        # Solo permitir actualizaciones en ciertos estados
        estados_editables = [
            EstadoIncapacidad.RADICADA,
            EstadoIncapacidad.OBSERVADA
        ]
        
        if incapacidad.estado not in estados_editables:
            raise InvalidStateException(
                f"No se puede actualizar una incapacidad en estado {incapacidad.estado}. "
                f"Estados editables: {', '.join([e.value for e in estados_editables])}"
            )
        
        # Validar fechas si se actualizan
        update_data = incapacidad_data.model_dump(exclude_unset=True)
        
        if 'fecha_inicio' in update_data or 'fecha_fin' in update_data:
            fecha_inicio = update_data.get('fecha_inicio', incapacidad.fecha_inicio)
            fecha_fin = update_data.get('fecha_fin', incapacidad.fecha_fin)
            self._validate_fechas(fecha_inicio, fecha_fin)
            
            # Recalcular días totales
            update_data['dias_totales'] = (fecha_fin - fecha_inicio).days + 1
        
        return await self.repository.update(db, id=incapacidad_id, obj_in=update_data)

    async def radicar_incapacidad(
        self,
        db: AsyncSession,
        incapacidad_id: UUID,
        usuario_id: Optional[UUID] = None
    ) -> Incapacidad:
        """
        Radica una incapacidad (pasa a estado EN_AUDITORIA).
        
        Args:
            db: Sesión de base de datos
            incapacidad_id: ID de la incapacidad
            usuario_id: ID del usuario que radica
            
        Returns:
            Incapacidad radicada
        """
        incapacidad = await self.get_incapacidad(db, incapacidad_id)
        
        # Validar transición de estado
        await self._validate_state_transition(
            incapacidad.estado,
            EstadoIncapacidad.EN_AUDITORIA
        )
        
        update_data = {
            'estado': EstadoIncapacidad.EN_AUDITORIA
        }
        
        if usuario_id:
            update_data['radicado_por_id'] = usuario_id
        
        # Actualizar incapacidad
        estado_anterior = incapacidad.estado
        incapacidad_actualizada = await self.repository.update(db, id=incapacidad_id, obj_in=update_data)
        
        # Registrar en historial
        await historial_estado_service.create_historial_entry(
            db=db,
            entity_type="incapacidad",
            entity_id=incapacidad_id,
            estado_anterior=estado_anterior.value if estado_anterior else None,
            estado_nuevo=EstadoIncapacidad.EN_AUDITORIA.value,
            observacion="Incapacidad radicada para auditoría",
            cambiado_por_id=usuario_id
        )
        
        return incapacidad_actualizada

    async def auditar_incapacidad(
        self,
        db: AsyncSession,
        incapacidad_id: UUID,
        accion: str,
        observaciones: str,
        usuario_id: Optional[UUID] = None
    ) -> Incapacidad:
        """
        Audita una incapacidad.
        
        Args:
            db: Sesión de base de datos
            incapacidad_id: ID de la incapacidad
            accion: SOLICITAR_INFORMACION, APROBAR_PARA_PAGO, RECHAZAR
            observaciones: Observaciones de la auditoría
            usuario_id: ID del auditor
            
        Returns:
            Incapacidad auditada
        """
        incapacidad = await self.get_incapacidad(db, incapacidad_id)
        
        if incapacidad.estado != EstadoIncapacidad.EN_AUDITORIA:
            raise InvalidStateException(
                f"Solo se pueden auditar incapacidades en estado EN_AUDITORIA. "
                f"Estado actual: {incapacidad.estado}"
            )
        
        nuevo_estado = None
        update_data = {
            'observaciones': observaciones,
            'fecha_auditoria': datetime.utcnow()
        }
        
        if usuario_id:
            update_data['auditado_por_id'] = usuario_id
        
        if accion == "SOLICITAR_INFORMACION":
            nuevo_estado = EstadoIncapacidad.OBSERVADA
        elif accion == "APROBAR_PARA_PAGO":
            nuevo_estado = EstadoIncapacidad.APROBADA
            update_data['fecha_aprobacion'] = datetime.utcnow()
            if usuario_id:
                update_data['aprobado_por_id'] = usuario_id
        elif accion == "RECHAZAR":
            nuevo_estado = EstadoIncapacidad.RECHAZADA
            update_data['fecha_rechazo'] = datetime.utcnow()
            update_data['motivo_rechazo'] = observaciones
        else:
            raise BadRequestException(f"Acción de auditoría inválida: {accion}")
        
        await self._validate_state_transition(incapacidad.estado, nuevo_estado)
        update_data['estado'] = nuevo_estado
        
        # Actualizar incapacidad
        estado_anterior = incapacidad.estado
        incapacidad_actualizada = await self.repository.update(db, id=incapacidad_id, obj_in=update_data)
        
        # Registrar en historial
        await historial_estado_service.create_historial_entry(
            db=db,
            entity_type="incapacidad",
            entity_id=incapacidad_id,
            estado_anterior=estado_anterior.value,
            estado_nuevo=nuevo_estado.value,
            observacion=f"Auditoría: {accion} - {observaciones}",
            cambiado_por_id=usuario_id
        )
        
        return incapacidad_actualizada

    async def aprobar_incapacidad(
        self,
        db: AsyncSession,
        incapacidad_id: UUID,
        usuario_id: Optional[UUID] = None
    ) -> Incapacidad:
        """
        Aprueba una incapacidad para pago.
        
        Args:
            db: Sesión de base de datos
            incapacidad_id: ID de la incapacidad
            usuario_id: ID del aprobador
            
        Returns:
            Incapacidad aprobada
        """
        incapacidad = await self.get_incapacidad(db, incapacidad_id)
        
        await self._validate_state_transition(
            incapacidad.estado,
            EstadoIncapacidad.APROBADA
        )
        
        update_data = {
            'estado': EstadoIncapacidad.APROBADA,
            'fecha_aprobacion': datetime.utcnow()
        }
        
        if usuario_id:
            update_data['aprobado_por_id'] = usuario_id
        
        # Actualizar incapacidad
        estado_anterior = incapacidad.estado
        incapacidad_actualizada = await self.repository.update(db, id=incapacidad_id, obj_in=update_data)
        
        # Registrar en historial
        await historial_estado_service.create_historial_entry(
            db=db,
            entity_type="incapacidad",
            entity_id=incapacidad_id,
            estado_anterior=estado_anterior.value,
            estado_nuevo=EstadoIncapacidad.APROBADA.value,
            observacion="Incapacidad aprobada para pago",
            cambiado_por_id=usuario_id
        )
        
        return incapacidad_actualizada

    async def rechazar_incapacidad(
        self,
        db: AsyncSession,
        incapacidad_id: UUID,
        motivo: str,
        usuario_id: Optional[UUID] = None
    ) -> Incapacidad:
        """
        Rechaza una incapacidad.
        
        Args:
            db: Sesión de base de datos
            incapacidad_id: ID de la incapacidad
            motivo: Motivo del rechazo
            usuario_id: ID del usuario que rechaza
            
        Returns:
            Incapacidad rechazada
        """
        incapacidad = await self.get_incapacidad(db, incapacidad_id)
        
        await self._validate_state_transition(
            incapacidad.estado,
            EstadoIncapacidad.RECHAZADA
        )
        
        update_data = {
            'estado': EstadoIncapacidad.RECHAZADA,
            'motivo_rechazo': motivo,
            'fecha_rechazo': datetime.utcnow()
        }
        
        if usuario_id:
            update_data['auditado_por_id'] = usuario_id
        
        # Actualizar incapacidad
        estado_anterior = incapacidad.estado
        incapacidad_actualizada = await self.repository.update(db, id=incapacidad_id, obj_in=update_data)
        
        # Registrar en historial
        await historial_estado_service.create_historial_entry(
            db=db,
            entity_type="incapacidad",
            entity_id=incapacidad_id,
            estado_anterior=estado_anterior.value,
            estado_nuevo=EstadoIncapacidad.RECHAZADA.value,
            observacion=f"Incapacidad rechazada: {motivo}",
            cambiado_por_id=usuario_id
        )
        
        return incapacidad_actualizada

    async def enviar_a_pago(
        self,
        db: AsyncSession,
        incapacidad_id: UUID,
        usuario_id: Optional[UUID] = None
    ) -> Incapacidad:
        """
        Envía una incapacidad aprobada a pago.
        
        Args:
            db: Sesión de base de datos
            incapacidad_id: ID de la incapacidad
            usuario_id: ID del usuario
            
        Returns:
            Incapacidad en estado EN_PAGO
        """
        incapacidad = await self.get_incapacidad(db, incapacidad_id)
        
        await self._validate_state_transition(
            incapacidad.estado,
            EstadoIncapacidad.EN_PAGO
        )
        
        # Validar que tenga valor calculado
        if not incapacidad.valor_total or incapacidad.valor_total <= 0:
            raise BadRequestException(
                "La incapacidad debe tener un valor_total calculado antes de enviar a pago"
            )
        
        update_data = {
            'estado': EstadoIncapacidad.EN_PAGO
        }
        
        # Actualizar incapacidad
        estado_anterior = incapacidad.estado
        incapacidad_actualizada = await self.repository.update(db, id=incapacidad_id, obj_in=update_data)
        
        # Registrar en historial
        await historial_estado_service.create_historial_entry(
            db=db,
            entity_type="incapacidad",
            entity_id=incapacidad_id,
            estado_anterior=estado_anterior.value,
            estado_nuevo=EstadoIncapacidad.EN_PAGO.value,
            observacion=f"Incapacidad enviada a pago por valor de ${incapacidad.valor_total}",
            cambiado_por_id=usuario_id
        )
        
        return incapacidad_actualizada

    async def marcar_como_pagada(
        self,
        db: AsyncSession,
        incapacidad_id: UUID,
        usuario_id: Optional[UUID] = None
    ) -> Incapacidad:
        """
        Marca una incapacidad como pagada.
        
        Args:
            db: Sesión de base de datos
            incapacidad_id: ID de la incapacidad
            usuario_id: ID del usuario
            
        Returns:
            Incapacidad pagada
        """
        incapacidad = await self.get_incapacidad(db, incapacidad_id)
        
        await self._validate_state_transition(
            incapacidad.estado,
            EstadoIncapacidad.PAGADA
        )
        
        update_data = {
            'estado': EstadoIncapacidad.PAGADA
        }
        
        # Actualizar incapacidad
        estado_anterior = incapacidad.estado
        incapacidad_actualizada = await self.repository.update(db, id=incapacidad_id, obj_in=update_data)
        
        # Registrar en historial
        await historial_estado_service.create_historial_entry(
            db=db,
            entity_type="incapacidad",
            entity_id=incapacidad_id,
            estado_anterior=estado_anterior.value,
            estado_nuevo=EstadoIncapacidad.PAGADA.value,
            observacion="Incapacidad marcada como pagada",
            cambiado_por_id=usuario_id
        )
        
        return incapacidad_actualizada

    async def get_historial_estados(
        self,
        db: AsyncSession,
        incapacidad_id: UUID
    ) -> List[dict]:
        """
        Obtiene el historial de cambios de estado.
        
        Args:
            db: Sesión de base de datos
            incapacidad_id: ID de la incapacidad
            
        Returns:
            Lista de cambios de estado
        """
        # TODO: Implementar cuando esté disponible el modelo HistorialEstado
        # Por ahora retorna información básica de la incapacidad
        incapacidad = await self.get_incapacidad(db, incapacidad_id)
        
        historial = []
        
        if incapacidad.fecha_radicacion:
            historial.append({
                'estado': EstadoIncapacidad.RADICADA.value,
                'fecha': incapacidad.fecha_radicacion,
                'usuario_id': incapacidad.radicado_por_id
            })
        
        if incapacidad.fecha_auditoria:
            historial.append({
                'estado': EstadoIncapacidad.EN_AUDITORIA.value,
                'fecha': incapacidad.fecha_auditoria,
                'usuario_id': incapacidad.auditado_por_id
            })
        
        if incapacidad.fecha_aprobacion:
            historial.append({
                'estado': EstadoIncapacidad.APROBADA.value,
                'fecha': incapacidad.fecha_aprobacion,
                'usuario_id': incapacidad.aprobado_por_id
            })
        
        if incapacidad.fecha_rechazo:
            historial.append({
                'estado': EstadoIncapacidad.RECHAZADA.value,
                'fecha': incapacidad.fecha_rechazo,
                'motivo': incapacidad.motivo_rechazo
            })
        
        return historial

    async def get_documentos(
        self,
        db: AsyncSession,
        incapacidad_id: UUID
    ) -> List[dict]:
        """
        Obtiene los documentos asociados a una incapacidad.
        
        Args:
            db: Sesión de base de datos
            incapacidad_id: ID de la incapacidad
            
        Returns:
            Lista de documentos
        """
        # TODO: Implementar cuando esté disponible el módulo de Documentos
        # Por ahora retorna lista vacía
        await self.get_incapacidad(db, incapacidad_id)
        return []

    async def _validate_incapacidad_arl(
        self,
        db: AsyncSession,
        empleado_id: UUID,
        empresa_id: UUID
    ) -> None:
        """Valida que empleado y empresa existan y estén activos para incapacidad ARL."""
        # Validar empleado
        empleado = await self.empleado_repository.get_by_id(db, empleado_id)
        if not empleado:
            raise NotFoundException(f"Empleado con ID {empleado_id} no encontrado")
        
        if empleado.estado != EstadoEmpleado.ACTIVO:
            raise BadRequestException(
                f"El empleado debe estar ACTIVO. Estado actual: {empleado.estado}"
            )
        
        # Validar empresa
        empresa = await self.empresa_repository.get_by_id(db, empresa_id)
        if not empresa:
            raise NotFoundException(f"Empresa con ID {empresa_id} no encontrada")
        
        if empresa.estado != EstadoEmpresa.ACTIVA:
            raise BadRequestException(
                f"La empresa debe estar ACTIVA. Estado actual: {empresa.estado}"
            )
        
        # Validar que el empleado pertenezca a la empresa
        if empleado.empresa_id != empresa_id:
            raise BadRequestException(
                f"El empleado no pertenece a la empresa especificada"
            )

    async def _validate_incapacidad_salud(
        self,
        db: AsyncSession,
        afiliado_id: UUID
    ) -> None:
        """Valida que el afiliado exista y esté activo para incapacidad SALUD."""
        afiliado = await self.afiliado_repository.get_by_id(db, afiliado_id)
        if not afiliado:
            raise NotFoundException(f"Afiliado con ID {afiliado_id} no encontrado")
        
        if afiliado.estado != EstadoAfiliado.ACTIVO:
            raise BadRequestException(
                f"El afiliado debe estar ACTIVO. Estado actual: {afiliado.estado}"
            )

    def _validate_fechas(
        self,
        fecha_inicio: date,
        fecha_fin: date
    ) -> None:
        """Valida que las fechas sean coherentes."""
        if fecha_fin < fecha_inicio:
            raise BadRequestException(
                "La fecha_fin debe ser mayor o igual a fecha_inicio"
            )
        
        # Las fechas pueden ser futuras (incapacidades proyectadas)
        # pero no más de 1 año en el futuro
        today = date.today()
        max_future = date(today.year + 1, today.month, today.day)
        
        if fecha_inicio > max_future:
            raise BadRequestException(
                "La fecha_inicio no puede ser más de 1 año en el futuro"
            )

    async def _validate_state_transition(
        self,
        current_state: EstadoIncapacidad,
        new_state: EstadoIncapacidad
    ) -> None:
        """Valida que la transición de estado sea permitida."""
        allowed = ALLOWED_TRANSITIONS.get(current_state, [])
        
        if new_state not in allowed:
            raise InvalidStateException(
                f"No se puede cambiar de {current_state.value} a {new_state.value}. "
                f"Transiciones permitidas: {', '.join([s.value for s in allowed])}"
            )

    async def _generar_numero_incapacidad(
        self,
        db: AsyncSession,
        tipo: TipoIncapacidad
    ) -> str:
        """Genera un número único de incapacidad."""
        # Formato: INC-ARL-YYYYMMDD-NNNN o INC-SAL-YYYYMMDD-NNNN
        prefix = "INC-ARL" if tipo == TipoIncapacidad.ARL else "INC-SAL"
        fecha_str = datetime.utcnow().strftime("%Y%m%d")
        
        # Intentar hasta encontrar un número único
        for i in range(1, 10000):
            numero = f"{prefix}-{fecha_str}-{i:04d}"
            existing = await self.repository.get_by_numero(db, numero)
            if not existing:
                return numero
        
        # Si llega aquí, usar UUID como fallback
        return f"{prefix}-{fecha_str}-{str(uuid.uuid4())[:8].upper()}"

    async def consultar_incapacidad_publica(
        self,
        db: AsyncSession,
        numero: Optional[str] = None,
        documento: Optional[str] = None,
        tipo_documento: Optional[str] = None
    ) -> dict:
        """
        Consultar incapacidad de forma pública (sin autenticación).
        
        Este método está diseñado para permitir consultas públicas sin autenticación,
        sanitizando todos los datos sensibles antes de retornarlos.
        
        Args:
            db: Sesión de base de datos
            numero: Número de radicación (opcional)
            documento: Número de documento (opcional)
            tipo_documento: Tipo de documento (opcional)
            
        Returns:
            Diccionario con datos sanitizados de la incapacidad
            
        Raises:
            BadRequestException: Si los parámetros son inválidos
            NotFoundException: Si no se encuentra la incapacidad
        """
        from sqlalchemy.orm import selectinload
        from sqlalchemy import select
        from app.models.empleado import Empleado
        from app.models.afiliado import Afiliado
        from app.core.logging import logger
        
        # Validar parámetros
        if not numero and not (documento and tipo_documento):
            raise BadRequestException(
                "Debe proporcionar número de radicación O documento + tipo_documento"
            )
        
        # Log de consulta (para auditoría)
        logger.info(
            f"Consulta pública de incapacidad",
            extra={
                "numero": numero,
                "tiene_documento": bool(documento),
                "tipo_documento": tipo_documento
            }
        )
        
        # Buscar incapacidad con eager loading
        query = select(Incapacidad).options(
            selectinload(Incapacidad.empleado),
            selectinload(Incapacidad.afiliado),
            selectinload(Incapacidad.empresa),
            selectinload(Incapacidad.documentos)
        )
        
        if numero:
            # Búsqueda por número de radicación
            query = query.where(Incapacidad.numero == numero.upper().strip())
        else:
            # Búsqueda por documento
            # Intentar buscar en empleado primero
            empleado_query = query.join(Incapacidad.empleado).where(
                Empleado.numero_documento == documento.strip()
            )
            # Si se proporciona tipo_documento, filtrar también por eso
            if tipo_documento:
                empleado_query = empleado_query.where(Empleado.tipo_documento == tipo_documento)
            
            result = await db.execute(empleado_query)
            incapacidad = result.scalar_one_or_none()
            
            # Si no se encuentra en empleado, buscar en afiliado
            if not incapacidad:
                afiliado_query = query.join(Incapacidad.afiliado).where(
                    Afiliado.numero_documento == documento.strip()
                )
                # Si se proporciona tipo_documento, filtrar también por eso
                if tipo_documento:
                    afiliado_query = afiliado_query.where(Afiliado.tipo_documento == tipo_documento)
                
                result = await db.execute(afiliado_query)
                incapacidad = result.scalar_one_or_none()
                
            if not incapacidad:
                raise NotFoundException(
                    "No se encontró ninguna incapacidad con los datos proporcionados"
                )
            
            # Retornar datos sanitizados directamente
            return await self._sanitize_incapacidad_publica(incapacidad, db)
        
        # Si es búsqueda por número, ejecutar query
        result = await db.execute(query)
        incapacidad = result.scalar_one_or_none()
        
        if not incapacidad:
            raise NotFoundException(
                "No se encontró ninguna incapacidad con los datos proporcionados"
            )
        
        # Sanitizar y retornar datos
        return await self._sanitize_incapacidad_publica(incapacidad, db)

    async def _sanitize_incapacidad_publica(self, incapacidad: Incapacidad, db: AsyncSession) -> dict:
        """
        Sanitiza los datos de una incapacidad para consulta pública.
        
        Elimina todos los datos sensibles:
        - Valores monetarios (salario_base, valor_dia, valor_total)
        - Cuentas bancarias
        - Números de documento completos
        - IDs de usuarios internos
        - Datos de auditores
        
        Args:
            incapacidad: Incapacidad a sanitizar
            db: Sesión de base de datos para consultas
            
        Returns:
            Diccionario con datos públicos sanitizados
        """
        # Obtener nombre completo del solicitante
        if incapacidad.empleado:
            nombre_completo = f"{incapacidad.empleado.nombres} {incapacidad.empleado.apellidos}"
            tipo_doc = incapacidad.empleado.tipo_documento.value if hasattr(incapacidad.empleado.tipo_documento, 'value') else str(incapacidad.empleado.tipo_documento)
        elif incapacidad.afiliado:
            nombre_completo = f"{incapacidad.afiliado.nombres} {incapacidad.afiliado.apellidos}"
            tipo_doc = incapacidad.afiliado.tipo_documento.value if hasattr(incapacidad.afiliado.tipo_documento, 'value') else str(incapacidad.afiliado.tipo_documento)
        else:
            nombre_completo = "Solicitante"
            tipo_doc = "N/A"
        
        # Filtrar solo documentos públicos (no incluir documentos sensibles internos)
        documentos_publicos = []
        for doc in incapacidad.documentos:
            tipo_doc_value = doc.tipo_documento.value if hasattr(doc.tipo_documento, 'value') else str(doc.tipo_documento)
            if tipo_doc_value in ["INCAPACIDAD_MEDICA", "CEDULA", "HISTORIA_CLINICA"]:
                documentos_publicos.append({
                    "id": str(doc.id),
                    "nombre_archivo": doc.nombre_archivo,
                    "tipo_documento": tipo_doc_value,
                    "tamanio_kb": doc.tamanio_bytes // 1024,
                    "fecha_upload": doc.created_at.isoformat()
                })
        
        # Cargar historial de estados usando el servicio polimórfico
        historial_completo = await historial_estado_service.get_incapacidad_history(
            db=db,
            incapacidad_id=incapacidad.id
        )
        
        # Construir historial ordenado cronológicamente
        historial = [
            {
                "estado": h.estado_nuevo.value if hasattr(h.estado_nuevo, 'value') else str(h.estado_nuevo),
                "fecha_cambio": h.created_at.isoformat(),
                # Solo incluir observaciones si el estado es OBSERVADA
                "observaciones": h.observacion if str(h.estado_nuevo) == "OBSERVADA" else None
            }
            for h in historial_completo
        ]
        
        # Determinar observaciones públicas (solo si está OBSERVADA)
        observaciones_publicas = None
        estado_actual = incapacidad.estado.value if hasattr(incapacidad.estado, 'value') else str(incapacidad.estado)
        if estado_actual == "OBSERVADA" and historial:
            # Buscar la última observación del estado OBSERVADA
            for h in reversed(historial):
                if h.get("observaciones"):
                    observaciones_publicas = h["observaciones"]
                    break
        
        # Construir response sanitizada
        return {
            "numero": incapacidad.numero,
            "estado": incapacidad.estado.value if hasattr(incapacidad.estado, 'value') else str(incapacidad.estado),
            "tipo": incapacidad.tipo.value if hasattr(incapacidad.tipo, 'value') else str(incapacidad.tipo),
            "fecha_inicio": incapacidad.fecha_inicio.isoformat(),
            "fecha_fin": incapacidad.fecha_fin.isoformat(),
            "dias_totales": incapacidad.dias_totales,
            "nombre_completo": nombre_completo,
            "tipo_documento": tipo_doc,
            # Información médica básica (sin detalles sensibles)
            "diagnostico_cie10": incapacidad.diagnostico_cie10,
            "descripcion_diagnostico": incapacidad.descripcion_diagnostico,
            "eps": incapacidad.eps,
            # Listas
            "historial_estados": historial,
            "documentos": documentos_publicos,
            "observaciones_publicas": observaciones_publicas,
            # Metadata
            "created_at": incapacidad.created_at.isoformat(),
            "updated_at": incapacidad.updated_at.isoformat()
        }


# Singleton instance
incapacidad_service = IncapacidadService()

"""
Service para lógica de negocio de Incapacidad con workflow de estados.
"""
from datetime import date, datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import UUID
import uuid
from app.core.logging import logger
from app.tasks.incapacidad_tasks import send_incapacidad_radicada_email_task

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, null as sa_null

from app.core.exceptions import (
    NotFoundException,
    BadRequestException,
    InvalidStateException,
    ConflictException,
    ForbiddenException
)
from app.db.repositories.incapacidad_repository import incapacidad_repository
from app.db.repositories.empleado_repository import empleado_repository
from app.db.repositories.afiliado_repository import afiliado_repository
from app.db.repositories.empresa_repository import empresa_repository
from app.services.historial_estado_service import historial_estado_service
from app.models.incapacidad import Incapacidad
from app.models.documento import Documento
from app.schemas.incapacidad import IncapacidadCreate, IncapacidadUpdate, AprobarAuditoriaRequest
from app.schemas.documento import PresignedUrlResponse
from app.utils.enums import (
    EstadoIncapacidad,
    TipoIncapacidad,
    TipoSiniestro,
    EstadoEmpleado,
    EstadoAfiliado,
    EstadoEmpresa,
    Prioridad,
    TipoDocumentoArchivo
)
from app.core.storage_core import storage_backend
from app.schemas.siniestro import SiniestroCreate
from app.services import glosada_notification_service


# Matriz de transiciones de estados permitidas
ALLOWED_TRANSITIONS: Dict[EstadoIncapacidad, List[EstadoIncapacidad]] = {
    EstadoIncapacidad.RADICADA: [
        EstadoIncapacidad.EN_AUDITORIA,
    ],
    EstadoIncapacidad.EN_AUDITORIA: [
        EstadoIncapacidad.PENDIENTE,
        EstadoIncapacidad.LIQUIDACION,
        EstadoIncapacidad.LIQUIDACION_PARCIAL,
        EstadoIncapacidad.GLOSADA,
        EstadoIncapacidad.CREACION_SINIESTRO,
    ],
    EstadoIncapacidad.PENDIENTE: [
        EstadoIncapacidad.EN_AUDITORIA,
        EstadoIncapacidad.GLOSADA,
    ],
    EstadoIncapacidad.CREACION_SINIESTRO: [
        EstadoIncapacidad.EN_AUDITORIA,
    ],
    EstadoIncapacidad.LIQUIDACION: [
        EstadoIncapacidad.EN_PAGO,
        EstadoIncapacidad.PAGADA,  # kept for the legacy /enviar-pago, /marcar-pagada endpoints
        EstadoIncapacidad.EN_AUDITORIA,
    ],
    EstadoIncapacidad.LIQUIDACION_PARCIAL: [
        EstadoIncapacidad.EN_PAGO_PARCIAL,
        EstadoIncapacidad.EN_AUDITORIA,
    ],
    EstadoIncapacidad.GLOSADA: [],
    EstadoIncapacidad.EN_PAGO: [
        EstadoIncapacidad.PAGADA,
    ],
    EstadoIncapacidad.EN_PAGO_PARCIAL: [
        EstadoIncapacidad.PAGADA_PARCIAL,
    ],
    EstadoIncapacidad.PAGADA: [],
    EstadoIncapacidad.PAGADA_PARCIAL: [],
}


# Tipos de documentos públicos permitidos para descarga sin autenticación
TIPOS_DOCUMENTOS_PUBLICOS = [
    TipoDocumentoArchivo.INCAPACIDAD_MEDICA,
    TipoDocumentoArchivo.CEDULA,
    TipoDocumentoArchivo.HISTORIA_CLINICA,
]


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
        incapacidad = await self.repository.create(db, incapacidad_dict)

        # Recargar con relaciones para que la serialización funcione correctamente
        return await self.repository.get_by_id_with_relations(db, incapacidad.id)

    async def create_from_pre_incapacidad(
        self,
        db: AsyncSession,
        pre_inc: Any,
        empleado: Optional[Any] = None,
        empresa: Optional[Any] = None,
        solicitante: Optional[Any] = None,
        usuario_id: Optional[UUID] = None,
        flush_only: bool = False,
    ) -> Incapacidad:
        """
        Create an Incapacidad directly from a PreIncapacidad — bypasses strict entity validation.
        Used by the unified background job to always create a record, even when empleado/empresa
        aren't in the DB yet. numero = str(pre_inc.numero_radicacion).
        """
        self._validate_fechas(pre_inc.fecha_inicio, pre_inc.fecha_fin)
        dias_totales = (pre_inc.fecha_fin - pre_inc.fecha_inicio).days + 1

        incapacidad_dict: Dict[str, Any] = {
            'numero': str(pre_inc.numero_radicacion),
            'tipo': TipoIncapacidad(pre_inc.tipo),
            'fecha_inicio': pre_inc.fecha_inicio,
            'fecha_fin': pre_inc.fecha_fin,
            'dias_totales': dias_totales,
            'diagnostico_cie10': pre_inc.diagnostico_cie10,
            'descripcion_diagnostico': pre_inc.descripcion_diagnostico,
            'nombre_medico': pre_inc.nombre_medico,
            'registro_medico': pre_inc.registro_medico,
            'ips': pre_inc.ips,
            'valor_dia': pre_inc.valor_dia,
            'observaciones': pre_inc.observaciones,
            'estado': EstadoIncapacidad.RADICADA,
            'fecha_radicacion': datetime.utcnow(),
            'empleado_id': empleado.id if empleado else None,
            'empresa_id': empresa.id if empresa else None,
            'solicitante_id': solicitante.id if solicitante else None,
        }

        if usuario_id:
            incapacidad_dict['radicado_por_id'] = usuario_id

        if flush_only:
            incapacidad = await self.repository.create_flushed(db, incapacidad_dict)
        else:
            incapacidad = await self.repository.create(db, incapacidad_dict)
        return await self.repository.get_by_id_with_relations(db, incapacidad.id)

    async def get_incapacidad(
        self,
        db: AsyncSession,
        incapacidad_id: UUID,
        with_relations: bool = True
    ) -> Incapacidad:
        """
        Obtiene una incapacidad por ID, opcionalmente con relaciones.
        
        Args:
            db: Sesión de base de datos
            incapacidad_id: ID de la incapacidad
            with_relations: Si True, carga todas las relaciones (empleado, empresa, afiliado)
            
        Returns:
            Incapacidad encontrada con relaciones cargadas si with_relations=True
            
        Raises:
            NotFoundException: Si la incapacidad no existe
        """
        if with_relations:
            incapacidad = await self.repository.get_by_id_with_relations(db, incapacidad_id)
        else:
            incapacidad = await self.repository.get_by_id(db, incapacidad_id)
            
        if not incapacidad:
            raise NotFoundException(f"Incapacidad con ID {incapacidad_id} no encontrada")
        logger.info(f"Incapacidad {incapacidad_id} obtenida con relaciones: {with_relations}")
        # Si es ARL y tiene empleado, cargar sus siniestros
        if with_relations and incapacidad.tipo == TipoIncapacidad.ARL and incapacidad.empleado_id:
            from app.db.repositories.siniestro_repository import SiniestroRepository
            siniestro_repo = SiniestroRepository()
            # Cargar todos los siniestros del empleado
            logger.info(f"Cargando siniestros para empleado {incapacidad.empleado_id}")
            incapacidad.siniestros_empleado = await siniestro_repo.get_by_empleado(
                db, 
                incapacidad.empleado_id,
                skip=0,
                limit=100  # Limitar a 100 siniestros
            )
        logger.info(f"Incapacidad {incapacidad_id} retornada")
        return incapacidad

    async def list_incapacidades(
        self,
        db: AsyncSession,
        tipo: Optional[TipoIncapacidad] = None,
        estado: Optional[EstadoIncapacidad] = None,
        numero: Optional[str] = None,
        empleado_id: Optional[UUID] = None,
        empleado_documento: Optional[str] = None,
        afiliado_id: Optional[UUID] = None,
        afiliado_documento: Optional[str] = None,
        empresa_id: Optional[UUID] = None,
        empresa_nit: Optional[str] = None,
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
            empleado_id: Filtrar por empleado (UUID)
            empleado_documento: Filtrar por documento de empleado
            afiliado_id: Filtrar por afiliado (UUID)
            afiliado_documento: Filtrar por documento de afiliado
            empresa_id: Filtrar por empresa (UUID)
            empresa_nit: Filtrar por NIT de empresa
            fecha_inicio_desde: Fecha mínima
            fecha_inicio_hasta: Fecha máxima
            skip: Registros a saltar
            limit: Máximo de registros
            
        Returns:
            Lista de incapacidades
        """
        # Resolver empleado_id si se proporciona documento
        if empleado_documento and not empleado_id:
            empleado = await self.empleado_repository.get_by_documento(db, empleado_documento)
            if empleado:
                empleado_id = empleado.id
                
        # Resolver afiliado_id si se proporciona documento
        if afiliado_documento and not afiliado_id:
            afiliado = await self.afiliado_repository.get_by_documento(db, afiliado_documento)
            if afiliado:
                afiliado_id = afiliado.id
                
        # Resolver empresa_id si se proporciona NIT
        if empresa_nit and not empresa_id:
            empresa = await self.empresa_repository.get_by_nit(db, empresa_nit)
            if empresa:
                empresa_id = empresa.id
        
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

    async def listar_pendientes(
        self,
        db: AsyncSession,
        tipo: Optional[TipoIncapacidad] = None,
        prioridad: Optional[Prioridad] = None,
        empresa_nit: Optional[str] = None,
        dias_antiguedad_min: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
        estados: Optional[List[EstadoIncapacidad]] = None,
    ) -> List[Dict]:
        """
        Listar incapacidades de una bandeja con cálculos de días.

        Args:
            db: Sesión de base de datos
            tipo: Filtro por tipo (ARL/SALUD)
            prioridad: Filtro por prioridad
            empresa_nit: Filtro por NIT de empresa (solo ARL)
            dias_antiguedad_min: Días mínimos desde radicación
            skip: Offset para paginación
            limit: Límite de resultados
            estados: Lista de estados a incluir; por defecto RADICADA/EN_AUDITORIA/PENDIENTE

        Returns:
            Lista de incapacidades con días calculados
        """
        estados_pendientes = estados or [
            EstadoIncapacidad.RADICADA,
            EstadoIncapacidad.EN_AUDITORIA,
            EstadoIncapacidad.PENDIENTE,
        ]

        # Usar repository para obtener incapacidades filtradas
        incapacidades = await self.repository.listar_pendientes(
            db=db,
            estados=estados_pendientes,
            tipo=tipo,
            prioridad=prioridad,
            empresa_nit=empresa_nit,
            skip=skip,
            limit=limit
        )
        
        # Enriquecer con cálculos
        from datetime import timezone
        ahora = datetime.now(timezone.utc)
        resultados = []

        ahora_naive = ahora.replace(tzinfo=None)

        for incap in incapacidades:
            # Normalize all timestamps to naive UTC before arithmetic.
            # asyncpg returns tz-aware for DateTime(timezone=True); test DB may return naive.
            created_at = incap.created_at
            updated_at = incap.updated_at
            created_at_naive = created_at.replace(tzinfo=None) if created_at.tzinfo is not None else created_at
            updated_at_naive = updated_at.replace(tzinfo=None) if updated_at.tzinfo is not None else updated_at

            dias_desde_radicacion = (ahora_naive - created_at_naive).days
            dias_en_estado_actual = (ahora_naive - updated_at_naive).days
            
            # Aplicar filtro de antigüedad si existe
            if dias_antiguedad_min is not None and dias_desde_radicacion < dias_antiguedad_min:
                continue
            
            # Retornar objeto con campos calculados
            resultado = {
                'incapacidad': incap,  # Objeto completo con relaciones
                'dias_desde_radicacion': dias_desde_radicacion,
                'dias_en_estado_actual': dias_en_estado_actual
            }
            resultados.append(resultado)
        
        return resultados

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
            EstadoIncapacidad.PENDIENTE,
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

    async def _cambiar_estado(
        self,
        db: AsyncSession,
        incapacidad: "Incapacidad",
        nuevo_estado: EstadoIncapacidad,
        observacion: str,
        usuario_id: Optional[UUID],
        extra_update: Optional[Dict[str, Any]] = None,
        flush_only: bool = False,
    ) -> "Incapacidad":
        """
        Helper centralizado para todas las transiciones de estado de una incapacidad.

        Garantiza que:
        1. La observación es no-vacía (obligatoria para toda transición).
        2. La transición está permitida por la matriz ALLOWED_TRANSITIONS.
        3. El estado se actualiza en la base de datos.
        4. Se escribe una entrada en historial_estado.

        Args:
            db: Sesión de base de datos
            incapacidad: Objeto Incapacidad actual (pre-transición)
            nuevo_estado: Estado destino
            observacion: Texto obligatorio que describe el motivo del cambio
            usuario_id: ID del usuario que ejecuta la transición
            extra_update: Campos adicionales a actualizar junto con el estado
            flush_only: Si True, usa flush en lugar de commit (para operaciones en pipeline)

        Returns:
            Incapacidad con el nuevo estado

        Raises:
            BadRequestException: Si observacion está vacía o es solo espacios
            InvalidStateException: Si la transición no está permitida
        """
        if not observacion or not observacion.strip():
            raise BadRequestException(
                f"La observación es obligatoria para la transición a {nuevo_estado.value}"
            )

        await self._validate_state_transition(incapacidad.estado, nuevo_estado)

        estado_anterior = incapacidad.estado
        update_data: Dict[str, Any] = {"estado": nuevo_estado, **(extra_update or {})}

        if flush_only:
            updated = await self.repository.update_flushed(db, id=incapacidad.id, obj_in=update_data)
        else:
            updated = await self.repository.update(db, id=incapacidad.id, obj_in=update_data)

        await historial_estado_service.create_historial_entry(
            db=db,
            entity_type="incapacidad",
            entity_id=incapacidad.id,
            estado_anterior=estado_anterior.value if estado_anterior else None,
            estado_nuevo=nuevo_estado.value,
            observacion=observacion,
            cambiado_por_id=usuario_id,
            flush_only=flush_only,
        )

        return updated

    async def radicar_incapacidad(
        self,
        db: AsyncSession,
        incapacidad_id: UUID,
        usuario_id: Optional[UUID] = None,
        flush_only: bool = False,
        observacion: str = "Incapacidad radicada para auditoría",
    ) -> Incapacidad:
        """
        Radica una incapacidad (pasa a estado EN_AUDITORIA).

        Args:
            db: Sesión de base de datos
            incapacidad_id: ID de la incapacidad
            usuario_id: ID del usuario que radica
            flush_only: Si True, usa flush en lugar de commit (para pipelines)
            observacion: Observación del cambio de estado (obligatoria, no vacía)

        Returns:
            Incapacidad radicada
        """
        incapacidad = await self.get_incapacidad(db, incapacidad_id)

        extra_update: Dict[str, Any] = {}
        if usuario_id:
            extra_update['radicado_por_id'] = usuario_id

        incapacidad_actualizada = await self._cambiar_estado(
            db=db,
            incapacidad=incapacidad,
            nuevo_estado=EstadoIncapacidad.EN_AUDITORIA,
            observacion=observacion,
            usuario_id=usuario_id,
            extra_update=extra_update,
            flush_only=flush_only,
        )
        
        try:
            # Preparar datos para el email
            from datetime import datetime
            
            # Determinar beneficiario (empleado o afiliado)
            beneficiario_nombre = "N/A"
            beneficiario_documento = "N/A"
            tipo_documento_str = "N/A"
            
            if incapacidad.empleado:
                beneficiario_nombre = f"{incapacidad.empleado.nombres} {incapacidad.empleado.apellidos}"
                beneficiario_documento = incapacidad.empleado.numero_documento
                tipo_documento_str = incapacidad.empleado.tipo_documento.value if hasattr(incapacidad.empleado.tipo_documento, 'value') else str(incapacidad.empleado.tipo_documento)
            elif incapacidad.afiliado:
                beneficiario_nombre = f"{incapacidad.afiliado.nombres} {incapacidad.afiliado.apellidos}"
                beneficiario_documento = incapacidad.afiliado.numero_documento
                tipo_documento_str = incapacidad.afiliado.tipo_documento.value if hasattr(incapacidad.afiliado.tipo_documento, 'value') else str(incapacidad.afiliado.tipo_documento)
            
            incapacidad_data = {
                "tipo": incapacidad.tipo.value if hasattr(incapacidad.tipo, 'value') else str(incapacidad.tipo),
                "beneficiario_nombre": beneficiario_nombre,
                "tipo_documento": tipo_documento_str,
                "numero_documento": beneficiario_documento,
                "fecha_inicio": incapacidad.fecha_inicio.isoformat() if incapacidad.fecha_inicio else None,
                "fecha_fin": incapacidad.fecha_fin.isoformat() if incapacidad.fecha_fin else None,
                "dias_totales": incapacidad.dias_totales,
                "diagnostico_cie10": incapacidad.diagnostico_cie10,
                "ips_nombre": incapacidad.ips_nombre if hasattr(incapacidad, 'ips_nombre') else "N/A",
                "medico_nombre": incapacidad.medico_nombre if hasattr(incapacidad, 'medico_nombre') else "N/A",
                "eps_nombre": incapacidad.eps if hasattr(incapacidad, 'eps') else "N/A"
            }
            
            send_incapacidad_radicada_email_task.delay(
                correo_solicitante=incapacidad.solicitante.correo,
                solicitante_nombre=incapacidad.solicitante.nombres + " " + incapacidad.solicitante.apellidos,
                numero_radicacion=incapacidad.numero,
                incapacidad_data=incapacidad_data
            )
            logger.info(f"Tarea de email programada para {incapacidad_id}")
        except Exception as email_error:
            logger.error(f"Error al programar email: {email_error}")
            # No fallar la radicación si falla el email
        
        return incapacidad_actualizada

    async def auditar_incapacidad(
        self,
        db: AsyncSession,
        incapacidad_id: UUID,
        accion: str,
        observaciones: str,
        usuario_id: Optional[UUID] = None,
        datos_aprobados: Optional[Dict[str, Any]] = None
    ) -> Incapacidad:
        """
        Audita una incapacidad con soporte para aprobación parcial.
        
        Args:
            db: Sesión de base de datos
            incapacidad_id: ID de la incapacidad
            accion: SOLICITAR_INFORMACION, APROBAR_PARA_PAGO, APROBAR_PARA_PAGO_PARCIAL, RECHAZAR
            observaciones: Observaciones de la auditoría
            usuario_id: ID del auditor
            datos_aprobados: Dict con campos modificados (solo para aprobación parcial)
            
        Returns:
            Incapacidad auditada
        """
        logger.info(f"Auditar incapacidad {incapacidad_id} con acción {accion}")
        incapacidad = await self.get_incapacidad(db, incapacidad_id)
        logger.info(f"se obtuvo incapacidad {incapacidad}")
        if incapacidad.estado != EstadoIncapacidad.EN_AUDITORIA:
            raise InvalidStateException(
                f"Solo se pueden auditar incapacidades en estado EN_AUDITORIA. "
                f"Estado actual: {incapacidad.estado}"
            )

        # Mandatory observation for ALL audit actions
        if not observaciones or not observaciones.strip():
            raise BadRequestException(
                "La observación es obligatoria para todas las transiciones de auditoría"
            )

        nuevo_estado = None
        # extra_update holds all field changes except 'estado' — _cambiar_estado sets that
        extra_update: Dict[str, Any] = {
            'observaciones': observaciones,
            'fecha_auditoria': datetime.utcnow()
        }

        if usuario_id:
            extra_update['auditado_por_id'] = usuario_id

        if accion == "SOLICITAR_INFORMACION":
            nuevo_estado = EstadoIncapacidad.PENDIENTE
            extra_update['pendiente_desde'] = datetime.utcnow()
        elif accion == "CREACION_SINIESTRO":
            nuevo_estado = EstadoIncapacidad.CREACION_SINIESTRO
        elif accion == "APROBAR_PARA_PAGO":
            nuevo_estado = EstadoIncapacidad.LIQUIDACION
            extra_update['fecha_aprobacion'] = datetime.utcnow()
            if usuario_id:
                extra_update['aprobado_por_id'] = usuario_id
        elif accion == "APROBAR_PARA_PAGO_PARCIAL":
            nuevo_estado = EstadoIncapacidad.LIQUIDACION_PARCIAL
            extra_update['fecha_aprobacion'] = datetime.utcnow()
            if usuario_id:
                extra_update['aprobado_por_id'] = usuario_id

            # Guardar datos aprobados en tabla separada
            if datos_aprobados:
                from app.db.repositories.auditoria_datos_repository import auditoria_datos_repository

                # Verificar si ya existe registro
                datos_existentes = await auditoria_datos_repository.get_by_incapacidad(
                    db, incapacidad_id
                )

                datos_to_save = {
                    'incapacidad_id': incapacidad_id,
                    'fecha_inicio_aprobada': datos_aprobados.get('fecha_inicio_aprobada'),
                    'fecha_fin_aprobada': datos_aprobados.get('fecha_fin_aprobada'),
                    'dias_aprobados': datos_aprobados.get('dias_aprobados'),
                    'cie10_aprobado': datos_aprobados.get('cie10_aprobado'),
                    'diagnostico_aprobado': datos_aprobados.get('diagnostico_aprobado'),
                    'observacion_auditoria': observaciones,
                    'auditado_por_id': usuario_id,
                    'fecha_auditoria': datetime.utcnow()
                }

                if datos_existentes:
                    await auditoria_datos_repository.update(
                        db, id=datos_existentes.id, obj_in=datos_to_save
                    )
                else:
                    await auditoria_datos_repository.create(db, obj_in=datos_to_save)
        elif accion == "RECHAZAR":
            nuevo_estado = EstadoIncapacidad.GLOSADA
            extra_update['fecha_rechazo'] = datetime.utcnow()
            extra_update['motivo_rechazo'] = observaciones
        else:
            raise BadRequestException(f"Acción de auditoría inválida: {accion}")

        # Gate: block approval/rejection for ARL incapacidades without a linked siniestro
        if nuevo_estado in (
            EstadoIncapacidad.LIQUIDACION,
            EstadoIncapacidad.LIQUIDACION_PARCIAL,
            EstadoIncapacidad.GLOSADA,
        ):
            if incapacidad.tipo == TipoIncapacidad.ARL and not incapacidad.siniestro_id:
                raise BadRequestException(
                    "Esta incapacidad no tiene un siniestro asociado. "
                    "Debe crear o vincular el siniestro antes de continuar."
                )

        # Gate: PRIMER_DIA_NO_PAGABLE — block full LIQUIDACION when fecha_inicio == fecha_siniestro
        if accion == "APROBAR_PARA_PAGO":
            if (
                incapacidad.tipo == TipoIncapacidad.ARL
                and incapacidad.siniestro
                and incapacidad.fecha_inicio == incapacidad.siniestro.fecha_siniestro
            ):
                raise BadRequestException(
                    "El primer día coincide con la fecha del siniestro: "
                    "debe usar aprobación parcial (APROBAR_PARA_PAGO_PARCIAL)."
                )

        incapacidad_actualizada = await self._cambiar_estado(
            db=db,
            incapacidad=incapacidad,
            nuevo_estado=nuevo_estado,
            observacion=f"Auditoría: {accion} - {observaciones}",
            usuario_id=usuario_id,
            extra_update=extra_update,
        )

        # Notificación best-effort para GLOSADA
        if nuevo_estado == EstadoIncapacidad.GLOSADA:
            try:
                # Recargar relaciones necesarias para la notificación
                incap_con_relaciones = await self.repository.get_by_id_with_relations(
                    db, incapacidad_id
                )
                await glosada_notification_service.notificar_glosada(
                    db, incap_con_relaciones, observaciones
                )
            except Exception as notif_exc:
                logger.error(
                    f"[GLOSADA] Notificación falló para incapacidad {incapacidad_id}: {notif_exc}"
                )

        return incapacidad_actualizada

    async def aprobar_en_auditoria(
        self,
        db: AsyncSession,
        incapacidad_id: UUID,
        data: "AprobarAuditoriaRequest",
        usuario_id: UUID,
    ) -> dict:
        """
        Aprueba una incapacidad en auditoría, auto-determinando LIQUIDACION o LIQUIDACION_PARCIAL.

        Siempre persiste auditoria_resultado (incluso si falla).
        Si alguna regla ERROR falla → rollback del estado + 400 con lista de reglas.
        Compara solo fechas y días para determinar LIQUIDACION vs LIQUIDACION_PARCIAL.
        """
        from app.services.incapacidad_validation_rules import (
            validate_field_level,
            validate_business_rules,
            validate_audit_only_rules,
        )
        from app.models.auditoria_resultado import AuditoriaResultado
        from app.services.auditoria_service import REGLAS_ESPERADAS
        from app.db.repositories.plantilla_auditoria_repository import plantilla_auditoria_repository
        from app.schemas.plantilla_auditoria import PlantillaAuditoriaCreate
        from app.services.plantilla_auditoria_service import plantilla_auditoria_service as pa_svc
        from sqlalchemy import select as sa_select
        from sqlalchemy.orm import selectinload

        # 1. Load incapacidad with relations
        inc = (await db.execute(
            sa_select(Incapacidad)
            .options(
                selectinload(Incapacidad.empleado),
                selectinload(Incapacidad.siniestro),
                selectinload(Incapacidad.afiliado),
            )
            .where(Incapacidad.id == incapacidad_id)
        )).scalar_one_or_none()

        if inc is None:
            raise NotFoundException(f"Incapacidad {incapacidad_id} no encontrada")

        if inc.estado != EstadoIncapacidad.EN_AUDITORIA:
            raise InvalidStateException(
                f"Solo se pueden aprobar incapacidades en estado EN_AUDITORIA. "
                f"Estado actual: {inc.estado.value}"
            )

        # 2. Compute dias_aprobados (inclusive: fin - inicio + 1)
        dias_aprobados = (data.fecha_fin_aprobada - data.fecha_inicio_aprobada).days + 1

        # 3. Build confirmed row dict and run all validation rules
        cie10_confirmado = data.cie10_aprobado or inc.diagnostico_cie10
        # For SALUD, use afiliado.numero_documento so EMPTY_EMPLEADO_NUMERO doesn't fire
        identificador_persona = (
            inc.empleado.numero_documento if inc.empleado
            else (inc.afiliado.numero_documento if inc.afiliado else None)
        )
        confirmed_row = {
            "tipo": inc.tipo.value if hasattr(inc.tipo, "value") else str(inc.tipo),
            "empleado_numero_documento": identificador_persona,
            "tipo_enfermedad": inc.subtipo,
            "fecha_inicio": data.fecha_inicio_aprobada,
            "fecha_fin": data.fecha_fin_aprobada,
            "dias_totales": dias_aprobados,
            "diagnostico_cie10": cie10_confirmado,
            "nombre_medico": data.nombre_medico or inc.nombre_medico,
            "registro_medico": inc.registro_medico,
            "siniestro_id": inc.siniestro_id,
            "fecha_siniestro": inc.siniestro.fecha_siniestro if inc.siniestro else None,
        }

        issues = (
            validate_field_level(confirmed_row)
            + validate_business_rules(confirmed_row)
            + validate_audit_only_rules(confirmed_row)
        )
        failed_by_code = {i["codigo"]: i for i in issues}

        # 4. Persist auditoria_resultado — always, even on validation failure
        existing_rows = (await db.execute(
            sa_select(AuditoriaResultado)
            .where(AuditoriaResultado.incapacidad_id == incapacidad_id)
        )).scalars().all()
        existing_by_regla = {r.regla: r for r in existing_rows}

        for codigo, categoria in REGLAS_ESPERADAS:
            issue = failed_by_code.get(codigo)
            aprobado = issue is None
            severidad = issue["severidad"] if issue else "INFO"
            detalle = issue["descripcion"] if issue else "Regla cumplida"

            if codigo in existing_by_regla:
                row_obj = existing_by_regla[codigo]
                row_obj.aprobado = aprobado
                row_obj.severidad = severidad
                row_obj.detalle = detalle
                db.add(row_obj)
            else:
                db.add(AuditoriaResultado(
                    incapacidad_id=incapacidad_id,
                    regla=codigo,
                    categoria=categoria,
                    aprobado=aprobado,
                    severidad=severidad,
                    detalle=detalle,
                ))

        await db.commit()  # Always commit auditoria_resultado

        # Reload inc — object is expired after commit
        inc = (await db.execute(
            sa_select(Incapacidad)
            .options(
                selectinload(Incapacidad.siniestro),
                selectinload(Incapacidad.afiliado),
            )
            .where(Incapacidad.id == incapacidad_id)
        )).scalar_one()

        # 5. Reject if any ERROR-level rule failed
        # EMPTY_EMPLEADO_NUMERO / EMPTY_TIPO_ENFERMEDAD are ARL-only at approval stage;
        # SALUD incapacidades have afiliados instead of empleados and no subtipo.
        _salud_skip = {"EMPTY_EMPLEADO_NUMERO", "EMPTY_TIPO_ENFERMEDAD"} if inc.tipo == TipoIncapacidad.SALUD else set()
        error_rules = [i for i in issues if i["severidad"] == "ERROR" and i["codigo"] not in _salud_skip]
        if error_rules:
            reglas_fallidas = [
                {"codigo": r["codigo"], "descripcion": r["descripcion"], "severidad": r["severidad"]}
                for r in error_rules
            ]
            raise BadRequestException(
                "La incapacidad no puede ser aprobada. Revise las reglas de auditoría.",
                details={"reglas_fallidas": reglas_fallidas},
            )

        # 6. Auto-determine LIQUIDACION vs LIQUIDACION_PARCIAL (dates and days only)
        dates_match = (
            data.fecha_inicio_aprobada == inc.fecha_inicio
            and data.fecha_fin_aprobada == inc.fecha_fin
            and dias_aprobados == inc.dias_totales
        )
        nuevo_estado = (
            EstadoIncapacidad.LIQUIDACION if dates_match
            else EstadoIncapacidad.LIQUIDACION_PARCIAL
        )

        # 7. Create/update plantilla_auditoria
        plantilla_data = PlantillaAuditoriaCreate(
            canal_recepcion=data.canal_recepcion,
            nombre_ips=data.nombre_ips,
            dias_autorizados=dias_aprobados,
            fecha_inicio_autorizada=data.fecha_inicio_aprobada,
            fecha_fin_autorizada=data.fecha_fin_aprobada,
            diagnostico_cie10=cie10_confirmado,
            descripcion_cie10=data.descripcion_cie10 or inc.descripcion_diagnostico,
            nombre_medico=data.nombre_medico,
            especialidad_medico=data.especialidad_medico,
            dias_documento=inc.dias_totales if nuevo_estado == EstadoIncapacidad.LIQUIDACION_PARCIAL else None,
            rango_pagado_inicio=data.fecha_inicio_aprobada if nuevo_estado == EstadoIncapacidad.LIQUIDACION_PARCIAL else None,
            rango_pagado_fin=data.fecha_fin_aprobada if nuevo_estado == EstadoIncapacidad.LIQUIDACION_PARCIAL else None,
        )
        plantilla_payload = plantilla_data.model_dump(exclude_none=False)
        plantilla_payload["auditado_por_id"] = str(usuario_id)
        await plantilla_auditoria_repository.upsert(
            db=db, incapacidad_id=incapacidad_id, data=plantilla_payload
        )

        # Reload inc again (upsert committed — inc expired)
        inc = (await db.execute(
            sa_select(Incapacidad).where(Incapacidad.id == incapacidad_id)
        )).scalar_one()

        # 8. Transition state
        extra_update: Dict[str, Any] = {
            "observaciones": data.observacion,
            "fecha_auditoria": datetime.utcnow(),
            "fecha_aprobacion": datetime.utcnow(),
            "aprobado_por_id": usuario_id,
            "auditado_por_id": usuario_id,
        }
        await self._cambiar_estado(
            db=db,
            incapacidad=inc,
            nuevo_estado=nuevo_estado,
            observacion=f"Aprobación: {data.observacion}",
            usuario_id=usuario_id,
            extra_update=extra_update,
        )

        # 9. Build texto_copiable from saved plantilla
        plantilla_final = await plantilla_auditoria_repository.get_by_incapacidad(db, incapacidad_id)
        texto_copiable = pa_svc.build_texto_copiable(plantilla_final) if plantilla_final else ""

        logger.info(
            f"Incapacidad {incapacidad_id} aprobada → {nuevo_estado.value} por usuario {usuario_id}"
        )
        return {"estado": nuevo_estado.value, "texto_copiable": texto_copiable}

    async def solicitar_creacion_siniestro(
        self,
        db: AsyncSession,
        incapacidad_id: UUID,
        observacion: str,
        usuario_id: UUID,
    ) -> "Incapacidad":
        """
        El AUDITOR solicita la creación de siniestro cuando no hay candidatos.

        Transición: EN_AUDITORIA → CREACION_SINIESTRO

        Raises:
            BadRequestException: Si la incapacidad no es ARL o la observación está vacía
            InvalidStateException: Si no está en EN_AUDITORIA
        """
        incapacidad = await self.get_incapacidad(db, incapacidad_id)

        if incapacidad.tipo != TipoIncapacidad.ARL:
            raise BadRequestException(
                "Solo las incapacidades ARL pueden pasar a CREACION_SINIESTRO"
            )

        if incapacidad.estado != EstadoIncapacidad.EN_AUDITORIA:
            raise InvalidStateException(
                f"La incapacidad debe estar en EN_AUDITORIA; "
                f"estado actual: {incapacidad.estado.value}"
            )

        return await self._cambiar_estado(
            db=db,
            incapacidad=incapacidad,
            nuevo_estado=EstadoIncapacidad.CREACION_SINIESTRO,
            observacion=observacion,
            usuario_id=usuario_id,
        )

    async def iniciar_creacion_siniestro(
        self,
        db: AsyncSession,
        incapacidad_id: UUID,
        fecha_siniestro: date,
        tipo_siniestro: TipoSiniestro,
        descripcion: str,
        usuario_id: UUID,
        observacion: str,
        numero_siniestro: Optional[str] = None,
    ) -> "Incapacidad":
        """
        Crea el siniestro y retorna la incapacidad a EN_AUDITORIA.

        Transición: CREACION_SINIESTRO → EN_AUDITORIA
        Solo aplica a incapacidades de tipo ARL que estén en CREACION_SINIESTRO.

        El siniestro se crea en la misma transacción; si la creación falla, el
        estado NO cambia y se propaga la excepción al caller.

        Args:
            db: Sesión de base de datos
            incapacidad_id: ID de la incapacidad
            fecha_siniestro: Fecha del accidente/evento
            tipo_siniestro: Tipo de siniestro (ACCIDENTE_TRABAJO, etc.)
            descripcion: Descripción del siniestro (mínimo 10 caracteres)
            usuario_id: ID del ADMIN que ejecuta la acción
            observacion: Observación obligatoria para el historial

        Returns:
            Incapacidad en estado EN_AUDITORIA con siniestro_id vinculado

        Raises:
            BadRequestException: Si la incapacidad no es ARL
            InvalidStateException: Si el estado actual no es CREACION_SINIESTRO
            ValidationException: Si los datos del siniestro son inválidos
        """
        from app.services.siniestro_service import siniestro_service

        incapacidad = await self.get_incapacidad(db, incapacidad_id)

        if incapacidad.tipo != TipoIncapacidad.ARL:
            raise BadRequestException(
                "La creación de siniestro solo aplica a incapacidades ARL"
            )

        if incapacidad.estado != EstadoIncapacidad.CREACION_SINIESTRO:
            raise InvalidStateException(
                f"La incapacidad debe estar en CREACION_SINIESTRO; "
                f"estado actual: {incapacidad.estado.value}"
            )

        # Crear el siniestro primero — si falla, el estado no cambia
        siniestro_data = SiniestroCreate(
            empleado_id=incapacidad.empleado_id,
            empresa_id=incapacidad.empresa_id,
            fecha_siniestro=fecha_siniestro,
            tipo_siniestro=tipo_siniestro,
            descripcion=descripcion,
            numero_siniestro=numero_siniestro,
        )
        siniestro = await siniestro_service.create_siniestro(db, siniestro_data)

        return await self._cambiar_estado(
            db=db,
            incapacidad=incapacidad,
            nuevo_estado=EstadoIncapacidad.EN_AUDITORIA,
            observacion=observacion,
            usuario_id=usuario_id,
            extra_update={
                "siniestro_id": siniestro.id,
                "numero_siniestro": siniestro.numero_siniestro,
            },
        )

    async def retornar_a_auditoria(
        self,
        db: AsyncSession,
        incapacidad_id: UUID,
        observaciones: str,
        usuario_id: Optional[UUID] = None
    ) -> Incapacidad:
        """
        Retorna una incapacidad desde PENDIENTE a EN_AUDITORIA.

        Clears pendiente_desde and transitions back to EN_AUDITORIA.

        Args:
            db: Sesión de base de datos
            incapacidad_id: ID de la incapacidad
            observaciones: Observaciones del retorno (obligatorias)
            usuario_id: ID del auditor

        Returns:
            Incapacidad en estado EN_AUDITORIA con pendiente_desde = None

        Raises:
            InvalidStateException: Si la incapacidad no está en PENDIENTE
            BadRequestException: Si observaciones está vacío
        """
        incapacidad = await self.get_incapacidad(db, incapacidad_id)

        if incapacidad.estado != EstadoIncapacidad.PENDIENTE:
            raise InvalidStateException(
                f"Solo se pueden retornar a auditoría incapacidades en estado PENDIENTE. "
                f"Estado actual: {incapacidad.estado}"
            )

        # Validate before wrapping in prefix so that _cambiar_estado gets the canonical
        # prefixed form while the raw value is checked here.
        if not observaciones or not observaciones.strip():
            raise BadRequestException(
                "La observación es obligatoria para retornar a auditoría"
            )

        extra_update: Dict[str, Any] = {
            'observaciones': observaciones,
            'pendiente_desde': sa_null(),  # Explicitly set to NULL (bypasses None-filter in base repo)
        }
        if usuario_id:
            extra_update['auditado_por_id'] = usuario_id

        return await self._cambiar_estado(
            db=db,
            incapacidad=incapacidad,
            nuevo_estado=EstadoIncapacidad.EN_AUDITORIA,
            observacion=f"Retorno a auditoría: {observaciones}",
            usuario_id=usuario_id,
            extra_update=extra_update,
        )

    async def aprobar_incapacidad(
        self,
        db: AsyncSession,
        incapacidad_id: UUID,
        usuario_id: Optional[UUID] = None,
        observacion: str = "Incapacidad aprobada para pago",
    ) -> Incapacidad:
        """
        Aprueba una incapacidad para pago.

        Args:
            db: Sesión de base de datos
            incapacidad_id: ID de la incapacidad
            usuario_id: ID del aprobador
            observacion: Observación del cambio de estado (obligatoria, no vacía)

        Returns:
            Incapacidad aprobada
        """
        incapacidad = await self.get_incapacidad(db, incapacidad_id)

        extra_update: Dict[str, Any] = {'fecha_aprobacion': datetime.utcnow()}
        if usuario_id:
            extra_update['aprobado_por_id'] = usuario_id

        return await self._cambiar_estado(
            db=db,
            incapacidad=incapacidad,
            nuevo_estado=EstadoIncapacidad.LIQUIDACION,
            observacion=observacion,
            usuario_id=usuario_id,
            extra_update=extra_update,
        )

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
            motivo: Motivo del rechazo (obligatorio, no vacío)
            usuario_id: ID del usuario que rechaza

        Returns:
            Incapacidad rechazada
        """
        incapacidad = await self.get_incapacidad(db, incapacidad_id)

        # Validate before wrapping in prefix (the f-string prefix would hide an empty value).
        if not motivo or not motivo.strip():
            raise BadRequestException(
                "La observación es obligatoria para la transición a GLOSADA"
            )

        extra_update: Dict[str, Any] = {
            'motivo_rechazo': motivo,
            'fecha_rechazo': datetime.utcnow(),
        }
        if usuario_id:
            extra_update['auditado_por_id'] = usuario_id

        return await self._cambiar_estado(
            db=db,
            incapacidad=incapacidad,
            nuevo_estado=EstadoIncapacidad.GLOSADA,
            observacion=f"Incapacidad glosada: {motivo}",
            usuario_id=usuario_id,
            extra_update=extra_update,
        )

    async def enviar_a_pago(
        self,
        db: AsyncSession,
        incapacidad_id: UUID,
        usuario_id: Optional[UUID] = None,
        observacion: Optional[str] = None,
    ) -> Incapacidad:
        """
        Envía una incapacidad aprobada a pago.

        Args:
            db: Sesión de base de datos
            incapacidad_id: ID de la incapacidad
            usuario_id: ID del usuario
            observacion: Observación del cambio (si omitida, se genera a partir de valor_total)

        Returns:
            Incapacidad en estado PAGADA
        """
        incapacidad = await self.get_incapacidad(db, incapacidad_id)

        # Validar que tenga valor calculado
        if not incapacidad.valor_total or incapacidad.valor_total <= 0:
            raise BadRequestException(
                "La incapacidad debe tener un valor_total calculado antes de enviar a pago"
            )

        obs = observacion or f"Incapacidad pagada por valor de ${incapacidad.valor_total}"

        return await self._cambiar_estado(
            db=db,
            incapacidad=incapacidad,
            nuevo_estado=EstadoIncapacidad.PAGADA,
            observacion=obs,
            usuario_id=usuario_id,
        )

    async def marcar_como_pagada(
        self,
        db: AsyncSession,
        incapacidad_id: UUID,
        usuario_id: Optional[UUID] = None,
        observacion: str = "Incapacidad marcada como pagada",
    ) -> Incapacidad:
        """
        Marca una incapacidad como pagada.

        Args:
            db: Sesión de base de datos
            incapacidad_id: ID de la incapacidad
            usuario_id: ID del usuario
            observacion: Observación del cambio de estado (obligatoria, no vacía)

        Returns:
            Incapacidad pagada
        """
        incapacidad = await self.get_incapacidad(db, incapacidad_id)

        return await self._cambiar_estado(
            db=db,
            incapacidad=incapacidad,
            nuevo_estado=EstadoIncapacidad.PAGADA,
            observacion=observacion,
            usuario_id=usuario_id,
        )

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
                'estado': EstadoIncapacidad.LIQUIDACION.value,
                'fecha': incapacidad.fecha_aprobacion,
                'usuario_id': incapacidad.aprobado_por_id
            })

        if incapacidad.fecha_rechazo:
            historial.append({
                'estado': EstadoIncapacidad.GLOSADA.value,
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

    async def get_stats(
        self,
        db: AsyncSession,
        empresa_id: Optional[UUID] = None,
        tipo: Optional[TipoIncapacidad] = None,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
    ) -> Dict[str, int]:
        """
        Obtener estadísticas del dashboard.
        
        Args:
            db: Sesión de base de datos
            empresa_id: Filtrar por empresa (opcional)
            tipo: Filtrar por tipo ARL/SALUD (opcional)
            fecha_desde: Filtrar desde fecha (opcional)
            fecha_hasta: Filtrar hasta fecha (opcional)
        
        Returns:
            Dict con métricas: pendientes, auditadas_hoy, proximas_vencer, rechazadas_observadas
        """
        return await self.repository.get_stats(
            db=db,
            empresa_id=empresa_id,
            tipo=tipo,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
        )

    async def get_extended_stats(
        self,
        db: AsyncSession,
        empresa_id: Optional[UUID] = None,
        tipo: Optional[TipoIncapacidad] = None,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
        top_limit: int = 10,
    ) -> Dict[str, any]:
        """
        Obtener estadísticas extendidas del dashboard con datos para gráficos.
        
        Args:
            db: Sesión de base de datos
            empresa_id: Filtrar por empresa (opcional)
            tipo: Filtrar por tipo ARL/SALUD (opcional)
            fecha_desde: Filtrar desde fecha (opcional)
            fecha_hasta: Filtrar hasta fecha (opcional)
            top_limit: Límite para rankings TOP (default 10)
        
        Returns:
            Dict con métricas básicas + datos agregados
        """
        return await self.repository.get_extended_stats(
            db=db,
            empresa_id=empresa_id,
            tipo=tipo,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            top_limit=top_limit,
        )

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
                # Solo incluir observaciones si el estado es PENDIENTE
                "observaciones": h.observacion if str(h.estado_nuevo) == "PENDIENTE" else None
            }
            for h in historial_completo
        ]

        # Determinar observaciones públicas (solo si está PENDIENTE)
        observaciones_publicas = None
        estado_actual = incapacidad.estado.value if hasattr(incapacidad.estado, 'value') else str(incapacidad.estado)
        if estado_actual == "PENDIENTE" and historial:
            # Buscar la última observación del estado PENDIENTE
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

    async def descargar_documento_publico(
        self,
        db: AsyncSession,
        numero: str,
        documento_id: UUID
    ) -> PresignedUrlResponse:
        """
        Genera URL de descarga pública para documento sin autenticación.
        
        Validaciones:
        1. Incapacidad existe
        2. Documento existe
        3. Documento pertenece a la incapacidad
        4. Tipo de documento es público
        
        Args:
            db: Sesión de base de datos
            numero: Número de radicación de la incapacidad
            documento_id: ID del documento
            
        Returns:
            PresignedUrlResponse con URL temporal (15 minutos)
            
        Raises:
            NotFoundException: Si incapacidad o documento no existen
            PermissionException: Si documento no pertenece o no es público
        """
        # 1. Buscar incapacidad por número
        incapacidad = await self.repository.get_by_numero(db, numero)
        if not incapacidad:
            raise NotFoundException(f"Incapacidad {numero} no encontrada")
        
        # 2. Buscar documento
        stmt = select(Documento).where(Documento.id == documento_id)
        result = await db.execute(stmt)
        documento = result.scalar_one_or_none()
        
        if not documento:
            raise NotFoundException(f"Documento {documento_id} no encontrado")
        
        # 3. Validar que el documento pertenece a la incapacidad
        if documento.incapacidad_id != incapacidad.id:
            raise ForbiddenException(
                "El documento no pertenece a esta incapacidad"
            )
        
        # 4. Validar que el tipo de documento es público
        if documento.tipo_documento not in TIPOS_DOCUMENTOS_PUBLICOS:
            raise ForbiddenException(
                "Este tipo de documento no es público"
            )
        
        # 5. Generar presigned URL (15 minutos = 900 segundos)
        try:
            presigned_url = storage_backend.get_presigned_url(
                object_path=documento.ruta_storage,
                expires=timedelta(minutes=15)
            )
        except Exception as e:
            raise BadRequestException(
                f"Error generando URL de descarga: {str(e)}"
            )
        
        # 6. Construir response
        return PresignedUrlResponse(
            url=presigned_url,
            expires_in=900,  # 15 minutos en segundos
            nombre_archivo=documento.nombre_archivo,
            tipo_documento=documento.tipo_documento
        )


# Singleton instance
incapacidad_service = IncapacidadService()

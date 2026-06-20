"""
API endpoints para gestión de Incapacidades.
"""
from __future__ import annotations

import io
from typing import Any, List, Optional
from uuid import UUID
from datetime import date, datetime

from fastapi import APIRouter, Depends, Query, Path, status, Body, HTTPException, Form, File, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel as _BM
from sqlalchemy import select as sa_select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.pre_incapacidad import PreIncapacidad
from app.schemas.incapacidad import (
    IncapacidadCreate,
    IncapacidadUpdate,
    IncapacidadInDB,
    IncapacidadAuditar,
    ConsultaIncapacidadPublicResponse,
    IncapacidadPendienteResponse,
    IncapacidadDetalleResponse,
    IncapacidadStatsResponse,
    IncapacidadStatsExtendedResponse,
    EmpleadoFallback,
    EmpresaFallback,
)
from app.schemas.documento import PresignedUrlResponse
from app.schemas.historial_estado import HistorialEstadoResponse
from app.schemas.auditoria_datos import AuditoriaDatosAprobadosResponse
from app.schemas.empleado import EmpleadoResponse
from app.schemas.empresa import EmpresaResponse
from app.schemas.afiliado import AfiliadoResponse
from app.schemas.siniestro import SiniestroInDB
from app.schemas.validation_inconsistencia import ValidationInconsistenciaRead, ValidacionesResponse
from app.schemas.radicacion import RadicacionResponse
from app.db.repositories.validation_inconsistencia_repository import ValidationInconsistenciaRepository
from app.services.incapacidad_service import incapacidad_service
from app.services.historial_estado_service import historial_estado_service
from app.utils.enums import EstadoIncapacidad, TipoIncapacidad, Prioridad
from app.core.exceptions import BadRequestException
from app.core.security import get_current_user, PermissionChecker, Permissions, require_empresa
from app.models.usuario import Usuario
from app.tasks.incapacidad_tasks import radicar_incapacidad_automatica_task
from app.core.logging import logger
from app.services.bulk_radicacion_service import generar_plantilla, parsear_y_validar, mapear_zip
from app.schemas.radicacion import RadicacionRowInput
from app.services.radicacion_pipeline_service import RadicacionPipelineService
from app.services.integracion.integracion_service import IntegracionService
from app.services.incapacidad_validation_rules import validate_row
from app.services.catalogo_service import catalogo_service
from app.services.documento_service import DocumentoService
from app.tasks.incapacidad_tasks import enqueue_auditoria_incapacidad
from app.utils.enums import TipoDocumentoAdjunto

router = APIRouter()


class PlantillaRequest(_BM):
    empleado_ids: List[UUID] = []


# ========== HELPER FUNCTIONS ==========

def _serialize_incapacidad(incap) -> dict:
    """
    Convierte objeto SQLAlchemy Incapacidad a dict serializable.
    
    Maneja la conversión de objetos relacionados (empleado, empresa, afiliado)
    de SQLAlchemy a Pydantic para evitar PydanticSerializationError.
    
    Args:
        incap: Objeto Incapacidad de SQLAlchemy
        
    Returns:
        Dict serializable con objetos relacionados convertidos a Pydantic
    """
    logger.info(f"Serializando incapacidad {incap.id}")
    # Convertir incapacidad base
    incap_dict = IncapacidadInDB.model_validate(incap).model_dump()
    logger.info(f"Vamos a convertir objetos relacionados para incapacidad {incap.id}")
    # Convertir objetos relacionados a schemas Pydantic
    if incap.empleado:
        incap_dict['empleado'] = EmpleadoResponse.model_validate(incap.empleado).model_dump()
    if incap.empresa:
        incap_dict['empresa'] = EmpresaResponse.model_validate(incap.empresa).model_dump()
    if incap.afiliado:
        incap_dict['afiliado'] = AfiliadoResponse.model_validate(incap.afiliado).model_dump()
    
    # imprimir en el log todo el diccionario
    logger.info(f"Incapacidad serializada: {incap_dict}")
    return incap_dict


# ========== ENDPOINTS PÚBLICOS (SIN AUTENTICACIÓN) ==========

@router.get(
    "/consultar",
    response_model=ConsultaIncapacidadPublicResponse,
    summary="Consultar incapacidad pública (sin autenticación)",
    description="Permite consultar el estado de una incapacidad por número o documento",
    tags=["incapacidades-publico"],
    responses={
        200: {
            "description": "Incapacidad encontrada",
            "content": {
                "application/json": {
                    "example": {
                        "numero": "INC-ARL-20260117-0001",
                        "estado": "EN_AUDITORIA",
                        "tipo": "ARL",
                        "fecha_inicio": "2026-01-10",
                        "fecha_fin": "2026-01-20",
                        "dias_totales": 11,
                        "nombre_completo": "Juan Pérez García",
                        "tipo_documento": "CC",
                        "diagnostico_cie10": "S06.0",
                        "descripcion_diagnostico": "Conmoción cerebral",
                        "eps": "EPS Salud Total",
                        "historial_estados": [
                            {
                                "estado": "RADICADA",
                                "fecha_cambio": "2026-01-10T09:00:00",
                                "observaciones": None
                            },
                            {
                                "estado": "EN_AUDITORIA",
                                "fecha_cambio": "2026-01-11T14:30:00",
                                "observaciones": None
                            }
                        ],
                        "documentos": [
                            {
                                "id": "550e8400-e29b-41d4-a716-446655440000",
                                "nombre_archivo": "incapacidad_medica.pdf",
                                "tipo_documento": "INCAPACIDAD_MEDICA",
                                "tamanio_kb": 450,
                                "fecha_upload": "2026-01-10T09:05:00"
                            }
                        ],
                        "observaciones_publicas": None,
                        "created_at": "2026-01-10T09:00:00",
                        "updated_at": "2026-01-11T14:30:00"
                    }
                }
            }
        },
        400: {
            "description": "Parámetros inválidos",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Debe proporcionar número de radicación O documento + tipo_documento"
                    }
                }
            }
        },
        404: {
            "description": "Incapacidad no encontrada",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "No se encontró ninguna incapacidad con los datos proporcionados"
                    }
                }
            }
        }
    }
)
async def consultar_incapacidad_publica(
    numero: Optional[str] = Query(
        None,
        description="Número de radicación (ej: INC-ARL-20260117-0001)",
        min_length=10,
        max_length=50
    ),
    documento: Optional[str] = Query(
        None,
        description="Número de documento de identidad",
        min_length=5,
        max_length=20
    ),
    tipo_documento: Optional[str] = Query(
        None,
        description="Tipo de documento (CC, CE, TI, PASAPORTE, PEP)"
    ),
    db: AsyncSession = Depends(get_db)
):
    """
    Consulta pública de incapacidad **SIN AUTENTICACIÓN**.
    
    ## Dos modos de búsqueda:
    
    ### 1. Por número de radicación:
    - **Parámetro**: `numero` (ej: INC-ARL-20260117-0001)
    
    **Ejemplo**:
    ```
    GET /api/v1/incapacidades/consultar?numero=INC-ARL-20260117-0001
    ```
    
    ### 2. Por documento de identidad:
    - **Parámetros**: `documento` + `tipo_documento`
    
    **Ejemplo**:
    ```
    GET /api/v1/incapacidades/consultar?documento=1234567890&tipo_documento=CC
    ```
    
    ## Retorna:
    - Información básica de la incapacidad
    - Timeline de estados (historial completo)
    - Lista de documentos descargables (solo públicos)
    - Observaciones del auditor (si las hay)
    - Información de contacto para soporte
    
    ## Nota de seguridad:
    - Los datos sensibles están **sanitizados**
    - No se incluyen: valores monetarios, cuentas bancarias, IDs internos
    - Solo se muestran documentos públicos: INCAPACIDAD_MEDICA, CEDULA, HISTORIA_CLINICA
    
    ## Rate limiting:
    - Máximo 20 requests por minuto por IP
    """
    # Validar parámetros
    if not numero and not (documento and tipo_documento):
        raise BadRequestException(
            "Debe proporcionar número de radicación O documento + tipo_documento"
        )
    
    # Consultar incapacidad
    result = await incapacidad_service.consultar_incapacidad_publica(
        db=db,
        numero=numero,
        documento=documento,
        tipo_documento=tipo_documento
    )
    
    return result


@router.get(
    "/{numero}/documentos/{documento_id}/download",
    response_model=PresignedUrlResponse,
    summary="Descargar documento público (sin autenticación)",
    description="Genera URL de descarga temporal para un documento público",
    tags=["incapacidades-publico"],
    responses={
        200: {
            "description": "URL de descarga generada exitosamente",
            "content": {
                "application/json": {
                    "example": {
                        "url": "http://localhost:9010/documentos/550e8400-e29b-41d4-a716-446655440000.pdf?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=...",
                        "expires_in": 900,
                        "nombre_archivo": "incapacidad_medica.pdf",
                        "tipo_documento": "INCAPACIDAD_MEDICA"
                    }
                }
            }
        },
        404: {
            "description": "Incapacidad o documento no encontrado",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Incapacidad INC-202601-000001 no encontrada"
                    }
                }
            }
        },
        403: {
            "description": "Documento no público o no pertenece a la incapacidad",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Este tipo de documento no es público"
                    }
                }
            }
        }
    }
)
async def descargar_documento_publico(
    numero: str = Path(
        ...,
        description="Número de radicación de la incapacidad",
        example="INC-ARL-20260117-0001"
    ),
    documento_id: UUID = Path(
        ...,
        description="ID del documento a descargar"
    ),
    db: AsyncSession = Depends(get_db)
):
    """
    Genera URL de descarga temporal (15 minutos) para documento público **SIN AUTENTICACIÓN**.
    
    ## Validaciones:
    - El documento debe pertenecer a la incapacidad especificada
    - El tipo de documento debe ser público (INCAPACIDAD_MEDICA, CEDULA, HISTORIA_CLINICA)
    
    ## Retorna:
    - URL pre-firmada válida por 15 minutos
    - Metadata del documento (nombre, tipo)
    
    ## Tipos de documentos públicos:
    - `INCAPACIDAD_MEDICA`: Documento médico de incapacidad
    - `CEDULA`: Cédula de ciudadanía o documento de identidad
    - `HISTORIA_CLINICA`: Historia clínica relacionada
    
    ## Tipos de documentos NO públicos:
    - `SOPORTE_PAGO`: Requiere autenticación
    - `OTROS`: Requiere autenticación
    
    ## Rate limiting:
    - Máximo 10 descargas por hora por IP
    """
    result = await incapacidad_service.descargar_documento_publico(
        db=db,
        numero=numero,
        documento_id=documento_id
    )
    
    return result


# ========== ENDPOINTS PROTEGIDOS (CON AUTENTICACIÓN) ==========


@router.get(
    "/pendientes",
    response_model=List[IncapacidadPendienteResponse],
    summary="Listar incapacidades pendientes de auditoría",
    description="Obtiene incapacidades en estados RADICADA, EN_AUDITORIA, OBSERVADA ordenadas por prioridad y antigüedad",
    tags=["incapacidades-auditoria"],
    dependencies=[Depends(PermissionChecker([Permissions.INCAPACIDAD_READ]))],
)
async def listar_incapacidades_pendientes(
    db: AsyncSession = Depends(get_db),
    tipo: Optional[TipoIncapacidad] = Query(None, description="Filtrar por tipo (ARL/SALUD)"),
    prioridad: Optional[Prioridad] = Query(None, description="Filtrar por prioridad"),
    empresa_nit: Optional[str] = Query(None, description="Filtrar por NIT de empresa (solo ARL)"),
    dias_antiguedad_min: Optional[int] = Query(None, ge=0, description="Días mínimos desde radicación"),
    skip: int = Query(0, ge=0, description="Offset para paginación"),
    limit: int = Query(100, ge=1, le=500, description="Límite de resultados"),
    current_user: Usuario = Depends(get_current_user)
) -> List[IncapacidadPendienteResponse]:
    """
    Listar incapacidades pendientes de auditoría.
    
    Filtra automáticamente por estados: RADICADA, EN_AUDITORIA, OBSERVADA.
    Ordena por prioridad (URGENTE → ALTA → NORMAL → BAJA) y luego por antigüedad.
    
    ## Filtros disponibles:
    - **tipo**: ARL o SALUD
    - **prioridad**: URGENTE, ALTA, NORMAL, BAJA
    - **empresa_nit**: NIT de empresa (solo para incapacidades ARL)
    - **dias_antiguedad_min**: Días mínimos desde que fue radicada
    
    ## Campos calculados en respuesta:
    - **dias_desde_radicacion**: Días transcurridos desde la radicación
    - **dias_en_estado_actual**: Días que lleva en el estado actual
    
    ## Ordenamiento:
    1. Por prioridad descendente (URGENTE primero)
    2. Por antigüedad ascendente (más antiguas primero)
    
    ## Permisos requeridos:
    - INCAPACIDAD_READ (roles: AUDITOR, APROBADOR, ADMIN)
    """
    incapacidades = await incapacidad_service.listar_pendientes(
        db=db,
        tipo=tipo,
        prioridad=prioridad,
        empresa_nit=empresa_nit,
        dias_antiguedad_min=dias_antiguedad_min,
        skip=skip,
        limit=limit
    )
    
    # Convertir objetos SQLAlchemy a schemas Pydantic
    result: list[dict] = []
    ids_sin_empleado: list[UUID] = []

    for item in incapacidades:
        # item es un dict con 'incapacidad' y campos calculados
        incap = item['incapacidad']

        # Convertir a dict base
        incap_dict = IncapacidadInDB.model_validate(incap).model_dump()

        # Agregar campos calculados
        incap_dict['dias_desde_radicacion'] = item['dias_desde_radicacion']
        incap_dict['dias_en_estado_actual'] = item['dias_en_estado_actual']

        # Inicializar fallback fields
        incap_dict['empleado_fallback'] = None
        incap_dict['empresa_fallback'] = None

        # Convertir objetos relacionados a schemas
        if incap.empleado:
            incap_dict['empleado'] = EmpleadoResponse.model_validate(incap.empleado).model_dump()
        if incap.empresa:
            incap_dict['empresa'] = EmpresaResponse.model_validate(incap.empresa).model_dump()
        if incap.afiliado:
            incap_dict['afiliado'] = AfiliadoResponse.model_validate(incap.afiliado).model_dump()

        if not incap.empleado_id:
            ids_sin_empleado.append(incap.id)

        result.append(incap_dict)

    # Batch query — one SELECT for all incapacidades without empleado
    if ids_sin_empleado:
        pre_rows = (
            await db.execute(
                sa_select(
                    PreIncapacidad.incapacidad_id,
                    PreIncapacidad.empleado_nombres,
                    PreIncapacidad.empleado_numero_documento,
                    PreIncapacidad.empresa_nit,
                    PreIncapacidad.empresa_nombre,
                ).where(PreIncapacidad.incapacidad_id.in_(ids_sin_empleado))
            )
        ).all()

        fallback_map: dict[str, Any] = {str(row.incapacidad_id): row for row in pre_rows}

        for item_dict in result:
            inc_id = str(item_dict['id'])
            if inc_id in fallback_map:
                row = fallback_map[inc_id]
                if row.empleado_nombres:
                    item_dict['empleado_fallback'] = EmpleadoFallback(
                        nombres=row.empleado_nombres,
                        numero_documento=row.empleado_numero_documento or '',
                    ).model_dump()
                if row.empresa_nit:
                    item_dict['empresa_fallback'] = EmpresaFallback(
                        nit=row.empresa_nit,
                        nombre=row.empresa_nombre or row.empresa_nit,
                    ).model_dump()

    return result



@router.post(
    "/",
    response_model=IncapacidadInDB,
    status_code=status.HTTP_201_CREATED,
    summary="Crear incapacidad",
    description="Crea una nueva incapacidad (ARL o SALUD) con validaciones de negocio"
)
async def create_incapacidad(
    incapacidad_data: IncapacidadCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Crea una nueva incapacidad.
    
    Validaciones para ARL:
    - Requiere empleado_id y empresa_id
    - El empleado debe estar ACTIVO
    - La empresa debe estar ACTIVA
    - El empleado debe pertenecer a la empresa
    
    Validaciones para SALUD:
    - Requiere afiliado_id
    - El afiliado debe estar ACTIVO
    - No debe tener empleado_id, empresa_id ni siniestro
    
    Validaciones comunes:
    - fecha_fin >= fecha_inicio
    - Genera número único automáticamente
    - Calcula días_totales automáticamente
    - Estado inicial: RADICADA
    
    **Proceso automático**:
    - Después de crear, se envía automáticamente una tarea en background
      para radicar la incapacidad (RADICADA → EN_AUDITORIA)
    """
    # Crear incapacidad
    incapacidad = await incapacidad_service.create_incapacidad(db, incapacidad_data)
    
    # Lanzar tarea de radicación automática en background (no espera)
    try:
        task = radicar_incapacidad_automatica_task.delay(str(incapacidad.id))
        logger.info(
            f"Tarea de radicación automática lanzada para incapacidad {incapacidad.numero}. "
            f"Task ID: {task.id}"
        )
    except Exception as e:
        # Si falla el lanzamiento de la tarea, loggear pero NO fallar la creación
        logger.error(
            f"Error al lanzar tarea de radicación para {incapacidad.numero}: {e}. "
            f"La incapacidad fue creada pero debe radicarse manualmente."
        )
    
    return _serialize_incapacidad(incapacidad)


@router.get(
    "/",
    response_model=List[IncapacidadInDB],
    summary="Listar incapacidades",
    description="Lista incapacidades con filtros opcionales"
)
async def list_incapacidades(
    tipo: Optional[TipoIncapacidad] = Query(None, description="Filtrar por tipo (ARL/SALUD)"),
    estado: Optional[EstadoIncapacidad] = Query(None, description="Filtrar por estado"),
    numero: Optional[str] = Query(None, description="Filtrar por número de incapacidad"),
    empleado_id: Optional[UUID] = Query(None, description="Filtrar por empleado (UUID)"),
    empleado_documento: Optional[str] = Query(None, description="Filtrar por documento de empleado"),
    afiliado_id: Optional[UUID] = Query(None, description="Filtrar por afiliado (UUID)"),
    afiliado_documento: Optional[str] = Query(None, description="Filtrar por documento de afiliado"),
    empresa_id: Optional[UUID] = Query(None, description="Filtrar por empresa (UUID)"),
    empresa_nit: Optional[str] = Query(None, description="Filtrar por NIT de empresa"),
    fecha_inicio_desde: Optional[date] = Query(None, description="Fecha inicio mínima"),
    fecha_inicio_hasta: Optional[date] = Query(None, description="Fecha inicio máxima"),
    skip: int = Query(0, ge=0, description="Número de registros a saltar"),
    limit: int = Query(100, ge=1, le=1000, description="Número máximo de registros"),
    db: AsyncSession = Depends(get_db)
):
    """
    Lista incapacidades con filtros opcionales.
    
    Filtros disponibles:
    - tipo: ARL o SALUD
    - estado: RADICADA, EN_AUDITORIA, OBSERVADA, APROBADA, RECHAZADA, EN_PAGO, PAGADA, CANCELADA
    - número: Número único de incapacidad
    - empleado_id/empleado_documento: Por empleado (UUID o documento)
    - afiliado_id/afiliado_documento: Por afiliado (UUID o documento)
    - empresa_id/empresa_nit: Por empresa (UUID o NIT)
    - fecha_inicio_desde/hasta: Rango de fechas de inicio
    
    Ordenamiento: Por fecha de radicación descendente
    """
    incapacidades = await incapacidad_service.list_incapacidades(
        db,
        tipo=tipo,
        estado=estado,
        numero=numero,
        empleado_id=empleado_id,
        empleado_documento=empleado_documento,
        afiliado_id=afiliado_id,
        afiliado_documento=afiliado_documento,
        empresa_id=empresa_id,
        empresa_nit=empresa_nit,
        fecha_inicio_desde=fecha_inicio_desde,
        fecha_inicio_hasta=fecha_inicio_hasta,
        skip=skip,
        limit=limit
    )
    
    # Convertir objetos SQLAlchemy a schemas Pydantic
    result = []
    for incap in incapacidades:
        incap_dict = IncapacidadInDB.model_validate(incap).model_dump()
        
        # Convertir objetos relacionados a schemas
        if incap.empleado:
            incap_dict['empleado'] = EmpleadoResponse.model_validate(incap.empleado).model_dump()
        if incap.empresa:
            incap_dict['empresa'] = EmpresaResponse.model_validate(incap.empresa).model_dump()
        if incap.afiliado:
            incap_dict['afiliado'] = AfiliadoResponse.model_validate(incap.afiliado).model_dump()
            
        result.append(incap_dict)
    
    return result


@router.get(
    "/mi-empresa",
    response_model=List[IncapacidadInDB],
    summary="Listar incapacidades de mi empresa",
    description="Lista las incapacidades ARL de la empresa autenticada. "
                "El empresa_id se toma del token — el cliente no puede elegir otra empresa.",
    tags=["incapacidades-empresa"]
)
async def list_mi_empresa(
    estado: Optional[EstadoIncapacidad] = Query(None, description="Filtrar por estado"),
    numero: Optional[str] = Query(None, description="Filtrar por número de incapacidad"),
    empleado_documento: Optional[str] = Query(None, description="Filtrar por documento de empleado"),
    fecha_inicio_desde: Optional[date] = Query(None, description="Fecha inicio mínima"),
    fecha_inicio_hasta: Optional[date] = Query(None, description="Fecha inicio máxima"),
    skip: int = Query(0, ge=0, description="Número de registros a saltar"),
    limit: int = Query(100, ge=1, le=1000, description="Número máximo de registros"),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_empresa),
):
    """
    Lista incapacidades ARL de la empresa del usuario autenticado.

    - empresa_id se fuerza desde el token (nunca desde el cliente).
    - tipo fijo: ARL (el portal externo gestiona sólo ARL).
    - Sólo accesible para el rol EMPRESA.
    - Filtra: estado, número, documento empleado, rango fechas.
    """
    if current_user.empresa_id is None:
        raise HTTPException(status_code=403, detail="Usuario EMPRESA sin empresa_id asignado")

    incapacidades = await incapacidad_service.list_incapacidades(
        db,
        tipo=TipoIncapacidad.ARL,
        estado=estado,
        numero=numero,
        empleado_documento=empleado_documento,
        empresa_id=current_user.empresa_id,
        fecha_inicio_desde=fecha_inicio_desde,
        fecha_inicio_hasta=fecha_inicio_hasta,
        skip=skip,
        limit=limit,
    )

    result = []
    for incap in incapacidades:
        incap_dict = IncapacidadInDB.model_validate(incap).model_dump()

        if incap.empleado:
            incap_dict['empleado'] = EmpleadoResponse.model_validate(incap.empleado).model_dump()
        if incap.empresa:
            incap_dict['empresa'] = EmpresaResponse.model_validate(incap.empresa).model_dump()
        if incap.afiliado:
            incap_dict['afiliado'] = AfiliadoResponse.model_validate(incap.afiliado).model_dump()

        result.append(incap_dict)

    return result


@router.get(
    "/stats",
    response_model=IncapacidadStatsResponse,
    summary="Estadísticas del dashboard",
    description="Obtiene métricas estadísticas del dashboard de incapacidades",
    dependencies=[Depends(PermissionChecker([Permissions.INCAPACIDAD_READ]))],
    tags=["incapacidades-dashboard"]
)
async def get_stats(
    empresa_id: Optional[UUID] = Query(None, description="Filtrar por empresa"),
    tipo: Optional[TipoIncapacidad] = Query(None, description="Filtrar por tipo (ARL/SALUD)"),
    fecha_desde: Optional[date] = Query(None, description="Filtrar desde fecha (YYYY-MM-DD)"),
    fecha_hasta: Optional[date] = Query(None, description="Filtrar hasta fecha (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> IncapacidadStatsResponse:
    """
    Obtener estadísticas del dashboard de incapacidades.
    
    Métricas calculadas:
    - **Pendientes**: Incapacidades en RADICADA o EN_AUDITORIA
    - **Auditadas Hoy**: Incapacidades que cambiaron a APROBADA/RECHAZADA/OBSERVADA hoy
    - **Próximas a Vencer**: Incapacidades con más de 7 días sin cambio de estado
    - **Rechazadas/Observadas**: Incapacidades en RECHAZADA u OBSERVADA
    
    Filtros opcionales:
    - empresa_id: ID de la empresa
    - tipo: ARL o SALUD
    - fecha_desde/fecha_hasta: Rango de fechas de creación
    
    Requiere permisos: INCAPACIDAD_READ
    Roles permitidos: ADMIN, AUDITOR, APROBADOR
    
    Example:
        GET /api/v1/incapacidades/stats?tipo=ARL&fecha_desde=2026-01-01
    """
    # Validar rango de fechas
    if fecha_desde and fecha_hasta and fecha_desde > fecha_hasta:
        raise HTTPException(
            status_code=400,
            detail="fecha_desde debe ser menor o igual a fecha_hasta"
        )
    
    # Obtener estadísticas
    stats = await incapacidad_service.get_stats(
        db=db,
        empresa_id=empresa_id,
        tipo=tipo,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
    )
    
    # Construir response con metadata
    return IncapacidadStatsResponse(
        **stats,
        fecha_calculo=datetime.utcnow(),
        filtros_aplicados={
            "empresa_id": str(empresa_id) if empresa_id else None,
            "tipo": tipo.value if tipo else None,
            "fecha_desde": fecha_desde.isoformat() if fecha_desde else None,
            "fecha_hasta": fecha_hasta.isoformat() if fecha_hasta else None,
        } if any([empresa_id, tipo, fecha_desde, fecha_hasta]) else None,
    )


@router.get(
    "/stats/extended",
    response_model=IncapacidadStatsExtendedResponse,
    summary="Estadísticas extendidas del dashboard con gráficos",
    description="Obtiene métricas estadísticas + datos agregados para visualizaciones",
    dependencies=[Depends(PermissionChecker([Permissions.INCAPACIDAD_READ]))],
    tags=["incapacidades-dashboard"]
)
async def get_extended_stats(
    empresa_id: Optional[UUID] = Query(None, description="Filtrar por empresa"),
    tipo: Optional[TipoIncapacidad] = Query(None, description="Filtrar por tipo (ARL/SALUD)"),
    fecha_desde: Optional[date] = Query(None, description="Filtrar desde fecha (YYYY-MM-DD)"),
    fecha_hasta: Optional[date] = Query(None, description="Filtrar hasta fecha (YYYY-MM-DD)"),
    top_limit: int = Query(10, ge=5, le=20, description="Límite para rankings TOP"),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> IncapacidadStatsExtendedResponse:
    """
    Obtener estadísticas extendidas del dashboard con datos para gráficos.
    
    Incluye:
    - **Métricas básicas**: pendientes, auditadas_hoy, proximas_vencer, rechazadas_observadas
    - **Top 10 Empresas**: Por cantidad de radicaciones
    - **Top 10 Diagnósticos CIE-10**: Más frecuentes con porcentaje
    - **Top 10 Empleados**: Con más días acumulados de incapacidad
    - **Distribución Estados**: Pendientes por estado (Pie Chart)
    - **Distribución Tipos**: ARL vs SALUD con valores (Donut Chart)
    - **Tendencia Mensual**: Últimos 6 meses (Line Chart)
    
    Filtros opcionales:
    - empresa_id: ID de empresa (solo stats de esa empresa)
    - tipo: ARL o SALUD (excluye el otro tipo)
    - fecha_desde/fecha_hasta: Rango de fechas de creación
    - top_limit: Cuántos items mostrar en rankings (5-20)
    
    Requiere permisos: INCAPACIDAD_READ
    Roles permitidos: ADMIN, AUDITOR, APROBADOR
    
    Example:
        GET /api/v1/incapacidades/stats/extended?tipo=ARL&top_limit=5
    """
    # Validar rango de fechas
    if fecha_desde and fecha_hasta and fecha_desde > fecha_hasta:
        raise HTTPException(
            status_code=400,
            detail="fecha_desde debe ser menor o igual a fecha_hasta"
        )
    
    # Obtener estadísticas extendidas
    stats = await incapacidad_service.get_extended_stats(
        db=db,
        empresa_id=empresa_id,
        tipo=tipo,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        top_limit=top_limit,
    )
    
    # Construir response con metadata
    return IncapacidadStatsExtendedResponse(
        **stats,
        fecha_calculo=datetime.utcnow(),
        filtros_aplicados={
            "empresa_id": str(empresa_id) if empresa_id else None,
            "tipo": tipo.value if tipo else None,
            "fecha_desde": fecha_desde.isoformat() if fecha_desde else None,
            "fecha_hasta": fecha_hasta.isoformat() if fecha_hasta else None,
            "top_limit": top_limit,
        } if any([empresa_id, tipo, fecha_desde, fecha_hasta]) else None,
    )


@router.post(
    "/radicar",
    response_model=RadicacionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Radicar incapacidad individual (EMPRESA)",
    tags=["incapacidades-empresa"],
)
async def radicar_individual(
    empleado_id: UUID = Form(...),
    tipo_enfermedad: str = Form(...),
    fecha_inicio: date = Form(...),
    fecha_fin: date = Form(...),
    dias_totales: int = Form(...),
    diagnostico_cie10: str = Form(...),
    nombre_medico: str = Form(...),
    registro_medico: str = Form(...),
    descripcion_diagnostico: Optional[str] = Form(None),
    ips: Optional[str] = Form(None),
    valor_dia: Optional[float] = Form(None),
    prorroga: bool = Form(False),
    observaciones: Optional[str] = Form(None),
    incapacidad_medica: List[UploadFile] = File(...),
    historia_clinica: Optional[List[UploadFile]] = File(None),
    soportes_adicionales: Optional[List[UploadFile]] = File(None),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_empresa),
):
    """Radica una incapacidad individual para usuarios EMPRESA."""
    import io as _io

    if current_user.empresa is None:
        raise HTTPException(status_code=403, detail="Usuario no vinculado a una empresa")

    row = RadicacionRowInput(
        empleado_id=empleado_id,
        tipo_enfermedad=tipo_enfermedad,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        dias_totales=dias_totales,
        diagnostico_cie10=diagnostico_cie10,
        descripcion_diagnostico=descripcion_diagnostico,
        nombre_medico=nombre_medico,
        registro_medico=registro_medico,
        ips=ips,
        valor_dia=valor_dia,
        prorroga=prorroga,
        observaciones=observaciones,
    )

    integracion = IntegracionService(db)
    pipeline = RadicacionPipelineService(db, enqueue_auditoria=enqueue_auditoria_incapacidad, integracion=integracion.procesar)
    result = await pipeline.radicar([row], empresa=current_user.empresa, radicado_por_id=current_user.id)

    item = result.items[0]
    if item.success and item.incapacidad_id:
        doc_svc = DocumentoService(db)
        grupos = {
            TipoDocumentoAdjunto.INCAPACIDAD_MEDICA.value: incapacidad_medica or [],
            TipoDocumentoAdjunto.HISTORIA_CLINICA.value: historia_clinica or [],
            TipoDocumentoAdjunto.OTROS.value: soportes_adicionales or [],
        }
        for tipo, archivos in grupos.items():
            for f in archivos:
                content = await f.read()
                await doc_svc.upload_documento(
                    incapacidad_id=item.incapacidad_id,
                    file_data=_io.BytesIO(content),
                    filename=f.filename,
                    content_type=f.content_type or "application/octet-stream",
                    tipo_documento=tipo,
                    uploaded_by_id=current_user.id,
                )
        await db.commit()

        if current_user.empresa.email_contacto:
            from app.tasks.email_tasks import send_email_task
            cuerpo = "Se radicaron las siguientes incapacidades:<br>" + f"- {item.numero}"
            try:
                send_email_task.delay(
                    to=current_user.empresa.email_contacto,
                    subject="Confirmación de radicación de incapacidades",
                    html_body=cuerpo,
                )
            except Exception as exc:
                # El correo no debe bloquear una radicación exitosa (broker caído, etc.)
                logger.error(f"No se pudo encolar el correo de resumen de radicación: {exc}")

    return result


@router.post(
    "/radicar-masiva/plantilla",
    summary="Descargar plantilla Excel (EMPRESA)",
    tags=["incapacidades-empresa"],
)
async def descargar_plantilla(
    payload: PlantillaRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_empresa),
):
    """Genera y descarga una plantilla Excel para radicación masiva.

    - Sin `empleado_ids`: devuelve solo la fila de cabecera.
    - Con `empleado_ids`: pre-rellena filas con datos de los empleados
      que pertenecen a la empresa del usuario autenticado.
    """
    content = await generar_plantilla(db, current_user.empresa_id, payload.empleado_ids)
    return StreamingResponse(
        io.BytesIO(content),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=plantilla_incapacidades.xlsx"},
    )


@router.post(
    "/radicar-masiva/validar",
    summary="Validar Excel masivo (EMPRESA)",
    tags=["incapacidades-empresa"],
)
async def validar_masivo(
    archivo: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_empresa),
):
    """Valida cada fila del Excel subido y devuelve resultados por fila.

    - Las filas completamente vacías son omitidas.
    - Cada empleado se resuelve por numero_documento dentro de la empresa autenticada.
    - Se retornan TODOS los errores por fila (no solo el primero).
    - ``valida=True`` solo cuando no hay errores de nivel ERROR.
    """
    content = await archivo.read()
    filas = await parsear_y_validar(db, current_user.empresa_id, content)
    return {
        "filas": filas,
        "total": len(filas),
        "validas": sum(1 for f in filas if f["valida"]),
    }


@router.post(
    "/radicar-masiva/zip",
    summary="Mapear ZIP de documentos (EMPRESA)",
    tags=["incapacidades-empresa"],
)
async def mapear_zip_masivo(
    archivo: UploadFile = File(...),
    documentos_esperados: str = Form(""),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_empresa),
):
    """Parsea un ZIP y mapea cada archivo al (numero_documento, tipo) correcto.

    Los bytes del archivo se mantienen en el cliente; este endpoint solo valida el mapeo.
    Convención de nombre: ``{numero_documento}_{TIPO}.{ext}``
    """
    content = await archivo.read()
    esperados = {d.strip() for d in documentos_esperados.split(",") if d.strip()}
    try:
        asignaciones = mapear_zip(content, esperados)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"asignaciones": asignaciones}


@router.post(
    "/radicar-masiva",
    response_model=RadicacionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Radicar incapacidades masivas (EMPRESA)",
    tags=["incapacidades-empresa"],
)
async def radicar_masiva(
    filas: str = Form(...),
    documentos: list[UploadFile] = File(default=[]),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_empresa),
):
    """Radica en lote incapacidades pre-validadas para usuarios EMPRESA.

    ``filas``: arreglo JSON de filas validadas por el cliente. El servidor
    re-valida cada fila (seguridad: nunca confiar en el cliente).

    ``documentos``: lista de UploadFile nombrados ``{empleado_id}__{TIPO}.{ext}``
    donde TIPO ∈ INCAPACIDAD | HISTORIA_CLINICA | SOPORTE.
    """
    import io as _io
    import json as _json

    # --- Parse the JSON payload -----------------------------------------------
    try:
        raw_rows = _json.loads(filas)
        if not isinstance(raw_rows, list):
            raise ValueError
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=400,
            detail="El campo 'filas' debe ser un arreglo JSON válido",
        )

    if current_user.empresa is None:
        raise HTTPException(status_code=403, detail="Usuario no vinculado a una empresa")

    # --- Server-side re-validation (never trust the client) -------------------
    parsed_rows: list[RadicacionRowInput] = []
    invalidas: list[dict] = []

    # Catálogo CIE-10: verificar existencia de los códigos en una sola consulta.
    # Un código con formato válido pero inexistente se rechaza (CIE10_NO_EXISTE).
    codigos_cie10 = {
        str(r["diagnostico_cie10"]).strip().upper()
        for r in raw_rows
        if isinstance(r, dict) and r.get("diagnostico_cie10")
    }
    catalogo_set = await catalogo_service.codigos_existentes(db, codigos_cie10)

    for r in raw_rows:
        empleado_id_raw = r.get("empleado_id")

        # Parse dates (may raise on bad input)
        try:
            fi = date.fromisoformat(r["fecha_inicio"])
            ff = date.fromisoformat(r["fecha_fin"])
        except (KeyError, ValueError, TypeError):
            invalidas.append({
                "empleado_id": empleado_id_raw,
                "errores": [{"codigo": "INVALID_FECHA", "descripcion": "Fechas faltantes o inválidas"}],
            })
            continue

        # Build the dict expected by validate_row (uses empleado_numero_documento as presence proxy)
        row_dict = {
            "tipo": "ARL",
            "empleado_numero_documento": empleado_id_raw,  # non-empty = present
            "tipo_enfermedad": r.get("tipo_enfermedad"),
            "fecha_inicio": fi,
            "fecha_fin": ff,
            "dias_totales": r.get("dias_totales"),
            "diagnostico_cie10": r.get("diagnostico_cie10"),
            "nombre_medico": r.get("nombre_medico"),
            "registro_medico": r.get("registro_medico"),
        }
        issues = validate_row(row_dict, catalogo_codigos=catalogo_set)
        # Only ERROR-level issues block the batch
        error_issues = [i for i in issues if i.get("severidad") == "ERROR"]
        if error_issues:
            invalidas.append({"empleado_id": empleado_id_raw, "errores": error_issues})
            continue

        try:
            parsed_rows.append(RadicacionRowInput(
                empleado_id=empleado_id_raw,
                tipo_enfermedad=r["tipo_enfermedad"],
                fecha_inicio=fi,
                fecha_fin=ff,
                dias_totales=r["dias_totales"],
                diagnostico_cie10=r["diagnostico_cie10"],
                descripcion_diagnostico=r.get("descripcion_diagnostico"),
                nombre_medico=r["nombre_medico"],
                registro_medico=r["registro_medico"],
                ips=r.get("ips"),
                valor_dia=r.get("valor_dia"),
                prorroga=bool(r.get("prorroga")),
                observaciones=r.get("observaciones"),
            ))
        except Exception as exc:
            invalidas.append({
                "empleado_id": empleado_id_raw,
                "errores": [{"codigo": "PARSE_ERROR", "descripcion": str(exc)}],
            })

    if invalidas:
        raise HTTPException(status_code=422, detail={"filas_invalidas": invalidas})

    # --- Run shared pipeline ---------------------------------------------------
    integracion = IntegracionService(db)
    pipeline = RadicacionPipelineService(
        db,
        enqueue_auditoria=enqueue_auditoria_incapacidad,
        integracion=integracion.procesar,
    )
    result = await pipeline.radicar(
        parsed_rows,
        empresa=current_user.empresa,
        radicado_por_id=current_user.id,
    )

    # --- Attach documents mapped by "{empleado_id}__{TIPO}.{ext}" -------------
    TIPO_MAP = {
        "INCAPACIDAD": TipoDocumentoAdjunto.INCAPACIDAD_MEDICA.value,
        "HISTORIA_CLINICA": TipoDocumentoAdjunto.HISTORIA_CLINICA.value,
        "SOPORTE": TipoDocumentoAdjunto.OTROS.value,
    }
    by_empleado = {
        str(i.empleado_id): i
        for i in result.items
        if i.success and i.incapacidad_id
    }
    doc_failures: list[dict] = []
    doc_svc = DocumentoService(db)
    for f in documentos:
        try:
            empleado_id_str, rest = f.filename.split("__", 1)
            tipo_token = rest.rsplit(".", 1)[0]
        except (ValueError, AttributeError):
            doc_failures.append({"filename": f.filename, "motivo": "nombre_invalido"})
            continue
        item = by_empleado.get(empleado_id_str)
        if not item:
            doc_failures.append({"filename": f.filename, "motivo": "empleado_no_radicado"})
            continue
        content = await f.read()
        try:
            await doc_svc.upload_documento(
                incapacidad_id=item.incapacidad_id,
                file_data=_io.BytesIO(content),
                filename=f.filename,
                content_type=f.content_type or "application/octet-stream",
                tipo_documento=TIPO_MAP.get(tipo_token, TipoDocumentoAdjunto.OTROS.value),
                uploaded_by_id=current_user.id,
            )
        except Exception as exc:
            logger.error(f"Error subiendo documento {f.filename!r}: {exc}")
            doc_failures.append({"filename": f.filename, "motivo": str(exc)})
    await db.commit()
    result.documentos_ignorados = doc_failures

    # --- Fault-isolated summary email -----------------------------------------
    if result.total_radicadas and current_user.empresa.email_contacto:
        from app.tasks.email_tasks import send_email_task
        numeros = [i.numero for i in result.items if i.success]
        cuerpo = (
            "Se radicaron las siguientes incapacidades:<br>"
            + "<br>".join(f"- {n}" for n in numeros)
        )
        try:
            send_email_task.delay(
                to=current_user.empresa.email_contacto,
                subject="Confirmación de radicación masiva de incapacidades",
                html_body=cuerpo,
            )
        except Exception as exc:
            logger.error(f"No se pudo encolar el correo de resumen masivo: {exc}")

    return result


@router.get(
    "/{incapacidad_id}",
    response_model=IncapacidadDetalleResponse,
    summary="Obtener incapacidad detallada",
    description="Obtiene una incapacidad por su ID con objetos completos de relaciones",
    dependencies=[Depends(PermissionChecker([Permissions.INCAPACIDAD_READ]))]
)
async def get_incapacidad(
    incapacidad_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtiene una incapacidad específica por ID con información completa.
    
    **Requiere autenticación JWT** y permisos de lectura de incapacidades.
    
    Retorna:
    - **Datos completos de la incapacidad**
    - **Empleado completo** (si es tipo ARL)
    - **Empresa completa** (si es tipo ARL)
    - **Afiliado completo** (si es tipo SALUD)
    - **Lista de siniestros del empleado** (si es tipo ARL)
    - Fechas, valores y estados
    - Información de auditoría
    
    Ejemplo de uso:
    ```
    GET /api/v1/incapacidades/550e8400-e29b-41d4-a716-446655440000
    Headers: Authorization: Bearer <jwt_token>
    ```
    """
    # Obtener incapacidad con relaciones cargadas
    incapacidad = await incapacidad_service.get_incapacidad(db, incapacidad_id, with_relations=True)
    
    # Convertir a dict base usando IncapacidadInDB
    incap_dict = IncapacidadInDB.model_validate(incapacidad).model_dump()
    
    # Agregar objetos relacionados convertidos a schemas Pydantic
    if incapacidad.empleado:
        incap_dict["empleado"] = EmpleadoResponse.model_validate(incapacidad.empleado).model_dump()
    
    if incapacidad.empresa:
        incap_dict["empresa"] = EmpresaResponse.model_validate(incapacidad.empresa).model_dump()
    
    if incapacidad.afiliado:
        incap_dict["afiliado"] = AfiliadoResponse.model_validate(incapacidad.afiliado).model_dump()
    
    # Agregar siniestros del empleado (ya están en el objeto incapacidad desde el service)
    if hasattr(incapacidad, 'siniestros_empleado') and incapacidad.siniestros_empleado:
        incap_dict["siniestros_empleado"] = [
            SiniestroInDB.model_validate(s).model_dump() 
            for s in incapacidad.siniestros_empleado
        ]
    
    return incap_dict


@router.put(
    "/{incapacidad_id}",
    response_model=IncapacidadInDB,
    summary="Actualizar incapacidad",
    description="Actualiza los datos de una incapacidad"
)
async def update_incapacidad(
    incapacidad_id: UUID,
    incapacidad_data: IncapacidadUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Actualiza los datos de una incapacidad.
    
    Restricciones:
    - Solo se puede actualizar en estados: RADICADA, OBSERVADA
    - Si se actualizan fechas, se recalculan días_totales
    - Actualiza el campo updated_at automáticamente
    
    Nota: Solo se actualizan los campos proporcionados (PATCH semántico)
    """
    incap = await incapacidad_service.update_incapacidad(db, incapacidad_id, incapacidad_data)
    return _serialize_incapacidad(incap)


@router.post(
    "/{incapacidad_id}/radicar",
    response_model=IncapacidadInDB,
    summary="Radicar incapacidad",
    description="Radica una incapacidad para auditoría (RADICADA → EN_AUDITORIA)"
)
async def radicar_incapacidad(
    incapacidad_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Radica una incapacidad para que pase a auditoría.
    
    Transición: RADICADA → EN_AUDITORIA
    
    Validaciones:
    - Debe estar en estado RADICADA
    - Registra fecha de radicación
    """
    incap = await incapacidad_service.radicar_incapacidad(db, incapacidad_id)
    return _serialize_incapacidad(incap)


@router.post(
    "/{incapacidad_id}/auditar",
    response_model=IncapacidadInDB,
    summary="Auditar incapacidad",
    description="Audita una incapacidad con soporte para aprobación parcial"
)
async def auditar_incapacidad(
    incapacidad_id: UUID,
    auditoria: IncapacidadAuditar,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Audita una incapacidad con soporte para aprobación parcial.
    
    Acciones disponibles:
    - SOLICITAR_INFORMACION: Pasa a OBSERVADA (requiere aclaración)
    - APROBAR_PARA_PAGO: Pasa a APROBADA (100% de días aprobados)
    - APROBAR_PARA_PAGO_PARCIAL: Pasa a APROBADA_PARCIALMENTE (días menores a solicitados)
    - RECHAZAR: Pasa a RECHAZADA (no procede)
    
    Para APROBAR_PARA_PAGO_PARCIAL se requieren campos adicionales:
    - fecha_inicio_aprobada
    - fecha_fin_aprobada
    - dias_aprobados
    - cie10_aprobado
    - diagnostico_aprobado
    
    Validaciones:
    - Debe estar en estado EN_AUDITORIA
    - Observaciones son obligatorias (mínimo 10 caracteres)
    - Registra fecha de auditoría y auditor
    """
    # Preparar datos aprobados si es aprobación parcial
    datos_aprobados = None
    if auditoria.accion == "APROBAR_PARA_PAGO_PARCIAL":
        datos_aprobados = {
            'fecha_inicio_aprobada': auditoria.fecha_inicio_aprobada,
            'fecha_fin_aprobada': auditoria.fecha_fin_aprobada,
            'dias_aprobados': auditoria.dias_aprobados,
            'cie10_aprobado': auditoria.cie10_aprobado,
            'diagnostico_aprobado': auditoria.diagnostico_aprobado,
        }
    
    incap = await incapacidad_service.auditar_incapacidad(
        db,
        incapacidad_id,
        auditoria.accion,
        auditoria.observaciones,
        current_user.id,
        datos_aprobados=datos_aprobados
    )
    logger.info(f"Incapacidad {incapacidad_id} auditada con acción {auditoria.accion} por usuario {current_user.id}")
    return _serialize_incapacidad(incap)


@router.post(
    "/{incapacidad_id}/aprobar",
    response_model=IncapacidadInDB,
    summary="Aprobar incapacidad",
    description="Aprueba una incapacidad para pago"
)
async def aprobar_incapacidad(
    incapacidad_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)  
):
    """
    Aprueba una incapacidad para pago.
    
    Transición: EN_AUDITORIA → APROBADA
    
    Validaciones:
    - Debe estar en estado EN_AUDITORIA
    - Registra fecha de aprobación y aprobador
    """
    incap = await incapacidad_service.aprobar_incapacidad(db, incapacidad_id, current_user.id)
    return _serialize_incapacidad(incap)


@router.post(
    "/{incapacidad_id}/rechazar",
    response_model=IncapacidadInDB,
    summary="Rechazar incapacidad",
    description="Rechaza una incapacidad"
)
async def rechazar_incapacidad(
    incapacidad_id: UUID,
    motivo: str = Body(..., embed=True, min_length=10),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)   
):
    """
    Rechaza una incapacidad.
    
    Transición: EN_AUDITORIA u OBSERVADA → RECHAZADA
    
    Validaciones:
    - Motivo es obligatorio (mínimo 10 caracteres)
    - Registra fecha de rechazo y motivo
    """
    incap = await incapacidad_service.rechazar_incapacidad(db, incapacidad_id, motivo, current_user.id)
    return _serialize_incapacidad(incap)


@router.post(
    "/{incapacidad_id}/enviar-pago",
    response_model=IncapacidadInDB,
    summary="Enviar a pago",
    description="Envía una incapacidad aprobada a pago"
)
async def enviar_a_pago(
    incapacidad_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Envía una incapacidad aprobada a pago.
    
    Transición: APROBADA → EN_PAGO
    
    Validaciones:
    - Debe estar en estado APROBADA
    - Debe tener valor_total calculado
    """
    incap = await incapacidad_service.enviar_a_pago(db, incapacidad_id, current_user.id)
    return _serialize_incapacidad(incap)


@router.post(
    "/{incapacidad_id}/marcar-pagada",
    response_model=IncapacidadInDB,
    summary="Marcar como pagada",
    description="Marca una incapacidad como pagada"
)
async def marcar_como_pagada(
    incapacidad_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Marca una incapacidad como pagada.
    
    Transición: EN_PAGO → PAGADA
    
    Validaciones:
    - Debe estar en estado EN_PAGO
    - Estado final del workflow
    """
    incap = await incapacidad_service.marcar_como_pagada(db, incapacidad_id, current_user.id)
    return _serialize_incapacidad(incap)


@router.get(
    "/{incapacidad_id}/documentos",
    response_model=List[dict],
    summary="Obtener documentos",
    description="Lista todos los documentos asociados a una incapacidad"
)
async def get_documentos(
    incapacidad_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Obtiene todos los documentos asociados a una incapacidad.
    
    Retorna una lista con:
    - ID del documento
    - Tipo de documento
    - Nombre del archivo
    - Tamaño
    - Fecha de carga
    - URL de descarga
    
    Nota: Por ahora retorna lista vacía. Cuando se implemente el módulo
    de Documentos, retornará los documentos reales.
    """
    return await incapacidad_service.get_documentos(db, incapacidad_id)


@router.get(
    "/{incapacidad_id}/historial",
    response_model=List[HistorialEstadoResponse],
    summary="Obtener historial de estados",
    description="Lista todos los cambios de estado de una incapacidad"
)
async def get_historial(
    incapacidad_id: UUID,
    skip: int = Query(0, ge=0, description="Registros a saltar"),
    limit: int = Query(100, ge=1, le=1000, description="Máximo de registros"),
    db: AsyncSession = Depends(get_db)
):
    """
    Obtiene el historial completo de cambios de estado de una incapacidad.
    
    Retorna una lista ordenada cronológicamente (más reciente primero) con:
    - Estado anterior y nuevo
    - Fecha del cambio
    - Usuario que realizó el cambio
    - Observaciones
    
    Útil para trazabilidad y auditoría de la incapacidad.
    """
    # Validar que la incapacidad existe
    await incapacidad_service.get_incapacidad(db, incapacidad_id)
    
    # Obtener historial
    items = await historial_estado_service.get_incapacidad_history(
        db=db,
        incapacidad_id=incapacidad_id,
        skip=skip,
        limit=limit
    )
    
    return [HistorialEstadoResponse.model_validate(item) for item in items]


@router.get(
    "/{incapacidad_id}/datos-aprobados",
    response_model=Optional[AuditoriaDatosAprobadosResponse],
    summary="Obtener datos aprobados en auditoría",
    description="Devuelve los datos aprobados si la incapacidad fue aprobada parcialmente"
)
async def get_datos_aprobados(
    incapacidad_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Obtiene los datos aprobados por el auditor durante la auditoría parcial.
    
    Retorna:
    - Fechas aprobadas (inicio y fin)
    - Días aprobados
    - Código CIE-10 aprobado
    - Diagnóstico aprobado
    - Observaciones de la auditoría
    - ID del auditor y fecha de auditoría
    
    Retorna None si la incapacidad no tiene aprobación parcial.
    
    Útil para:
    - Mostrar en el frontend los datos finales aprobados vs los solicitados
    - Generar órdenes de pago con valores correctos
    - Reportes de diferencias entre solicitado y aprobado
    """
    from app.db.repositories.auditoria_datos_repository import auditoria_datos_repository
    
    # Validar que la incapacidad existe
    await incapacidad_service.get_incapacidad(db, incapacidad_id)
    
    # Obtener datos aprobados
    datos = await auditoria_datos_repository.get_by_incapacidad(db, incapacidad_id)

    # Convertir a schema Pydantic si existe
    if datos:
        return AuditoriaDatosAprobadosResponse.model_validate(datos)
    return None


@router.get(
    "/{incapacidad_id}/validaciones",
    response_model=ValidacionesResponse,
    summary="Obtener validaciones de una incapacidad",
    tags=["incapacidades-auditoria"],
)
async def get_validaciones_incapacidad(
    incapacidad_id: UUID = Path(..., description="ID de la incapacidad"),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(
        PermissionChecker([Permissions.INCAPACIDAD_READ])
    ),
) -> ValidacionesResponse:
    await incapacidad_service.get_incapacidad(db, incapacidad_id, with_relations=False)
    repo = ValidationInconsistenciaRepository(db)
    issues = await repo.get_by_incapacidad(incapacidad_id)
    issues_read = [ValidationInconsistenciaRead.model_validate(i) for i in issues]
    return ValidacionesResponse(
        issues=issues_read,
        has_errors=any(i.severidad == "ERROR" for i in issues),
        has_fraud_alert=any(i.categoria == "FRAUD_ALERT" for i in issues),
        total=len(issues),
    )

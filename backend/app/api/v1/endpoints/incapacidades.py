"""
API endpoints para gestión de Incapacidades.
"""
from __future__ import annotations

from typing import List, Optional
from uuid import UUID
from datetime import date, datetime

from fastapi import APIRouter, Depends, Query, Path, status, Body, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.incapacidad import (
    IncapacidadCreate,
    IncapacidadUpdate,
    IncapacidadInDB,
    IncapacidadAuditar,
    ConsultaIncapacidadPublicResponse,
    IncapacidadPendienteResponse,
    IncapacidadDetalleResponse,
    IncapacidadStatsResponse,
)
from app.schemas.documento import PresignedUrlResponse
from app.schemas.historial_estado import HistorialEstadoResponse
from app.schemas.empleado import EmpleadoResponse
from app.schemas.empresa import EmpresaResponse
from app.schemas.afiliado import AfiliadoResponse
from app.schemas.siniestro import SiniestroInDB
from app.services.incapacidad_service import incapacidad_service
from app.services.historial_estado_service import historial_estado_service
from app.utils.enums import EstadoIncapacidad, TipoIncapacidad, Prioridad
from app.core.exceptions import BadRequestException
from app.core.security import get_current_user, PermissionChecker, Permissions
from app.models.usuario import Usuario
from app.tasks.incapacidad_tasks import radicar_incapacidad_automatica_task
from app.core.logging import logger 

router = APIRouter()


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
    tags=["incapacidades-auditoria"]
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
    return incapacidades



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
    
    return incapacidad


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
    return await incapacidad_service.list_incapacidades(
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
    return await incapacidad_service.update_incapacidad(db, incapacidad_id, incapacidad_data)


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
    return await incapacidad_service.radicar_incapacidad(db, incapacidad_id)


@router.post(
    "/{incapacidad_id}/auditar",
    response_model=IncapacidadInDB,
    summary="Auditar incapacidad",
    description="Audita una incapacidad con diferentes acciones"
)
async def auditar_incapacidad(
    incapacidad_id: UUID,
    auditoria: IncapacidadAuditar,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Audita una incapacidad.
    
    Acciones disponibles:
    - SOLICITAR_INFORMACION: Pasa a OBSERVADA (requiere aclaración)
    - APROBAR_PARA_PAGO: Pasa a APROBADA (lista para pagar)
    - RECHAZAR: Pasa a RECHAZADA (no procede)
    
    Validaciones:
    - Debe estar en estado EN_AUDITORIA
    - Observaciones son obligatorias (mínimo 10 caracteres)
    - Registra fecha de auditoría y auditor
    """
    return await incapacidad_service.auditar_incapacidad(
        db,
        incapacidad_id,
        auditoria.accion,
        auditoria.observaciones,
        current_user.id
    )


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
    return await incapacidad_service.aprobar_incapacidad(db, incapacidad_id, current_user.id)


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
    return await incapacidad_service.rechazar_incapacidad(db, incapacidad_id, motivo, current_user.id)


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
    return await incapacidad_service.enviar_a_pago(db, incapacidad_id, current_user.id)


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
    return await incapacidad_service.marcar_como_pagada(db, incapacidad_id, current_user.id)


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

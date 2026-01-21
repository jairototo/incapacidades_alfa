"""
API endpoints para gestión de Incapacidades.
"""
from typing import List, Optional
from uuid import UUID
from datetime import date

from fastapi import APIRouter, Depends, Query, status, Body
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.incapacidad import (
    IncapacidadCreate,
    IncapacidadUpdate,
    IncapacidadInDB,
    IncapacidadAuditar,
    ConsultaIncapacidadPublicResponse,
)
from app.schemas.historial_estado import HistorialEstadoResponse
from app.services.incapacidad_service import incapacidad_service
from app.services.historial_estado_service import historial_estado_service
from app.utils.enums import EstadoIncapacidad, TipoIncapacidad, Prioridad
from app.core.exceptions import BadRequestException

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


# ========== ENDPOINTS PROTEGIDOS (CON AUTENTICACIÓN) ==========



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
    """
    return await incapacidad_service.create_incapacidad(db, incapacidad_data)


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
    empleado_id: Optional[UUID] = Query(None, description="Filtrar por empleado"),
    afiliado_id: Optional[UUID] = Query(None, description="Filtrar por afiliado"),
    empresa_id: Optional[UUID] = Query(None, description="Filtrar por empresa"),
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
    - empleado_id: UUID del empleado (para ARL)
    - afiliado_id: UUID del afiliado (para SALUD)
    - empresa_id: UUID de la empresa (para ARL)
    - fecha_inicio_desde/hasta: Rango de fechas de inicio
    
    Ordenamiento: Por fecha de radicación descendente
    """
    return await incapacidad_service.list_incapacidades(
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


@router.get(
    "/{incapacidad_id}",
    response_model=IncapacidadInDB,
    summary="Obtener incapacidad",
    description="Obtiene una incapacidad por su ID"
)
async def get_incapacidad(
    incapacidad_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Obtiene una incapacidad específica por ID.
    
    Retorna toda la información de la incapacidad incluyendo:
    - Datos de la incapacidad
    - Relaciones (empleado/afiliado/empresa según tipo)
    - Fechas y valores
    - Estado actual
    - Información de auditoría
    """
    return await incapacidad_service.get_incapacidad(db, incapacidad_id)


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
    db: AsyncSession = Depends(get_db)
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
        auditoria.observaciones
    )


@router.post(
    "/{incapacidad_id}/aprobar",
    response_model=IncapacidadInDB,
    summary="Aprobar incapacidad",
    description="Aprueba una incapacidad para pago"
)
async def aprobar_incapacidad(
    incapacidad_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Aprueba una incapacidad para pago.
    
    Transición: EN_AUDITORIA → APROBADA
    
    Validaciones:
    - Debe estar en estado EN_AUDITORIA
    - Registra fecha de aprobación y aprobador
    """
    return await incapacidad_service.aprobar_incapacidad(db, incapacidad_id)


@router.post(
    "/{incapacidad_id}/rechazar",
    response_model=IncapacidadInDB,
    summary="Rechazar incapacidad",
    description="Rechaza una incapacidad"
)
async def rechazar_incapacidad(
    incapacidad_id: UUID,
    motivo: str = Body(..., embed=True, min_length=10),
    db: AsyncSession = Depends(get_db)
):
    """
    Rechaza una incapacidad.
    
    Transición: EN_AUDITORIA u OBSERVADA → RECHAZADA
    
    Validaciones:
    - Motivo es obligatorio (mínimo 10 caracteres)
    - Registra fecha de rechazo y motivo
    """
    return await incapacidad_service.rechazar_incapacidad(db, incapacidad_id, motivo)


@router.post(
    "/{incapacidad_id}/enviar-pago",
    response_model=IncapacidadInDB,
    summary="Enviar a pago",
    description="Envía una incapacidad aprobada a pago"
)
async def enviar_a_pago(
    incapacidad_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Envía una incapacidad aprobada a pago.
    
    Transición: APROBADA → EN_PAGO
    
    Validaciones:
    - Debe estar en estado APROBADA
    - Debe tener valor_total calculado
    """
    return await incapacidad_service.enviar_a_pago(db, incapacidad_id)


@router.post(
    "/{incapacidad_id}/marcar-pagada",
    response_model=IncapacidadInDB,
    summary="Marcar como pagada",
    description="Marca una incapacidad como pagada"
)
async def marcar_como_pagada(
    incapacidad_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Marca una incapacidad como pagada.
    
    Transición: EN_PAGO → PAGADA
    
    Validaciones:
    - Debe estar en estado EN_PAGO
    - Estado final del workflow
    """
    return await incapacidad_service.marcar_como_pagada(db, incapacidad_id)


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

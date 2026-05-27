"""
API endpoints para gestión de Órdenes de Pago.
"""
from __future__ import annotations

from typing import List, Optional
from uuid import UUID
from datetime import datetime
import csv
from io import StringIO

from fastapi import APIRouter, Depends, Query, status, Body
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from apps.backend.app.db.session import get_db
from apps.backend.app.core.security import get_current_user, PermissionChecker, Permissions
from apps.backend.app.models.usuario import Usuario
from apps.backend.app.schemas.orden_pago import (
    OrdenPagoResponse,
    OrdenPagoListItem,
    OrdenPagoAnular,
    OrdenPagoAprobar,
    OrdenPagoUpdate
)
from apps.backend.app.schemas.historial_estado import HistorialEstadoResponse
from apps.backend.app.services.orden_pago_service import orden_pago_service
from apps.backend.app.services.historial_estado_service import historial_estado_service
from apps.backend.app.utils.enums import EstadoOrdenPago, RolUsuario

router = APIRouter()


@router.post(
    "/",
    response_model=OrdenPagoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generar orden de pago desde incapacidad",
    description="Crea una orden de pago automáticamente desde una incapacidad APROBADA"
)
async def create_orden_pago(
    incapacidad_id: UUID = Body(..., embed=True),
    observaciones: Optional[str] = Body(None, embed=True),
    db: AsyncSession = Depends(get_db),
    current_user: 'Usuario' = Depends(get_current_user)
):
    """
    Genera una orden de pago desde una incapacidad aprobada.
    
    Validaciones:
    - La incapacidad debe existir y estar en estado APROBADA
    - No debe existir otra orden activa para la misma incapacidad
    - El beneficiario debe tener información bancaria completa
    - Auto-genera número de orden secuencial (OP-YYYY-NNNNN)
    
    Estado inicial: GENERADA
    """
    return await orden_pago_service.create_orden_from_incapacidad(
        db=db,
        incapacidad_id=incapacidad_id,
        usuario_id=current_user.id,
        observaciones=observaciones
    )


@router.get(
    "/",
    response_model=List[OrdenPagoListItem],
    summary="Listar órdenes de pago",
    description="Lista órdenes de pago con filtros opcionales"
)
async def list_ordenes_pago(
    estado: Optional[EstadoOrdenPago] = Query(None, description="Filtrar por estado"),
    empresa_id: Optional[UUID] = Query(None, description="Filtrar por empresa"),
    skip: int = Query(0, ge=0, description="Número de registros a saltar"),
    limit: int = Query(100, ge=1, le=1000, description="Número máximo de registros"),
    db: AsyncSession = Depends(get_db),
    current_user: 'Usuario' = Depends(get_current_user)
):
    """
    Lista órdenes de pago con filtros opcionales.
    
    Filtros disponibles:
    - estado: Filtrar por estado de la orden
    - empresa_id: Filtrar por empresa (a través de la incapacidad)
    """
    ordenes = await orden_pago_service.list_ordenes_pago(
        db=db,
        estado=estado,
        empresa_id=empresa_id,
        skip=skip,
        limit=limit
    )
    
    return ordenes


@router.get(
    "/{orden_pago_id}",
    response_model=OrdenPagoResponse,
    summary="Obtener orden de pago",
    description="Obtiene el detalle completo de una orden de pago"
)
async def get_orden_pago(
    orden_pago_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: 'Usuario' = Depends(get_current_user)
):
    """
    Obtiene una orden de pago por ID.
    """
    return await orden_pago_service.get_orden_pago(db, orden_pago_id)


@router.put(
    "/{orden_pago_id}",
    response_model=OrdenPagoResponse,
    summary="Actualizar orden de pago",
    description="Actualiza una orden de pago (solo en estado GENERADA)"
)
async def update_orden_pago(
    orden_pago_id: UUID,
    update_data: OrdenPagoUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: 'Usuario' = Depends(get_current_user)
):
    """
    Actualiza una orden de pago.
    
    Restricciones:
    - Solo se pueden editar órdenes en estado GENERADA
    - Los cambios de estado deben hacerse mediante los endpoints específicos
    """
    return await orden_pago_service.update_orden_pago(
        db=db,
        orden_pago_id=orden_pago_id,
        update_data=update_data,
        usuario_id=current_user.id
    )


@router.post(
    "/{orden_pago_id}/aprobar",
    response_model=OrdenPagoResponse,
    summary="Aprobar orden de pago",
    description="Aprueba una orden de pago (solo ADMIN)"
    # dependencies=[Depends(PermissionChecker([Permissions.ORDEN_PAGO_APPROVE]))]
)
async def aprobar_orden(
    orden_pago_id: UUID,
    data: OrdenPagoAprobar,
    db: AsyncSession = Depends(get_db),
    current_user: 'Usuario' = Depends(get_current_user)
):
    """
    Aprueba una orden de pago.
    
    Permisos: Solo ADMIN
    
    Transición de estado: GENERADA → APROBADA
    
    Una vez aprobada, la orden queda lista para ser pagada.
    """
    return await orden_pago_service.aprobar_orden(
        db=db,
        orden_pago_id=orden_pago_id,
        usuario_id=current_user.id,
        usuario_rol=current_user.rol,
        observaciones=data.observaciones
    )


@router.post(
    "/{orden_pago_id}/registrar-pago",
    response_model=OrdenPagoResponse,
    summary="Registrar pago de orden",
    description="Registra el pago efectivo de una orden APROBADA"
)
async def registrar_pago(
    orden_pago_id: UUID,
    referencia_pago: str = Body(..., min_length=1, max_length=100, embed=True),
    comprobante_ruta: Optional[str] = Body(None, embed=True),
    observaciones: Optional[str] = Body(None, embed=True),
    db: AsyncSession = Depends(get_db),
    current_user: 'Usuario' = Depends(get_current_user)
):
    """
    Registra el pago de una orden aprobada.
    
    Transición de estado: APROBADA → PAGADA
    
    Campos obligatorios:
    - referencia_pago: Número de referencia bancaria
    
    También actualiza automáticamente la incapacidad asociada a estado PAGADA.
    """
    return await orden_pago_service.registrar_pago(
        db=db,
        orden_pago_id=orden_pago_id,
        usuario_id=current_user.id,
        referencia_pago=referencia_pago,
        comprobante_ruta=comprobante_ruta,
        observaciones=observaciones
    )


@router.post(
    "/{orden_pago_id}/anular",
    response_model=OrdenPagoResponse,
    summary="Anular orden de pago",
    description="Anula una orden de pago"
)
async def anular_orden(
    orden_pago_id: UUID,
    data: OrdenPagoAnular,
    db: AsyncSession = Depends(get_db),
    current_user: 'Usuario' = Depends(get_current_user)
):
    """
    Anula una orden de pago.
    
    Transición de estado: GENERADA/APROBADA → ANULADA
    
    No se pueden anular órdenes ya PAGADAS.
    El motivo de anulación es obligatorio (mínimo 10 caracteres).
    """
    return await orden_pago_service.anular_orden(
        db=db,
        orden_pago_id=orden_pago_id,
        usuario_id=current_user.id,
        motivo_anulacion=data.motivo_anulacion
    )


@router.get(
    "/{orden_pago_id}/historial",
    response_model=List[HistorialEstadoResponse],
    summary="Obtener historial de estados",
    description="Obtiene el historial completo de cambios de estado de una orden"
)
async def get_historial_orden(
    orden_pago_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: 'Usuario' = Depends(get_current_user)
):
    """
    Obtiene el historial de estados de una orden de pago.
    
    Incluye:
    - Estado anterior y nuevo
    - Fecha y hora del cambio
    - Usuario que realizó el cambio
    - Observaciones
    """
    # Verificar que la orden existe
    await orden_pago_service.get_orden_pago(db, orden_pago_id)
    
    # Obtener historial
    historial = await historial_estado_service.get_historial_by_entity(
        db=db,
        entity_type="OrdenPago",
        entity_id=orden_pago_id
    )
    
    return historial


@router.get(
    "/export/csv",
    summary="Exportar órdenes a CSV",
    description="Exporta órdenes de pago aprobadas a formato CSV para carga bancaria",
    response_class=StreamingResponse
)
async def export_ordenes_csv(
    estado: EstadoOrdenPago = Query(EstadoOrdenPago.APROBADA, description="Estado a exportar"),
    db: AsyncSession = Depends(get_db),
    current_user: 'Usuario' = Depends(get_current_user)
):
    """
    Exporta órdenes de pago a CSV con formato bancario.
    
    Columnas del CSV:
    - Número Orden
    - Beneficiario
    - Documento
    - Banco
    - Tipo Cuenta
    - Número Cuenta
    - Valor
    - Referencia
    """
    # Obtener órdenes aprobadas
    ordenes = await orden_pago_service.list_ordenes_pago(
        db=db,
        estado=estado,
        skip=0,
        limit=10000  # Límite alto para exportación
    )
    
    # Crear CSV en memoria
    output = StringIO()
    writer = csv.writer(output)
    
    # Encabezados
    writer.writerow([
        "Número Orden",
        "Beneficiario",
        "Documento",
        "Banco",
        "Tipo Cuenta",
        "Número Cuenta",
        "Valor",
        "Referencia"
    ])
    
    # Datos
    for orden in ordenes:
        writer.writerow([
            orden.numero_orden,
            orden.beneficiario_nombre,
            orden.beneficiario_documento,
            orden.banco,
            orden.tipo_cuenta,
            orden.cuenta_bancaria,
            float(orden.valor_pagar),
            orden.referencia_pago or ""
        ])
    
    # Preparar respuesta
    output.seek(0)
    
    filename = f"ordenes_pago_{estado}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )

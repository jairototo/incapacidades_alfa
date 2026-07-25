"""
Service para lógica de negocio de OrdenPago con workflow de estados.
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    NotFoundException,
    BadRequestException,
    InvalidStateException,
    ForbiddenException
)
from app.db.repositories.orden_pago_repository import OrdenPagoRepository
from app.db.repositories.incapacidad_repository import IncapacidadRepository
from app.services.historial_estado_service import historial_estado_service
from app.models.orden_pago import OrdenPago
from app.schemas.orden_pago import OrdenPagoCreate, OrdenPagoUpdate
from app.utils.enums import (
    EstadoOrdenPago,
    EstadoIncapacidad,
    RolUsuario,
    BeneficiarioTipo,
    MetodoPago
)


class OrdenPagoService:
    """Service para operaciones de negocio de OrdenPago."""

    def __init__(self):
        """Inicializa el service con los repositories necesarios."""
        self.repository = OrdenPagoRepository()
        self.incapacidad_repository = IncapacidadRepository()

    async def generate_numero_orden(
        self,
        db: AsyncSession
    ) -> str:
        """
        Genera un número de orden secuencial único.
        
        Formato: OP-YYYY-NNNNN (ej: OP-2026-00001)
        
        Args:
            db: Sesión de base de datos
            
        Returns:
            Número de orden generado
        """
        current_year = datetime.utcnow().year
        
        # Obtener último número del año actual
        last_numero = await self.repository.get_last_numero_orden(db, current_year)
        
        if last_numero:
            # Extraer el secuencial del formato OP-2026-00001
            parts = last_numero.split("-")
            if len(parts) == 3:
                try:
                    last_seq = int(parts[2])
                    next_seq = last_seq + 1
                except (ValueError, IndexError):
                    next_seq = 1
            else:
                next_seq = 1
        else:
            # Primera orden del año
            next_seq = 1
        
        # Formatear con ceros a la izquierda (5 dígitos)
        numero_orden = f"OP-{current_year}-{next_seq:05d}"
        
        return numero_orden

    async def create_orden_from_incapacidad(
        self,
        db: AsyncSession,
        incapacidad_id: UUID,
        usuario_id: UUID,
        observaciones: Optional[str] = None
    ) -> OrdenPago:
        """
        Crea una orden de pago desde una incapacidad en EN_PAGO o EN_PAGO_PARCIAL.

        Args:
            db: Sesión de base de datos
            incapacidad_id: ID de la incapacidad
            usuario_id: ID del usuario que crea la orden
            observaciones: Observaciones opcionales

        Returns:
            OrdenPago creada

        Raises:
            NotFoundException: Si la incapacidad no existe
            BadRequestException: Si la incapacidad no está en EN_PAGO ni EN_PAGO_PARCIAL
            ConflictException: Si ya existe una orden activa para esta incapacidad
        """
        # 1. Verificar que la incapacidad existe
        incapacidad = await self.incapacidad_repository.get_by_id(db, incapacidad_id)
        if not incapacidad:
            raise NotFoundException(f"Incapacidad {incapacidad_id} no encontrada")

        # 2. Validar que esté en estado EN_PAGO o EN_PAGO_PARCIAL (liquidación completada, lista para pago)
        if incapacidad.estado not in (EstadoIncapacidad.EN_PAGO, EstadoIncapacidad.EN_PAGO_PARCIAL):
            raise BadRequestException(
                f"La incapacidad debe estar en EN_PAGO o EN_PAGO_PARCIAL. Estado actual: {incapacidad.estado}"
            )
        
        # 3. Verificar que no exista otra orden activa (no ANULADA ni RECHAZADA)
        exists = await self.repository.exists_for_incapacidad(
            db,
            incapacidad_id,
            exclude_estados=[EstadoOrdenPago.ANULADA, EstadoOrdenPago.RECHAZADA]
        )
        
        if exists:
            raise BadRequestException(
                "Ya existe una orden de pago activa para esta incapacidad"
            )
        
        # 4. Generar número de orden único
        numero_orden = await self.generate_numero_orden(db)
        
        # 5. Determinar beneficiario según tipo de incapacidad
        if incapacidad.empleado_id:
            # Incapacidad ARL - Beneficiario es el empleado
            beneficiario_tipo = BeneficiarioTipo.EMPLEADO
            beneficiario_id = incapacidad.empleado_id
            beneficiario_nombre = incapacidad.empleado.nombre_completo
            beneficiario_documento = incapacidad.empleado.numero_documento
            cuenta_bancaria = incapacidad.empleado.cuenta_bancaria
            banco = incapacidad.empleado.banco
            tipo_cuenta = incapacidad.empleado.tipo_cuenta
        elif incapacidad.afiliado_id:
            # Incapacidad SALUD - Beneficiario es el afiliado
            beneficiario_tipo = BeneficiarioTipo.AFILIADO
            beneficiario_id = incapacidad.afiliado_id
            beneficiario_nombre = incapacidad.afiliado.nombre_completo
            beneficiario_documento = incapacidad.afiliado.numero_documento
            cuenta_bancaria = incapacidad.afiliado.cuenta_bancaria
            banco = incapacidad.afiliado.banco
            tipo_cuenta = incapacidad.afiliado.tipo_cuenta
        else:
            raise BadRequestException(
                "La incapacidad no tiene empleado ni afiliado asociado"
            )
        
        # 6. Validar información bancaria
        if not cuenta_bancaria or not banco or not tipo_cuenta:
            raise BadRequestException(
                f"El beneficiario no tiene información bancaria completa"
            )
        
        # 7. Crear la orden de pago
        orden_pago_data = {
            "numero_orden": numero_orden,
            "incapacidad_id": incapacidad_id,
            "beneficiario_tipo": beneficiario_tipo,
            "beneficiario_id": beneficiario_id,
            "beneficiario_nombre": beneficiario_nombre,
            "beneficiario_documento": beneficiario_documento,
            "cuenta_bancaria": cuenta_bancaria,
            "banco": banco,
            "tipo_cuenta": tipo_cuenta,
            "valor_pagar": incapacidad.valor_total or Decimal("0"),
            "estado_pago": EstadoOrdenPago.GENERADA,
            "fecha_generacion": datetime.utcnow(),
            "metodo_pago": MetodoPago.TRANSFERENCIA,
            "creado_por_id": usuario_id
        }
        
        orden_pago = await self.repository.create(db, orden_pago_data)
        
        # 8. Registrar en historial de estados
        await historial_estado_service.create_historial(
            db=db,
            entity_type="OrdenPago",
            entity_id=orden_pago.id,
            estado_anterior=None,
            estado_nuevo=EstadoOrdenPago.GENERADA,
            observaciones=observaciones or f"Orden generada desde incapacidad {incapacidad.numero}",
            usuario_id=usuario_id
        )
        
        return orden_pago

    async def aprobar_orden(
        self,
        db: AsyncSession,
        orden_pago_id: UUID,
        usuario_id: UUID,
        usuario_rol: RolUsuario,
        observaciones: Optional[str] = None
    ) -> OrdenPago:
        """
        Aprueba una orden de pago (solo ADMIN).
        
        Args:
            db: Sesión de base de datos
            orden_pago_id: ID de la orden
            usuario_id: ID del usuario que aprueba
            usuario_rol: Rol del usuario
            observaciones: Observaciones de la aprobación
            
        Returns:
            OrdenPago actualizada
            
        Raises:
            NotFoundException: Si la orden no existe
            ForbiddenException: Si el usuario no es ADMIN
            InvalidStateException: Si la orden no está en estado GENERADA
        """
        # 1. Validar permisos
        if usuario_rol != RolUsuario.ADMIN:
            raise ForbiddenException("Solo los ADMIN pueden aprobar órdenes de pago")
        
        # 2. Obtener la orden
        orden_pago = await self.repository.get_by_id(db, orden_pago_id)
        if not orden_pago:
            raise NotFoundException(f"Orden de pago {orden_pago_id} no encontrada")
        
        # 3. Validar estado actual
        if orden_pago.estado_pago != EstadoOrdenPago.GENERADA:
            raise InvalidStateException(
                f"Solo se pueden aprobar órdenes en estado GENERADA. Estado actual: {orden_pago.estado_pago}"
            )
        
        # 4. Actualizar estado
        estado_anterior = orden_pago.estado_pago
        update_data = {
            "estado_pago": EstadoOrdenPago.APROBADA,
            "aprobado_por_id": usuario_id
        }
        
        orden_pago = await self.repository.update(db, orden_pago_id, update_data)
        
        # 5. Registrar en historial
        await historial_estado_service.create_historial(
            db=db,
            entity_type="OrdenPago",
            entity_id=orden_pago.id,
            estado_anterior=estado_anterior,
            estado_nuevo=EstadoOrdenPago.APROBADA,
            observaciones=observaciones or "Orden de pago aprobada",
            usuario_id=usuario_id
        )
        
        return orden_pago

    async def registrar_pago(
        self,
        db: AsyncSession,
        orden_pago_id: UUID,
        usuario_id: UUID,
        referencia_pago: str,
        comprobante_ruta: Optional[str] = None,
        observaciones: Optional[str] = None
    ) -> OrdenPago:
        """
        Registra el pago de una orden APROBADA.
        
        Args:
            db: Sesión de base de datos
            orden_pago_id: ID de la orden
            usuario_id: ID del usuario que registra el pago
            referencia_pago: Referencia del pago bancario
            comprobante_ruta: Ruta del comprobante de pago
            observaciones: Observaciones del pago
            
        Returns:
            OrdenPago actualizada
            
        Raises:
            NotFoundException: Si la orden no existe
            InvalidStateException: Si la orden no está APROBADA
        """
        # 1. Obtener la orden
        orden_pago = await self.repository.get_by_id(db, orden_pago_id)
        if not orden_pago:
            raise NotFoundException(f"Orden de pago {orden_pago_id} no encontrada")
        
        # 2. Validar estado actual
        if orden_pago.estado_pago != EstadoOrdenPago.APROBADA:
            raise InvalidStateException(
                f"Solo se pueden pagar órdenes APROBADAS. Estado actual: {orden_pago.estado_pago}"
            )
        
        # 3. Validar referencia de pago
        if not referencia_pago or len(referencia_pago.strip()) == 0:
            raise BadRequestException("La referencia de pago es obligatoria")
        
        # 4. Actualizar estado
        estado_anterior = orden_pago.estado_pago
        update_data = {
            "estado_pago": EstadoOrdenPago.PAGADA,
            "fecha_pago": datetime.utcnow(),
            "referencia_pago": referencia_pago,
            "comprobante_ruta": comprobante_ruta
        }
        
        orden_pago = await self.repository.update(db, orden_pago_id, update_data)
        
        # 5. Registrar en historial
        await historial_estado_service.create_historial(
            db=db,
            entity_type="OrdenPago",
            entity_id=orden_pago.id,
            estado_anterior=estado_anterior,
            estado_nuevo=EstadoOrdenPago.PAGADA,
            observaciones=observaciones or f"Pago registrado con referencia {referencia_pago}",
            usuario_id=usuario_id
        )
        
        # 6. Actualizar estado de la incapacidad a PAGADA / PAGADA_PARCIAL
        incapacidad = await self.incapacidad_repository.get_by_id(db, orden_pago.incapacidad_id)
        if incapacidad and incapacidad.estado in [EstadoIncapacidad.EN_PAGO, EstadoIncapacidad.EN_PAGO_PARCIAL]:
            from app.services.incapacidad_service import incapacidad_service
            nuevo_estado = (
                EstadoIncapacidad.PAGADA_PARCIAL
                if incapacidad.estado == EstadoIncapacidad.EN_PAGO_PARCIAL
                else EstadoIncapacidad.PAGADA
            )
            await incapacidad_service._cambiar_estado(
                db=db,
                incapacidad=incapacidad,
                nuevo_estado=nuevo_estado,
                observacion=f"Pago registrado en orden {orden_pago.numero_orden}",
                usuario_id=usuario_id,
            )
        
        return orden_pago

    async def anular_orden(
        self,
        db: AsyncSession,
        orden_pago_id: UUID,
        usuario_id: UUID,
        motivo_anulacion: str
    ) -> OrdenPago:
        """
        Anula una orden de pago.
        
        Args:
            db: Sesión de base de datos
            orden_pago_id: ID de la orden
            usuario_id: ID del usuario que anula
            motivo_anulacion: Motivo de la anulación (obligatorio)
            
        Returns:
            OrdenPago actualizada
            
        Raises:
            NotFoundException: Si la orden no existe
            InvalidStateException: Si la orden ya está PAGADA o ANULADA
            BadRequestException: Si no se proporciona motivo
        """
        # 1. Obtener la orden
        orden_pago = await self.repository.get_by_id(db, orden_pago_id)
        if not orden_pago:
            raise NotFoundException(f"Orden de pago {orden_pago_id} no encontrada")
        
        # 2. Validar estado actual
        if orden_pago.estado_pago in [EstadoOrdenPago.PAGADA, EstadoOrdenPago.ANULADA]:
            raise InvalidStateException(
                f"No se puede anular una orden en estado {orden_pago.estado_pago}"
            )
        
        # 3. Validar motivo
        if not motivo_anulacion or len(motivo_anulacion.strip()) < 10:
            raise BadRequestException(
                "El motivo de anulación es obligatorio (mínimo 10 caracteres)"
            )
        
        # 4. Actualizar estado
        estado_anterior = orden_pago.estado_pago
        update_data = {
            "estado_pago": EstadoOrdenPago.ANULADA,
            "fecha_anulacion": datetime.utcnow(),
            "motivo_anulacion": motivo_anulacion
        }
        
        orden_pago = await self.repository.update(db, orden_pago_id, update_data)
        
        # 5. Registrar en historial
        await historial_estado_service.create_historial(
            db=db,
            entity_type="OrdenPago",
            entity_id=orden_pago.id,
            estado_anterior=estado_anterior,
            estado_nuevo=EstadoOrdenPago.ANULADA,
            observaciones=motivo_anulacion,
            usuario_id=usuario_id
        )
        
        return orden_pago

    async def get_orden_pago(
        self,
        db: AsyncSession,
        orden_pago_id: UUID
    ) -> OrdenPago:
        """
        Obtiene una orden de pago por ID.
        
        Args:
            db: Sesión de base de datos
            orden_pago_id: ID de la orden
            
        Returns:
            OrdenPago
            
        Raises:
            NotFoundException: Si no existe
        """
        orden_pago = await self.repository.get_by_id(db, orden_pago_id)
        if not orden_pago:
            raise NotFoundException(f"Orden de pago {orden_pago_id} no encontrada")
        
        return orden_pago

    async def list_ordenes_pago(
        self,
        db: AsyncSession,
        estado: Optional[EstadoOrdenPago] = None,
        empresa_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[OrdenPago]:
        """
        Lista órdenes de pago con filtros opcionales.
        
        Args:
            db: Sesión de base de datos
            estado: Filtrar por estado
            empresa_id: Filtrar por empresa
            skip: Registros a saltar
            limit: Límite de registros
            
        Returns:
            Lista de órdenes de pago
        """
        if estado:
            return await self.repository.list_by_estado(db, estado, skip, limit)
        elif empresa_id:
            return await self.repository.list_by_empresa(db, empresa_id, skip, limit)
        else:
            return await self.repository.list_all(db, skip, limit)

    async def update_orden_pago(
        self,
        db: AsyncSession,
        orden_pago_id: UUID,
        update_data: OrdenPagoUpdate,
        usuario_id: UUID
    ) -> OrdenPago:
        """
        Actualiza una orden de pago (solo en estado GENERADA).
        
        Args:
            db: Sesión de base de datos
            orden_pago_id: ID de la orden
            update_data: Datos a actualizar
            usuario_id: ID del usuario
            
        Returns:
            OrdenPago actualizada
            
        Raises:
            NotFoundException: Si no existe
            InvalidStateException: Si no está en estado GENERADA
        """
        orden_pago = await self.repository.get_by_id(db, orden_pago_id)
        if not orden_pago:
            raise NotFoundException(f"Orden de pago {orden_pago_id} no encontrada")
        
        if orden_pago.estado_pago != EstadoOrdenPago.GENERADA:
            raise InvalidStateException(
                f"Solo se pueden editar órdenes en estado GENERADA"
            )
        
        update_dict = update_data.model_dump(exclude_unset=True)
        return await self.repository.update(db, orden_pago_id, update_dict)


# Singleton
orden_pago_service = OrdenPagoService()

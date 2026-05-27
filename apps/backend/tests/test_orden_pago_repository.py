"""
Tests for OrdenPagoRepository.
"""
import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from apps.backend.app.db.repositories.orden_pago_repository import OrdenPagoRepository
from apps.backend.app.models.orden_pago import OrdenPago
from apps.backend.app.models.incapacidad import Incapacidad
from apps.backend.app.models.empleado import Empleado
from apps.backend.app.models.empresa import Empresa
from apps.backend.app.utils.enums import (
    EstadoOrdenPago,
    EstadoIncapacidad,
    TipoIncapacidad,
    BeneficiarioTipo,
    MetodoPago,
    TipoCuenta,
    EstadoEmpresa,
    EstadoEmpleado,
    TipoDocumento
)


@pytest.fixture
async def test_empresa(db_session: AsyncSession):
    """Crea una empresa de prueba."""
    empresa = Empresa(
        nit="900123456",
        razon_social="Empresa Test SA",
        estado=EstadoEmpresa.ACTIVA
    )
    db_session.add(empresa)
    await db_session.commit()
    await db_session.refresh(empresa)
    return empresa


@pytest.fixture
async def test_empleado(db_session: AsyncSession, test_empresa):
    """Crea un empleado de prueba."""
    empleado = Empleado(
        empresa_id=test_empresa.id,
        numero_documento="1234567890",
        tipo_documento=TipoDocumento.CC,
        nombres="Juan",
        apellidos="Pérez",
        fecha_ingreso=datetime.utcnow().date(),
        cuenta_bancaria="1234567890",
        banco="Bancolombia",
        tipo_cuenta=TipoCuenta.AHORROS,
        estado=EstadoEmpleado.ACTIVO
    )
    db_session.add(empleado)
    await db_session.commit()
    await db_session.refresh(empleado)
    return empleado


@pytest.fixture
async def test_incapacidad(db_session: AsyncSession, test_empresa, test_empleado):
    """Crea una incapacidad de prueba."""
    incapacidad = Incapacidad(
        numero=f"INC-TEST-{uuid4().hex[:8]}",
        tipo=TipoIncapacidad.ARL,
        empresa_id=test_empresa.id,
        empleado_id=test_empleado.id,
        fecha_inicio=datetime.utcnow().date(),
        fecha_fin=(datetime.utcnow() + timedelta(days=5)).date(),
        dias_totales=5,
        valor_incapacidad=Decimal("1500000.00"),
        estado=EstadoIncapacidad.APROBADA,
        diagnostico="Fractura de brazo"
    )
    db_session.add(incapacidad)
    await db_session.commit()
    await db_session.refresh(incapacidad)
    return incapacidad


@pytest.fixture
async def test_orden_pago(db_session: AsyncSession, test_incapacidad, test_empleado):
    """Crea una orden de pago de prueba."""
    orden = OrdenPago(
        numero_orden="OP-2026-00001",
        incapacidad_id=test_incapacidad.id,
        beneficiario_tipo=BeneficiarioTipo.EMPLEADO,
        beneficiario_id=test_empleado.id,
        beneficiario_nombre=test_empleado.nombre_completo,
        beneficiario_documento=test_empleado.numero_documento,
        cuenta_bancaria=test_empleado.cuenta_bancaria,
        banco=test_empleado.banco,
        tipo_cuenta=test_empleado.tipo_cuenta,
        valor_pagar=Decimal("1500000.00"),
        estado_pago=EstadoOrdenPago.GENERADA,
        metodo_pago=MetodoPago.TRANSFERENCIA
    )
    db_session.add(orden)
    await db_session.commit()
    await db_session.refresh(orden)
    return orden


@pytest.mark.asyncio
async def test_get_by_numero_orden(db_session: AsyncSession, test_orden_pago):
    """Test obtener orden por número."""
    repository = OrdenPagoRepository()
    
    orden = await repository.get_by_numero_orden(db_session, "OP-2026-00001")
    
    assert orden is not None
    assert orden.id == test_orden_pago.id
    assert orden.numero_orden == "OP-2026-00001"


@pytest.mark.asyncio
async def test_get_by_numero_orden_not_found(db_session: AsyncSession):
    """Test obtener orden por número que no existe."""
    repository = OrdenPagoRepository()
    
    orden = await repository.get_by_numero_orden(db_session, "OP-2026-99999")
    
    assert orden is None


@pytest.mark.asyncio
async def test_get_by_incapacidad_id(db_session: AsyncSession, test_orden_pago, test_incapacidad):
    """Test obtener órdenes por incapacidad."""
    repository = OrdenPagoRepository()
    
    # Crear segunda orden para la misma incapacidad
    orden2 = OrdenPago(
        numero_orden="OP-2026-00002",
        incapacidad_id=test_incapacidad.id,
        beneficiario_tipo=BeneficiarioTipo.EMPLEADO,
        beneficiario_id=test_orden_pago.beneficiario_id,
        beneficiario_nombre="Test User",
        beneficiario_documento="123456",
        cuenta_bancaria="123456",
        banco="Banco Test",
        tipo_cuenta=TipoCuenta.AHORROS,
        valor_pagar=Decimal("500000.00"),
        estado_pago=EstadoOrdenPago.GENERADA
    )
    db_session.add(orden2)
    await db_session.commit()
    
    ordenes = await repository.get_by_incapacidad_id(db_session, test_incapacidad.id)
    
    assert len(ordenes) == 2
    assert ordenes[0].incapacidad_id == test_incapacidad.id
    assert ordenes[1].incapacidad_id == test_incapacidad.id


@pytest.mark.asyncio
async def test_list_by_estado(db_session: AsyncSession, test_orden_pago):
    """Test listar órdenes por estado."""
    repository = OrdenPagoRepository()
    
    # Crear orden con estado diferente
    orden2 = OrdenPago(
        numero_orden="OP-2026-00002",
        incapacidad_id=test_orden_pago.incapacidad_id,
        beneficiario_tipo=BeneficiarioTipo.EMPLEADO,
        beneficiario_id=test_orden_pago.beneficiario_id,
        beneficiario_nombre="Test User",
        beneficiario_documento="123456",
        cuenta_bancaria="123456",
        banco="Banco Test",
        tipo_cuenta=TipoCuenta.AHORROS,
        valor_pagar=Decimal("500000.00"),
        estado_pago=EstadoOrdenPago.APROBADA
    )
    db_session.add(orden2)
    await db_session.commit()
    
    ordenes_generadas = await repository.list_by_estado(
        db_session, EstadoOrdenPago.GENERADA
    )
    ordenes_aprobadas = await repository.list_by_estado(
        db_session, EstadoOrdenPago.APROBADA
    )
    
    assert len(ordenes_generadas) == 1
    assert ordenes_generadas[0].estado_pago == EstadoOrdenPago.GENERADA
    
    assert len(ordenes_aprobadas) == 1
    assert ordenes_aprobadas[0].estado_pago == EstadoOrdenPago.APROBADA


@pytest.mark.asyncio
async def test_list_by_empresa(db_session: AsyncSession, test_orden_pago, test_empresa):
    """Test listar órdenes por empresa."""
    repository = OrdenPagoRepository()
    
    ordenes = await repository.list_by_empresa(db_session, test_empresa.id)
    
    assert len(ordenes) >= 1
    # Verificar que todas las órdenes pertenecen a la empresa
    for orden in ordenes:
        assert orden.incapacidad.empresa_id == test_empresa.id


@pytest.mark.asyncio
async def test_list_pending_payment(db_session: AsyncSession, test_orden_pago):
    """Test listar órdenes pendientes de pago."""
    repository = OrdenPagoRepository()
    
    # Cambiar estado a APROBADA
    test_orden_pago.estado_pago = EstadoOrdenPago.APROBADA
    await db_session.commit()
    
    ordenes = await repository.list_pending_payment(db_session)
    
    assert len(ordenes) >= 1
    assert all(o.estado_pago == EstadoOrdenPago.APROBADA for o in ordenes)


@pytest.mark.asyncio
async def test_get_with_incapacidad(db_session: AsyncSession, test_orden_pago):
    """Test obtener orden con incapacidad cargada."""
    repository = OrdenPagoRepository()
    
    orden = await repository.get_with_incapacidad(db_session, test_orden_pago.id)
    
    assert orden is not None
    assert orden.incapacidad is not None
    assert orden.incapacidad.id == test_orden_pago.incapacidad_id


@pytest.mark.asyncio
async def test_get_last_numero_orden(db_session: AsyncSession, test_orden_pago):
    """Test obtener último número de orden."""
    repository = OrdenPagoRepository()
    
    ultimo = await repository.get_last_numero_orden(db_session, 2026)
    
    assert ultimo is not None
    assert ultimo.startswith("OP-2026-")


@pytest.mark.asyncio
async def test_exists_for_incapacidad(db_session: AsyncSession, test_orden_pago, test_incapacidad):
    """Test verificar existencia de orden para incapacidad."""
    repository = OrdenPagoRepository()
    
    # Debe existir
    exists = await repository.exists_for_incapacidad(db_session, test_incapacidad.id)
    assert exists is True
    
    # No debe existir para incapacidad inexistente
    exists = await repository.exists_for_incapacidad(db_session, uuid4())
    assert exists is False


@pytest.mark.asyncio
async def test_exists_for_incapacidad_exclude_estados(db_session: AsyncSession, test_orden_pago, test_incapacidad):
    """Test verificar existencia excluyendo estados."""
    repository = OrdenPagoRepository()
    
    # Cambiar a ANULADA
    test_orden_pago.estado_pago = EstadoOrdenPago.ANULADA
    await db_session.commit()
    
    # No debe existir si excluimos ANULADA
    exists = await repository.exists_for_incapacidad(
        db_session,
        test_incapacidad.id,
        exclude_estados=[EstadoOrdenPago.ANULADA]
    )
    assert exists is False


@pytest.mark.asyncio
async def test_list_by_fecha_range(db_session: AsyncSession, test_orden_pago):
    """Test listar órdenes por rango de fechas."""
    repository = OrdenPagoRepository()
    
    fecha_inicio = datetime.utcnow() - timedelta(days=1)
    fecha_fin = datetime.utcnow() + timedelta(days=1)
    
    ordenes = await repository.list_by_fecha_range(
        db_session, fecha_inicio, fecha_fin
    )
    
    assert len(ordenes) >= 1
    for orden in ordenes:
        assert fecha_inicio <= orden.fecha_generacion <= fecha_fin

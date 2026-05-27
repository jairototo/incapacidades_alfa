"""
Tests for OrdenPagoService.
"""
import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import AsyncMock, patch

from sqlalchemy.ext.asyncio import AsyncSession

from apps.backend.app.services.orden_pago_service import orden_pago_service
from apps.backend.app.models.orden_pago import OrdenPago
from apps.backend.app.models.incapacidad import Incapacidad
from apps.backend.app.models.empleado import Empleado
from apps.backend.app.models.empresa import Empresa
from apps.backend.app.models.afiliado import Afiliado
from apps.backend.app.core.exceptions import (
    NotFoundException,
    BadRequestException,
    InvalidStateException,
    ForbiddenException
)
from apps.backend.app.utils.enums import (
    EstadoOrdenPago,
    EstadoIncapacidad,
    TipoIncapacidad,
    BeneficiarioTipo,
    TipoCuenta,
    EstadoEmpresa,
    EstadoEmpleado,
    EstadoAfiliado,
    TipoDocumento,
    RolUsuario,
    TipoPoliza
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
async def test_afiliado(db_session: AsyncSession):
    """Crea un afiliado de prueba."""
    from datetime import datetime
    afiliado = Afiliado(
        numero_documento="9876543210",
        tipo_documento=TipoDocumento.CC,
        nombres="María",
        apellidos="García",
        numero_poliza="POL-001",
        tipo_poliza=TipoPoliza.INDIVIDUAL,
        fecha_inicio_poliza=datetime.utcnow().date(),
        cuenta_bancaria="9876543210",
        banco="Davivienda",
        tipo_cuenta=TipoCuenta.AHORROS,
        estado=EstadoAfiliado.ACTIVO
    )
    db_session.add(afiliado)
    await db_session.commit()
    await db_session.refresh(afiliado)
    return afiliado


@pytest.fixture
async def test_incapacidad_arl_aprobada(db_session: AsyncSession, test_empresa, test_empleado):
    """Crea una incapacidad ARL aprobada."""
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
async def test_incapacidad_salud_aprobada(db_session: AsyncSession, test_afiliado):
    """Crea una incapacidad SALUD aprobada."""
    incapacidad = Incapacidad(
        numero=f"INC-TEST-{uuid4().hex[:8]}",
        tipo=TipoIncapacidad.SALUD,
        afiliado_id=test_afiliado.id,
        fecha_inicio=datetime.utcnow().date(),
        fecha_fin=(datetime.utcnow() + timedelta(days=3)).date(),
        dias_totales=3,
        valor_incapacidad=Decimal("900000.00"),
        estado=EstadoIncapacidad.APROBADA,
        diagnostico="Gripe"
    )
    db_session.add(incapacidad)
    await db_session.commit()
    await db_session.refresh(incapacidad)
    return incapacidad


@pytest.mark.asyncio
async def test_generate_numero_orden_first(db_session: AsyncSession):
    """Test generar primer número de orden del año."""
    numero = await orden_pago_service.generate_numero_orden(db_session)
    
    current_year = datetime.utcnow().year
    assert numero == f"OP-{current_year}-00001"


@pytest.mark.asyncio
async def test_generate_numero_orden_sequential(db_session: AsyncSession, test_incapacidad_arl_aprobada, test_empleado):
    """Test generar números de orden secuenciales."""
    # Crear primera orden
    orden1 = OrdenPago(
        numero_orden="OP-2026-00001",
        incapacidad_id=test_incapacidad_arl_aprobada.id,
        beneficiario_tipo=BeneficiarioTipo.EMPLEADO,
        beneficiario_id=test_empleado.id,
        beneficiario_nombre=test_empleado.nombre_completo,
        beneficiario_documento=test_empleado.numero_documento,
        cuenta_bancaria=test_empleado.cuenta_bancaria,
        banco=test_empleado.banco,
        tipo_cuenta=test_empleado.tipo_cuenta,
        valor_pagar=Decimal("1000000.00"),
        estado_pago=EstadoOrdenPago.GENERADA
    )
    db_session.add(orden1)
    await db_session.commit()
    
    # Generar siguiente número
    numero = await orden_pago_service.generate_numero_orden(db_session)
    
    assert numero == "OP-2026-00002"


@pytest.mark.asyncio
async def test_create_orden_from_incapacidad_arl_success(
    db_session: AsyncSession,
    test_incapacidad_arl_aprobada,
    test_empleado
):
    """Test crear orden de pago desde incapacidad ARL exitosamente."""
    usuario_id = uuid4()
    
    # Mock del historial_estado_service
    with patch("app.services.orden_pago_service.historial_estado_service.create_historial", new_callable=AsyncMock):
        orden = await orden_pago_service.create_orden_from_incapacidad(
            db=db_session,
            incapacidad_id=test_incapacidad_arl_aprobada.id,
            usuario_id=usuario_id
        )
    
    assert orden is not None
    assert orden.numero_orden.startswith("OP-")
    assert orden.incapacidad_id == test_incapacidad_arl_aprobada.id
    assert orden.beneficiario_tipo == BeneficiarioTipo.EMPLEADO
    assert orden.beneficiario_id == test_empleado.id
    assert orden.beneficiario_nombre == test_empleado.nombre_completo
    assert orden.valor_pagar == test_incapacidad_arl_aprobada.valor_incapacidad
    assert orden.estado_pago == EstadoOrdenPago.GENERADA
    assert orden.cuenta_bancaria == test_empleado.cuenta_bancaria


@pytest.mark.asyncio
async def test_create_orden_from_incapacidad_salud_success(
    db_session: AsyncSession,
    test_incapacidad_salud_aprobada,
    test_afiliado
):
    """Test crear orden de pago desde incapacidad SALUD exitosamente."""
    usuario_id = uuid4()
    
    with patch("app.services.orden_pago_service.historial_estado_service.create_historial", new_callable=AsyncMock):
        orden = await orden_pago_service.create_orden_from_incapacidad(
            db=db_session,
            incapacidad_id=test_incapacidad_salud_aprobada.id,
            usuario_id=usuario_id
        )
    
    assert orden is not None
    assert orden.beneficiario_tipo == BeneficiarioTipo.AFILIADO
    assert orden.beneficiario_id == test_afiliado.id
    assert orden.beneficiario_nombre == test_afiliado.nombre_completo
    assert orden.valor_pagar == test_incapacidad_salud_aprobada.valor_incapacidad


@pytest.mark.asyncio
async def test_create_orden_incapacidad_not_found(db_session: AsyncSession):
    """Test crear orden con incapacidad inexistente."""
    usuario_id = uuid4()
    incapacidad_id_fake = uuid4()
    
    with pytest.raises(NotFoundException) as exc_info:
        await orden_pago_service.create_orden_from_incapacidad(
            db=db_session,
            incapacidad_id=incapacidad_id_fake,
            usuario_id=usuario_id
        )
    
    assert "no encontrada" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_create_orden_incapacidad_not_approved(
    db_session: AsyncSession,
    test_incapacidad_arl_aprobada
):
    """Test crear orden con incapacidad no aprobada."""
    # Cambiar estado a RADICADA
    test_incapacidad_arl_aprobada.estado = EstadoIncapacidad.RADICADA
    await db_session.commit()
    
    usuario_id = uuid4()
    
    with pytest.raises(BadRequestException) as exc_info:
        await orden_pago_service.create_orden_from_incapacidad(
            db=db_session,
            incapacidad_id=test_incapacidad_arl_aprobada.id,
            usuario_id=usuario_id
        )
    
    assert "aprobada" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_create_orden_duplicate_fails(
    db_session: AsyncSession,
    test_incapacidad_arl_aprobada,
    test_empleado
):
    """Test crear orden duplicada falla."""
    usuario_id = uuid4()
    
    # Crear primera orden
    with patch("app.services.orden_pago_service.historial_estado_service.create_historial", new_callable=AsyncMock):
        await orden_pago_service.create_orden_from_incapacidad(
            db=db_session,
            incapacidad_id=test_incapacidad_arl_aprobada.id,
            usuario_id=usuario_id
        )
    
    # Intentar crear segunda orden para la misma incapacidad
    with pytest.raises(BadRequestException) as exc_info:
        with patch("app.services.orden_pago_service.historial_estado_service.create_historial", new_callable=AsyncMock):
            await orden_pago_service.create_orden_from_incapacidad(
                db=db_session,
                incapacidad_id=test_incapacidad_arl_aprobada.id,
                usuario_id=usuario_id
            )
    
    assert "ya existe" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_aprobar_orden_success(
    db_session: AsyncSession,
    test_incapacidad_arl_aprobada
):
    """Test aprobar orden exitosamente."""
    usuario_id = uuid4()
    
    # Crear orden
    with patch("app.services.orden_pago_service.historial_estado_service.create_historial", new_callable=AsyncMock):
        orden = await orden_pago_service.create_orden_from_incapacidad(
            db=db_session,
            incapacidad_id=test_incapacidad_arl_aprobada.id,
            usuario_id=usuario_id
        )
    
    # Aprobar orden
    admin_id = uuid4()
    with patch("app.services.orden_pago_service.historial_estado_service.create_historial", new_callable=AsyncMock):
        orden_aprobada = await orden_pago_service.aprobar_orden(
            db=db_session,
            orden_pago_id=orden.id,
            usuario_id=admin_id,
            usuario_rol=RolUsuario.ADMIN
        )
    
    assert orden_aprobada.estado_pago == EstadoOrdenPago.APROBADA
    assert orden_aprobada.aprobado_por_id == admin_id


@pytest.mark.asyncio
async def test_aprobar_orden_unauthorized(
    db_session: AsyncSession,
    test_incapacidad_arl_aprobada
):
    """Test aprobar orden sin permisos falla."""
    usuario_id = uuid4()
    
    # Crear orden
    with patch("app.services.orden_pago_service.historial_estado_service.create_historial", new_callable=AsyncMock):
        orden = await orden_pago_service.create_orden_from_incapacidad(
            db=db_session,
            incapacidad_id=test_incapacidad_arl_aprobada.id,
            usuario_id=usuario_id
        )
    
    # Intentar aprobar con rol EMPLEADO
    with pytest.raises(ForbiddenException):
        await orden_pago_service.aprobar_orden(
            db=db_session,
            orden_pago_id=orden.id,
            usuario_id=uuid4(),
            usuario_rol=RolUsuario.EMPLEADO
        )


@pytest.mark.asyncio
async def test_aprobar_orden_invalid_state(
    db_session: AsyncSession,
    test_incapacidad_arl_aprobada,
    test_empleado
):
    """Test aprobar orden en estado inválido."""
    # Crear orden manualmente ya APROBADA
    orden = OrdenPago(
        numero_orden="OP-2026-00099",
        incapacidad_id=test_incapacidad_arl_aprobada.id,
        beneficiario_tipo=BeneficiarioTipo.EMPLEADO,
        beneficiario_id=test_empleado.id,
        beneficiario_nombre=test_empleado.nombre_completo,
        beneficiario_documento=test_empleado.numero_documento,
        cuenta_bancaria=test_empleado.cuenta_bancaria,
        banco=test_empleado.banco,
        tipo_cuenta=test_empleado.tipo_cuenta,
        valor_pagar=Decimal("1000000.00"),
        estado_pago=EstadoOrdenPago.APROBADA
    )
    db_session.add(orden)
    await db_session.commit()
    
    with pytest.raises(InvalidStateException):
        await orden_pago_service.aprobar_orden(
            db=db_session,
            orden_pago_id=orden.id,
            usuario_id=uuid4(),
            usuario_rol=RolUsuario.ADMIN
        )


@pytest.mark.asyncio
async def test_registrar_pago_success(
    db_session: AsyncSession,
    test_incapacidad_arl_aprobada,
    test_empleado
):
    """Test registrar pago exitosamente."""
    # Crear orden APROBADA
    orden = OrdenPago(
        numero_orden="OP-2026-00050",
        incapacidad_id=test_incapacidad_arl_aprobada.id,
        beneficiario_tipo=BeneficiarioTipo.EMPLEADO,
        beneficiario_id=test_empleado.id,
        beneficiario_nombre=test_empleado.nombre_completo,
        beneficiario_documento=test_empleado.numero_documento,
        cuenta_bancaria=test_empleado.cuenta_bancaria,
        banco=test_empleado.banco,
        tipo_cuenta=test_empleado.tipo_cuenta,
        valor_pagar=Decimal("1000000.00"),
        estado_pago=EstadoOrdenPago.APROBADA
    )
    db_session.add(orden)
    await db_session.commit()
    await db_session.refresh(orden)
    
    # Registrar pago
    usuario_id = uuid4()
    with patch("app.services.orden_pago_service.historial_estado_service.create_historial", new_callable=AsyncMock):
        with patch("app.services.orden_pago_service.incapacidad_service") as mock_incap_service:
            mock_incap_service.cambiar_estado = AsyncMock()
            
            orden_pagada = await orden_pago_service.registrar_pago(
                db=db_session,
                orden_pago_id=orden.id,
                usuario_id=usuario_id,
                referencia_pago="REF-12345",
                comprobante_ruta="/comprobantes/comp.pdf"
            )
    
    assert orden_pagada.estado_pago == EstadoOrdenPago.PAGADA
    assert orden_pagada.referencia_pago == "REF-12345"
    assert orden_pagada.fecha_pago is not None


@pytest.mark.asyncio
async def test_registrar_pago_invalid_state(
    db_session: AsyncSession,
    test_incapacidad_arl_aprobada,
    test_empleado
):
    """Test registrar pago en estado inválido."""
    # Crear orden GENERADA
    orden = OrdenPago(
        numero_orden="OP-2026-00051",
        incapacidad_id=test_incapacidad_arl_aprobada.id,
        beneficiario_tipo=BeneficiarioTipo.EMPLEADO,
        beneficiario_id=test_empleado.id,
        beneficiario_nombre=test_empleado.nombre_completo,
        beneficiario_documento=test_empleado.numero_documento,
        cuenta_bancaria=test_empleado.cuenta_bancaria,
        banco=test_empleado.banco,
        tipo_cuenta=test_empleado.tipo_cuenta,
        valor_pagar=Decimal("1000000.00"),
        estado_pago=EstadoOrdenPago.GENERADA
    )
    db_session.add(orden)
    await db_session.commit()
    
    with pytest.raises(InvalidStateException):
        await orden_pago_service.registrar_pago(
            db=db_session,
            orden_pago_id=orden.id,
            usuario_id=uuid4(),
            referencia_pago="REF-12345"
        )


@pytest.mark.asyncio
async def test_anular_orden_success(
    db_session: AsyncSession,
    test_incapacidad_arl_aprobada,
    test_empleado
):
    """Test anular orden exitosamente."""
    # Crear orden GENERADA
    orden = OrdenPago(
        numero_orden="OP-2026-00060",
        incapacidad_id=test_incapacidad_arl_aprobada.id,
        beneficiario_tipo=BeneficiarioTipo.EMPLEADO,
        beneficiario_id=test_empleado.id,
        beneficiario_nombre=test_empleado.nombre_completo,
        beneficiario_documento=test_empleado.numero_documento,
        cuenta_bancaria=test_empleado.cuenta_bancaria,
        banco=test_empleado.banco,
        tipo_cuenta=test_empleado.tipo_cuenta,
        valor_pagar=Decimal("1000000.00"),
        estado_pago=EstadoOrdenPago.GENERADA
    )
    db_session.add(orden)
    await db_session.commit()
    await db_session.refresh(orden)
    
    # Anular
    usuario_id = uuid4()
    with patch("app.services.orden_pago_service.historial_estado_service.create_historial", new_callable=AsyncMock):
        orden_anulada = await orden_pago_service.anular_orden(
            db=db_session,
            orden_pago_id=orden.id,
            usuario_id=usuario_id,
            motivo_anulacion="Prueba de anulación por error en datos"
        )
    
    assert orden_anulada.estado_pago == EstadoOrdenPago.ANULADA
    assert orden_anulada.motivo_anulacion == "Prueba de anulación por error en datos"
    assert orden_anulada.fecha_anulacion is not None


@pytest.mark.asyncio
async def test_anular_orden_pagada_fails(
    db_session: AsyncSession,
    test_incapacidad_arl_aprobada,
    test_empleado
):
    """Test anular orden ya pagada falla."""
    # Crear orden PAGADA
    orden = OrdenPago(
        numero_orden="OP-2026-00061",
        incapacidad_id=test_incapacidad_arl_aprobada.id,
        beneficiario_tipo=BeneficiarioTipo.EMPLEADO,
        beneficiario_id=test_empleado.id,
        beneficiario_nombre=test_empleado.nombre_completo,
        beneficiario_documento=test_empleado.numero_documento,
        cuenta_bancaria=test_empleado.cuenta_bancaria,
        banco=test_empleado.banco,
        tipo_cuenta=test_empleado.tipo_cuenta,
        valor_pagar=Decimal("1000000.00"),
        estado_pago=EstadoOrdenPago.PAGADA,
        fecha_pago=datetime.utcnow()
    )
    db_session.add(orden)
    await db_session.commit()
    
    with pytest.raises(InvalidStateException):
        await orden_pago_service.anular_orden(
            db=db_session,
            orden_pago_id=orden.id,
            usuario_id=uuid4(),
            motivo_anulacion="Intento de anular orden pagada"
        )


@pytest.mark.asyncio
async def test_anular_orden_motivo_corto_fails(
    db_session: AsyncSession,
    test_incapacidad_arl_aprobada,
    test_empleado
):
    """Test anular orden con motivo muy corto falla."""
    # Crear orden
    orden = OrdenPago(
        numero_orden="OP-2026-00062",
        incapacidad_id=test_incapacidad_arl_aprobada.id,
        beneficiario_tipo=BeneficiarioTipo.EMPLEADO,
        beneficiario_id=test_empleado.id,
        beneficiario_nombre=test_empleado.nombre_completo,
        beneficiario_documento=test_empleado.numero_documento,
        cuenta_bancaria=test_empleado.cuenta_bancaria,
        banco=test_empleado.banco,
        tipo_cuenta=test_empleado.tipo_cuenta,
        valor_pagar=Decimal("1000000.00"),
        estado_pago=EstadoOrdenPago.GENERADA
    )
    db_session.add(orden)
    await db_session.commit()
    
    with pytest.raises(BadRequestException) as exc_info:
        await orden_pago_service.anular_orden(
            db=db_session,
            orden_pago_id=orden.id,
            usuario_id=uuid4(),
            motivo_anulacion="Error"  # Menos de 10 caracteres
        )
    
    assert "10 caracteres" in str(exc_info.value).lower()

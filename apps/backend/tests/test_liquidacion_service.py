"""
TDD tests for Task 5.2: Liquidacion service + endpoints.

Tests:
1.  devolucion_requiere_observacion — BadRequestException when observacion=""
2.  devolucion_desde_estado_invalido — InvalidStateException when not in LIQUIDACION/LIQUIDACION_PARCIAL
3.  devolucion_exitosa_desde_liquidacion — transitions to EN_AUDITORIA
4.  devolucion_exitosa_desde_liquidacion_parcial — transitions to EN_AUDITORIA
5.  guardar_liquidacion_crea_registro — crea registro en DB
6.  guardar_liquidacion_actualiza_registro — segunda llamada actualiza (no duplica)
7.  guardar_liquidacion_estado_invalido — InvalidStateException when not in LIQUIDACION
8.  get_liquidacion_not_found — NotFoundException when no liquidacion exists
9.  calcular_ibl_stub_retorna_null — always returns ibl=None
10. calcular_breakdown_placeholder_all_none — all values None while C1 pending
11. calcular_breakdown_ibl_none — None ibl returns all None breakdown
12. completar_liquidacion_a_en_pago — LIQUIDACION → EN_PAGO
13. completar_liquidacion_a_en_pago_parcial — LIQUIDACION_PARCIAL → EN_PAGO_PARCIAL
14. completar_liquidacion_sin_registro — NotFoundException if no liquidacion saved
"""
import pytest
import sqlalchemy as sa
from datetime import date
from decimal import Decimal
from uuid import uuid4

from app.core.exceptions import BadRequestException, InvalidStateException, NotFoundException
from app.utils.enums import EstadoIncapacidad


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _make_incapacidad(db_session, estado: str = "LIQUIDACION") -> sa.engine.Row:
    """Insert a minimal incapacidad in the given estado and return its id."""
    inc_id = uuid4()
    await db_session.execute(sa.text("""
        INSERT INTO incapacidad (
            id, numero, tipo, estado, prioridad, prorroga,
            fecha_inicio, fecha_fin, dias_totales, fecha_radicacion,
            created_at, updated_at
        ) VALUES (
            :id, :numero, 'ARL', :estado, 'NORMAL', false,
            '2026-01-01', '2026-01-10', 10, NOW(),
            NOW(), NOW()
        )
    """), {"id": str(inc_id), "numero": f"INC-TEST-{inc_id.hex[:8]}", "estado": estado})
    await db_session.commit()
    return inc_id


async def _make_incapacidad_arl_con_siniestro(db_session, estado: str = "LIQUIDACION") -> "UUID":
    """Crea Empresa + Empleado + Siniestro + Incapacidad (ARL) vinculados, vía ORM."""
    from app.models.empresa import Empresa
    from app.models.empleado import Empleado
    from app.models.siniestro import Siniestro
    from app.models.incapacidad import Incapacidad
    from app.utils.enums import TipoDocumento, TipoIncapacidad, TipoSiniestro

    uid = uuid4()
    empresa = Empresa(nit=f"900{uid.hex[:6]}", razon_social="TechCorp S.A.S.")
    db_session.add(empresa)
    await db_session.flush()

    empleado = Empleado(
        empresa_id=empresa.id,
        numero_documento=str(uid.int % 10**9),
        tipo_documento=TipoDocumento.CC,
        nombres="Juan",
        apellidos="Pérez",
        fecha_ingreso=date(2020, 1, 1),
    )
    db_session.add(empleado)
    await db_session.flush()

    siniestro = Siniestro(
        numero_siniestro=f"SIN-TEST-{uid.hex[:8]}",
        empleado_id=empleado.id,
        empresa_id=empresa.id,
        fecha_siniestro=date(2026, 5, 1),
        tipo_siniestro=TipoSiniestro.ACCIDENTE_TRABAJO,
        descripcion="Accidente de prueba",
    )
    db_session.add(siniestro)
    await db_session.flush()

    incapacidad = Incapacidad(
        numero=f"INC-TEST-{uid.hex[:8]}",
        tipo=TipoIncapacidad.ARL,
        empresa_id=empresa.id,
        empleado_id=empleado.id,
        siniestro_id=siniestro.id,
        estado=estado,
        fecha_inicio=date(2026, 6, 1),
        fecha_fin=date(2026, 6, 10),
        dias_totales=10,
    )
    db_session.add(incapacidad)
    await db_session.commit()
    await db_session.refresh(incapacidad)
    return incapacidad.id


async def _make_liquidador(db_session) -> "UUID":
    """Create a minimal usuario (AUDITOR role) via ORM and return its id."""
    from app.models.usuario import Usuario
    from app.utils.enums import RolUsuario, EstadoUsuario
    from app.core.security import get_password_hash

    uid = uuid4()
    usuario = Usuario(
        username=f"liq_{uid.hex[:6]}",
        email=f"liq_{uid.hex[:6]}@test.com",
        password_hash=get_password_hash("Test123!"),
        nombre_completo="Liquidador Test",
        rol=RolUsuario.AUDITOR,
        estado=EstadoUsuario.ACTIVO,
    )
    db_session.add(usuario)
    await db_session.commit()
    await db_session.refresh(usuario)
    return usuario.id


async def _make_liquidacion_row(db_session, incapacidad_id) -> None:
    """Insert a minimal liquidacion row for the given incapacidad."""
    liq_id = uuid4()
    await db_session.execute(sa.text("""
        INSERT INTO liquidacion (
            id, incapacidad_id, dias_autorizados,
            fecha_inicio_autorizada, fecha_fin_autorizada,
            created_at, updated_at
        ) VALUES (
            :id, :inc_id, 10,
            '2026-01-01', '2026-01-10',
            NOW(), NOW()
        )
    """), {"id": str(liq_id), "inc_id": str(incapacidad_id)})
    await db_session.commit()


# ---------------------------------------------------------------------------
# 1. Devolution requires non-empty observacion
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_devolucion_requiere_observacion(db_session):
    """BadRequestException when observacion is empty."""
    from app.services.liquidacion_service import liquidacion_service

    inc_id = await _make_incapacidad(db_session, "LIQUIDACION")

    with pytest.raises(BadRequestException):
        await liquidacion_service.devolver_a_auditoria(
            db=db_session,
            incapacidad_id=inc_id,
            observacion="",
            liquidador_id=uuid4(),
        )


@pytest.mark.asyncio
async def test_devolucion_observacion_espacios_en_blanco(db_session):
    """BadRequestException when observacion is whitespace only."""
    from app.services.liquidacion_service import liquidacion_service

    inc_id = await _make_incapacidad(db_session, "LIQUIDACION")

    with pytest.raises(BadRequestException):
        await liquidacion_service.devolver_a_auditoria(
            db=db_session,
            incapacidad_id=inc_id,
            observacion="   ",
            liquidador_id=uuid4(),
        )


# ---------------------------------------------------------------------------
# 2. Devolution fails when incapacidad is not in LIQUIDACION / LIQUIDACION_PARCIAL
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_devolucion_desde_estado_invalido(db_session):
    """InvalidStateException when incapacidad is in EN_AUDITORIA."""
    from app.services.liquidacion_service import liquidacion_service

    inc_id = await _make_incapacidad(db_session, "EN_AUDITORIA")

    with pytest.raises(InvalidStateException):
        await liquidacion_service.devolver_a_auditoria(
            db=db_session,
            incapacidad_id=inc_id,
            observacion="Datos incorrectos",
            liquidador_id=uuid4(),
        )


# ---------------------------------------------------------------------------
# 3. Devolution from LIQUIDACION → EN_AUDITORIA
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_devolucion_exitosa_desde_liquidacion(db_session):
    """Successful devolution: LIQUIDACION → EN_AUDITORIA."""
    from app.services.liquidacion_service import liquidacion_service

    inc_id = await _make_incapacidad(db_session, "LIQUIDACION")
    liquidador_id = await _make_liquidador(db_session)

    incapacidad = await liquidacion_service.devolver_a_auditoria(
        db=db_session,
        incapacidad_id=inc_id,
        observacion="El IBL registrado no coincide con el reporte de nómina",
        liquidador_id=liquidador_id,
    )

    assert incapacidad.estado == EstadoIncapacidad.EN_AUDITORIA


# ---------------------------------------------------------------------------
# 4. Devolution from LIQUIDACION_PARCIAL → EN_AUDITORIA
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_devolucion_exitosa_desde_liquidacion_parcial(db_session):
    """Successful devolution: LIQUIDACION_PARCIAL → EN_AUDITORIA."""
    from app.services.liquidacion_service import liquidacion_service

    inc_id = await _make_incapacidad(db_session, "LIQUIDACION_PARCIAL")
    liquidador_id = await _make_liquidador(db_session)

    incapacidad = await liquidacion_service.devolver_a_auditoria(
        db=db_session,
        incapacidad_id=inc_id,
        observacion="Días aprobados no corresponden al diagnóstico",
        liquidador_id=liquidador_id,
    )

    assert incapacidad.estado == EstadoIncapacidad.EN_AUDITORIA


# ---------------------------------------------------------------------------
# 5. guardar_liquidacion creates a record
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_guardar_liquidacion_crea_registro(db_session):
    """guardar_liquidacion creates a Liquidacion row in the DB."""
    from app.services.liquidacion_service import liquidacion_service
    from app.schemas.liquidacion import LiquidacionGuardar

    inc_id = await _make_incapacidad(db_session, "LIQUIDACION")
    liquidador_id = await _make_liquidador(db_session)

    payload = LiquidacionGuardar(
        dias_autorizados=10,
        fecha_inicio_autorizada=date(2026, 1, 1),
        fecha_fin_autorizada=date(2026, 1, 10),
        ibl=Decimal("3500000.00"),
        notas_liquidador="Prueba de creación",
    )

    liq = await liquidacion_service.guardar_liquidacion(
        db=db_session,
        incapacidad_id=inc_id,
        data=payload,
        liquidador_id=liquidador_id,
    )

    assert liq is not None
    assert liq.incapacidad_id == inc_id
    assert liq.ibl == Decimal("3500000.00")
    assert liq.dias_autorizados == 10
    assert str(liq.liquidador_id) == str(liquidador_id)


# ---------------------------------------------------------------------------
# 6. guardar_liquidacion updates existing record (no duplicate)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_guardar_liquidacion_actualiza_registro(db_session):
    """Second call to guardar_liquidacion updates instead of inserting duplicate."""
    from app.services.liquidacion_service import liquidacion_service
    from app.schemas.liquidacion import LiquidacionGuardar

    inc_id = await _make_incapacidad(db_session, "LIQUIDACION")
    liquidador_id = await _make_liquidador(db_session)

    base_payload = LiquidacionGuardar(
        dias_autorizados=10,
        fecha_inicio_autorizada=date(2026, 1, 1),
        fecha_fin_autorizada=date(2026, 1, 10),
        ibl=Decimal("3500000.00"),
    )
    await liquidacion_service.guardar_liquidacion(
        db=db_session,
        incapacidad_id=inc_id,
        data=base_payload,
        liquidador_id=liquidador_id,
    )

    updated_payload = LiquidacionGuardar(
        dias_autorizados=10,
        fecha_inicio_autorizada=date(2026, 1, 1),
        fecha_fin_autorizada=date(2026, 1, 10),
        ibl=Decimal("4000000.00"),
        notas_liquidador="Valor IBL corregido",
    )
    liq2 = await liquidacion_service.guardar_liquidacion(
        db=db_session,
        incapacidad_id=inc_id,
        data=updated_payload,
        liquidador_id=liquidador_id,
    )

    assert liq2.ibl == Decimal("4000000.00")
    assert liq2.notas_liquidador == "Valor IBL corregido"

    # Only one row in the DB
    count_row = await db_session.execute(
        sa.text("SELECT COUNT(*) FROM liquidacion WHERE incapacidad_id = :id"),
        {"id": str(inc_id)},
    )
    assert count_row.scalar() == 1


# ---------------------------------------------------------------------------
# 7. guardar_liquidacion fails for wrong state
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_guardar_liquidacion_estado_invalido(db_session):
    """InvalidStateException when incapacidad is not in LIQUIDACION/LIQUIDACION_PARCIAL."""
    from app.services.liquidacion_service import liquidacion_service
    from app.schemas.liquidacion import LiquidacionGuardar

    inc_id = await _make_incapacidad(db_session, "EN_AUDITORIA")
    liquidador_id = await _make_liquidador(db_session)

    payload = LiquidacionGuardar(
        dias_autorizados=5,
        fecha_inicio_autorizada=date(2026, 1, 1),
        fecha_fin_autorizada=date(2026, 1, 5),
    )

    with pytest.raises(InvalidStateException):
        await liquidacion_service.guardar_liquidacion(
            db=db_session,
            incapacidad_id=inc_id,
            data=payload,
            liquidador_id=liquidador_id,
        )


# ---------------------------------------------------------------------------
# 8. get_liquidacion raises NotFoundException when not found
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_liquidacion_not_found(db_session):
    """NotFoundException when no liquidacion exists for the incapacidad."""
    from app.services.liquidacion_service import liquidacion_service

    inc_id = await _make_incapacidad(db_session, "LIQUIDACION")

    with pytest.raises(NotFoundException):
        await liquidacion_service.get_liquidacion(db_session, inc_id)


# ---------------------------------------------------------------------------
# 9. calcular_ibl_stub always returns ibl=None
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_calcular_ibl_stub_retorna_null(db_session):
    """calcular_ibl_stub returns ibl=None with informative nota."""
    from app.services.liquidacion_service import liquidacion_service

    inc_id = await _make_incapacidad(db_session, "LIQUIDACION")

    result = await liquidacion_service.calcular_ibl_stub(db_session, inc_id)

    assert result["ibl"] is None
    assert "Imaginex" in result["nota"]


# ---------------------------------------------------------------------------
# 10. _calcular_breakdown_real — valores correctos con seed 2026
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_calcular_breakdown_valores_correctos(db_session):
    """_calcular_breakdown_real devuelve valores correctos usando seed 2026."""
    from app.services.liquidacion_service import _calcular_breakdown_real

    await db_session.execute(sa.text("""
        INSERT INTO ibl_parametros
          (id, ano, aporte_patronal_pension, aporte_patronal_salud,
           aporte_trabajador_pension, aporte_trabajador_salud,
           created_at, updated_at)
        VALUES
          (gen_random_uuid(), 2026, 12.00, 8.50, 4.00, 4.00, NOW(), NOW())
        ON CONFLICT (ano) DO NOTHING
    """))
    await db_session.commit()

    ibl = Decimal("3500000")
    dias = 10
    result = await _calcular_breakdown_real(db_session, ibl, dias, 2026)

    assert result["incapacidad_temporal"] == Decimal("35000000.00")
    assert result["aporte_patronal_pension"] == Decimal("4200000.00")
    assert result["aporte_trabajador_pension"] == Decimal("1400000.00")
    assert result["aporte_patronal_salud"] == Decimal("2975000.00")
    assert result["aporte_trabajador_salud"] == Decimal("1400000.00")
    assert result["aporte_adicional_trabajador_pension"] is None
    expected_total = (
        Decimal("35000000.00") + Decimal("4200000.00") + Decimal("1400000.00")
        + Decimal("2975000.00") + Decimal("1400000.00")
    )
    assert result["valor_total"] == expected_total


@pytest.mark.asyncio
async def test_calcular_breakdown_ano_sin_parametros(db_session):
    """_calcular_breakdown_real lanza BadRequestException para año sin parámetros."""
    from app.core.exceptions import BadRequestException
    from app.services.liquidacion_service import _calcular_breakdown_real

    with pytest.raises(BadRequestException) as exc_info:
        await _calcular_breakdown_real(db_session, Decimal("3500000"), 10, 2030)

    assert "2030" in str(exc_info.value)


# ---------------------------------------------------------------------------
# 11. calcular_breakdown with ibl=None returns None for all breakdown fields
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_calcular_breakdown_ibl_none(db_session):
    """When ibl=None, calcular_breakdown returns None for all breakdown values."""
    from app.services.liquidacion_service import liquidacion_service

    inc_id = await _make_incapacidad(db_session, "LIQUIDACION")

    result = await liquidacion_service.calcular_breakdown(
        db=db_session,
        incapacidad_id=inc_id,
        ibl=None,
        dias=10,
    )

    assert result["ibl"] is None
    assert result["dias"] == 10
    assert result["incapacidad_temporal"] is None
    assert "nota" in result


# ---------------------------------------------------------------------------
# 12. completar_liquidacion: LIQUIDACION → EN_PAGO
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_completar_liquidacion_a_en_pago(db_session):
    """completar_liquidacion transitions LIQUIDACION → EN_PAGO."""
    from app.services.liquidacion_service import liquidacion_service

    inc_id = await _make_incapacidad(db_session, "LIQUIDACION")
    liquidador_id = await _make_liquidador(db_session)
    await _make_liquidacion_row(db_session, inc_id)

    incapacidad = await liquidacion_service.completar_liquidacion(
        db=db_session,
        incapacidad_id=inc_id,
        liquidador_id=liquidador_id,
    )

    assert incapacidad.estado == EstadoIncapacidad.EN_PAGO


# ---------------------------------------------------------------------------
# 13. completar_liquidacion: LIQUIDACION_PARCIAL → EN_PAGO_PARCIAL
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_completar_liquidacion_a_en_pago_parcial(db_session):
    """completar_liquidacion transitions LIQUIDACION_PARCIAL → EN_PAGO_PARCIAL."""
    from app.services.liquidacion_service import liquidacion_service

    inc_id = await _make_incapacidad(db_session, "LIQUIDACION_PARCIAL")
    liquidador_id = await _make_liquidador(db_session)
    await _make_liquidacion_row(db_session, inc_id)

    incapacidad = await liquidacion_service.completar_liquidacion(
        db=db_session,
        incapacidad_id=inc_id,
        liquidador_id=liquidador_id,
    )

    assert incapacidad.estado == EstadoIncapacidad.EN_PAGO_PARCIAL


# ---------------------------------------------------------------------------
# 14. completar_liquidacion fails if no liquidacion record exists
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_completar_liquidacion_sin_registro(db_session):
    """NotFoundException when completar_liquidacion called without a saved liquidacion."""
    from app.services.liquidacion_service import liquidacion_service

    inc_id = await _make_incapacidad(db_session, "LIQUIDACION")
    liquidador_id = await _make_liquidador(db_session)

    with pytest.raises(NotFoundException):
        await liquidacion_service.completar_liquidacion(
            db=db_session,
            incapacidad_id=inc_id,
            liquidador_id=liquidador_id,
        )


# ---------------------------------------------------------------------------
# 15. guardar_liquidacion writes sucursal onto the linked Siniestro
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_guardar_liquidacion_updates_siniestro_sucursal(db_session):
    """guardar_liquidacion writes sucursal onto the linked Siniestro, and the
    returned Liquidacion carries it back for the response schema."""
    from app.services.liquidacion_service import liquidacion_service
    from app.services.incapacidad_service import incapacidad_service
    from app.schemas.liquidacion import LiquidacionGuardar
    from app.utils.enums import SucursalSiniestro

    inc_id = await _make_incapacidad_arl_con_siniestro(db_session, "LIQUIDACION")
    liquidador_id = await _make_liquidador(db_session)

    data = LiquidacionGuardar(
        dias_autorizados=5,
        fecha_inicio_autorizada=date(2026, 6, 1),
        fecha_fin_autorizada=date(2026, 6, 5),
        sucursal=SucursalSiniestro.BOGOTA,
    )
    liquidacion = await liquidacion_service.guardar_liquidacion(
        db=db_session, incapacidad_id=inc_id, data=data, liquidador_id=liquidador_id,
    )

    incapacidad = await incapacidad_service.get_incapacidad(db_session, inc_id)
    assert incapacidad.siniestro.sucursal == SucursalSiniestro.BOGOTA
    assert liquidacion.sucursal == SucursalSiniestro.BOGOTA

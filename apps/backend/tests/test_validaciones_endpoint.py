"""
Tests de integración para GET /api/v1/incapacidades/{id}/validaciones.
"""
from datetime import date, datetime, timedelta
from uuid import uuid4
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.incapacidad import Incapacidad
from app.models.pre_incapacidad import PreIncapacidad
from app.models.validation_inconsistencia import ValidationInconsistencia
from app.utils.enums import TipoIncapacidad, EstadoIncapacidad, Prioridad


async def _seed_incapacidad(db: AsyncSession) -> Incapacidad:
    inc = Incapacidad(
        numero=f"INC-VAL-{uuid4().hex[:8]}",
        tipo=TipoIncapacidad.ARL,
        estado=EstadoIncapacidad.EN_AUDITORIA,
        prioridad=Prioridad.NORMAL,
        fecha_inicio=date.today(),
        fecha_fin=date.today() + timedelta(days=5),
        dias_totales=6,
        fecha_radicacion=datetime.utcnow(),
    )
    db.add(inc)
    await db.flush()
    return inc


async def _seed_pre_inc(db: AsyncSession, incapacidad_id) -> PreIncapacidad:
    pre = PreIncapacidad(
        estado="PROCESADA",
        solicitante_correo="x@x.com",
        solicitante_nombres="X",
        empleado_tipo_documento="CC",
        empleado_numero_documento="11111111",
        empleado_nombres="Test",
        tipo="ARL",
        tipo_enfermedad="ACCIDENTE_TRABAJO",
        fecha_inicio=date.today(),
        fecha_fin=date.today() + timedelta(days=5),
        dias_totales=6,
        diagnostico_cie10="M54.5",
        nombre_medico="Dr. X",
        registro_medico="REG-X",
        incapacidad_id=incapacidad_id,
    )
    db.add(pre)
    await db.flush()
    return pre


@pytest.mark.asyncio
async def test_get_validaciones_returns_issues(
    client: AsyncClient, db_session: AsyncSession, admin_token_headers: dict
):
    """El endpoint retorna los issues asociados a la incapacidad."""
    inc = await _seed_incapacidad(db_session)
    pre = await _seed_pre_inc(db_session, inc.id)
    issue = ValidationInconsistencia(
        pre_incapacidad_id=pre.id,
        incapacidad_id=inc.id,
        categoria="INTEGRATION_CHECK",
        severidad="WARNING",
        codigo="EMPLEADO_NOT_FOUND",
        descripcion="Empleado no encontrado en BD",
    )
    db_session.add(issue)
    await db_session.commit()

    response = await client.get(
        f"/api/v1/incapacidades/{inc.id}/validaciones",
        headers=admin_token_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["has_errors"] is False
    assert data["has_fraud_alert"] is False
    assert data["issues"][0]["codigo"] == "EMPLEADO_NOT_FOUND"


@pytest.mark.asyncio
async def test_get_validaciones_has_fraud_alert(
    client: AsyncClient, db_session: AsyncSession, admin_token_headers: dict
):
    """has_fraud_alert es True cuando hay un issue de categoría FRAUD_ALERT."""
    inc = await _seed_incapacidad(db_session)
    pre = await _seed_pre_inc(db_session, inc.id)
    issue = ValidationInconsistencia(
        pre_incapacidad_id=pre.id,
        incapacidad_id=inc.id,
        categoria="FRAUD_ALERT",
        severidad="WARNING",
        codigo="POSSIBLE_DUPLICATE",
        descripcion="Posible duplicado",
    )
    db_session.add(issue)
    await db_session.commit()

    response = await client.get(
        f"/api/v1/incapacidades/{inc.id}/validaciones",
        headers=admin_token_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["has_fraud_alert"] is True


@pytest.mark.asyncio
async def test_get_validaciones_empty_for_clean_incapacidad(
    client: AsyncClient, db_session: AsyncSession, admin_token_headers: dict
):
    """Incapacidad sin issues retorna lista vacía y todos los flags en False."""
    inc = await _seed_incapacidad(db_session)
    await db_session.commit()

    response = await client.get(
        f"/api/v1/incapacidades/{inc.id}/validaciones",
        headers=admin_token_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["has_errors"] is False
    assert data["has_fraud_alert"] is False
    assert data["issues"] == []


@pytest.mark.asyncio
async def test_get_validaciones_includes_pre_incapacidad_issues(
    client: AsyncClient, db_session: AsyncSession, admin_token_headers: dict
):
    """Issues con solo pre_incapacidad_id (sin incapacidad_id directo) también aparecen."""
    inc = await _seed_incapacidad(db_session)
    pre = await _seed_pre_inc(db_session, inc.id)
    issue = ValidationInconsistencia(
        pre_incapacidad_id=pre.id,
        incapacidad_id=None,
        categoria="FIELD_VALIDATION",
        severidad="INFO",
        codigo="MISSING_FIELD",
        descripcion="Campo faltante",
    )
    db_session.add(issue)
    await db_session.commit()

    response = await client.get(
        f"/api/v1/incapacidades/{inc.id}/validaciones",
        headers=admin_token_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["issues"][0]["codigo"] == "MISSING_FIELD"


@pytest.mark.asyncio
async def test_pendientes_includes_empleado_fallback(
    client: AsyncClient, db_session: AsyncSession, admin_token_headers: dict
):
    """Cuando empleado_id es NULL, el response incluye empleado_fallback desde pre_incapacidad."""
    from datetime import datetime
    inc = Incapacidad(
        numero=f"INC-FB-{uuid4().hex[:8]}",
        tipo=TipoIncapacidad.ARL,
        estado=EstadoIncapacidad.RADICADA,
        prioridad=Prioridad.NORMAL,
        fecha_inicio=date.today(),
        fecha_fin=date.today() + timedelta(days=5),
        dias_totales=6,
        fecha_radicacion=datetime.utcnow(),
        empleado_id=None,
        empresa_id=None,
    )
    db_session.add(inc)
    await db_session.flush()

    pre = PreIncapacidad(
        estado="PROCESADA",
        solicitante_correo="fb@test.com",
        solicitante_nombres="FB",
        empleado_tipo_documento="CC",
        empleado_numero_documento="99887766",
        empleado_nombres="Carlos Fallback",
        tipo="ARL",
        tipo_enfermedad="ACCIDENTE_TRABAJO",
        fecha_inicio=date.today(),
        fecha_fin=date.today() + timedelta(days=5),
        dias_totales=6,
        diagnostico_cie10="S50.0",
        nombre_medico="Dr. FB",
        registro_medico="REG-FB",
        empresa_nit="999888777",
        empresa_nombre="Empresa Fallback SAS",
        incapacidad_id=inc.id,
    )
    db_session.add(pre)
    await db_session.commit()

    response = await client.get("/api/v1/incapacidades/pendientes", headers=admin_token_headers)
    assert response.status_code == 200
    items = response.json()
    target = next((i for i in items if i["numero"] == inc.numero), None)
    assert target is not None
    assert target["empleado_fallback"] is not None
    assert target["empleado_fallback"]["nombres"] == "Carlos Fallback"
    assert target["empleado_fallback"]["numero_documento"] == "99887766"
    assert target["empresa_fallback"] is not None
    assert target["empresa_fallback"]["nit"] == "999888777"
    assert target["empresa_fallback"]["nombre"] == "Empresa Fallback SAS"

"""
Tests de integración para los endpoints de pre-incapacidades.
Cubre: POST /radicar, POST /{id}/documentos, GET /{id}
"""
import io
from datetime import date, timedelta
from unittest.mock import patch, MagicMock
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pre_incapacidad import PreIncapacidad


RADICAR_URL = "/api/v1/pre-incapacidades/radicar"

VALID_PAYLOAD = {
    "solicitante": {
        "correo": "solicitante@test.com",
        "nombres": "Maria",
        "apellidos": "González",
        "telefono": "3001234567",
    },
    "empresa": {
        "nit": "900123456",
        "nombre": "Empresa Test SAS",
    },
    "empleado": {
        "tipo_documento": "CC",
        "numero_documento": "1234567890",
        "nombres": "Carlos",
        "apellidos": "Pérez",
        "email": "carlos@test.com",
        "telefono": "3109876543",
    },
    "incapacidad": {
        "tipo_enfermedad": "ACCIDENTE_TRABAJO",
        "fecha_inicio": str(date.today()),
        "fecha_fin": str(date.today() + timedelta(days=5)),
        "diagnostico_cie10": "M545",
        "nombre_medico": "Dr. García",
        "registro_medico": "REG-001",
    },
}


@pytest.fixture
async def pre_incapacidad_en_db(db_session: AsyncSession) -> PreIncapacidad:
    """Crea una pre-incapacidad real en BD para tests de consulta y documentos."""
    pre_inc = PreIncapacidad(
        estado="PENDIENTE",
        solicitante_correo="test@example.com",
        solicitante_nombres="Juan",
        empleado_tipo_documento="CC",
        empleado_numero_documento="9876543210",
        empleado_nombres="Pedro",
        tipo="ARL",
        tipo_enfermedad="ACCIDENTE_TRABAJO",
        fecha_inicio=date.today(),
        fecha_fin=date.today() + timedelta(days=5),
        dias_totales=6,
        diagnostico_cie10="M545",
        nombre_medico="Dr. López",
        registro_medico="MED-001",
        empresa_nit="900999888",
        empresa_nombre="Empresa API Test",
    )
    db_session.add(pre_inc)
    await db_session.commit()
    await db_session.refresh(pre_inc)
    return pre_inc


# ── POST /radicar ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_radicar_returns_201_with_numero_radicacion(client: AsyncClient):
    """POST /radicar debe retornar 201 con numero_radicacion y estado PENDIENTE."""
    with patch("app.tasks.incapacidad_tasks.promote_pre_incapacidad_task") as mock_task:
        mock_task.delay = MagicMock()
        response = await client.post(RADICAR_URL, json=VALID_PAYLOAD)

    assert response.status_code == 201
    data = response.json()
    assert "numero_radicacion" in data
    assert data["estado"] == "PENDIENTE"
    assert data["numero_radicacion"] > 0


@pytest.mark.asyncio
async def test_radicar_enqueues_promotion_task(client: AsyncClient):
    """POST /radicar debe encolar la tarea de promoción."""
    with patch("app.tasks.incapacidad_tasks.promote_pre_incapacidad_task") as mock_task:
        mock_task.delay = MagicMock()
        response = await client.post(RADICAR_URL, json=VALID_PAYLOAD)

    assert response.status_code == 201
    mock_task.delay.assert_called_once()


@pytest.mark.asyncio
async def test_radicar_sin_empresa_returns_201(client: AsyncClient):
    """POST /radicar sin empresa (trabajador independiente) debe funcionar."""
    payload = dict(VALID_PAYLOAD)
    payload["empresa"] = None

    with patch("app.tasks.incapacidad_tasks.promote_pre_incapacidad_task") as mock_task:
        mock_task.delay = MagicMock()
        response = await client.post(RADICAR_URL, json=payload)

    assert response.status_code == 201


@pytest.mark.asyncio
async def test_radicar_invalid_email_returns_422(client: AsyncClient):
    """POST /radicar con email inválido debe retornar 422."""
    payload = dict(VALID_PAYLOAD)
    payload["solicitante"] = dict(VALID_PAYLOAD["solicitante"])
    payload["solicitante"]["correo"] = "not-an-email"

    response = await client.post(RADICAR_URL, json=payload)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_radicar_invalid_date_range_returns_422(client: AsyncClient):
    """POST /radicar con fecha_fin < fecha_inicio debe retornar 422."""
    payload = dict(VALID_PAYLOAD)
    payload["incapacidad"] = dict(VALID_PAYLOAD["incapacidad"])
    payload["incapacidad"]["fecha_inicio"] = str(date.today())
    payload["incapacidad"]["fecha_fin"] = str(date.today() - timedelta(days=1))

    response = await client.post(RADICAR_URL, json=payload)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_radicar_missing_required_field_returns_422(client: AsyncClient):
    """POST /radicar sin campo requerido debe retornar 422."""
    payload = dict(VALID_PAYLOAD)
    payload["empleado"] = dict(VALID_PAYLOAD["empleado"])
    del payload["empleado"]["numero_documento"]

    response = await client.post(RADICAR_URL, json=payload)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_radicar_invalid_tipo_documento_returns_422(client: AsyncClient):
    """POST /radicar con tipo_documento no permitido debe retornar 422."""
    payload = dict(VALID_PAYLOAD)
    payload["empleado"] = dict(VALID_PAYLOAD["empleado"])
    payload["empleado"]["tipo_documento"] = "INVALID"

    response = await client.post(RADICAR_URL, json=payload)

    assert response.status_code == 422


# ── GET /{id} ──────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_pre_incapacidad_returns_200(
    client: AsyncClient, pre_incapacidad_en_db: PreIncapacidad
):
    """GET /{id} debe retornar 200 con los datos completos."""
    response = await client.get(f"/api/v1/pre-incapacidades/{pre_incapacidad_en_db.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(pre_incapacidad_en_db.id)
    assert data["estado"] == "PENDIENTE"
    assert data["tipo"] == "ARL"
    assert data["empleado_numero_documento"] == "9876543210"
    assert data["empresa_nit"] == "900999888"


@pytest.mark.asyncio
async def test_get_pre_incapacidad_includes_documentos_array(
    client: AsyncClient, pre_incapacidad_en_db: PreIncapacidad
):
    """GET /{id} debe incluir el campo 'documentos' como array."""
    response = await client.get(f"/api/v1/pre-incapacidades/{pre_incapacidad_en_db.id}")

    data = response.json()
    assert "documentos" in data
    assert isinstance(data["documentos"], list)


@pytest.mark.asyncio
async def test_get_pre_incapacidad_includes_validation_inconsistencias(
    client: AsyncClient, pre_incapacidad_en_db: PreIncapacidad
):
    """GET /{id} debe incluir el campo 'validation_inconsistencias' como array."""
    response = await client.get(f"/api/v1/pre-incapacidades/{pre_incapacidad_en_db.id}")

    data = response.json()
    assert "validation_inconsistencias" in data
    assert isinstance(data["validation_inconsistencias"], list)


@pytest.mark.asyncio
async def test_get_pre_incapacidad_not_found_returns_404(client: AsyncClient):
    """GET /{id} con ID inexistente debe retornar 404."""
    response = await client.get(f"/api/v1/pre-incapacidades/{uuid4()}")

    assert response.status_code == 404


# ── POST /{id}/documentos ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_upload_documento_returns_201(
    client: AsyncClient, pre_incapacidad_en_db: PreIncapacidad
):
    """POST /{id}/documentos con archivo válido debe retornar 201."""
    file_content = b"%PDF-1.4 test content"
    files = {"file": ("test.pdf", io.BytesIO(file_content), "application/pdf")}
    data = {"tipo_documento": "INCAPACIDAD_MEDICA"}

    response = await client.post(
        f"/api/v1/pre-incapacidades/{pre_incapacidad_en_db.id}/documentos",
        files=files,
        data=data,
    )

    assert response.status_code == 201
    resp_data = response.json()
    assert "id" in resp_data
    assert resp_data["tipo_documento"] == "INCAPACIDAD_MEDICA"
    assert resp_data["nombre_original"] == "test.pdf"
    assert resp_data["estado_subida"] in ("OK", "ERROR")


@pytest.mark.asyncio
async def test_upload_documento_invalid_tipo_returns_422(
    client: AsyncClient, pre_incapacidad_en_db: PreIncapacidad
):
    """POST /{id}/documentos con tipo inválido debe retornar 422 (ValidationException)."""
    files = {"file": ("test.pdf", io.BytesIO(b"content"), "application/pdf")}
    data = {"tipo_documento": "TIPO_INVALIDO"}

    response = await client.post(
        f"/api/v1/pre-incapacidades/{pre_incapacidad_en_db.id}/documentos",
        files=files,
        data=data,
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_upload_documento_invalid_extension_returns_422(
    client: AsyncClient, pre_incapacidad_en_db: PreIncapacidad
):
    """POST /{id}/documentos con extensión no permitida debe retornar 422 (ValidationException)."""
    files = {"file": ("malware.exe", io.BytesIO(b"bad content"), "application/octet-stream")}
    data = {"tipo_documento": "SOPORTE_ADICIONAL"}

    response = await client.post(
        f"/api/v1/pre-incapacidades/{pre_incapacidad_en_db.id}/documentos",
        files=files,
        data=data,
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_upload_documento_pre_inc_not_found_returns_404(client: AsyncClient):
    """POST /{id}/documentos con pre-incapacidad inexistente debe retornar 404."""
    files = {"file": ("test.pdf", io.BytesIO(b"content"), "application/pdf")}
    data = {"tipo_documento": "INCAPACIDAD_MEDICA"}

    response = await client.post(
        f"/api/v1/pre-incapacidades/{uuid4()}/documentos",
        files=files,
        data=data,
    )

    assert response.status_code == 404

"""
Tests para el endpoint REST de registro manual de siniestro previsional
(Task 4.4): app/api/v1/endpoints/previsionales/siniestros.py.

Usa `client` (httpx AsyncClient contra la app real, `get_db` sobreescrito
con `db_session` -- ver tests/conftest.py), mismo patrón de fixtures que
`test_endpoints_previsionales_auditoria.py` (Task 4.2).
"""
from __future__ import annotations

from datetime import date
from uuid import uuid4

import pytest
import pytest_asyncio

from app.core.security import create_access_token, get_password_hash
from app.models.previsionales.incapacidad_previsional import IncapacidadPrevisional
from app.models.previsionales.lote_previsional import LotePrevisional
from app.models.usuario import Usuario
from app.utils.enums import EstadoUsuario, RolUsuario


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


async def _crear_usuario_con_rol(db_session, rol: RolUsuario, username: str) -> Usuario:
    usuario = Usuario(
        username=username,
        email=f"{username}@example.com",
        password_hash=get_password_hash("Test1234!"),
        nombre_completo=f"Usuario {rol.value}",
        rol=rol,
        estado=EstadoUsuario.ACTIVO,
    )
    db_session.add(usuario)
    await db_session.commit()
    await db_session.refresh(usuario)
    return usuario


def _headers_para(usuario: Usuario) -> dict:
    token = create_access_token(
        data={"sub": str(usuario.id), "token_version": usuario.token_version}
    )
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def auditor_previsionales(db_session) -> Usuario:
    return await _crear_usuario_con_rol(
        db_session, RolUsuario.AUDITOR_PREVISIONALES, "auditor_previsionales_sin_ep"
    )


@pytest_asyncio.fixture
async def auditor_previsionales_headers(auditor_previsionales) -> dict:
    return _headers_para(auditor_previsionales)


@pytest_asyncio.fixture
async def readonly_headers(db_session) -> dict:
    usuario = await _crear_usuario_con_rol(db_session, RolUsuario.READONLY, "readonly_sin_ep")
    return _headers_para(usuario)


@pytest_asyncio.fixture
async def incapacidad_previsional(db_session) -> IncapacidadPrevisional:
    """Una IncapacidadPrevisional aislada dentro de su propio lote, usada
    para probar el autocompletado de `identificacion` vía `incapacidad_id`."""
    lote = LotePrevisional(nombre_archivo="RADICADOS_AUDITORIA_SIN_EP.xlsx")
    db_session.add(lote)
    await db_session.flush()

    inc = IncapacidadPrevisional(
        lote_id=lote.id,
        identificacion="1000000042",
        fecha_inicial=date(2026, 1, 1),
        fecha_final=date(2026, 1, 20),
        tipo_ingreso="INICIAL",
    )
    db_session.add(inc)
    await db_session.commit()
    await db_session.refresh(inc)
    return inc


ENDPOINT = "/api/v1/previsionales/siniestros"


# ---------------------------------------------------------------------------
# POST /previsionales/siniestros
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_crear_siniestro_con_todos_los_campos(client, auditor_previsionales_headers):
    resp = await client.post(
        ENDPOINT,
        headers=auditor_previsionales_headers,
        json={
            "identificacion": "1000000010",
            "numero_siniestro": "SIN-MANUAL-001",
            "origen": "ARL",
            "estado": "ABIERTO",
            "fecha_aviso": "2026-01-10",
            "fecha_siniestro": "2026-01-05",
        },
    )

    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["identificacion"] == "1000000010"
    assert data["numero_siniestro"] == "SIN-MANUAL-001"
    assert data["origen"] == "ARL"
    assert data["estado"] == "ABIERTO"
    assert data["fecha_aviso"] == "2026-01-10"
    assert data["fecha_siniestro"] == "2026-01-05"
    assert "id" in data


@pytest.mark.asyncio
async def test_crear_siniestro_solo_campos_requeridos(client, auditor_previsionales_headers):
    resp = await client.post(
        ENDPOINT,
        headers=auditor_previsionales_headers,
        json={
            "identificacion": "1000000011",
            "numero_siniestro": "SIN-MANUAL-002",
        },
    )

    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["identificacion"] == "1000000011"
    assert data["numero_siniestro"] == "SIN-MANUAL-002"
    assert data["origen"] is None
    assert data["estado"] is None
    assert data["fecha_aviso"] is None
    assert data["fecha_siniestro"] is None


@pytest.mark.asyncio
async def test_crear_siniestro_fecha_siniestro_posterior_a_aviso_no_se_rechaza(
    client, auditor_previsionales_headers
):
    """Regla AP del motor de auditoría trata esta comparación como
    informativa para datos importados; por consistencia, tampoco se
    rechaza aquí (ver docstring del endpoint)."""
    resp = await client.post(
        ENDPOINT,
        headers=auditor_previsionales_headers,
        json={
            "identificacion": "1000000012",
            "numero_siniestro": "SIN-MANUAL-003",
            "fecha_aviso": "2026-01-01",
            "fecha_siniestro": "2026-01-15",
        },
    )

    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["fecha_aviso"] == "2026-01-01"
    assert data["fecha_siniestro"] == "2026-01-15"


@pytest.mark.asyncio
async def test_crear_siniestro_autocompleta_identificacion_desde_incapacidad(
    client, auditor_previsionales_headers, incapacidad_previsional
):
    resp = await client.post(
        ENDPOINT,
        headers=auditor_previsionales_headers,
        json={
            "numero_siniestro": "SIN-MANUAL-004",
            "incapacidad_id": str(incapacidad_previsional.id),
        },
    )

    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["identificacion"] == incapacidad_previsional.identificacion


@pytest.mark.asyncio
async def test_crear_siniestro_identificacion_inconsistente_con_incapacidad_400(
    client, auditor_previsionales_headers, incapacidad_previsional
):
    resp = await client.post(
        ENDPOINT,
        headers=auditor_previsionales_headers,
        json={
            "identificacion": "9999999999",
            "numero_siniestro": "SIN-MANUAL-005",
            "incapacidad_id": str(incapacidad_previsional.id),
        },
    )

    assert resp.status_code == 400, resp.text


@pytest.mark.asyncio
async def test_crear_siniestro_incapacidad_id_inexistente_404(
    client, auditor_previsionales_headers
):
    resp = await client.post(
        ENDPOINT,
        headers=auditor_previsionales_headers,
        json={
            "numero_siniestro": "SIN-MANUAL-006",
            "incapacidad_id": str(uuid4()),
        },
    )

    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_crear_siniestro_sin_identificacion_ni_incapacidad_id_400(
    client, auditor_previsionales_headers
):
    resp = await client.post(
        ENDPOINT,
        headers=auditor_previsionales_headers,
        json={"numero_siniestro": "SIN-MANUAL-007"},
    )

    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_crear_siniestro_numero_siniestro_duplicado_409(
    client, auditor_previsionales_headers
):
    payload = {
        "identificacion": "1000000013",
        "numero_siniestro": "SIN-MANUAL-DUP",
    }
    primera = await client.post(ENDPOINT, headers=auditor_previsionales_headers, json=payload)
    assert primera.status_code == 201, primera.text

    segunda = await client.post(
        ENDPOINT,
        headers=auditor_previsionales_headers,
        json={"identificacion": "1000000014", "numero_siniestro": "SIN-MANUAL-DUP"},
    )
    assert segunda.status_code == 409, segunda.text


@pytest.mark.asyncio
async def test_crear_siniestro_sin_token_401(client):
    resp = await client.post(
        ENDPOINT,
        json={"identificacion": "1000000015", "numero_siniestro": "SIN-MANUAL-008"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_crear_siniestro_sin_permiso_403(client, readonly_headers):
    resp = await client.post(
        ENDPOINT,
        headers=readonly_headers,
        json={"identificacion": "1000000016", "numero_siniestro": "SIN-MANUAL-009"},
    )
    assert resp.status_code == 403

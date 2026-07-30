"""
Tests para los endpoints REST del workflow de auditoría previsional
(Task 4.2): app/api/v1/endpoints/previsionales/auditoria.py.

Usa `client` (httpx AsyncClient contra la app real, `get_db` sobreescrito
con `db_session` -- ver tests/conftest.py) y siembra directamente
`LotePrevisional`/`IncapacidadPrevisional` vía el ORM (mismo patrón que
`test_auditoria_previsional_service.py`, Task 3.3) en vez de subir un excel
completo -- estos endpoints no re-parsean archivos, así que sembrar filas
directamente es más simple y estable.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
import pytest_asyncio

from app.core.security import create_access_token, get_password_hash
from app.models.previsionales.incapacidad_previsional import IncapacidadPrevisional
from app.models.previsionales.lote_previsional import LotePrevisional
from app.models.usuario import Usuario
from app.services.previsionales.auditoria_service import auditoria_previsional_service
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
        db_session, RolUsuario.AUDITOR_PREVISIONALES, "auditor_previsionales_aud_ep"
    )


@pytest_asyncio.fixture
async def auditor_previsionales_headers(auditor_previsionales) -> dict:
    return _headers_para(auditor_previsionales)


@pytest_asyncio.fixture
async def readonly_headers(db_session) -> dict:
    usuario = await _crear_usuario_con_rol(db_session, RolUsuario.READONLY, "readonly_aud_ep")
    return _headers_para(usuario)


@pytest_asyncio.fixture
async def incapacidad_previsional(db_session) -> IncapacidadPrevisional:
    """Una IncapacidadPrevisional aislada dentro de su propio lote, sin
    referencia externa -- suficiente para PATCH/aval/duplicar, que no
    dependen de siniestros/solicitudes."""
    lote = LotePrevisional(nombre_archivo="RADICADOS_AUDITORIA_EP.xlsx")
    db_session.add(lote)
    await db_session.flush()

    inc = IncapacidadPrevisional(
        lote_id=lote.id,
        identificacion="1000000001",
        fecha_inicial=date(2026, 1, 1),
        fecha_final=date(2026, 1, 20),
        tipo_ingreso="INICIAL",
        numero_siniestro="SIN-001",
        valor_afp=Decimal("500000"),
    )
    db_session.add(inc)
    await db_session.commit()
    await db_session.refresh(inc)
    return inc


@pytest_asyncio.fixture
async def incapacidad_auditada(db_session, incapacidad_previsional) -> IncapacidadPrevisional:
    """Corre `auditar_incapacidad` sobre la incapacidad sembrada para que
    tenga señales AB-AT persistidas (necesario para GET .../senales)."""
    await auditoria_previsional_service.auditar_incapacidad(db_session, incapacidad_previsional.id)
    return incapacidad_previsional


# ---------------------------------------------------------------------------
# GET /previsionales/incapacidades/{id}/senales
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_senales_devuelve_las_19_senales_persistidas(
    client, auditor_previsionales_headers, incapacidad_auditada
):
    resp = await client.get(
        f"/api/v1/previsionales/incapacidades/{incapacidad_auditada.id}/senales",
        headers=auditor_previsionales_headers,
    )

    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert len(data) == 19
    codigos = {s["codigo"] for s in data}
    assert "AB" in codigos
    assert "AC" in codigos
    for senal in data:
        assert senal["incapacidad_previsional_id"] == str(incapacidad_auditada.id)
        assert senal["estado"] in ("OK", "ALERTA", "PENDIENTE", "INFO")


@pytest.mark.asyncio
async def test_get_senales_incapacidad_inexistente_devuelve_404(
    client, auditor_previsionales_headers
):
    resp = await client.get(
        f"/api/v1/previsionales/incapacidades/{uuid4()}/senales",
        headers=auditor_previsionales_headers,
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_senales_sin_permiso_devuelve_403(
    client, readonly_headers, incapacidad_previsional
):
    resp = await client.get(
        f"/api/v1/previsionales/incapacidades/{incapacidad_previsional.id}/senales",
        headers=readonly_headers,
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_get_senales_sin_token_devuelve_401(client, incapacidad_previsional):
    resp = await client.get(
        f"/api/v1/previsionales/incapacidades/{incapacidad_previsional.id}/senales",
    )
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# PATCH /previsionales/incapacidades/{id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_patch_actualiza_dia_181_alfa(
    client, auditor_previsionales_headers, incapacidad_previsional
):
    resp = await client.patch(
        f"/api/v1/previsionales/incapacidades/{incapacidad_previsional.id}",
        headers=auditor_previsionales_headers,
        json={"dia_181_alfa": "2026-01-15"},
    )

    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["dia_181_alfa"] == "2026-01-15"
    assert data["id"] == str(incapacidad_previsional.id)


@pytest.mark.asyncio
async def test_patch_incapacidad_inexistente_devuelve_404(
    client, auditor_previsionales_headers
):
    resp = await client.patch(
        f"/api/v1/previsionales/incapacidades/{uuid4()}",
        headers=auditor_previsionales_headers,
        json={"dia_181_alfa": "2026-01-15"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_patch_sin_permiso_devuelve_403(
    client, readonly_headers, incapacidad_previsional
):
    resp = await client.patch(
        f"/api/v1/previsionales/incapacidades/{incapacidad_previsional.id}",
        headers=readonly_headers,
        json={"dia_181_alfa": "2026-01-15"},
    )
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# POST /previsionales/incapacidades/{id}/aval
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_post_aval_si_exitoso(
    client, auditor_previsionales_headers, auditor_previsionales, incapacidad_previsional
):
    resp = await client.post(
        f"/api/v1/previsionales/incapacidades/{incapacidad_previsional.id}/aval",
        headers=auditor_previsionales_headers,
        json={"aval": "SI"},
    )

    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["aval"] == "SI"
    assert data["estado"] == "AVALADO"


@pytest.mark.asyncio
async def test_post_aval_no_sin_motivo_devuelve_400(
    client, auditor_previsionales_headers, incapacidad_previsional
):
    resp = await client.post(
        f"/api/v1/previsionales/incapacidades/{incapacidad_previsional.id}/aval",
        headers=auditor_previsionales_headers,
        json={"aval": "NO"},
    )

    assert resp.status_code == 400, resp.text
    assert "motivo" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_post_aval_no_con_motivo_exitoso(
    client, auditor_previsionales_headers, incapacidad_previsional
):
    resp = await client.post(
        f"/api/v1/previsionales/incapacidades/{incapacidad_previsional.id}/aval",
        headers=auditor_previsionales_headers,
        json={"aval": "NO", "motivo": "Documentación incompleta"},
    )

    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["aval"] == "NO"
    assert data["motivo_no_aval"] == "Documentación incompleta"
    assert data["estado"] == "NO_AVALADO"


@pytest.mark.asyncio
async def test_post_aval_incapacidad_inexistente_devuelve_404(
    client, auditor_previsionales_headers
):
    resp = await client.post(
        f"/api/v1/previsionales/incapacidades/{uuid4()}/aval",
        headers=auditor_previsionales_headers,
        json={"aval": "SI"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_post_aval_sin_permiso_devuelve_403(
    client, readonly_headers, incapacidad_previsional
):
    resp = await client.post(
        f"/api/v1/previsionales/incapacidades/{incapacidad_previsional.id}/aval",
        headers=readonly_headers,
        json={"aval": "SI"},
    )
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# POST /previsionales/incapacidades/{id}/duplicar
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_post_duplicar_crea_nueva_fila_marcada_como_duplicado_interno(
    client, auditor_previsionales_headers, incapacidad_previsional
):
    resp = await client.post(
        f"/api/v1/previsionales/incapacidades/{incapacidad_previsional.id}/duplicar",
        headers=auditor_previsionales_headers,
        json={"fecha_inicial": "2026-02-01", "fecha_final": "2026-02-10"},
    )

    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["id"] != str(incapacidad_previsional.id)
    assert data["incapacidad_origen_id"] == str(incapacidad_previsional.id)
    assert data["es_duplicado_interno"] is True
    assert data["fecha_inicial"] == "2026-02-01"
    assert data["fecha_final"] == "2026-02-10"
    # Campos copiables heredados del origen (ver _CAMPOS_COPIABLES_EN_DUPLICADO)
    assert data["identificacion"] == incapacidad_previsional.identificacion


@pytest.mark.asyncio
async def test_post_duplicar_incapacidad_inexistente_devuelve_404(
    client, auditor_previsionales_headers
):
    resp = await client.post(
        f"/api/v1/previsionales/incapacidades/{uuid4()}/duplicar",
        headers=auditor_previsionales_headers,
        json={"fecha_inicial": "2026-02-01", "fecha_final": "2026-02-10"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_post_duplicar_sin_permiso_devuelve_403(
    client, readonly_headers, incapacidad_previsional
):
    resp = await client.post(
        f"/api/v1/previsionales/incapacidades/{incapacidad_previsional.id}/duplicar",
        headers=readonly_headers,
        json={"fecha_inicial": "2026-02-01", "fecha_final": "2026-02-10"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_post_duplicar_sin_token_devuelve_401(client, incapacidad_previsional):
    resp = await client.post(
        f"/api/v1/previsionales/incapacidades/{incapacidad_previsional.id}/duplicar",
        json={"fecha_inicial": "2026-02-01", "fecha_final": "2026-02-10"},
    )
    assert resp.status_code == 401

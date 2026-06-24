"""
TDD tests for Task 4.1: plantilla_auditoria table, service, and endpoints.

Tests:
1. Schema validation — canal_recepcion and required date/int fields
2. Schema computes linea_autorizacion automatically
3. Service create_or_update creates new plantilla
4. Service create_or_update updates existing plantilla (upsert)
5. Service get_by_incapacidad raises NotFoundException when not found
6. Endpoint POST creates plantilla (AUDITOR)
7. Endpoint GET retrieves plantilla (AUDITOR)
8. Endpoint GET texto-copiable returns formatted text (AUDITOR)
9. Non-AUDITOR/ADMIN role is rejected (403)
10. POST is idempotent — second call updates, not duplicates
"""
import pytest
from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

from app.core.exceptions import NotFoundException
from app.schemas.plantilla_auditoria import PlantillaAuditoriaCreate
from app.utils.enums import TipoIncapacidad, EstadoIncapacidad, Prioridad


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
async def incapacidad_en_auditoria_pa(db_session, test_empleado, test_empresa):
    """ARL incapacidad in EN_AUDITORIA state for plantilla tests."""
    from app.models.incapacidad import Incapacidad

    inc = Incapacidad(
        numero=f"INC-PA-{uuid4().hex[:6].upper()}",
        empleado_id=test_empleado.id,
        empresa_id=test_empresa.id,
        tipo=TipoIncapacidad.ARL,
        fecha_inicio=date(2026, 6, 1),
        fecha_fin=date(2026, 6, 10),
        dias_totales=10,
        diagnostico_cie10="M545",
        descripcion_diagnostico="Lumbago no especificado",
        valor_dia=Decimal("100000.00"),
        valor_total=Decimal("1000000.00"),
        estado=EstadoIncapacidad.EN_AUDITORIA,
        fecha_radicacion=datetime.utcnow(),
        prioridad=Prioridad.NORMAL,
    )
    db_session.add(inc)
    await db_session.commit()
    await db_session.refresh(inc)
    return inc


@pytest.fixture
async def auditor_token_headers(test_user_auditor) -> dict:
    """Create authentication headers for auditor user."""
    from app.core.security import create_access_token

    token = create_access_token(
        data={
            "sub": str(test_user_auditor.id),
            "token_version": test_user_auditor.token_version,
        }
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def readonly_user(db_session):
    """Create a READONLY user for auth guard tests."""
    from app.models.usuario import Usuario
    from app.utils.enums import RolUsuario, EstadoUsuario
    from app.core.security import get_password_hash

    usuario = Usuario(
        username=f"readonly_{uuid4().hex[:6]}",
        email=f"readonly_{uuid4().hex[:6]}@example.com",
        password_hash=get_password_hash("Readonly123!"),
        nombre_completo="Usuario Solo Lectura",
        rol=RolUsuario.READONLY,
        estado=EstadoUsuario.ACTIVO,
    )
    db_session.add(usuario)
    await db_session.commit()
    await db_session.refresh(usuario)
    return usuario


@pytest.fixture
async def readonly_token_headers(readonly_user) -> dict:
    """Create authentication headers for readonly user."""
    from app.core.security import create_access_token

    token = create_access_token(
        data={
            "sub": str(readonly_user.id),
            "token_version": readonly_user.token_version,
        }
    )
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Unit tests: Schema
# ---------------------------------------------------------------------------


def test_schema_requires_canal_recepcion():
    """PlantillaAuditoriaCreate must raise when required fields are missing."""
    with pytest.raises(Exception):
        PlantillaAuditoriaCreate()  # type: ignore[call-arg]


def test_schema_requires_dias_autorizados():
    """dias_autorizados must be > 0."""
    with pytest.raises(Exception):
        PlantillaAuditoriaCreate(
            canal_recepcion="Portal",
            dias_autorizados=0,  # Invalid
            fecha_inicio_autorizada=date(2026, 6, 1),
            fecha_fin_autorizada=date(2026, 6, 10),
        )


def test_schema_computes_linea_autorizacion():
    """Schema must auto-compute linea_autorizacion after validation."""
    schema = PlantillaAuditoriaCreate(
        canal_recepcion="Portal",
        dias_autorizados=10,
        fecha_inicio_autorizada=date(2026, 6, 1),
        fecha_fin_autorizada=date(2026, 6, 10),
    )
    assert schema.linea_autorizacion is not None
    assert "Se autoriza pago por 10 días" in schema.linea_autorizacion
    assert "2026-06-01" in schema.linea_autorizacion
    assert "2026-06-10" in schema.linea_autorizacion


def test_schema_allows_optional_fields():
    """Optional fields can be omitted."""
    schema = PlantillaAuditoriaCreate(
        canal_recepcion="Onbase",
        dias_autorizados=5,
        fecha_inicio_autorizada=date(2026, 7, 1),
        fecha_fin_autorizada=date(2026, 7, 5),
    )
    assert schema.nombre_ips is None
    assert schema.diagnostico_cie10 is None
    assert schema.nombre_medico is None


# ---------------------------------------------------------------------------
# Service tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_service_create_plantilla(
    db_session, incapacidad_en_auditoria_pa, test_user_auditor
):
    """create_or_update must create a new PlantillaAuditoria."""
    from app.services.plantilla_auditoria_service import plantilla_auditoria_service

    data = PlantillaAuditoriaCreate(
        canal_recepcion="Portal",
        dias_autorizados=10,
        fecha_inicio_autorizada=date(2026, 6, 1),
        fecha_fin_autorizada=date(2026, 6, 10),
        diagnostico_cie10="M545",
        nombre_medico="Dr. Juan López",
    )

    plantilla = await plantilla_auditoria_service.create_or_update(
        db=db_session,
        incapacidad_id=incapacidad_en_auditoria_pa.id,
        data=data,
        usuario_id=test_user_auditor.id,
    )

    assert plantilla.incapacidad_id == incapacidad_en_auditoria_pa.id
    assert plantilla.canal_recepcion == "Portal"
    assert plantilla.dias_autorizados == 10
    assert plantilla.auditado_por_id == test_user_auditor.id
    assert "Se autoriza pago por 10 días" in plantilla.linea_autorizacion


@pytest.mark.asyncio
async def test_service_update_plantilla_is_idempotent(
    db_session, incapacidad_en_auditoria_pa, test_user_auditor
):
    """create_or_update called twice must update, not create a duplicate."""
    from app.services.plantilla_auditoria_service import plantilla_auditoria_service
    from app.db.repositories.plantilla_auditoria_repository import plantilla_auditoria_repository

    data_v1 = PlantillaAuditoriaCreate(
        canal_recepcion="Portal",
        dias_autorizados=10,
        fecha_inicio_autorizada=date(2026, 6, 1),
        fecha_fin_autorizada=date(2026, 6, 10),
    )

    p1 = await plantilla_auditoria_service.create_or_update(
        db=db_session,
        incapacidad_id=incapacidad_en_auditoria_pa.id,
        data=data_v1,
        usuario_id=test_user_auditor.id,
    )

    data_v2 = PlantillaAuditoriaCreate(
        canal_recepcion="Imaginex",  # updated
        dias_autorizados=15,          # updated
        fecha_inicio_autorizada=date(2026, 6, 1),
        fecha_fin_autorizada=date(2026, 6, 15),
    )

    p2 = await plantilla_auditoria_service.create_or_update(
        db=db_session,
        incapacidad_id=incapacidad_en_auditoria_pa.id,
        data=data_v2,
        usuario_id=test_user_auditor.id,
    )

    # Same ID → updated, not duplicated
    assert p1.id == p2.id
    assert p2.canal_recepcion == "Imaginex"
    assert p2.dias_autorizados == 15


@pytest.mark.asyncio
async def test_service_get_raises_not_found_when_missing(
    db_session, incapacidad_en_auditoria_pa
):
    """get_by_incapacidad must raise NotFoundException when no plantilla exists."""
    from app.services.plantilla_auditoria_service import plantilla_auditoria_service

    with pytest.raises(NotFoundException):
        await plantilla_auditoria_service.get_by_incapacidad(
            db=db_session,
            incapacidad_id=incapacidad_en_auditoria_pa.id,
        )


@pytest.mark.asyncio
async def test_service_get_raises_not_found_for_unknown_incapacidad(db_session):
    """get_by_incapacidad must raise NotFoundException for unknown incapacidad_id."""
    from app.services.plantilla_auditoria_service import plantilla_auditoria_service

    with pytest.raises(NotFoundException):
        await plantilla_auditoria_service.get_by_incapacidad(
            db=db_session,
            incapacidad_id=uuid4(),
        )


# ---------------------------------------------------------------------------
# Endpoint tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_endpoint_post_creates_plantilla(
    client, incapacidad_en_auditoria_pa, auditor_token_headers
):
    """POST endpoint must create plantilla and return 200 with linea_autorizacion."""
    resp = await client.post(
        f"/api/v1/incapacidades/{incapacidad_en_auditoria_pa.id}/plantilla-auditoria",
        json={
            "canal_recepcion": "Portal",
            "dias_autorizados": 10,
            "fecha_inicio_autorizada": "2026-06-01",
            "fecha_fin_autorizada": "2026-06-10",
        },
        headers=auditor_token_headers,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["incapacidad_id"] == str(incapacidad_en_auditoria_pa.id)
    assert data["canal_recepcion"] == "Portal"
    assert data["dias_autorizados"] == 10
    assert "Se autoriza pago por 10 días" in data["linea_autorizacion"]


@pytest.mark.asyncio
async def test_endpoint_post_is_idempotent(
    client, incapacidad_en_auditoria_pa, auditor_token_headers
):
    """Second POST must update and return the same ID."""
    url = f"/api/v1/incapacidades/{incapacidad_en_auditoria_pa.id}/plantilla-auditoria"

    r1 = await client.post(
        url,
        json={
            "canal_recepcion": "Portal",
            "dias_autorizados": 5,
            "fecha_inicio_autorizada": "2026-06-01",
            "fecha_fin_autorizada": "2026-06-05",
        },
        headers=auditor_token_headers,
    )
    assert r1.status_code == 200

    r2 = await client.post(
        url,
        json={
            "canal_recepcion": "Onbase",
            "dias_autorizados": 8,
            "fecha_inicio_autorizada": "2026-06-01",
            "fecha_fin_autorizada": "2026-06-08",
        },
        headers=auditor_token_headers,
    )
    assert r2.status_code == 200
    assert r1.json()["id"] == r2.json()["id"]
    assert r2.json()["canal_recepcion"] == "Onbase"


@pytest.mark.asyncio
async def test_endpoint_get_returns_plantilla(
    client, incapacidad_en_auditoria_pa, auditor_token_headers
):
    """GET endpoint must return the previously created plantilla."""
    url = f"/api/v1/incapacidades/{incapacidad_en_auditoria_pa.id}/plantilla-auditoria"

    # Create first
    await client.post(
        url,
        json={
            "canal_recepcion": "Portal",
            "dias_autorizados": 10,
            "fecha_inicio_autorizada": "2026-06-01",
            "fecha_fin_autorizada": "2026-06-10",
        },
        headers=auditor_token_headers,
    )

    # Then GET
    resp = await client.get(url, headers=auditor_token_headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["canal_recepcion"] == "Portal"
    assert data["dias_autorizados"] == 10


@pytest.mark.asyncio
async def test_endpoint_get_returns_404_when_no_plantilla(
    client, incapacidad_en_auditoria_pa, auditor_token_headers
):
    """GET endpoint must return 404 when no plantilla exists."""
    resp = await client.get(
        f"/api/v1/incapacidades/{incapacidad_en_auditoria_pa.id}/plantilla-auditoria",
        headers=auditor_token_headers,
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_endpoint_texto_copiable(
    client, incapacidad_en_auditoria_pa, auditor_token_headers
):
    """GET texto-copiable must return {'texto': '...'} with formatted string."""
    url = f"/api/v1/incapacidades/{incapacidad_en_auditoria_pa.id}/plantilla-auditoria"

    await client.post(
        url,
        json={
            "canal_recepcion": "Portal",
            "dias_autorizados": 10,
            "fecha_inicio_autorizada": "2026-06-01",
            "fecha_fin_autorizada": "2026-06-10",
            "diagnostico_cie10": "M545",
            "descripcion_cie10": "Lumbago no especificado",
            "nombre_medico": "Dr. García",
            "especialidad_medico": "Medicina general",
            "nombre_ips": "Clínica Norte",
        },
        headers=auditor_token_headers,
    )

    resp = await client.get(
        f"{url}/texto-copiable",
        headers=auditor_token_headers,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "texto" in data
    assert "Se autoriza pago por 10 días" in data["texto"]
    assert "CIE-10: M545" in data["texto"]
    assert "Dr. García" in data["texto"]


@pytest.mark.asyncio
async def test_endpoint_auth_guard_readonly_role(
    client, incapacidad_en_auditoria_pa, readonly_token_headers
):
    """READONLY role must receive 403 on POST endpoint."""
    resp = await client.post(
        f"/api/v1/incapacidades/{incapacidad_en_auditoria_pa.id}/plantilla-auditoria",
        json={
            "canal_recepcion": "Portal",
            "dias_autorizados": 5,
            "fecha_inicio_autorizada": "2026-06-01",
            "fecha_fin_autorizada": "2026-06-05",
        },
        headers=readonly_token_headers,
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_endpoint_auth_guard_get_readonly_role(
    client, incapacidad_en_auditoria_pa, readonly_token_headers
):
    """READONLY role must receive 403 on GET endpoint."""
    resp = await client.get(
        f"/api/v1/incapacidades/{incapacidad_en_auditoria_pa.id}/plantilla-auditoria",
        headers=readonly_token_headers,
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_endpoint_auth_guard_no_token(client, incapacidad_en_auditoria_pa):
    """Missing token must receive 401."""
    resp = await client.get(
        f"/api/v1/incapacidades/{incapacidad_en_auditoria_pa.id}/plantilla-auditoria"
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_endpoint_admin_can_access(
    client, incapacidad_en_auditoria_pa, admin_token_headers
):
    """ADMIN role must be able to create and read plantilla."""
    url = f"/api/v1/incapacidades/{incapacidad_en_auditoria_pa.id}/plantilla-auditoria"

    resp = await client.post(
        url,
        json={
            "canal_recepcion": "Imaginex",
            "dias_autorizados": 7,
            "fecha_inicio_autorizada": "2026-06-01",
            "fecha_fin_autorizada": "2026-06-07",
        },
        headers=admin_token_headers,
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["canal_recepcion"] == "Imaginex"

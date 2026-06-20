"""
Tests for GET /incapacidades/mi-empresa — company-scoped listing endpoint.
"""
import datetime as dt
import pytest
import pytest_asyncio
from httpx import AsyncClient
from app.models.empresa import Empresa
from app.models.empleado import Empleado
from app.models.incapacidad import Incapacidad
from app.utils.enums import TipoIncapacidad, EstadoIncapacidad


@pytest_asyncio.fixture
async def incapacidad_de_mi_empresa(db_session, test_empleado, test_empresa):
    inc = Incapacidad(
        numero="ARL-MIEMP-0001", tipo=TipoIncapacidad.ARL,
        empleado_id=test_empleado.id, empresa_id=test_empresa.id,
        fecha_inicio=dt.date(2026, 6, 1), fecha_fin=dt.date(2026, 6, 5), dias_totales=5,
        diagnostico_cie10="S00.0", nombre_medico="Dr X", registro_medico="RM-1",
        estado=EstadoIncapacidad.RADICADA, fecha_radicacion=dt.datetime.utcnow(),
    )
    db_session.add(inc)
    await db_session.commit()
    await db_session.refresh(inc)
    return inc


@pytest_asyncio.fixture
async def incapacidad_de_otra_empresa(db_session):
    otra = Empresa(nit="999000111", razon_social="Otra SA", email_contacto="o@o.com", estado="ACTIVA")
    db_session.add(otra)
    await db_session.flush()
    emp = Empleado(empresa_id=otra.id, numero_documento="999999", tipo_documento="CC",
                   nombres="Otro", apellidos="Empleado", fecha_ingreso=dt.date(2020, 1, 1), estado="ACTIVO")
    db_session.add(emp)
    await db_session.flush()
    inc = Incapacidad(
        numero="ARL-OTRA-0001", tipo=TipoIncapacidad.ARL,
        empleado_id=emp.id, empresa_id=otra.id,
        fecha_inicio=dt.date(2026, 6, 1), fecha_fin=dt.date(2026, 6, 5), dias_totales=5,
        diagnostico_cie10="S00.0", nombre_medico="Dr Y", registro_medico="RM-2",
        estado=EstadoIncapacidad.RADICADA, fecha_radicacion=dt.datetime.utcnow(),
    )
    db_session.add(inc)
    await db_session.commit()
    await db_session.refresh(inc)
    return inc


@pytest.mark.asyncio
async def test_mi_empresa_only_returns_own_records(client: AsyncClient, empresa_user_token,
                                                    incapacidad_de_mi_empresa, incapacidad_de_otra_empresa):
    resp = await client.get("/api/v1/incapacidades/mi-empresa",
                            headers={"Authorization": f"Bearer {empresa_user_token}"})
    assert resp.status_code == 200, resp.text
    numeros = {item["numero"] for item in resp.json()}
    assert incapacidad_de_mi_empresa.numero in numeros
    assert incapacidad_de_otra_empresa.numero not in numeros


@pytest.mark.asyncio
async def test_mi_empresa_filters_by_estado(client: AsyncClient, empresa_user_token, incapacidad_de_mi_empresa):
    resp = await client.get("/api/v1/incapacidades/mi-empresa", params={"estado": "RADICADA"},
                            headers={"Authorization": f"Bearer {empresa_user_token}"})
    assert resp.status_code == 200, resp.text
    assert all(i["estado"] == "RADICADA" for i in resp.json())

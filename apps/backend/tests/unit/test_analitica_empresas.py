"""GET /empresas/analitica: top-10 ranking + 12-month trend, both server-aggregated."""
from datetime import datetime, timedelta

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_analitica_top_empresas_ordered_desc_capped_at_10(
    client: AsyncClient, db_session, admin_token_headers
):
    from app.models.empresa import Empresa
    from app.models.incapacidad import Incapacidad
    from app.utils.enums import EstadoEmpresa, TipoIncapacidad, EstadoIncapacidad, Prioridad
    from decimal import Decimal

    empresas = []
    for i in range(3):
        empresa = Empresa(
            nit=f"90010000{i}",
            razon_social=f"Empresa Analitica {i}",
            email_contacto=f"analitica{i}@empresa.com",
            estado=EstadoEmpresa.ACTIVA,
        )
        db_session.add(empresa)
        empresas.append(empresa)
    await db_session.commit()
    for e in empresas:
        await db_session.refresh(e)

    # empresas[0] gets 3 incapacidades, empresas[1] gets 1, empresas[2] gets 0.
    counts = [3, 1, 0]
    numero = 0
    for empresa, count in zip(empresas, counts):
        for _ in range(count):
            numero += 1
            db_session.add(Incapacidad(
                numero=f"INC-ANALITICA-{numero}",
                empresa_id=empresa.id,
                tipo=TipoIncapacidad.ARL,
                fecha_inicio=datetime.utcnow().date(),
                fecha_fin=datetime.utcnow().date(),
                dias_totales=1,
                diagnostico_cie10="M545",
                descripcion_diagnostico="Test",
                valor_dia=Decimal("100000"),
                valor_total=Decimal("100000"),
                estado=EstadoIncapacidad.RADICADA,
                fecha_radicacion=datetime.utcnow(),
                prioridad=Prioridad.NORMAL,
            ))
    await db_session.commit()

    resp = await client.get("/api/v1/empresas/analitica", headers=admin_token_headers)
    assert resp.status_code == 200
    body = resp.json()

    top = body["top_empresas"]
    assert len(top) <= 10
    assert top[0]["nit"] == "900100000"
    assert top[0]["total_radicadas"] == 3
    assert top[1]["nit"] == "900100001"
    assert top[1]["total_radicadas"] == 1


@pytest.mark.asyncio
async def test_analitica_tendencia_mensual_has_12_zero_filled_months(
    client: AsyncClient, admin_token_headers
):
    resp = await client.get("/api/v1/empresas/analitica", headers=admin_token_headers)
    assert resp.status_code == 200
    tendencia = resp.json()["tendencia_mensual"]
    assert len(tendencia) == 12
    for item in tendencia:
        assert "periodo" in item and "total" in item

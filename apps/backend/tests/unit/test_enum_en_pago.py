from datetime import date, datetime
from uuid import uuid4

import pytest

from app.utils.enums import EstadoIncapacidad, TipoIncapacidad, Prioridad, EstadoAfiliado


def test_en_pago_states_exist():
    assert EstadoIncapacidad.EN_PAGO == "EN_PAGO"
    assert EstadoIncapacidad.EN_PAGO_PARCIAL == "EN_PAGO_PARCIAL"


@pytest.mark.parametrize(
    "estado",
    [EstadoIncapacidad.EN_PAGO, EstadoIncapacidad.EN_PAGO_PARCIAL],
)
@pytest.mark.asyncio
async def test_en_pago_states_round_trip_to_db(db_session, estado):
    """Regression test for Task 1.1 review finding #1: the test-DB
    `estadoincapacidad` enum type (bootstrapped by hand in conftest.py,
    bypassing Alembic) must include EN_PAGO/EN_PAGO_PARCIAL or writes with
    these states fail with 'invalid input value for enum estadoincapacidad'.
    """
    from app.models.incapacidad import Incapacidad
    from app.models.afiliado import Afiliado

    afiliado = Afiliado(
        numero_poliza=f"POL-{uuid4().hex[:6]}",
        tipo_poliza="INDIVIDUAL",
        numero_documento=f"DOC{uuid4().hex[:6]}",
        tipo_documento="CC",
        nombres="María",
        apellidos="Test",
        fecha_inicio_poliza=date(2024, 1, 1),
        estado=EstadoAfiliado.ACTIVO,
    )
    db_session.add(afiliado)
    await db_session.flush()

    inc = Incapacidad(
        numero=f"INC-TEST-{uuid4().hex[:8]}",
        tipo=TipoIncapacidad.SALUD,
        estado=estado,
        prioridad=Prioridad.NORMAL,
        fecha_inicio=date(2026, 1, 1),
        fecha_fin=date(2026, 1, 10),
        dias_totales=10,
        diagnostico_cie10="M545",
        descripcion_diagnostico="Lumbago no especificado",
        nombre_medico="Dr. García",
        registro_medico="RM12345",
        fecha_radicacion=datetime.utcnow(),
        afiliado_id=afiliado.id,
    )
    db_session.add(inc)
    await db_session.commit()
    await db_session.refresh(inc)

    assert inc.estado == estado

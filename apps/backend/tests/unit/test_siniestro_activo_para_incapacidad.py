import pytest
from datetime import date
from app.db.repositories.siniestro_repository import siniestro_repository
from app.models.siniestro import Siniestro
from app.utils.enums import TipoSiniestro, GravedadSiniestro, EstadoSiniestro


def _make_siniestro(empleado_id, empresa_id, numero, fecha_siniestro, estado):
    return Siniestro(
        numero_siniestro=numero,
        empleado_id=empleado_id,
        empresa_id=empresa_id,
        fecha_siniestro=fecha_siniestro,
        tipo_siniestro=TipoSiniestro.ACCIDENTE_TRABAJO,
        descripcion="Caída en escalera",
        gravedad=GravedadSiniestro.LEVE,
        estado=estado,
    )


@pytest.mark.asyncio
async def test_returns_none_when_no_siniestro(db_session, test_empleado):
    result = await siniestro_repository.get_activo_para_incapacidad(
        db_session, test_empleado.id, date(2026, 6, 1)
    )
    assert result is None


@pytest.mark.asyncio
async def test_excludes_siniestro_after_fecha_inicio(db_session, test_empleado, test_empresa):
    sin = _make_siniestro(
        test_empleado.id, test_empresa.id, "SIN-FUT-001",
        date(2026, 6, 10), EstadoSiniestro.REPORTADO,
    )
    db_session.add(sin)
    await db_session.commit()

    result = await siniestro_repository.get_activo_para_incapacidad(
        db_session, test_empleado.id, date(2026, 6, 1)
    )
    assert result is None


@pytest.mark.asyncio
async def test_excludes_cerrado_and_anulado(db_session, test_empleado, test_empresa):
    for numero, estado in [("SIN-CER-001", EstadoSiniestro.CERRADO), ("SIN-ANU-001", EstadoSiniestro.ANULADO)]:
        db_session.add(_make_siniestro(test_empleado.id, test_empresa.id, numero, date(2026, 5, 1), estado))
    await db_session.commit()

    result = await siniestro_repository.get_activo_para_incapacidad(
        db_session, test_empleado.id, date(2026, 6, 1)
    )
    assert result is None


@pytest.mark.asyncio
async def test_picks_most_recent_qualifying_siniestro(db_session, test_empleado, test_empresa):
    older = _make_siniestro(test_empleado.id, test_empresa.id, "SIN-OLD-001", date(2026, 1, 1), EstadoSiniestro.REPORTADO)
    newer = _make_siniestro(test_empleado.id, test_empresa.id, "SIN-NEW-001", date(2026, 5, 20), EstadoSiniestro.EN_INVESTIGACION)
    db_session.add_all([older, newer])
    await db_session.commit()

    result = await siniestro_repository.get_activo_para_incapacidad(
        db_session, test_empleado.id, date(2026, 6, 1)
    )
    assert result is not None
    assert result.numero_siniestro == "SIN-NEW-001"


@pytest.mark.asyncio
async def test_includes_siniestro_on_same_day_as_fecha_inicio(db_session, test_empleado, test_empresa):
    sin = _make_siniestro(test_empleado.id, test_empresa.id, "SIN-SAME-001", date(2026, 6, 1), EstadoSiniestro.REPORTADO)
    db_session.add(sin)
    await db_session.commit()

    result = await siniestro_repository.get_activo_para_incapacidad(
        db_session, test_empleado.id, date(2026, 6, 1)
    )
    assert result is not None
    assert result.numero_siniestro == "SIN-SAME-001"

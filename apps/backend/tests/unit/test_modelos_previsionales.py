"""
Tests para los 8 modelos previsionales (Task 2.1).

Verifica:
- Se puede crear un lote con 2 incapacidades y 3 periodos.
- Cascade delete: borrar el lote borra sus incapacidades y, en cadena, los
  periodos de esas incapacidades.
- Cascade delete: borrar una incapacidad borra sus propios periodos.
- El CheckConstraint de `aval` rechaza valores fuera de ('SI', 'NO').
"""
from datetime import date

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models.previsionales.incapacidad_previsional import IncapacidadPrevisional
from app.models.previsionales.lote_previsional import LotePrevisional
from app.models.previsionales.periodo_previsional import PeriodoPrevisional


@pytest_asyncio.fixture
async def lote_con_incapacidades_y_periodos(db_session):
    """Crea 1 lote -> 2 incapacidades -> 3 periodos (2 en la primera, 1 en la segunda)."""
    lote = LotePrevisional(nombre_archivo="RADICADOS_AUDITORIA_20260706.xlsx")
    db_session.add(lote)
    await db_session.flush()

    inc1 = IncapacidadPrevisional(lote_id=lote.id, identificacion="4661182", fecha_inicial=date(2026, 7, 11))
    inc2 = IncapacidadPrevisional(lote_id=lote.id, identificacion="23333262", fecha_inicial=date(2026, 7, 11))
    db_session.add_all([inc1, inc2])
    await db_session.flush()

    per1 = PeriodoPrevisional(
        incapacidad_id=inc1.id, orden=1,
        fecha_inicio=date(2026, 7, 11), fecha_fin=date(2026, 7, 31), dias=21,
    )
    per2 = PeriodoPrevisional(
        incapacidad_id=inc1.id, orden=2,
        fecha_inicio=date(2026, 8, 1), fecha_fin=date(2026, 8, 10), dias=10,
    )
    per3 = PeriodoPrevisional(
        incapacidad_id=inc2.id, orden=1,
        fecha_inicio=date(2026, 7, 11), fecha_fin=date(2026, 7, 20), dias=10,
    )
    db_session.add_all([per1, per2, per3])
    await db_session.commit()

    return lote, [inc1, inc2], [per1, per2, per3]


@pytest.mark.asyncio
async def test_crea_lote_con_incapacidades_y_periodos(db_session, lote_con_incapacidades_y_periodos):
    lote, incapacidades, periodos = lote_con_incapacidades_y_periodos

    assert lote.id is not None
    assert len(incapacidades) == 2
    assert len(periodos) == 3

    total_periodos = await db_session.execute(
        select(PeriodoPrevisional).where(
            PeriodoPrevisional.incapacidad_id.in_([i.id for i in incapacidades])
        )
    )
    assert len(total_periodos.scalars().all()) == 3


@pytest.mark.asyncio
async def test_borrar_lote_hace_cascade_a_incapacidades_y_periodos(db_session, lote_con_incapacidades_y_periodos):
    lote, incapacidades, periodos = lote_con_incapacidades_y_periodos
    incapacidad_ids = [i.id for i in incapacidades]
    periodo_ids = [p.id for p in periodos]

    await db_session.delete(lote)
    await db_session.commit()

    result_inc = await db_session.execute(
        select(IncapacidadPrevisional).where(IncapacidadPrevisional.id.in_(incapacidad_ids))
    )
    assert result_inc.scalars().all() == []

    result_per = await db_session.execute(
        select(PeriodoPrevisional).where(PeriodoPrevisional.id.in_(periodo_ids))
    )
    assert result_per.scalars().all() == []


@pytest.mark.asyncio
async def test_borrar_incapacidad_hace_cascade_a_sus_periodos(db_session, lote_con_incapacidades_y_periodos):
    lote, incapacidades, periodos = lote_con_incapacidades_y_periodos
    inc1, inc2 = incapacidades
    periodos_inc1_ids = [p.id for p in periodos if p.incapacidad_id == inc1.id]
    periodos_inc2_ids = [p.id for p in periodos if p.incapacidad_id == inc2.id]

    await db_session.delete(inc1)
    await db_session.commit()

    result_per_inc1 = await db_session.execute(
        select(PeriodoPrevisional).where(PeriodoPrevisional.id.in_(periodos_inc1_ids))
    )
    assert result_per_inc1.scalars().all() == []

    # Los periodos de la otra incapacidad (no borrada) siguen intactos.
    result_per_inc2 = await db_session.execute(
        select(PeriodoPrevisional).where(PeriodoPrevisional.id.in_(periodos_inc2_ids))
    )
    assert len(result_per_inc2.scalars().all()) == 1

    # La incapacidad hermana sigue existiendo.
    result_inc2 = await db_session.execute(
        select(IncapacidadPrevisional).where(IncapacidadPrevisional.id == inc2.id)
    )
    assert result_inc2.scalar_one_or_none() is not None


@pytest.mark.asyncio
async def test_aval_invalido_lanza_integrity_error(db_session):
    lote = LotePrevisional(nombre_archivo="test.xlsx")
    db_session.add(lote)
    await db_session.flush()

    inc = IncapacidadPrevisional(lote_id=lote.id, identificacion="12345", aval="X")
    db_session.add(inc)

    with pytest.raises(IntegrityError):
        await db_session.commit()

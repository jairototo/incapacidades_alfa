"""
Tests para `liquidacion_service.py` (Task 3.4, primera mitad) -- la capa de
persistencia de la liquidación previsional.

Usa `db_session` (Postgres async real, no mocks) siguiendo el mismo patrón
que `test_lote_service.py`/`test_repositorios_previsionales.py`. Los años
usados en las fechas de prueba (2026) deben tener SMLMV sembrado, porque los
tests unit usan `create_all` (no migraciones) y la tabla `smlmv_parametros`
arranca vacía.
"""
from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import select

from app.core.exceptions import BadRequestException, NotFoundException
from app.db.repositories.previsionales import periodo_previsional_repository
from app.models.previsionales.incapacidad_previsional import IncapacidadPrevisional
from app.models.previsionales.lote_previsional import LotePrevisional
from app.models.previsionales.periodo_previsional import PeriodoPrevisional
from app.models.previsionales.smlmv_parametros import SmlmvParametros
from app.services.previsionales.liquidacion_previsional import calcular_valor
from app.services.previsionales.liquidacion_service import liquidacion_previsional_service
from app.services.previsionales.segmentacion import Segmento

SMLMV_2026 = Decimal("1750905.00")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def smlmv_2026(db_session):
    smlmv = SmlmvParametros(ano=2026, valor=SMLMV_2026, vigente_desde=date(2026, 1, 1))
    db_session.add(smlmv)
    await db_session.commit()
    return smlmv


@pytest_asyncio.fixture
async def lote_con_periodos(db_session, smlmv_2026):
    """
    Un lote con dos incapacidades:
      - `inc_normal`: 1 segmento, IBC alto (no aplica piso), sin es_duplicado_interno.
      - `inc_duplicada`: es_duplicado_interno=True -- debe quedar EXCLUIDA de `liquidar_lote`.
    Ambas con sus `PeriodoPrevisional` ya persistidos con valores DELIBERADAMENTE
    obsoletos/incorrectos (simulando una carga vieja), para verificar que
    `liquidar_incapacidad`/`liquidar_lote` los RECALCULAN de verdad.
    """
    lote = LotePrevisional(nombre_archivo="RADICADOS_TEST_LIQUIDACION.xlsx")
    db_session.add(lote)
    await db_session.flush()

    inc_normal = IncapacidadPrevisional(
        lote_id=lote.id,
        identificacion="1000000001",
        fecha_inicial=date(2026, 3, 1),
        fecha_final=date(2026, 3, 15),
        valor_afp=Decimal("500000.00"),
        es_duplicado_interno=False,
    )
    inc_duplicada = IncapacidadPrevisional(
        lote_id=lote.id,
        identificacion="1000000002",
        fecha_inicial=date(2026, 3, 1),
        fecha_final=date(2026, 3, 10),
        valor_afp=Decimal("100000.00"),
        es_duplicado_interno=True,
    )
    db_session.add_all([inc_normal, inc_duplicada])
    await db_session.flush()

    # 15 dias, IBC alto -> 50% del IBC supera el piso SMLMV.
    periodo_normal = PeriodoPrevisional(
        incapacidad_id=inc_normal.id,
        orden=1,
        fecha_inicio=date(2026, 3, 1),
        fecha_fin=date(2026, 3, 15),
        dias=15,
        ibc=Decimal("3000000.00"),
        salario=Decimal("3000000.00"),
        dias_cotizados=15,
        # Valores obsoletos/incorrectos a propósito -- deben ser sobreescritos.
        smlmv_aplicado=Decimal("1.00"),
        base_diaria=Decimal("1.00"),
        valor_segmento=Decimal("1.00"),
    )
    periodo_duplicada = PeriodoPrevisional(
        incapacidad_id=inc_duplicada.id,
        orden=1,
        fecha_inicio=date(2026, 3, 1),
        fecha_fin=date(2026, 3, 10),
        dias=10,
        ibc=Decimal("1000000.00"),
        salario=Decimal("1000000.00"),
        dias_cotizados=10,
    )
    db_session.add_all([periodo_normal, periodo_duplicada])
    await db_session.commit()
    await db_session.refresh(inc_normal)
    await db_session.refresh(inc_duplicada)

    return {
        "lote": lote,
        "inc_normal": inc_normal,
        "inc_duplicada": inc_duplicada,
        "periodo_normal": periodo_normal,
    }


def _valor_esperado_inc_normal():
    """Replica exacta de lo que `calcular_valor` (Task 1.2) debe producir
    para el segmento de `inc_normal` -- la prueba de que el servicio no
    reinventa la fórmula, solo la conecta con la BD."""
    seg = Segmento(orden=1, fecha_inicio=date(2026, 3, 1), fecha_fin=date(2026, 3, 15), dias=15)
    total, detalle = calcular_valor([(seg, Decimal("3000000.00"))], {2026: SMLMV_2026})
    return total, detalle[0]


# ---------------------------------------------------------------------------
# liquidar_incapacidad
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_recalcula_valor_auditado_y_diferencia_matching_calcular_valor(
    db_session, lote_con_periodos
):
    inc_normal = lote_con_periodos["inc_normal"]
    valor_esperado, detalle_esperado = _valor_esperado_inc_normal()

    resultado = await liquidacion_previsional_service.liquidar_incapacidad(db_session, inc_normal.id)

    assert resultado.valor_auditado == valor_esperado
    assert resultado.diferencia_valor_afp == valor_esperado - Decimal("500000.00")

    periodos = await periodo_previsional_repository.get_by_incapacidad(db_session, inc_normal.id)
    assert len(periodos) == 1
    periodo = periodos[0]
    assert periodo.smlmv_aplicado == detalle_esperado.smlmv_aplicado
    assert periodo.valor_segmento == detalle_esperado.valor_segmento
    assert periodo.base_diaria == detalle_esperado.base_mensual / Decimal(30)


@pytest.mark.asyncio
async def test_liquidar_es_idempotente_re_ejecutar_no_duplica_periodos_ni_cambia_resultado(
    db_session, lote_con_periodos
):
    inc_normal = lote_con_periodos["inc_normal"]

    primero = await liquidacion_previsional_service.liquidar_incapacidad(db_session, inc_normal.id)
    segundo = await liquidacion_previsional_service.liquidar_incapacidad(db_session, inc_normal.id)

    assert primero.valor_auditado == segundo.valor_auditado
    assert primero.diferencia_valor_afp == segundo.diferencia_valor_afp

    periodos = await periodo_previsional_repository.get_by_incapacidad(db_session, inc_normal.id)
    assert len(periodos) == 1  # no se duplicó ni recreó la fila del periodo


@pytest.mark.asyncio
async def test_liquidar_usa_smlmv_vigente_no_el_valor_basura_de_la_carga(db_session, lote_con_periodos):
    """El fixture siembra el periodo con smlmv_aplicado=1.00 (basura) y la
    tabla SmlmvParametros con el valor real -- liquidar debe reemplazar la
    basura por el SMLMV vigente, no dejar el valor viejo."""
    inc_normal = lote_con_periodos["inc_normal"]
    _, detalle_esperado = _valor_esperado_inc_normal()

    await liquidacion_previsional_service.liquidar_incapacidad(db_session, inc_normal.id)

    periodos = await periodo_previsional_repository.get_by_incapacidad(db_session, inc_normal.id)
    assert periodos[0].smlmv_aplicado == SMLMV_2026
    assert periodos[0].smlmv_aplicado == detalle_esperado.smlmv_aplicado


@pytest.mark.asyncio
async def test_liquidar_incapacidad_inexistente_lanza_not_found(db_session, smlmv_2026):
    with pytest.raises(NotFoundException):
        await liquidacion_previsional_service.liquidar_incapacidad(db_session, uuid4())


@pytest.mark.asyncio
async def test_liquidar_incapacidad_sin_periodos_lanza_bad_request(db_session, smlmv_2026):
    lote = LotePrevisional(nombre_archivo="SIN_PERIODOS.xlsx")
    db_session.add(lote)
    await db_session.flush()
    inc = IncapacidadPrevisional(
        lote_id=lote.id,
        identificacion="9999999999",
        fecha_inicial=date(2026, 1, 1),
        fecha_final=date(2026, 1, 5),
    )
    db_session.add(inc)
    await db_session.commit()
    await db_session.refresh(inc)

    with pytest.raises(BadRequestException):
        await liquidacion_previsional_service.liquidar_incapacidad(db_session, inc.id)


@pytest.mark.asyncio
async def test_liquidar_incapacidad_sin_smlmv_del_ano_lanza_bad_request(db_session):
    """Sin fixture `smlmv_2026` -- la tabla smlmv_parametros esta vacia."""
    lote = LotePrevisional(nombre_archivo="SIN_SMLMV.xlsx")
    db_session.add(lote)
    await db_session.flush()
    inc = IncapacidadPrevisional(
        lote_id=lote.id,
        identificacion="8888888888",
        fecha_inicial=date(2026, 1, 1),
        fecha_final=date(2026, 1, 5),
    )
    db_session.add(inc)
    await db_session.flush()
    periodo = PeriodoPrevisional(
        incapacidad_id=inc.id,
        orden=1,
        fecha_inicio=date(2026, 1, 1),
        fecha_fin=date(2026, 1, 5),
        dias=5,
        ibc=Decimal("1000000.00"),
    )
    db_session.add(periodo)
    await db_session.commit()
    await db_session.refresh(inc)

    with pytest.raises(BadRequestException):
        await liquidacion_previsional_service.liquidar_incapacidad(db_session, inc.id)


# ---------------------------------------------------------------------------
# liquidar_lote
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_liquidar_lote_liquida_solo_no_duplicadas_y_retorna_conteo(db_session, lote_con_periodos):
    lote = lote_con_periodos["lote"]
    inc_normal = lote_con_periodos["inc_normal"]
    inc_duplicada = lote_con_periodos["inc_duplicada"]
    valor_esperado, _ = _valor_esperado_inc_normal()

    liquidadas = await liquidacion_previsional_service.liquidar_lote(db_session, lote.id)

    assert liquidadas == 1  # solo inc_normal -- inc_duplicada es es_duplicado_interno=True

    result = await db_session.execute(
        select(IncapacidadPrevisional).where(IncapacidadPrevisional.id == inc_normal.id)
    )
    inc_normal_actualizada = result.scalar_one()
    assert inc_normal_actualizada.valor_auditado == valor_esperado

    result = await db_session.execute(
        select(IncapacidadPrevisional).where(IncapacidadPrevisional.id == inc_duplicada.id)
    )
    inc_duplicada_actualizada = result.scalar_one()
    # La duplicada NUNCA se toca -- sigue sin valor_auditado.
    assert inc_duplicada_actualizada.valor_auditado is None


@pytest.mark.asyncio
async def test_liquidar_lote_vacio_retorna_cero(db_session, smlmv_2026):
    lote = LotePrevisional(nombre_archivo="LOTE_VACIO.xlsx")
    db_session.add(lote)
    await db_session.commit()
    await db_session.refresh(lote)

    liquidadas = await liquidacion_previsional_service.liquidar_lote(db_session, lote.id)
    assert liquidadas == 0


@pytest.mark.asyncio
async def test_liquidar_lote_omite_incapacidad_sin_periodos_sin_abortar_el_lote(
    db_session, lote_con_periodos
):
    """Una tercera incapacidad sin periodos no debe abortar la liquidacion
    de las demas -- mismo espiritu tolerante-por-fila que lote_service."""
    lote = lote_con_periodos["lote"]
    inc_sin_periodos = IncapacidadPrevisional(
        lote_id=lote.id,
        identificacion="7777777777",
        fecha_inicial=date(2026, 3, 1),
        fecha_final=date(2026, 3, 5),
        es_duplicado_interno=False,
    )
    db_session.add(inc_sin_periodos)
    await db_session.commit()

    liquidadas = await liquidacion_previsional_service.liquidar_lote(db_session, lote.id)

    # Solo inc_normal se liquida -- inc_duplicada excluida, inc_sin_periodos omitida.
    assert liquidadas == 1

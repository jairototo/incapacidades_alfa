"""
Tests para los repositorios previsionales (Task 2.2).

Cubre las consultas no triviales listadas en el brief:
- `get_by_lote` con cada filtro (sin_siniestro, repetidas, errores,
  dif_valor) aplicado individualmente.
- `get_previa_del_afiliado` (encadenamiento de prórrogas).
- `get_by_incapacidad` de periodos, ordenado por `orden`.
- `siniestro_previsional_repository.get_by_identificacion` devolviendo una
  LISTA ordenada (no colapsando a un solo valor) cuando hay múltiples
  siniestros para la misma identificación.
- `solicitud_previsional_repository.get_by_identificacion` con el mismo
  criterio de no-colapso.
- `exists_by_identificacion_fecha` de ITE histórico (True/False).
- Los métodos de carga masiva (`get_by_identificaciones`,
  `get_existentes`) resolviendo varias identificaciones en una sola
  llamada.
- `senal_auditoria_previsional_repository.bulk_create_flushed`.
"""
from datetime import date
from decimal import Decimal

import pytest
import pytest_asyncio

from app.db.repositories.previsionales import (
    ite_historico_repository,
    incapacidad_previsional_repository,
    lote_previsional_repository,
    periodo_previsional_repository,
    senal_auditoria_previsional_repository,
    siniestro_previsional_repository,
    solicitud_previsional_repository,
)
from app.models.previsionales.ite_historico import IteHistorico
from app.models.previsionales.incapacidad_previsional import IncapacidadPrevisional
from app.models.previsionales.lote_previsional import LotePrevisional
from app.models.previsionales.periodo_previsional import PeriodoPrevisional
from app.models.previsionales.siniestro_previsional import SiniestroPrevisional
from app.models.previsionales.solicitud_previsional import SolicitudPrevisional


# ---------------------------------------------------------------------------
# Fixtures de datos
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def lote_con_incapacidades(db_session):
    """Crea un lote con incapacidades cubriendo cada combinación de filtro."""
    lote = LotePrevisional(nombre_archivo="RADICADOS_TEST.xlsx")
    db_session.add(lote)
    await db_session.flush()

    # Sin siniestro, sin errores, sin diferencia de valor, no repetida.
    inc_limpia = IncapacidadPrevisional(
        lote_id=lote.id,
        identificacion="1000000001",
        fecha_inicial=date(2026, 1, 1),
        fecha_final=date(2026, 1, 10),
        numero_siniestro=None,
        errores_carga=None,
        diferencia_valor_afp=None,
        es_duplicado_interno=False,
    )
    # Con siniestro.
    inc_con_siniestro = IncapacidadPrevisional(
        lote_id=lote.id,
        identificacion="1000000002",
        fecha_inicial=date(2026, 1, 5),
        fecha_final=date(2026, 1, 15),
        numero_siniestro="SIN-001",
        errores_carga=None,
        diferencia_valor_afp=None,
        es_duplicado_interno=False,
    )
    # Repetida (duplicado interno).
    inc_repetida = IncapacidadPrevisional(
        lote_id=lote.id,
        identificacion="1000000003",
        fecha_inicial=date(2026, 1, 1),
        fecha_final=date(2026, 1, 10),
        numero_siniestro=None,
        errores_carga=None,
        diferencia_valor_afp=None,
        es_duplicado_interno=True,
    )
    # Con errores de carga.
    inc_con_errores = IncapacidadPrevisional(
        lote_id=lote.id,
        identificacion="1000000004",
        fecha_inicial=date(2026, 1, 1),
        fecha_final=date(2026, 1, 10),
        numero_siniestro=None,
        errores_carga={"columna_ibc": "valor no numérico"},
        diferencia_valor_afp=None,
        es_duplicado_interno=False,
    )
    # Con diferencia de valor AFP.
    inc_con_dif_valor = IncapacidadPrevisional(
        lote_id=lote.id,
        identificacion="1000000005",
        fecha_inicial=date(2026, 1, 1),
        fecha_final=date(2026, 1, 10),
        numero_siniestro=None,
        errores_carga=None,
        valor_afp=Decimal("100000.00"),
        valor_auditado=Decimal("120000.00"),
        diferencia_valor_afp=Decimal("20000.00"),
        es_duplicado_interno=False,
    )

    db_session.add_all(
        [inc_limpia, inc_con_siniestro, inc_repetida, inc_con_errores, inc_con_dif_valor]
    )
    await db_session.commit()

    return {
        "lote": lote,
        "limpia": inc_limpia,
        "con_siniestro": inc_con_siniestro,
        "repetida": inc_repetida,
        "con_errores": inc_con_errores,
        "con_dif_valor": inc_con_dif_valor,
    }


# ---------------------------------------------------------------------------
# get_by_lote + filtros
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_by_lote_sin_filtros_devuelve_todas(db_session, lote_con_incapacidades):
    lote_id = lote_con_incapacidades["lote"].id
    resultado = await incapacidad_previsional_repository.get_by_lote(db_session, lote_id)
    assert len(resultado) == 5


@pytest.mark.asyncio
async def test_get_by_lote_filtro_sin_siniestro(db_session, lote_con_incapacidades):
    lote_id = lote_con_incapacidades["lote"].id
    resultado = await incapacidad_previsional_repository.get_by_lote(
        db_session, lote_id, filtros={"sin_siniestro": True}
    )
    ids = {r.id for r in resultado}
    assert lote_con_incapacidades["con_siniestro"].id not in ids
    assert lote_con_incapacidades["limpia"].id in ids
    assert len(resultado) == 4


@pytest.mark.asyncio
async def test_get_by_lote_filtro_con_siniestro(db_session, lote_con_incapacidades):
    lote_id = lote_con_incapacidades["lote"].id
    resultado = await incapacidad_previsional_repository.get_by_lote(
        db_session, lote_id, filtros={"sin_siniestro": False}
    )
    assert len(resultado) == 1
    assert resultado[0].id == lote_con_incapacidades["con_siniestro"].id


@pytest.mark.asyncio
async def test_get_by_lote_filtro_repetidas(db_session, lote_con_incapacidades):
    lote_id = lote_con_incapacidades["lote"].id
    resultado = await incapacidad_previsional_repository.get_by_lote(
        db_session, lote_id, filtros={"repetidas": True}
    )
    assert len(resultado) == 1
    assert resultado[0].id == lote_con_incapacidades["repetida"].id


@pytest.mark.asyncio
async def test_get_by_lote_filtro_errores(db_session, lote_con_incapacidades):
    lote_id = lote_con_incapacidades["lote"].id
    resultado = await incapacidad_previsional_repository.get_by_lote(
        db_session, lote_id, filtros={"errores": True}
    )
    assert len(resultado) == 1
    assert resultado[0].id == lote_con_incapacidades["con_errores"].id


@pytest.mark.asyncio
async def test_get_by_lote_filtro_dif_valor(db_session, lote_con_incapacidades):
    lote_id = lote_con_incapacidades["lote"].id
    resultado = await incapacidad_previsional_repository.get_by_lote(
        db_session, lote_id, filtros={"dif_valor": True}
    )
    assert len(resultado) == 1
    assert resultado[0].id == lote_con_incapacidades["con_dif_valor"].id


@pytest.mark.asyncio
async def test_get_by_lote_combinando_filtros(db_session, lote_con_incapacidades):
    """sin_siniestro=True AND errores=False debe excluir con_siniestro y con_errores."""
    lote_id = lote_con_incapacidades["lote"].id
    resultado = await incapacidad_previsional_repository.get_by_lote(
        db_session, lote_id, filtros={"sin_siniestro": True, "errores": False}
    )
    ids = {r.id for r in resultado}
    assert lote_con_incapacidades["con_siniestro"].id not in ids
    assert lote_con_incapacidades["con_errores"].id not in ids
    assert lote_con_incapacidades["limpia"].id in ids


# ---------------------------------------------------------------------------
# get_previa_del_afiliado
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_previa_del_afiliado_encuentra_la_inmediatamente_anterior(
    db_session, lote_con_incapacidades
):
    lote_id = lote_con_incapacidades["lote"].id
    identificacion = "9000000001"

    previa_lejana = IncapacidadPrevisional(
        lote_id=lote_id,
        identificacion=identificacion,
        fecha_inicial=date(2025, 1, 1),
        fecha_final=date(2025, 1, 10),
    )
    previa_cercana = IncapacidadPrevisional(
        lote_id=lote_id,
        identificacion=identificacion,
        fecha_inicial=date(2025, 12, 1),
        fecha_final=date(2025, 12, 20),
    )
    posterior = IncapacidadPrevisional(
        lote_id=lote_id,
        identificacion=identificacion,
        fecha_inicial=date(2026, 2, 1),
        fecha_final=date(2026, 2, 10),
    )
    db_session.add_all([previa_lejana, previa_cercana, posterior])
    await db_session.commit()

    resultado = await incapacidad_previsional_repository.get_previa_del_afiliado(
        db_session, identificacion, fecha_inicial=date(2026, 1, 1)
    )

    assert resultado is not None
    assert resultado.id == previa_cercana.id


@pytest.mark.asyncio
async def test_get_previa_del_afiliado_sin_previas_devuelve_none(db_session):
    resultado = await incapacidad_previsional_repository.get_previa_del_afiliado(
        db_session, "9999999999", fecha_inicial=date(2026, 1, 1)
    )
    assert resultado is None


# ---------------------------------------------------------------------------
# periodo_previsional_repository.get_by_incapacidad
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_by_incapacidad_periodos_ordenados_por_orden(db_session, lote_con_incapacidades):
    incapacidad_id = lote_con_incapacidades["limpia"].id

    periodo_2 = PeriodoPrevisional(
        incapacidad_id=incapacidad_id,
        orden=2,
        fecha_inicio=date(2026, 1, 6),
        fecha_fin=date(2026, 1, 10),
        dias=5,
    )
    periodo_1 = PeriodoPrevisional(
        incapacidad_id=incapacidad_id,
        orden=1,
        fecha_inicio=date(2026, 1, 1),
        fecha_fin=date(2026, 1, 5),
        dias=5,
    )
    db_session.add_all([periodo_2, periodo_1])
    await db_session.commit()

    resultado = await periodo_previsional_repository.get_by_incapacidad(db_session, incapacidad_id)

    assert [p.orden for p in resultado] == [1, 2]


# ---------------------------------------------------------------------------
# siniestro_previsional_repository — lista, nunca .first()
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_by_identificacion_siniestros_devuelve_lista_ordenada(db_session):
    identificacion = "5000000001"

    s_antiguo = SiniestroPrevisional(
        identificacion=identificacion,
        numero_siniestro="SIN-A",
        fecha_siniestro=date(2025, 1, 1),
    )
    s_reciente = SiniestroPrevisional(
        identificacion=identificacion,
        numero_siniestro="SIN-B",
        fecha_siniestro=date(2025, 6, 1),
    )
    otro_afiliado = SiniestroPrevisional(
        identificacion="5000000002",
        numero_siniestro="SIN-C",
        fecha_siniestro=date(2025, 3, 1),
    )
    db_session.add_all([s_antiguo, s_reciente, otro_afiliado])
    await db_session.commit()

    resultado = await siniestro_previsional_repository.get_by_identificacion(
        db_session, identificacion
    )

    assert isinstance(resultado, list)
    assert len(resultado) == 2
    assert [s.numero_siniestro for s in resultado] == ["SIN-B", "SIN-A"]


@pytest.mark.asyncio
async def test_get_by_identificaciones_siniestros_carga_masiva(db_session):
    """Una sola llamada debe resolver varias identificaciones (evita N+1)."""
    s1 = SiniestroPrevisional(identificacion="6000000001", numero_siniestro="SIN-X")
    s2 = SiniestroPrevisional(identificacion="6000000002", numero_siniestro="SIN-Y")
    s3 = SiniestroPrevisional(identificacion="6000000003", numero_siniestro="SIN-Z")
    db_session.add_all([s1, s2, s3])
    await db_session.commit()

    resultado = await siniestro_previsional_repository.get_by_identificaciones(
        db_session, ["6000000001", "6000000002"]
    )

    identificaciones_resultado = {s.identificacion for s in resultado}
    assert identificaciones_resultado == {"6000000001", "6000000002"}


@pytest.mark.asyncio
async def test_get_by_identificaciones_siniestros_lista_vacia(db_session):
    resultado = await siniestro_previsional_repository.get_by_identificaciones(db_session, [])
    assert resultado == []


# ---------------------------------------------------------------------------
# solicitud_previsional_repository — misma filosofía de no-colapso
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_by_identificacion_solicitudes_devuelve_lista_ordenada(db_session):
    identificacion = "7000000001"

    sol_antigua = SolicitudPrevisional(
        identificacion=identificacion,
        radicado="RAD-1",
        fecha_inicial=date(2025, 1, 1),
    )
    sol_reciente = SolicitudPrevisional(
        identificacion=identificacion,
        radicado="RAD-2",
        fecha_inicial=date(2025, 8, 1),
    )
    db_session.add_all([sol_antigua, sol_reciente])
    await db_session.commit()

    resultado = await solicitud_previsional_repository.get_by_identificacion(
        db_session, identificacion
    )

    assert isinstance(resultado, list)
    assert len(resultado) == 2
    assert [s.radicado for s in resultado] == ["RAD-2", "RAD-1"]


@pytest.mark.asyncio
async def test_get_by_identificaciones_solicitudes_carga_masiva(db_session):
    sol1 = SolicitudPrevisional(identificacion="8000000001", radicado="RAD-A")
    sol2 = SolicitudPrevisional(identificacion="8000000002", radicado="RAD-B")
    db_session.add_all([sol1, sol2])
    await db_session.commit()

    resultado = await solicitud_previsional_repository.get_by_identificaciones(
        db_session, ["8000000001", "8000000002"]
    )
    assert len(resultado) == 2


# ---------------------------------------------------------------------------
# ite_historico_repository
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_exists_by_identificacion_fecha_true(db_session):
    ite = IteHistorico(identificacion="4000000001", fecha_inicial=date(2026, 3, 1))
    db_session.add(ite)
    await db_session.commit()

    existe = await ite_historico_repository.exists_by_identificacion_fecha(
        db_session, "4000000001", date(2026, 3, 1)
    )
    assert existe is True


@pytest.mark.asyncio
async def test_exists_by_identificacion_fecha_false(db_session):
    existe = await ite_historico_repository.exists_by_identificacion_fecha(
        db_session, "4000000099", date(2026, 3, 1)
    )
    assert existe is False


@pytest.mark.asyncio
async def test_get_existentes_ite_carga_masiva(db_session):
    ite1 = IteHistorico(identificacion="4100000001", fecha_inicial=date(2026, 4, 1))
    ite2 = IteHistorico(identificacion="4100000002", fecha_inicial=date(2026, 4, 2))
    db_session.add_all([ite1, ite2])
    await db_session.commit()

    claves = [
        ("4100000001", date(2026, 4, 1)),
        ("4100000002", date(2026, 4, 2)),
        ("4100000003", date(2026, 4, 3)),  # no existe
    ]
    resultado = await ite_historico_repository.get_existentes(db_session, claves)

    assert resultado == {
        ("4100000001", date(2026, 4, 1)),
        ("4100000002", date(2026, 4, 2)),
    }


@pytest.mark.asyncio
async def test_get_existentes_ite_lista_vacia(db_session):
    resultado = await ite_historico_repository.get_existentes(db_session, [])
    assert resultado == set()


# ---------------------------------------------------------------------------
# senal_auditoria_previsional_repository.bulk_create_flushed
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_bulk_create_flushed_senales(db_session, lote_con_incapacidades):
    incapacidad_id = lote_con_incapacidades["limpia"].id

    senales = [
        {
            "incapacidad_previsional_id": incapacidad_id,
            "codigo": "AB",
            "nombre": "Observación",
            "estado": "OK",
            "detalle": "Todo en orden",
        },
        {
            "incapacidad_previsional_id": incapacidad_id,
            "codigo": "AT",
            "nombre": "Doble pago",
            "estado": "ALERTA",
            "detalle": "Ya existe pago ITE previo",
        },
    ]

    creadas = await senal_auditoria_previsional_repository.bulk_create_flushed(
        db_session, senales
    )
    await db_session.commit()

    assert len(creadas) == 2
    assert all(s.id is not None for s in creadas)

    resultado = await senal_auditoria_previsional_repository.get_by_incapacidad(
        db_session, incapacidad_id
    )
    assert len(resultado) == 2
    codigos = {s.codigo for s in resultado}
    assert codigos == {"AB", "AT"}


@pytest.mark.asyncio
async def test_bulk_create_flushed_lista_vacia(db_session):
    resultado = await senal_auditoria_previsional_repository.bulk_create_flushed(db_session, [])
    assert resultado == []


# ---------------------------------------------------------------------------
# lote_previsional_repository — CRUD básico heredado
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_lote_previsional_crud_basico(db_session):
    lote = await lote_previsional_repository.create(
        db_session, {"nombre_archivo": "OTRO_LOTE.xlsx"}
    )
    assert lote.id is not None
    assert lote.estado == "CARGADO"

    encontrado = await lote_previsional_repository.get_by_id(db_session, lote.id)
    assert encontrado is not None
    assert encontrado.nombre_archivo == "OTRO_LOTE.xlsx"

"""
Tests para `auditoria_service.py` (Task 3.3) -- el orquestador que conecta
el motor puro de 19 reglas AB-AT (Task 1.4, `auditoria_rules.py`) con la
persistencia (`SenalAuditoriaPrevisional`) y las referencias externas ya
importadas por Task 3.2 (`siniestros_previsionales`/`solicitudes_previsionales`/
`ite_historico`).

Usa `db_session` (Postgres async real, no mocks) siguiendo el mismo patrón
que `test_lote_service.py`/`test_repositorios_previsionales.py`.

Sobre el conteo de queries de `construir_contexto`: en vez de instrumentar
`db_session.execute` (frágil frente a refactors internos de SQLAlchemy), se
verifica el resultado -- el contenido exacto de `ContextoAuditoria` para un
lote con siniestros/solicitudes/ite_historico sembrados -- y se deja a la
revisión de código (ver reporte de la tarea) la verificación de que
`_cargar_incapacidades_y_contexto` hace exactamente 4 llamadas `await
db.execute(...)`-equivalentes (una por `get_by_lote`,
`get_by_identificaciones` x2, `get_existentes`), ninguna dentro de un loop
por incapacidad.
"""
from datetime import date
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy import select

from app.core.exceptions import BadRequestException, NotFoundException
from app.db.repositories.previsionales import senal_auditoria_previsional_repository
from app.models.previsionales.incapacidad_previsional import IncapacidadPrevisional
from app.models.previsionales.ite_historico import IteHistorico
from app.models.previsionales.lote_previsional import LotePrevisional
from app.models.previsionales.siniestro_previsional import SiniestroPrevisional
from app.models.previsionales.solicitud_previsional import SolicitudPrevisional
from app.services.previsionales.auditoria_rules import REGLAS_PREVISIONALES
from app.services.previsionales.auditoria_service import auditoria_previsional_service


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def lote_para_auditar(db_session):
    """
    Un lote con 2 incapacidades de identificaciones distintas, más
    referencia externa (siniestro, solicitud, ite_historico) para UNA de
    ellas -- suficiente para ejercitar tanto el camino "con referencia"
    como el camino "sin referencia" (PENDIENTE) de las reglas.
    """
    lote = LotePrevisional(nombre_archivo="RADICADOS_AUDITORIA_TEST.xlsx")
    db_session.add(lote)
    await db_session.flush()

    inc_1 = IncapacidadPrevisional(
        lote_id=lote.id,
        identificacion="1000000001",
        fecha_inicial=date(2026, 1, 1),
        fecha_final=date(2026, 1, 20),
        tipo_ingreso="INICIAL",
        numero_siniestro="SIN-001",
        valor_afp=Decimal("500000"),
        dia_181_afp=date(2025, 6, 1),
        dia_181_arpis=date(2025, 6, 1),
    )
    inc_2 = IncapacidadPrevisional(
        lote_id=lote.id,
        identificacion="2000000002",
        fecha_inicial=date(2026, 2, 1),
        fecha_final=date(2026, 2, 15),
        tipo_ingreso="INICIAL",
    )
    db_session.add_all([inc_1, inc_2])
    await db_session.flush()

    siniestro = SiniestroPrevisional(
        identificacion="1000000001",
        numero_siniestro="SIN-001",
        origen="ARL",
        estado="ABIERTO",
        fecha_aviso=date(2025, 5, 1),
        fecha_siniestro=date(2025, 4, 28),
    )
    solicitud = SolicitudPrevisional(
        identificacion="1000000001",
        radicado="RAD-001",
        dia_181=date(2025, 6, 1),
        fecha_crie=date(2025, 5, 15),
    )
    ite = IteHistorico(
        identificacion="1000000001",
        fecha_inicial=date(2026, 1, 1),
        fecha_final=date(2026, 1, 20),
        valor_pagado=Decimal("500000"),
    )
    db_session.add_all([siniestro, solicitud, ite])
    await db_session.commit()
    await db_session.refresh(inc_1)
    await db_session.refresh(inc_2)

    return {"lote": lote, "inc_1": inc_1, "inc_2": inc_2}


# ---------------------------------------------------------------------------
# construir_contexto
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_construir_contexto_trae_siniestro_solicitud_e_ite_para_la_fila_con_referencia(
    db_session, lote_para_auditar
):
    ctx = await auditoria_previsional_service.construir_contexto(
        db_session, lote_para_auditar["lote"].id
    )

    assert "1000000001" in ctx.siniestros_por_id
    assert len(ctx.siniestros_por_id["1000000001"]) == 1
    assert ctx.siniestros_por_id["1000000001"][0].numero_siniestro == "SIN-001"

    assert "1000000001" in ctx.solicitudes_por_id
    assert ctx.solicitudes_por_id["1000000001"].dia_181 == date(2025, 6, 1)
    assert ctx.solicitudes_por_id["1000000001"].fecha_crie == date(2025, 5, 15)

    assert ("1000000001", date(2026, 1, 1)) in ctx.ite_por_clave


@pytest.mark.asyncio
async def test_construir_contexto_sin_referencia_para_identificacion_ausente(
    db_session, lote_para_auditar
):
    ctx = await auditoria_previsional_service.construir_contexto(
        db_session, lote_para_auditar["lote"].id
    )

    assert "2000000002" not in ctx.siniestros_por_id
    assert "2000000002" not in ctx.solicitudes_por_id
    assert ("2000000002", date(2026, 2, 1)) not in ctx.ite_por_clave


@pytest.mark.asyncio
async def test_construir_contexto_solicitud_ambigua_queda_ausente_del_dict(db_session):
    """
    Fix (ronda 1): con 2+ `SolicitudPrevisional` distintas para la misma
    identificación, `_elegir_solicitudes` ya NO elige "la primera" -- la
    identificación debe quedar ausente de `solicitudes_por_id`, igual que
    `_seleccionar_siniestro` deja ausente una identificación con 2+
    siniestros candidatos.
    """
    lote = LotePrevisional(nombre_archivo="RADICADOS_SOLICITUD_AMBIGUA.xlsx")
    db_session.add(lote)
    await db_session.flush()

    inc = IncapacidadPrevisional(
        lote_id=lote.id,
        identificacion="4000000004",
        fecha_inicial=date(2026, 4, 1),
        fecha_final=date(2026, 4, 20),
        tipo_ingreso="INICIAL",
    )
    db_session.add(inc)
    await db_session.flush()

    sol_a = SolicitudPrevisional(
        identificacion="4000000004",
        radicado="RAD-A",
        dia_181=date(2025, 9, 1),
        fecha_crie=date(2025, 8, 15),
    )
    sol_b = SolicitudPrevisional(
        identificacion="4000000004",
        radicado="RAD-B",
        dia_181=date(2025, 10, 1),
        fecha_crie=date(2025, 9, 15),
    )
    db_session.add_all([sol_a, sol_b])
    await db_session.commit()
    await db_session.refresh(inc)

    ctx = await auditoria_previsional_service.construir_contexto(db_session, lote.id)
    assert "4000000004" not in ctx.solicitudes_por_id

    total = await auditoria_previsional_service.auditar_lote(db_session, lote.id)
    assert total == 1

    senales = await senal_auditoria_previsional_repository.get_by_incapacidad(db_session, inc.id)
    senal_ae = next(s for s in senales if s.codigo == "AE")
    senal_ag = next(s for s in senales if s.codigo == "AG")
    # Ambigüedad genuina (2 solicitudes distintas) -> PENDIENTE, no un OK
    # con un valor elegido sin base real.
    assert senal_ae.estado == "PENDIENTE"
    assert senal_ae.valor is None
    assert senal_ag.estado == "PENDIENTE"
    assert senal_ag.valor is None


@pytest.mark.asyncio
async def test_construir_contexto_repetidas_por_clave_se_deriva_del_lote(db_session):
    lote = LotePrevisional(nombre_archivo="RADICADOS_REPETIDAS.xlsx")
    db_session.add(lote)
    await db_session.flush()

    a = IncapacidadPrevisional(
        lote_id=lote.id, identificacion="3000000003", fecha_inicial=date(2026, 3, 1),
        fecha_final=date(2026, 3, 10),
    )
    b = IncapacidadPrevisional(
        lote_id=lote.id, identificacion="3000000003", fecha_inicial=date(2026, 3, 1),
        fecha_final=date(2026, 3, 12),
    )
    db_session.add_all([a, b])
    await db_session.commit()

    ctx = await auditoria_previsional_service.construir_contexto(db_session, lote.id)

    clave = ("3000000003", date(2026, 3, 1))
    assert clave in ctx.repetidas_por_clave
    assert len(ctx.repetidas_por_clave[clave]) == 2
    assert {str(a.id), str(b.id)} == set(ctx.repetidas_por_clave[clave])


# ---------------------------------------------------------------------------
# auditar_lote
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_auditar_lote_persiste_19_senales_por_incapacidad(db_session, lote_para_auditar):
    total = await auditoria_previsional_service.auditar_lote(
        db_session, lote_para_auditar["lote"].id
    )
    assert total == 2

    senales_inc_1 = await senal_auditoria_previsional_repository.get_by_incapacidad(
        db_session, lote_para_auditar["inc_1"].id
    )
    senales_inc_2 = await senal_auditoria_previsional_repository.get_by_incapacidad(
        db_session, lote_para_auditar["inc_2"].id
    )
    assert len(senales_inc_1) == len(REGLAS_PREVISIONALES) == 19
    assert len(senales_inc_2) == 19

    codigos_inc_1 = {s.codigo for s in senales_inc_1}
    assert codigos_inc_1 == {codigo for codigo, _nombre, _fn in REGLAS_PREVISIONALES}

    # AT (doble pago): inc_1 comparte (identificacion, fecha_inicial) con el
    # ITE histórico sembrado -> debe salir en ALERTA.
    senal_at = next(s for s in senales_inc_1 if s.codigo == "AT")
    assert senal_at.estado == "ALERTA"
    assert senal_at.valor is True

    # AM (siniestro): inc_1 tiene exactamente un candidato -> OK con el
    # número de siniestro.
    senal_am = next(s for s in senales_inc_1 if s.codigo == "AM")
    assert senal_am.estado == "OK"
    assert senal_am.valor == "SIN-001"

    # inc_2 no tiene siniestro asociado -> AM en PENDIENTE.
    senal_am_2 = next(s for s in senales_inc_2 if s.codigo == "AM")
    assert senal_am_2.estado == "PENDIENTE"


@pytest.mark.asyncio
async def test_auditar_lote_dos_veces_no_duplica_senales(db_session, lote_para_auditar):
    await auditoria_previsional_service.auditar_lote(db_session, lote_para_auditar["lote"].id)
    await auditoria_previsional_service.auditar_lote(db_session, lote_para_auditar["lote"].id)

    senales_inc_1 = await senal_auditoria_previsional_repository.get_by_incapacidad(
        db_session, lote_para_auditar["inc_1"].id
    )
    assert len(senales_inc_1) == 19


@pytest.mark.asyncio
async def test_auditar_lote_ah_ai_son_dict_tipado_no_texto(db_session, lote_para_auditar):
    await auditoria_previsional_service.auditar_lote(db_session, lote_para_auditar["lote"].id)

    senales = await senal_auditoria_previsional_repository.get_by_incapacidad(
        db_session, lote_para_auditar["inc_1"].id
    )
    senal_ah = next(s for s in senales if s.codigo == "AH")
    assert isinstance(senal_ah.valor, dict)
    assert senal_ah.valor["identificacion"] == "1000000001"
    assert senal_ah.valor["fecha"] == "2026-01-01"


# ---------------------------------------------------------------------------
# auditar_incapacidad
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_auditar_incapacidad_sin_ctx_construye_contexto_minimo(
    db_session, lote_para_auditar
):
    senales = await auditoria_previsional_service.auditar_incapacidad(
        db_session, lote_para_auditar["inc_1"].id
    )
    assert len(senales) == 19
    senal_am = next(s for s in senales if s.codigo == "AM")
    assert senal_am.estado == "OK"
    assert senal_am.valor == "SIN-001"


@pytest.mark.asyncio
async def test_auditar_incapacidad_id_inexistente_lanza_not_found(db_session):
    import uuid

    with pytest.raises(NotFoundException):
        await auditoria_previsional_service.auditar_incapacidad(db_session, uuid.uuid4())


# ---------------------------------------------------------------------------
# registrar_aval
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_registrar_aval_no_sin_motivo_lanza_bad_request_y_no_toca_bd(
    db_session, lote_para_auditar, test_usuario
):
    inc = lote_para_auditar["inc_1"]

    with pytest.raises(BadRequestException):
        await auditoria_previsional_service.registrar_aval(
            db_session, inc.id, "NO", None, test_usuario.id
        )

    result = await db_session.execute(
        select(IncapacidadPrevisional).where(IncapacidadPrevisional.id == inc.id)
    )
    fresca = result.scalar_one()
    assert fresca.aval is None
    assert fresca.usuario_auditoria_id is None
    assert fresca.fecha_auditoria is None


@pytest.mark.asyncio
async def test_registrar_aval_no_con_motivo_vacio_lanza_bad_request(
    db_session, lote_para_auditar, test_usuario
):
    inc = lote_para_auditar["inc_1"]
    with pytest.raises(BadRequestException):
        await auditoria_previsional_service.registrar_aval(
            db_session, inc.id, "NO", "", test_usuario.id
        )


@pytest.mark.asyncio
async def test_registrar_aval_si_persiste_usuario_y_fecha(
    db_session, lote_para_auditar, test_usuario
):
    inc = lote_para_auditar["inc_1"]

    actualizada = await auditoria_previsional_service.registrar_aval(
        db_session, inc.id, "SI", None, test_usuario.id
    )

    assert actualizada.aval == "SI"
    assert actualizada.motivo_no_aval is None
    assert actualizada.usuario_auditoria_id == test_usuario.id
    assert actualizada.fecha_auditoria is not None
    assert actualizada.estado == "AVALADO"


@pytest.mark.asyncio
async def test_registrar_aval_no_con_motivo_persiste_motivo_y_estado_no_avalado(
    db_session, lote_para_auditar, test_usuario
):
    inc = lote_para_auditar["inc_2"]

    actualizada = await auditoria_previsional_service.registrar_aval(
        db_session, inc.id, "NO", "Documentación incompleta", test_usuario.id
    )

    assert actualizada.aval == "NO"
    assert actualizada.motivo_no_aval == "Documentación incompleta"
    assert actualizada.estado == "NO_AVALADO"


@pytest.mark.asyncio
async def test_registrar_aval_id_inexistente_lanza_not_found(db_session, test_usuario):
    import uuid

    with pytest.raises(NotFoundException):
        await auditoria_previsional_service.registrar_aval(
            db_session, uuid.uuid4(), "SI", None, test_usuario.id
        )


@pytest.mark.asyncio
async def test_registrar_aval_estado_liquidado_lanza_bad_request_y_no_regresa_estado(
    db_session, lote_para_auditar, test_usuario
):
    """
    Fix (ronda 1): si la fila ya avanzó más allá de la etapa de auditoría
    (aquí, LIQUIDADO), `registrar_aval` debe rechazar la llamada en vez de
    retroceder `estado` silenciosamente de vuelta a AVALADO/NO_AVALADO.
    """
    inc = lote_para_auditar["inc_1"]
    inc.estado = "LIQUIDADO"
    db_session.add(inc)
    await db_session.commit()

    with pytest.raises(BadRequestException):
        await auditoria_previsional_service.registrar_aval(
            db_session, inc.id, "SI", None, test_usuario.id
        )

    result = await db_session.execute(
        select(IncapacidadPrevisional).where(IncapacidadPrevisional.id == inc.id)
    )
    fresca = result.scalar_one()
    # El estado NO debe haber regresado a AVALADO -- sigue en LIQUIDADO.
    assert fresca.estado == "LIQUIDADO"
    assert fresca.aval is None
    assert fresca.usuario_auditoria_id is None


@pytest.mark.asyncio
async def test_registrar_aval_estado_pagado_lanza_bad_request(
    db_session, lote_para_auditar, test_usuario
):
    inc = lote_para_auditar["inc_2"]
    inc.estado = "PAGADO"
    db_session.add(inc)
    await db_session.commit()

    with pytest.raises(BadRequestException):
        await auditoria_previsional_service.registrar_aval(
            db_session, inc.id, "NO", "Motivo cualquiera", test_usuario.id
        )

    result = await db_session.execute(
        select(IncapacidadPrevisional).where(IncapacidadPrevisional.id == inc.id)
    )
    fresca = result.scalar_one()
    assert fresca.estado == "PAGADO"


# ---------------------------------------------------------------------------
# duplicar
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_duplicar_crea_registro_marcado_con_origen_y_fechas_propias(
    db_session, lote_para_auditar, test_usuario
):
    origen = lote_para_auditar["inc_1"]

    copia = await auditoria_previsional_service.duplicar(
        db_session,
        origen.id,
        {"fecha_inicial": date(2026, 1, 21), "fecha_final": date(2026, 1, 31)},
        test_usuario.id,
    )

    assert copia.id != origen.id
    assert copia.es_duplicado_interno is True
    assert copia.incapacidad_origen_id == origen.id
    assert copia.fecha_inicial == date(2026, 1, 21)
    assert copia.fecha_final == date(2026, 1, 31)
    # Campos identitarios heredados del origen.
    assert copia.identificacion == origen.identificacion
    assert copia.lote_id == origen.lote_id
    # La copia es una fila NUEVA: no hereda el aval del origen.
    assert copia.aval is None
    assert copia.usuario_auditoria_id is None
    assert copia.metadata_["duplicado_por_usuario_id"] == str(test_usuario.id)
    assert copia.metadata_["duplicado_de_incapacidad_id"] == str(origen.id)

    # Persistido de verdad (no solo en memoria).
    result = await db_session.execute(
        select(IncapacidadPrevisional).where(IncapacidadPrevisional.id == copia.id)
    )
    assert result.scalar_one() is not None


@pytest.mark.asyncio
async def test_duplicar_sin_fechas_lanza_bad_request(db_session, lote_para_auditar, test_usuario):
    origen = lote_para_auditar["inc_1"]
    with pytest.raises(BadRequestException):
        await auditoria_previsional_service.duplicar(db_session, origen.id, {}, test_usuario.id)


@pytest.mark.asyncio
async def test_duplicar_id_inexistente_lanza_not_found(db_session, test_usuario):
    import uuid

    with pytest.raises(NotFoundException):
        await auditoria_previsional_service.duplicar(
            db_session,
            uuid.uuid4(),
            {"fecha_inicial": date(2026, 1, 1), "fecha_final": date(2026, 1, 5)},
            test_usuario.id,
        )

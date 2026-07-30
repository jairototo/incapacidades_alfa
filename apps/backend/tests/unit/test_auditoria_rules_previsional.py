"""
Tests for the AB-AT pension-disability audit rules engine.

Every `regla_xx_*` function is pure (dict row + frozen ContextoAuditoria ->
Senal). The four "lock" tests below (test_ac_aval_nunca_se_autocalcula,
test_ah_fi_es_tupla_tipada_no_texto, test_aj_ak_quedan_pendientes_por_falta_de_datos_externos,
test_am_con_varios_siniestros_no_elige_silenciosamente) are taken verbatim
from the approved implementation brief (task 1.4) and encode the four
contracts this module must never "fix" with a heuristic:
- AC (aval) never auto-computed.
- AH/AI (FI/FF) are a typed dict, never a concatenated string.
- AJ/AK (CI/CF) are permanently PENDIENTE (no [1]DATOS workbook available).
- AM (siniestro) never silently picks a candidate when there's more than one.
"""
from dataclasses import replace
from datetime import date, timedelta

from app.services.previsionales.auditoria_rules import (
    REGLAS_PREVISIONALES,
    ContextoAuditoria,
    Senal,
    SiniestroRef,
    SolicitudRef,
    agrupar_repetidas,
    encadenar_prorrogas,
    evaluar_todas,
    regla_ab_observacion,
    regla_ac_aval,
    regla_ad_repetidas,
    regla_ae_dia_181,
    regla_af_dia_540,
    regla_ag_fecha_crie,
    regla_ah_fi,
    regla_ai_ff,
    regla_aj_ci,
    regla_ak_cf,
    regla_al_comparacion_dia181,
    regla_am_siniestro,
    regla_an_origen,
    regla_ao_estado,
    regla_ap_fecha_siniestro,
    regla_aq_pago_ite,
    regla_ar_siniestro_valor,
    regla_as_sipren,
    regla_at_doble_pago,
)

ctx_vacio = ContextoAuditoria(
    solicitudes_por_id={},
    siniestros_por_id={},
    ite_por_clave=set(),
    repetidas_por_clave={},
)


# ---------------------------------------------------------------------------
# Los cuatro tests-candado del brief (verbatim)
# ---------------------------------------------------------------------------


def test_ac_aval_nunca_se_autocalcula():
    s = regla_ac_aval({"aval": None}, ctx_vacio)
    assert s.estado == "PENDIENTE" and s.valor is None


def test_ah_fi_es_tupla_tipada_no_texto():
    s = regla_ah_fi({"identificacion": "4661182", "fecha_inicial": date(2026, 7, 11)}, ctx_vacio)
    assert not isinstance(s.valor, str)  # el bug que estamos corrigiendo
    assert s.valor == {"identificacion": "4661182", "fecha": date(2026, 7, 11)}


def test_aj_ak_quedan_pendientes_por_falta_de_datos_externos():
    row = {"identificacion": "4661182"}
    assert regla_aj_ci(row, ctx_vacio).estado == "PENDIENTE"
    assert regla_ak_cf(row, ctx_vacio).estado == "PENDIENTE"


def test_am_con_varios_siniestros_no_elige_silenciosamente():
    sin_a = SiniestroRef(numero_siniestro="SIN-A", origen="ARL", estado="ABIERTO")
    sin_b = SiniestroRef(numero_siniestro="SIN-B", origen="ARL", estado="CERRADO")
    ctx = replace(ctx_vacio, siniestros_por_id={"123": [sin_a, sin_b]})
    s = regla_am_siniestro({"identificacion": "123"}, ctx)
    assert s.estado == "PENDIENTE" and s.valor["seleccionado"] is None
    assert s.valor["candidatos"] == [sin_a, sin_b]


def test_ad_repetidas_independiente_del_orden():
    r1 = {"id": "r1", "identificacion": "23333262", "fecha_inicial": date(2026, 7, 11)}
    r2 = {"id": "r2", "identificacion": "23333262", "fecha_inicial": date(2026, 7, 11)}
    r3 = {"id": "r3", "identificacion": "23333262", "fecha_inicial": date(2026, 7, 11)}
    rows = [r1, r3, r2]  # desordenadas a proposito
    grupos = agrupar_repetidas(rows)
    assert len(grupos[("23333262", date(2026, 7, 11))]) == 3


# ---------------------------------------------------------------------------
# Una regla a la vez, AB..AT
# ---------------------------------------------------------------------------


def test_ab_observacion_ok():
    s = regla_ab_observacion({"dia_181_alfa": date(2026, 7, 11)}, ctx_vacio)
    assert s.codigo == "AB" and s.estado == "OK" and s.valor == "DIA 181 2026-07-11"


def test_ab_observacion_pendiente_sin_dato():
    s = regla_ab_observacion({}, ctx_vacio)
    assert s.estado == "PENDIENTE" and s.valor is None


def test_ac_aval_ok_cuando_ya_lo_seteo_un_humano():
    s = regla_ac_aval({"aval": "SI"}, ctx_vacio)
    assert s.estado == "OK" and s.valor == "SI"


def test_ad_alerta_si_hay_repetidas():
    ctx = replace(ctx_vacio, repetidas_por_clave={("111", date(2026, 7, 11)): ["a", "b"]})
    s = regla_ad_repetidas({"identificacion": "111", "fecha_inicial": date(2026, 7, 11)}, ctx)
    assert s.estado == "ALERTA" and s.valor == ["a", "b"]


def test_ad_ok_si_no_hay_repetidas():
    ctx = replace(ctx_vacio, repetidas_por_clave={("111", date(2026, 7, 11)): ["a"]})
    s = regla_ad_repetidas({"identificacion": "111", "fecha_inicial": date(2026, 7, 11)}, ctx)
    assert s.estado == "OK"


def test_ae_dia_181_afp_pendiente_si_afiliado_no_esta():
    s = regla_ae_dia_181({"identificacion": "999"}, ctx_vacio)
    assert s.estado == "PENDIENTE" and s.valor is None


def test_ae_dia_181_afp_ok():
    ctx = replace(ctx_vacio, solicitudes_por_id={"111": SolicitudRef(dia_181=date(2026, 1, 1))})
    s = regla_ae_dia_181({"identificacion": "111"}, ctx)
    assert s.estado == "OK" and s.valor == date(2026, 1, 1)


def test_af_dia_540_es_dia_181_mas_359():
    ctx = replace(ctx_vacio, solicitudes_por_id={"111": SolicitudRef(dia_181=date(2026, 1, 1))})
    s = regla_af_dia_540({"identificacion": "111"}, ctx)
    assert s.estado == "OK" and s.valor == date(2026, 1, 1) + timedelta(days=359)


def test_af_dia_540_pendiente_sin_base():
    s = regla_af_dia_540({"identificacion": "999"}, ctx_vacio)
    assert s.estado == "PENDIENTE" and s.valor is None


def test_ag_fecha_crie_ok():
    ctx = replace(ctx_vacio, solicitudes_por_id={"111": SolicitudRef(fecha_crie=date(2026, 2, 2))})
    s = regla_ag_fecha_crie({"identificacion": "111"}, ctx)
    assert s.estado == "OK" and s.valor == date(2026, 2, 2)


def test_ag_fecha_crie_pendiente_si_afiliado_no_esta():
    s = regla_ag_fecha_crie({"identificacion": "999"}, ctx_vacio)
    assert s.estado == "PENDIENTE"


def test_ai_ff_es_tupla_tipada():
    s = regla_ai_ff({"identificacion": "4661182", "fecha_final": date(2026, 8, 1)}, ctx_vacio)
    assert not isinstance(s.valor, str)
    assert s.valor == {"identificacion": "4661182", "fecha": date(2026, 8, 1)}


def test_al_ok_si_coinciden():
    s = regla_al_comparacion_dia181({"dia_181_arpis": date(2026, 1, 1), "dia_181_afp": date(2026, 1, 1)}, ctx_vacio)
    assert s.estado == "OK" and s.valor is True


def test_al_alerta_si_no_coinciden():
    s = regla_al_comparacion_dia181({"dia_181_arpis": date(2026, 1, 1), "dia_181_afp": date(2026, 1, 2)}, ctx_vacio)
    assert s.estado == "ALERTA" and s.valor is False


def test_al_pendiente_si_falta_alguno():
    s = regla_al_comparacion_dia181({"dia_181_arpis": date(2026, 1, 1)}, ctx_vacio)
    assert s.estado == "PENDIENTE"


def test_am_pendiente_sin_siniestro_asociado():
    s = regla_am_siniestro({"identificacion": "999"}, ctx_vacio)
    assert s.estado == "PENDIENTE" and s.valor is None


def test_am_ok_con_un_solo_siniestro():
    sin_a = SiniestroRef(numero_siniestro="SIN-A", origen="ARL", estado="ABIERTO")
    ctx = replace(ctx_vacio, siniestros_por_id={"111": [sin_a]})
    s = regla_am_siniestro({"identificacion": "111"}, ctx)
    assert s.estado == "OK" and s.valor == "SIN-A"


def test_an_origen_ok_con_un_solo_siniestro():
    sin_a = SiniestroRef(numero_siniestro="SIN-A", origen="ARL", estado="ABIERTO")
    ctx = replace(ctx_vacio, siniestros_por_id={"111": [sin_a]})
    s = regla_an_origen({"identificacion": "111"}, ctx)
    assert s.estado == "OK" and s.valor == "ARL"


def test_an_pendiente_con_varios_siniestros():
    sin_a = SiniestroRef(numero_siniestro="SIN-A", origen="ARL", estado="ABIERTO")
    sin_b = SiniestroRef(numero_siniestro="SIN-B", origen="ARL", estado="CERRADO")
    ctx = replace(ctx_vacio, siniestros_por_id={"111": [sin_a, sin_b]})
    s = regla_an_origen({"identificacion": "111"}, ctx)
    assert s.estado == "PENDIENTE"


def test_ao_estado_ok_con_un_solo_siniestro():
    sin_a = SiniestroRef(numero_siniestro="SIN-A", origen="ARL", estado="ABIERTO")
    ctx = replace(ctx_vacio, siniestros_por_id={"111": [sin_a]})
    s = regla_ao_estado({"identificacion": "111"}, ctx)
    assert s.estado == "OK" and s.valor == "ABIERTO"


def test_ap_fechas_siniestro_tupla_tipada():
    sin_a = SiniestroRef(
        numero_siniestro="SIN-A", origen="ARL", estado="ABIERTO",
        fecha_aviso=date(2026, 1, 5), fecha_siniestro=date(2026, 1, 1),
    )
    ctx = replace(ctx_vacio, siniestros_por_id={"111": [sin_a]})
    s = regla_ap_fecha_siniestro({"identificacion": "111"}, ctx)
    assert s.estado == "OK"
    assert s.valor == {"fecha_aviso": date(2026, 1, 5), "fecha_siniestro": date(2026, 1, 1)}


def test_aq_pago_ite_texto():
    s = regla_aq_pago_ite({"fecha_inicial": date(2026, 7, 11), "fecha_final": date(2026, 7, 25)}, ctx_vacio)
    assert s.estado == "OK"
    assert s.valor == "SE REALIZA PAGO DE ITE DE 2026-07-11 A 2026-07-25"


def test_aq_pago_ite_pendiente_sin_fechas():
    s = regla_aq_pago_ite({"fecha_inicial": date(2026, 7, 11)}, ctx_vacio)
    assert s.estado == "PENDIENTE"


def test_ar_siniestro_valor_texto():
    s = regla_ar_siniestro_valor({"numero_siniestro": "SIN-A", "valor_afp": "1750905"}, ctx_vacio)
    assert s.estado == "OK" and s.valor == "SIN-A 1750905"


def test_ar_siniestro_valor_pendiente_si_falta_algo():
    s = regla_ar_siniestro_valor({"numero_siniestro": "SIN-A"}, ctx_vacio)
    assert s.estado == "PENDIENTE"


def test_as_sipren_siempre_info():
    s = regla_as_sipren({}, ctx_vacio)
    assert s.estado == "INFO"


def test_at_alerta_si_posible_doble_pago():
    ctx = replace(ctx_vacio, ite_por_clave={("111", date(2026, 7, 11))})
    s = regla_at_doble_pago({"identificacion": "111", "fecha_inicial": date(2026, 7, 11)}, ctx)
    assert s.estado == "ALERTA" and s.valor is True


def test_at_ok_si_no_hay_coincidencia():
    s = regla_at_doble_pago({"identificacion": "111", "fecha_inicial": date(2026, 7, 11)}, ctx_vacio)
    assert s.estado == "OK" and s.valor is False


# ---------------------------------------------------------------------------
# Orquestacion / registro
# ---------------------------------------------------------------------------


def test_reglas_previsionales_tiene_19_entradas_ab_a_at():
    assert len(REGLAS_PREVISIONALES) == 19
    codigos = [codigo for codigo, _nombre, _funcion in REGLAS_PREVISIONALES]
    assert codigos == [
        "AB", "AC", "AD", "AE", "AF", "AG", "AH", "AI", "AJ", "AK",
        "AL", "AM", "AN", "AO", "AP", "AQ", "AR", "AS", "AT",
    ]


def test_evaluar_todas_corre_las_19_reglas_en_orden():
    row = {
        "identificacion": "4661182",
        "fecha_inicial": date(2026, 7, 11),
        "fecha_final": date(2026, 7, 25),
        "aval": None,
        "dia_181_alfa": None,
        "dia_181_arpis": None,
        "dia_181_afp": None,
        "numero_siniestro": None,
        "valor_afp": None,
    }
    senales = evaluar_todas(row, ctx_vacio)
    assert len(senales) == 19
    assert all(isinstance(s, Senal) for s in senales)
    assert [s.codigo for s in senales] == [
        "AB", "AC", "AD", "AE", "AF", "AG", "AH", "AI", "AJ", "AK",
        "AL", "AM", "AN", "AO", "AP", "AQ", "AR", "AS", "AT",
    ]


# ---------------------------------------------------------------------------
# encadenar_prorrogas
# ---------------------------------------------------------------------------


def test_encadenar_prorrogas_encuentra_la_incapacidad_anterior():
    original = {
        "id": "orig", "identificacion": "111", "tipo_ingreso": "INICIAL",
        "fecha_inicial": date(2026, 6, 1), "fecha_final": date(2026, 6, 30),
    }
    prorroga = {
        "id": "prorroga1", "identificacion": "111", "tipo_ingreso": "PRORROGA",
        "fecha_inicial": date(2026, 7, 1), "fecha_final": date(2026, 7, 31),
    }
    encadenadas = encadenar_prorrogas([prorroga, original])
    assert encadenadas == {"prorroga1": "orig"}


def test_encadenar_prorrogas_huerfana_mapea_a_none():
    prorroga = {
        "id": "prorroga1", "identificacion": "111", "tipo_ingreso": "PRORROGA",
        "fecha_inicial": date(2026, 7, 1), "fecha_final": date(2026, 7, 31),
    }
    encadenadas = encadenar_prorrogas([prorroga])
    assert encadenadas == {"prorroga1": None}


def test_encadenar_prorrogas_ignora_filas_no_encadenables():
    inicial = {
        "id": "a", "identificacion": "111", "tipo_ingreso": "INICIAL",
        "fecha_inicial": date(2026, 6, 1), "fecha_final": date(2026, 6, 30),
    }
    encadenadas = encadenar_prorrogas([inicial])
    assert encadenadas == {}


def test_encadenar_prorrogas_elige_la_mas_reciente_entre_varias_previas():
    vieja = {
        "id": "vieja", "identificacion": "111", "tipo_ingreso": "INICIAL",
        "fecha_inicial": date(2026, 4, 1), "fecha_final": date(2026, 4, 30),
    }
    reciente = {
        "id": "reciente", "identificacion": "111", "tipo_ingreso": "PRORROGA",
        "fecha_inicial": date(2026, 6, 1), "fecha_final": date(2026, 6, 30),
    }
    prorroga = {
        "id": "prorroga2", "identificacion": "111", "tipo_ingreso": "PRORROGA",
        "fecha_inicial": date(2026, 7, 1), "fecha_final": date(2026, 7, 31),
    }
    encadenadas = encadenar_prorrogas([vieja, reciente, prorroga])
    assert encadenadas["prorroga2"] == "reciente"

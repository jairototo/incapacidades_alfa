"""
Motor de reglas de auditoria AB-AT (hoja FORMALIZACION, columnas AB a AT).

Espeja la separacion que ya existe en el repo entre reglas puras
(`incapacidad_validation_rules.py`) y el orquestador que persiste
(`auditoria_service.py`). Diferencia de forma: AB-AT no son predicados,
producen valores heterogeneos, asi que la senal lleva un `valor: Any` en vez
de un `aprobado: bool`.

Todas las funciones `regla_xx_*` son puras: reciben una fila (`dict`) del
lote y un `ContextoAuditoria` congelado, precargado UNA VEZ por lote por la
capa de servicio (tarea posterior, no esta). Nunca hacen I/O, nunca tocan
BD/async -- eso evita el N+1 que CLAUDE.md senala como el pecado capital
del repo (Laravel original: ~2500 queries para 255 filas).

Contratos deliberados que este modulo NO debe "arreglar" con heuristicas:

- AC (aval): jamas se autocalcula. Vive en PENDIENTE mientras `aval is None`
  y solo un auditor humano lo cambia, via una accion separada fuera de este
  motor.
- AH/AI (FI/FF): `valor` es SIEMPRE un dict tipado
  `{"identificacion": str, "fecha": date}`, nunca texto concatenado. El
  macro de Excel original concatenaba identificacion + fecha en un string y
  eso rompia silenciosamente por mezclas de formato de fecha (el "bug" que
  esta version corrige, no replica).
- AJ/AK (CI/CF): PENDIENTE fijo, siempre. El libro externo `[1]DATOS` nunca
  fue entregado a este proyecto. Esto es permanente, no un TODO pendiente de
  resolver.
- AM (siniestro) y, por extension, AN/AO/AP (que dependen de la misma
  seleccion): si hay mas de un siniestro candidato para la misma
  identificacion, NUNCA se elige silenciosamente -- ni "el primero" al
  estilo del VLOOKUP original de Excel, ni "el mas reciente" al estilo del
  requerimiento de negocio (nunca reconciliado con el macro). Se emite
  PENDIENTE exponiendo los candidatos, precedente de estilo:
  `liquidacion_service.py` devuelve `None` con comentario "formula TBD" en
  vez de inventar un valor.
"""
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any, Callable, Literal

EstadoSenal = Literal["OK", "ALERTA", "PENDIENTE", "INFO"]

# AF cierra el debate 360 vs 540: el resultado es el dia 540
# (dia_181 + 359 dias = dia 540). La columna O de la AFP es solo informativa.
_DIAS_DIA_181_A_DIA_540 = 359

# tipo_ingreso que participan en el encadenamiento de prorrogas (ver
# `encadenar_prorrogas`).
_TIPOS_ENCADENABLES = {"PRORROGA", "TUTELA_P", "AJUSTE"}


@dataclass(frozen=True)
class Senal:
    """Resultado de evaluar una regla AB-AT sobre una fila."""

    codigo: str  # "AB".."AT"
    nombre: str
    estado: EstadoSenal
    valor: Any  # date | dict | bool | str | list | None
    detalle: str | None = None


@dataclass(frozen=True)
class SolicitudRef:
    """Referencia minima a una solicitud AFP, usada por AE/AG.

    Campos limitados a lo que las reglas realmente leen: el dia 181 segun la
    AFP (AE, y base aritmetica de AF) y la fecha CRIE (AG).
    """

    dia_181: date | None = None
    fecha_crie: date | None = None


@dataclass(frozen=True)
class SiniestroRef:
    """Referencia minima a un siniestro ARL, usada por AM-AP.

    Campos limitados a lo que las reglas realmente leen: numero de siniestro
    (AM), origen (AN), estado (AO) y las dos fechas del siniestro (AP).
    """

    numero_siniestro: str
    origen: str
    estado: str
    fecha_aviso: date | None = None
    fecha_siniestro: date | None = None


@dataclass(frozen=True)
class ContextoAuditoria:
    """Datos de referencia precargados una vez por lote (nunca por fila)."""

    solicitudes_por_id: dict[str, SolicitudRef]  # AE, AG
    siniestros_por_id: dict[str, list[SiniestroRef]]  # AM-AP (LISTA, ver arriba)
    ite_por_clave: set[tuple[str, date]]  # AT
    repetidas_por_clave: dict[tuple[str, date], list[str]]  # AD
    datos_externos_disponibles: bool = False  # AJ/AK (reservado; ver nota AJ/AK)


# ---------------------------------------------------------------------------
# Helper interno: seleccion de siniestro compartida por AM-AP
# ---------------------------------------------------------------------------


def _seleccionar_siniestro(
    ctx: ContextoAuditoria, identificacion: str | None
) -> tuple[SiniestroRef | None, list[SiniestroRef]]:
    """Devuelve (seleccionado, candidatos).

    `seleccionado` es un SiniestroRef solo si hay EXACTAMENTE un candidato.
    Con 0 o con 2+ candidatos, `seleccionado` es None -- el llamador decide
    como reportar la ambiguedad/ausencia, pero ninguna regla puede derivar
    un campo del siniestro sin una seleccion inequivoca.
    """
    candidatos = ctx.siniestros_por_id.get(identificacion, []) if identificacion is not None else []
    if len(candidatos) == 1:
        return candidatos[0], candidatos
    return None, candidatos


# ---------------------------------------------------------------------------
# Reglas AB-AT
# ---------------------------------------------------------------------------


def regla_ab_observacion(row: dict, ctx: ContextoAuditoria) -> Senal:
    """AB: 'DIA 181 ' + dia_181_alfa -- el auditado, no el de la AFP."""
    dia_181_alfa = row.get("dia_181_alfa")
    if dia_181_alfa is None:
        return Senal("AB", "Dia 181 (auditado)", "PENDIENTE", None,
                     "Aun no hay dia_181_alfa calculado por el auditor")
    return Senal("AB", "Dia 181 (auditado)", "OK", f"DIA 181 {dia_181_alfa}")


def regla_ac_aval(row: dict, ctx: ContextoAuditoria) -> Senal:
    """AC: siempre PENDIENTE mientras aval is None. Nunca se autocalcula."""
    aval = row.get("aval")
    if aval is None:
        return Senal("AC", "Aval", "PENDIENTE", None,
                     "El aval lo define un auditor humano; esta regla nunca lo autocalcula")
    return Senal("AC", "Aval", "OK", aval)


def regla_ad_repetidas(row: dict, ctx: ContextoAuditoria) -> Senal:
    """AD: ALERTA si hay mas de una fila del lote con (identificacion, fecha_inicial)."""
    clave = (row.get("identificacion"), row.get("fecha_inicial"))
    lista = ctx.repetidas_por_clave.get(clave, [])
    if len(lista) > 1:
        return Senal("AD", "Filas repetidas en el lote", "ALERTA", lista,
                     f"{len(lista)} filas del lote comparten identificacion y fecha inicial")
    return Senal("AD", "Filas repetidas en el lote", "OK", lista)


def regla_ae_dia_181(row: dict, ctx: ContextoAuditoria) -> Senal:
    """AE: dia_181 de solicitudes (AFP); PENDIENTE si el afiliado no esta."""
    sol = ctx.solicitudes_por_id.get(row.get("identificacion"))
    if sol is None or sol.dia_181 is None:
        return Senal("AE", "Dia 181 (AFP)", "PENDIENTE", None,
                     "El afiliado no esta en las solicitudes AFP, o no tiene dia_181")
    return Senal("AE", "Dia 181 (AFP)", "OK", sol.dia_181)


def regla_af_dia_540(row: dict, ctx: ContextoAuditoria) -> Senal:
    """AF: dia_181 + 359 dias. Aritmetica pura -- cierra el debate 360/540."""
    sol = ctx.solicitudes_por_id.get(row.get("identificacion"))
    if sol is None or sol.dia_181 is None:
        return Senal("AF", "Dia 540 (limite)", "PENDIENTE", None,
                     "No hay dia_181 base (AFP) para calcular el limite")
    return Senal("AF", "Dia 540 (limite)", "OK",
                 sol.dia_181 + timedelta(days=_DIAS_DIA_181_A_DIA_540))


def regla_ag_fecha_crie(row: dict, ctx: ContextoAuditoria) -> Senal:
    """AG: fecha_crie de solicitudes (AFP)."""
    sol = ctx.solicitudes_por_id.get(row.get("identificacion"))
    if sol is None or sol.fecha_crie is None:
        return Senal("AG", "Fecha CRIE", "PENDIENTE", None,
                     "El afiliado no esta en las solicitudes AFP, o no tiene fecha_crie")
    return Senal("AG", "Fecha CRIE", "OK", sol.fecha_crie)


def regla_ah_fi(row: dict, ctx: ContextoAuditoria) -> Senal:
    """AH (FI): {"identificacion": str, "fecha": date} -- tupla tipada, jamas texto."""
    ident, fecha = row.get("identificacion"), row.get("fecha_inicial")
    if ident is None or fecha is None:
        return Senal("AH", "FI", "PENDIENTE", None, "Falta identificacion o fecha_inicial")
    return Senal("AH", "FI", "OK", {"identificacion": ident, "fecha": fecha})


def regla_ai_ff(row: dict, ctx: ContextoAuditoria) -> Senal:
    """AI (FF): {"identificacion": str, "fecha": date} -- tupla tipada, jamas texto."""
    ident, fecha = row.get("identificacion"), row.get("fecha_final")
    if ident is None or fecha is None:
        return Senal("AI", "FF", "PENDIENTE", None, "Falta identificacion o fecha_final")
    return Senal("AI", "FF", "OK", {"identificacion": ident, "fecha": fecha})


def regla_aj_ci(row: dict, ctx: ContextoAuditoria) -> Senal:
    """AJ (CI): PENDIENTE fijo -- el libro externo [1]DATOS no fue entregado."""
    return Senal("AJ", "CI", "PENDIENTE", None,
                 "Depende del libro externo [1]DATOS, nunca entregado a este proyecto")


def regla_ak_cf(row: dict, ctx: ContextoAuditoria) -> Senal:
    """AK (CF): PENDIENTE fijo -- el libro externo [1]DATOS no fue entregado."""
    return Senal("AK", "CF", "PENDIENTE", None,
                 "Depende del libro externo [1]DATOS, nunca entregado a este proyecto")


def regla_al_comparacion_dia181(row: dict, ctx: ContextoAuditoria) -> Senal:
    """AL: OK si dia_181_arpis == dia_181_afp, si no ALERTA. No es la regla del CRIE."""
    arpis, afp = row.get("dia_181_arpis"), row.get("dia_181_afp")
    if arpis is None or afp is None:
        return Senal("AL", "Coincidencia dia 181 (Arpis vs AFP)", "PENDIENTE", None,
                     "Falta dia_181_arpis o dia_181_afp en la fila")
    if arpis == afp:
        return Senal("AL", "Coincidencia dia 181 (Arpis vs AFP)", "OK", True)
    return Senal("AL", "Coincidencia dia 181 (Arpis vs AFP)", "ALERTA", False,
                 f"dia_181_arpis={arpis!r} != dia_181_afp={afp!r}")


def regla_am_siniestro(row: dict, ctx: ContextoAuditoria) -> Senal:
    """AM: numero de siniestro del afiliado.

    Si hay 0 candidatos: PENDIENTE (sin siniestro asociado). Si hay 2+:
    PENDIENTE con `{"candidatos": [...], "seleccionado": None}` -- nunca se
    elige silenciosamente "el primero" (VLOOKUP original) ni "el mas
    reciente" (requerimiento de negocio sin reconciliar).
    """
    ident = row.get("identificacion")
    seleccionado, candidatos = _seleccionar_siniestro(ctx, ident)
    if not candidatos:
        return Senal("AM", "Siniestro", "PENDIENTE", None,
                     "El afiliado no tiene siniestro asociado")
    if seleccionado is None:
        return Senal("AM", "Siniestro", "PENDIENTE",
                     {"candidatos": candidatos, "seleccionado": None},
                     f"{len(candidatos)} siniestros candidatos para la misma identificacion; "
                     "requiere seleccion manual (primera coincidencia vs mas reciente sin resolver)")
    return Senal("AM", "Siniestro", "OK", seleccionado.numero_siniestro)


def regla_an_origen(row: dict, ctx: ContextoAuditoria) -> Senal:
    """AN: origen del siniestro seleccionado (ver AM para la seleccion).

    Con 2+ candidatos comparte la misma ambiguedad que AM (derivan de la
    misma seleccion), asi que expone el mismo payload
    `{"candidatos": [...], "seleccionado": None}` en vez de dejar `valor` en
    None -- para que un consumidor de la senal AN no tenga que cruzar con AM
    para ver los candidatos.
    """
    ident = row.get("identificacion")
    seleccionado, candidatos = _seleccionar_siniestro(ctx, ident)
    if not candidatos:
        return Senal("AN", "Origen del siniestro", "PENDIENTE", None,
                     "El afiliado no tiene siniestro asociado")
    if seleccionado is None:
        return Senal("AN", "Origen del siniestro", "PENDIENTE",
                     {"candidatos": candidatos, "seleccionado": None},
                     f"{len(candidatos)} siniestros candidatos sin seleccionar; ver AM")
    return Senal("AN", "Origen del siniestro", "OK", seleccionado.origen)


def regla_ao_estado(row: dict, ctx: ContextoAuditoria) -> Senal:
    """AO: estado del siniestro seleccionado (ver AM para la seleccion).

    Con 2+ candidatos comparte la misma ambiguedad que AM (derivan de la
    misma seleccion), asi que expone el mismo payload
    `{"candidatos": [...], "seleccionado": None}` en vez de dejar `valor` en
    None -- para que un consumidor de la senal AO no tenga que cruzar con AM
    para ver los candidatos.
    """
    ident = row.get("identificacion")
    seleccionado, candidatos = _seleccionar_siniestro(ctx, ident)
    if not candidatos:
        return Senal("AO", "Estado del siniestro", "PENDIENTE", None,
                     "El afiliado no tiene siniestro asociado")
    if seleccionado is None:
        return Senal("AO", "Estado del siniestro", "PENDIENTE",
                     {"candidatos": candidatos, "seleccionado": None},
                     f"{len(candidatos)} siniestros candidatos sin seleccionar; ver AM")
    return Senal("AO", "Estado del siniestro", "OK", seleccionado.estado)


def regla_ap_fecha_siniestro(row: dict, ctx: ContextoAuditoria) -> Senal:
    """AP: fechas del siniestro seleccionado, tipadas (aviso y siniestro).

    Con 2+ candidatos comparte la misma ambiguedad que AM (derivan de la
    misma seleccion), asi que expone el mismo payload
    `{"candidatos": [...], "seleccionado": None}` en vez de dejar `valor` en
    None -- para que un consumidor de la senal AP no tenga que cruzar con AM
    para ver los candidatos.
    """
    ident = row.get("identificacion")
    seleccionado, candidatos = _seleccionar_siniestro(ctx, ident)
    if not candidatos:
        return Senal("AP", "Fechas del siniestro", "PENDIENTE", None,
                     "El afiliado no tiene siniestro asociado")
    if seleccionado is None:
        return Senal("AP", "Fechas del siniestro", "PENDIENTE",
                     {"candidatos": candidatos, "seleccionado": None},
                     f"{len(candidatos)} siniestros candidatos sin seleccionar; ver AM")
    return Senal("AP", "Fechas del siniestro", "OK",
                 {"fecha_aviso": seleccionado.fecha_aviso,
                  "fecha_siniestro": seleccionado.fecha_siniestro})


def regla_aq_pago_ite(row: dict, ctx: ContextoAuditoria) -> Senal:
    """AQ: "SE REALIZA PAGO DE ITE DE {fecha_inicial} A {fecha_final}"."""
    fi, ff = row.get("fecha_inicial"), row.get("fecha_final")
    if fi is None or ff is None:
        return Senal("AQ", "Texto pago ITE", "PENDIENTE", None,
                     "Falta fecha_inicial o fecha_final")
    return Senal("AQ", "Texto pago ITE", "OK", f"SE REALIZA PAGO DE ITE DE {fi} A {ff}")


def regla_ar_siniestro_valor(row: dict, ctx: ContextoAuditoria) -> Senal:
    """AR: f"{numero_siniestro} {valor_afp}" -- campos propios de la fila."""
    numero, valor_afp = row.get("numero_siniestro"), row.get("valor_afp")
    if numero is None or valor_afp is None:
        return Senal("AR", "Siniestro + valor AFP", "PENDIENTE", None,
                     "Falta numero_siniestro o valor_afp en la fila")
    return Senal("AR", "Siniestro + valor AFP", "OK", f"{numero} {valor_afp}")


def regla_as_sipren(row: dict, ctx: ContextoAuditoria) -> Senal:
    """AS: INFO -- lo llena Sipren, fuera del alcance de este motor."""
    return Senal("AS", "Sipren", "INFO", None,
                 "Este campo lo diligencia Sipren; no se calcula en este motor")


def regla_at_doble_pago(row: dict, ctx: ContextoAuditoria) -> Senal:
    """AT: ALERTA si (identificacion, fecha_inicial) in ctx.ite_por_clave."""
    clave = (row.get("identificacion"), row.get("fecha_inicial"))
    if clave in ctx.ite_por_clave:
        return Senal("AT", "Posible doble pago", "ALERTA", True,
                     f"Ya existe un ITE pagado para identificacion={clave[0]!r}, fecha_inicial={clave[1]!r}")
    return Senal("AT", "Posible doble pago", "OK", False)


# ---------------------------------------------------------------------------
# Registro de reglas y orquestacion por fila
# ---------------------------------------------------------------------------

REGLAS_PREVISIONALES: list[tuple[str, str, Callable[[dict, ContextoAuditoria], Senal]]] = [
    ("AB", "Dia 181 (auditado)", regla_ab_observacion),
    ("AC", "Aval", regla_ac_aval),
    ("AD", "Filas repetidas en el lote", regla_ad_repetidas),
    ("AE", "Dia 181 (AFP)", regla_ae_dia_181),
    ("AF", "Dia 540 (limite)", regla_af_dia_540),
    ("AG", "Fecha CRIE", regla_ag_fecha_crie),
    ("AH", "FI", regla_ah_fi),
    ("AI", "FF", regla_ai_ff),
    ("AJ", "CI", regla_aj_ci),
    ("AK", "CF", regla_ak_cf),
    ("AL", "Coincidencia dia 181 (Arpis vs AFP)", regla_al_comparacion_dia181),
    ("AM", "Siniestro", regla_am_siniestro),
    ("AN", "Origen del siniestro", regla_an_origen),
    ("AO", "Estado del siniestro", regla_ao_estado),
    ("AP", "Fechas del siniestro", regla_ap_fecha_siniestro),
    ("AQ", "Texto pago ITE", regla_aq_pago_ite),
    ("AR", "Siniestro + valor AFP", regla_ar_siniestro_valor),
    ("AS", "Sipren", regla_as_sipren),
    ("AT", "Posible doble pago", regla_at_doble_pago),
]


def evaluar_todas(row: dict, ctx: ContextoAuditoria) -> list[Senal]:
    """Corre las 19 reglas AB-AT sobre una fila, en orden de columna."""
    return [funcion(row, ctx) for _codigo, _nombre, funcion in REGLAS_PREVISIONALES]


# ---------------------------------------------------------------------------
# Helpers de lote: agrupacion y encadenamiento (usados para construir ctx)
# ---------------------------------------------------------------------------


def agrupar_repetidas(rows: list[dict]) -> dict[tuple[str, date], list[str]]:
    """Agrupa las filas del lote por (identificacion, fecha_inicial).

    Independiente del orden de entrada: el resultado solo depende del
    conjunto de filas, no de en que orden llegaron. Respalda la regla AD.
    Cada fila debe traer "id" (identificador unico de la fila dentro del
    lote), "identificacion" y "fecha_inicial".

    Igual que las 19 `regla_xx_*`, lee con `.get(...)` en vez de indexar
    directo: una fila mal formada (le falta "id", "identificacion" o
    "fecha_inicial") no puede agruparse y simplemente se excluye del
    resultado -- nunca aborta el lote completo con un KeyError.
    """
    grupos: dict[tuple[str, date], list[str]] = {}
    for row in rows:
        row_id = row.get("id")
        identificacion = row.get("identificacion")
        fecha_inicial = row.get("fecha_inicial")
        if row_id is None or identificacion is None or fecha_inicial is None:
            continue
        clave = (identificacion, fecha_inicial)
        grupos.setdefault(clave, []).append(row_id)
    return grupos


def encadenar_prorrogas(rows: list[dict]) -> dict[str, str | None]:
    """Encadena cada fila de prorroga/tutela/ajuste con la incapacidad previa.

    Para cada fila cuyo "tipo_ingreso" esta en {PRORROGA, TUTELA_P, AJUSTE},
    busca -- entre las demas filas del mismo afiliado ("identificacion") --
    la incapacidad inmediatamente anterior: la que tiene la mayor
    "fecha_final" estrictamente menor a la "fecha_inicial" de la fila
    actual. Si no existe ninguna (fila huerfana, sin predecesora en el
    lote), la mapea a None.

    Cada fila debe traer "id", "identificacion", "tipo_ingreso",
    "fecha_inicial" y "fecha_final".

    Igual que las 19 `regla_xx_*`, lee con `.get(...)` en vez de indexar
    directo. Una fila candidata a encadenarse (o una fila candidata a ser
    predecesora) que le falte "id", "identificacion" o "fecha_inicial"
    (para la fila actual) simplemente se excluye de la computacion -- nunca
    aborta el lote completo con un KeyError.
    """
    encadenadas: dict[str, str | None] = {}
    for row in rows:
        if row.get("tipo_ingreso") not in _TIPOS_ENCADENABLES:
            continue
        row_id = row.get("id")
        ident = row.get("identificacion")
        fecha_inicial = row.get("fecha_inicial")
        if row_id is None or ident is None or fecha_inicial is None:
            continue
        mejor_id: str | None = None
        mejor_fecha_final: date | None = None
        for otra in rows:
            otra_id = otra.get("id")
            otra_ident = otra.get("identificacion")
            if otra_id is None or otra_id == row_id or otra_ident != ident:
                continue
            fecha_final_otra = otra.get("fecha_final")
            if fecha_final_otra is None or fecha_final_otra >= fecha_inicial:
                continue
            if mejor_fecha_final is None or fecha_final_otra > mejor_fecha_final:
                mejor_fecha_final = fecha_final_otra
                mejor_id = otra_id
        encadenadas[row_id] = mejor_id
    return encadenadas

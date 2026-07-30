"""
Exportador ARPIS: agrupacion de salarios, normalizacion de radicado,
mapeo de tipo de ingreso y construccion del libro Excel de cargue.

El motor legado (macro de Excel) que este modulo reemplaza tenia un bug
critico: cuando una incapacidad cambiaba de salario mas de 3 veces durante
su duracion, la macro metia silenciosamente los dias sobrantes en el tercer
grupo de salario, perdiendo informacion sin avisar a nadie. Este modulo NO
replica ese comportamiento -- `agrupar_salarios` levanta
`DemasiadosGruposError` en vez de truncar. La decision de que hacer con esa
alerta (bloquear el lote, marcarlo para revision manual, etc.) es de una
capa posterior; esta funcion solo detecta y avisa.
"""
import io
from dataclasses import dataclass
from decimal import Decimal

from openpyxl import Workbook

from app.services.previsionales.segmentacion import Segmento

# ---------------------------------------------------------------------------
# Agrupacion de salarios
# ---------------------------------------------------------------------------

# ARPIS solo tiene 3 columnas de salario/dias (K-M / N-P). Mas de 3 grupos
# es la senal de alerta que la macro original ocultaba.
_MAX_GRUPOS_SALARIO = 3


@dataclass(frozen=True)
class GrupoSalario:
    """Un tramo de segmentos consecutivos con el mismo salario.

    `dias` es la SUMA de `dias` de todos los segmentos del tramo (no el
    numero de segmentos ni de meses).
    """

    salario: Decimal
    dias: int
    segmentos: list[Segmento]


class DemasiadosGruposError(ValueError):
    """Mas de 3 grupos de salario distintos y consecutivos en la incapacidad.

    La macro de Excel original truncaba silenciosamente los grupos 4+ dentro
    del grupo 3, perdiendo dias. Este error existe para que eso nunca vuelva
    a pasar sin que alguien se entere.
    """


def agrupar_salarios(pares: list[tuple[Segmento, Decimal]]) -> list[GrupoSalario]:
    """Agrupa segmentos en tramos consecutivos con el mismo salario.

    Args:
        pares: lista ordenada de (Segmento, salario) -- un par por segmento,
            en el mismo orden que produce `segmentar`.

    Returns:
        Lista de GrupoSalario, en orden. El salario de cada grupo cambia
        respecto al anterior (nunca dos grupos consecutivos con el mismo
        salario).

    Raises:
        DemasiadosGruposError: si resultan mas de 3 grupos.
    """
    if not pares:
        return []

    grupos: list[GrupoSalario] = []
    salario_actual = pares[0][1]
    segmentos_actuales = [pares[0][0]]

    for segmento, salario in pares[1:]:
        if salario == salario_actual:
            segmentos_actuales.append(segmento)
            continue
        grupos.append(
            GrupoSalario(
                salario=salario_actual,
                dias=sum(s.dias for s in segmentos_actuales),
                segmentos=segmentos_actuales,
            )
        )
        salario_actual = salario
        segmentos_actuales = [segmento]

    grupos.append(
        GrupoSalario(
            salario=salario_actual,
            dias=sum(s.dias for s in segmentos_actuales),
            segmentos=segmentos_actuales,
        )
    )

    if len(grupos) > _MAX_GRUPOS_SALARIO:
        raise DemasiadosGruposError(
            f"{len(grupos)} grupos de salario detectados (maximo {_MAX_GRUPOS_SALARIO}); "
            "la macro original los perdia metiendolos callados en el grupo 3"
        )

    return grupos


# ---------------------------------------------------------------------------
# Normalizacion de radicado
# ---------------------------------------------------------------------------

_MARCADOR_RAD_NO = "Rad No. "
_LONGITUD_QUE_RECIBE_CERO = 15


def _aplicar_padding(valor: str) -> str:
    if len(valor) == _LONGITUD_QUE_RECIBE_CERO:
        return "0" + valor
    return valor


def normalizar_radicado(radicado: str, observacion: str | None) -> str:
    """Normaliza un numero de radicado ARPIS.

    Si `radicado` son puros digitos (ignorando espacios en blanco al inicio
    o al final), se usa tal cual (salvo padding de 15->16 digitos). Si no,
    se extrae de `observacion` el texto que sigue al literal "Rad No. "
    hasta el siguiente espacio, y se le aplica la misma regla de padding --
    pero solo si ese texto extraido tambien es puramente numerico. Este
    modulo existe para fallar ruidosamente en vez de devolver basura (ver
    docstring del modulo); un valor no numerico extraido de la observacion
    (p.ej. "ERROR" en "algo Rad No. ERROR mas texto") NO se retorna
    silenciosamente -- se levanta ValueError.

    Raises:
        ValueError: si `radicado` no es numerico y no se encuentra el patron
            "Rad No. " en `observacion` (incluyendo `observacion is None`),
            o si el valor encontrado tras el patron no es puramente
            numerico.
    """
    if radicado:
        radicado_normalizado = radicado.strip()
        if radicado_normalizado.isdigit():
            return _aplicar_padding(radicado_normalizado)

    if observacion is not None:
        idx = observacion.find(_MARCADOR_RAD_NO)
        if idx != -1:
            resto = observacion[idx + len(_MARCADOR_RAD_NO):]
            extraido = resto.split(None, 1)[0] if resto.strip() else ""
            if extraido:
                if not extraido.isdigit():
                    raise ValueError(
                        f"Valor extraido de observacion tras el patron "
                        f"{_MARCADOR_RAD_NO!r} no es numerico: {extraido!r} "
                        f"(observacion={observacion!r})"
                    )
                return _aplicar_padding(extraido)

    raise ValueError(
        f"Radicado no numerico ({radicado!r}) y no se encontro el patron "
        f"{_MARCADOR_RAD_NO!r} en la observacion ({observacion!r})"
    )


# ---------------------------------------------------------------------------
# Mapeo de tipo de ingreso
# ---------------------------------------------------------------------------

# (codigo_arpis, es_ajuste, es_tutela)
_TIPO_INGRESO_MAP: dict[str, tuple[int, bool, bool]] = {
    "INICIAL": (1, False, False),
    "TUTELA_I": (1, False, True),
    "PRORROGA": (2, False, False),
    "TUTELA_P": (2, False, True),
    "AJUSTE": (2, True, False),
}


def mapear_tipo_ingreso(tipo: str) -> tuple[int, bool, bool]:
    """Mapea el tipo de ingreso de negocio al codigo binario ARPIS.

    Returns:
        (codigo_arpis, es_ajuste, es_tutela)

    Raises:
        ValueError: tipo no reconocido ("CASO NO DEFINIDO" en el sistema legado).
    """
    try:
        return _TIPO_INGRESO_MAP[tipo]
    except KeyError:
        raise ValueError(
            f"CASO NO DEFINIDO: tipo_ingreso {tipo!r} no es un valor reconocido "
            f"(esperado uno de {sorted(_TIPO_INGRESO_MAP)})"
        )


# ---------------------------------------------------------------------------
# Construccion del libro ARPIS
# ---------------------------------------------------------------------------

_TITULO_FILA_1 = "Campos de información archivo de cargue:"
_TITULO_FILA_2 = "Detalle solicitud de Auditoría - Incapacidades"

_ENCABEZADOS = [
    "Tipo Identificación",
    "No. Identificación",
    "Dia 181",
    "No. Radicado",
    "Fecha radicación AFP",
    "Fecha radicación Alfa",
    "Tipo Ingreso",
    "Fecha inicial incapacidad",
    "Fecha final incapacidad",
    "Ajuste",
    "Salario 1",
    "Salario 2",
    "Salario 3",
    "Días incapacidad 1",
    "Días incapacidad 2",
    "Días incapacidad 3",
    "Observación AFP",
    "CIE10",
    "Causal excepción",
    "Observación causal",
]

_FILA_ENCABEZADO = 3
_FILA_PRIMER_DATO = 4


def _valor_grupo(grupos: list[GrupoSalario], indice: int, campo: str):
    if indice >= len(grupos):
        return None
    return getattr(grupos[indice], campo)


def construir_libro_arpis(filas: list[dict]) -> bytes:
    """Construye el libro Excel de cargue ARPIS.

    Cada `fila` es un dict con el registro ya procesado de una incapacidad:
    - tipo_identificacion, identificacion, dia_181, radicado
    - fecha_radicacion_afp, fecha_radicacion_alfa
    - tipo_ingreso (string crudo: INICIAL/TUTELA_I/PRORROGA/TUTELA_P/AJUSTE)
    - fecha_inicial, fecha_final
    - grupos_salario: list[GrupoSalario] (salida de `agrupar_salarios`, max 3)
    - observacion, cie10_list (list[str], se usa solo el primero)
    - observacion_causal

    El codigo ARPIS de tipo de ingreso, el flag de ajuste y el flag de
    tutela (causal excepcion) se derivan aqui mismo via `mapear_tipo_ingreso`
    a partir de `tipo_ingreso` -- no se leen como campos separados en `fila`,
    para no tener dos fuentes de verdad que puedan desincronizarse.

    Returns:
        Bytes del archivo .xlsx (fila 1-2 titulos, fila 3 encabezado,
        datos desde fila 4).
    """
    wb = Workbook()
    ws = wb.active
    ws.title = "Cargue ARPIS"

    ws["A1"] = _TITULO_FILA_1
    ws["A2"] = _TITULO_FILA_2
    for col_idx, encabezado in enumerate(_ENCABEZADOS, start=1):
        ws.cell(row=_FILA_ENCABEZADO, column=col_idx, value=encabezado)

    fila_excel = _FILA_PRIMER_DATO
    for fila in filas:
        codigo_ingreso, es_ajuste, es_tutela = mapear_tipo_ingreso(fila.get("tipo_ingreso") or "")
        grupos = fila.get("grupos_salario") or []
        cie10_list = fila.get("cie10_list") or []

        valores = [
            fila.get("tipo_identificacion"),                       # A
            fila.get("identificacion"),                            # B
            fila.get("dia_181"),                                   # C
            fila.get("radicado"),                                  # D
            fila.get("fecha_radicacion_afp"),                      # E
            fila.get("fecha_radicacion_alfa"),                     # F
            codigo_ingreso,                                        # G
            fila.get("fecha_inicial"),                             # H
            fila.get("fecha_final"),                                # I
            1 if es_ajuste else None,                              # J
            _valor_grupo(grupos, 0, "salario"),                    # K
            _valor_grupo(grupos, 1, "salario"),                    # L
            _valor_grupo(grupos, 2, "salario"),                    # M
            _valor_grupo(grupos, 0, "dias"),                       # N
            _valor_grupo(grupos, 1, "dias"),                       # O
            _valor_grupo(grupos, 2, "dias"),                       # P
            fila.get("observacion"),                               # Q
            cie10_list[0] if cie10_list else None,                 # R
            1 if es_tutela else None,                              # S
            fila.get("observacion_causal"),                        # T
        ]
        for col_idx, valor in enumerate(valores, start=1):
            ws.cell(row=fila_excel, column=col_idx, value=valor)
        fila_excel += 1

    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()

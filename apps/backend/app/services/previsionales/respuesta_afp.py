"""
Generador del excel de respuesta al fondo (AFP) -- Task 3.4, segunda mitad.

Spec (`docs/especificaciones/modulo_previsionales.md`, §4.5): "se devuelve
el mismo excel del lote sin modificaciones, agregando solo dos columnas"
(AVAL, OBSERVACION). Por eso `generar_respuesta` NUNCA reconstruye el libro
desde cero -- abre los bytes originales tal como se archivaron en storage
(`lote_service.cargar_lote`, `metadata_["archivo_original_path"]`) con
`data_only=False` (conserva fórmulas/formato) y solo AGREGA celdas al final
de las columnas existentes.

-----------------------------------------------------------------------
RIESGO DE EMPAREJAMIENTO FILA-A-FILA (leer antes de tocar este archivo)
-----------------------------------------------------------------------
`IncapacidadPrevisional` (Tasks 2.1/3.1) NO tiene una columna que guarde el
número de fila original del excel del que se cargó. Emparejar cada registro
persistido con SU fila exacta del worksheet original por POSICIÓN (fila N
del excel -> fila N-ésima persistida) sería un match FALSO en cuanto
cualquier fila se hubiera descartado durante la carga sin persistir ningún
registro (`lote_service._persistir_fila` devuelve `None` -- y por lo tanto
NO cuenta como fila persistida -- cuando un campo de identidad excede su
longitud de columna, o cuando falla incluso el reintento degradado; ver
docstring de `LotePrevisionalService._persistir_fila`). Con esas filas
"agujereadas", un match por posición desalinearía TODAS las filas
siguientes silenciosamente -- exactamente el tipo de error que este módulo
existe para evitar (ver CLAUDE.md, ver `auditoria_rules.py`).

En vez de eso, este módulo empareja por CONTENIDO: `(identificacion,
fecha_inicial)`. Por qué esa clave es segura -- `agrupar_repetidas`
(`auditoria_rules.py`, usada por `lote_service.cargar_lote` para poblar
`es_duplicado_interno`) agrupa las filas EXACTAMENTE por esa misma clave, y
`lote_service` marca TODAS las filas de un grupo con 2+ como
`es_duplicado_interno=True` -- nunca elige "la original". Como consecuencia
directa: entre las incapacidades NO marcadas como duplicado interno de un
mismo lote, `(identificacion, fecha_inicial)` es garantizado único. Filtrar
por `es_duplicado_interno=False` (mismo filtro `{"repetidas": False}` que ya
usa `incapacidad_previsional_repository.get_by_lote`) y re-derivar esa
misma clave de cada fila del worksheet (con los mismos parsers tolerantes
de `excel_common.py` que usó la carga original) da un emparejamiento
robusto frente a filas descartadas, SIN inventar un match por posición.

Riesgo residual que SÍ queda (documentado también en el reporte de la
tarea, no silenciado): si una fila del worksheet no puede re-parsear
identificación/fecha_inicial de forma idéntica a como lo hizo la carga
original (p.ej. el archivo se editó a mano entre la carga y la generación
de la respuesta), esa fila del worksheet simplemente no encuentra match y
se deja SIN AVAL/OBSERVACION -- nunca se le atribuye el resultado de otra
fila. Es la alternativa "fallar silenciosamente hacia 'sin dato'" en vez de
"adivinar", coherente con el resto del módulo.
-----------------------------------------------------------------------

Otros judgment calls, documentados también en el reporte de la tarea:

- `aval is None` (incapacidad aún no auditada): la fila del worksheet
  correspondiente se deja SIN escribir AVAL/OBSERVACION (blank), no se
  inventa un tercer valor tipo "PENDIENTE" que el spec no pidió.
- Columna OBSERVACION cuando AVAL="SI": se reutiliza el texto YA
  CALCULADO por la señal persistida `SenalAuditoriaPrevisional(codigo="AB")`
  (Task 1.4/3.3: `"DIA 181 " + dia_181_alfa`) -- si esa señal no existe
  (el lote nunca se auditó) o sigue en PENDIENTE (`valor` no es `str`, aún
  sin `dia_181_alfa`), la observación queda en blanco -- no se recalcula
  aquí ni se inventa un texto. NUNCA se usa `senal.detalle` como fallback:
  para `codigo="AB"`, `detalle` solo trae el mensaje interno de depuración
  de la rama PENDIENTE (`regla_ab_observacion`), nunca el texto "DIA 181
  ..." reutilizable (fix-round de esta tarea; ese fallback filtraba texto
  interno hacia el excel que se le envía al fondo).
  Resuelto con UN solo query batch para todas las incapacidades
  avaladas-SI del lote (`_indice_observaciones_avaladas` ->
  `senal_auditoria_previsional_repository.get_by_incapacidades`), no un
  query por fila (fix-round: N+1 detectado en revisión).

Gap preexistente y conocido (NO se arregla en esta tarea, ver brief):
`storage_backend.get_file_content(...)` es un método específico de
`FileSystemStorage` (`app/core/storage_core/filesystem.py`), NO forma
parte de la interfaz abstracta `StorageBackend`
(`app/core/storage_core/base.py`) ni lo implementa `MinIOStorage`. Este
repo usa filesystem como backend por defecto (ver CLAUDE.md); si algún día
se configura `STORAGE_BACKEND=minio`, esta llamada rompe en tiempo de
ejecución con `AttributeError`. Arreglarlo implicaría agregar el método
abstracto + su implementación en MinIOStorage -- fuera de alcance aquí.
"""
import io
from typing import Any
from uuid import UUID

import openpyxl
from openpyxl.utils import column_index_from_string
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, NotFoundException
from app.core.storage_core import storage_backend
from app.db.repositories.previsionales import (
    incapacidad_previsional_repository,
    lote_previsional_repository,
    senal_auditoria_previsional_repository,
)
from app.services.previsionales.excel_common import CeldaInvalidaError, es_vacio, parse_fecha, texto
from app.utils.enums import AvalPrevisional

_HOJA_FORMALIZACION = "FORMALIZACION"
_COL_IDENTIFICACION = "B"
_COL_FECHA_INICIAL = "F"
_FILA_ENCABEZADO = 1
_PRIMERA_FILA_DATOS = 2
_CODIGO_SENAL_AB = "AB"

_IDX_IDENTIFICACION = column_index_from_string(_COL_IDENTIFICACION)
_IDX_FECHA_INICIAL = column_index_from_string(_COL_FECHA_INICIAL)


def _construir_indice_por_clave(incapacidades: list) -> dict[tuple[str, Any], Any]:
    """
    `(identificacion, fecha_inicial)` -> `IncapacidadPrevisional`, solo para
    incapacidades YA filtradas a `es_duplicado_interno=False` -- ver la nota
    de riesgo de emparejamiento en el docstring del módulo para el porqué
    esta clave es segura (única) en ese subconjunto.
    """
    indice: dict[tuple[str, Any], Any] = {}
    for inc in incapacidades:
        if inc.identificacion is None or inc.fecha_inicial is None:
            continue
        indice[(inc.identificacion, inc.fecha_inicial)] = inc
    return indice


async def _indice_observaciones_avaladas(
    db: AsyncSession, incapacidad_ids: list[UUID]
) -> dict[UUID, str | None]:
    """
    incapacidad_id -> texto de OBSERVACION cuando AVAL="SI", para TODAS las
    incapacidades avaladas del lote, resuelto con UNA sola query batch (fix-
    round: antes esto era `senal_auditoria_previsional_repository.
    get_by_incapacidad` -- una query por fila avalada-SI dentro del loop,
    el mismo patrón N+1 que CLAUDE.md marca como pecado capital del repo).

    Reutiliza el texto YA CALCULADO por la señal persistida `codigo="AB"`
    (`"DIA 181 " + dia_181_alfa`, ver `auditoria_rules.regla_ab_observacion`)
    -- nunca se recalcula aquí. El valor del dict es `None` si la señal no
    existe (lote nunca auditado) o sigue PENDIENTE (`valor` no es un `str`
    porque `dia_181_alfa` aún no se definió por el auditor).

    IMPORTANTE (fix-round): NO se usa `senal_ab.detalle` como fallback. Para
    `codigo="AB"`, `detalle` solo se puebla en la rama PENDIENTE de
    `regla_ab_observacion` con un mensaje interno de depuración ("Aun no hay
    dia_181_alfa calculado por el auditor") -- nunca con el texto "DIA 181
    ..." reutilizable, que SOLO vive en `valor` en la rama OK. Devolver
    `detalle` filtraba ese texto interno hacia el excel que se le envía al
    fondo.
    """
    senales_por_incapacidad = await senal_auditoria_previsional_repository.get_by_incapacidades(
        db, incapacidad_ids
    )
    indice: dict[UUID, str | None] = {}
    for incapacidad_id, senales in senales_por_incapacidad.items():
        senal_ab = next((s for s in senales if s.codigo == _CODIGO_SENAL_AB), None)
        indice[incapacidad_id] = (
            senal_ab.valor if senal_ab is not None and isinstance(senal_ab.valor, str) else None
        )
    return indice


async def generar_respuesta(db: AsyncSession, lote_id: UUID) -> bytes:
    """Recupera el excel original del lote desde storage, lo abre preservando formato
    (data_only=False), y le agrega exactamente dos columnas nuevas: AVAL y OBSERVACION.
    Excluye las filas es_duplicado_interno=True (duplicados internos no van en la
    respuesta al fondo). Retorna los bytes del libro resultante.

    Raises:
        NotFoundException: el lote no existe, o su archivo original ya no
            existe físicamente en storage.
        BadRequestException: el lote no tiene archivo original archivado
            (`metadata_["archivo_original_path"]` ausente), o ese archivo
            no es un excel válido / no trae la hoja FORMALIZACION.
    """
    lote = await lote_previsional_repository.get_by_id(db, lote_id)
    if lote is None:
        raise NotFoundException(f"LotePrevisional {lote_id} no encontrado")

    ruta_original = (lote.metadata_ or {}).get("archivo_original_path")
    if not ruta_original:
        raise BadRequestException(
            f"El lote {lote_id} no tiene un archivo original archivado en storage "
            "(metadata_['archivo_original_path'] ausente) -- no se puede generar la respuesta"
        )

    # Ver nota de "Gap preexistente y conocido" en el docstring del módulo:
    # `get_file_content` no es parte de la interfaz abstracta `StorageBackend`.
    original_bytes = storage_backend.get_file_content(ruta_original)  # type: ignore[attr-defined]
    if original_bytes is None:
        raise NotFoundException(
            f"El archivo original del lote {lote_id} no existe en storage (ruta: {ruta_original!r})"
        )

    try:
        wb = openpyxl.load_workbook(io.BytesIO(original_bytes), data_only=False)
    except Exception as exc:
        raise BadRequestException(
            f"El archivo original del lote {lote_id} no es un excel válido: {exc}"
        ) from exc

    if _HOJA_FORMALIZACION not in wb.sheetnames:
        raise BadRequestException(
            f"El archivo original del lote {lote_id} no trae la hoja {_HOJA_FORMALIZACION!r}"
        )
    ws = wb[_HOJA_FORMALIZACION]

    incapacidades = await incapacidad_previsional_repository.get_by_lote(
        db, lote_id, {"repetidas": False}
    )
    indice_por_clave = _construir_indice_por_clave(incapacidades)

    # Batch-load de las señales AB de TODAS las incapacidades avaladas-SI del
    # lote en UNA query (fix-round: evita el N+1 que había antes, un query
    # por fila dentro del loop -- ver docstring de `_indice_observaciones_avaladas`).
    ids_avaladas_si = [
        inc.id for inc in incapacidades if inc.aval == AvalPrevisional.SI.value
    ]
    indice_observaciones = await _indice_observaciones_avaladas(db, ids_avaladas_si)

    col_aval = ws.max_column + 1
    col_obs = col_aval + 1
    ws.cell(row=_FILA_ENCABEZADO, column=col_aval, value="AVAL")
    ws.cell(row=_FILA_ENCABEZADO, column=col_obs, value="OBSERVACION")

    max_row = ws.max_row or 1
    for row_num in range(_PRIMERA_FILA_DATOS, max_row + 1):
        identificacion_raw = ws.cell(row=row_num, column=_IDX_IDENTIFICACION).value
        fecha_inicial_raw = ws.cell(row=row_num, column=_IDX_FECHA_INICIAL).value

        if es_vacio(identificacion_raw) and es_vacio(fecha_inicial_raw):
            continue  # fila vacía -- misma convención que lote_service

        try:
            identificacion = texto(identificacion_raw)
            fecha_inicial = parse_fecha(fecha_inicial_raw) if not es_vacio(fecha_inicial_raw) else None
        except CeldaInvalidaError:
            # No se puede re-derivar la clave de match -- se deja la fila
            # intacta (ver riesgo residual en el docstring del módulo).
            continue

        if identificacion is None or fecha_inicial is None:
            continue

        inc = indice_por_clave.get((identificacion, fecha_inicial))
        if inc is None:
            # No persistida (descartada en la carga) o duplicado interno --
            # se deja la fila intacta, sin AVAL/OBSERVACION.
            continue

        if inc.aval == AvalPrevisional.SI.value:
            aval_texto = "SI"
            observacion_texto = indice_observaciones.get(inc.id)
        elif inc.aval == AvalPrevisional.NO.value:
            aval_texto = "NO"
            observacion_texto = inc.motivo_no_aval
        else:
            # aval aún no definido -- se deja la fila sin AVAL/OBSERVACION
            # (blank), no se inventa un tercer valor (ver docstring del módulo).
            continue

        ws.cell(row=row_num, column=col_aval, value=aval_texto)
        ws.cell(row=row_num, column=col_obs, value=observacion_texto)

    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()

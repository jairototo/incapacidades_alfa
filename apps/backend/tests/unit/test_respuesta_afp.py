"""
Tests para `respuesta_afp.py` (Task 3.4, segunda mitad) -- generador del
excel de respuesta al fondo (AVAL + OBSERVACION agregadas al libro original).

Usa `db_session` (Postgres async real) y `storage_backend` REAL (filesystem,
igual que `test_lote_service.py` -- no se mockea, el contenedor de test ya
corre con `STORAGE_BACKEND=filesystem`): se construye un workbook sintético
en memoria con la forma mínima de la hoja FORMALIZACION, se sube vía
`storage_backend.upload_file` (mismo camino que usa `lote_service.cargar_lote`
para archivar el original), y se referencia desde
`lote.metadata_["archivo_original_path"]`.
"""
import io
from datetime import date

import openpyxl
import pytest
import pytest_asyncio
from openpyxl import Workbook

from app.core.exceptions import BadRequestException, NotFoundException
from app.core.storage_core import storage_backend
from app.models.previsionales.incapacidad_previsional import IncapacidadPrevisional
from app.models.previsionales.lote_previsional import LotePrevisional
from app.models.previsionales.senal_auditoria_previsional import SenalAuditoriaPrevisional
from app.services.previsionales.respuesta_afp import generar_respuesta

_ENCABEZADO_FORMALIZACION = [
    "Junio",
    "# IDENTIFICACION",
    "RADICADO",
    "FECHA RADICACION AFP",
    "TIPO INGRESO",
    "FECHA_INICIAL",
    "FECHA_FINAL",
    "No. DIAS",
]

# (identificacion, radicado, fecha_inicial, fecha_final) -- suficiente para
# el match por (identificacion, fecha_inicial); las demas columnas son
# irrelevantes para este test pero se dejan para simular un libro real.
_FILAS = [
    ("1000000001", "R-001", date(2026, 3, 1), date(2026, 3, 15)),  # avalada SI
    ("1000000002", "R-002", date(2026, 3, 1), date(2026, 3, 10)),  # avalada NO
    ("1000000003", "R-003", date(2026, 3, 1), date(2026, 3, 5)),  # duplicado interno
    ("1000000004", "R-004", date(2026, 3, 1), date(2026, 3, 8)),  # sin auditar (aval None)
]


def _construir_workbook_original() -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "FORMALIZACION"
    ws.append(_ENCABEZADO_FORMALIZACION)
    for identificacion, radicado, f_ini, f_fin in _FILAS:
        ws.append([None, identificacion, radicado, None, "INICIAL", f_ini, f_fin, None])
    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


@pytest_asyncio.fixture
async def lote_con_respuesta_pendiente(db_session):
    original_bytes = _construir_workbook_original()
    ruta_storage, _md5, _sha256, _size = storage_backend.upload_file(
        file_data=io.BytesIO(original_bytes),
        file_name="RADICADOS_TEST_RESPUESTA.xlsx",
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        folder="lotes_previsionales",
    )

    lote = LotePrevisional(
        nombre_archivo="RADICADOS_TEST_RESPUESTA.xlsx",
        metadata_={"archivo_original_path": ruta_storage},
    )
    db_session.add(lote)
    await db_session.flush()

    inc_si = IncapacidadPrevisional(
        lote_id=lote.id,
        identificacion="1000000001",
        radicado="R-001",
        fecha_inicial=date(2026, 3, 1),
        fecha_final=date(2026, 3, 15),
        aval="SI",
        dia_181_alfa=date(2026, 8, 1),
        es_duplicado_interno=False,
    )
    inc_no = IncapacidadPrevisional(
        lote_id=lote.id,
        identificacion="1000000002",
        radicado="R-002",
        fecha_inicial=date(2026, 3, 1),
        fecha_final=date(2026, 3, 10),
        aval="NO",
        motivo_no_aval="Diagnostico no compatible con incapacidad prolongada",
        es_duplicado_interno=False,
    )
    inc_duplicada = IncapacidadPrevisional(
        lote_id=lote.id,
        identificacion="1000000003",
        radicado="R-003",
        fecha_inicial=date(2026, 3, 1),
        fecha_final=date(2026, 3, 5),
        aval="SI",  # aunque tenga aval, es_duplicado_interno la excluye igual
        es_duplicado_interno=True,
    )
    inc_sin_auditar = IncapacidadPrevisional(
        lote_id=lote.id,
        identificacion="1000000004",
        radicado="R-004",
        fecha_inicial=date(2026, 3, 1),
        fecha_final=date(2026, 3, 8),
        aval=None,
        es_duplicado_interno=False,
    )
    db_session.add_all([inc_si, inc_no, inc_duplicada, inc_sin_auditar])
    await db_session.flush()

    senal_ab = SenalAuditoriaPrevisional(
        incapacidad_previsional_id=inc_si.id,
        codigo="AB",
        nombre="Dia 181 (auditado)",
        estado="OK",
        valor="DIA 181 2026-08-01",
        detalle=None,
    )
    db_session.add(senal_ab)
    await db_session.commit()

    return {
        "lote": lote,
        "inc_si": inc_si,
        "inc_no": inc_no,
        "inc_duplicada": inc_duplicada,
        "inc_sin_auditar": inc_sin_auditar,
    }


def _leer_fila_por_identificacion(ws, identificacion: str) -> dict:
    encabezados = [c.value for c in ws[1]]
    idx_ident = encabezados.index("# IDENTIFICACION") + 1
    idx_aval = len(encabezados) - 1  # AVAL fue agregada como penúltima columna
    idx_obs = len(encabezados)  # OBSERVACION es la última
    for row in ws.iter_rows(min_row=2):
        if row[idx_ident - 1].value == identificacion:
            return {
                "aval": row[idx_aval - 1].value,
                "observacion": row[idx_obs - 1].value,
                "radicado": row[2].value,  # columna original C, sin modificar
            }
    raise AssertionError(f"Fila con identificacion={identificacion!r} no encontrada")


@pytest.mark.asyncio
async def test_agrega_columnas_aval_y_observacion_al_encabezado(db_session, lote_con_respuesta_pendiente):
    lote = lote_con_respuesta_pendiente["lote"]

    resultado_bytes = await generar_respuesta(db_session, lote.id)

    wb = openpyxl.load_workbook(io.BytesIO(resultado_bytes))
    ws = wb["FORMALIZACION"]
    encabezados = [c.value for c in ws[1]]
    assert encabezados[-2:] == ["AVAL", "OBSERVACION"]
    # Las columnas originales no se tocaron.
    assert encabezados[:8] == _ENCABEZADO_FORMALIZACION


@pytest.mark.asyncio
async def test_fila_avalada_si_trae_aval_y_observacion_desde_senal_ab(
    db_session, lote_con_respuesta_pendiente
):
    lote = lote_con_respuesta_pendiente["lote"]

    resultado_bytes = await generar_respuesta(db_session, lote.id)

    wb = openpyxl.load_workbook(io.BytesIO(resultado_bytes))
    ws = wb["FORMALIZACION"]
    fila = _leer_fila_por_identificacion(ws, "1000000001")
    assert fila["aval"] == "SI"
    assert fila["observacion"] == "DIA 181 2026-08-01"
    assert fila["radicado"] == "R-001"  # dato original intacto


@pytest.mark.asyncio
async def test_fila_avalada_no_trae_aval_y_motivo_no_aval(db_session, lote_con_respuesta_pendiente):
    lote = lote_con_respuesta_pendiente["lote"]

    resultado_bytes = await generar_respuesta(db_session, lote.id)

    wb = openpyxl.load_workbook(io.BytesIO(resultado_bytes))
    ws = wb["FORMALIZACION"]
    fila = _leer_fila_por_identificacion(ws, "1000000002")
    assert fila["aval"] == "NO"
    assert fila["observacion"] == "Diagnostico no compatible con incapacidad prolongada"


@pytest.mark.asyncio
async def test_fila_duplicado_interno_queda_sin_aval_ni_observacion(
    db_session, lote_con_respuesta_pendiente
):
    lote = lote_con_respuesta_pendiente["lote"]

    resultado_bytes = await generar_respuesta(db_session, lote.id)

    wb = openpyxl.load_workbook(io.BytesIO(resultado_bytes))
    ws = wb["FORMALIZACION"]
    fila = _leer_fila_por_identificacion(ws, "1000000003")
    assert fila["aval"] is None
    assert fila["observacion"] is None
    # La fila SIGUE presente en el libro (no se borra), solo sin las 2 celdas.
    assert fila["radicado"] == "R-003"


@pytest.mark.asyncio
async def test_fila_sin_auditar_aval_none_queda_en_blanco(db_session, lote_con_respuesta_pendiente):
    lote = lote_con_respuesta_pendiente["lote"]

    resultado_bytes = await generar_respuesta(db_session, lote.id)

    wb = openpyxl.load_workbook(io.BytesIO(resultado_bytes))
    ws = wb["FORMALIZACION"]
    fila = _leer_fila_por_identificacion(ws, "1000000004")
    assert fila["aval"] is None
    assert fila["observacion"] is None


@pytest.mark.asyncio
async def test_no_reconstruye_el_libro_todas_las_filas_originales_se_conservan(
    db_session, lote_con_respuesta_pendiente
):
    lote = lote_con_respuesta_pendiente["lote"]

    resultado_bytes = await generar_respuesta(db_session, lote.id)

    wb = openpyxl.load_workbook(io.BytesIO(resultado_bytes))
    ws = wb["FORMALIZACION"]
    # Encabezado (1) + 4 filas de datos, ninguna se borró ni se agregó.
    assert ws.max_row == 5
    identificaciones = [ws.cell(row=r, column=2).value for r in range(2, ws.max_row + 1)]
    assert identificaciones == ["1000000001", "1000000002", "1000000003", "1000000004"]


@pytest.mark.asyncio
async def test_lote_inexistente_lanza_not_found(db_session):
    from uuid import uuid4

    with pytest.raises(NotFoundException):
        await generar_respuesta(db_session, uuid4())


@pytest.mark.asyncio
async def test_lote_sin_archivo_original_lanza_bad_request(db_session):
    lote = LotePrevisional(nombre_archivo="SIN_ARCHIVO.xlsx")
    db_session.add(lote)
    await db_session.commit()
    await db_session.refresh(lote)

    with pytest.raises(BadRequestException):
        await generar_respuesta(db_session, lote.id)

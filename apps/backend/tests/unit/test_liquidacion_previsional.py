"""
Tests for the pension-disability liquidation formula (base IBC).

CRITICAL CORRECTION TO THE WRITTEN SPEC: the liquidation base is the IBC
column, not SALARIO as an earlier spec draft claimed. This was empirically
verified against 37 parseable rows of the insurer's own audited workbook:
computing Sum(max(IBC_mes * 50%, SMLMV_ano) / 30 * dias_mes) matches the
audited VALOR column in 37/37 cases; the same formula using SALARIO instead
of IBC only matches 35/37 -- the 2 mismatches are rows where SALARIO=0 but
IBC holds the real base salary, proving IBC is the correct base.

Cases in test_piso_smlmv_cuando_ibc_bajo through test_dos_pisos_al_cruzar_ano
are taken verbatim from the approved implementation brief (task 1.2).
"""
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

import openpyxl
import pytest

from app.services.previsionales.liquidacion_previsional import (
    DetallePeriodo,
    calcular_valor,
)
from app.services.previsionales.segmentacion import segmentar

SMLMV = {2024: Decimal(1300000), 2025: Decimal(1423500), 2026: Decimal(1750905)}


def test_piso_smlmv_cuando_ibc_bajo():
    # 35 de 40 filas reales
    segs = segmentar(date(2026, 7, 11), date(2026, 7, 25))  # 15 dias
    total, det = calcular_valor([(segs[0], Decimal("1750905"))], SMLMV)
    # 1750905/2=875452.5 < SMLMV -> piso 1750905/30*15
    assert total == Decimal("875453")
    assert det[0].piso_aplicado is True


def test_base_es_ibc_no_salario_caso_16743444():
    segs = segmentar(date(2026, 5, 28), date(2026, 6, 26))  # 4 + 26 = 30 dias
    total, det = calcular_valor([(s, Decimal("3750905")) for s in segs], SMLMV)
    assert total == Decimal("1875453")  # 50% de IBC supera el piso
    assert all(d.piso_aplicado is False for d in det)


def test_base_es_ibc_no_salario_caso_18594086():
    segs = segmentar(date(2026, 5, 16), date(2026, 7, 14))  # 3 segmentos, 60 dias
    total, _ = calcular_valor([(s, Decimal("4600000")) for s in segs], SMLMV)
    assert total == Decimal("4600000")


def test_dos_pisos_al_cruzar_ano():
    segs = segmentar(date(2025, 12, 20), date(2026, 1, 10))
    _, det = calcular_valor([(s, Decimal("100000")) for s in segs], SMLMV)
    assert det[0].smlmv_aplicado == Decimal(1423500)
    assert det[1].smlmv_aplicado == Decimal(1750905)


def test_detalle_periodo_shape():
    """The returned DetallePeriodo entries expose everything needed for audit trails."""
    segs = segmentar(date(2026, 7, 11), date(2026, 7, 25))
    total, det = calcular_valor([(segs[0], Decimal("1750905"))], SMLMV)
    assert len(det) == 1
    d = det[0]
    assert isinstance(d, DetallePeriodo)
    assert d.segmento == segs[0]
    assert d.ibc == Decimal("1750905")
    assert d.base_mensual == Decimal(1750905)  # floor won (50% IBC < SMLMV)
    assert d.smlmv_aplicado == Decimal(1750905)
    assert d.valor_segmento == Decimal("875452.5")
    assert d.piso_aplicado is True


def test_lista_vacia_retorna_cero():
    total, det = calcular_valor([], SMLMV)
    assert total == Decimal(0)
    assert det == []


# ---------------------------------------------------------------------------
# Paso 5 - test de regresion masiva contra el workbook auditado real.
# ---------------------------------------------------------------------------

FIXTURE_NAME = "Copy_RADICADOS_AUDITORIA_20260706.xlsx"

# Column letters per the brief: F=FECHA_INICIAL, G=FECHA_FINAL, K=IBC, P=VALOR.
# openpyxl row tuples are 0-indexed, so column F is index 5, G=6, K=10, P=15.
COL_FECHA_INICIAL = 5
COL_FECHA_FINAL = 6
COL_IBC = 10
COL_VALOR = 15


def _resolve_fixture_path() -> Path:
    """
    Locate the real audited workbook fixture.

    Preferred location is the canonical repo-root path
    docs/recursos_previsionales/Copy_RADICADOS_AUDITORIA_20260706.xlsx (found by
    walking up from this file until a `.git` directory is found). This works
    for local/host test runs.

    The Docker container this backend runs tests in (`incapacidades-api`) only
    bind-mounts `apps/backend` (see docker-compose.yml `api.volumes: .:/app`),
    so the repo-root `docs/` folder is NOT reachable from inside the
    container. For that case we fall back to a checked-in copy at
    tests/fixtures/, following the same convention already used by
    afp_formalizacion_encrypted.xlsx in this test suite.
    """
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / ".git").exists():
            candidate = parent / "docs" / "recursos_previsionales" / FIXTURE_NAME
            if candidate.exists():
                return candidate
            break

    fallback = Path(__file__).resolve().parent.parent / "fixtures" / FIXTURE_NAME
    if fallback.exists():
        return fallback

    pytest.fail(
        f"Could not locate {FIXTURE_NAME} at docs/recursos_previsionales/ "
        f"(repo root) or tests/fixtures/ (Docker fallback)."
    )


def _parse_fecha_tolerante(valor) -> date:
    """
    Parse FECHA_INICIAL/FECHA_FINAL cells that may be real datetime cells or
    'dd/mm/yyyy' text, per the real workbook's inconsistent formatting.
    """
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    texto = str(valor).strip()
    dia, mes, ano = texto.split("/")
    return date(int(ano), int(mes), int(dia))


def _split_ibc(valor) -> list[Decimal]:
    """Split the IBC column: may be 'N - N ' (repeated per segment) or a bare number."""
    if isinstance(valor, str):
        partes = [p.strip() for p in valor.split("-") if p.strip()]
        return [Decimal(p) for p in partes]
    return [Decimal(str(valor))]


@pytest.mark.slow
def test_regresion_masiva_contra_workbook_auditado():
    fixture_path = _resolve_fixture_path()
    wb = openpyxl.load_workbook(fixture_path, data_only=True)
    ws = wb["FORMALIZACION"]

    comparadas = 0
    coincidencias = 0
    saltadas_por_desalineacion = 0
    fallos = []

    for idx, row in enumerate(ws.iter_rows(min_row=2, max_col=17), start=2):
        identificacion = row[1].value
        if identificacion is None:
            continue

        fecha_inicial_raw = row[COL_FECHA_INICIAL].value
        fecha_final_raw = row[COL_FECHA_FINAL].value
        ibc_raw = row[COL_IBC].value
        valor_raw = row[COL_VALOR].value

        if fecha_inicial_raw is None or fecha_final_raw is None or ibc_raw is None or valor_raw is None:
            continue

        fecha_inicial = _parse_fecha_tolerante(fecha_inicial_raw)
        fecha_final = _parse_fecha_tolerante(fecha_final_raw)
        segmentos = segmentar(fecha_inicial, fecha_final)
        ibcs = _split_ibc(ibc_raw)

        if len(segmentos) != len(ibcs):
            # Real data has ~3 such rows (expected, not a bug) -- skip for comparison.
            saltadas_por_desalineacion += 1
            continue

        pares = list(zip(segmentos, ibcs))
        total, _ = calcular_valor(pares, SMLMV)

        esperado = Decimal(str(valor_raw)).quantize(Decimal("1"))
        comparadas += 1
        if total == esperado:
            coincidencias += 1
        else:
            fallos.append((idx, total, esperado))

    assert comparadas >= 30, (
        f"Only {comparadas} comparable rows found (need >= 30). "
        f"Skipped {saltadas_por_desalineacion} rows for segment/IBC count mismatch. "
        "A near-zero comparable count usually means the fixture path, sheet "
        "name, or column layout changed."
    )
    assert fallos == [], f"{len(fallos)}/{comparadas} rows mismatched: {fallos}"
    assert coincidencias == comparadas

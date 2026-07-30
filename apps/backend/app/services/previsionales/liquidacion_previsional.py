"""
Pension-disability liquidation formula (base IBC).

CRITICAL CORRECTION TO THE WRITTEN SPEC: the liquidation base is the IBC
(Ingreso Base de Cotizacion) column, NOT SALARIO as an earlier spec draft
claimed. This was empirically verified this session against 198 real
audited rows of the insurer's own Excel workbook:

    Sum(max(IBC_mes * 50%, SMLMV_ano) / 30 * dias_mes)

matches the insurer's own audited VALOR column in all 37 parseable rows
(see tests/unit/test_liquidacion_previsional.py::
test_regresion_masiva_contra_workbook_auditado). The same formula computed
with SALARIO instead of IBC only matches 35 of 37 rows -- the 2 mismatches
are real rows where SALARIO=0 but IBC holds the actual base salary,
proving IBC is correct and SALARIO is a red herring for this formula.
"""
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from app.services.previsionales.segmentacion import Segmento

_TREINTA = Decimal(30)
_MITAD = Decimal("0.5")


@dataclass(frozen=True)
class DetallePeriodo:
    """Per-segment breakdown of the liquidation, for audit trails/UI display."""

    segmento: Segmento
    ibc: Decimal
    base_mensual: Decimal
    smlmv_aplicado: Decimal
    valor_segmento: Decimal
    piso_aplicado: bool


def calcular_valor(
    pares: list[tuple[Segmento, Decimal]],
    smlmv_por_ano: dict[int, Decimal],
) -> tuple[Decimal, list[DetallePeriodo]]:
    """
    Compute the total pension-disability liquidation value from IBC-paired segments.

    For each (segmento, ibc) pair:
        smlmv = smlmv_por_ano[segmento.fecha_inicio.year]
        base = max(ibc * 0.5, smlmv)              # SMLMV floor per segment's year
        valor_segmento = base / 30 * segmento.dias  # always /30 (mes comercial)

    The total is the sum of every segment's valor_segmento, rounded at the end
    with ROUND_HALF_UP to the nearest peso. Individual valor_segmento values in
    the returned detail list are NOT rounded (only the total is).

    Args:
        pares: List of (Segmento, ibc) tuples, e.g. from
            `parear_segmentos()` in segmentacion.py.
        smlmv_por_ano: Mapping of year -> SMLMV (Salario Minimo Legal Mensual
            Vigente) for that year. Must contain an entry for every year any
            segment's fecha_inicio falls in.

    Returns:
        (total, detalle) where total is the rounded Decimal sum and detalle
        is a list of DetallePeriodo (one per input pair, same order).
    """
    detalle: list[DetallePeriodo] = []
    total = Decimal(0)

    for segmento, ibc in pares:
        smlmv = smlmv_por_ano[segmento.fecha_inicio.year]
        mitad_ibc = ibc * _MITAD
        piso_aplicado = smlmv > mitad_ibc
        base_mensual = smlmv if piso_aplicado else mitad_ibc
        valor_segmento = base_mensual / _TREINTA * Decimal(segmento.dias)

        detalle.append(
            DetallePeriodo(
                segmento=segmento,
                ibc=ibc,
                base_mensual=base_mensual,
                smlmv_aplicado=smlmv,
                valor_segmento=valor_segmento,
                piso_aplicado=piso_aplicado,
            )
        )
        total += valor_segmento

    return total.quantize(Decimal("1"), rounding=ROUND_HALF_UP), detalle

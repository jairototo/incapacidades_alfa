"""
Monthly segmentation of date ranges and AFP column parsing.

Handles splitting disability claim date ranges into monthly segments
and parsing AFP excel columns with multiple dash-separated values.
"""
import calendar
from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class Segmento:
    """
    A monthly segment of a disability claim period.

    Attributes:
        orden: Sequential segment number (1-based)
        fecha_inicio: Inclusive start date of segment
        fecha_fin: Inclusive end date of segment
        dias: Number of days in segment (inclusive counting)
    """

    orden: int
    fecha_inicio: date
    fecha_fin: date
    dias: int


class ConteoSegmentosError(ValueError):
    """Raised when segment counts don't align across data sources."""


def segmentar(fecha_inicial: date, fecha_final: date) -> list[Segmento]:
    """
    Split a date range into monthly segments.

    Each segment spans complete calendar months or partial months as needed.
    A segment at month boundary ends on the last day of the month.
    Days are counted inclusively: (fecha_fin - fecha_inicio) + 1.

    Real-world use: disability claim filing dates must align with payroll
    periods, which are monthly. This function ensures accurate month-by-month
    tracking for AFP contributions and day counts.

    Args:
        fecha_inicial: Inclusive start date
        fecha_final: Inclusive end date

    Returns:
        Ordered list of Segmento objects covering the entire date range
    """
    segmentos = []
    orden = 1

    current_start = fecha_inicial

    while current_start <= fecha_final:
        # Get the last day of the current month
        last_day_of_month = calendar.monthrange(current_start.year, current_start.month)[1]
        month_end = date(current_start.year, current_start.month, last_day_of_month)

        # Segment ends at month boundary or at fecha_final, whichever comes first
        segment_end = min(fecha_final, month_end)

        # Count days inclusively
        dias = (segment_end - current_start).days + 1

        segmentos.append(
            Segmento(
                orden=orden,
                fecha_inicio=current_start,
                fecha_fin=segment_end,
                dias=dias,
            )
        )

        # Stop if we've reached the end of the range
        if segment_end == fecha_final:
            break

        # Move to first day of next month
        if current_start.month == 12:
            current_start = date(current_start.year + 1, 1, 1)
        else:
            current_start = date(current_start.year, current_start.month + 1, 1)

        orden += 1

    return segmentos


def split_multivalor(valor: str | float | int | None) -> list[Decimal]:
    """
    Parse AFP excel columns containing possibly multiple dash-separated values.

    AFP files sometimes represent multiple payroll periods as a single column
    with values separated by dashes. This function normalizes all input forms
    into a consistent list of Decimal values.

    Args:
        valor: Input from AFP column: string (possibly with dashes), single number,
               or None/empty

    Returns:
        List of Decimal values. Empty list for None or empty string input.
    """
    if valor is None:
        return []

    if isinstance(valor, str):
        if not valor.strip():
            return []
        # Split by '-', strip whitespace, filter empty strings
        parts = [part.strip() for part in valor.split("-") if part.strip()]
        return [Decimal(part) for part in parts]

    if isinstance(valor, (int, float)):
        return [Decimal(str(valor))]

    return []


def parear_segmentos(segs, ibc, salario, dias_cotizados) -> list[tuple[Segmento, Decimal, Decimal, int]]:
    """
    Pair monthly segments with corresponding AFP data columns.

    Ensures that the number of segments matches the number of values in each
    AFP column (IBC, salary, days worked). A mismatch indicates a data quality
    issue that should be caught before further processing.

    Args:
        segs: List of Segmento objects
        ibc: List of Decimal IBC (Base Income) values
        salario: List of Decimal salary values
        dias_cotizados: List of int days worked

    Returns:
        List of tuples: (Segmento, Decimal ibc, Decimal salario, int dias_cotizados)

    Raises:
        ConteoSegmentosError: If any data source has a different count than segments
    """
    num_segs = len(segs)
    if (
        len(ibc) != num_segs
        or len(salario) != num_segs
        or len(dias_cotizados) != num_segs
    ):
        raise ConteoSegmentosError(
            f"Segment count mismatch: {num_segs} segments but "
            f"ibc={len(ibc)}, salario={len(salario)}, dias_cotizados={len(dias_cotizados)}"
        )

    return list(zip(segs, ibc, salario, dias_cotizados))

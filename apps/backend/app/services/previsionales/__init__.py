"""
Services for previsionales (pension) domain.

This package contains business logic for processing pension/previsional claims,
including date segmentation and AFP column parsing.
"""
from app.services.previsionales.segmentacion import (
    ConteoSegmentosError,
    Segmento,
    parear_segmentos,
    segmentar,
    split_multivalor,
)

__all__ = [
    "Segmento",
    "segmentar",
    "split_multivalor",
    "ConteoSegmentosError",
    "parear_segmentos",
]

"""
Schemas Pydantic para la importación de datos de referencia previsionales
(Task 4.1) -- ver `app/services/previsionales/referencia_adapter.py`.
"""
from __future__ import annotations

from pydantic import BaseModel


class ReferenciaImportarResponse(BaseModel):
    """Respuesta de POST /previsionales/referencia/importar."""

    tipo: str
    importados: int

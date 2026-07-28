"""Schemas de Pydantic para la carga masiva de empleados."""
from typing import List, Optional

from pydantic import BaseModel


class FilaError(BaseModel):
    """Un error de validación en una fila específica del Excel de carga masiva."""
    fila: int
    columna: Optional[str] = None
    mensaje: str


class ValidacionMasivaResponse(BaseModel):
    """Resultado del dry-run de validación de carga masiva."""
    total_filas: int
    validas: int
    con_error: int
    errores: List[FilaError]


class ConfirmacionMasivaResponse(BaseModel):
    """Resultado de la confirmación de carga masiva (inserción parcial)."""
    total_filas: int
    insertadas: int
    con_error: int
    errores: List[FilaError]

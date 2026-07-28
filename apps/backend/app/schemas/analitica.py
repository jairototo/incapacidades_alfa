"""Schemas de Pydantic para el endpoint de analítica de empresas."""
from typing import List
from uuid import UUID

from pydantic import BaseModel


class EmpresaTopItem(BaseModel):
    """Una fila del ranking top-10 de empresas por incapacidades radicadas."""
    empresa_id: UUID
    razon_social: str
    nit: str
    total_radicadas: int


class TendenciaMensualItem(BaseModel):
    """Total de incapacidades radicadas en un mes (YYYY-MM)."""
    periodo: str
    total: int


class AnaliticaEmpresasResponse(BaseModel):
    """Respuesta combinada del endpoint de analítica de empresas."""
    top_empresas: List[EmpresaTopItem]
    tendencia_mensual: List[TendenciaMensualItem]

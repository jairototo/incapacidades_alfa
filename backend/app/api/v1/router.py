"""
Main API router for v1.
"""
from fastapi import APIRouter

from app.api.v1.endpoints import (
    health,
    auth,
    afiliados,
    empresas,
    empleados,
    incapacidades,
    siniestros,
    historial_estado,
    documentos,
    storage
)

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(afiliados.router, prefix="/afiliados", tags=["afiliados"])
api_router.include_router(empresas.router, prefix="/empresas", tags=["empresas"])
api_router.include_router(empleados.router, prefix="/empleados", tags=["empleados"])
api_router.include_router(incapacidades.router, prefix="/incapacidades", tags=["incapacidades"])
api_router.include_router(siniestros.router, prefix="/siniestros", tags=["siniestros"])
api_router.include_router(historial_estado.router, prefix="/historial", tags=["historial"])
api_router.include_router(documentos.router, prefix="/documentos", tags=["documentos"])
api_router.include_router(storage.router, prefix="/storage", tags=["storage"])

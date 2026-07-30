"""
Main API router for v1.
"""
from app.api.v1.endpoints import afiliados, auditar_creacion_siniestro, auth, catalogos, creacion_siniestro, documentos, empleados, empresas, health, historial_estado, incapacidades, liquidacion, ordenes_pago, plantilla_auditoria, pre_incapacidades, siniestros, solicitantes, storage
from fastapi import APIRouter

from app.api.v1.endpoints import (
    usuarios
)
from app.api.v1.endpoints.previsionales import auditoria as previsionales_auditoria
from app.api.v1.endpoints.previsionales import lotes as previsionales_lotes
from app.api.v1.endpoints.previsionales import parametros as previsionales_parametros
from app.api.v1.endpoints.previsionales import referencia as previsionales_referencia

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(usuarios.router, prefix="/usuarios", tags=["usuarios"])
api_router.include_router(solicitantes.router, prefix="/solicitantes", tags=["solicitantes"])
api_router.include_router(catalogos.router, prefix="/catalogos", tags=["catalogos"])
api_router.include_router(afiliados.router, prefix="/afiliados", tags=["afiliados"])
api_router.include_router(empresas.router, prefix="/empresas", tags=["empresas"])
api_router.include_router(empleados.router, prefix="/empleados", tags=["empleados"])
api_router.include_router(incapacidades.router, prefix="/incapacidades", tags=["incapacidades"])
api_router.include_router(auditar_creacion_siniestro.router, prefix="/incapacidades", tags=["auditar-creacion-siniestro"])
api_router.include_router(creacion_siniestro.router, prefix="/incapacidades", tags=["creacion-siniestro"])
api_router.include_router(plantilla_auditoria.router, prefix="/incapacidades", tags=["plantilla-auditoria"])
api_router.include_router(liquidacion.router, prefix="/incapacidades", tags=["liquidacion"])
api_router.include_router(siniestros.router, prefix="/siniestros", tags=["siniestros"])
api_router.include_router(historial_estado.router, prefix="/historial", tags=["historial"])
api_router.include_router(documentos.router, prefix="/documentos", tags=["documentos"])
api_router.include_router(storage.router, prefix="/storage", tags=["storage"])
api_router.include_router(ordenes_pago.router, prefix="/ordenes-pago", tags=["ordenes-pago"])
api_router.include_router(pre_incapacidades.router, prefix="/pre-incapacidades", tags=["pre-incapacidades"])
api_router.include_router(previsionales_lotes.router, prefix="/previsionales/lotes", tags=["previsionales-lotes"])
api_router.include_router(previsionales_referencia.router, prefix="/previsionales/referencia", tags=["previsionales-referencia"])
api_router.include_router(previsionales_parametros.router, prefix="/previsionales/parametros", tags=["previsionales-parametros"])
api_router.include_router(previsionales_auditoria.router, prefix="/previsionales/incapacidades", tags=["previsionales-auditoria"])

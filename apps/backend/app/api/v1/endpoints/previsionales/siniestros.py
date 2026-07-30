"""
API endpoint para registro manual de Siniestro Previsional (Task 4.4).

Ruta:
  POST /previsionales/siniestros

Permisos: PREVISIONAL_LOAD (AUDITOR_PREVISIONALES, ADMIN) -- clasificado como
acción de "carga" por el plan, igual que la importación de referencia
(Task 4.1).

--- GAP DE ESQUEMA (documentado, no resuelto aquí) -----------------------
El texto original del plan (§4.2 del spec) describe este formulario como
"similar a la tabla siniestros, más: ciudad, departamento, estado, eps,
arl". El modelo real construido en Task 2.1 (`SiniestroPrevisional`) NO
tiene columnas `ciudad`/`departamento`/`eps`/`arl` -- solo `identificacion`,
`numero_siniestro`, `origen`, `estado`, `fecha_aviso`, `fecha_siniestro`.
Este endpoint se construye alrededor de lo que el modelo genuinamente
tiene; esos 4 campos NO se inventan ni se guardan en un JSONB catch-all.
Si son requeridos de verdad para el negocio, hace falta una migración
futura que agregue las columnas -- fuera de alcance de esta tarea (ver
`app/schemas/previsionales/siniestros.py` para el mismo aviso).

--- DECISIONES DE ESTA TAREA ----------------------------------------------

1. `identificacion` requerido vs. autocompletado desde `incapacidad_id`:
   el único campo genuinamente autocompletable desde una
   `IncapacidadPrevisional` es `identificacion` (los demás campos del
   siniestro -- numero_siniestro, origen, estado, fechas -- no existen en
   `IncapacidadPrevisional`, que solo trae el `numero_siniestro`
   *reportado por la AFP*, un dato distinto al siniestro real). Regla:
   - Si se da `incapacidad_id` y NO `identificacion`: se autocompleta desde
     la incapacidad.
   - Si se dan ambos: deben coincidir, o se rechaza con 400 (evita crear un
     siniestro con una identificación que contradice la incapacidad que el
     usuario dijo estar usando como referencia).
   - Si no se da ninguno de los dos: 400 ("identificacion es requerida").

2. `fecha_siniestro < fecha_aviso`: la regla AP del motor de auditoría
   (`auditoria_rules.regla_ap_fecha_siniestro`) trata esta comparación como
   puramente informativa para datos importados -- nunca rechaza, solo
   reporta las fechas tal cual. Por consistencia, este endpoint tampoco
   rechaza cuando `fecha_siniestro >= fecha_aviso` (orden invertido u
   fechas iguales): se registra tal cual, sin bloquear la captura manual.
   No se agrega un campo de "warning" en la respuesta -- documentado aquí
   en vez de añadir un mecanismo nuevo no pedido por el spec.

3. `numero_siniestro` duplicado: el modelo NO declara `unique=True` (ver
   `siniestro_previsional.py`), así que no hay `IntegrityError` de BD que
   mapear. Se agregó un pre-check de aplicación
   (`get_by_numero_siniestro`) que devuelve `DuplicateException` (409) si
   ya existe un siniestro con ese número -- una probable colisión de
   captura manual, a diferencia de la ambigüedad por `identificacion`
   (múltiples siniestros por afiliado), que sí es un caso de negocio
   válido documentado en el repositorio.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, DuplicateException, NotFoundException
from app.core.security import PermissionChecker, Permissions, get_current_user
from app.db.repositories.previsionales import (
    incapacidad_previsional_repository,
    siniestro_previsional_repository,
)
from app.db.session import get_db
from app.models.usuario import Usuario
from app.schemas.previsionales.siniestros import (
    SiniestroPrevisionalCreateRequest,
    SiniestroPrevisionalResponse,
)

router = APIRouter()

_SINIESTRO_LOAD_PERMISSIONS = [Permissions.PREVISIONAL_LOAD]


@router.post(
    "",
    response_model=SiniestroPrevisionalResponse,
    status_code=201,
    summary="Registrar manualmente un siniestro previsional",
    dependencies=[Depends(PermissionChecker(_SINIESTRO_LOAD_PERMISSIONS))],
)
async def crear_siniestro(
    body: SiniestroPrevisionalCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> SiniestroPrevisionalResponse:
    """
    Registro manual de un siniestro previsional (fuera del flujo de
    importación masiva de Task 3.2/4.1). Ver el docstring del módulo para
    el detalle completo de las 3 decisiones de esta tarea (gap de columnas,
    resolución de `identificacion`, comparación de fechas, duplicados).

    **Permisos**: PREVISIONAL_LOAD (AUDITOR_PREVISIONALES, ADMIN)
    """
    identificacion = body.identificacion

    if body.incapacidad_id is not None:
        incapacidad = await incapacidad_previsional_repository.get_by_id(db, body.incapacidad_id)
        if incapacidad is None:
            raise NotFoundException(
                f"IncapacidadPrevisional {body.incapacidad_id} no encontrada"
            )
        if identificacion is None:
            identificacion = incapacidad.identificacion
        elif incapacidad.identificacion is not None and identificacion != incapacidad.identificacion:
            raise BadRequestException(
                "identificacion no coincide con la de la incapacidad_id indicada "
                f"({identificacion!r} vs {incapacidad.identificacion!r})"
            )

    if not identificacion:
        raise BadRequestException(
            "identificacion es requerida (directamente o vía incapacidad_id)"
        )

    existente = await siniestro_previsional_repository.get_by_numero_siniestro(
        db, body.numero_siniestro
    )
    if existente is not None:
        raise DuplicateException(
            f"Ya existe un siniestro con numero_siniestro={body.numero_siniestro!r}"
        )

    creado = await siniestro_previsional_repository.create(
        db,
        {
            "identificacion": identificacion,
            "numero_siniestro": body.numero_siniestro,
            "origen": body.origen,
            "estado": body.estado,
            "fecha_aviso": body.fecha_aviso,
            "fecha_siniestro": body.fecha_siniestro,
        },
    )
    return SiniestroPrevisionalResponse.model_validate(creado)

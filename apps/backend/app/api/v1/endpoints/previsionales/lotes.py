"""
API endpoints para Lotes Previsionales (Task 4.1).

Todos los endpoints requieren autenticación JWT y el permiso indicado
(AUDITOR_PREVISIONALES, AUDITOR_JURIDICO o ADMIN según el permiso).

Endpoints:
  POST /previsionales/lotes                          — cargar un lote desde el excel AFP
  GET  /previsionales/lotes                           — listar lotes (paginado)
  GET  /previsionales/lotes/{lote_id}                  — detalle de un lote
  GET  /previsionales/lotes/{lote_id}/incapacidades    — listar incapacidades de un lote (filtros)
  POST /previsionales/lotes/{lote_id}/actualizar       — [GAP] re-cruce de siniestros, ver docstring
  GET  /previsionales/lotes/{lote_id}/arpis.xlsx       — exportar el libro de cargue ARPIS

Permisos: PREVISIONAL_LOAD (POST /lotes, POST /actualizar), PREVISIONAL_READ
(los GET), PREVISIONAL_EXPORT (GET /arpis.xlsx).
"""
from __future__ import annotations

import io
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.core.security import PermissionChecker, Permissions, get_current_user
from app.db.repositories.previsionales import (
    incapacidad_previsional_repository,
    lote_previsional_repository,
    periodo_previsional_repository,
)
from app.db.session import get_db
from app.models.previsionales.incapacidad_previsional import IncapacidadPrevisional
from app.models.previsionales.periodo_previsional import PeriodoPrevisional
from app.models.usuario import Usuario
from app.schemas.previsionales.lote import IncapacidadPrevisionalResponse, LotePrevisionalResponse
from app.services.previsionales.arpis_export import (
    agrupar_salarios,
    construir_libro_arpis,
    mapear_tipo_ingreso,
)
from app.services.previsionales.lote_service import lote_previsional_service
from app.services.previsionales.segmentacion import Segmento

router = APIRouter()

_LOTE_LOAD_PERMISSIONS = [Permissions.PREVISIONAL_LOAD]
_LOTE_READ_PERMISSIONS = [Permissions.PREVISIONAL_READ]
_LOTE_EXPORT_PERMISSIONS = [Permissions.PREVISIONAL_EXPORT]

_CONTENT_TYPE_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


# ---------------------------------------------------------------------------
# POST /previsionales/lotes
# ---------------------------------------------------------------------------

@router.post(
    "",
    response_model=LotePrevisionalResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cargar un lote previsional desde el excel de la AFP",
    dependencies=[Depends(PermissionChecker(_LOTE_LOAD_PERMISSIONS))],
)
async def cargar_lote(
    file: UploadFile = File(...),
    password: Optional[str] = Form(None),
    nombre_archivo: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> LotePrevisionalResponse:
    """
    Carga un lote previsional desde el excel (posiblemente cifrado) de la AFP.

    `password` es OPCIONAL a propósito: el excel puede o no venir cifrado
    según el ambiente -- `lote_excel_reader.descifrar_si_aplica` detecta el
    cifrado por magic bytes OLE2/CFB, nunca por extensión, y ya maneja
    ambos casos (con/sin contraseña). Este endpoint no repite esa
    validación, se delega íntegramente en
    `lote_previsional_service.cargar_lote` (que levanta
    `BadRequestException` si el archivo está cifrado sin contraseña, o con
    una contraseña incorrecta -- mapeado a 400 por el exception handler
    global).

    Si `nombre_archivo` no se envía explícitamente, se usa el nombre
    original del archivo subido.

    **Permisos**: PREVISIONAL_LOAD (AUDITOR_PREVISIONALES, ADMIN)
    """
    file_bytes = await file.read()
    lote = await lote_previsional_service.cargar_lote(
        db=db,
        file_bytes=file_bytes,
        password=password,
        nombre_archivo=nombre_archivo or file.filename or "lote.xlsx",
        usuario_id=current_user.id,
    )
    return LotePrevisionalResponse.model_validate(lote)


# ---------------------------------------------------------------------------
# GET /previsionales/lotes
# ---------------------------------------------------------------------------

@router.get(
    "",
    response_model=list[LotePrevisionalResponse],
    summary="Listar lotes previsionales",
    dependencies=[Depends(PermissionChecker(_LOTE_READ_PERMISSIONS))],
)
async def listar_lotes(
    skip: int = Query(0, ge=0, description="Número de registros a saltar"),
    limit: int = Query(100, ge=1, le=1000, description="Número máximo de registros"),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> list[LotePrevisionalResponse]:
    """
    Lista los lotes previsionales cargados, paginado (skip/limit), del más
    reciente al más antiguo (orden por defecto de
    `BaseRepository.get_multi`).

    Cada elemento trae los "contadores" ya persistidos en el propio lote
    (`total_filas`, `total_incapacidades`) -- deliberadamente NO se
    calculan aquí desgloses adicionales por filtro
    (sin_siniestro/repetidas/errores/dif_valor) por lote, porque eso
    implicaría una query de agregación por cada lote listado (riesgo de
    N+1, contrario al principio de CLAUDE.md). Para ese nivel de detalle
    usar GET /lotes/{id}/incapacidades con los filtros correspondientes.

    **Permisos**: PREVISIONAL_READ (AUDITOR_PREVISIONALES, AUDITOR_JURIDICO, ADMIN)
    """
    lotes = await lote_previsional_repository.get_multi(db, skip=skip, limit=limit)
    return [LotePrevisionalResponse.model_validate(lote) for lote in lotes]


# ---------------------------------------------------------------------------
# GET /previsionales/lotes/{lote_id}
# ---------------------------------------------------------------------------

@router.get(
    "/{lote_id}",
    response_model=LotePrevisionalResponse,
    summary="Obtener el detalle de un lote previsional",
    dependencies=[Depends(PermissionChecker(_LOTE_READ_PERMISSIONS))],
)
async def obtener_lote(
    lote_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> LotePrevisionalResponse:
    """**Permisos**: PREVISIONAL_READ (AUDITOR_PREVISIONALES, AUDITOR_JURIDICO, ADMIN)"""
    lote = await lote_previsional_repository.get_by_id(db, lote_id)
    if lote is None:
        raise NotFoundException(f"Lote previsional {lote_id} no encontrado")
    return LotePrevisionalResponse.model_validate(lote)


# ---------------------------------------------------------------------------
# GET /previsionales/lotes/{lote_id}/incapacidades
# ---------------------------------------------------------------------------

@router.get(
    "/{lote_id}/incapacidades",
    response_model=list[IncapacidadPrevisionalResponse],
    summary="Listar las incapacidades de un lote, con filtros opcionales",
    dependencies=[Depends(PermissionChecker(_LOTE_READ_PERMISSIONS))],
)
async def listar_incapacidades_del_lote(
    lote_id: UUID,
    sin_siniestro: Optional[bool] = Query(
        None, description="True: numero_siniestro IS NULL; False: NOT NULL"
    ),
    repetidas: Optional[bool] = Query(
        None, description="Filtra por es_duplicado_interno == valor"
    ),
    errores: Optional[bool] = Query(
        None, description="True: con errores_carga; False: sin errores_carga"
    ),
    dif_valor: Optional[bool] = Query(
        None, description="True: diferencia_valor_afp no nula y != 0"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> list[IncapacidadPrevisionalResponse]:
    """
    Filtros disponibles (ver
    `IncapacidadPrevisionalRepository.get_by_lote` para el mapeo exacto de
    cada uno a columnas): sin_siniestro, repetidas, errores, dif_valor.
    Todos son opcionales y se combinan con AND cuando se envía más de uno.

    **Permisos**: PREVISIONAL_READ (AUDITOR_PREVISIONALES, AUDITOR_JURIDICO, ADMIN)
    """
    lote = await lote_previsional_repository.get_by_id(db, lote_id)
    if lote is None:
        raise NotFoundException(f"Lote previsional {lote_id} no encontrado")

    filtros: dict[str, Any] = {
        "sin_siniestro": sin_siniestro,
        "repetidas": repetidas,
        "errores": errores,
        "dif_valor": dif_valor,
    }
    incapacidades = await incapacidad_previsional_repository.get_by_lote(db, lote_id, filtros)
    return [IncapacidadPrevisionalResponse.model_validate(i) for i in incapacidades]


# ---------------------------------------------------------------------------
# POST /previsionales/lotes/{lote_id}/actualizar
# ---------------------------------------------------------------------------

@router.post(
    "/{lote_id}/actualizar",
    summary="[GAP] Re-cruce de siniestros de un lote ya cargado",
    dependencies=[Depends(PermissionChecker(_LOTE_LOAD_PERMISSIONS))],
)
async def actualizar_lote(
    lote_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> None:
    """
    **GAP conocido (Task 4.1)**: no existe hoy, en la capa de servicio
    (`lote_service.py`, `referencia_adapter.py`), un método explícito de
    "re-cruce" que vuelva a cruzar los siniestros de un lote YA persistido
    contra los datos de referencia (`SiniestroPrevisional`) importados más
    recientemente, sin re-parsear el excel original desde cero.
    `cargar_lote` hace todo el trabajo (parseo + persistencia + cruce
    interno de repetidas/prórrogas) en una sola pasada atada a un archivo
    nuevo -- no está diseñado para volver a ejecutarse sobre un lote ya
    existente.

    Inventar esa lógica de negocio aquí (qué campos tocar, si se debe
    re-evaluar `numero_siniestro`/`estado`, cómo tratar incapacidades ya
    auditadas por un humano) está fuera del alcance de esta tarea y
    requiere una decisión explícita del equipo de negocio. Este endpoint
    existe únicamente para fijar el contrato de ruta y permisos
    (POST /previsionales/lotes/{id}/actualizar, permiso PREVISIONAL_LOAD)
    -- devuelve 501 con una nota clara en vez de adivinar la lógica.

    **Permisos**: PREVISIONAL_LOAD (AUDITOR_PREVISIONALES, ADMIN)
    """
    lote = await lote_previsional_repository.get_by_id(db, lote_id)
    if lote is None:
        raise NotFoundException(f"Lote previsional {lote_id} no encontrado")

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=(
            "Re-cruce de siniestros no implementado: no existe un método de "
            "servicio explícito para re-cruzar un lote ya persistido contra "
            "la referencia más reciente sin re-parsear el excel original "
            "desde cero. Ver la nota de gap en el reporte de Task 4.1 y en "
            "el docstring de este endpoint."
        ),
    )


# ---------------------------------------------------------------------------
# GET /previsionales/lotes/{lote_id}/arpis.xlsx
# ---------------------------------------------------------------------------

def _construir_filas_arpis(
    incapacidades: list[IncapacidadPrevisional],
    periodos_por_incapacidad: dict[UUID, list[PeriodoPrevisional]],
) -> list[dict]:
    """
    Traduce las incapacidades y periodos ya persistidos de un lote al
    formato `fila: dict` que espera `arpis_export.construir_libro_arpis`
    (ver su docstring para el shape exacto esperado).

    Decisiones de mapeo (judgment calls de esta tarea, no del diseño
    previo):
    - `dia_181` se puebla desde `dia_181_afp` (el único de los tres campos
      dia_181_* que `lote_service.cargar_lote` efectivamente escribe hoy;
      `dia_181_alfa`/`dia_181_arpis` quedan sin poblar a propósito, ver su
      propio comentario en `incapacidad_previsional.py`). Si una tarea
      futura empieza a poblar `dia_181_alfa` (candidato sugerido por la
      regla AB), este mapeo debe revisarse.
    - `radicado` usa `radicado_normalizado` (ya calculado en la carga vía
      `normalizar_radicado`) con fallback al `radicado` crudo si el
      normalizado no quedó poblado (fila con error de parseo).
    - `observacion_causal` se lee directo de la columna homónima del
      modelo -- hoy siempre viene `None` porque `lote_service.cargar_lote`
      guarda ese dato crudo (columna AA) dentro de `metadata_` en vez de
      en esta columna (ver decisión 3 en el docstring de `lote_service.py`)
      . No es un bug de esta tarea: se lee la columna que el modelo expone
      para este propósito, tal como está poblada hoy.

    Una incapacidad que no se puede traducir de forma segura (sin
    `tipo_ingreso`, tipo de ingreso no reconocido, más de 3 grupos de
    salario -- `DemasiadosGruposError`, o un periodo sin `salario`) se
    OMITE del libro de cargue con un `logger.warning`, en vez de abortar
    toda la exportación -- mismo principio tolerante-por-fila que el resto
    del módulo (`lote_service.cargar_lote`, `referencia_adapter.py`).
    """
    filas: list[dict] = []
    for inc in incapacidades:
        if not inc.tipo_ingreso:
            logger.warning(
                f"ARPIS export: incapacidad {inc.id} sin tipo_ingreso -- omitida "
                "del libro de cargue (mapear_tipo_ingreso requiere un valor reconocido)."
            )
            continue

        periodos = periodos_por_incapacidad.get(inc.id, [])
        pares: list[tuple[Segmento, Any]] = []
        fila_valida = True
        for p in periodos:
            if p.salario is None:
                logger.warning(
                    f"ARPIS export: periodo {p.id} de la incapacidad {inc.id} sin "
                    "salario -- incapacidad omitida del libro de cargue."
                )
                fila_valida = False
                break
            pares.append(
                (
                    Segmento(
                        orden=p.orden,
                        fecha_inicio=p.fecha_inicio,
                        fecha_fin=p.fecha_fin,
                        dias=p.dias,
                    ),
                    p.salario,
                )
            )
        if not fila_valida:
            continue

        try:
            grupos_salario = agrupar_salarios(pares) if pares else []
            # Validación temprana: `construir_libro_arpis` vuelve a llamar
            # `mapear_tipo_ingreso` internamente por fila, pero fallar aquí
            # (y omitir solo esta incapacidad) es preferible a dejar que
            # una sola fila con tipo_ingreso corrupto aborte TODO el libro
            # dentro de `construir_libro_arpis`.
            mapear_tipo_ingreso(inc.tipo_ingreso)
        except ValueError as exc:
            logger.warning(
                f"ARPIS export: incapacidad {inc.id} omitida del libro de cargue: {exc}"
            )
            continue

        filas.append(
            {
                "tipo_identificacion": inc.tipo_identificacion,
                "identificacion": inc.identificacion,
                "dia_181": inc.dia_181_afp,
                "radicado": inc.radicado_normalizado or inc.radicado,
                "fecha_radicacion_afp": inc.fecha_radicacion_afp,
                "fecha_radicacion_alfa": inc.fecha_radicacion_alfa,
                "tipo_ingreso": inc.tipo_ingreso,
                "fecha_inicial": inc.fecha_inicial,
                "fecha_final": inc.fecha_final,
                "grupos_salario": grupos_salario,
                "observacion": inc.observacion,
                "cie10_list": [inc.cie10] if inc.cie10 else [],
                "observacion_causal": inc.observacion_causal,
            }
        )
    return filas


@router.get(
    "/{lote_id}/arpis.xlsx",
    summary="Exportar el libro de cargue ARPIS de un lote",
    dependencies=[Depends(PermissionChecker(_LOTE_EXPORT_PERMISSIONS))],
)
async def exportar_arpis(
    lote_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> StreamingResponse:
    """
    Genera el libro .xlsx de cargue ARPIS a partir de las incapacidades y
    periodos ya persistidos del lote (ver `_construir_filas_arpis`).

    **Permisos**: PREVISIONAL_EXPORT (AUDITOR_PREVISIONALES, AUDITOR_JURIDICO, ADMIN)
    """
    lote = await lote_previsional_repository.get_by_id(db, lote_id)
    if lote is None:
        raise NotFoundException(f"Lote previsional {lote_id} no encontrado")

    incapacidades = await incapacidad_previsional_repository.get_by_lote(db, lote_id, filtros=None)
    incapacidad_ids = [inc.id for inc in incapacidades]
    periodos_por_incapacidad = await periodo_previsional_repository.get_by_incapacidades(
        db, incapacidad_ids
    )

    filas = _construir_filas_arpis(incapacidades, periodos_por_incapacidad)
    content = construir_libro_arpis(filas)

    return StreamingResponse(
        io.BytesIO(content),
        media_type=_CONTENT_TYPE_XLSX,
        headers={"Content-Disposition": f"attachment; filename=arpis_lote_{lote_id}.xlsx"},
    )

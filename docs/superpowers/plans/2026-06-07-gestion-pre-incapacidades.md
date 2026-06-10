# Pre-Incapacidad Gestión (Internal Management) Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the internal gestión workflow that lets internal users view, correct, return, and manually promote pre-incapacidades to full incapacidades from `sistema-interno`.

**Architecture:**
- **Backend**: 5 new authenticated endpoints added to existing `pre_incapacidades.py` router; one Alembic migration adds `motivo_devolucion` TEXT field; `ValidationInconsistenciaRepository` gains a `delete_by_pre_incapacidad` method; `PromotePreIncapacidadService` is updated to optionally clear previous issues and actually create the `Incapacidad` record on success (currently a TODO).
- **Frontend**: New `/pre-incapacidades/` section in `sistema-interno` with a **Bandeja** (inbox) listing page and a **Gestionar** detail page. The detail page follows the same split-screen pattern as the existing `GestionarPage` (document viewer left, action tabs right).
- **Email**: A formal Jinja2 HTML template `devolucion_pre_incapacidad.html` is added. The devolution endpoint queues a Celery email task using the existing `send_email_task`.

**Tech Stack:** FastAPI (SQLAlchemy 2.0 async), Alembic, Celery/RabbitMQ, Jinja2, React + Vite, React Query, Tailwind v3, Zod v3, Zustand, Shadcn/ui, TypeScript

---

## Context & Key Decisions

### Backend gaps (all pre-incapacidad routes are currently public/unauthenticated)
- `GET /api/v1/pre-incapacidades/` does not exist — only `GET /{id}` (public)
- There is no devolution, update, or manual-promote endpoint
- `PromotePreIncapacidadService.promote_pre_incapacidad()` has a `# TODO` that skips actual `Incapacidad` creation
- `ValidationInconsistenciaRepository` cannot delete by `pre_incapacidad_id` — needed before re-validation

### Estado values used in this feature
- `PENDIENTE` — initial state, background job pending or failed
- `RECHAZADA` — background job found blocking ERRORs, needs manual review
- `DEVUELTA` — internal user returned to external party for correction (new value, fits String(20))
- `PROCESADA` — successfully promoted to full `Incapacidad`
- `ERROR` — Celery task threw an unhandled exception

The **bandeja** shows: `PENDIENTE`, `RECHAZADA`, `ERROR`.

### Empresa/empleado resolution flow
Pre-incapacidad stores flat text: `empresa_nit`, `empleado_numero_documento`. The existing `GET /api/v1/empresas/` and `GET /api/v1/empleados/` endpoints handle search. The user can also create empresa/empleado via existing `POST /empresas/` and `POST /empleados/`. Once the user corrects `empresa_nit` (via PATCH), the next `promover` call will find the empresa.

### Authentication pattern (mirrors `incapacidades.py`)
```python
from app.core.security import get_current_user, PermissionChecker, Permissions
current_user: Usuario = Depends(get_current_user)
```
The list, update, devolver, and promover endpoints all require JWT.

---

## File Structure

```
apps/backend/
├── alembic/versions/
│   └── xxxx_add_motivo_devolucion_to_pre_incapacidad.py     [NEW]
├── app/
│   ├── api/v1/endpoints/
│   │   └── pre_incapacidades.py                              [MODIFY] +5 endpoints
│   ├── db/repositories/
│   │   └── validation_inconsistencia_repository.py           [MODIFY] +delete method
│   ├── models/
│   │   └── pre_incapacidad.py                                [MODIFY] +motivo_devolucion
│   ├── services/
│   │   └── pre_incapacidad_promotion_service.py              [MODIFY] +clear + Incapacidad creation
│   ├── tasks/
│   │   └── email_tasks.py                                    [MODIFY] +devolucion task
│   └── templates/email/
│       └── devolucion_pre_incapacidad.html                   [NEW]

apps/frontend/sistema-interno/src/
├── types/
│   └── preIncapacidad.ts                                     [NEW]
├── services/
│   └── preIncapacidadService.ts                              [NEW]
├── router/
│   └── index.tsx                                             [MODIFY] +routes
├── components/
│   ├── layout/
│   │   └── Sidebar.tsx                                       [MODIFY] +nav entry
│   └── pre-incapacidades/                                    [NEW dir]
│       ├── ValidationInconsistenciasList.tsx                 [NEW]
│       ├── DevolucionModal.tsx                               [NEW]
│       └── ResolverEntidadesPanel.tsx                        [NEW]
└── pages/
    └── pre-incapacidades/                                    [NEW dir]
        ├── BandejaPage.tsx                                   [NEW]
        └── GestionarPreIncapacidadPage.tsx                   [NEW]
```

---

## Chunk 1: Backend — DB Migration + New Endpoints

### Task 1: Add `motivo_devolucion` to pre_incapacidad + internal endpoints

**Files:**
- Modify: `apps/backend/app/models/pre_incapacidad.py`
- Create: `apps/backend/alembic/versions/xxxx_add_motivo_devolucion.py`
- Modify: `apps/backend/app/api/v1/endpoints/pre_incapacidades.py`

- [ ] **Step 1: Add field to model**

Edit `apps/backend/app/models/pre_incapacidad.py` — add after `error_procesamiento`:

```python
    # ── Devolución (set by internal users) ───────────────────────────────────
    motivo_devolucion: Mapped[Optional[str]] = mapped_column(Text)
```

- [ ] **Step 2: Create Alembic migration**

Run from `apps/backend/`:
```bash
make migrate msg="add motivo_devolucion to pre_incapacidad"
```

Edit the generated file so `upgrade()` reads:
```python
def upgrade() -> None:
    op.add_column(
        'pre_incapacidad',
        sa.Column('motivo_devolucion', sa.Text(), nullable=True)
    )

def downgrade() -> None:
    op.drop_column('pre_incapacidad', 'motivo_devolucion')
```

Apply:
```bash
make upgrade-db
```

Expected: Migration applies without errors.

- [ ] **Step 3: Add list schema and devolution schema to `schemas/pre_incapacidad.py`**

Edit `apps/backend/app/schemas/pre_incapacidad.py` — append at end:

```python
# ── Internal schemas (requires authentication) ─────────────────────────────────

class PreIncapacidadListItem(BaseModel):
    """Fila resumida para la bandeja interna."""
    id: UUID
    numero_radicacion: int
    estado: str
    tipo: str
    empleado_nombres: str
    empleado_numero_documento: str
    empresa_nit: Optional[str]
    empresa_nombre: Optional[str]
    fecha_inicio: date
    fecha_fin: date
    dias_totales: int
    total_errores: int = 0
    total_warnings: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


class PreIncapacidadUpdate(BaseModel):
    """Campos editables por el usuario interno para corregir datos."""
    empresa_nit: Optional[str] = None
    empresa_nombre: Optional[str] = None
    empleado_tipo_documento: Optional[str] = None
    empleado_numero_documento: Optional[str] = None
    empleado_nombres: Optional[str] = None
    empleado_apellidos: Optional[str] = None
    empleado_email: Optional[str] = None
    tipo_enfermedad: Optional[str] = None
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    diagnostico_cie10: Optional[str] = None
    descripcion_diagnostico: Optional[str] = None
    nombre_medico: Optional[str] = None
    registro_medico: Optional[str] = None
    ips: Optional[str] = None
    valor_dia: Optional[Decimal] = None


class DevolucionRequest(BaseModel):
    """Cuerpo del request para devolver una pre-incapacidad."""
    motivo: str = Field(..., min_length=20, max_length=2000,
                        description="Motivo de devolución (mínimo 20 caracteres)")


class DevolucionResponse(BaseModel):
    """Respuesta de la operación de devolución."""
    id: UUID
    estado: str
    motivo_devolucion: str
    email_enviado: bool


class PromocionResponse(BaseModel):
    """Respuesta de la operación de promoción manual."""
    success: bool
    pre_incapacidad_id: UUID
    incapacidad_id: Optional[UUID] = None
    errors: int
    warnings: int
    message: str
```

- [ ] **Step 4: Add internal endpoints to `pre_incapacidades.py`**

Append at the end of `apps/backend/app/api/v1/endpoints/pre_incapacidades.py`:

```python
# ── Internal endpoints (require JWT authentication) ────────────────────────────

from app.core.security import get_current_user
from app.models.usuario import Usuario
from app.schemas.pre_incapacidad import (
    PreIncapacidadListItem,
    PreIncapacidadUpdate,
    DevolucionRequest,
    DevolucionResponse,
    PromocionResponse,
)
from app.schemas.validation_inconsistencia import ValidationInconsistenciaRead
from app.db.repositories.validation_inconsistencia_repository import ValidationInconsistenciaRepository
from sqlalchemy import select, func


@router.get(
    "/",
    response_model=list[PreIncapacidadListItem],
    summary="[Interno] Listar pre-incapacidades",
    description="Lista pre-incapacidades para la bandeja interna. Requiere autenticación.",
)
async def listar_pre_incapacidades(
    estado: Optional[str] = Query(None, description="PENDIENTE | RECHAZADA | ERROR | DEVUELTA"),
    search: Optional[str] = Query(None, description="Buscar por documento o nombres del empleado"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> list[PreIncapacidadListItem]:
    """Lista pre-incapacidades de la bandeja interna con conteo de issues."""
    from app.models.pre_incapacidad import PreIncapacidad
    from app.models.validation_inconsistencia import ValidationInconsistencia

    query = select(PreIncapacidad)

    # Filtro por estado (por defecto: PENDIENTE + RECHAZADA + ERROR)
    if estado:
        query = query.where(PreIncapacidad.estado == estado)
    else:
        query = query.where(
            PreIncapacidad.estado.in_(["PENDIENTE", "RECHAZADA", "ERROR"])
        )

    # Filtro por búsqueda
    if search:
        query = query.where(
            (PreIncapacidad.empleado_nombres.ilike(f"%{search}%")) |
            (PreIncapacidad.empleado_numero_documento.ilike(f"%{search}%")) |
            (PreIncapacidad.empresa_nombre.ilike(f"%{search}%"))
        )

    query = query.order_by(PreIncapacidad.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    pre_incapacidades = result.scalars().all()

    # Enriquecer con conteos de issues
    items = []
    for pre_inc in pre_incapacidades:
        # Count issues for this pre_incapacidad
        count_query = select(
            ValidationInconsistencia.severidad,
            func.count(ValidationInconsistencia.id).label("cnt")
        ).where(
            ValidationInconsistencia.pre_incapacidad_id == pre_inc.id
        ).group_by(ValidationInconsistencia.severidad)

        count_result = await db.execute(count_query)
        counts = {row.severidad: row.cnt for row in count_result}

        items.append(PreIncapacidadListItem(
            id=pre_inc.id,
            numero_radicacion=pre_inc.numero_radicacion,
            estado=pre_inc.estado,
            tipo=pre_inc.tipo,
            empleado_nombres=pre_inc.empleado_nombres,
            empleado_numero_documento=pre_inc.empleado_numero_documento,
            empresa_nit=pre_inc.empresa_nit,
            empresa_nombre=pre_inc.empresa_nombre,
            fecha_inicio=pre_inc.fecha_inicio,
            fecha_fin=pre_inc.fecha_fin,
            dias_totales=pre_inc.dias_totales,
            total_errores=counts.get("ERROR", 0),
            total_warnings=counts.get("WARNING", 0),
            created_at=pre_inc.created_at,
        ))

    return items


@router.patch(
    "/{pre_incapacidad_id}",
    response_model=PreIncapacidadResponse,
    summary="[Interno] Corregir datos de pre-incapacidad",
    description="Permite al usuario interno corregir campos de la pre-incapacidad antes de promover.",
)
async def actualizar_pre_incapacidad(
    pre_incapacidad_id: UUID,
    data: PreIncapacidadUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> PreIncapacidadResponse:
    service = PreIncapacidadService(db)
    pre_inc = await service.repo.get_by_id(db, pre_incapacidad_id)
    if not pre_inc:
        from app.core.exceptions import NotFoundException
        raise NotFoundException(f"Pre-incapacidad {pre_incapacidad_id} no encontrada")

    # Apply only provided fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(pre_inc, field, value)

    # Recalculate dias_totales if dates changed
    if "fecha_inicio" in update_data or "fecha_fin" in update_data:
        pre_inc.dias_totales = (pre_inc.fecha_fin - pre_inc.fecha_inicio).days + 1

    db.add(pre_inc)
    await db.commit()
    await db.refresh(pre_inc)
    return PreIncapacidadResponse.model_validate(pre_inc)


@router.post(
    "/{pre_incapacidad_id}/devolver",
    response_model=DevolucionResponse,
    summary="[Interno] Devolver pre-incapacidad al solicitante",
    description=(
        "Cambia el estado a DEVUELTA, guarda el motivo, y envía una carta formal "
        "por email al solicitante. Requiere autenticación."
    ),
)
async def devolver_pre_incapacidad(
    pre_incapacidad_id: UUID,
    data: DevolucionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> DevolucionResponse:
    service = PreIncapacidadService(db)
    repo = service.repo

    pre_inc = await repo.get_by_id(db, pre_incapacidad_id)
    if not pre_inc:
        from app.core.exceptions import NotFoundException
        raise NotFoundException(f"Pre-incapacidad {pre_incapacidad_id} no encontrada")

    # Update estado and reason
    pre_inc.estado = "DEVUELTA"
    pre_inc.motivo_devolucion = data.motivo
    db.add(pre_inc)
    await db.commit()
    await db.refresh(pre_inc)

    # Send devolution email via Celery (fire-and-forget)
    email_sent = False
    try:
        from app.tasks.email_tasks import send_devolucion_pre_incapacidad_email_task
        send_devolucion_pre_incapacidad_email_task.delay(
            correo_solicitante=pre_inc.solicitante_correo,
            solicitante_nombre=pre_inc.solicitante_nombres,
            numero_radicacion=str(pre_inc.numero_radicacion),
            empleado_nombre=pre_inc.empleado_nombres,
            empleado_documento=pre_inc.empleado_numero_documento,
            empresa_nombre=pre_inc.empresa_nombre or "Independiente",
            fecha_inicio=str(pre_inc.fecha_inicio),
            dias_totales=pre_inc.dias_totales,
            motivo=data.motivo,
            usuario_nombre=f"{current_user.nombres} {current_user.apellidos}",
        )
        email_sent = True
    except Exception as e:
        import logging
        logging.error(f"Failed to enqueue devolucion email for {pre_incapacidad_id}: {e}")

    return DevolucionResponse(
        id=pre_inc.id,
        estado=pre_inc.estado,
        motivo_devolucion=pre_inc.motivo_devolucion,
        email_enviado=email_sent,
    )


@router.post(
    "/{pre_incapacidad_id}/promover",
    response_model=PromocionResponse,
    summary="[Interno] Promover manualmente a incapacidad",
    description=(
        "Limpia validaciones previas, re-valida con la data actual, y crea la Incapacidad "
        "si no quedan ERRORs. Requiere autenticación."
    ),
)
async def promover_pre_incapacidad(
    pre_incapacidad_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> PromocionResponse:
    from app.services.pre_incapacidad_promotion_service import PromotePreIncapacidadService

    service = PromotePreIncapacidadService(db)
    result = await service.promote_pre_incapacidad(
        pre_incapacidad_id,
        clear_existing_issues=True,
        usuario_id=current_user.id,
    )

    return PromocionResponse(
        success=result.success,
        pre_incapacidad_id=result.pre_incapacidad_id,
        incapacidad_id=result.incapacidad_id,
        errors=result.validation_summary.errors,
        warnings=result.validation_summary.warnings,
        message="Incapacidad creada exitosamente" if result.success else result.error_message or "Validación fallida",
    )
```

Note: these imports are needed at the top of `pre_incapacidades.py` (add to existing imports):
```python
from fastapi import Query
from typing import Optional
```

- [ ] **Step 5: Run tests to make sure public endpoints still pass**

```bash
docker compose exec api sh -c "python -m pytest tests/test_pre_incapacidad_api.py -v --no-cov"
```

Expected: 15 passed (same as before).

- [ ] **Step 6: Commit**

```bash
git add apps/backend/app/models/pre_incapacidad.py \
        apps/backend/app/schemas/pre_incapacidad.py \
        apps/backend/app/api/v1/endpoints/pre_incapacidades.py \
        apps/backend/alembic/versions/
git commit -m "feat: add motivo_devolucion field and internal pre-incapacidad endpoints"
```

---

## Chunk 2: Backend — Service Updates + Email

### Task 2: Update PromotePreIncapacidadService + ValidationInconsistenciaRepository + Email template

**Files:**
- Modify: `apps/backend/app/db/repositories/validation_inconsistencia_repository.py`
- Modify: `apps/backend/app/services/pre_incapacidad_promotion_service.py`
- Modify: `apps/backend/app/tasks/email_tasks.py`
- Create: `apps/backend/app/templates/email/devolucion_pre_incapacidad.html`

- [ ] **Step 1: Add `delete_by_pre_incapacidad` to ValidationInconsistenciaRepository**

Edit `apps/backend/app/db/repositories/validation_inconsistencia_repository.py` — add method after `has_errors`:

```python
    async def delete_by_pre_incapacidad(self, pre_inc_id: UUID) -> int:
        """Elimina todas las inconsistencias de una pre-incapacidad. Retorna el número eliminado."""
        from sqlalchemy import delete
        stmt = delete(ValidationInconsistencia).where(
            ValidationInconsistencia.pre_incapacidad_id == pre_inc_id
        )
        result = await self.db.execute(stmt)
        return result.rowcount
```

- [ ] **Step 2: Update `PromotePreIncapacidadService.promote_pre_incapacidad()` signature**

Edit `apps/backend/app/services/pre_incapacidad_promotion_service.py`.

Change the method signature from:
```python
    async def promote_pre_incapacidad(
        self,
        pre_incapacidad_id: UUID,
    ) -> PromotionResult:
```
To:
```python
    async def promote_pre_incapacidad(
        self,
        pre_incapacidad_id: UUID,
        clear_existing_issues: bool = False,
        usuario_id: Optional[UUID] = None,
    ) -> PromotionResult:
```

Add `from typing import Optional` to imports if not present.

- [ ] **Step 3: Add clear-issues step at the top of `promote_pre_incapacidad`**

After the `if not pre_inc: return ...` block and before `# 2. Fetch related entities`, add:

```python
            # 1b. Optionally clear existing validation issues (for manual re-promotion)
            if clear_existing_issues:
                deleted = await self.validation_repo.delete_by_pre_incapacidad(pre_incapacidad_id)
                await self.db.commit()
                logger.info(f"Cleared {deleted} existing issues for {pre_incapacidad_id}")
```

- [ ] **Step 4: Implement Incapacidad creation (replace the `# TODO`)**

In `promote_pre_incapacidad()`, find:
```python
            # 6. Crear incapacidad (MOCK para ahora)
            # TODO: Implementar creación de incapacidad cuando service esté disponible
            logger.info(
                f"Pre-incapacidad {pre_incapacidad_id} validation passed - "
                f"creating incapacidad..."
            )
            await self.pre_inc_repo.update_estado(self.db, pre_incapacidad_id, "PROCESADA")
            await self.db.commit()  # Commit estado change

            return PromotionResult(
                success=True,
                pre_incapacidad_id=pre_incapacidad_id,
                incapacidad_id=None,  # TODO: set when created
                validation_summary=validation_summary,
                timestamp=datetime.utcnow(),
            )
```

Replace with:
```python
            # 6. Crear incapacidad real
            logger.info(
                f"Pre-incapacidad {pre_incapacidad_id} validation passed - "
                f"creating incapacidad..."
            )
            incapacidad_id = None
            try:
                from app.services.incapacidad_service import incapacidad_service
                from app.schemas.incapacidad import IncapacidadCreate
                from app.utils.enums import TipoIncapacidad

                inc_data = IncapacidadCreate(
                    tipo=TipoIncapacidad.ARL,
                    empleado_id=empleado.id if empleado else None,
                    empresa_id=empresa.id if empresa else None,
                    fecha_inicio=pre_inc.fecha_inicio,
                    fecha_fin=pre_inc.fecha_fin,
                    diagnostico_cie10=pre_inc.diagnostico_cie10,
                    descripcion_diagnostico=pre_inc.descripcion_diagnostico,
                    nombre_medico=pre_inc.nombre_medico,
                    registro_medico=pre_inc.registro_medico,
                    ips=pre_inc.ips,
                    valor_dia=pre_inc.valor_dia,
                    observaciones=pre_inc.observaciones,
                )
                incapacidad = await incapacidad_service.create_incapacidad(
                    self.db, inc_data, usuario_id=usuario_id
                )
                incapacidad_id = incapacidad.id
                logger.info(f"Created incapacidad {incapacidad_id} from pre-incapacidad {pre_incapacidad_id}")
            except Exception as e:
                logger.error(f"Failed to create incapacidad from {pre_incapacidad_id}: {e}")
                raise

            await self.pre_inc_repo.update_estado(self.db, pre_incapacidad_id, "PROCESADA")
            await self.db.commit()

            return PromotionResult(
                success=True,
                pre_incapacidad_id=pre_incapacidad_id,
                incapacidad_id=incapacidad_id,
                validation_summary=validation_summary,
                timestamp=datetime.utcnow(),
            )
```

- [ ] **Step 5: Add devolution email task**

Edit `apps/backend/app/tasks/email_tasks.py` — append at end:

```python
@celery_app.task(name="send_devolucion_pre_incapacidad_email")
def send_devolucion_pre_incapacidad_email_task(
    correo_solicitante: str,
    solicitante_nombre: str,
    numero_radicacion: str,
    empleado_nombre: str,
    empleado_documento: str,
    empresa_nombre: str,
    fecha_inicio: str,
    dias_totales: int,
    motivo: str,
    usuario_nombre: str,
):
    """Envía carta de devolución formal al solicitante."""
    logger.info(f"[EMAIL] Enviando devolución radicación {numero_radicacion} a {correo_solicitante}")
    try:
        from datetime import datetime as dt
        context = {
            "solicitante_nombre": solicitante_nombre,
            "numero_radicacion": numero_radicacion,
            "empleado_nombre": empleado_nombre,
            "empleado_documento": empleado_documento,
            "empresa_nombre": empresa_nombre,
            "fecha_inicio": fecha_inicio,
            "dias_totales": dias_totales,
            "motivo": motivo,
            "usuario_nombre": usuario_nombre,
            "fecha_devolucion": dt.utcnow().strftime("%d de %B de %Y"),
            "year": dt.utcnow().year,
        }
        success = email_service.send_template_email(
            to=correo_solicitante,
            subject=f"Devolución Radicación N° {numero_radicacion} — Información Requerida",
            template_name="devolucion_pre_incapacidad.html",
            context=context,
        )
        return {"status": "sent" if success else "failed", "to": correo_solicitante}
    except Exception as e:
        logger.error(f"[EMAIL] Error al enviar devolución: {e}")
        return {"status": "error", "error": str(e)}
```

- [ ] **Step 6: Create email template**

Create `apps/backend/app/templates/email/devolucion_pre_incapacidad.html`:

```html
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Devolución de Radicación</title>
  <style>
    body { font-family: Arial, sans-serif; background: #f4f4f4; margin: 0; padding: 20px; }
    .container { max-width: 680px; margin: auto; background: #fff; border: 1px solid #ddd; }
    .header { background: #003366; color: #fff; padding: 24px 32px; }
    .header h1 { margin: 0; font-size: 20px; letter-spacing: 1px; text-transform: uppercase; }
    .header p { margin: 4px 0 0; font-size: 13px; opacity: 0.8; }
    .body { padding: 32px; color: #333; line-height: 1.7; }
    .ref { font-size: 13px; color: #555; margin-bottom: 24px; border-left: 3px solid #003366; padding-left: 12px; }
    .ref strong { color: #003366; }
    .motivo-box { background: #fef9e7; border: 1px solid #f0c040; border-radius: 4px; padding: 16px 20px; margin: 24px 0; }
    .motivo-box p { margin: 0; font-size: 14px; }
    .footer { background: #f8f9fa; border-top: 1px solid #ddd; padding: 16px 32px; font-size: 12px; color: #777; }
    .firma { margin-top: 32px; padding-top: 16px; border-top: 1px solid #eee; }
    table.datos { width: 100%; border-collapse: collapse; margin: 16px 0; font-size: 13px; }
    table.datos td { padding: 6px 8px; border-bottom: 1px solid #f0f0f0; }
    table.datos td:first-child { color: #555; width: 180px; }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>Seguros Alfa — Gestión de Incapacidades</h1>
      <p>Comunicación Oficial</p>
    </div>

    <div class="body">
      <p>{{ fecha_devolucion }}</p>

      <p>Señor(a) <strong>{{ solicitante_nombre }}</strong>,</p>

      <p>Por medio de la presente, nos dirigimos a usted en relación con la radicación de incapacidad
      enviada a través de nuestro portal, para informarle que la misma ha sido revisada por nuestro
      equipo de gestión y <strong>requiere corrección o información adicional</strong> antes de poder
      ser procesada.</p>

      <div class="ref">
        <strong>Referencia de la solicitud:</strong><br>
        Radicación N° {{ numero_radicacion }}
      </div>

      <p><strong>Datos de la radicación:</strong></p>
      <table class="datos">
        <tr><td>Empleado:</td><td>{{ empleado_nombre }} — {{ empleado_documento }}</td></tr>
        <tr><td>Empresa:</td><td>{{ empresa_nombre }}</td></tr>
        <tr><td>Fecha inicio:</td><td>{{ fecha_inicio }}</td></tr>
        <tr><td>Días solicitados:</td><td>{{ dias_totales }}</td></tr>
      </table>

      <p><strong>Motivo de la devolución:</strong></p>
      <div class="motivo-box">
        <p>{{ motivo }}</p>
      </div>

      <p>Le solicitamos amablemente corregir la información señalada y radicar nuevamente su solicitud
      a través del portal de radicación en el menor tiempo posible, para evitar demoras en el
      procesamiento de su incapacidad.</p>

      <p>Si tiene alguna pregunta o requiere asistencia, puede comunicarse con nuestro equipo de
      soporte.</p>

      <div class="firma">
        <p>Cordialmente,</p>
        <p><strong>{{ usuario_nombre }}</strong><br>
        Equipo de Gestión de Incapacidades<br>
        Seguros Alfa</p>
      </div>
    </div>

    <div class="footer">
      <p>Este es un mensaje automático generado por el sistema de gestión de incapacidades de Seguros Alfa.
      Por favor no responda a este correo directamente.</p>
      <p>&copy; {{ year }} Seguros Alfa. Todos los derechos reservados.</p>
    </div>
  </div>
</body>
</html>
```

- [ ] **Step 7: Verify backend starts correctly**

```bash
docker compose restart api
docker compose logs api --tail=30
```

Expected: No import errors, server starts on port 8010.

- [ ] **Step 8: Verify new endpoints appear in Swagger**

Open http://localhost:8010/docs — confirm `GET /pre-incapacidades/`, `PATCH /pre-incapacidades/{id}`, `POST /pre-incapacidades/{id}/devolver`, `POST /pre-incapacidades/{id}/promover` appear under the `pre-incapacidades` tag.

- [ ] **Step 9: Commit**

```bash
git add apps/backend/app/db/repositories/validation_inconsistencia_repository.py \
        apps/backend/app/services/pre_incapacidad_promotion_service.py \
        apps/backend/app/tasks/email_tasks.py \
        apps/backend/app/templates/email/devolucion_pre_incapacidad.html
git commit -m "feat: implement Incapacidad creation in promotion service, add devolution email"
```

---

## Chunk 3: Frontend — Types, Service, Router & Sidebar

### Task 3: TypeScript types + service + routing for pre-incapacidades

**Files:**
- Create: `apps/frontend/sistema-interno/src/types/preIncapacidad.ts`
- Create: `apps/frontend/sistema-interno/src/services/preIncapacidadService.ts`
- Modify: `apps/frontend/sistema-interno/src/router/index.tsx`
- Modify: `apps/frontend/sistema-interno/src/components/layout/Sidebar.tsx`

- [ ] **Step 1: Create TypeScript types**

Create `apps/frontend/sistema-interno/src/types/preIncapacidad.ts`:

```typescript
import type { ValidationInconsistenciaRead } from './validationInconsistencia';

export type EstadoPreIncapacidad =
  | 'PENDIENTE'
  | 'PROCESADA'
  | 'RECHAZADA'
  | 'DEVUELTA'
  | 'ERROR';

export interface PreIncapacidadListItem {
  id: string;
  numero_radicacion: number;
  estado: EstadoPreIncapacidad;
  tipo: 'ARL' | 'SALUD';
  empleado_nombres: string;
  empleado_numero_documento: string;
  empresa_nit: string | null;
  empresa_nombre: string | null;
  fecha_inicio: string;
  fecha_fin: string;
  dias_totales: number;
  total_errores: number;
  total_warnings: number;
  created_at: string;
}

export interface PreDocumento {
  id: string;
  tipo_documento: string;
  nombre_original: string;
  estado_subida: 'OK' | 'ERROR';
  created_at: string;
}

export interface PreIncapacidadDetalle {
  id: string;
  numero_radicacion: number;
  estado: EstadoPreIncapacidad;
  tipo: string;
  tipo_enfermedad: string;
  // Solicitante
  solicitante_correo: string;
  solicitante_nombres: string;
  solicitante_apellidos: string | null;
  solicitante_telefono: string | null;
  // Empresa
  empresa_nit: string | null;
  empresa_nombre: string | null;
  // Empleado
  empleado_tipo_documento: string;
  empleado_numero_documento: string;
  empleado_nombres: string;
  empleado_apellidos: string | null;
  empleado_email: string | null;
  // Incapacidad
  fecha_inicio: string;
  fecha_fin: string;
  dias_totales: number;
  diagnostico_cie10: string;
  descripcion_diagnostico: string | null;
  nombre_medico: string;
  registro_medico: string;
  ips: string | null;
  valor_dia: string | null;
  // Trazabilidad
  error_procesamiento: string | null;
  motivo_devolucion: string | null;
  created_at: string;
  // Relaciones
  documentos: PreDocumento[];
  validation_inconsistencias: ValidationInconsistenciaRead[];
}

export interface PreIncapacidadUpdate {
  empresa_nit?: string;
  empresa_nombre?: string;
  empleado_tipo_documento?: string;
  empleado_numero_documento?: string;
  empleado_nombres?: string;
  empleado_apellidos?: string;
  empleado_email?: string;
  tipo_enfermedad?: string;
  fecha_inicio?: string;
  fecha_fin?: string;
  diagnostico_cie10?: string;
  descripcion_diagnostico?: string;
  nombre_medico?: string;
  registro_medico?: string;
  ips?: string;
  valor_dia?: number;
}

export interface DevolucionRequest {
  motivo: string;
}

export interface DevolucionResponse {
  id: string;
  estado: string;
  motivo_devolucion: string;
  email_enviado: boolean;
}

export interface PromocionResponse {
  success: boolean;
  pre_incapacidad_id: string;
  incapacidad_id: string | null;
  errors: number;
  warnings: number;
  message: string;
}

export interface BandejaFiltros {
  estado?: EstadoPreIncapacidad;
  search?: string;
  skip?: number;
  limit?: number;
}
```

Create `apps/frontend/sistema-interno/src/types/validationInconsistencia.ts`:

```typescript
export type Severidad = 'ERROR' | 'WARNING' | 'INFO';
export type Categoria =
  | 'FIELD_VALIDATION'
  | 'BUSINESS_RULE'
  | 'FRAUD_ALERT'
  | 'INTEGRATION_CHECK';

export interface ValidationInconsistenciaRead {
  id: string;
  pre_incapacidad_id: string;
  incapacidad_id: string | null;
  categoria: Categoria;
  severidad: Severidad;
  codigo: string;
  descripcion: string;
  campo_afectado: string | null;
  valor_encontrado: string | null;
  valor_esperado: string | null;
  fecha_deteccion: string;
}
```

Update `apps/frontend/sistema-interno/src/types/index.ts` — add exports:
```typescript
export * from './preIncapacidad';
export * from './validationInconsistencia';
```

- [ ] **Step 2: Create pre-incapacidad API service**

Create `apps/frontend/sistema-interno/src/services/preIncapacidadService.ts`:

```typescript
import api from '@/lib/api';
import type {
  PreIncapacidadListItem,
  PreIncapacidadDetalle,
  PreIncapacidadUpdate,
  DevolucionRequest,
  DevolucionResponse,
  PromocionResponse,
  BandejaFiltros,
} from '@/types/preIncapacidad';

export const preIncapacidadService = {
  /**
   * GET /api/v1/pre-incapacidades/
   * Bandeja interna — lista con filtros.
   */
  async listar(filtros: BandejaFiltros = {}): Promise<PreIncapacidadListItem[]> {
    const params = Object.fromEntries(
      Object.entries({
        estado: filtros.estado,
        search: filtros.search,
        skip: filtros.skip ?? 0,
        limit: filtros.limit ?? 50,
      }).filter(([_, v]) => v !== undefined && v !== null && v !== '')
    );
    const { data } = await api.get<PreIncapacidadListItem[]>('/pre-incapacidades/', { params });
    return data;
  },

  /**
   * GET /api/v1/pre-incapacidades/{id}
   */
  async getById(id: string): Promise<PreIncapacidadDetalle> {
    const { data } = await api.get<PreIncapacidadDetalle>(`/pre-incapacidades/${id}`);
    return data;
  },

  /**
   * PATCH /api/v1/pre-incapacidades/{id}
   */
  async actualizar(id: string, data: PreIncapacidadUpdate): Promise<PreIncapacidadDetalle> {
    const { data: response } = await api.patch<PreIncapacidadDetalle>(`/pre-incapacidades/${id}`, data);
    return response;
  },

  /**
   * POST /api/v1/pre-incapacidades/{id}/devolver
   */
  async devolver(id: string, motivo: DevolucionRequest): Promise<DevolucionResponse> {
    const { data } = await api.post<DevolucionResponse>(`/pre-incapacidades/${id}/devolver`, motivo);
    return data;
  },

  /**
   * POST /api/v1/pre-incapacidades/{id}/promover
   */
  async promover(id: string): Promise<PromocionResponse> {
    const { data } = await api.post<PromocionResponse>(`/pre-incapacidades/${id}/promover`);
    return data;
  },
};
```

Update `apps/frontend/sistema-interno/src/services/index.ts` — add export:
```typescript
export { preIncapacidadService } from './preIncapacidadService';
```

- [ ] **Step 3: Add routes to router**

Edit `apps/frontend/sistema-interno/src/router/index.tsx`.

Add imports at top:
```typescript
import { BandejaPage } from '@/pages/pre-incapacidades/BandejaPage';
import { GestionarPreIncapacidadPage } from '@/pages/pre-incapacidades/GestionarPreIncapacidadPage';
```

Inside the `children` of the protected `AppShell` route, after the `incapacidades` route block, add:
```typescript
          // Pre-Incapacidades — ADMIN y AUDITOR
          {
            path: '/pre-incapacidades',
            element: <ProtectedRoute allowedRoles={[RolUsuario.ADMIN, RolUsuario.AUDITOR]} />,
            children: [
              {
                path: 'bandeja',
                element: <BandejaPage />,
              },
              {
                path: ':id/gestionar',
                element: <GestionarPreIncapacidadPage />,
              },
            ],
          },
```

- [ ] **Step 4: Add navigation entry to Sidebar**

Edit `apps/frontend/sistema-interno/src/components/layout/Sidebar.tsx`.

Add import `Inbox` from lucide-react:
```typescript
import {
  // ...existing imports...
  Inbox,
} from 'lucide-react';
```

In `menuItems`, add a new entry after the `Incapacidades` item:
```typescript
  {
    label: 'Pre-Incapacidades',
    icon: Inbox,
    children: [
      {
        label: 'Bandeja',
        icon: ClipboardList,
        href: '/pre-incapacidades/bandeja',
        roles: ['ADMIN', 'AUDITOR'],
      },
    ],
  },
```

- [ ] **Step 5: Verify dev server starts**

```bash
cd apps/frontend/sistema-interno && npm run dev
```

Expected: No TypeScript errors, dev server starts.

- [ ] **Step 6: Commit**

```bash
git add apps/frontend/sistema-interno/src/types/ \
        apps/frontend/sistema-interno/src/services/preIncapacidadService.ts \
        apps/frontend/sistema-interno/src/services/index.ts \
        apps/frontend/sistema-interno/src/router/index.tsx \
        apps/frontend/sistema-interno/src/components/layout/Sidebar.tsx
git commit -m "feat: add pre-incapacidad types, service, router and sidebar navigation"
```

---

## Chunk 4: Frontend — Bandeja Page

### Task 4: Build the BandejaPage inbox

**Files:**
- Create: `apps/frontend/sistema-interno/src/pages/pre-incapacidades/BandejaPage.tsx`

- [ ] **Step 1: Create `pages/pre-incapacidades/` directory and `BandejaPage.tsx`**

```typescript
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { Inbox, Search, AlertCircle, AlertTriangle, CheckCircle, Clock } from 'lucide-react';
import type { ColumnDef } from '@tanstack/react-table';

import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { DataTable } from '@/components/shared/DataTable';
import { preIncapacidadService } from '@/services/preIncapacidadService';
import type { PreIncapacidadListItem, EstadoPreIncapacidad } from '@/types/preIncapacidad';
import { formatDate, formatRelativeDate } from '@/utils/formatters';
import { useDebounce } from '@/hooks/useDebounce';

function EstadoBadge({ estado }: { estado: EstadoPreIncapacidad }) {
  const config: Record<EstadoPreIncapacidad, { variant: 'default' | 'secondary' | 'destructive' | 'outline'; label: string }> = {
    PENDIENTE: { variant: 'default', label: 'Pendiente' },
    RECHAZADA: { variant: 'destructive', label: 'Rechazada' },
    ERROR: { variant: 'outline', label: 'Error' },
    DEVUELTA: { variant: 'secondary', label: 'Devuelta' },
    PROCESADA: { variant: 'default', label: 'Procesada' },
  };
  const { variant, label } = config[estado] ?? { variant: 'outline', label: estado };
  return <Badge variant={variant}>{label}</Badge>;
}

function IssueCount({ errors, warnings }: { errors: number; warnings: number }) {
  if (errors === 0 && warnings === 0) return <span className="text-slate-400 text-sm">—</span>;
  return (
    <div className="flex items-center gap-2">
      {errors > 0 && (
        <span className="flex items-center gap-1 text-red-600 text-sm font-medium">
          <AlertCircle className="h-3.5 w-3.5" />
          {errors}
        </span>
      )}
      {warnings > 0 && (
        <span className="flex items-center gap-1 text-yellow-600 text-sm">
          <AlertTriangle className="h-3.5 w-3.5" />
          {warnings}
        </span>
      )}
    </div>
  );
}

const columns: ColumnDef<PreIncapacidadListItem>[] = [
  {
    accessorKey: 'numero_radicacion',
    header: 'N° Radicación',
    cell: ({ row }) => (
      <span className="font-mono text-sm font-semibold">{row.original.numero_radicacion}</span>
    ),
  },
  {
    accessorKey: 'estado',
    header: 'Estado',
    cell: ({ row }) => <EstadoBadge estado={row.original.estado} />,
  },
  {
    accessorKey: 'empleado_nombres',
    header: 'Empleado',
    cell: ({ row }) => (
      <div>
        <p className="font-medium">{row.original.empleado_nombres}</p>
        <p className="text-sm text-slate-500">{row.original.empleado_numero_documento}</p>
      </div>
    ),
  },
  {
    accessorKey: 'empresa_nombre',
    header: 'Empresa',
    cell: ({ row }) =>
      row.original.empresa_nombre ? (
        <div>
          <p className="font-medium text-sm">{row.original.empresa_nombre}</p>
          <p className="text-xs text-slate-500">NIT: {row.original.empresa_nit}</p>
        </div>
      ) : (
        <span className="text-slate-400 text-sm">Independiente</span>
      ),
  },
  {
    accessorKey: 'fecha_inicio',
    header: 'Período',
    cell: ({ row }) => (
      <div className="text-sm">
        <p>{formatDate(row.original.fecha_inicio)}</p>
        <p className="text-slate-500">{row.original.dias_totales} días</p>
      </div>
    ),
  },
  {
    id: 'issues',
    header: 'Issues',
    cell: ({ row }) => (
      <IssueCount errors={row.original.total_errores} warnings={row.original.total_warnings} />
    ),
  },
  {
    accessorKey: 'created_at',
    header: 'Radicado',
    cell: ({ row }) => (
      <div className="text-sm">
        <p>{formatDate(row.original.created_at)}</p>
        <p className="text-slate-500 flex items-center gap-1">
          <Clock className="h-3 w-3" />
          {formatRelativeDate(row.original.created_at)}
        </p>
      </div>
    ),
  },
  {
    id: 'actions',
    header: '',
    cell: ({ row }) => {
      const navigate = useNavigate();
      return (
        <Button
          size="sm"
          variant="default"
          onClick={() => navigate(`/pre-incapacidades/${row.original.id}/gestionar`)}
        >
          Gestionar
        </Button>
      );
    },
  },
];

export function BandejaPage() {
  const [search, setSearch] = useState('');
  const [estado, setEstado] = useState<string>('');
  const debouncedSearch = useDebounce(search, 300);

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['pre-incapacidades-bandeja', debouncedSearch, estado],
    queryFn: () =>
      preIncapacidadService.listar({
        search: debouncedSearch || undefined,
        estado: (estado as EstadoPreIncapacidad) || undefined,
      }),
    staleTime: 30_000,
    refetchInterval: 2 * 60_000,
  });

  const total = data?.length ?? 0;
  const totalErrores = data?.reduce((s, i) => s + i.total_errores, 0) ?? 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 flex items-center gap-3">
            <Inbox className="h-8 w-8 text-blue-600" />
            Bandeja Pre-Incapacidades
            {total > 0 && (
              <Badge variant="destructive" className="text-base">{total}</Badge>
            )}
          </h1>
          <p className="text-slate-500 mt-1">
            Pre-radicaciones que requieren revisión o corrección manual
          </p>
        </div>
        {totalErrores > 0 && (
          <div className="flex items-center gap-2 text-red-600 bg-red-50 border border-red-200 rounded-lg px-4 py-2">
            <AlertCircle className="h-5 w-5" />
            <span className="text-sm font-medium">{totalErrores} errores críticos</span>
          </div>
        )}
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <Input
            placeholder="Buscar por nombre o documento..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
        <Select value={estado} onValueChange={setEstado}>
          <SelectTrigger className="w-44">
            <SelectValue placeholder="Todos los estados" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="">Todos</SelectItem>
            <SelectItem value="PENDIENTE">Pendiente</SelectItem>
            <SelectItem value="RECHAZADA">Rechazada</SelectItem>
            <SelectItem value="ERROR">Error</SelectItem>
            <SelectItem value="DEVUELTA">Devuelta</SelectItem>
          </SelectContent>
        </Select>
        <Button variant="outline" onClick={() => refetch()}>
          Actualizar
        </Button>
      </div>

      {/* Table */}
      <div className="bg-white rounded-lg shadow">
        <div className="p-6">
          {!isLoading && total === 0 ? (
            <div className="text-center py-12">
              <CheckCircle className="mx-auto h-16 w-16 text-green-500" />
              <h3 className="mt-4 text-xl font-medium text-slate-900">¡Bandeja vacía!</h3>
              <p className="mt-2 text-slate-500">No hay pre-incapacidades pendientes de revisión.</p>
            </div>
          ) : (
            <DataTable
              columns={columns}
              data={data ?? []}
              isLoading={isLoading}
              emptyMessage="No se encontraron pre-incapacidades con los filtros aplicados."
            />
          )}
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Verify page renders without errors**

Open http://localhost:5173/pre-incapacidades/bandeja — should show the table (empty or with data).

- [ ] **Step 3: Commit**

```bash
git add apps/frontend/sistema-interno/src/pages/pre-incapacidades/
git commit -m "feat: add pre-incapacidad bandeja (inbox) page"
```

---

## Chunk 5: Frontend — Components + Gestión Detail Page

### Task 5: Validation list + devolution modal + resolver panel

**Files:**
- Create: `apps/frontend/sistema-interno/src/components/pre-incapacidades/ValidationInconsistenciasList.tsx`
- Create: `apps/frontend/sistema-interno/src/components/pre-incapacidades/DevolucionModal.tsx`
- Create: `apps/frontend/sistema-interno/src/components/pre-incapacidades/ResolverEntidadesPanel.tsx`

- [ ] **Step 1: Create ValidationInconsistenciasList**

```typescript
// apps/frontend/sistema-interno/src/components/pre-incapacidades/ValidationInconsistenciasList.tsx
import { AlertCircle, AlertTriangle, Info, ChevronDown, ChevronUp } from 'lucide-react';
import { useState } from 'react';
import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';
import { cn } from '@/lib/utils';
import type { ValidationInconsistenciaRead, Severidad, Categoria } from '@/types/validationInconsistencia';

interface Props {
  issues: ValidationInconsistenciaRead[];
}

const SEVERIDAD_CONFIG: Record<Severidad, { icon: typeof AlertCircle; className: string; label: string }> = {
  ERROR: { icon: AlertCircle, className: 'text-red-600 bg-red-50 border-red-200', label: 'Error' },
  WARNING: { icon: AlertTriangle, className: 'text-yellow-700 bg-yellow-50 border-yellow-200', label: 'Aviso' },
  INFO: { icon: Info, className: 'text-blue-600 bg-blue-50 border-blue-200', label: 'Info' },
};

const CATEGORIA_LABELS: Record<Categoria, string> = {
  FIELD_VALIDATION: 'Validación de campo',
  BUSINESS_RULE: 'Regla de negocio',
  FRAUD_ALERT: 'Alerta de fraude',
  INTEGRATION_CHECK: 'Verificación de integración',
};

function IssueRow({ issue }: { issue: ValidationInconsistenciaRead }) {
  const [expanded, setExpanded] = useState(false);
  const config = SEVERIDAD_CONFIG[issue.severidad];
  const Icon = config.icon;

  return (
    <div className={cn('border rounded-lg p-3 mb-2', config.className)}>
      <div
        className="flex items-start justify-between cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-start gap-2 flex-1">
          <Icon className="h-4 w-4 mt-0.5 flex-shrink-0" />
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium">{issue.descripcion}</p>
            <p className="text-xs opacity-70 mt-0.5">
              {CATEGORIA_LABELS[issue.categoria]} · <code className="font-mono">{issue.codigo}</code>
              {issue.campo_afectado && <> · campo: <code className="font-mono">{issue.campo_afectado}</code></>}
            </p>
          </div>
        </div>
        <button className="ml-2 flex-shrink-0 opacity-60 hover:opacity-100">
          {expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </button>
      </div>
      {expanded && (issue.valor_encontrado || issue.valor_esperado) && (
        <div className="mt-2 pt-2 border-t border-current border-opacity-20 grid grid-cols-2 gap-2 text-xs">
          {issue.valor_encontrado && (
            <div>
              <span className="opacity-70">Valor encontrado:</span>
              <code className="block font-mono mt-0.5">{issue.valor_encontrado}</code>
            </div>
          )}
          {issue.valor_esperado && (
            <div>
              <span className="opacity-70">Valor esperado:</span>
              <code className="block font-mono mt-0.5">{issue.valor_esperado}</code>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export function ValidationInconsistenciasList({ issues }: Props) {
  const errors = issues.filter((i) => i.severidad === 'ERROR');
  const warnings = issues.filter((i) => i.severidad === 'WARNING');
  const infos = issues.filter((i) => i.severidad === 'INFO');

  if (issues.length === 0) {
    return (
      <Card className="p-6 text-center bg-green-50 border-green-200">
        <AlertCircle className="h-8 w-8 text-green-600 mx-auto mb-2" />
        <p className="font-medium text-green-800">Sin inconsistencias detectadas</p>
        <p className="text-sm text-green-600 mt-1">Esta pre-incapacidad puede ser promovida.</p>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {/* Summary bar */}
      <div className="flex items-center gap-3">
        {errors.length > 0 && (
          <Badge variant="destructive" className="gap-1">
            <AlertCircle className="h-3.5 w-3.5" />
            {errors.length} error{errors.length > 1 ? 'es' : ''}
          </Badge>
        )}
        {warnings.length > 0 && (
          <Badge variant="outline" className="gap-1 border-yellow-400 text-yellow-700">
            <AlertTriangle className="h-3.5 w-3.5" />
            {warnings.length} aviso{warnings.length > 1 ? 's' : ''}
          </Badge>
        )}
        {infos.length > 0 && (
          <Badge variant="secondary" className="gap-1">
            <Info className="h-3.5 w-3.5" />
            {infos.length} info
          </Badge>
        )}
      </div>

      {/* Lists by severity */}
      {errors.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-red-700 uppercase tracking-wide mb-2">Errores bloqueantes</p>
          {errors.map((i) => <IssueRow key={i.id} issue={i} />)}
        </div>
      )}
      {warnings.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-yellow-700 uppercase tracking-wide mb-2">Avisos</p>
          {warnings.map((i) => <IssueRow key={i.id} issue={i} />)}
        </div>
      )}
      {infos.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-blue-600 uppercase tracking-wide mb-2">Información</p>
          {infos.map((i) => <IssueRow key={i.id} issue={i} />)}
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Create DevolucionModal**

```typescript
// apps/frontend/sistema-interno/src/components/pre-incapacidades/DevolucionModal.tsx
import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { CornerDownLeft, Loader2, Mail } from 'lucide-react';
import { z } from 'zod';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useToast } from '@/hooks/use-toast';
import { preIncapacidadService } from '@/services/preIncapacidadService';

const schema = z.object({
  motivo: z.string().min(20, 'El motivo debe tener al menos 20 caracteres').max(2000),
});
type FormData = z.infer<typeof schema>;

interface Props {
  preIncapacidadId: string;
  numeroRadicacion: number;
  solicitanteCorreo: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess: () => void;
}

export function DevolucionModal({
  preIncapacidadId,
  numeroRadicacion,
  solicitanteCorreo,
  open,
  onOpenChange,
  onSuccess,
}: Props) {
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FormData>({ resolver: zodResolver(schema) });

  const mutation = useMutation({
    mutationFn: (data: FormData) =>
      preIncapacidadService.devolver(preIncapacidadId, { motivo: data.motivo }),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ['pre-incapacidades-bandeja'] });
      queryClient.invalidateQueries({ queryKey: ['pre-incapacidad', preIncapacidadId] });
      toast({
        title: 'Pre-incapacidad devuelta',
        description: result.email_enviado
          ? `Carta de devolución enviada a ${solicitanteCorreo}`
          : 'Estado actualizado. El email no pudo enviarse.',
      });
      reset();
      onOpenChange(false);
      onSuccess();
    },
    onError: (error: any) => {
      toast({
        title: 'Error al devolver',
        description: error.response?.data?.detail ?? 'No se pudo procesar la devolución',
        variant: 'destructive',
      });
    },
  });

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <CornerDownLeft className="h-5 w-5 text-orange-500" />
            Devolver radicación N° {numeroRadicacion}
          </DialogTitle>
          <DialogDescription>
            Se enviará una carta formal por email a{' '}
            <strong>{solicitanteCorreo}</strong> explicando el motivo de la devolución.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit((d) => mutation.mutate(d))} className="space-y-4">
          <Alert>
            <Mail className="h-4 w-4" />
            <AlertDescription>
              El estado cambiará a <strong>DEVUELTA</strong> y se enviará una carta
              empresarial formal al solicitante.
            </AlertDescription>
          </Alert>

          <div className="space-y-2">
            <Label htmlFor="motivo">
              Motivo de devolución <span className="text-red-500">*</span>
            </Label>
            <Textarea
              id="motivo"
              rows={6}
              placeholder="Describa detalladamente qué información requiere corrección y cómo el solicitante debe proceder..."
              {...register('motivo')}
              className={errors.motivo ? 'border-red-500' : ''}
            />
            {errors.motivo && (
              <p className="text-sm text-red-600">{errors.motivo.message}</p>
            )}
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancelar
            </Button>
            <Button
              type="submit"
              variant="destructive"
              disabled={mutation.isPending}
            >
              {mutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Devolver y enviar email
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
```

Note: `Dialog`, `Textarea`, `Alert`, and `AlertDescription` from Shadcn must be present. Check with:
```bash
ls apps/frontend/sistema-interno/src/components/ui/ | grep -E "dialog|textarea|alert"
```
If missing, install via shadcn CLI:
```bash
cd apps/frontend/sistema-interno && npx shadcn@latest add dialog textarea alert
```

- [ ] **Step 3: Create ResolverEntidadesPanel**

This panel allows searching/creating empresa and empleado from within the gestión view.

```typescript
// apps/frontend/sistema-interno/src/components/pre-incapacidades/ResolverEntidadesPanel.tsx
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Search, Building2, User, Plus, Check } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Label } from '@/components/ui/label';
import api from '@/lib/api';
import { useDebounce } from '@/hooks/useDebounce';
import type { PreIncapacidadDetalle } from '@/types/preIncapacidad';

interface EmpresaSearchResult {
  id: string;
  nit: string;
  razon_social: string;
  estado: string;
}

interface EmpleadoSearchResult {
  id: string;
  numero_documento: string;
  nombres: string;
  apellidos: string;
  estado: string;
}

interface Props {
  preInc: PreIncapacidadDetalle;
  onEmpresaSelected: (nit: string, nombre: string) => void;
  onEmpleadoSelected: (tipoDoc: string, numero: string, nombres: string) => void;
}

function EmpresaSearch({ currentNit, onSelected }: { currentNit: string | null; onSelected: (nit: string, nombre: string) => void }) {
  const [q, setQ] = useState('');
  const dq = useDebounce(q, 400);

  const { data, isLoading } = useQuery({
    queryKey: ['empresa-search', dq],
    queryFn: async () => {
      if (!dq || dq.length < 2) return [];
      const { data } = await api.get<EmpresaSearchResult[]>('/empresas/', { params: { search: dq, limit: 10 } });
      return data;
    },
    enabled: dq.length >= 2,
  });

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <Building2 className="h-4 w-4 text-slate-500" />
        <Label className="font-medium">Empresa</Label>
        {currentNit && (
          <Badge variant="outline" className="text-xs">NIT actual: {currentNit}</Badge>
        )}
      </div>
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
        <Input
          placeholder="Buscar por NIT o razón social..."
          value={q}
          onChange={(e) => setQ(e.target.value)}
          className="pl-9"
        />
      </div>
      {isLoading && <p className="text-sm text-slate-500">Buscando...</p>}
      {data && data.length > 0 && (
        <div className="border rounded-md divide-y max-h-40 overflow-y-auto">
          {data.map((emp) => (
            <div
              key={emp.id}
              className="flex items-center justify-between p-2 hover:bg-slate-50 cursor-pointer"
              onClick={() => { onSelected(emp.nit, emp.razon_social); setQ(''); }}
            >
              <div>
                <p className="text-sm font-medium">{emp.razon_social}</p>
                <p className="text-xs text-slate-500">NIT: {emp.nit}</p>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant={emp.estado === 'ACTIVA' ? 'default' : 'secondary'} className="text-xs">
                  {emp.estado}
                </Badge>
                <Check className="h-4 w-4 text-green-600" />
              </div>
            </div>
          ))}
        </div>
      )}
      {data && data.length === 0 && dq.length >= 2 && !isLoading && (
        <p className="text-sm text-slate-500 italic">
          No encontrada. Cree la empresa desde el módulo Empresas y luego edite el NIT aquí.
        </p>
      )}
    </div>
  );
}

function EmpleadoSearch({ currentDoc, onSelected }: { currentDoc: string; onSelected: (tipoDoc: string, numero: string, nombres: string) => void }) {
  const [q, setQ] = useState('');
  const dq = useDebounce(q, 400);

  const { data, isLoading } = useQuery({
    queryKey: ['empleado-search', dq],
    queryFn: async () => {
      if (!dq || dq.length < 3) return [];
      const { data } = await api.get<EmpleadoSearchResult[]>('/empleados/', { params: { search: dq, limit: 10 } });
      return data;
    },
    enabled: dq.length >= 3,
  });

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <User className="h-4 w-4 text-slate-500" />
        <Label className="font-medium">Empleado</Label>
        {currentDoc && (
          <Badge variant="outline" className="text-xs">Doc actual: {currentDoc}</Badge>
        )}
      </div>
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
        <Input
          placeholder="Buscar por documento o nombre..."
          value={q}
          onChange={(e) => setQ(e.target.value)}
          className="pl-9"
        />
      </div>
      {isLoading && <p className="text-sm text-slate-500">Buscando...</p>}
      {data && data.length > 0 && (
        <div className="border rounded-md divide-y max-h-40 overflow-y-auto">
          {data.map((emp) => (
            <div
              key={emp.id}
              className="flex items-center justify-between p-2 hover:bg-slate-50 cursor-pointer"
              onClick={() => { onSelected('CC', emp.numero_documento, `${emp.nombres} ${emp.apellidos}`); setQ(''); }}
            >
              <div>
                <p className="text-sm font-medium">{emp.nombres} {emp.apellidos}</p>
                <p className="text-xs text-slate-500">Doc: {emp.numero_documento}</p>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant={emp.estado === 'ACTIVO' ? 'default' : 'secondary'} className="text-xs">
                  {emp.estado}
                </Badge>
                <Check className="h-4 w-4 text-green-600" />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export function ResolverEntidadesPanel({ preInc, onEmpresaSelected, onEmpleadoSelected }: Props) {
  const hasEmpresaError = preInc.validation_inconsistencias.some(
    (i) => i.codigo === 'EMPRESA_NOT_FOUND' && i.severidad === 'ERROR'
  );
  const hasEmpleadoError = preInc.validation_inconsistencias.some(
    (i) => i.codigo === 'EMPLEADO_NOT_FOUND' && i.severidad === 'ERROR'
  );

  if (!hasEmpresaError && !hasEmpleadoError) return null;

  return (
    <Card className="p-4 border-orange-200 bg-orange-50 space-y-4">
      <p className="text-sm font-semibold text-orange-800">
        Resolución de entidades requerida
      </p>
      {hasEmpresaError && (
        <EmpresaSearch
          currentNit={preInc.empresa_nit}
          onSelected={onEmpresaSelected}
        />
      )}
      {hasEmpleadoError && (
        <EmpleadoSearch
          currentDoc={preInc.empleado_numero_documento}
          onSelected={onEmpleadoSelected}
        />
      )}
    </Card>
  );
}
```

- [ ] **Step 4: Commit components**

```bash
git add apps/frontend/sistema-interno/src/components/pre-incapacidades/
git commit -m "feat: add ValidationInconsistenciasList, DevolucionModal, ResolverEntidadesPanel components"
```

---

### Task 6: GestionarPreIncapacidadPage

**Files:**
- Create: `apps/frontend/sistema-interno/src/pages/pre-incapacidades/GestionarPreIncapacidadPage.tsx`

- [ ] **Step 1: Create the gestión detail page**

```typescript
// apps/frontend/sistema-interno/src/pages/pre-incapacidades/GestionarPreIncapacidadPage.tsx
import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  ArrowLeft,
  AlertCircle,
  FileText,
  Edit3,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Loader2,
  CornerDownLeft,
} from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useToast } from '@/hooks/use-toast';
import { cn } from '@/lib/utils';

import { ValidationInconsistenciasList } from '@/components/pre-incapacidades/ValidationInconsistenciasList';
import { DevolucionModal } from '@/components/pre-incapacidades/DevolucionModal';
import { ResolverEntidadesPanel } from '@/components/pre-incapacidades/ResolverEntidadesPanel';
import { DocumentosViewer } from '@/components/incapacidades/DocumentosViewer';

import { preIncapacidadService } from '@/services/preIncapacidadService';
import type { PreIncapacidadUpdate } from '@/types/preIncapacidad';
import { formatDate } from '@/utils/formatters';

// Badge variant helper
function estadoBadgeVariant(estado: string): 'default' | 'secondary' | 'destructive' | 'outline' {
  switch (estado) {
    case 'PENDIENTE': return 'default';
    case 'RECHAZADA': return 'destructive';
    case 'ERROR': return 'outline';
    case 'DEVUELTA': return 'secondary';
    case 'PROCESADA': return 'default';
    default: return 'outline';
  }
}

export function GestionarPreIncapacidadPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const [showDocs, setShowDocs] = useState(true);
  const [activeTab, setActiveTab] = useState('inconsistencias');
  const [showDevolucion, setShowDevolucion] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [editFields, setEditFields] = useState<PreIncapacidadUpdate>({});

  // ── Queries ──────────────────────────────────────────────────────────────────
  const { data: preInc, isLoading, error } = useQuery({
    queryKey: ['pre-incapacidad', id],
    queryFn: () => preIncapacidadService.getById(id!),
    enabled: !!id,
  });

  // ── Mutations ─────────────────────────────────────────────────────────────────

  const updateMutation = useMutation({
    mutationFn: (data: PreIncapacidadUpdate) =>
      preIncapacidadService.actualizar(id!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pre-incapacidad', id] });
      setEditMode(false);
      setEditFields({});
      toast({ title: 'Datos actualizados' });
    },
    onError: (e: any) =>
      toast({ title: 'Error al guardar', description: e.response?.data?.detail, variant: 'destructive' }),
  });

  const promoverMutation = useMutation({
    mutationFn: () => preIncapacidadService.promover(id!),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ['pre-incapacidad', id] });
      queryClient.invalidateQueries({ queryKey: ['pre-incapacidades-bandeja'] });
      if (result.success) {
        toast({ title: '✅ Incapacidad creada', description: result.message });
        setTimeout(() => navigate('/pre-incapacidades/bandeja'), 1500);
      } else {
        toast({
          title: `Validación fallida — ${result.errors} error(es)`,
          description: result.message,
          variant: 'destructive',
        });
        setActiveTab('inconsistencias');
      }
    },
    onError: (e: any) =>
      toast({ title: 'Error al promover', description: e.response?.data?.detail, variant: 'destructive' }),
  });

  // ── Loading / Error states ────────────────────────────────────────────────────

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  if (error || !preInc) {
    return (
      <div className="flex items-center justify-center h-96">
        <Card className="p-8 max-w-md text-center space-y-4">
          <AlertCircle className="h-16 w-16 text-red-500 mx-auto" />
          <h2 className="text-xl font-bold">Pre-incapacidad no encontrada</h2>
          <Button onClick={() => navigate('/pre-incapacidades/bandeja')}>Volver a Bandeja</Button>
        </Card>
      </div>
    );
  }

  const errorCount = preInc.validation_inconsistencias.filter((i) => i.severidad === 'ERROR').length;
  const canPromote = !['PROCESADA', 'DEVUELTA'].includes(preInc.estado);
  const canDevolver = !['PROCESADA', 'DEVUELTA'].includes(preInc.estado);

  const handleEntityResolution = (field: keyof PreIncapacidadUpdate, value: string) => {
    const updated = { ...editFields, [field]: value };
    setEditFields(updated);
    updateMutation.mutate(updated);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" onClick={() => navigate('/pre-incapacidades/bandeja')}>
            <ArrowLeft className="h-5 w-5 mr-2" />
            Bandeja
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-3">
              Pre-Incapacidad
              <Badge variant={estadoBadgeVariant(preInc.estado)}>{preInc.estado}</Badge>
              {errorCount > 0 && (
                <Badge variant="destructive" className="gap-1">
                  <AlertCircle className="h-3.5 w-3.5" />
                  {errorCount} error{errorCount > 1 ? 'es' : ''}
                </Badge>
              )}
            </h1>
            <p className="text-slate-500 font-mono">N° {preInc.numero_radicacion}</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Toggle document sidebar */}
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowDocs(!showDocs)}
          >
            {showDocs ? (
              <><ChevronLeft className="h-4 w-4 mr-1" /> Ocultar docs</>
            ) : (
              <><ChevronRight className="h-4 w-4 mr-1" /> Documentos ({preInc.documentos.length})</>
            )}
          </Button>

          {/* Action buttons */}
          {canDevolver && (
            <Button
              variant="outline"
              className="border-orange-400 text-orange-700 hover:bg-orange-50"
              onClick={() => setShowDevolucion(true)}
            >
              <CornerDownLeft className="h-4 w-4 mr-2" />
              Devolver
            </Button>
          )}
          {canPromote && (
            <Button
              onClick={() => promoverMutation.mutate()}
              disabled={promoverMutation.isPending}
              className="bg-green-600 hover:bg-green-700"
            >
              {promoverMutation.isPending ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <CheckCircle2 className="h-4 w-4 mr-2" />
              )}
              Promover a Incapacidad
            </Button>
          )}
        </div>
      </div>

      {/* Already processed notice */}
      {preInc.estado === 'PROCESADA' && (
        <Card className="p-4 bg-green-50 border-green-200">
          <p className="text-green-800 text-sm font-medium flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4" />
            Esta pre-incapacidad fue promovida exitosamente a una incapacidad completa.
          </p>
        </Card>
      )}

      {/* Split-screen layout */}
      <div className="flex gap-6">
        {/* Document sidebar */}
        {showDocs && (
          <div className="w-1/2 flex-shrink-0">
            <Card className="sticky top-6 h-full">
              <div className="p-4 border-b flex items-center gap-2">
                <FileText className="h-4 w-4 text-blue-600" />
                <span className="font-semibold">Documentos Adjuntos</span>
                <Badge variant="secondary">{preInc.documentos.length}</Badge>
              </div>
              <div className="p-4 overflow-y-auto max-h-[calc(100vh-220px)]">
                {/* DocumentosViewer expects Documento[] from incapacidades — use a compatible adapter */}
                <div className="space-y-3">
                  {preInc.documentos.length === 0 && (
                    <p className="text-slate-500 text-sm text-center py-4">Sin documentos adjuntos</p>
                  )}
                  {preInc.documentos.map((doc) => (
                    <div key={doc.id} className="border rounded-lg p-3 bg-slate-50">
                      <p className="text-sm font-medium">{doc.tipo_documento}</p>
                      <p className="text-xs text-slate-500">{doc.nombre_original}</p>
                      <Badge
                        variant={doc.estado_subida === 'OK' ? 'default' : 'destructive'}
                        className="text-xs mt-1"
                      >
                        {doc.estado_subida}
                      </Badge>
                    </div>
                  ))}
                </div>
              </div>
            </Card>
          </div>
        )}

        {/* Main tabs panel */}
        <div className={cn('flex-1', showDocs ? 'w-1/2' : 'w-full')}>
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="inconsistencias" className="gap-2">
                <AlertCircle className="h-4 w-4" />
                Inconsistencias{errorCount > 0 && ` (${errorCount})`}
              </TabsTrigger>
              <TabsTrigger value="datos" className="gap-2">
                <Edit3 className="h-4 w-4" />
                Datos
              </TabsTrigger>
            </TabsList>

            {/* Tab: Inconsistencias */}
            <TabsContent value="inconsistencias" className="space-y-4 mt-4">
              <ValidationInconsistenciasList issues={preInc.validation_inconsistencias} />

              {/* Entity resolution panel (shown when EMPRESA_NOT_FOUND or EMPLEADO_NOT_FOUND) */}
              <ResolverEntidadesPanel
                preInc={preInc}
                onEmpresaSelected={(nit, nombre) => handleEntityResolution('empresa_nit', nit)}
                onEmpleadoSelected={(tipoDoc, numero, nombres) => {
                  updateMutation.mutate({
                    empleado_tipo_documento: tipoDoc,
                    empleado_numero_documento: numero,
                    empleado_nombres: nombres,
                  });
                }}
              />

              {/* Promote CTA when no errors */}
              {errorCount === 0 && canPromote && (
                <Card className="p-4 bg-green-50 border-green-200 flex items-center justify-between">
                  <p className="text-green-800 text-sm font-medium">
                    Sin errores — listo para promover a incapacidad completa.
                  </p>
                  <Button
                    size="sm"
                    onClick={() => promoverMutation.mutate()}
                    disabled={promoverMutation.isPending}
                    className="bg-green-600 hover:bg-green-700"
                  >
                    {promoverMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Promover ahora'}
                  </Button>
                </Card>
              )}
            </TabsContent>

            {/* Tab: Datos */}
            <TabsContent value="datos" className="space-y-4 mt-4">
              <div className="flex items-center justify-between">
                <p className="text-sm text-slate-500">Corrija los campos necesarios antes de volver a promover.</p>
                {!editMode ? (
                  <Button size="sm" variant="outline" onClick={() => setEditMode(true)}>
                    <Edit3 className="h-4 w-4 mr-1" /> Editar
                  </Button>
                ) : (
                  <div className="flex gap-2">
                    <Button size="sm" variant="outline" onClick={() => { setEditMode(false); setEditFields({}); }}>
                      Cancelar
                    </Button>
                    <Button
                      size="sm"
                      disabled={updateMutation.isPending}
                      onClick={() => updateMutation.mutate(editFields)}
                    >
                      {updateMutation.isPending && <Loader2 className="h-4 w-4 mr-1 animate-spin" />}
                      Guardar
                    </Button>
                  </div>
                )}
              </div>

              <div className="grid grid-cols-2 gap-4">
                {/* Empresa */}
                <div className="col-span-2 space-y-2 border-b pb-4">
                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Empresa</p>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <Label className="text-xs">NIT</Label>
                      {editMode ? (
                        <Input
                          defaultValue={preInc.empresa_nit ?? ''}
                          onChange={(e) => setEditFields((p) => ({ ...p, empresa_nit: e.target.value }))}
                        />
                      ) : (
                        <p className="text-sm mt-1">{preInc.empresa_nit ?? '—'}</p>
                      )}
                    </div>
                    <div>
                      <Label className="text-xs">Nombre</Label>
                      {editMode ? (
                        <Input
                          defaultValue={preInc.empresa_nombre ?? ''}
                          onChange={(e) => setEditFields((p) => ({ ...p, empresa_nombre: e.target.value }))}
                        />
                      ) : (
                        <p className="text-sm mt-1">{preInc.empresa_nombre ?? '—'}</p>
                      )}
                    </div>
                  </div>
                </div>

                {/* Empleado */}
                <div className="col-span-2 space-y-2 border-b pb-4">
                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Empleado</p>
                  <div className="grid grid-cols-3 gap-3">
                    <div>
                      <Label className="text-xs">Tipo Doc.</Label>
                      {editMode ? (
                        <Input
                          defaultValue={preInc.empleado_tipo_documento}
                          onChange={(e) => setEditFields((p) => ({ ...p, empleado_tipo_documento: e.target.value }))}
                        />
                      ) : (
                        <p className="text-sm mt-1">{preInc.empleado_tipo_documento}</p>
                      )}
                    </div>
                    <div>
                      <Label className="text-xs">Número Doc.</Label>
                      {editMode ? (
                        <Input
                          defaultValue={preInc.empleado_numero_documento}
                          onChange={(e) => setEditFields((p) => ({ ...p, empleado_numero_documento: e.target.value }))}
                        />
                      ) : (
                        <p className="text-sm mt-1">{preInc.empleado_numero_documento}</p>
                      )}
                    </div>
                    <div>
                      <Label className="text-xs">Nombres</Label>
                      {editMode ? (
                        <Input
                          defaultValue={preInc.empleado_nombres}
                          onChange={(e) => setEditFields((p) => ({ ...p, empleado_nombres: e.target.value }))}
                        />
                      ) : (
                        <p className="text-sm mt-1">{preInc.empleado_nombres} {preInc.empleado_apellidos ?? ''}</p>
                      )}
                    </div>
                  </div>
                </div>

                {/* Incapacidad data */}
                <div className="col-span-2 space-y-2">
                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Incapacidad</p>
                  <div className="grid grid-cols-2 gap-3">
                    <div><Label className="text-xs">Fecha inicio</Label><p className="text-sm mt-1">{formatDate(preInc.fecha_inicio)}</p></div>
                    <div><Label className="text-xs">Fecha fin</Label><p className="text-sm mt-1">{formatDate(preInc.fecha_fin)}</p></div>
                    <div><Label className="text-xs">Días totales</Label><p className="text-sm mt-1">{preInc.dias_totales}</p></div>
                    <div><Label className="text-xs">CIE-10</Label><p className="text-sm mt-1 font-mono">{preInc.diagnostico_cie10}</p></div>
                    <div><Label className="text-xs">Médico</Label><p className="text-sm mt-1">{preInc.nombre_medico}</p></div>
                    <div><Label className="text-xs">Reg. médico</Label><p className="text-sm mt-1">{preInc.registro_medico}</p></div>
                  </div>
                </div>

                {/* System notes */}
                {(preInc.error_procesamiento || preInc.motivo_devolucion) && (
                  <div className="col-span-2 space-y-2 border-t pt-4">
                    <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Notas del sistema</p>
                    {preInc.error_procesamiento && (
                      <div className="bg-red-50 border border-red-200 rounded p-3 text-sm text-red-700">
                        <strong>Error de procesamiento:</strong> {preInc.error_procesamiento}
                      </div>
                    )}
                    {preInc.motivo_devolucion && (
                      <div className="bg-orange-50 border border-orange-200 rounded p-3 text-sm text-orange-700">
                        <strong>Motivo de devolución:</strong> {preInc.motivo_devolucion}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </TabsContent>
          </Tabs>
        </div>
      </div>

      {/* Devolution modal */}
      {preInc && (
        <DevolucionModal
          preIncapacidadId={preInc.id}
          numeroRadicacion={preInc.numero_radicacion}
          solicitanteCorreo={preInc.solicitante_correo}
          open={showDevolucion}
          onOpenChange={setShowDevolucion}
          onSuccess={() => navigate('/pre-incapacidades/bandeja')}
        />
      )}
    </div>
  );
}
```

- [ ] **Step 2: Verify page renders when navigating to a pre-incapacidad**

Start the dev server and navigate to `/pre-incapacidades/bandeja`. Click "Gestionar" on any item. Confirm:
- Split-screen layout appears (document list + tabs)
- "Inconsistencias" tab shows the ValidationInconsistenciasList
- "Datos" tab shows the correction form
- "Devolver" button opens the DevolucionModal
- "Promover a Incapacidad" button triggers the mutation

- [ ] **Step 3: Commit**

```bash
git add apps/frontend/sistema-interno/src/pages/pre-incapacidades/GestionarPreIncapacidadPage.tsx
git commit -m "feat: add GestionarPreIncapacidadPage with validation display, edit form, devolution and promotion"
```

---

## Implementation Notes

### Dependencies to verify before starting
- `react-hook-form` and `@hookform/resolvers` must be present in `sistema-interno`:
  ```bash
  grep "react-hook-form\|hookform" apps/frontend/sistema-interno/package.json
  ```
  If missing: `npm install react-hook-form @hookform/resolvers`

- Shadcn components: `Dialog`, `Textarea`, `Alert` may be missing — check `src/components/ui/` and install if needed:
  ```bash
  npx shadcn@latest add dialog textarea alert
  ```

### Backend test note
The new authenticated endpoints (GET /, PATCH /{id}, POST /{id}/devolver, POST /{id}/promover) require a valid JWT to call. In tests, mock `get_current_user` dependency or use a test user fixture. The pre-existing `client` fixture uses the `testclient` without JWT — either add a new authenticated client fixture or skip authentication in test mode via an env flag.

### Empleado lookup in PromotePreIncapacidadService
The existing service looks up empleado with `empleado_repository.get_by_documento(db, numero_documento, empresa.id)`. The `empresa.id` is the FK UUID, not the NIT. This means if the user updates `empresa_nit` to a valid NIT, the next `promover` call will find the empresa first, then use `empresa.id` to look up the empleado. No change needed here.

### `formatDate` and `formatRelativeDate`
These utilities already exist at `apps/frontend/sistema-interno/src/utils/formatters.ts`. Use them directly.

### `DataTable` component
Already exists at `apps/frontend/sistema-interno/src/components/shared/DataTable.tsx`. Used as-is.

---

## Next Steps After Implementation

1. **Manual test** the full flow: Radicar from portal-externo → job runs → RECHAZADA → Gestionar → Fix empresa_nit → Promover → PROCESADA
2. **Test devolution email**: check Celery logs and email server  
3. **Backend tests**: write integration tests for the 4 new endpoints (list, update, devolver, promover)
4. **Edge case**: Handle SALUD-type pre-incapacidades (no empresa/empleado — uses afiliado) — currently the promotion service only handles ARL; SALUD support is future scope

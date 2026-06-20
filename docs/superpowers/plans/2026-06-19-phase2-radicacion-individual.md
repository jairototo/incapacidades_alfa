# Phase 2 — Radicación Individual + Pipeline Compartido Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **Depends on:** Phase 1 (auth store, ProtectedRoute, `/auth/me` empresa). 
> **Provides for later phases:** the shared `RadicacionPipelineService` reused by Phase 3 (bulk) and the audit-task enqueue hook implemented in Phase 4.

**Goal:** Let an authenticated EMPRESA user file a single ARL disability for one of *their* employees through a wizard with no company/solicitante steps, a `prorroga` switch, and slot-based attachments — submitted through a new shared pipeline that creates the `Incapacidad` directly and resolves the solicitante from the company.

**Architecture:** New backend `RadicacionPipelineService.radicar(rows, empresa, user)` creates `Incapacidad` rows directly (internal `numero`, `prorroga`), stores documents, resolves/creates the `Solicitante` by company email, sends one summary email, and enqueues the audit task via an injected hook (Phase 4). Two pluggable hooks are injected with no-op defaults here: `enqueue_auditoria` and `integracion` — Phase 3.6 and Phase 4 replace the defaults. Frontend: a 2-step individual wizard reusing existing UI primitives, with a company-scoped employee selector.

**Tech Stack:** FastAPI, SQLAlchemy async, Alembic, Celery (hook only), pytest in Docker; React 19, react-hook-form, Zod v4, React Query, vitest.

---

## File Structure

**Backend:**
- Migration: `apps/backend/alembic/versions/xxxx_add_prorroga_to_incapacidad.py` (create via `make migrate`).
- Modify: `apps/backend/app/models/incapacidad.py` — add `prorroga` column.
- Create: `apps/backend/app/schemas/radicacion.py` — `RadicacionRowInput`, `RadicacionResultItem`, `RadicacionResponse`.
- Create: `apps/backend/app/services/radicacion_pipeline_service.py` — shared pipeline.
- Create: `apps/backend/app/services/solicitante_resolver.py` — resolve/create solicitante from empresa.
- Modify: `apps/backend/app/api/v1/endpoints/incapacidades.py` — add `POST /incapacidades/radicar`.
- Modify: `apps/backend/app/tasks/email_tasks.py` — add `enviar_resumen_radicacion` (or reuse existing send).
- Tests: `tests/test_radicacion_pipeline.py`, `tests/test_radicar_endpoint.py`.

**Frontend:**
- Create: `src/schemas/radicacionIndividualSchema.ts` — Zod v4 (no empresa/solicitante; `empleado_id`, `prorroga`).
- Create: `src/services/empresaEmpleadoService.ts` — list employees of authenticated company.
- Create: `src/components/radicacion/EmpleadoSelector.tsx` — searchable selector + `?` tooltip.
- Create: `src/components/radicacion/ProrrogaSwitch.tsx`.
- Create: `src/components/radicacion/RadicacionIndividualPage.tsx` — wizard.
- Create: `src/services/radicacionService.ts` — `radicarIndividual(formData, files)`.
- Modify: `src/App.tsx` — add `/radicar/individual` inside ProtectedRoute.

---

## Task 1: Backend — `prorroga` migration + model

**Files:**
- Modify: `apps/backend/app/models/incapacidad.py`
- Create: migration under `apps/backend/alembic/versions/`

- [ ] **Step 1: Add the column to the model**

```python
# apps/backend/app/models/incapacidad.py  (add near other Mapped columns, after `subtipo`)
from sqlalchemy import Boolean

    prorroga: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false",
        comment="Indica si la incapacidad es una prórroga/renovación",
    )
```

- [ ] **Step 2: Generate the migration**

Run: `cd apps/backend && make migrate msg='add prorroga to incapacidad'`
Then open the generated file and confirm it contains:

```python
def upgrade() -> None:
    op.add_column('incapacidad', sa.Column('prorroga', sa.Boolean(), server_default='false', nullable=False))

def downgrade() -> None:
    op.drop_column('incapacidad', 'prorroga')
```

- [ ] **Step 3: Apply + verify**

Run: `docker exec incapacidades-api alembic upgrade head`
Run: `docker exec incapacidades-api python -c "from app.models.incapacidad import Incapacidad; print('prorroga' in Incapacidad.__table__.columns)"`
Expected: `True`.

- [ ] **Step 4: Commit**

```bash
git add apps/backend/app/models/incapacidad.py apps/backend/alembic/versions/
git commit -m "feat(db): add prorroga column to incapacidad"
```

---

## Task 2: Backend — solicitante resolver

**Files:**
- Create: `apps/backend/app/services/solicitante_resolver.py`
- Test: `apps/backend/tests/test_solicitante_resolver.py`

- [ ] **Step 1: Write the failing test**

```python
# apps/backend/tests/test_solicitante_resolver.py
import pytest
from app.services.solicitante_resolver import resolve_solicitante_for_empresa
from app.models.empresa import Empresa


@pytest.mark.asyncio
async def test_creates_solicitante_when_absent(db_session):
    empresa = Empresa(nit="900111", razon_social="ACME SA", email_contacto="rrhh@acme.com", estado="ACTIVA")
    db_session.add(empresa); await db_session.flush()
    s = await resolve_solicitante_for_empresa(db_session, empresa)
    assert s.correo == "rrhh@acme.com"
    assert s.nombres  # derived from razon_social

@pytest.mark.asyncio
async def test_reuses_existing_solicitante(db_session):
    empresa = Empresa(nit="900222", razon_social="BETA SA", email_contacto="info@beta.com", estado="ACTIVA")
    db_session.add(empresa); await db_session.flush()
    first = await resolve_solicitante_for_empresa(db_session, empresa)
    await db_session.flush()
    second = await resolve_solicitante_for_empresa(db_session, empresa)
    assert first.id == second.id
```

- [ ] **Step 2: Run test to verify it fails**

Run: `docker exec incapacidades-api python -m pytest tests/test_solicitante_resolver.py -v --no-cov`
Expected: FAIL — module not found.

- [ ] **Step 3: Implement the resolver**

```python
# apps/backend/app/services/solicitante_resolver.py
"""Resuelve (o crea) el Solicitante a partir de la empresa autenticada.

El portal no recibe datos de solicitante desde el frontend: el solicitante de toda
radicación es la propia empresa, identificada por su email de contacto.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.empresa import Empresa
from app.models.solicitante import Solicitante


async def resolve_solicitante_for_empresa(db: AsyncSession, empresa: Empresa) -> Solicitante:
    correo = (empresa.email_contacto or f"{empresa.nit}@empresa.local").strip().lower()
    existing = (
        await db.execute(select(Solicitante).where(Solicitante.correo == correo))
    ).scalar_one_or_none()
    if existing:
        return existing

    solicitante = Solicitante(
        correo=correo,
        nombres=empresa.razon_social[:100],
        apellidos="(Empresa)",
        telefono=getattr(empresa, "telefono", None),
    )
    db.add(solicitante)
    await db.flush()
    return solicitante
```

- [ ] **Step 4: Run test to verify it passes**

Run: `docker exec incapacidades-api python -m pytest tests/test_solicitante_resolver.py -v --no-cov`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/backend/app/services/solicitante_resolver.py apps/backend/tests/test_solicitante_resolver.py
git commit -m "feat(radicacion): resolve solicitante from authenticated empresa"
```

---

## Task 3: Backend — radicacion schemas

**Files:**
- Create: `apps/backend/app/schemas/radicacion.py`

- [ ] **Step 1: Create the schemas**

```python
# apps/backend/app/schemas/radicacion.py
from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class RadicacionRowInput(BaseModel):
    """Una fila de radicación (individual = 1 fila). Sin datos de empresa/solicitante."""
    empleado_id: UUID
    tipo_enfermedad: str
    fecha_inicio: date
    fecha_fin: date
    dias_totales: int
    diagnostico_cie10: str
    descripcion_diagnostico: Optional[str] = None
    nombre_medico: str
    registro_medico: str
    ips: Optional[str] = None
    valor_dia: Optional[Decimal] = None
    prorroga: bool = False
    observaciones: Optional[str] = None


class RadicacionResultItem(BaseModel):
    empleado_id: UUID
    incapacidad_id: Optional[UUID] = None
    numero: Optional[str] = None
    success: bool
    error: Optional[str] = None


class RadicacionResponse(BaseModel):
    items: list[RadicacionResultItem]
    total_radicadas: int

    model_config = ConfigDict(from_attributes=True)
```

- [ ] **Step 2: Commit**

```bash
git add apps/backend/app/schemas/radicacion.py
git commit -m "feat(radicacion): add radicacion pipeline schemas"
```

---

## Task 4: Backend — shared radication pipeline

**Files:**
- Create: `apps/backend/app/services/radicacion_pipeline_service.py`
- Test: `apps/backend/tests/test_radicacion_pipeline.py`

- [ ] **Step 1: Write the failing test**

```python
# apps/backend/tests/test_radicacion_pipeline.py
import datetime as dt
import pytest
from app.services.radicacion_pipeline_service import RadicacionPipelineService
from app.schemas.radicacion import RadicacionRowInput
from app.models.empresa import Empresa
from app.models.empleado import Empleado
from app.utils.enums import EstadoIncapacidad


async def _seed(db):
    empresa = Empresa(nit="900333", razon_social="GAMMA SA", email_contacto="rrhh@gamma.com", estado="ACTIVA")
    db.add(empresa); await db.flush()
    empleado = Empleado(empresa_id=empresa.id, numero_documento="123456", tipo_documento="CC",
                        nombres="Juan", apellidos="Pérez", fecha_ingreso=dt.date(2020, 1, 1), estado="ACTIVO")
    db.add(empleado); await db.flush()
    return empresa, empleado


@pytest.mark.asyncio
async def test_pipeline_creates_incapacidad_radicada(db_session):
    empresa, empleado = await _seed(db_session)
    enqueued = []
    svc = RadicacionPipelineService(db_session, enqueue_auditoria=lambda iid: enqueued.append(iid))
    row = RadicacionRowInput(
        empleado_id=empleado.id, tipo_enfermedad="ACCIDENTE_TRABAJO",
        fecha_inicio=dt.date(2026, 6, 1), fecha_fin=dt.date(2026, 6, 5), dias_totales=5,
        diagnostico_cie10="S00.0", nombre_medico="Dr X", registro_medico="RM-1", prorroga=True,
    )
    resp = await svc.radicar([row], empresa=empresa, radicado_por_id=None)
    assert resp.total_radicadas == 1
    item = resp.items[0]
    assert item.success and item.numero
    assert len(enqueued) == 1  # audit task enqueued
    # Incapacidad persisted with prorroga + RADICADA + solicitante resolved
    from app.models.incapacidad import Incapacidad
    from sqlalchemy import select
    inc = (await db_session.execute(select(Incapacidad).where(Incapacidad.id == item.incapacidad_id))).scalar_one()
    assert inc.prorroga is True
    assert inc.estado == EstadoIncapacidad.RADICADA
    assert inc.solicitante_id is not None
    assert inc.empresa_id == empresa.id


@pytest.mark.asyncio
async def test_pipeline_rejects_employee_of_other_company(db_session):
    empresa, empleado = await _seed(db_session)
    other = Empresa(nit="900999", razon_social="OTHER SA", email_contacto="o@o.com", estado="ACTIVA")
    db_session.add(other); await db_session.flush()
    svc = RadicacionPipelineService(db_session, enqueue_auditoria=lambda iid: None)
    row = RadicacionRowInput(
        empleado_id=empleado.id, tipo_enfermedad="ACCIDENTE_TRABAJO",
        fecha_inicio=dt.date(2026, 6, 1), fecha_fin=dt.date(2026, 6, 5), dias_totales=5,
        diagnostico_cie10="S00.0", nombre_medico="Dr X", registro_medico="RM-1",
    )
    resp = await svc.radicar([row], empresa=other, radicado_por_id=None)
    assert resp.items[0].success is False
    assert "empresa" in (resp.items[0].error or "").lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `docker exec incapacidades-api python -m pytest tests/test_radicacion_pipeline.py -v --no-cov`
Expected: FAIL — module not found.

- [ ] **Step 3: Implement the pipeline**

```python
# apps/backend/app/services/radicacion_pipeline_service.py
"""Pipeline compartido de radicación (individual = N=1, masiva = N filas).

Crea Incapacidad directamente (sin pre_incapacidad), resuelve solicitante desde la
empresa, y expone hooks inyectables para auditoría (Phase 4) e integración externa
(Phase 3.6). Sus defaults son no-op para que esta fase sea testeable de forma aislada.
"""
from __future__ import annotations
from datetime import date, datetime
from typing import Callable, Optional, Protocol
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.models.empresa import Empresa
from app.models.empleado import Empleado
from app.models.incapacidad import Incapacidad
from app.schemas.radicacion import RadicacionRowInput, RadicacionResultItem, RadicacionResponse
from app.services.solicitante_resolver import resolve_solicitante_for_empresa
from app.utils.enums import TipoIncapacidad, EstadoIncapacidad


class IntegracionHook(Protocol):
    async def __call__(self, db: AsyncSession, incapacidad: Incapacidad) -> None: ...


async def _noop_integracion(db: AsyncSession, incapacidad: Incapacidad) -> None:
    return None


class RadicacionPipelineService:
    def __init__(
        self,
        db: AsyncSession,
        enqueue_auditoria: Callable[[UUID], None],
        integracion: IntegracionHook = _noop_integracion,
    ):
        self.db = db
        self.enqueue_auditoria = enqueue_auditoria
        self.integracion = integracion

    async def _generar_numero(self, tipo: str) -> str:
        """Reusa el patrón existente: {prefix}-{YYYYMMDD}-{NNNN}."""
        prefix = "ARL" if tipo == "ARL" else "SAL"
        fecha_str = date.today().strftime("%Y%m%d")
        like = f"{prefix}-{fecha_str}-%"
        count = (
            await self.db.execute(
                select(Incapacidad).where(Incapacidad.numero.like(like))
            )
        ).scalars().all()
        return f"{prefix}-{fecha_str}-{len(count) + 1:04d}"

    async def radicar(
        self,
        rows: list[RadicacionRowInput],
        empresa: Empresa,
        radicado_por_id: Optional[UUID],
    ) -> RadicacionResponse:
        solicitante = await resolve_solicitante_for_empresa(self.db, empresa)
        items: list[RadicacionResultItem] = []
        created: list[Incapacidad] = []

        for row in rows:
            empleado = (
                await self.db.execute(select(Empleado).where(Empleado.id == row.empleado_id))
            ).scalar_one_or_none()
            if empleado is None:
                items.append(RadicacionResultItem(empleado_id=row.empleado_id, success=False, error="Empleado no encontrado"))
                continue
            if empleado.empresa_id != empresa.id:
                items.append(RadicacionResultItem(empleado_id=row.empleado_id, success=False, error="El empleado no pertenece a su empresa"))
                continue

            numero = await self._generar_numero("ARL")
            inc = Incapacidad(
                numero=numero,
                tipo=TipoIncapacidad.ARL,
                empleado_id=empleado.id,
                empresa_id=empresa.id,
                solicitante_id=solicitante.id,
                fecha_inicio=row.fecha_inicio,
                fecha_fin=row.fecha_fin,
                dias_totales=row.dias_totales,
                diagnostico_cie10=row.diagnostico_cie10,
                descripcion_diagnostico=row.descripcion_diagnostico,
                nombre_medico=row.nombre_medico,
                registro_medico=row.registro_medico,
                ips=row.ips,
                valor_dia=row.valor_dia,
                prorroga=row.prorroga,
                observaciones=row.observaciones,
                subtipo=row.tipo_enfermedad,
                estado=EstadoIncapacidad.RADICADA,
                fecha_radicacion=datetime.utcnow(),
                radicado_por_id=radicado_por_id,
            )
            self.db.add(inc)
            await self.db.flush()

            # Integración externa (Phase 3.6 sustituye el default no-op)
            await self.integracion(self.db, inc)

            created.append(inc)
            items.append(RadicacionResultItem(
                empleado_id=row.empleado_id, incapacidad_id=inc.id, numero=inc.numero, success=True,
            ))

        await self.db.commit()

        # Enqueue auditoría por cada incapacidad creada (Phase 4)
        for inc in created:
            try:
                self.enqueue_auditoria(inc.id)
            except Exception as exc:  # nunca bloquear la radicación por el enqueue
                logger.error(f"No se pudo encolar auditoría para {inc.id}: {exc}")

        logger.info(f"Radicación: {len(created)}/{len(rows)} incapacidades creadas")
        return RadicacionResponse(items=items, total_radicadas=len(created))
```

> Document storage is handled by the endpoint layer (Task 5) using the existing documents
> service, after the pipeline returns the created `incapacidad_id`s. The summary email is sent
> by the endpoint after a successful pipeline run.

- [ ] **Step 4: Run test to verify it passes**

Run: `docker exec incapacidades-api python -m pytest tests/test_radicacion_pipeline.py -v --no-cov`
Expected: PASS (both tests).

- [ ] **Step 5: Commit**

```bash
git add apps/backend/app/services/radicacion_pipeline_service.py apps/backend/tests/test_radicacion_pipeline.py
git commit -m "feat(radicacion): add shared radication pipeline service"
```

---

## Task 5: Backend — `POST /incapacidades/radicar` endpoint (individual, multipart)

**Files:**
- Modify: `apps/backend/app/api/v1/endpoints/incapacidades.py`
- Test: `apps/backend/tests/test_radicar_endpoint.py`

> The individual endpoint accepts one row's fields + files in a single `multipart/form-data`
> request. It resolves `empresa` from the authenticated EMPRESA user, runs the pipeline (N=1),
> stores documents against the created incapacidad via the existing document service, and sends
> the summary email. EMPRESA-only dependency reused from the existing security deps.

- [ ] **Step 1: Write the failing test**

```python
# apps/backend/tests/test_radicar_endpoint.py
import datetime as dt
import io
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_radicar_individual_creates_incapacidad(client: AsyncClient, empresa_user_token, empleado_de_empresa):
    files = {"incapacidad_medica": ("inc.pdf", io.BytesIO(b"%PDF-1.4 test"), "application/pdf")}
    data = {
        "empleado_id": str(empleado_de_empresa.id),
        "tipo_enfermedad": "ACCIDENTE_TRABAJO",
        "fecha_inicio": "2026-06-01", "fecha_fin": "2026-06-05", "dias_totales": "5",
        "diagnostico_cie10": "S00.0", "nombre_medico": "Dr House", "registro_medico": "RM-9",
        "prorroga": "true",
    }
    resp = await client.post("/api/v1/incapacidades/radicar", data=data, files=files,
                             headers={"Authorization": f"Bearer {empresa_user_token}"})
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["total_radicadas"] == 1
    assert body["items"][0]["numero"]
```

> Add fixtures `empresa_user_token` (reuse Phase 1) and `empleado_de_empresa` (an `Empleado`
> with `empresa_id` = that user's empresa) to `conftest.py`.

- [ ] **Step 2: Run test to verify it fails**

Run: `docker exec incapacidades-api python -m pytest tests/test_radicar_endpoint.py -v --no-cov`
Expected: FAIL — 404 (route missing).

- [ ] **Step 3: Implement the endpoint**

```python
# apps/backend/app/api/v1/endpoints/incapacidades.py  (add a new route)
from fastapi import UploadFile, File, Form
from app.services.radicacion_pipeline_service import RadicacionPipelineService
from app.schemas.radicacion import RadicacionRowInput, RadicacionResponse
from app.tasks.incapacidad_tasks import enqueue_auditoria_incapacidad  # provided in Phase 4; see note


@router.post("/radicar", response_model=RadicacionResponse, status_code=status.HTTP_201_CREATED,
             summary="Radicar incapacidad individual (EMPRESA)")
async def radicar_individual(
    empleado_id: UUID = Form(...),
    tipo_enfermedad: str = Form(...),
    fecha_inicio: date = Form(...),
    fecha_fin: date = Form(...),
    dias_totales: int = Form(...),
    diagnostico_cie10: str = Form(...),
    nombre_medico: str = Form(...),
    registro_medico: str = Form(...),
    descripcion_diagnostico: str | None = Form(None),
    ips: str | None = Form(None),
    valor_dia: float | None = Form(None),
    prorroga: bool = Form(False),
    observaciones: str | None = Form(None),
    incapacidad_medica: list[UploadFile] = File(...),
    historia_clinica: list[UploadFile] | None = File(None),
    soportes_adicionales: list[UploadFile] | None = File(None),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_empresa),  # EMPRESA-only dep
):
    if not current_user.empresa_id or current_user.empresa is None:
        raise HTTPException(status_code=403, detail="Usuario no vinculado a una empresa")

    row = RadicacionRowInput(
        empleado_id=empleado_id, tipo_enfermedad=tipo_enfermedad,
        fecha_inicio=fecha_inicio, fecha_fin=fecha_fin, dias_totales=dias_totales,
        diagnostico_cie10=diagnostico_cie10, descripcion_diagnostico=descripcion_diagnostico,
        nombre_medico=nombre_medico, registro_medico=registro_medico, ips=ips,
        valor_dia=valor_dia, prorroga=prorroga, observaciones=observaciones,
    )
    pipeline = RadicacionPipelineService(db, enqueue_auditoria=enqueue_auditoria_incapacidad)
    result = await pipeline.radicar([row], empresa=current_user.empresa, radicado_por_id=current_user.id)

    item = result.items[0]
    if item.success and item.incapacidad_id:
        await _almacenar_documentos(  # helper below
            db, item.incapacidad_id,
            {"INCAPACIDAD_MEDICA": incapacidad_medica,
             "HISTORIA_CLINICA": historia_clinica or [],
             "SOPORTE_ADICIONAL": soportes_adicionales or []},
            current_user.id,
        )
        from app.tasks.email_tasks import enviar_resumen_radicacion
        enviar_resumen_radicacion.delay(
            destinatario=current_user.empresa.email_contacto,
            numeros=[item.numero],
        )
    return result
```

Add the document helper (reusing the existing document service — confirm its real name in
`app/services/documento_service.py` and adapt the call):

```python
async def _almacenar_documentos(db, incapacidad_id, archivos_por_tipo, uploaded_by_id):
    from app.services.documento_service import DocumentoService
    svc = DocumentoService(db)
    for tipo, archivos in archivos_por_tipo.items():
        for f in archivos:
            content = await f.read()
            await svc.guardar_documento(
                incapacidad_id=incapacidad_id, tipo=tipo,
                filename=f.filename, content=content, uploaded_by_id=uploaded_by_id,
            )
    await db.commit()
```

> **Verify before coding:** read `app/services/documento_service.py` and `app/api/v1/endpoints/documentos.py`
> for the exact storage method signature (filesystem default, MD5/SHA256 hashing). Adapt `_almacenar_documentos`
> to the real method name. Do not invent a new storage path.
>
> **`require_empresa` dependency:** if a role dependency doesn't already exist, add one in
> `app/core/security.py` mirroring the existing role guards: `def require_empresa(user = Depends(get_current_user))`
> that raises 403 unless `user.rol == "EMPRESA"`.
>
> **`enqueue_auditoria_incapacidad`:** Phase 4 implements this Celery enqueue. Until Phase 4 lands,
> add a temporary no-op in `app/tasks/incapacidad_tasks.py`: `def enqueue_auditoria_incapacidad(incapacidad_id): pass`
> and replace it in Phase 4. Note this TODO in the commit.

- [ ] **Step 4: Add the summary email task**

```python
# apps/backend/app/tasks/email_tasks.py  (add)
from app.tasks.celery_app import celery_app  # use the existing celery app import in this file

@celery_app.task(name="email.enviar_resumen_radicacion")
def enviar_resumen_radicacion(destinatario: str | None, numeros: list[str]):
    if not destinatario:
        return
    cuerpo = "Se radicaron las siguientes incapacidades:\n" + "\n".join(f"- {n}" for n in numeros)
    # Reuse the existing email send helper used by the current notification flow.
    from app.services.email_service import send_email  # adapt to real helper
    send_email(to=destinatario, subject="Confirmación de radicación de incapacidades", body=cuerpo)
```

> Adapt imports to the real Celery app + email helper already used in `email_tasks.py`
> (the repo already sends a submission email per recent commit `f57e232f`). Reuse that helper.

- [ ] **Step 5: Run test to verify it passes**

Run: `docker exec incapacidades-api python -m pytest tests/test_radicar_endpoint.py -v --no-cov`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add apps/backend/app/api/v1/endpoints/incapacidades.py apps/backend/app/tasks/email_tasks.py apps/backend/tests/test_radicar_endpoint.py
git commit -m "feat(radicacion): add individual radicar endpoint with document storage + summary email"
```

---

## Task 6: Frontend — company-scoped employee service + selector

**Files:**
- Create: `apps/frontend/portal-externo/src/services/empresaEmpleadoService.ts`
- Create: `apps/frontend/portal-externo/src/components/radicacion/EmpleadoSelector.tsx`
- Test: `src/components/radicacion/__tests__/EmpleadoSelector.test.tsx`

- [ ] **Step 1: Create the employee query (scoped to authenticated company)**

```typescript
// src/services/empresaEmpleadoService.ts
import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';
import { useAuthStore } from '@/store/authStore';
import type { EmpleadoResponse } from '@/types/api';

export function useEmpleadosDeMiEmpresa(search: string) {
  const empresaId = useAuthStore((s) => s.user?.empresa_id);
  return useQuery({
    queryKey: ['empleados', 'mi-empresa', empresaId, search],
    queryFn: async () => {
      const { data } = await api.get<EmpleadoResponse[]>('/empleados', {
        params: { empresa_id: empresaId, search: search || undefined, estado: 'ACTIVO', limit: 50 },
      });
      return data;
    },
    enabled: !!empresaId,
    staleTime: 5 * 60 * 1000,
  });
}
```

- [ ] **Step 2: Write the failing test for the selector**

```tsx
// src/components/radicacion/__tests__/EmpleadoSelector.test.tsx
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { EmpleadoSelector } from '@/components/radicacion/EmpleadoSelector';

vi.mock('@/services/empresaEmpleadoService', () => ({
  useEmpleadosDeMiEmpresa: () => ({
    data: [{ id: 'e1', numero_documento: '123', nombres: 'Ana', apellidos: 'Gómez' }],
    isLoading: false,
  }),
}));

const wrap = (ui: React.ReactNode) =>
  render(<QueryClientProvider client={new QueryClient()}>{ui}</QueryClientProvider>);

describe('EmpleadoSelector', () => {
  it('renders the help tooltip text and selects an employee', () => {
    const onChange = vi.fn();
    wrap(<EmpleadoSelector value={undefined} onChange={onChange} />);
    expect(screen.getByLabelText(/ayuda/i)).toBeInTheDocument();
    fireEvent.click(screen.getByText(/Ana Gómez/));
    expect(onChange).toHaveBeenCalledWith('e1');
  });
});
```

- [ ] **Step 3: Run test to verify it fails**

Run: `npm test -- src/components/radicacion/__tests__/EmpleadoSelector.test.tsx`
Expected: FAIL — component not found.

- [ ] **Step 4: Implement the selector with `?` tooltip**

```tsx
// src/components/radicacion/EmpleadoSelector.tsx
import { useState } from 'react';
import { HelpCircle } from 'lucide-react';
import { useEmpleadosDeMiEmpresa } from '@/services/empresaEmpleadoService';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';

interface Props {
  value?: string;
  onChange: (empleadoId: string) => void;
  error?: string;
}

export function EmpleadoSelector({ value, onChange, error }: Props) {
  const [search, setSearch] = useState('');
  const { data: empleados = [], isLoading } = useEmpleadosDeMiEmpresa(search);
  const seleccionado = empleados.find((e) => e.id === value);

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-1">
        <Label htmlFor="empleado-search">Empleado</Label>
        <span aria-label="ayuda" title="Si no encuentra al empleado, reporte el caso a Servicio al Cliente."
          className="text-muted-foreground cursor-help">
          <HelpCircle className="h-4 w-4" />
        </span>
      </div>
      <Input id="empleado-search" placeholder="Buscar por nombre o documento…"
        value={seleccionado ? `${seleccionado.nombres} ${seleccionado.apellidos}` : search}
        onChange={(e) => { setSearch(e.target.value); if (value) onChange(''); }} />
      {!seleccionado && (
        <ul className="max-h-48 overflow-auto rounded-md border border-border divide-y">
          {isLoading && <li className="p-2 text-sm text-muted-foreground">Cargando…</li>}
          {!isLoading && empleados.length === 0 && (
            <li className="p-2 text-sm text-muted-foreground">Sin resultados.</li>
          )}
          {empleados.map((e) => (
            <li key={e.id}>
              <button type="button" onClick={() => onChange(e.id)}
                className="w-full text-left p-2 text-sm hover:bg-muted">
                {e.nombres} {e.apellidos} — {e.numero_documento}
              </button>
            </li>
          ))}
        </ul>
      )}
      {error && <p className="text-sm text-[#D92D20]">{error}</p>}
    </div>
  );
}
```

- [ ] **Step 5: Run test to verify it passes**

Run: `npm test -- src/components/radicacion/__tests__/EmpleadoSelector.test.tsx`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/services/empresaEmpleadoService.ts src/components/radicacion/EmpleadoSelector.tsx src/components/radicacion/__tests__/EmpleadoSelector.test.tsx
git commit -m "feat(radicacion): add company-scoped employee selector with help tooltip"
```

---

## Task 7: Frontend — individual schema + ProrrogaSwitch

**Files:**
- Create: `apps/frontend/portal-externo/src/schemas/radicacionIndividualSchema.ts`
- Create: `apps/frontend/portal-externo/src/components/radicacion/ProrrogaSwitch.tsx`

- [ ] **Step 1: Create the schema (no empresa/solicitante; empleado_id + prorroga)**

```typescript
// src/schemas/radicacionIndividualSchema.ts
import { z } from 'zod';

export const radicacionIndividualSchema = z
  .object({
    empleado_id: z.string().uuid('Seleccione un empleado'),
    prorroga: z.boolean().default(false),
    tipo_enfermedad: z.enum(['ACCIDENTE_TRABAJO', 'ENFERMEDAD_LABORAL', 'ACCIDENTE_TRAYECTO'], {
      message: 'Seleccione el tipo de enfermedad',
    }),
    fecha_inicio: z.date({ required_error: 'La fecha de inicio es obligatoria' }),
    fecha_fin: z.date({ required_error: 'La fecha de fin es obligatoria' }),
    diagnostico_cie10: z.string().regex(/^[A-Z]\d{3}(\.\d{1,2})?$/, 'Formato CIE-10 inválido'),
    descripcion_diagnostico: z.string().max(500).optional().or(z.literal('')),
    nombre_medico: z.string().min(2, 'El nombre del médico es obligatorio').max(200),
    registro_medico: z.string().min(3).max(50).regex(/^[a-zA-Z0-9\-]+$/, 'Solo letras, números y guiones'),
    ips: z.string().max(255).optional().or(z.literal('')),
    observaciones: z.string().max(1000).optional().or(z.literal('')),
  })
  .refine((d) => !d.fecha_fin || !d.fecha_inicio || d.fecha_fin >= d.fecha_inicio, {
    message: 'La fecha de fin debe ser igual o posterior a la fecha de inicio',
    path: ['fecha_fin'],
  });

export type RadicacionIndividualFormData = z.infer<typeof radicacionIndividualSchema>;
```

- [ ] **Step 2: Create ProrrogaSwitch**

```tsx
// src/components/radicacion/ProrrogaSwitch.tsx
import { Label } from '@/components/ui/Label';

interface Props { checked: boolean; onChange: (v: boolean) => void; }

export function ProrrogaSwitch({ checked, onChange }: Props) {
  return (
    <div className="flex items-center justify-between rounded-md border border-input p-3">
      <div>
        <Label htmlFor="prorroga">¿Es una prórroga?</Label>
        <p className="text-xs text-muted-foreground">Active si esta incapacidad es continuación de una anterior.</p>
      </div>
      <button id="prorroga" type="button" role="switch" aria-checked={checked}
        onClick={() => onChange(!checked)}
        className={`relative h-6 w-11 rounded-full transition-colors ${checked ? 'bg-primary' : 'bg-gray-300'}`}>
        <span className={`absolute top-0.5 h-5 w-5 rounded-full bg-white transition-transform ${checked ? 'translate-x-5' : 'translate-x-0.5'}`} />
      </button>
    </div>
  );
}
```

- [ ] **Step 3: Commit**

```bash
git add src/schemas/radicacionIndividualSchema.ts src/components/radicacion/ProrrogaSwitch.tsx
git commit -m "feat(radicacion): add individual schema and prorroga switch"
```

---

## Task 8: Frontend — individual radication page + service + route

**Files:**
- Create: `apps/frontend/portal-externo/src/services/radicacionService.ts`
- Create: `apps/frontend/portal-externo/src/components/radicacion/RadicacionIndividualPage.tsx`
- Modify: `apps/frontend/portal-externo/src/App.tsx`
- Test: `src/components/radicacion/__tests__/RadicacionIndividualPage.test.tsx`

- [ ] **Step 1: Create the submit service (multipart)**

```typescript
// src/services/radicacionService.ts
import api from '@/lib/api';

export interface RadicacionResponse {
  total_radicadas: number;
  items: { empleado_id: string; incapacidad_id?: string; numero?: string; success: boolean; error?: string }[];
}

export async function radicarIndividual(form: FormData): Promise<RadicacionResponse> {
  const { data } = await api.post<RadicacionResponse>('/incapacidades/radicar', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}
```

- [ ] **Step 2: Write the failing test (smoke: renders steps, validates employee required)**

```tsx
// src/components/radicacion/__tests__/RadicacionIndividualPage.test.tsx
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { RadicacionIndividualPage } from '@/components/radicacion/RadicacionIndividualPage';

vi.mock('@/services/empresaEmpleadoService', () => ({
  useEmpleadosDeMiEmpresa: () => ({ data: [], isLoading: false }),
}));

const wrap = () => render(
  <QueryClientProvider client={new QueryClient()}>
    <MemoryRouter><RadicacionIndividualPage /></MemoryRouter>
  </QueryClientProvider>,
);

describe('RadicacionIndividualPage', () => {
  it('renders the form heading and the prorroga switch', () => {
    wrap();
    expect(screen.getByText(/radicación individual/i)).toBeInTheDocument();
    expect(screen.getByRole('switch')).toBeInTheDocument();
  });
});
```

- [ ] **Step 3: Run test to verify it fails**

Run: `npm test -- src/components/radicacion/__tests__/RadicacionIndividualPage.test.tsx`
Expected: FAIL — component not found.

- [ ] **Step 4: Implement the page**

```tsx
// src/components/radicacion/RadicacionIndividualPage.tsx
import { useState } from 'react';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useNavigate } from 'react-router-dom';
import { radicacionIndividualSchema, type RadicacionIndividualFormData } from '@/schemas/radicacionIndividualSchema';
import { EmpleadoSelector } from './EmpleadoSelector';
import { ProrrogaSwitch } from './ProrrogaSwitch';
import { radicarIndividual } from '@/services/radicacionService';
import { FileUpload } from '@/components/ui/FileUpload';
import { Button } from '@/components/ui/Button';
import { useToast } from '@/hooks/use-toast';

function toApiDate(d: Date) { return d.toISOString().split('T')[0]; }

export function RadicacionIndividualPage() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [files, setFiles] = useState<{ incapacidad: File[]; historia: File[]; soportes: File[] }>({ incapacidad: [], historia: [], soportes: [] });
  const { control, register, handleSubmit, formState: { errors, isSubmitting } } =
    useForm<RadicacionIndividualFormData>({ resolver: zodResolver(radicacionIndividualSchema), defaultValues: { prorroga: false } });

  const onSubmit = async (v: RadicacionIndividualFormData) => {
    if (files.incapacidad.length === 0) {
      toast({ title: 'Falta el documento de incapacidad', variant: 'destructive' }); return;
    }
    const dias = Math.max(1, Math.round((v.fecha_fin.getTime() - v.fecha_inicio.getTime()) / 86400000) + 1);
    const fd = new FormData();
    fd.append('empleado_id', v.empleado_id);
    fd.append('tipo_enfermedad', v.tipo_enfermedad);
    fd.append('fecha_inicio', toApiDate(v.fecha_inicio));
    fd.append('fecha_fin', toApiDate(v.fecha_fin));
    fd.append('dias_totales', String(dias));
    fd.append('diagnostico_cie10', v.diagnostico_cie10);
    fd.append('nombre_medico', v.nombre_medico);
    fd.append('registro_medico', v.registro_medico);
    fd.append('prorroga', String(v.prorroga));
    if (v.descripcion_diagnostico) fd.append('descripcion_diagnostico', v.descripcion_diagnostico);
    if (v.ips) fd.append('ips', v.ips);
    if (v.observaciones) fd.append('observaciones', v.observaciones);
    files.incapacidad.forEach((f) => fd.append('incapacidad_medica', f));
    files.historia.forEach((f) => fd.append('historia_clinica', f));
    files.soportes.forEach((f) => fd.append('soportes_adicionales', f));

    try {
      const resp = await radicarIndividual(fd);
      const item = resp.items[0];
      if (!item.success) { toast({ title: 'No se pudo radicar', description: item.error, variant: 'destructive' }); return; }
      toast({ title: 'Incapacidad radicada', description: `Número: ${item.numero}` });
      navigate('/consulta');
    } catch (e: any) {
      toast({ title: 'Error al radicar', description: e?.response?.data?.detail || 'Intente nuevamente', variant: 'destructive' });
    }
  };

  return (
    <div className="max-w-3xl mx-auto p-6 space-y-6">
      <h1 className="text-2xl font-bold text-foreground">Radicación Individual</h1>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6 bg-white rounded-lg shadow-sm border border-border p-6">
        <Controller control={control} name="empleado_id"
          render={({ field }) => (
            <EmpleadoSelector value={field.value} onChange={field.onChange} error={errors.empleado_id?.message} />
          )} />
        <Controller control={control} name="prorroga"
          render={({ field }) => <ProrrogaSwitch checked={field.value} onChange={field.onChange} />} />
        {/* Reuse the existing incapacidad-data fields (tipo_enfermedad, fechas, CIE-10, médico, IPS, etc.)
            with the project's Input/Select/DatePicker/CIE10Autocomplete primitives, bound via register/Controller.
            Mirror Paso2IncapacidadDocumentos for field layout, minus solicitante/empresa. */}
        <div className="space-y-4">
          <label className="block text-sm font-medium text-foreground">Documento de incapacidad (obligatorio)</label>
          <FileUpload onFileSelect={(f) => setFiles((p) => ({ ...p, incapacidad: f }))} maxFiles={1} />
          <label className="block text-sm font-medium text-foreground">Historia clínica (opcional)</label>
          <FileUpload onFileSelect={(f) => setFiles((p) => ({ ...p, historia: f }))} maxFiles={3} />
          <label className="block text-sm font-medium text-foreground">Soportes adicionales (opcional)</label>
          <FileUpload onFileSelect={(f) => setFiles((p) => ({ ...p, soportes: f }))} maxFiles={5} />
        </div>
        <div className="flex justify-end gap-3">
          <Button type="button" variant="outline" onClick={() => navigate('/')}>Cancelar</Button>
          <Button type="submit" disabled={isSubmitting}>{isSubmitting ? 'Radicando…' : 'Radicar incapacidad'}</Button>
        </div>
      </form>
    </div>
  );
}
```

> The incapacidad-data fields (tipo_enfermedad, fecha_inicio, fecha_fin, diagnostico_cie10,
> descripcion_diagnostico, nombre_medico, registro_medico, ips, observaciones) must be added
> using the existing primitives (`Select`, `DatePicker`, `CIE10Autocomplete`, `Input`, `Textarea`)
> bound to the form. Copy the field markup from `Paso2IncapacidadDocumentos.tsx`, removing the
> solicitante/empresa pieces. Keep validations from `radicacionIndividualSchema`.

- [ ] **Step 5: Add the route**

In `src/App.tsx`, inside the `<ProtectedRoute />` block:

```tsx
import { RadicacionIndividualPage } from '@/components/radicacion/RadicacionIndividualPage';
// ...
<Route path="/radicar/individual" element={<RadicacionIndividualPage />} />
```

- [ ] **Step 6: Run tests + build**

Run: `npm test -- src/components/radicacion && npm run build`
Expected: PASS + build OK.

- [ ] **Step 7: Commit**

```bash
git add src/services/radicacionService.ts src/components/radicacion/RadicacionIndividualPage.tsx src/App.tsx src/components/radicacion/__tests__/
git commit -m "feat(radicacion): add individual filing page wired to shared pipeline"
```

---

## Self-Review Notes (coverage vs spec Phase 2)

- Remove company step (resolved from auth) → pipeline uses `current_user.empresa`. ✅
- Remove solicitante step (auto-resolved) → Task 2 resolver. ✅
- Employee selector scoped to company + `?` tooltip text → Task 6. ✅
- `prorroga` switch + DB column → Tasks 1, 7. ✅
- Attachments same slot-based upload (D9) → Task 8 uses existing `FileUpload`. ✅
- Unified pipeline (D5), individual = N=1 → Tasks 4–5. ✅
- Audit enqueue + external integration are injected hooks (defaults no-op) → replaced in Phase 4 / Phase 3.6. ✅ (dependency noted)

**Known cross-phase TODOs created here:** temporary no-op `enqueue_auditoria_incapacidad` (Phase 4 replaces); no-op `integracion` hook (Phase 3.6 replaces). Both are explicit and tested via the no-op path.

**Manual verification:** log in as EMPRESA, open `/radicar/individual`, pick an employee, toggle prórroga, attach a PDF, submit; confirm a `numero` is returned and the Incapacidad exists in `RADICADA` with `prorroga=true` and a resolved solicitante.

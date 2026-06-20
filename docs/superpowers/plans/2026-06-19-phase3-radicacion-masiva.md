# Phase 3 — Radicación Masiva + Integración (stubs) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **Depends on:** Phase 1 (auth), Phase 2 (`RadicacionPipelineService`, `prorroga`, employee selector, `radicacionService`).
> **Provides:** ServiAlfa/Sicat stubs + `communication_log` (3.6) wired into the pipeline; bulk Excel/ZIP UI + endpoints.

**Goal:** Let an EMPRESA user bulk-file ARL disabilities: download a pre-fillable Excel template, upload it for per-row validation, attach documents per row or via a global ZIP, and submit once every row passes — creating Incapacidades through the shared pipeline, with each filing logged to `communication_log` and a stubbed ServiAlfa/Sicat integration.

**Architecture:** Backend gains `communication_log` + `incapacidad.numero_radicacion_servialfa` (migrations), `ServiAlfaClient`/`SicatClient` stubs behind an `IntegracionService` that logs every attempt, and three endpoints: template generation (openpyxl), Excel validation, ZIP mapping. Bulk submit reuses `RadicacionPipelineService` with N rows and the real integration hook. Frontend: a masiva page orchestrating template modal → upload/validation table → per-row/ZIP documents → gated submit.

**Tech Stack:** FastAPI, openpyxl, Python `zipfile`, SQLAlchemy/Alembic, Celery; React 19, React Query, vitest.

---

## File Structure

**Backend:**
- Migrations: `add_numero_radicacion_servialfa_to_incapacidad`, `create_communication_log`.
- Create: `app/models/communication_log.py`.
- Modify: `app/models/incapacidad.py` — `numero_radicacion_servialfa` + `communication_logs` rel.
- Create: `app/services/integracion/servialfa_client.py`, `app/services/integracion/sicat_client.py`, `app/services/integracion/integracion_service.py`.
- Create: `app/services/incapacidad_validation_rules.py` — shared rule functions operating on a plain dict.
- Create: `app/services/bulk_radicacion_service.py` — Excel template gen, parse+validate, ZIP map.
- Modify: `app/api/v1/endpoints/incapacidades.py` — `/radicar-masiva/plantilla`, `/radicar-masiva/validar`, `/radicar-masiva/zip`, `/radicar-masiva` (submit).
- Tests: `test_communication_log.py`, `test_integracion_stubs.py`, `test_bulk_template.py`, `test_bulk_validation.py`, `test_bulk_zip.py`, `test_bulk_submit.py`.

**Frontend:**
- Create: `src/services/bulkRadicacionService.ts`.
- Create: `src/components/radicacion/masiva/SeleccionEmpleadosModal.tsx`.
- Create: `src/components/radicacion/masiva/TablaValidacion.tsx`.
- Create: `src/components/radicacion/masiva/ZipUpload.tsx`.
- Create: `src/components/radicacion/masiva/RadicacionMasivaPage.tsx`.
- Modify: `src/App.tsx` — `/radicar/masiva`.

---

## Task 1: Backend — `numero_radicacion_servialfa` + `communication_log`

**Files:**
- Modify: `app/models/incapacidad.py`
- Create: `app/models/communication_log.py`
- Migrations under `alembic/versions/`
- Test: `tests/test_communication_log.py`

- [ ] **Step 1: Add the model column**

```python
# app/models/incapacidad.py  (add near other columns)
    numero_radicacion_servialfa: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True,
        comment="Número de radicación definitivo retornado por ServiAlfa (llega vía integración)",
    )
```

And add the relationship (after `validation_inconsistencias`):

```python
    communication_logs: Mapped[list["CommunicationLog"]] = relationship(
        "CommunicationLog", back_populates="incapacidad", cascade="all, delete-orphan",
    )
```

- [ ] **Step 2: Create the CommunicationLog model**

```python
# app/models/communication_log.py
"""Bitácora de intentos de integración con sistemas externos (ServiAlfa, Sicat).

Sirve como prueba de radicación y trazabilidad para auditorías.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID
from sqlalchemy import String, Text, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB

from app.models.base import BaseModel


class CommunicationLog(BaseModel):
    __tablename__ = "communication_log"

    incapacidad_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("incapacidad.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    sistema: Mapped[str] = mapped_column(String(20), nullable=False, comment="SERVIALFA | SICAT")
    estado: Mapped[str] = mapped_column(String(20), nullable=False, comment="SUCCESS | FAILURE | PENDING")
    payload_resumen: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    respuesta: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    mensaje: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at_log: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    incapacidad: Mapped["Incapacidad"] = relationship("Incapacidad", back_populates="communication_logs")

    def __repr__(self) -> str:
        return f"<CommunicationLog {self.sistema} [{self.estado}] inc={self.incapacidad_id}>"
```

> Register the model in `app/models/__init__.py` so Alembic autogenerate sees it.

- [ ] **Step 3: Generate + apply migrations**

Run: `cd apps/backend && make migrate msg='add numero_radicacion_servialfa and communication_log'`
Confirm the generated migration adds the column AND creates `communication_log` (PK, FK→incapacidad CASCADE, index on `incapacidad_id`). Then:
Run: `docker exec incapacidades-api alembic upgrade head`

- [ ] **Step 4: Write + run the model test**

```python
# tests/test_communication_log.py
import datetime as dt
import pytest
from sqlalchemy import select
from app.models.communication_log import CommunicationLog
from app.models.incapacidad import Incapacidad


@pytest.mark.asyncio
async def test_communication_log_links_to_incapacidad(db_session, incapacidad_factory):
    inc = await incapacidad_factory(db_session)  # helper creating a minimal ARL incapacidad
    log = CommunicationLog(incapacidad_id=inc.id, sistema="SERVIALFA", estado="PENDING",
                           payload_resumen={"numero": inc.numero})
    db_session.add(log); await db_session.flush()
    found = (await db_session.execute(select(CommunicationLog).where(CommunicationLog.incapacidad_id == inc.id))).scalars().all()
    assert len(found) == 1 and found[0].sistema == "SERVIALFA"
```

Run: `docker exec incapacidades-api python -m pytest tests/test_communication_log.py -v --no-cov`
Expected: PASS (add `incapacidad_factory` to conftest if absent — a minimal valid ARL `Incapacidad`).

- [ ] **Step 5: Commit**

```bash
git add apps/backend/app/models/communication_log.py apps/backend/app/models/incapacidad.py apps/backend/app/models/__init__.py apps/backend/alembic/versions/ apps/backend/tests/test_communication_log.py
git commit -m "feat(db): add communication_log table and servialfa number column"
```

---

## Task 2: Backend — ServiAlfa/Sicat stubs + IntegracionService

**Files:**
- Create: `app/services/integracion/__init__.py`, `servialfa_client.py`, `sicat_client.py`, `integracion_service.py`
- Test: `tests/test_integracion_stubs.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_integracion_stubs.py
import pytest
from sqlalchemy import select
from app.services.integracion.integracion_service import IntegracionService
from app.models.communication_log import CommunicationLog


@pytest.mark.asyncio
async def test_integracion_logs_servialfa_and_sicat(db_session, incapacidad_factory):
    inc = await incapacidad_factory(db_session)
    svc = IntegracionService(db_session)
    await svc.procesar(db_session, inc)
    logs = (await db_session.execute(select(CommunicationLog).where(CommunicationLog.incapacidad_id == inc.id))).scalars().all()
    sistemas = {l.sistema for l in logs}
    assert {"SERVIALFA", "SICAT"} <= sistemas
    # ServiAlfa number stored on the incapacidad
    assert inc.numero_radicacion_servialfa is not None
    # Sicat log references the servialfa number
    sicat = next(l for l in logs if l.sistema == "SICAT")
    assert sicat.payload_resumen.get("numero_radicacion_servialfa") == inc.numero_radicacion_servialfa
```

- [ ] **Step 2: Run test to verify it fails**

Run: `docker exec incapacidades-api python -m pytest tests/test_integracion_stubs.py -v --no-cov`
Expected: FAIL — module not found.

- [ ] **Step 3: Implement the stub clients**

```python
# app/services/integracion/servialfa_client.py
"""Cliente ServiAlfa (Centro de Operaciones de Servicio al Cliente).

STUB: hoy retorna un número mock. Sustituir `enviar` por la llamada HTTP real
cuando lleguen las specs, manteniendo la firma.
"""
from datetime import datetime
from app.models.incapacidad import Incapacidad


class ServiAlfaClient:
    async def enviar(self, incapacidad: Incapacidad) -> dict:
        numero = f"SA-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{str(incapacidad.id)[:8]}"
        return {
            "estado": "SUCCESS",
            "numero_radicacion_servialfa": numero,
            "payload_resumen": {"numero": incapacidad.numero, "empleado_id": str(incapacidad.empleado_id)},
            "respuesta": {"ok": True, "stub": True},
        }
```

```python
# app/services/integracion/sicat_client.py
"""Cliente Sicat (Centro de Gestión Documental).

STUB: hoy retorna éxito. Cada envío referencia el numero_radicacion_servialfa.
"""
from app.models.incapacidad import Incapacidad


class SicatClient:
    async def enviar(self, incapacidad: Incapacidad, numero_radicacion_servialfa: str) -> dict:
        return {
            "estado": "SUCCESS",
            "payload_resumen": {
                "numero": incapacidad.numero,
                "numero_radicacion_servialfa": numero_radicacion_servialfa,
                "documentos": len(incapacidad.documentos) if incapacidad.documentos is not None else 0,
            },
            "respuesta": {"ok": True, "stub": True},
        }
```

- [ ] **Step 4: Implement the orchestrating IntegracionService**

```python
# app/services/integracion/integracion_service.py
"""Orquesta ServiAlfa → Sicat y registra cada intento en communication_log."""
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.models.incapacidad import Incapacidad
from app.models.communication_log import CommunicationLog
from app.services.integracion.servialfa_client import ServiAlfaClient
from app.services.integracion.sicat_client import SicatClient


class IntegracionService:
    def __init__(self, db: AsyncSession, servialfa: ServiAlfaClient | None = None, sicat: SicatClient | None = None):
        self.servialfa = servialfa or ServiAlfaClient()
        self.sicat = sicat or SicatClient()

    def _log(self, db, inc, sistema, result):
        db.add(CommunicationLog(
            incapacidad_id=inc.id, sistema=sistema,
            estado=result.get("estado", "FAILURE"),
            payload_resumen=result.get("payload_resumen"),
            respuesta=result.get("respuesta"),
            mensaje=result.get("mensaje"),
        ))

    async def procesar(self, db: AsyncSession, inc: Incapacidad) -> None:
        """Hook compatible con RadicacionPipelineService.integracion."""
        # 1. ServiAlfa
        try:
            sa = await self.servialfa.enviar(inc)
        except Exception as exc:
            logger.error(f"ServiAlfa falló para {inc.id}: {exc}")
            self._log(db, inc, "SERVIALFA", {"estado": "FAILURE", "mensaje": str(exc)})
            return
        inc.numero_radicacion_servialfa = sa["numero_radicacion_servialfa"]
        self._log(db, inc, "SERVIALFA", sa)

        # 2. Sicat (referencia el número de ServiAlfa)
        try:
            sk = await self.sicat.enviar(inc, inc.numero_radicacion_servialfa)
            self._log(db, inc, "SICAT", sk)
        except Exception as exc:
            logger.error(f"Sicat falló para {inc.id}: {exc}")
            self._log(db, inc, "SICAT", {"estado": "FAILURE", "mensaje": str(exc),
                                          "payload_resumen": {"numero_radicacion_servialfa": inc.numero_radicacion_servialfa}})
        await db.flush()
```

> `app/services/integracion/__init__.py` may be empty.

- [ ] **Step 5: Run test to verify it passes**

Run: `docker exec incapacidades-api python -m pytest tests/test_integracion_stubs.py -v --no-cov`
Expected: PASS.

- [ ] **Step 6: Wire the real hook into the pipeline endpoints**

In `app/api/v1/endpoints/incapacidades.py`, change the pipeline construction (individual endpoint from Phase 2 **and** the bulk submit endpoint in Task 8) to inject the integration hook:

```python
from app.services.integracion.integracion_service import IntegracionService
# ...
integracion = IntegracionService(db)
pipeline = RadicacionPipelineService(db, enqueue_auditoria=enqueue_auditoria_incapacidad, integracion=integracion.procesar)
```

- [ ] **Step 7: Commit**

```bash
git add apps/backend/app/services/integracion/ apps/backend/app/api/v1/endpoints/incapacidades.py apps/backend/tests/test_integracion_stubs.py
git commit -m "feat(integracion): add ServiAlfa/Sicat stubs logging to communication_log"
```

---

## Task 3: Backend — shared validation rules (dict-based)

**Files:**
- Create: `app/services/incapacidad_validation_rules.py`
- Test: `tests/test_incapacidad_validation_rules.py`

> Port the field + business rules out of `PreIncapacidadValidationService` into pure functions
> that take a plain `dict` (a parsed Excel row) and return a list of issues. This module is reused
> by bulk validation here AND by the Phase 4 audit job (operating on an Incapacidad mapped to a dict).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_incapacidad_validation_rules.py
import datetime as dt
from app.services.incapacidad_validation_rules import validate_field_level, validate_business_rules


def _valid_row():
    return dict(
        empleado_numero_documento="123456", tipo="ARL", tipo_enfermedad="ACCIDENTE_TRABAJO",
        fecha_inicio=dt.date(2026, 6, 1), fecha_fin=dt.date(2026, 6, 5), dias_totales=5,
        diagnostico_cie10="S00.0", nombre_medico="Dr X", registro_medico="RM-1",
    )


def test_field_level_flags_missing_document():
    row = _valid_row(); row["empleado_numero_documento"] = ""
    issues = validate_field_level(row)
    assert any(i["codigo"] == "EMPTY_EMPLEADO_NUMERO" for i in issues)


def test_field_level_flags_inverted_dates():
    row = _valid_row(); row["fecha_fin"] = dt.date(2026, 5, 1)
    issues = validate_field_level(row)
    assert any(i["codigo"] == "INVALID_DATE_RANGE" for i in issues)


def test_business_rules_flag_dias_mismatch():
    row = _valid_row(); row["dias_totales"] = 99
    issues = validate_business_rules(row)
    assert any(i["codigo"] == "DIAS_TOTALES_MISMATCH" for i in issues)


def test_valid_row_has_no_field_issues():
    assert validate_field_level(_valid_row()) == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `docker exec incapacidades-api python -m pytest tests/test_incapacidad_validation_rules.py -v --no-cov`
Expected: FAIL — module not found.

- [ ] **Step 3: Implement the rules module**

```python
# app/services/incapacidad_validation_rules.py
"""Reglas de validación reutilizables sobre una fila/dict de incapacidad.

Origen: PreIncapacidadValidationService. Aquí son funciones puras (dict -> issues),
reutilizadas por la radicación masiva (validación de Excel) y por el job de auditoría
(Phase 4, mapeando una Incapacidad a dict).
"""
from datetime import date

ISSUE_KEYS = ("codigo", "categoria", "severidad", "descripcion", "campo_afectado")


def _issue(codigo, categoria, severidad, descripcion, campo=None):
    return {"codigo": codigo, "categoria": categoria, "severidad": severidad,
            "descripcion": descripcion, "campo_afectado": campo}


def validate_field_level(row: dict) -> list[dict]:
    issues: list[dict] = []
    req = {
        "empleado_numero_documento": "EMPTY_EMPLEADO_NUMERO",
        "tipo_enfermedad": "EMPTY_TIPO_ENFERMEDAD",
        "diagnostico_cie10": "EMPTY_DIAGNOSTICO_CIE10",
        "nombre_medico": "EMPTY_NOMBRE_MEDICO",
        "registro_medico": "EMPTY_REGISTRO_MEDICO",
    }
    for campo, codigo in req.items():
        if not row.get(campo):
            issues.append(_issue(codigo, "FIELD_VALIDATION", "ERROR", f"{campo} es requerido", campo))

    if row.get("tipo") not in ("ARL", "SALUD"):
        issues.append(_issue("INVALID_TIPO", "FIELD_VALIDATION", "ERROR", "Tipo debe ser ARL o SALUD", "tipo"))
    if not row.get("fecha_inicio"):
        issues.append(_issue("EMPTY_FECHA_INICIO", "FIELD_VALIDATION", "ERROR", "Fecha de inicio requerida", "fecha_inicio"))
    if not row.get("fecha_fin"):
        issues.append(_issue("EMPTY_FECHA_FIN", "FIELD_VALIDATION", "ERROR", "Fecha de fin requerida", "fecha_fin"))
    if row.get("fecha_inicio") and row.get("fecha_fin") and row["fecha_fin"] < row["fecha_inicio"]:
        issues.append(_issue("INVALID_DATE_RANGE", "FIELD_VALIDATION", "ERROR",
                             "Fecha de fin no puede ser anterior a fecha de inicio", "fecha_fin"))
    return issues


def validate_business_rules(row: dict) -> list[dict]:
    issues: list[dict] = []
    fi, ff, dias = row.get("fecha_inicio"), row.get("fecha_fin"), row.get("dias_totales")
    if fi and ff:
        expected = (ff - fi).days + 1
        if dias is not None and dias != expected:
            issues.append(_issue("DIAS_TOTALES_MISMATCH", "BUSINESS_RULE", "WARNING",
                                 f"Días totales ({dias}) no coincide con el rango ({expected})", "dias_totales"))
    if fi and (date.today() - fi).days > 30:
        issues.append(_issue("RETROACTIVE_BEYOND_LIMIT", "BUSINESS_RULE", "WARNING",
                             "Incapacidad retroactiva más de 30 días", "fecha_inicio"))
    if dias and dias > 180:
        issues.append(_issue("DURATION_EXCEEDS_LIMIT", "BUSINESS_RULE", "WARNING",
                             "Duración excede 180 días", "dias_totales"))
    return issues


def validate_row(row: dict) -> list[dict]:
    return validate_field_level(row) + validate_business_rules(row)
```

> After this lands, refactor `PreIncapacidadValidationService.validate_field_level/validate_business_rules`
> to delegate to these functions (mapping the model to a dict) so there is a single source of truth.
> Keep the existing service tests green.

- [ ] **Step 4: Run test to verify it passes**

Run: `docker exec incapacidades-api python -m pytest tests/test_incapacidad_validation_rules.py -v --no-cov`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/backend/app/services/incapacidad_validation_rules.py apps/backend/tests/test_incapacidad_validation_rules.py
git commit -m "feat(validation): extract reusable dict-based incapacidad validation rules"
```

---

## Task 4: Backend — Excel template generation

**Files:**
- Create: `app/services/bulk_radicacion_service.py` (template part)
- Modify: `app/api/v1/endpoints/incapacidades.py` — `POST /radicar-masiva/plantilla`
- Test: `tests/test_bulk_template.py`

> Columns (must mirror individual fields incl. `prorroga`):
> `numero_documento, tipo_documento, empleado_nombres, empleado_apellidos, tipo_enfermedad,
> fecha_inicio, fecha_fin, dias_totales, diagnostico_cie10, descripcion_diagnostico,
> nombre_medico, registro_medico, ips, valor_dia, prorroga, observaciones`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_bulk_template.py
import io
import pytest
from openpyxl import load_workbook
from httpx import AsyncClient

EXPECTED_HEADERS = ["numero_documento","tipo_documento","empleado_nombres","empleado_apellidos",
  "tipo_enfermedad","fecha_inicio","fecha_fin","dias_totales","diagnostico_cie10",
  "descripcion_diagnostico","nombre_medico","registro_medico","ips","valor_dia","prorroga","observaciones"]


@pytest.mark.asyncio
async def test_template_headers_only(client: AsyncClient, empresa_user_token):
    resp = await client.post("/api/v1/incapacidades/radicar-masiva/plantilla", json={"empleado_ids": []},
                             headers={"Authorization": f"Bearer {empresa_user_token}"})
    assert resp.status_code == 200
    wb = load_workbook(io.BytesIO(resp.content))
    ws = wb.active
    headers = [c.value for c in ws[1]]
    assert headers == EXPECTED_HEADERS
    assert ws.max_row == 1  # headers only


@pytest.mark.asyncio
async def test_template_prefilled(client: AsyncClient, empresa_user_token, empleado_de_empresa):
    resp = await client.post("/api/v1/incapacidades/radicar-masiva/plantilla",
                             json={"empleado_ids": [str(empleado_de_empresa.id)]},
                             headers={"Authorization": f"Bearer {empresa_user_token}"})
    wb = load_workbook(io.BytesIO(resp.content)); ws = wb.active
    assert ws.max_row == 2
    assert ws.cell(row=2, column=1).value == empleado_de_empresa.numero_documento
```

- [ ] **Step 2: Run test to verify it fails**

Run: `docker exec incapacidades-api python -m pytest tests/test_bulk_template.py -v --no-cov`
Expected: FAIL — route missing.

- [ ] **Step 3: Implement the template generator**

```python
# app/services/bulk_radicacion_service.py
"""Servicio de radicación masiva: plantilla Excel, parseo+validación, mapeo ZIP."""
import io
from uuid import UUID
from openpyxl import Workbook, load_workbook
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.empleado import Empleado

TEMPLATE_HEADERS = [
    "numero_documento", "tipo_documento", "empleado_nombres", "empleado_apellidos",
    "tipo_enfermedad", "fecha_inicio", "fecha_fin", "dias_totales", "diagnostico_cie10",
    "descripcion_diagnostico", "nombre_medico", "registro_medico", "ips", "valor_dia",
    "prorroga", "observaciones",
]


async def generar_plantilla(db: AsyncSession, empresa_id: UUID, empleado_ids: list[UUID]) -> bytes:
    wb = Workbook(); ws = wb.active; ws.title = "Incapacidades"
    ws.append(TEMPLATE_HEADERS)
    if empleado_ids:
        empleados = (await db.execute(
            select(Empleado).where(Empleado.id.in_(empleado_ids), Empleado.empresa_id == empresa_id)
        )).scalars().all()
        for e in empleados:
            ws.append([e.numero_documento, str(e.tipo_documento), e.nombres, e.apellidos,
                       "", "", "", "", "", "", "", "", "", "", "NO", ""])
    buf = io.BytesIO(); wb.save(buf); return buf.getvalue()
```

Endpoint:

```python
# app/api/v1/endpoints/incapacidades.py
from fastapi.responses import StreamingResponse
from pydantic import BaseModel as _BM

class PlantillaRequest(_BM):
    empleado_ids: list[UUID] = []

@router.post("/radicar-masiva/plantilla", summary="Descargar plantilla Excel (EMPRESA)")
async def descargar_plantilla(payload: PlantillaRequest, db: AsyncSession = Depends(get_db),
                              current_user: Usuario = Depends(require_empresa)):
    from app.services.bulk_radicacion_service import generar_plantilla
    content = await generar_plantilla(db, current_user.empresa_id, payload.empleado_ids)
    return StreamingResponse(
        io.BytesIO(content),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=plantilla_incapacidades.xlsx"},
    )
```

> Confirm `openpyxl` is in `apps/backend/pyproject.toml`/requirements. If not: add it and `make install`.

- [ ] **Step 4: Run test to verify it passes**

Run: `docker exec incapacidades-api python -m pytest tests/test_bulk_template.py -v --no-cov`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/backend/app/services/bulk_radicacion_service.py apps/backend/app/api/v1/endpoints/incapacidades.py apps/backend/tests/test_bulk_template.py
git commit -m "feat(masiva): add Excel template generation endpoint"
```

---

## Task 5: Backend — Excel upload + per-row validation

**Files:**
- Modify: `app/services/bulk_radicacion_service.py` (parse + validate)
- Modify: `app/api/v1/endpoints/incapacidades.py` — `POST /radicar-masiva/validar`
- Test: `tests/test_bulk_validation.py`

> Returns one result per non-empty row: row index, the parsed fields, the matched `empleado_id`
> (resolved by `numero_documento` within the company), and **all** validation errors.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_bulk_validation.py
import io
import datetime as dt
import pytest
from openpyxl import Workbook
from httpx import AsyncClient
from app.services.bulk_radicacion_service import TEMPLATE_HEADERS


def _xlsx(rows):
    wb = Workbook(); ws = wb.active; ws.append(TEMPLATE_HEADERS)
    for r in rows: ws.append(r)
    buf = io.BytesIO(); wb.save(buf); buf.seek(0); return buf


@pytest.mark.asyncio
async def test_validation_reports_errors_and_skips_empty(client, empresa_user_token, empleado_de_empresa):
    doc = empleado_de_empresa.numero_documento
    good = [doc, "CC", "Ana", "Gómez", "ACCIDENTE_TRABAJO", "2026-06-01", "2026-06-05", 5, "S00.0", "", "Dr X", "RM-1", "", "", "NO", ""]
    bad = [doc, "CC", "Ana", "Gómez", "ACCIDENTE_TRABAJO", "2026-06-10", "2026-06-05", 5, "", "", "", "", "", "", "NO", ""]
    empty = ["", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""]
    buf = _xlsx([good, bad, empty])
    resp = await client.post("/api/v1/incapacidades/radicar-masiva/validar",
        files={"archivo": ("data.xlsx", buf, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        headers={"Authorization": f"Bearer {empresa_user_token}"})
    assert resp.status_code == 200
    rows = resp.json()["filas"]
    assert len(rows) == 2  # empty row skipped
    assert rows[0]["valida"] is True and rows[0]["empleado_id"]
    assert rows[1]["valida"] is False
    codigos = {e["codigo"] for e in rows[1]["errores"]}
    assert "INVALID_DATE_RANGE" in codigos and "EMPTY_DIAGNOSTICO_CIE10" in codigos
```

- [ ] **Step 2: Run test to verify it fails**

Run: `docker exec incapacidades-api python -m pytest tests/test_bulk_validation.py -v --no-cov`
Expected: FAIL — route missing.

- [ ] **Step 3: Implement parse + validate**

```python
# app/services/bulk_radicacion_service.py  (append)
import datetime as dt
from app.services.incapacidad_validation_rules import validate_row

def _parse_date(v):
    if v in (None, ""): return None
    if isinstance(v, dt.datetime): return v.date()
    if isinstance(v, dt.date): return v
    return dt.date.fromisoformat(str(v).strip()[:10])

def _is_empty(values) -> bool:
    return all(v in (None, "") for v in values)


async def parsear_y_validar(db: AsyncSession, empresa_id: UUID, file_bytes: bytes) -> list[dict]:
    wb = load_workbook(io.BytesIO(file_bytes), data_only=True); ws = wb.active
    # map docs of this company once
    empleados = (await db.execute(select(Empleado).where(Empleado.empresa_id == empresa_id))).scalars().all()
    by_doc = {e.numero_documento.strip(): e for e in empleados}

    resultados = []
    for idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        cells = list(row) + [None] * (len(TEMPLATE_HEADERS) - len(row))
        if _is_empty(cells):
            continue
        data = dict(zip(TEMPLATE_HEADERS, cells))
        empleado = by_doc.get(str(data.get("numero_documento") or "").strip())
        parsed = {
            "tipo": "ARL",
            "empleado_numero_documento": str(data.get("numero_documento") or "").strip(),
            "tipo_enfermedad": data.get("tipo_enfermedad"),
            "fecha_inicio": _parse_date(data.get("fecha_inicio")),
            "fecha_fin": _parse_date(data.get("fecha_fin")),
            "dias_totales": int(data["dias_totales"]) if data.get("dias_totales") not in (None, "") else None,
            "diagnostico_cie10": data.get("diagnostico_cie10"),
            "descripcion_diagnostico": data.get("descripcion_diagnostico"),
            "nombre_medico": data.get("nombre_medico"),
            "registro_medico": data.get("registro_medico"),
            "ips": data.get("ips"),
            "valor_dia": data.get("valor_dia"),
            "prorroga": str(data.get("prorroga") or "").strip().upper() in ("SI", "SÍ", "TRUE", "1", "YES"),
            "observaciones": data.get("observaciones"),
        }
        errores = validate_row(parsed)
        if empleado is None:
            errores.append({"codigo": "EMPLEADO_NO_ENCONTRADO", "categoria": "INTEGRATION_CHECK",
                            "severidad": "ERROR", "descripcion": "Empleado no pertenece a su empresa o no existe",
                            "campo_afectado": "numero_documento"})
        resultados.append({
            "fila": idx,
            "empleado_id": str(empleado.id) if empleado else None,
            "datos": {**parsed, "fecha_inicio": parsed["fecha_inicio"].isoformat() if parsed["fecha_inicio"] else None,
                      "fecha_fin": parsed["fecha_fin"].isoformat() if parsed["fecha_fin"] else None},
            "errores": errores,
            "valida": len(errores) == 0,
        })
    return resultados
```

Endpoint:

```python
@router.post("/radicar-masiva/validar", summary="Validar Excel masivo (EMPRESA)")
async def validar_masivo(archivo: UploadFile = File(...), db: AsyncSession = Depends(get_db),
                         current_user: Usuario = Depends(require_empresa)):
    from app.services.bulk_radicacion_service import parsear_y_validar
    content = await archivo.read()
    filas = await parsear_y_validar(db, current_user.empresa_id, content)
    return {"filas": filas, "total": len(filas), "validas": sum(1 for f in filas if f["valida"])}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `docker exec incapacidades-api python -m pytest tests/test_bulk_validation.py -v --no-cov`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/backend/app/services/bulk_radicacion_service.py apps/backend/app/api/v1/endpoints/incapacidades.py apps/backend/tests/test_bulk_validation.py
git commit -m "feat(masiva): add Excel upload + per-row validation endpoint"
```

---

## Task 6: Backend — global ZIP mapping

**Files:**
- Modify: `app/services/bulk_radicacion_service.py` (zip map)
- Modify: `app/api/v1/endpoints/incapacidades.py` — `POST /radicar-masiva/zip`
- Test: `tests/test_bulk_zip.py`

> Convention: `{numero_documento}_{TIPO}.{ext}` (e.g. `1023555444_INCAPACIDAD.pdf`).
> Max ZIP size 20 MB. Returns, per filename, the matched `numero_documento`, `tipo`, and whether
> it matched a known document of the company. The frontend keeps the actual file bytes locally and
> only re-sends them on final submit; this endpoint validates the **mapping**.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_bulk_zip.py
import io, zipfile
import pytest


def _zip(names):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for n in names: z.writestr(n, b"x")
    buf.seek(0); return buf


@pytest.mark.asyncio
async def test_zip_maps_filenames(client, empresa_user_token, empleado_de_empresa):
    doc = empleado_de_empresa.numero_documento
    buf = _zip([f"{doc}_INCAPACIDAD.pdf", f"{doc}_HISTORIA_CLINICA.jpg", "basura.txt"])
    resp = await client.post("/api/v1/incapacidades/radicar-masiva/zip",
        files={"archivo": ("docs.zip", buf, "application/zip")},
        data={"documentos_esperados": doc},
        headers={"Authorization": f"Bearer {empresa_user_token}"})
    assert resp.status_code == 200
    body = resp.json()
    matched = {(m["numero_documento"], m["tipo"]) for m in body["asignaciones"] if m["match"]}
    assert (doc, "INCAPACIDAD") in matched and (doc, "HISTORIA_CLINICA") in matched
    assert any(m["match"] is False for m in body["asignaciones"])  # basura.txt
```

- [ ] **Step 2: Run test to verify it fails**

Run: `docker exec incapacidades-api python -m pytest tests/test_bulk_zip.py -v --no-cov`
Expected: FAIL — route missing.

- [ ] **Step 3: Implement zip mapping**

```python
# app/services/bulk_radicacion_service.py  (append)
import zipfile, re

TIPOS_VALIDOS = {"INCAPACIDAD", "HISTORIA_CLINICA", "SOPORTE", "SOPORTE_ADICIONAL"}
_NAME_RE = re.compile(r"^(?P<doc>[A-Za-z0-9]+)_(?P<tipo>[A-Z_]+)\.(?P<ext>[A-Za-z0-9]+)$")
MAX_ZIP_BYTES = 20 * 1024 * 1024


def mapear_zip(file_bytes: bytes, documentos_esperados: set[str]) -> list[dict]:
    if len(file_bytes) > MAX_ZIP_BYTES:
        raise ValueError("El ZIP excede el tamaño máximo de 20 MB")
    asignaciones = []
    with zipfile.ZipFile(io.BytesIO(file_bytes)) as z:
        for name in z.namelist():
            if name.endswith("/"):
                continue
            base = name.split("/")[-1]
            m = _NAME_RE.match(base)
            if not m:
                asignaciones.append({"archivo": base, "match": False, "motivo": "Nombre no cumple convención"})
                continue
            doc, tipo = m.group("doc"), m.group("tipo")
            ok = tipo in TIPOS_VALIDOS and doc in documentos_esperados
            asignaciones.append({
                "archivo": base, "numero_documento": doc, "tipo": tipo,
                "match": ok, "motivo": None if ok else "Documento o tipo no reconocido",
            })
    return asignaciones
```

Endpoint:

```python
@router.post("/radicar-masiva/zip", summary="Mapear ZIP de documentos (EMPRESA)")
async def mapear_zip_masivo(archivo: UploadFile = File(...), documentos_esperados: str = Form(""),
                            db: AsyncSession = Depends(get_db), current_user: Usuario = Depends(require_empresa)):
    from app.services.bulk_radicacion_service import mapear_zip
    content = await archivo.read()
    esperados = {d.strip() for d in documentos_esperados.split(",") if d.strip()}
    try:
        asignaciones = mapear_zip(content, esperados)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"asignaciones": asignaciones}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `docker exec incapacidades-api python -m pytest tests/test_bulk_zip.py -v --no-cov`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/backend/app/services/bulk_radicacion_service.py apps/backend/app/api/v1/endpoints/incapacidades.py apps/backend/tests/test_bulk_zip.py
git commit -m "feat(masiva): add ZIP filename mapping endpoint"
```

---

## Task 7: Backend — bulk submit (multipart, reuses pipeline)

**Files:**
- Modify: `app/api/v1/endpoints/incapacidades.py` — `POST /radicar-masiva`
- Test: `tests/test_bulk_submit.py`

> Accepts a JSON `filas` payload (validated rows with `empleado_id` + fields) plus the documents
> for all rows in one multipart body, named `{empleado_id}__{TIPO}` (frontend builds these). Server
> re-validates every row server-side (never trust the client), rejects if any row is invalid, runs
> the pipeline for all rows, stores documents per row, and sends ONE summary email.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_bulk_submit.py
import io, json
import pytest


@pytest.mark.asyncio
async def test_bulk_submit_creates_all(client, empresa_user_token, empleado_de_empresa):
    eid = str(empleado_de_empresa.id)
    filas = [{
        "empleado_id": eid, "tipo_enfermedad": "ACCIDENTE_TRABAJO",
        "fecha_inicio": "2026-06-01", "fecha_fin": "2026-06-05", "dias_totales": 5,
        "diagnostico_cie10": "S00.0", "nombre_medico": "Dr X", "registro_medico": "RM-1", "prorroga": False,
    }]
    files = [("documentos", (f"{eid}__INCAPACIDAD.pdf", io.BytesIO(b"%PDF"), "application/pdf"))]
    resp = await client.post("/api/v1/incapacidades/radicar-masiva",
        data={"filas": json.dumps(filas)}, files=files,
        headers={"Authorization": f"Bearer {empresa_user_token}"})
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["total_radicadas"] == 1
    assert body["items"][0]["numero"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `docker exec incapacidades-api python -m pytest tests/test_bulk_submit.py -v --no-cov`
Expected: FAIL — route missing.

- [ ] **Step 3: Implement the submit endpoint**

```python
@router.post("/radicar-masiva", response_model=RadicacionResponse, status_code=status.HTTP_201_CREATED,
             summary="Radicar incapacidades masivas (EMPRESA)")
async def radicar_masiva(
    filas: str = Form(...),  # JSON array of validated rows
    documentos: list[UploadFile] = File(default=[]),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(require_empresa),
):
    import json
    from app.services.incapacidad_validation_rules import validate_row
    from app.services.integracion.integracion_service import IntegracionService

    raw_rows = json.loads(filas)
    # Server-side re-validation: reject the whole batch if any row is invalid.
    parsed_rows = []
    for r in raw_rows:
        row_dict = {**r, "tipo": "ARL",
                    "empleado_numero_documento": r.get("empleado_id"),  # presence only
                    "fecha_inicio": date.fromisoformat(r["fecha_inicio"]),
                    "fecha_fin": date.fromisoformat(r["fecha_fin"])}
        issues = validate_row(row_dict)
        if issues:
            raise HTTPException(status_code=422, detail={"fila": r.get("empleado_id"), "errores": issues})
        parsed_rows.append(RadicacionRowInput(
            empleado_id=r["empleado_id"], tipo_enfermedad=r["tipo_enfermedad"],
            fecha_inicio=row_dict["fecha_inicio"], fecha_fin=row_dict["fecha_fin"],
            dias_totales=r["dias_totales"], diagnostico_cie10=r["diagnostico_cie10"],
            descripcion_diagnostico=r.get("descripcion_diagnostico"),
            nombre_medico=r["nombre_medico"], registro_medico=r["registro_medico"],
            ips=r.get("ips"), valor_dia=r.get("valor_dia"), prorroga=bool(r.get("prorroga")),
            observaciones=r.get("observaciones"),
        ))

    integracion = IntegracionService(db)
    pipeline = RadicacionPipelineService(db, enqueue_auditoria=enqueue_auditoria_incapacidad, integracion=integracion.procesar)
    result = await pipeline.radicar(parsed_rows, empresa=current_user.empresa, radicado_por_id=current_user.id)

    # Map documents (named "{empleado_id}__{TIPO}") to their created incapacidad and store.
    by_empleado = {str(i.empleado_id): i for i in result.items if i.success}
    archivos_por_inc: dict = {}
    for f in documentos:
        try:
            empleado_id, tipo = f.filename.split("__", 1)
            tipo = tipo.rsplit(".", 1)[0]
        except ValueError:
            continue
        item = by_empleado.get(empleado_id)
        if item:
            archivos_por_inc.setdefault(item.incapacidad_id, []).append((tipo, await f.read(), f.filename))
    for inc_id, archivos in archivos_por_inc.items():
        await _almacenar_documentos_bulk(db, inc_id, archivos, current_user.id)
    await db.commit()

    if result.total_radicadas:
        from app.tasks.email_tasks import enviar_resumen_radicacion
        enviar_resumen_radicacion.delay(
            destinatario=current_user.empresa.email_contacto,
            numeros=[i.numero for i in result.items if i.success],
        )
    return result
```

Add the bulk document helper (reuse the real document service like Phase 2's `_almacenar_documentos`):

```python
async def _almacenar_documentos_bulk(db, incapacidad_id, archivos, uploaded_by_id):
    from app.services.documento_service import DocumentoService
    svc = DocumentoService(db)
    for tipo, content, filename in archivos:
        await svc.guardar_documento(incapacidad_id=incapacidad_id, tipo=tipo,
                                    filename=filename, content=content, uploaded_by_id=uploaded_by_id)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `docker exec incapacidades-api python -m pytest tests/test_bulk_submit.py -v --no-cov`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/backend/app/api/v1/endpoints/incapacidades.py apps/backend/tests/test_bulk_submit.py
git commit -m "feat(masiva): add bulk submit endpoint reusing shared pipeline"
```

---

## Task 8: Frontend — bulk service

**Files:**
- Create: `apps/frontend/portal-externo/src/services/bulkRadicacionService.ts`

- [ ] **Step 1: Create the service**

```typescript
// src/services/bulkRadicacionService.ts
import api from '@/lib/api';

export interface ValidacionFila {
  fila: number;
  empleado_id: string | null;
  datos: Record<string, any>;
  errores: { codigo: string; descripcion: string; campo_afectado?: string; severidad: string }[];
  valida: boolean;
}

export async function descargarPlantilla(empleadoIds: string[]): Promise<Blob> {
  const { data } = await api.post('/incapacidades/radicar-masiva/plantilla',
    { empleado_ids: empleadoIds }, { responseType: 'blob' });
  return data;
}

export async function validarExcel(file: File): Promise<{ filas: ValidacionFila[]; total: number; validas: number }> {
  const fd = new FormData(); fd.append('archivo', file);
  const { data } = await api.post('/incapacidades/radicar-masiva/validar', fd,
    { headers: { 'Content-Type': 'multipart/form-data' } });
  return data;
}

export async function mapearZip(file: File, documentos: string[]) {
  const fd = new FormData(); fd.append('archivo', file); fd.append('documentos_esperados', documentos.join(','));
  const { data } = await api.post('/incapacidades/radicar-masiva/zip', fd,
    { headers: { 'Content-Type': 'multipart/form-data' } });
  return data as { asignaciones: { archivo: string; numero_documento?: string; tipo?: string; match: boolean; motivo?: string }[] };
}

export async function radicarMasiva(filas: any[], documentos: { name: string; file: File }[]) {
  const fd = new FormData();
  fd.append('filas', JSON.stringify(filas));
  documentos.forEach((d) => fd.append('documentos', d.file, d.name));
  const { data } = await api.post('/incapacidades/radicar-masiva', fd,
    { headers: { 'Content-Type': 'multipart/form-data' } });
  return data as { total_radicadas: number; items: { empleado_id: string; numero?: string; success: boolean; error?: string }[] };
}
```

- [ ] **Step 2: Commit**

```bash
git add src/services/bulkRadicacionService.ts
git commit -m "feat(masiva): add bulk radicacion service client"
```

---

## Task 9: Frontend — employee selection modal (template)

**Files:**
- Create: `src/components/radicacion/masiva/SeleccionEmpleadosModal.tsx`
- Test: `src/components/radicacion/masiva/__tests__/SeleccionEmpleadosModal.test.tsx`

- [ ] **Step 1: Write the failing test**

```tsx
// __tests__/SeleccionEmpleadosModal.test.tsx
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { SeleccionEmpleadosModal } from '@/components/radicacion/masiva/SeleccionEmpleadosModal';

vi.mock('@/services/empresaEmpleadoService', () => ({
  useEmpleadosDeMiEmpresa: () => ({ data: [
    { id: 'e1', numero_documento: '1', nombres: 'Ana', apellidos: 'G' },
    { id: 'e2', numero_documento: '2', nombres: 'Beto', apellidos: 'L' },
  ], isLoading: false }),
}));

describe('SeleccionEmpleadosModal', () => {
  it('downloads with selected employees', () => {
    const onDownload = vi.fn();
    render(<SeleccionEmpleadosModal open onClose={() => {}} onDownload={onDownload} />);
    fireEvent.click(screen.getByLabelText(/seleccionar Ana G/i));
    fireEvent.click(screen.getByRole('button', { name: /descargar/i }));
    expect(onDownload).toHaveBeenCalledWith(['e1']);
  });

  it('allows header-only download with no selection', () => {
    const onDownload = vi.fn();
    render(<SeleccionEmpleadosModal open onClose={() => {}} onDownload={onDownload} />);
    fireEvent.click(screen.getByRole('button', { name: /descargar/i }));
    expect(onDownload).toHaveBeenCalledWith([]);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- SeleccionEmpleadosModal`
Expected: FAIL — component not found.

- [ ] **Step 3: Implement the modal**

```tsx
// src/components/radicacion/masiva/SeleccionEmpleadosModal.tsx
import { useState } from 'react';
import { useEmpleadosDeMiEmpresa } from '@/services/empresaEmpleadoService';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';

interface Props { open: boolean; onClose: () => void; onDownload: (ids: string[]) => void; }

export function SeleccionEmpleadosModal({ open, onClose, onDownload }: Props) {
  const [search, setSearch] = useState('');
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const { data: empleados = [], isLoading } = useEmpleadosDeMiEmpresa(search);
  if (!open) return null;

  const toggle = (id: string) =>
    setSelected((prev) => { const n = new Set(prev); n.has(id) ? n.delete(id) : n.add(id); return n; });

  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[80vh] flex flex-col">
        <div className="p-4 border-b border-border">
          <h2 className="text-lg font-bold text-foreground">Seleccionar empleados para la plantilla</h2>
          <p className="text-sm text-muted-foreground">Sin selección, la plantilla se descarga solo con encabezados.</p>
        </div>
        <div className="p-4">
          <Input placeholder="Buscar…" value={search} onChange={(e) => setSearch(e.target.value)} />
        </div>
        <ul className="flex-1 overflow-auto px-4 divide-y">
          {isLoading && <li className="py-2 text-sm text-muted-foreground">Cargando…</li>}
          {empleados.map((e) => (
            <li key={e.id} className="py-2 flex items-center gap-2">
              <input type="checkbox" aria-label={`Seleccionar ${e.nombres} ${e.apellidos}`}
                checked={selected.has(e.id)} onChange={() => toggle(e.id)} />
              <span className="text-sm">{e.nombres} {e.apellidos} — {e.numero_documento}</span>
            </li>
          ))}
        </ul>
        <div className="p-4 border-t border-border flex justify-end gap-3">
          <Button variant="outline" onClick={onClose}>Cancelar</Button>
          <Button onClick={() => onDownload([...selected])}>Descargar plantilla</Button>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm test -- SeleccionEmpleadosModal`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/components/radicacion/masiva/SeleccionEmpleadosModal.tsx src/components/radicacion/masiva/__tests__/SeleccionEmpleadosModal.test.tsx
git commit -m "feat(masiva): add employee-selection modal for template download"
```

---

## Task 10: Frontend — validation table with per-row docs + delete

**Files:**
- Create: `src/components/radicacion/masiva/TablaValidacion.tsx`
- Test: `src/components/radicacion/masiva/__tests__/TablaValidacion.test.tsx`

> Renders one row per `ValidacionFila`. Invalid rows: list ALL errors. Valid rows: render
> file slots for `INCAPACIDAD`, `HISTORIA_CLINICA`, `SOPORTE`. Every row has a delete button.
> Document state is lifted to the parent page (Task 12) via callbacks.

- [ ] **Step 1: Write the failing test**

```tsx
// __tests__/TablaValidacion.test.tsx
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { TablaValidacion } from '@/components/radicacion/masiva/TablaValidacion';

const filas = [
  { fila: 2, empleado_id: 'e1', datos: { numero_documento: '1' }, errores: [], valida: true },
  { fila: 3, empleado_id: null, datos: { numero_documento: '2' },
    errores: [
      { codigo: 'INVALID_DATE_RANGE', descripcion: 'Fechas invertidas', severidad: 'ERROR' },
      { codigo: 'EMPTY_DIAGNOSTICO_CIE10', descripcion: 'CIE-10 requerido', severidad: 'ERROR' },
    ], valida: false },
];

describe('TablaValidacion', () => {
  it('shows all errors for an invalid row and slots for a valid one', () => {
    render(<TablaValidacion filas={filas as any} documentos={{}} onAddDoc={vi.fn()} onDelete={vi.fn()} />);
    expect(screen.getByText(/Fechas invertidas/)).toBeInTheDocument();
    expect(screen.getByText(/CIE-10 requerido/)).toBeInTheDocument();
    expect(screen.getByText(/INCAPACIDAD/)).toBeInTheDocument(); // slot label on valid row
  });

  it('calls onDelete when a row is removed', () => {
    const onDelete = vi.fn();
    render(<TablaValidacion filas={filas as any} documentos={{}} onAddDoc={vi.fn()} onDelete={onDelete} />);
    fireEvent.click(screen.getAllByRole('button', { name: /eliminar fila/i })[0]);
    expect(onDelete).toHaveBeenCalledWith(2);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- TablaValidacion`
Expected: FAIL — component not found.

- [ ] **Step 3: Implement the table**

```tsx
// src/components/radicacion/masiva/TablaValidacion.tsx
import { Trash2 } from 'lucide-react';
import type { ValidacionFila } from '@/services/bulkRadicacionService';
import { FileUpload } from '@/components/ui/FileUpload';

const SLOTS = ['INCAPACIDAD', 'HISTORIA_CLINICA', 'SOPORTE'] as const;
export type DocMap = Record<string, Partial<Record<(typeof SLOTS)[number], File>>>; // key: empleado_id

interface Props {
  filas: ValidacionFila[];
  documentos: DocMap;
  onAddDoc: (empleadoId: string, tipo: string, file: File) => void;
  onDelete: (fila: number) => void;
  /** Filas que bloquean el envío (validación o documento faltante). Cuando se intenta enviar
   *  inválido, el padre llena este set para resaltar visualmente cada fila bloqueante. */
  blocking?: Set<number>;
}

export function TablaValidacion({ filas, documentos, onAddDoc, onDelete, blocking }: Props) {
  return (
    <div className="space-y-3">
      {filas.map((f) => {
        const isBlocking = blocking?.has(f.fila) ?? false;
        return (
        <div key={f.fila} id={`fila-${f.fila}`}
          className={`rounded-lg border p-4 transition-shadow ${f.valida && !isBlocking ? 'border-border' : 'border-[#D92D20]'} ${isBlocking ? 'ring-2 ring-[#D92D20] bg-[#D92D20]/5' : ''}`}>
          <div className="flex items-start justify-between">
            <div>
              <p className="font-medium text-foreground">Documento: {f.datos.numero_documento}</p>
              {!f.valida && (
                <ul className="mt-2 list-disc pl-5 text-sm text-[#D92D20]">
                  {f.errores.map((e, i) => <li key={i}>{e.descripcion}</li>)}
                </ul>
              )}
            </div>
            <button type="button" aria-label="Eliminar fila" onClick={() => onDelete(f.fila)}
              className="text-muted-foreground hover:text-[#D92D20]"><Trash2 className="h-4 w-4" /></button>
          </div>
          {f.valida && f.empleado_id && (
            <div className="mt-3 grid gap-3 sm:grid-cols-3">
              {SLOTS.map((tipo) => (
                <div key={tipo}>
                  <p className="text-xs font-medium text-foreground mb-1">
                    {tipo}{documentos[f.empleado_id!]?.[tipo] ? ' ✓' : ''}
                  </p>
                  <FileUpload multiple={false} maxFiles={1}
                    onFileSelect={(files) => files[0] && onAddDoc(f.empleado_id!, tipo, files[0])} />
                </div>
              ))}
            </div>
          )}
        </div>
        );
      })}
    </div>
  );
}
```

> Each row carries `id="fila-{N}"` so the page can scroll to the first blocking row, and accepts a
> `blocking` set to apply the red ring/background to every blocking row at once.

- [ ] **Step 4: Run test to verify it passes**

Run: `npm test -- TablaValidacion`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/components/radicacion/masiva/TablaValidacion.tsx src/components/radicacion/masiva/__tests__/TablaValidacion.test.tsx
git commit -m "feat(masiva): add validation results table with per-row document slots"
```

---

## Task 11: Frontend — global ZIP upload component

**Files:**
- Create: `src/components/radicacion/masiva/ZipUpload.tsx`
- Test: `src/components/radicacion/masiva/__tests__/ZipUpload.test.tsx`

- [ ] **Step 1: Write the failing test**

```tsx
// __tests__/ZipUpload.test.tsx
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ZipUpload } from '@/components/radicacion/masiva/ZipUpload';

describe('ZipUpload', () => {
  it('rejects a ZIP over 20MB', () => {
    const onZip = vi.fn();
    render(<ZipUpload onZipSelected={onZip} />);
    const big = new File([new Uint8Array(21 * 1024 * 1024)], 'big.zip', { type: 'application/zip' });
    fireEvent.change(screen.getByLabelText(/zip/i), { target: { files: [big] } });
    expect(screen.getByText(/20 MB/)).toBeInTheDocument();
    expect(onZip).not.toHaveBeenCalled();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- ZipUpload`
Expected: FAIL — component not found.

- [ ] **Step 3: Implement ZipUpload**

```tsx
// src/components/radicacion/masiva/ZipUpload.tsx
import { useState } from 'react';

const MAX = 20 * 1024 * 1024;

export function ZipUpload({ onZipSelected }: { onZipSelected: (file: File) => void }) {
  const [error, setError] = useState<string | null>(null);
  return (
    <div className="rounded-lg border border-dashed border-input p-4">
      <label htmlFor="zip-input" className="block text-sm font-medium text-foreground mb-2">
        Cargar ZIP de documentos (máx 20 MB) — nombres: {'{documento}_{TIPO}.ext'}
      </label>
      <input id="zip-input" type="file" accept=".zip" aria-label="zip"
        onChange={(e) => {
          const f = e.target.files?.[0]; if (!f) return;
          if (f.size > MAX) { setError('El ZIP excede el máximo de 20 MB'); return; }
          setError(null); onZipSelected(f);
        }} />
      {error && <p className="text-sm text-[#D92D20] mt-2">{error}</p>}
    </div>
  );
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm test -- ZipUpload`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/components/radicacion/masiva/ZipUpload.tsx src/components/radicacion/masiva/__tests__/ZipUpload.test.tsx
git commit -m "feat(masiva): add global ZIP upload component with 20MB guard"
```

---

## Task 12: Frontend — masiva page (orchestration + gated submit) + route

**Files:**
- Create: `src/components/radicacion/masiva/RadicacionMasivaPage.tsx`
- Modify: `src/App.tsx`
- Test: `src/components/radicacion/masiva/__tests__/RadicacionMasivaPage.test.tsx`

> Orchestrates: template modal → validate upload → table + per-row/ZIP docs → gated submit.
> Submit is enabled only when every kept row is valid AND has at least the `INCAPACIDAD` doc.
> Clicking while disabled shows a summary of blocking rows.

- [ ] **Step 1: Write the failing test (gating summary)**

```tsx
// __tests__/RadicacionMasivaPage.test.tsx
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { RadicacionMasivaPage } from '@/components/radicacion/masiva/RadicacionMasivaPage';

vi.mock('@/services/empresaEmpleadoService', () => ({ useEmpleadosDeMiEmpresa: () => ({ data: [], isLoading: false }) }));

const wrap = () => render(
  <QueryClientProvider client={new QueryClient()}>
    <MemoryRouter><RadicacionMasivaPage /></MemoryRouter>
  </QueryClientProvider>,
);

describe('RadicacionMasivaPage', () => {
  it('renders the template download and no submit button before any rows are loaded', () => {
    wrap();
    expect(screen.getByRole('button', { name: /descargar plantilla/i })).toBeInTheDocument();
    // Submit only appears after an Excel is validated (filas.length > 0).
    expect(screen.queryByRole('button', { name: /radicar incapacidades/i })).not.toBeInTheDocument();
  });
});
```

> **Add a second test** that seeds `filas` with one blocking row (mock `validarExcel` to return an
> invalid row, trigger the upload, then click "Radicar Incapacidades") and asserts: the summary banner
> appears (`getByRole('alert')`), it names the blocking count, and the blocking row gets the highlight
> ring. Because the submit button is `aria-disabled` (not HTML `disabled`), the click reaches
> `onSubmitClick`. Example assertion after an invalid click:
>
> ```tsx
> fireEvent.click(screen.getByRole('button', { name: /radicar incapacidades/i }));
> expect(screen.getByRole('alert')).toHaveTextContent(/impiden radicar/i);
> ```
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- RadicacionMasivaPage`
Expected: FAIL — component not found.

- [ ] **Step 3: Implement the page**

```tsx
// src/components/radicacion/masiva/RadicacionMasivaPage.tsx
import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { SeleccionEmpleadosModal } from './SeleccionEmpleadosModal';
import { TablaValidacion, type DocMap } from './TablaValidacion';
import { ZipUpload } from './ZipUpload';
import { Button } from '@/components/ui/Button';
import { useToast } from '@/hooks/use-toast';
import {
  descargarPlantilla, validarExcel, mapearZip, radicarMasiva, type ValidacionFila,
} from '@/services/bulkRadicacionService';

export function RadicacionMasivaPage() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [modalOpen, setModalOpen] = useState(false);
  const [filas, setFilas] = useState<ValidacionFila[]>([]);
  const [documentos, setDocumentos] = useState<DocMap>({});
  const [submitting, setSubmitting] = useState(false);

  const handleDownload = async (ids: string[]) => {
    const blob = await descargarPlantilla(ids);
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a'); a.href = url; a.download = 'plantilla_incapacidades.xlsx'; a.click();
    URL.revokeObjectURL(url); setModalOpen(false);
  };

  const handleExcel = async (file: File) => {
    const res = await validarExcel(file);
    setFilas(res.filas);
  };

  const handleZip = async (file: File) => {
    const docs = filas.map((f) => f.datos.numero_documento).filter(Boolean);
    const res = await mapearZip(file, docs);
    toast({ title: 'ZIP procesado', description: `${res.asignaciones.filter((a) => a.match).length} documentos reconocidos` });
    // Re-fetch the real File objects: the frontend keeps the uploaded zip; for matched entries we
    // extract bytes client-side with the same {doc}_{TIPO} convention and place them into `documentos`.
    // Implementation detail: use a zip reader (e.g. fflate) to read entries and map to empleado_id by numero_documento.
  };

  const addDoc = (empleadoId: string, tipo: string, file: File) =>
    setDocumentos((p) => ({ ...p, [empleadoId]: { ...p[empleadoId], [tipo]: file } }));

  const deleteRow = (fila: number) => setFilas((p) => p.filter((f) => f.fila !== fila));

  const [mostrarBloqueos, setMostrarBloqueos] = useState(false);

  const blocking = useMemo(() => filas.filter((f) =>
    !f.valida || !f.empleado_id || !documentos[f.empleado_id]?.['INCAPACIDAD']), [filas, documentos]);
  const blockingSet = useMemo(() => new Set(blocking.map((f) => f.fila)), [blocking]);
  const canSubmit = filas.length > 0 && blocking.length === 0;

  /** Motivos de bloqueo por fila, para el banner resumen. */
  const motivosBloqueo = useMemo(() => blocking.map((f) => {
    const razones: string[] = [];
    if (!f.valida) razones.push(`${f.errores.length} error(es) de validación`);
    if (f.valida && f.empleado_id && !documentos[f.empleado_id]?.['INCAPACIDAD']) razones.push('falta documento INCAPACIDAD');
    if (!f.empleado_id) razones.push('empleado no reconocido');
    return { fila: f.fila, doc: f.datos.numero_documento, razones };
  }), [blocking, documentos]);

  const onSubmitClick = async () => {
    if (!canSubmit) {
      // (1) banner resumen, (2) resaltar todas las filas bloqueantes, (3) scroll a la primera.
      setMostrarBloqueos(true);
      const primera = blocking[0];
      if (primera) {
        document.getElementById(`fila-${primera.fila}`)?.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
      return;
    }
    setMostrarBloqueos(false);
    setSubmitting(true);
    try {
      const payload = filas.map((f) => ({ empleado_id: f.empleado_id, ...f.datos }));
      const docs: { name: string; file: File }[] = [];
      filas.forEach((f) => {
        const m = documentos[f.empleado_id!] || {};
        Object.entries(m).forEach(([tipo, file]) => file && docs.push({ name: `${f.empleado_id}__${tipo}.${file.name.split('.').pop()}`, file }));
      });
      const res = await radicarMasiva(payload, docs);
      toast({ title: 'Radicación masiva completa', description: `${res.total_radicadas} incapacidades radicadas` });
      navigate('/consulta');
    } catch (e: any) {
      toast({ title: 'Error al radicar', description: e?.response?.data?.detail ? JSON.stringify(e.response.data.detail) : 'Intente nuevamente', variant: 'destructive' });
    } finally { setSubmitting(false); }
  };

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-6">
      <h1 className="text-2xl font-bold text-foreground">Radicación Masiva</h1>
      <div className="flex flex-wrap gap-3">
        <Button onClick={() => setModalOpen(true)}>Descargar plantilla</Button>
        <label className="inline-flex items-center px-4 py-2 rounded-md border border-input cursor-pointer text-sm">
          Subir Excel diligenciado
          <input type="file" accept=".xlsx" className="hidden"
            onChange={(e) => e.target.files?.[0] && handleExcel(e.target.files[0])} />
        </label>
      </div>

      {filas.length > 0 && (
        <>
          {mostrarBloqueos && blocking.length > 0 && (
            <div role="alert" className="rounded-lg border border-[#D92D20] bg-[#D92D20]/5 p-4">
              <p className="font-bold text-[#D92D20]">
                {blocking.length} fila(s) impiden radicar. Corrija lo siguiente:
              </p>
              <ul className="mt-2 list-disc pl-5 text-sm text-[#D92D20]">
                {motivosBloqueo.map((m) => (
                  <li key={m.fila}>
                    <button type="button" className="underline"
                      onClick={() => document.getElementById(`fila-${m.fila}`)?.scrollIntoView({ behavior: 'smooth', block: 'center' })}>
                      Documento {m.doc} (fila {m.fila})
                    </button>: {m.razones.join(', ')}
                  </li>
                ))}
              </ul>
            </div>
          )}
          <ZipUpload onZipSelected={handleZip} />
          <TablaValidacion filas={filas} documentos={documentos} onAddDoc={addDoc} onDelete={deleteRow}
            blocking={mostrarBloqueos ? blockingSet : undefined} />
          <div className="flex items-center justify-between border-t border-border pt-4">
            <p className="text-sm text-muted-foreground">
              {filas.length - blocking.length}/{filas.length} listas para radicar.
            </p>
            {/* Clickable-but-styled-disabled: keep the click reaching onSubmitClick so an invalid
                attempt triggers the banner + scroll + highlight. NOT the HTML `disabled` attribute. */}
            <Button onClick={onSubmitClick} aria-disabled={!canSubmit || submitting}
              className={!canSubmit || submitting ? 'opacity-50 cursor-not-allowed' : ''}>
              {submitting ? 'Radicando…' : 'Radicar Incapacidades'}
            </Button>
          </div>
        </>
      )}

      <SeleccionEmpleadosModal open={modalOpen} onClose={() => setModalOpen(false)} onDownload={handleDownload} />
    </div>
  );
}
```

> **ZIP client-side extraction:** to place ZIP file bytes into the per-row `documentos` map, add a
> client zip reader. Use `fflate` (`npm i fflate`): unzip entries, parse `{doc}_{TIPO}.ext`, find the
> matching `fila.empleado_id` by `numero_documento`, and call `addDoc`. Keep the server `/zip` endpoint
> as the source of truth for *which* names are valid; the client reader only materializes Files for upload.

> **Blocking-submit behavior (spec 3.4, refined):** the submit button is **clickable-but-styled-disabled**
> (`aria-disabled` + reduced opacity, NOT the HTML `disabled` attribute), so an invalid click still reaches
> `onSubmitClick`. On an invalid click it must: **(1)** show a summary banner at the top of the table
> listing how many rows block submission and why (with deep-links that scroll to each), **(2)** highlight
> every blocking row at once (red ring/background via the `blocking` set passed to `TablaValidacion`), and
> **(3)** smooth-scroll to the first blocking row. Once all rows are valid + have the `INCAPACIDAD` document,
> `canSubmit` is true and the click submits.

- [ ] **Step 4: Add the route**

```tsx
// src/App.tsx — inside <ProtectedRoute />
import { RadicacionMasivaPage } from '@/components/radicacion/masiva/RadicacionMasivaPage';
<Route path="/radicar/masiva" element={<RadicacionMasivaPage />} />
```

- [ ] **Step 5: Run tests + build**

Run: `npm test -- masiva && npm run build`
Expected: PASS + build OK.

- [ ] **Step 6: Commit**

```bash
git add src/components/radicacion/masiva/RadicacionMasivaPage.tsx src/App.tsx src/components/radicacion/masiva/__tests__/RadicacionMasivaPage.test.tsx
git commit -m "feat(masiva): add bulk filing page with gated submit"
```

---

## Self-Review Notes (coverage vs spec Phase 3 + 3.6)

- 3.1 template modal + headers-only/pre-filled + all fields incl. prorroga → Tasks 4, 9. ✅
- 3.2 upload+validate, skip empty, all errors per row, slots on valid rows, delete → Tasks 5, 10. ✅
- 3.3 global ZIP ≤20MB, `{doc}_{TIPO}.ext`, mapping result → Tasks 6, 11, 12. ✅
- 3.4 submit gating + summary on invalid click → Task 12. ✅
- 3.5 direct Incapacidad, internal numero, solicitante from company, audit enqueue, ONE summary email → Task 7 (reuses Phase 2 pipeline). ✅
- 3.6 ServiAlfa/Sicat stubs + communication_log + numero_radicacion_servialfa + Sicat references SA number → Tasks 1, 2. ✅

**Type consistency:** `ValidacionFila`, `DocMap`, `descargarPlantilla/validarExcel/mapearZip/radicarMasiva`,
`enqueue_auditoria_incapacidad`, `IntegracionService.procesar`, `RadicacionPipelineService(..., integracion=)`
all match Phase 2/Phase 4 definitions.

**Manual verification:** download template (empty + pre-filled), fill 2 rows (1 invalid), upload → see
all errors on the bad row + slots on the good one, delete the bad row, attach INCAPACIDAD, submit → 1
filed; check `communication_log` has SERVIALFA+SICAT rows and the Incapacidad has `numero_radicacion_servialfa`.

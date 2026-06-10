# Gestionar Incapacidad — Mejoras de Bandeja y Vista Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Añadir fallback de empleado/empresa en bandeja de pendientes, nuevo endpoint de validaciones, strip de contexto compacto en tab Auditoría, y panel de Validaciones (renombrado desde Detalle Completo).

**Architecture:** Dos cambios en el backend (repositorio + endpoint) enriquecen las respuestas existentes sin migraciones de BD. Tres nuevos componentes frontend consumen los nuevos datos. La lógica de fallback se maneja en batch para evitar N+1.

**Tech Stack:** FastAPI + SQLAlchemy async (backend), React + TypeScript + TanStack Query + Tailwind v3 + Shadcn/ui (frontend), pytest asyncio (tests backend), vitest + React Testing Library (tests frontend).

---

## Archivos a crear o modificar

| Archivo | Acción |
|---------|--------|
| `apps/backend/app/db/repositories/validation_inconsistencia_repository.py` | Modificar — agregar `get_by_incapacidad` |
| `apps/backend/app/schemas/validation_inconsistencia.py` | Modificar — agregar `ValidacionesResponse` |
| `apps/backend/app/schemas/incapacidad.py` | Modificar — agregar `EmpleadoFallback`, `EmpresaFallback`, campos a `IncapacidadPendienteResponse` |
| `apps/backend/app/api/v1/endpoints/incapacidades.py` | Modificar — fallback en pendientes + nuevo endpoint `/validaciones` |
| `apps/backend/tests/test_validation_inconsistencia_repository.py` | Crear |
| `apps/backend/tests/test_validaciones_endpoint.py` | Crear |
| `apps/frontend/sistema-interno/src/types/incapacidad.ts` | Modificar — agregar tipos fallback y validaciones |
| `apps/frontend/sistema-interno/src/services/incapacidadService.ts` | Modificar — agregar `getValidaciones` |
| `apps/frontend/sistema-interno/src/pages/incapacidades/PendientesPage.tsx` | Modificar — columna empleado/empresa con fallback |
| `apps/frontend/sistema-interno/src/components/incapacidades/IncapacidadContextStrip.tsx` | Crear |
| `apps/frontend/sistema-interno/src/components/incapacidades/ValidacionesPanel.tsx` | Crear |
| `apps/frontend/sistema-interno/src/components/incapacidades/__tests__/IncapacidadContextStrip.test.tsx` | Crear |
| `apps/frontend/sistema-interno/src/components/incapacidades/__tests__/ValidacionesPanel.test.tsx` | Crear |
| `apps/frontend/sistema-interno/src/pages/incapacidades/GestionarPage.tsx` | Modificar — fetch validaciones, strip en audit tab, renombrar tab |

---

## Task 1: `get_by_incapacidad` en el repositorio de validaciones

**Files:**
- Modify: `apps/backend/app/db/repositories/validation_inconsistencia_repository.py`
- Create: `apps/backend/tests/test_validation_inconsistencia_repository.py`

- [ ] **Step 1: Escribir el test que falla**

Crear `apps/backend/tests/test_validation_inconsistencia_repository.py`:

```python
"""
Tests para ValidationInconsistenciaRepository.get_by_incapacidad.
Verifica que retorna issues tanto por incapacidad_id directo como
via pre_incapacidad.incapacidad_id.
"""
from datetime import date, timedelta
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.validation_inconsistencia_repository import ValidationInconsistenciaRepository
from app.models.pre_incapacidad import PreIncapacidad
from app.models.incapacidad import Incapacidad
from app.models.validation_inconsistencia import ValidationInconsistencia
from app.utils.enums import TipoIncapacidad, EstadoIncapacidad, Prioridad


async def _make_incapacidad(db: AsyncSession) -> Incapacidad:
    inc = Incapacidad(
        numero=f"INC-TEST-{uuid4().hex[:8]}",
        tipo=TipoIncapacidad.ARL,
        estado=EstadoIncapacidad.EN_AUDITORIA,
        prioridad=Prioridad.NORMAL,
        fecha_inicio=date.today(),
        fecha_fin=date.today() + timedelta(days=5),
        dias_totales=6,
        fecha_radicacion=__import__('datetime').datetime.utcnow(),
    )
    db.add(inc)
    await db.flush()
    return inc


async def _make_pre_inc(db: AsyncSession, incapacidad_id=None) -> PreIncapacidad:
    pre = PreIncapacidad(
        estado="PROCESADA",
        solicitante_correo="x@x.com",
        solicitante_nombres="X",
        empleado_tipo_documento="CC",
        empleado_numero_documento="11111111",
        empleado_nombres="Test",
        tipo="ARL",
        tipo_enfermedad="ACCIDENTE_TRABAJO",
        fecha_inicio=date.today(),
        fecha_fin=date.today() + timedelta(days=5),
        dias_totales=6,
        diagnostico_cie10="M54.5",
        nombre_medico="Dr. X",
        registro_medico="REG-X",
        incapacidad_id=incapacidad_id,
    )
    db.add(pre)
    await db.flush()
    return pre


@pytest.mark.asyncio
async def test_get_by_incapacidad_direct_link(db_session: AsyncSession):
    """Issue con incapacidad_id directo debe aparecer."""
    inc = await _make_incapacidad(db_session)
    pre = await _make_pre_inc(db_session, incapacidad_id=inc.id)
    issue = ValidationInconsistencia(
        pre_incapacidad_id=pre.id,
        incapacidad_id=inc.id,
        categoria="BUSINESS_RULE",
        severidad="WARNING",
        codigo="TEST_CODE",
        descripcion="Test",
    )
    db_session.add(issue)
    await db_session.commit()

    repo = ValidationInconsistenciaRepository(db_session)
    results = await repo.get_by_incapacidad(inc.id)
    assert len(results) == 1
    assert results[0].codigo == "TEST_CODE"


@pytest.mark.asyncio
async def test_get_by_incapacidad_via_pre_incapacidad(db_session: AsyncSession):
    """Issue con solo pre_incapacidad_id debe aparecer si pre_inc apunta a la incapacidad."""
    inc = await _make_incapacidad(db_session)
    pre = await _make_pre_inc(db_session, incapacidad_id=inc.id)
    issue = ValidationInconsistencia(
        pre_incapacidad_id=pre.id,
        incapacidad_id=None,  # sin link directo
        categoria="INTEGRATION_CHECK",
        severidad="WARNING",
        codigo="EMPRESA_NOT_FOUND",
        descripcion="Empresa no encontrada",
    )
    db_session.add(issue)
    await db_session.commit()

    repo = ValidationInconsistenciaRepository(db_session)
    results = await repo.get_by_incapacidad(inc.id)
    assert len(results) == 1
    assert results[0].codigo == "EMPRESA_NOT_FOUND"


@pytest.mark.asyncio
async def test_get_by_incapacidad_excludes_other(db_session: AsyncSession):
    """Issues de otra incapacidad no deben aparecer."""
    inc_a = await _make_incapacidad(db_session)
    inc_b = await _make_incapacidad(db_session)
    pre_b = await _make_pre_inc(db_session, incapacidad_id=inc_b.id)
    issue = ValidationInconsistencia(
        pre_incapacidad_id=pre_b.id,
        incapacidad_id=inc_b.id,
        categoria="FRAUD_ALERT",
        severidad="WARNING",
        codigo="POSSIBLE_DUPLICATE",
        descripcion="Duplicado",
    )
    db_session.add(issue)
    await db_session.commit()

    repo = ValidationInconsistenciaRepository(db_session)
    results = await repo.get_by_incapacidad(inc_a.id)
    assert len(results) == 0


@pytest.mark.asyncio
async def test_get_by_incapacidad_returns_both_sources(db_session: AsyncSession):
    """Debe retornar issues tanto de incapacidad_id directo como de pre_incapacidad."""
    inc = await _make_incapacidad(db_session)
    pre = await _make_pre_inc(db_session, incapacidad_id=inc.id)

    # issue via pre_incapacidad (sin incapacidad_id)
    issue_pre = ValidationInconsistencia(
        pre_incapacidad_id=pre.id,
        incapacidad_id=None,
        categoria="INTEGRATION_CHECK",
        severidad="WARNING",
        codigo="EMPLEADO_NOT_FOUND",
        descripcion="Empleado no encontrado",
    )
    # issue con incapacidad_id directo
    issue_direct = ValidationInconsistencia(
        pre_incapacidad_id=pre.id,
        incapacidad_id=inc.id,
        categoria="BUSINESS_RULE",
        severidad="WARNING",
        codigo="OVERLAPPING_PERIOD",
        descripcion="Periodo solapado",
    )
    db_session.add_all([issue_pre, issue_direct])
    await db_session.commit()

    repo = ValidationInconsistenciaRepository(db_session)
    results = await repo.get_by_incapacidad(inc.id)
    codigos = {r.codigo for r in results}
    assert "EMPLEADO_NOT_FOUND" in codigos
    assert "OVERLAPPING_PERIOD" in codigos
```

- [ ] **Step 2: Ejecutar el test para confirmar que falla**

```bash
docker exec incapacidades-api sh -c "/home/appuser/.local/bin/pytest tests/test_validation_inconsistencia_repository.py -v --no-cov 2>&1"
```

Esperado: `FAILED` con `AttributeError: 'ValidationInconsistenciaRepository' object has no attribute 'get_by_incapacidad'`

- [ ] **Step 3: Implementar `get_by_incapacidad`**

Abrir `apps/backend/app/db/repositories/validation_inconsistencia_repository.py`.

Cambiar el import de la línea 7:

```python
from sqlalchemy import select, and_, delete, or_
```

Agregar después del método `delete_by_pre_incapacidad`:

```python
    async def get_by_incapacidad(self, incapacidad_id: UUID) -> list[ValidationInconsistencia]:
        """Retorna todos los issues de una incapacidad:
        - issues con incapacidad_id directo, O
        - issues cuya pre_incapacidad apunta a esta incapacidad."""
        from app.models.pre_incapacidad import PreIncapacidad

        subq = select(PreIncapacidad.id).where(
            PreIncapacidad.incapacidad_id == incapacidad_id
        )
        query = (
            select(ValidationInconsistencia)
            .where(
                or_(
                    ValidationInconsistencia.incapacidad_id == incapacidad_id,
                    ValidationInconsistencia.pre_incapacidad_id.in_(subq),
                )
            )
            .order_by(ValidationInconsistencia.fecha_deteccion)
        )
        result = await self.db.execute(query)
        return result.scalars().all()
```

- [ ] **Step 4: Ejecutar los tests para confirmar que pasan**

```bash
docker exec incapacidades-api sh -c "/home/appuser/.local/bin/pytest tests/test_validation_inconsistencia_repository.py -v --no-cov 2>&1"
```

Esperado: `4 passed`

- [ ] **Step 5: Commit**

```bash
git add apps/backend/app/db/repositories/validation_inconsistencia_repository.py \
        apps/backend/tests/test_validation_inconsistencia_repository.py
git commit -m "feat: add get_by_incapacidad to ValidationInconsistenciaRepository"
```

---

## Task 2: Schemas — `ValidacionesResponse`, `EmpleadoFallback`, `EmpresaFallback`

**Files:**
- Modify: `apps/backend/app/schemas/validation_inconsistencia.py`
- Modify: `apps/backend/app/schemas/incapacidad.py`

- [ ] **Step 1: Agregar `ValidacionesResponse` a validation_inconsistencia.py**

Abrir `apps/backend/app/schemas/validation_inconsistencia.py`. Agregar al final del archivo:

```python
class ValidacionesResponse(BaseModel):
    """Respuesta del endpoint GET /incapacidades/{id}/validaciones."""
    issues: list[ValidationInconsistenciaRead]
    has_errors: bool
    has_fraud_alert: bool
    total: int
```

- [ ] **Step 2: Agregar `EmpleadoFallback`, `EmpresaFallback` y campos a `IncapacidadPendienteResponse`**

Abrir `apps/backend/app/schemas/incapacidad.py`.

Localizar la clase `IncapacidadPendienteResponse` (línea ~317). Antes de esa clase, agregar los dos schemas de fallback:

```python
class EmpleadoFallback(BaseModel):
    """Datos crudos del empleado desde pre_incapacidad cuando no está en BD."""
    nombres: str
    numero_documento: str

    model_config = {"from_attributes": True}


class EmpresaFallback(BaseModel):
    """Datos crudos de la empresa desde pre_incapacidad cuando no está en BD."""
    nit: str
    nombre: str

    model_config = {"from_attributes": True}
```

Modificar `IncapacidadPendienteResponse`:

```python
class IncapacidadPendienteResponse(IncapacidadInDB):
    """
    Schema para incapacidad pendiente de auditoría con datos adicionales.
    Incluye días desde radicación, días en estado actual, y fallback de
    empleado/empresa desde pre_incapacidad cuando no existen en BD.
    """
    dias_desde_radicacion: int = Field(..., description="Días desde que fue radicada")
    dias_en_estado_actual: int = Field(..., description="Días en el estado actual")
    empleado_fallback: Optional[EmpleadoFallback] = Field(
        None, description="Datos crudos del empleado si no existe en BD"
    )
    empresa_fallback: Optional[EmpresaFallback] = Field(
        None, description="Datos crudos de la empresa si no existe en BD"
    )

    model_config = {"from_attributes": True}
```

- [ ] **Step 3: Verificar que los schemas importan sin errores**

```bash
docker exec incapacidades-api sh -c "python -c 'from app.schemas.incapacidad import IncapacidadPendienteResponse, EmpleadoFallback, EmpresaFallback; from app.schemas.validation_inconsistencia import ValidacionesResponse; print(\"OK\")' 2>&1"
```

Esperado: `OK`

- [ ] **Step 4: Commit**

```bash
git add apps/backend/app/schemas/validation_inconsistencia.py \
        apps/backend/app/schemas/incapacidad.py
git commit -m "feat: add ValidacionesResponse, EmpleadoFallback, EmpresaFallback schemas"
```

---

## Task 3: Endpoint `GET /incapacidades/{id}/validaciones`

**Files:**
- Modify: `apps/backend/app/api/v1/endpoints/incapacidades.py`
- Create: `apps/backend/tests/test_validaciones_endpoint.py`

- [ ] **Step 1: Escribir el test que falla**

Crear `apps/backend/tests/test_validaciones_endpoint.py`:

```python
"""
Tests de integración para GET /api/v1/incapacidades/{id}/validaciones.
"""
from datetime import date, timedelta
from uuid import uuid4
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.incapacidad import Incapacidad
from app.models.pre_incapacidad import PreIncapacidad
from app.models.validation_inconsistencia import ValidationInconsistencia
from app.utils.enums import TipoIncapacidad, EstadoIncapacidad, Prioridad


async def _seed_incapacidad(db: AsyncSession) -> Incapacidad:
    inc = Incapacidad(
        numero=f"INC-VAL-{uuid4().hex[:8]}",
        tipo=TipoIncapacidad.ARL,
        estado=EstadoIncapacidad.EN_AUDITORIA,
        prioridad=Prioridad.NORMAL,
        fecha_inicio=date.today(),
        fecha_fin=date.today() + timedelta(days=5),
        dias_totales=6,
        fecha_radicacion=__import__('datetime').datetime.utcnow(),
    )
    db.add(inc)
    await db.flush()
    return inc


async def _seed_pre_inc(db: AsyncSession, incapacidad_id) -> PreIncapacidad:
    pre = PreIncapacidad(
        estado="PROCESADA",
        solicitante_correo="x@x.com",
        solicitante_nombres="X",
        empleado_tipo_documento="CC",
        empleado_numero_documento="11111111",
        empleado_nombres="Test",
        tipo="ARL",
        tipo_enfermedad="ACCIDENTE_TRABAJO",
        fecha_inicio=date.today(),
        fecha_fin=date.today() + timedelta(days=5),
        dias_totales=6,
        diagnostico_cie10="M54.5",
        nombre_medico="Dr. X",
        registro_medico="REG-X",
        incapacidad_id=incapacidad_id,
    )
    db.add(pre)
    await db.flush()
    return pre


@pytest.mark.asyncio
async def test_get_validaciones_returns_issues(
    client: AsyncClient, db_session: AsyncSession
):
    """El endpoint retorna los issues asociados a la incapacidad."""
    inc = await _seed_incapacidad(db_session)
    pre = await _seed_pre_inc(db_session, inc.id)
    issue = ValidationInconsistencia(
        pre_incapacidad_id=pre.id,
        incapacidad_id=inc.id,
        categoria="INTEGRATION_CHECK",
        severidad="WARNING",
        codigo="EMPLEADO_NOT_FOUND",
        descripcion="Empleado no encontrado en BD",
    )
    db_session.add(issue)
    await db_session.commit()

    response = await client.get(f"/api/v1/incapacidades/{inc.id}/validaciones")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["has_errors"] is False
    assert data["has_fraud_alert"] is False
    assert data["issues"][0]["codigo"] == "EMPLEADO_NOT_FOUND"


@pytest.mark.asyncio
async def test_get_validaciones_has_fraud_alert(
    client: AsyncClient, db_session: AsyncSession
):
    """has_fraud_alert es True cuando hay un issue de categoría FRAUD_ALERT."""
    inc = await _seed_incapacidad(db_session)
    pre = await _seed_pre_inc(db_session, inc.id)
    issue = ValidationInconsistencia(
        pre_incapacidad_id=pre.id,
        incapacidad_id=inc.id,
        categoria="FRAUD_ALERT",
        severidad="WARNING",
        codigo="POSSIBLE_DUPLICATE",
        descripcion="Posible duplicado",
    )
    db_session.add(issue)
    await db_session.commit()

    response = await client.get(f"/api/v1/incapacidades/{inc.id}/validaciones")
    assert response.status_code == 200
    data = response.json()
    assert data["has_fraud_alert"] is True


@pytest.mark.asyncio
async def test_get_validaciones_empty_for_clean_incapacidad(
    client: AsyncClient, db_session: AsyncSession
):
    """Incapacidad sin issues retorna lista vacía y todos los flags en False."""
    inc = await _seed_incapacidad(db_session)
    await db_session.commit()

    response = await client.get(f"/api/v1/incapacidades/{inc.id}/validaciones")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["has_errors"] is False
    assert data["has_fraud_alert"] is False
    assert data["issues"] == []


@pytest.mark.asyncio
async def test_get_validaciones_includes_pre_incapacidad_issues(
    client: AsyncClient, db_session: AsyncSession
):
    """Issues con solo pre_incapacidad_id (sin incapacidad_id directo) también aparecen."""
    inc = await _seed_incapacidad(db_session)
    pre = await _seed_pre_inc(db_session, inc.id)
    issue = ValidationInconsistencia(
        pre_incapacidad_id=pre.id,
        incapacidad_id=None,
        categoria="FIELD_VALIDATION",
        severidad="INFO",
        codigo="MISSING_FIELD",
        descripcion="Campo faltante",
    )
    db_session.add(issue)
    await db_session.commit()

    response = await client.get(f"/api/v1/incapacidades/{inc.id}/validaciones")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["issues"][0]["codigo"] == "MISSING_FIELD"
```

- [ ] **Step 2: Ejecutar el test para confirmar que falla**

```bash
docker exec incapacidades-api sh -c "/home/appuser/.local/bin/pytest tests/test_validaciones_endpoint.py -v --no-cov 2>&1"
```

Esperado: `FAILED` con `404` (endpoint no existe aún)

- [ ] **Step 3: Implementar el endpoint**

Abrir `apps/backend/app/api/v1/endpoints/incapacidades.py`.

En la sección de imports, añadir:

```python
from app.db.repositories.validation_inconsistencia_repository import ValidationInconsistenciaRepository
from app.schemas.validation_inconsistencia import ValidationInconsistenciaRead, ValidacionesResponse
```

Buscar el último endpoint en el router (cerca del final del archivo). Añadir el nuevo endpoint antes del cierre del archivo:

```python
@router.get(
    "/{incapacidad_id}/validaciones",
    response_model=ValidacionesResponse,
    summary="Obtener validaciones de una incapacidad",
    description="Retorna todos los issues de validation_inconsistencia asociados a esta incapacidad, "
                "incluyendo los generados desde pre_incapacidad.",
    tags=["incapacidades-auditoria"],
)
async def get_validaciones_incapacidad(
    incapacidad_id: UUID = Path(..., description="ID de la incapacidad"),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(
        PermissionChecker([Permissions.INCAPACIDAD_READ])
    ),
) -> ValidacionesResponse:
    """
    Obtiene todos los issues de validación asociados a una incapacidad.

    Incluye issues con incapacidad_id directo Y issues cuya pre_incapacidad
    apunta a esta incapacidad (generados durante el flujo de promoción).
    """
    repo = ValidationInconsistenciaRepository(db)
    issues = await repo.get_by_incapacidad(incapacidad_id)
    issues_read = [ValidationInconsistenciaRead.model_validate(i) for i in issues]
    return ValidacionesResponse(
        issues=issues_read,
        has_errors=any(i.severidad == "ERROR" for i in issues),
        has_fraud_alert=any(i.categoria == "FRAUD_ALERT" for i in issues),
        total=len(issues),
    )
```

- [ ] **Step 4: Ejecutar los tests para confirmar que pasan**

```bash
docker exec incapacidades-api sh -c "/home/appuser/.local/bin/pytest tests/test_validaciones_endpoint.py -v --no-cov 2>&1"
```

Esperado: `4 passed`

- [ ] **Step 5: Commit**

```bash
git add apps/backend/app/api/v1/endpoints/incapacidades.py \
        apps/backend/tests/test_validaciones_endpoint.py
git commit -m "feat: add GET /incapacidades/{id}/validaciones endpoint"
```

---

## Task 4: Fallback de empleado/empresa en endpoint de pendientes

**Files:**
- Modify: `apps/backend/app/api/v1/endpoints/incapacidades.py`

- [ ] **Step 1: Escribir el test que falla**

Agregar al final de `apps/backend/tests/test_validaciones_endpoint.py`:

```python
@pytest.mark.asyncio
async def test_pendientes_includes_empleado_fallback(
    client: AsyncClient, db_session: AsyncSession
):
    """Cuando empleado_id es NULL, el response incluye empleado_fallback desde pre_incapacidad."""
    from app.models.empresa import Empresa
    from app.utils.enums import EstadoEmpresa

    inc = Incapacidad(
        numero=f"INC-FB-{uuid4().hex[:8]}",
        tipo=TipoIncapacidad.ARL,
        estado=EstadoIncapacidad.RADICADA,
        prioridad=Prioridad.NORMAL,
        fecha_inicio=date.today(),
        fecha_fin=date.today() + timedelta(days=5),
        dias_totales=6,
        fecha_radicacion=__import__('datetime').datetime.utcnow(),
        empleado_id=None,
        empresa_id=None,
    )
    db_session.add(inc)
    await db_session.flush()

    pre = PreIncapacidad(
        estado="PROCESADA",
        solicitante_correo="fb@test.com",
        solicitante_nombres="FB",
        empleado_tipo_documento="CC",
        empleado_numero_documento="99887766",
        empleado_nombres="Carlos Fallback",
        tipo="ARL",
        tipo_enfermedad="ACCIDENTE_TRABAJO",
        fecha_inicio=date.today(),
        fecha_fin=date.today() + timedelta(days=5),
        dias_totales=6,
        diagnostico_cie10="S50.0",
        nombre_medico="Dr. FB",
        registro_medico="REG-FB",
        empresa_nit="999888777",
        empresa_nombre="Empresa Fallback SAS",
        incapacidad_id=inc.id,
    )
    db_session.add(pre)
    await db_session.commit()

    response = await client.get("/api/v1/incapacidades/pendientes")
    assert response.status_code == 200
    items = response.json()
    target = next((i for i in items if i["numero"] == inc.numero), None)
    assert target is not None
    assert target["empleado_fallback"] is not None
    assert target["empleado_fallback"]["nombres"] == "Carlos Fallback"
    assert target["empleado_fallback"]["numero_documento"] == "99887766"
    assert target["empresa_fallback"] is not None
    assert target["empresa_fallback"]["nit"] == "999888777"
    assert target["empresa_fallback"]["nombre"] == "Empresa Fallback SAS"
```

- [ ] **Step 2: Ejecutar el test para confirmar que falla**

```bash
docker exec incapacidades-api sh -c "/home/appuser/.local/bin/pytest tests/test_validaciones_endpoint.py::test_pendientes_includes_empleado_fallback -v --no-cov 2>&1"
```

Esperado: `FAILED` — `empleado_fallback` es `None` en la respuesta.

- [ ] **Step 3: Implementar el batch fallback en el endpoint de pendientes**

Abrir `apps/backend/app/api/v1/endpoints/incapacidades.py`.

En la sección de imports, añadir:

```python
from sqlalchemy import select as sa_select
from app.models.pre_incapacidad import PreIncapacidad
from app.schemas.incapacidad import EmpleadoFallback, EmpresaFallback
```

Localizar la función `listar_incapacidades_pendientes`. Reemplazar el bloque de serialización (desde `result = []` hasta el `return result`) con:

```python
    # Paso 1: construir resultados base
    result = []
    ids_sin_empleado: list[UUID] = []

    for item in incapacidades:
        incap = item['incapacidad']
        incap_dict = IncapacidadInDB.model_validate(incap).model_dump()
        incap_dict['dias_desde_radicacion'] = item['dias_desde_radicacion']
        incap_dict['dias_en_estado_actual'] = item['dias_en_estado_actual']
        incap_dict['empleado_fallback'] = None
        incap_dict['empresa_fallback'] = None

        if incap.empleado:
            incap_dict['empleado'] = EmpleadoResponse.model_validate(incap.empleado).model_dump()
        if incap.empresa:
            incap_dict['empresa'] = EmpresaResponse.model_validate(incap.empresa).model_dump()
        if incap.afiliado:
            incap_dict['afiliado'] = AfiliadoResponse.model_validate(incap.afiliado).model_dump()

        if not incap.empleado_id:
            ids_sin_empleado.append(incap.id)

        result.append(incap_dict)

    # Paso 2: batch query a pre_incapacidad para fallback (un solo SELECT)
    if ids_sin_empleado:
        pre_rows = (
            await db.execute(
                sa_select(
                    PreIncapacidad.incapacidad_id,
                    PreIncapacidad.empleado_nombres,
                    PreIncapacidad.empleado_numero_documento,
                    PreIncapacidad.empresa_nit,
                    PreIncapacidad.empresa_nombre,
                ).where(PreIncapacidad.incapacidad_id.in_(ids_sin_empleado))
            )
        ).all()

        fallback_map: dict[str, dict] = {
            str(row.incapacidad_id): row for row in pre_rows
        }

        for item_dict in result:
            inc_id = str(item_dict['id'])
            if inc_id in fallback_map:
                row = fallback_map[inc_id]
                item_dict['empleado_fallback'] = EmpleadoFallback(
                    nombres=row.empleado_nombres,
                    numero_documento=row.empleado_numero_documento,
                ).model_dump()
                if row.empresa_nit:
                    item_dict['empresa_fallback'] = EmpresaFallback(
                        nit=row.empresa_nit,
                        nombre=row.empresa_nombre or row.empresa_nit,
                    ).model_dump()

    return result
```

- [ ] **Step 4: Ejecutar todos los tests del archivo**

```bash
docker exec incapacidades-api sh -c "/home/appuser/.local/bin/pytest tests/test_validaciones_endpoint.py -v --no-cov 2>&1"
```

Esperado: `5 passed`

- [ ] **Step 5: Commit**

```bash
git add apps/backend/app/api/v1/endpoints/incapacidades.py \
        apps/backend/tests/test_validaciones_endpoint.py
git commit -m "feat: add employee/company fallback from pre_incapacidad in pendientes endpoint"
```

---

## Task 5: Frontend — tipos y método de servicio

**Files:**
- Modify: `apps/frontend/sistema-interno/src/types/incapacidad.ts`
- Modify: `apps/frontend/sistema-interno/src/services/incapacidadService.ts`

- [ ] **Step 1: Agregar tipos en `incapacidad.ts`**

Abrir `apps/frontend/sistema-interno/src/types/incapacidad.ts`.

Al final del archivo, añadir:

```typescript
/**
 * Fallback de empleado desde pre_incapacidad (cuando no está en BD)
 */
export interface EmpleadoFallback {
  nombres: string;
  numero_documento: string;
}

/**
 * Fallback de empresa desde pre_incapacidad (cuando no está en BD)
 */
export interface EmpresaFallback {
  nit: string;
  nombre: string;
}

/**
 * Incapacidad Pendiente — extiende Incapacidad con campos calculados y fallbacks
 */
export interface IncapacidadPendiente extends Incapacidad {
  dias_desde_radicacion: number;
  dias_en_estado_actual: number;
  empleado_fallback?: EmpleadoFallback | null;
  empresa_fallback?: EmpresaFallback | null;
}

/**
 * Issue de validación (desde validation_inconsistencia)
 */
export interface ValidationIssue {
  id: string;
  pre_incapacidad_id: string;
  incapacidad_id: string | null;
  categoria: 'FIELD_VALIDATION' | 'BUSINESS_RULE' | 'FRAUD_ALERT' | 'INTEGRATION_CHECK';
  severidad: 'ERROR' | 'WARNING' | 'INFO';
  codigo: string;
  descripcion: string;
  campo_afectado?: string | null;
  valor_encontrado?: string | null;
  valor_esperado?: string | null;
  fecha_deteccion: string;
}

/**
 * Respuesta del endpoint GET /incapacidades/{id}/validaciones
 */
export interface ValidacionesResponse {
  issues: ValidationIssue[];
  has_errors: boolean;
  has_fraud_alert: boolean;
  total: number;
}
```

Reemplazar la interfaz `IncapacidadPendiente` existente (que ya estaba definida más arriba en el archivo) con la versión nueva. Para evitar duplicado, buscar y eliminar:

```typescript
export interface IncapacidadPendiente extends Incapacidad {
  dias_desde_radicacion: number;
  dias_en_estado_actual: number;
}
```

- [ ] **Step 2: Agregar `getValidaciones` al servicio**

Abrir `apps/frontend/sistema-interno/src/services/incapacidadService.ts`.

Actualizar el import de tipos al inicio:

```typescript
import type {
  Incapacidad,
  IncapacidadFiltros,
  IncapacidadPendiente,
  FiltrosPendientes,
  HistorialEstado,
  Documento,
  AuditoriaDatosAprobados,
  IncapacidadAuditarRequest,
  ValidacionesResponse,
} from '@/types/incapacidad';
```

Añadir el método `getValidaciones` al objeto `incapacidadService`, antes del cierre `};`:

```typescript
  /**
   * Obtener validaciones de una incapacidad
   * GET /api/v1/incapacidades/{id}/validaciones
   */
  async getValidaciones(id: string): Promise<ValidacionesResponse> {
    const { data } = await api.get<ValidacionesResponse>(
      `/incapacidades/${id}/validaciones`
    );
    return data;
  },
```

- [ ] **Step 3: Verificar tipos con TypeScript**

```bash
cd /opt/apps/incapacidades_vs/apps/frontend/sistema-interno && npx tsc --noEmit 2>&1 | head -30
```

Esperado: sin errores en los archivos modificados.

- [ ] **Step 4: Commit**

```bash
git add apps/frontend/sistema-interno/src/types/incapacidad.ts \
        apps/frontend/sistema-interno/src/services/incapacidadService.ts
git commit -m "feat: add ValidationIssue, ValidacionesResponse types and getValidaciones service method"
```

---

## Task 6: Frontend — columna empleado/empresa con fallback en PendientesPage

**Files:**
- Modify: `apps/frontend/sistema-interno/src/pages/incapacidades/PendientesPage.tsx`

- [ ] **Step 1: Actualizar la definición de columnas**

Abrir `apps/frontend/sistema-interno/src/pages/incapacidades/PendientesPage.tsx`.

Reemplazar la columna `accessorKey: 'empleado'`:

```tsx
  {
    accessorKey: 'empleado',
    header: 'Empleado / Afiliado',
    cell: ({ row }) => {
      const empleado = row.original.empleado;
      const afiliado = row.original.afiliado;
      const fallback = row.original.empleado_fallback;

      if (empleado) {
        return (
          <div>
            <p className="font-medium">
              {empleado.nombres} {empleado.apellidos}
            </p>
            <p className="text-sm text-slate-500">{empleado.numero_documento}</p>
          </div>
        );
      }

      if (afiliado) {
        return (
          <div>
            <p className="font-medium">
              {afiliado.nombres} {afiliado.apellidos}
            </p>
            <p className="text-sm text-slate-500">{afiliado.numero_documento}</p>
          </div>
        );
      }

      if (fallback) {
        return (
          <div>
            <div className="flex items-center gap-1.5">
              <p className="font-medium">{fallback.nombres}</p>
              <span className="text-xs bg-slate-100 text-slate-500 border border-slate-200 rounded px-1 py-0.5 leading-none">
                Sin ficha
              </span>
            </div>
            <p className="text-sm text-slate-500">{fallback.numero_documento}</p>
          </div>
        );
      }

      return <span className="text-slate-400">—</span>;
    },
  },
```

Reemplazar la columna `accessorKey: 'empresa'`:

```tsx
  {
    accessorKey: 'empresa',
    header: 'Empresa',
    cell: ({ row }) => {
      const empresa = row.original.empresa;
      const fallback = row.original.empresa_fallback;

      if (empresa) {
        return (
          <div>
            <p className="font-medium">{empresa.razon_social}</p>
            <p className="text-sm text-slate-500">NIT: {empresa.nit}</p>
          </div>
        );
      }

      if (fallback) {
        return (
          <div>
            <div className="flex items-center gap-1.5">
              <p className="font-medium">{fallback.nombre}</p>
              <span className="text-xs bg-slate-100 text-slate-500 border border-slate-200 rounded px-1 py-0.5 leading-none">
                Sin ficha
              </span>
            </div>
            <p className="text-sm text-slate-500">NIT: {fallback.nit}</p>
          </div>
        );
      }

      return <span className="text-slate-500">Afiliado</span>;
    },
  },
```

- [ ] **Step 2: Verificar TypeScript**

```bash
cd /opt/apps/incapacidades_vs/apps/frontend/sistema-interno && npx tsc --noEmit 2>&1 | head -20
```

Esperado: sin errores.

- [ ] **Step 3: Commit**

```bash
git add apps/frontend/sistema-interno/src/pages/incapacidades/PendientesPage.tsx
git commit -m "feat: show empleado_fallback and empresa_fallback in pendientes table"
```

---

## Task 7: Frontend — componente `IncapacidadContextStrip`

**Files:**
- Create: `apps/frontend/sistema-interno/src/components/incapacidades/IncapacidadContextStrip.tsx`
- Create: `apps/frontend/sistema-interno/src/components/incapacidades/__tests__/IncapacidadContextStrip.test.tsx`

- [ ] **Step 1: Escribir el test que falla**

Crear `apps/frontend/sistema-interno/src/components/incapacidades/__tests__/IncapacidadContextStrip.test.tsx`:

```tsx
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { IncapacidadContextStrip } from '../IncapacidadContextStrip';
import { TipoIncapacidad, EstadoIncapacidad } from '@/types';

const baseIncapacidad = {
  id: 'inc-1',
  numero: 'INC-001',
  tipo: TipoIncapacidad.ARL,
  estado: EstadoIncapacidad.EN_AUDITORIA,
  prioridad: 'NORMAL',
  fecha_inicio: '2026-06-01',
  fecha_fin: '2026-06-07',
  dias_totales: 7,
  diagnostico_cie10: 'M54.5',
  diagnostico_descripcion: 'Lumbalgia',
  valor_total: 350000,
  created_at: '2026-06-01T10:00:00Z',
  updated_at: '2026-06-01T10:00:00Z',
  empleado: {
    id: 'emp-1',
    tipo_documento: 'CEDULA',
    numero_documento: '12345678',
    nombres: 'Pedro',
    apellidos: 'Promo',
    empresa_id: 'emp-co-1',
  },
  empresa: {
    id: 'co-1',
    nit: '901000999',
    razon_social: 'Empresa Test SAS',
    email_contacto: 'test@empresa.com',
  },
};

describe('IncapacidadContextStrip', () => {
  it('muestra el nombre y documento del empleado', () => {
    render(
      <IncapacidadContextStrip
        incapacidad={baseIncapacidad as any}
        hasFraudAlert={false}
      />
    );
    expect(screen.getByText(/Pedro Promo/)).toBeInTheDocument();
    expect(screen.getByText(/12345678/)).toBeInTheDocument();
  });

  it('muestra CIE-10 y rango de fechas', () => {
    render(
      <IncapacidadContextStrip
        incapacidad={baseIncapacidad as any}
        hasFraudAlert={false}
      />
    );
    expect(screen.getByText(/M54\.5/)).toBeInTheDocument();
    expect(screen.getByText(/7 días/)).toBeInTheDocument();
  });

  it('muestra badge Sin ficha y aplica estilo ámbar cuando no hay empleado en BD', () => {
    const sinEmpleado = {
      ...baseIncapacidad,
      empleado: undefined,
      empleado_fallback: { nombres: 'Luis Fallback', numero_documento: '99887766' },
    };
    render(
      <IncapacidadContextStrip
        incapacidad={sinEmpleado as any}
        hasFraudAlert={false}
        empleadoFallback={{ nombres: 'Luis Fallback', numero_documento: '99887766' }}
      />
    );
    expect(screen.getByText(/Luis Fallback/)).toBeInTheDocument();
    expect(screen.getByText('Sin ficha')).toBeInTheDocument();
  });

  it('aplica clase de alerta roja cuando hasFraudAlert es true', () => {
    const { container } = render(
      <IncapacidadContextStrip
        incapacidad={{ ...baseIncapacidad, empleado: undefined } as any}
        hasFraudAlert={true}
        empleadoFallback={{ nombres: 'Luis', numero_documento: '99887766' }}
      />
    );
    const empleadoSection = container.querySelector('[data-testid="empleado-section"]');
    expect(empleadoSection?.className).toMatch(/red/);
  });
});
```

- [ ] **Step 2: Ejecutar el test para confirmar que falla**

```bash
cd /opt/apps/incapacidades_vs/apps/frontend/sistema-interno && npx vitest run src/components/incapacidades/__tests__/IncapacidadContextStrip.test.tsx --reporter=verbose 2>&1 | tail -20
```

Esperado: error de módulo no encontrado.

- [ ] **Step 3: Crear el componente**

Crear `apps/frontend/sistema-interno/src/components/incapacidades/IncapacidadContextStrip.tsx`:

```tsx
import { AlertTriangle } from 'lucide-react';
import type { Incapacidad, EmpleadoFallback } from '@/types/incapacidad';
import { cn } from '@/lib/utils';
import { formatDate } from '@/utils/formatters';

interface IncapacidadContextStripProps {
  incapacidad: Incapacidad;
  hasFraudAlert: boolean;
  empleadoFallback?: EmpleadoFallback | null;
}

export function IncapacidadContextStrip({
  incapacidad,
  hasFraudAlert,
  empleadoFallback,
}: IncapacidadContextStripProps) {
  const empleado = incapacidad.empleado;
  const empresa = incapacidad.empresa;
  const sinEmpleadoBD = !empleado;

  const empleadoNombre = empleado
    ? `${empleado.nombres} ${empleado.apellidos}`
    : empleadoFallback?.nombres ?? '—';

  const empleadoDoc = empleado?.numero_documento ?? empleadoFallback?.numero_documento ?? '';

  const empresaNombre = empresa?.razon_social ?? '—';

  return (
    <div className="bg-slate-50 border border-slate-200 rounded-md p-3 flex flex-wrap gap-3 text-sm">
      {/* Bloque empleado */}
      <div
        data-testid="empleado-section"
        className={cn(
          'flex flex-col rounded px-2 py-1 border',
          hasFraudAlert
            ? 'bg-red-50 border-red-300 text-red-900'
            : sinEmpleadoBD
            ? 'bg-amber-50 border-amber-300 text-amber-900'
            : 'bg-white border-slate-200 text-slate-700'
        )}
      >
        <span className="text-xs font-medium text-slate-500 uppercase tracking-wide leading-none mb-0.5">
          Empleado
        </span>
        <div className="flex items-center gap-1.5">
          {hasFraudAlert && <AlertTriangle className="h-3 w-3 text-red-500 flex-shrink-0" />}
          <span className="font-medium">{empleadoNombre}</span>
          {sinEmpleadoBD && (
            <span className="text-xs bg-amber-100 text-amber-700 border border-amber-200 rounded px-1 leading-none">
              Sin ficha
            </span>
          )}
        </div>
        {empleadoDoc && (
          <span className="text-xs opacity-75">{empleadoDoc}</span>
        )}
      </div>

      {/* Bloque empresa */}
      <div className="flex flex-col bg-white border border-slate-200 rounded px-2 py-1 text-slate-700">
        <span className="text-xs font-medium text-slate-500 uppercase tracking-wide leading-none mb-0.5">
          Empresa
        </span>
        <span className="font-medium">{empresaNombre}</span>
        {empresa?.nit && (
          <span className="text-xs text-slate-500">NIT {empresa.nit}</span>
        )}
      </div>

      {/* Bloque diagnóstico */}
      <div className="flex flex-col bg-white border border-slate-200 rounded px-2 py-1 text-slate-700">
        <span className="text-xs font-medium text-slate-500 uppercase tracking-wide leading-none mb-0.5">
          Diagnóstico
        </span>
        <span className="font-medium font-mono">{incapacidad.diagnostico_cie10 ?? '—'}</span>
        {incapacidad.diagnostico_descripcion && (
          <span className="text-xs text-slate-500 max-w-[160px] truncate">
            {incapacidad.diagnostico_descripcion}
          </span>
        )}
      </div>

      {/* Bloque período */}
      <div className="flex flex-col bg-white border border-slate-200 rounded px-2 py-1 text-slate-700">
        <span className="text-xs font-medium text-slate-500 uppercase tracking-wide leading-none mb-0.5">
          Período
        </span>
        <span className="font-medium">
          {formatDate(incapacidad.fecha_inicio)} → {formatDate(incapacidad.fecha_fin)}
        </span>
        <span className="text-xs text-slate-500">{incapacidad.dias_totales} días</span>
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Ejecutar los tests para confirmar que pasan**

```bash
cd /opt/apps/incapacidades_vs/apps/frontend/sistema-interno && npx vitest run src/components/incapacidades/__tests__/IncapacidadContextStrip.test.tsx --reporter=verbose 2>&1 | tail -20
```

Esperado: `4 passed`

- [ ] **Step 5: Commit**

```bash
git add apps/frontend/sistema-interno/src/components/incapacidades/IncapacidadContextStrip.tsx \
        apps/frontend/sistema-interno/src/components/incapacidades/__tests__/IncapacidadContextStrip.test.tsx
git commit -m "feat: add IncapacidadContextStrip compact summary component"
```

---

## Task 8: Frontend — componente `ValidacionesPanel`

**Files:**
- Create: `apps/frontend/sistema-interno/src/components/incapacidades/ValidacionesPanel.tsx`
- Create: `apps/frontend/sistema-interno/src/components/incapacidades/__tests__/ValidacionesPanel.test.tsx`

- [ ] **Step 1: Escribir el test que falla**

Crear `apps/frontend/sistema-interno/src/components/incapacidades/__tests__/ValidacionesPanel.test.tsx`:

```tsx
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ValidacionesPanel } from '../ValidacionesPanel';
import type { ValidationIssue } from '@/types/incapacidad';

const makeIssue = (overrides: Partial<ValidationIssue>): ValidationIssue => ({
  id: 'issue-1',
  pre_incapacidad_id: 'pre-1',
  incapacidad_id: 'inc-1',
  categoria: 'INTEGRATION_CHECK',
  severidad: 'WARNING',
  codigo: 'EMPLEADO_NOT_FOUND',
  descripcion: 'Empleado no encontrado en BD',
  campo_afectado: null,
  valor_encontrado: null,
  valor_esperado: null,
  fecha_deteccion: '2026-06-10T10:00:00Z',
  ...overrides,
});

describe('ValidacionesPanel', () => {
  it('muestra los issues con su código y descripción', () => {
    render(<ValidacionesPanel issues={[makeIssue({})]} isLoading={false} />);
    expect(screen.getByText('EMPLEADO_NOT_FOUND')).toBeInTheDocument();
    expect(screen.getByText('Empleado no encontrado en BD')).toBeInTheDocument();
  });

  it('muestra categorías sin problemas en verde cuando no hay issues', () => {
    render(<ValidacionesPanel issues={[]} isLoading={false} />);
    expect(screen.getByText(/FIELD_VALIDATION/i)).toBeInTheDocument();
    expect(screen.getByText(/BUSINESS_RULE/i)).toBeInTheDocument();
    expect(screen.getByText(/FRAUD_ALERT/i)).toBeInTheDocument();
    expect(screen.getByText(/INTEGRATION_CHECK/i)).toBeInTheDocument();
  });

  it('los issues ERROR aparecen antes que los WARNING', () => {
    const issues = [
      makeIssue({ id: '1', severidad: 'WARNING', codigo: 'WARN_CODE', descripcion: 'Warning issue' }),
      makeIssue({ id: '2', severidad: 'ERROR', codigo: 'ERR_CODE', descripcion: 'Error issue' }),
    ];
    render(<ValidacionesPanel issues={issues} isLoading={false} />);
    const items = screen.getAllByRole('listitem');
    const errIdx = items.findIndex(el => el.textContent?.includes('ERR_CODE'));
    const warnIdx = items.findIndex(el => el.textContent?.includes('WARN_CODE'));
    expect(errIdx).toBeLessThan(warnIdx);
  });

  it('cuando isLoading es true muestra estado de carga', () => {
    render(<ValidacionesPanel issues={[]} isLoading={true} />);
    expect(screen.getByText(/cargando/i)).toBeInTheDocument();
  });

  it('categorías con issues no aparecen en la sección de sin problemas', () => {
    const issues = [makeIssue({ categoria: 'FRAUD_ALERT' })];
    render(<ValidacionesPanel issues={issues} isLoading={false} />);
    // FRAUD_ALERT tiene issues — no debe aparecer en sección verde
    const greenItems = screen.queryAllByText(/sin problemas/i);
    // Los textos "sin problemas" deben ser de otras categorías, no FRAUD_ALERT
    const fraudAlertGreen = greenItems.find(el =>
      el.closest('li')?.textContent?.includes('FRAUD_ALERT')
    );
    expect(fraudAlertGreen).toBeUndefined();
  });
});
```

- [ ] **Step 2: Ejecutar el test para confirmar que falla**

```bash
cd /opt/apps/incapacidades_vs/apps/frontend/sistema-interno && npx vitest run src/components/incapacidades/__tests__/ValidacionesPanel.test.tsx --reporter=verbose 2>&1 | tail -20
```

Esperado: error de módulo no encontrado.

- [ ] **Step 3: Crear el componente**

Crear `apps/frontend/sistema-interno/src/components/incapacidades/ValidacionesPanel.tsx`:

```tsx
import { AlertCircle, AlertTriangle, Info, CheckCircle } from 'lucide-react';
import type { ValidationIssue } from '@/types/incapacidad';
import { cn } from '@/lib/utils';

type Categoria = 'FIELD_VALIDATION' | 'BUSINESS_RULE' | 'FRAUD_ALERT' | 'INTEGRATION_CHECK';

const CATEGORIA_LABELS: Record<Categoria, string> = {
  FIELD_VALIDATION: 'Validación de campos',
  BUSINESS_RULE: 'Reglas de negocio',
  FRAUD_ALERT: 'Alerta de fraude',
  INTEGRATION_CHECK: 'Verificación de integración',
};

const SEVERIDAD_ORDER: Record<string, number> = { ERROR: 0, WARNING: 1, INFO: 2 };

interface ValidacionesPanelProps {
  issues: ValidationIssue[];
  isLoading: boolean;
}

export function ValidacionesPanel({ issues, isLoading }: ValidacionesPanelProps) {
  if (isLoading) {
    return (
      <div className="py-8 text-center text-slate-500 text-sm">Cargando validaciones…</div>
    );
  }

  const sorted = [...issues].sort(
    (a, b) => (SEVERIDAD_ORDER[a.severidad] ?? 3) - (SEVERIDAD_ORDER[b.severidad] ?? 3)
  );

  const categoriasConIssues = new Set(issues.map(i => i.categoria));
  const categoriasSinIssues = (Object.keys(CATEGORIA_LABELS) as Categoria[]).filter(
    c => !categoriasConIssues.has(c)
  );

  return (
    <div className="space-y-4">
      {/* Sección 1: Issues encontrados */}
      {sorted.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-slate-700 mb-2">
            Alertas y problemas detectados ({sorted.length})
          </h3>
          <ul className="space-y-1.5" role="list">
            {sorted.map(issue => (
              <IssueRow key={issue.id} issue={issue} />
            ))}
          </ul>
        </div>
      )}

      {/* Sección 2: Categorías sin problemas */}
      {categoriasSinIssues.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold text-slate-700 mb-2">
            Sin problemas detectados
          </h3>
          <ul className="space-y-1" role="list">
            {categoriasSinIssues.map(cat => (
              <li
                key={cat}
                className="flex items-center gap-2 text-sm text-green-700 bg-green-50 border border-green-200 rounded px-3 py-1.5"
              >
                <CheckCircle className="h-3.5 w-3.5 flex-shrink-0" />
                <span className="font-mono text-xs font-medium">{cat}</span>
                <span className="text-green-600">— {CATEGORIA_LABELS[cat]} sin problemas</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {sorted.length === 0 && categoriasSinIssues.length === 0 && (
        <p className="text-sm text-slate-500 py-4 text-center">
          No se encontraron validaciones registradas.
        </p>
      )}
    </div>
  );
}

function IssueRow({ issue }: { issue: ValidationIssue }) {
  const config = {
    ERROR: {
      icon: <AlertCircle className="h-3.5 w-3.5 text-red-500 flex-shrink-0 mt-0.5" />,
      className: 'bg-red-50 border-red-200 text-red-900',
      badgeCls: 'bg-red-100 text-red-700 border-red-200',
    },
    WARNING: {
      icon: <AlertTriangle className="h-3.5 w-3.5 text-amber-500 flex-shrink-0 mt-0.5" />,
      className: 'bg-amber-50 border-amber-200 text-amber-900',
      badgeCls: 'bg-amber-100 text-amber-700 border-amber-200',
    },
    INFO: {
      icon: <Info className="h-3.5 w-3.5 text-blue-500 flex-shrink-0 mt-0.5" />,
      className: 'bg-blue-50 border-blue-200 text-blue-900',
      badgeCls: 'bg-blue-100 text-blue-700 border-blue-200',
    },
  }[issue.severidad] ?? {
    icon: <Info className="h-3.5 w-3.5 text-slate-400 flex-shrink-0 mt-0.5" />,
    className: 'bg-slate-50 border-slate-200 text-slate-700',
    badgeCls: 'bg-slate-100 text-slate-600 border-slate-200',
  };

  return (
    <li
      className={cn('flex items-start gap-2 border rounded px-3 py-2 text-sm', config.className)}
      role="listitem"
    >
      {config.icon}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className={cn('font-mono text-xs font-semibold border rounded px-1.5 py-0.5 leading-none', config.badgeCls)}>
            {issue.codigo}
          </span>
          {issue.campo_afectado && (
            <span className="text-xs bg-slate-100 text-slate-500 border border-slate-200 rounded px-1.5 py-0.5 leading-none">
              {issue.campo_afectado}
            </span>
          )}
        </div>
        <p className="mt-0.5 leading-snug">{issue.descripcion}</p>
        {issue.valor_encontrado && (
          <p className="text-xs opacity-75 mt-0.5">
            Encontrado: <span className="font-mono">{issue.valor_encontrado}</span>
            {issue.valor_esperado && (
              <> · Esperado: <span className="font-mono">{issue.valor_esperado}</span></>
            )}
          </p>
        )}
      </div>
    </li>
  );
}
```

- [ ] **Step 4: Ejecutar los tests para confirmar que pasan**

```bash
cd /opt/apps/incapacidades_vs/apps/frontend/sistema-interno && npx vitest run src/components/incapacidades/__tests__/ValidacionesPanel.test.tsx --reporter=verbose 2>&1 | tail -20
```

Esperado: `5 passed`

- [ ] **Step 5: Commit**

```bash
git add apps/frontend/sistema-interno/src/components/incapacidades/ValidacionesPanel.tsx \
        apps/frontend/sistema-interno/src/components/incapacidades/__tests__/ValidacionesPanel.test.tsx
git commit -m "feat: add ValidacionesPanel component with sorted issues and clean-category display"
```

---

## Task 9: Frontend — `GestionarPage` wiring

**Files:**
- Modify: `apps/frontend/sistema-interno/src/pages/incapacidades/GestionarPage.tsx`

- [ ] **Step 1: Agregar el import de los nuevos componentes y tipo**

Abrir `apps/frontend/sistema-interno/src/pages/incapacidades/GestionarPage.tsx`.

Añadir a los imports existentes:

```tsx
import { IncapacidadContextStrip } from '@/components/incapacidades/IncapacidadContextStrip';
import { ValidacionesPanel } from '@/components/incapacidades/ValidacionesPanel';
```

- [ ] **Step 2: Agregar la query de validaciones**

Después de la query de `datosAprobados` (línea ~69), añadir:

```tsx
  // Query: Obtener validaciones
  const { data: validaciones, isLoading: validacionesLoading } = useQuery({
    queryKey: ['incapacidad', id, 'validaciones'],
    queryFn: () => incapacidadService.getValidaciones(id!),
    enabled: !!id,
  });

  const hasFraudAlert = validaciones?.has_fraud_alert ?? false;
```

- [ ] **Step 3: Insertar el strip de contexto en el tab Auditoría**

Localizar el `TabsContent value="auditoria"`. Después de la apertura del `<TabsContent>` y antes del bloque `{canManage ? (`, insertar:

```tsx
              {/* Strip de contexto compacto */}
              {incapacidad && (
                <IncapacidadContextStrip
                  incapacidad={incapacidad}
                  hasFraudAlert={hasFraudAlert}
                />
              )}
```

- [ ] **Step 4: Renombrar tab y reemplazar contenido de "Detalle Completo"**

Localizar el `TabsTrigger value="detalle"` y cambiar su label:

```tsx
              <TabsTrigger value="detalle" className="space-x-2">
                <FileText className="h-4 w-4" />
                <span>Validaciones</span>
              </TabsTrigger>
```

Localizar el `TabsContent value="detalle"` y reemplazar **todo su contenido** por:

```tsx
            {/* Tab: Validaciones */}
            <TabsContent value="detalle" className="space-y-4">
              <ValidacionesPanel
                issues={validaciones?.issues ?? []}
                isLoading={validacionesLoading}
              />
            </TabsContent>
```

- [ ] **Step 5: Verificar TypeScript**

```bash
cd /opt/apps/incapacidades_vs/apps/frontend/sistema-interno && npx tsc --noEmit 2>&1 | head -20
```

Esperado: sin errores.

- [ ] **Step 6: Ejecutar todos los tests del frontend**

```bash
cd /opt/apps/incapacidades_vs/apps/frontend/sistema-interno && npx vitest run --reporter=verbose 2>&1 | tail -30
```

Esperado: todos los tests existentes pasan junto con los nuevos.

- [ ] **Step 7: Commit**

```bash
git add apps/frontend/sistema-interno/src/pages/incapacidades/GestionarPage.tsx
git commit -m "feat: add context strip to audit tab and rename Detalle Completo to Validaciones"
```

---

## Self-Review

**Cobertura de spec:**
- ✅ Columna empleado con fallback desde `pre_incapacidad` (Task 4 backend + Task 6 frontend)
- ✅ `empresa_nit` y `empresa_nombre` incluidos en fallback (Task 4 + Task 6)
- ✅ Endpoint `GET /incapacidades/{id}/validaciones` incluye issues de `pre_incapacidad` (Task 3)
- ✅ Strip compacto en tab Auditoría (Task 9)
- ✅ Borde ámbar si sin ficha, borde rojo si FRAUD_ALERT (Task 7)
- ✅ Tab renombrado a "Validaciones", issues fallidos primero (Task 8)
- ✅ Categorías sin issues mostradas en verde (Task 8)

**Consistencia de tipos:**
- `EmpleadoFallback` definido en Task 2 (backend) y Task 5 (frontend) — mismo contrato
- `ValidacionesResponse` definido en Task 2 y consumido en Tasks 3, 5, 9
- `hasFraudAlert` derivado de `validaciones?.has_fraud_alert` en Task 9 — coincide con campo del schema Task 2

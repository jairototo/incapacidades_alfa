# Asignación de Auditoría por Sucursal Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** When an incapacidad enters `EN_AUDITORIA`, automatically assign it to an auditor chosen by the sucursal of its active siniestro (load-balanced among that sucursal's auditors), fall back to `auditor_default` when no qualifying siniestro exists, expose the assignment as a bandeja filter, and add an admin module to manage auditors and see their workload.

**Architecture:** Three additive DB columns (`usuario.sucursal`, `usuario.incapacidades_asignadas_activas`, `incapacidad.auditor_asignado_id`). A new `auditor_assignment_service.py` does the sucursal+load-balance pick, called from `auditoria_service.auditar_incapacidad()` (the Celery-driven RADICADA→EN_AUDITORIA path, per the source requirement). The workload counter is kept in sync by a hook inside `IncapacidadService._cambiar_estado()`, the single choke point every later transition already passes through. The admin module extends the existing `usuario_service`/`usuarios.py` CRUD (already ADMIN-gated) rather than building new CRUD.

**Tech Stack:** FastAPI + SQLAlchemy 2 async, Alembic, PostgreSQL, Celery, React 18 + Tailwind v3, Zod v3, React Query, Vitest, pytest (Docker exec).

## Global Constraints

- Backend tests: `docker exec incapacidades-api python -m pytest <path> -v --no-cov` (container is already running; only run the tests for the file(s) you just touched, not the whole suite, per repo convention).
- Frontend tests: `npm test -- <pattern>` from `apps/frontend/sistema-interno/`.
- TDD: red → implement → green → commit per task.
- Conventional Commits: `feat:`, `fix:`, `refactor:`, `test:`, `chore:`, `docs:`.
- Never N+1: use `selectinload` for every new eager-load.
- All historial_estado entries use `entity_type="incapacidad"` and string state values (already enforced by `_cambiar_estado`/`_registrar_historial` — do not bypass them).
- Spec doc: `docs/superpowers/specs/2026-07-25-asignacion-auditoria-sucursal-design.md` — read it first if anything below is ambiguous.
- Excel source: `docs/recursos_arl/Asignación Auditores - Incapacidades ARL.xlsx` (Cali, Medellín, Cartagena → 1 auditor each; Bogotá → 4). Its "casos" column's legacy per-person/odd-even routing text is intentionally NOT implemented — sucursal + load-balance only.
- Alembic head at plan-writing time: `4941157b1c2c` (file `20260725_1521_4941157b1c2c_add_en_pago_states_to_chk_incapacidad_.py`). Use it as `down_revision` for the new migration; if another migration has landed by the time you run this task, re-check `alembic heads` and adjust.

---

## Phase 1: Data Model

### Task 1: Add `usuario.sucursal`, `usuario.incapacidades_asignadas_activas`, `incapacidad.auditor_asignado_id`

**Files:**
- Create: `apps/backend/alembic/versions/<timestamp>_add_auditor_sucursal_assignment.py`
- Modify: `apps/backend/app/models/usuario.py`
- Modify: `apps/backend/app/models/incapacidad.py`
- Test: `apps/backend/tests/unit/test_auditor_assignment_columns.py`

**Interfaces:**
- Produces: `Usuario.sucursal: Optional[SucursalSiniestro]`, `Usuario.incapacidades_asignadas_activas: int`, `Incapacidad.auditor_asignado_id: Optional[UUID]`, `Incapacidad.auditor_asignado: Optional[Usuario]` (relationship, no back_populates — matches the existing asymmetric pattern used by `auditado_por`/`aprobado_por`/`radicado_por`).

- [ ] **Step 1: Write the failing test**

```python
# apps/backend/tests/unit/test_auditor_assignment_columns.py
import pytest
from app.utils.enums import RolUsuario, EstadoUsuario, SucursalSiniestro


@pytest.mark.asyncio
async def test_usuario_has_sucursal_and_carga_columns(db_session):
    from app.models.usuario import Usuario
    from app.core.security import get_password_hash

    usuario = Usuario(
        username="test.auditor.col",
        email="test.auditor.col@example.com",
        password_hash=get_password_hash("Test123!"),
        nombre_completo="Auditor Columnas Test",
        rol=RolUsuario.AUDITOR,
        estado=EstadoUsuario.ACTIVO,
        sucursal=SucursalSiniestro.CALI,
    )
    db_session.add(usuario)
    await db_session.commit()
    await db_session.refresh(usuario)

    assert usuario.sucursal == SucursalSiniestro.CALI
    assert usuario.incapacidades_asignadas_activas == 0


@pytest.mark.asyncio
async def test_incapacidad_has_auditor_asignado_column(db_session, test_incapacidad, test_user_auditor):
    test_incapacidad.auditor_asignado_id = test_user_auditor.id
    db_session.add(test_incapacidad)
    await db_session.commit()
    await db_session.refresh(test_incapacidad)

    assert test_incapacidad.auditor_asignado_id == test_user_auditor.id
```

- [ ] **Step 2: Run to verify it fails**

Run: `docker exec incapacidades-api python -m pytest tests/unit/test_auditor_assignment_columns.py -v --no-cov`
Expected: FAIL — `TypeError: 'sucursal' is an invalid keyword argument for Usuario` (column doesn't exist yet).

- [ ] **Step 3: Add columns to `app/models/usuario.py`**

Add the import and two columns (after the existing `token_version`/`must_change_password` fields, before the `# Relaciones` comment):

```python
from app.utils.enums import RolUsuario, EstadoUsuario, SucursalSiniestro
```

```python
    sucursal: Mapped[Optional[SucursalSiniestro]] = mapped_column(
        String(50),
        nullable=True,
        comment="Sucursal asignada (solo aplica a rol=AUDITOR); determina qué incapacidades ARL puede recibir",
    )
    incapacidades_asignadas_activas: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0",
        comment="Contador de incapacidades actualmente asignadas y abiertas (balanceo de carga); no es acumulado histórico",
    )
```

- [ ] **Step 4: Add column + relationship to `app/models/incapacidad.py`**

Add the column right after the existing `aprobado_por_id` line:

```python
    auditor_asignado_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("usuario.id"),
        comment="Auditor asignado automáticamente al entrar a EN_AUDITORIA, según sucursal del siniestro y balanceo de carga",
    )
```

Add the relationship right after the existing `auditado_por` relationship:

```python
    auditor_asignado: Mapped[Optional["Usuario"]] = relationship("Usuario", foreign_keys=[auditor_asignado_id])
```

- [ ] **Step 5: Generate and write the Alembic migration**

```bash
cd apps/backend
docker exec incapacidades-api alembic revision -m "add auditor sucursal assignment columns"
```

Edit the generated file (set `down_revision = "4941157b1c2c"` if not already, and fill in):

```python
from alembic import op
import sqlalchemy as sa


def upgrade() -> None:
    op.add_column("usuario", sa.Column("sucursal", sa.String(length=50), nullable=True))
    op.add_column(
        "usuario",
        sa.Column("incapacidades_asignadas_activas", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "incapacidad",
        sa.Column("auditor_asignado_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "incapacidad_auditor_asignado_id_fkey",
        "incapacidad", "usuario",
        ["auditor_asignado_id"], ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("incapacidad_auditor_asignado_id_fkey", "incapacidad", type_="foreignkey")
    op.drop_column("incapacidad", "auditor_asignado_id")
    op.drop_column("usuario", "incapacidades_asignadas_activas")
    op.drop_column("usuario", "sucursal")
```

- [ ] **Step 6: Apply the migration**

```bash
docker exec incapacidades-api alembic upgrade head
```

Expected: no error. Verify with `docker exec incapacidades-postgres psql -U postgres -d incapacidades -c "\d usuario"` — `sucursal` and `incapacidades_asignadas_activas` present.

- [ ] **Step 7: Run test to verify it passes**

Run: `docker exec incapacidades-api python -m pytest tests/unit/test_auditor_assignment_columns.py -v --no-cov`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add apps/backend/alembic/versions/ apps/backend/app/models/usuario.py apps/backend/app/models/incapacidad.py apps/backend/tests/unit/test_auditor_assignment_columns.py
git commit -m "feat(db): add usuario.sucursal, usuario.incapacidades_asignadas_activas, incapacidad.auditor_asignado_id"
```

---

## Phase 2: Siniestro Lookup + Assignment Algorithm

### Task 2: `SiniestroRepository.get_activo_para_incapacidad()`

**Files:**
- Modify: `apps/backend/app/db/repositories/siniestro_repository.py`
- Test: `apps/backend/tests/unit/test_siniestro_activo_para_incapacidad.py`

**Interfaces:**
- Produces: `SiniestroRepository.get_activo_para_incapacidad(db, empleado_id: UUID, fecha_inicio: date) -> Optional[Siniestro]` — the most recent siniestro of that employee with `estado IN (REPORTADO, EN_INVESTIGACION)` and `fecha_siniestro <= fecha_inicio`. Returns `None` if none qualifies. Distinct from the existing `get_candidatos()` (which serves the manual vincular-siniestro UI, has no estado filter, and bounds by `fecha_fin` — do not modify it).

- [ ] **Step 1: Write the failing tests**

```python
# apps/backend/tests/unit/test_siniestro_activo_para_incapacidad.py
import pytest
from datetime import date
from app.db.repositories.siniestro_repository import siniestro_repository
from app.models.siniestro import Siniestro
from app.utils.enums import TipoSiniestro, GravedadSiniestro, EstadoSiniestro


def _make_siniestro(empleado_id, empresa_id, numero, fecha_siniestro, estado):
    return Siniestro(
        numero_siniestro=numero,
        empleado_id=empleado_id,
        empresa_id=empresa_id,
        fecha_siniestro=fecha_siniestro,
        tipo_siniestro=TipoSiniestro.ACCIDENTE_TRABAJO,
        descripcion="Caída en escalera",
        gravedad=GravedadSiniestro.LEVE,
        estado=estado,
    )


@pytest.mark.asyncio
async def test_returns_none_when_no_siniestro(db_session, test_empleado):
    result = await siniestro_repository.get_activo_para_incapacidad(
        db_session, test_empleado.id, date(2026, 6, 1)
    )
    assert result is None


@pytest.mark.asyncio
async def test_excludes_siniestro_after_fecha_inicio(db_session, test_empleado, test_empresa):
    sin = _make_siniestro(
        test_empleado.id, test_empresa.id, "SIN-FUT-001",
        date(2026, 6, 10), EstadoSiniestro.REPORTADO,
    )
    db_session.add(sin)
    await db_session.commit()

    result = await siniestro_repository.get_activo_para_incapacidad(
        db_session, test_empleado.id, date(2026, 6, 1)
    )
    assert result is None


@pytest.mark.asyncio
async def test_excludes_cerrado_and_anulado(db_session, test_empleado, test_empresa):
    for numero, estado in [("SIN-CER-001", EstadoSiniestro.CERRADO), ("SIN-ANU-001", EstadoSiniestro.ANULADO)]:
        db_session.add(_make_siniestro(test_empleado.id, test_empresa.id, numero, date(2026, 5, 1), estado))
    await db_session.commit()

    result = await siniestro_repository.get_activo_para_incapacidad(
        db_session, test_empleado.id, date(2026, 6, 1)
    )
    assert result is None


@pytest.mark.asyncio
async def test_picks_most_recent_qualifying_siniestro(db_session, test_empleado, test_empresa):
    older = _make_siniestro(test_empleado.id, test_empresa.id, "SIN-OLD-001", date(2026, 1, 1), EstadoSiniestro.REPORTADO)
    newer = _make_siniestro(test_empleado.id, test_empresa.id, "SIN-NEW-001", date(2026, 5, 20), EstadoSiniestro.EN_INVESTIGACION)
    db_session.add_all([older, newer])
    await db_session.commit()

    result = await siniestro_repository.get_activo_para_incapacidad(
        db_session, test_empleado.id, date(2026, 6, 1)
    )
    assert result is not None
    assert result.numero_siniestro == "SIN-NEW-001"


@pytest.mark.asyncio
async def test_includes_siniestro_on_same_day_as_fecha_inicio(db_session, test_empleado, test_empresa):
    sin = _make_siniestro(test_empleado.id, test_empresa.id, "SIN-SAME-001", date(2026, 6, 1), EstadoSiniestro.REPORTADO)
    db_session.add(sin)
    await db_session.commit()

    result = await siniestro_repository.get_activo_para_incapacidad(
        db_session, test_empleado.id, date(2026, 6, 1)
    )
    assert result is not None
    assert result.numero_siniestro == "SIN-SAME-001"
```

- [ ] **Step 2: Run to verify it fails**

Run: `docker exec incapacidades-api python -m pytest tests/unit/test_siniestro_activo_para_incapacidad.py -v --no-cov`
Expected: FAIL — `AttributeError: 'SiniestroRepository' object has no attribute 'get_activo_para_incapacidad'`

- [ ] **Step 3: Implement the method**

Add to `app/db/repositories/siniestro_repository.py` (same class as `get_candidatos`, keep both — they serve different callers):

```python
    async def get_activo_para_incapacidad(
        self,
        db: AsyncSession,
        empleado_id: UUID,
        fecha_inicio: date,
    ) -> Optional[Siniestro]:
        """
        Encuentra el siniestro activo más reciente del empleado que pudo haber
        originado una incapacidad con esta fecha_inicio.

        "Activo" = estado in (REPORTADO, EN_INVESTIGACION) — excluye CERRADO/ANULADO.
        El siniestro debe ocurrir el mismo día o antes del inicio de la incapacidad
        (fecha_siniestro <= fecha_inicio); nunca después.

        Usado por auditor_assignment_service para determinar la sucursal a la
        que enrutar la auditoría. No confundir con get_candidatos(), que sirve
        la UI manual de vinculación de siniestro (sin filtro de estado, acotado
        por fecha_fin en vez de fecha_inicio).

        Returns:
            El siniestro calificado más reciente, o None si ninguno califica.
        """
        query = (
            select(Siniestro)
            .where(
                and_(
                    Siniestro.empleado_id == empleado_id,
                    Siniestro.estado.in_([EstadoSiniestro.REPORTADO, EstadoSiniestro.EN_INVESTIGACION]),
                    Siniestro.fecha_siniestro <= fecha_inicio,
                )
            )
            .order_by(Siniestro.fecha_siniestro.desc())
            .limit(1)
        )
        result = await db.execute(query)
        return result.scalars().first()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `docker exec incapacidades-api python -m pytest tests/unit/test_siniestro_activo_para_incapacidad.py -v --no-cov`
Expected: PASS (5 tests)

- [ ] **Step 5: Commit**

```bash
git add apps/backend/app/db/repositories/siniestro_repository.py apps/backend/tests/unit/test_siniestro_activo_para_incapacidad.py
git commit -m "feat(siniestro): add get_activo_para_incapacidad for auditor assignment lookup"
```

---

### Task 3: `auditor_assignment_service.py` — sucursal pick + load balance + default fallback

**Files:**
- Create: `apps/backend/app/services/auditor_assignment_service.py`
- Test: `apps/backend/tests/test_auditor_assignment_service.py`

**Interfaces:**
- Consumes: `siniestro_repository.get_activo_para_incapacidad(db, empleado_id, fecha_inicio)` (Task 2).
- Produces: `async def asignar_auditor(db: AsyncSession, incapacidad: Incapacidad) -> Usuario` — sets `incapacidad.auditor_asignado_id`, increments the chosen auditor's `incapacidades_asignadas_activas`, returns the `Usuario` assigned. Raises `RuntimeError` if `auditor_default` doesn't exist (a seeding problem, not a request error — see Task 6).

- [ ] **Step 1: Write the failing tests**

```python
# apps/backend/tests/test_auditor_assignment_service.py
import pytest
from datetime import date, datetime
from app.services.auditor_assignment_service import asignar_auditor
from app.models.incapacidad import Incapacidad
from app.models.siniestro import Siniestro
from app.models.usuario import Usuario
from app.utils.enums import (
    TipoIncapacidad, EstadoIncapacidad, TipoSiniestro, GravedadSiniestro,
    EstadoSiniestro, RolUsuario, EstadoUsuario, SucursalSiniestro,
)
from app.core.security import get_password_hash


async def _make_auditor(db_session, username, sucursal, carga=0):
    u = Usuario(
        username=username, email=f"{username}@segurosalfa-test.com.co",
        password_hash=get_password_hash("Test123!"), nombre_completo=username,
        rol=RolUsuario.AUDITOR, estado=EstadoUsuario.ACTIVO,
        sucursal=sucursal, incapacidades_asignadas_activas=carga,
    )
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)
    return u


async def _make_default_auditor(db_session):
    u = Usuario(
        username="auditor_default", email="auditor.default@segurosalfa-test.com.co",
        password_hash=get_password_hash("Test123!"), nombre_completo="Auditor por Defecto",
        rol=RolUsuario.AUDITOR, estado=EstadoUsuario.ACTIVO,
    )
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)
    return u


@pytest.mark.asyncio
async def test_assigns_by_sucursal_of_active_siniestro(db_session, test_empleado, test_empresa):
    auditor_cali = await _make_auditor(db_session, "test.cali", SucursalSiniestro.CALI)
    sin = Siniestro(
        numero_siniestro="SIN-CALI-001", empleado_id=test_empleado.id, empresa_id=test_empresa.id,
        fecha_siniestro=date(2026, 5, 1), tipo_siniestro=TipoSiniestro.ACCIDENTE_TRABAJO,
        descripcion="x", gravedad=GravedadSiniestro.LEVE, estado=EstadoSiniestro.REPORTADO,
        sucursal=SucursalSiniestro.CALI,
    )
    db_session.add(sin)
    await db_session.commit()

    inc = Incapacidad(
        numero="ARL-ASIG-001", tipo=TipoIncapacidad.ARL, empleado_id=test_empleado.id,
        empresa_id=test_empresa.id, fecha_inicio=date(2026, 5, 2), fecha_fin=date(2026, 5, 10),
        dias_totales=8, estado=EstadoIncapacidad.EN_AUDITORIA, fecha_radicacion=datetime.utcnow(),
    )
    db_session.add(inc)
    await db_session.commit()

    auditor = await asignar_auditor(db_session, inc)

    assert auditor.id == auditor_cali.id
    assert inc.auditor_asignado_id == auditor_cali.id
    await db_session.refresh(auditor_cali)
    assert auditor_cali.incapacidades_asignadas_activas == 1


@pytest.mark.asyncio
async def test_load_balances_between_auditors_same_sucursal(db_session, test_empleado, test_empresa):
    busy = await _make_auditor(db_session, "test.bta.busy", SucursalSiniestro.BOGOTA, carga=5)
    idle = await _make_auditor(db_session, "test.bta.idle", SucursalSiniestro.BOGOTA, carga=1)
    sin = Siniestro(
        numero_siniestro="SIN-BTA-001", empleado_id=test_empleado.id, empresa_id=test_empresa.id,
        fecha_siniestro=date(2026, 5, 1), tipo_siniestro=TipoSiniestro.ACCIDENTE_TRABAJO,
        descripcion="x", gravedad=GravedadSiniestro.LEVE, estado=EstadoSiniestro.EN_INVESTIGACION,
        sucursal=SucursalSiniestro.BOGOTA,
    )
    db_session.add(sin)
    await db_session.commit()

    inc = Incapacidad(
        numero="ARL-ASIG-002", tipo=TipoIncapacidad.ARL, empleado_id=test_empleado.id,
        empresa_id=test_empresa.id, fecha_inicio=date(2026, 5, 3), fecha_fin=date(2026, 5, 10),
        dias_totales=7, estado=EstadoIncapacidad.EN_AUDITORIA, fecha_radicacion=datetime.utcnow(),
    )
    db_session.add(inc)
    await db_session.commit()

    auditor = await asignar_auditor(db_session, inc)

    assert auditor.id == idle.id
    assert busy.incapacidades_asignadas_activas == 5  # unchanged


@pytest.mark.asyncio
async def test_falls_back_to_default_when_no_siniestro(db_session, test_afiliado):
    default_auditor = await _make_default_auditor(db_session)

    inc = Incapacidad(
        numero="SALUD-ASIG-001", tipo=TipoIncapacidad.SALUD, afiliado_id=test_afiliado.id,
        fecha_inicio=date(2026, 5, 3), fecha_fin=date(2026, 5, 10), dias_totales=7,
        estado=EstadoIncapacidad.EN_AUDITORIA, fecha_radicacion=datetime.utcnow(),
    )
    db_session.add(inc)
    await db_session.commit()

    auditor = await asignar_auditor(db_session, inc)

    assert auditor.id == default_auditor.id
    assert inc.auditor_asignado_id == default_auditor.id


@pytest.mark.asyncio
async def test_falls_back_to_default_when_no_auditor_configured_for_sucursal(db_session, test_empleado, test_empresa):
    default_auditor = await _make_default_auditor(db_session)
    # No AUDITOR configured for CARTAGENA
    sin = Siniestro(
        numero_siniestro="SIN-CTG-001", empleado_id=test_empleado.id, empresa_id=test_empresa.id,
        fecha_siniestro=date(2026, 5, 1), tipo_siniestro=TipoSiniestro.ACCIDENTE_TRABAJO,
        descripcion="x", gravedad=GravedadSiniestro.LEVE, estado=EstadoSiniestro.REPORTADO,
        sucursal=SucursalSiniestro.CARTAGENA,
    )
    db_session.add(sin)
    await db_session.commit()

    inc = Incapacidad(
        numero="ARL-ASIG-003", tipo=TipoIncapacidad.ARL, empleado_id=test_empleado.id,
        empresa_id=test_empresa.id, fecha_inicio=date(2026, 5, 2), fecha_fin=date(2026, 5, 10),
        dias_totales=8, estado=EstadoIncapacidad.EN_AUDITORIA, fecha_radicacion=datetime.utcnow(),
    )
    db_session.add(inc)
    await db_session.commit()

    auditor = await asignar_auditor(db_session, inc)

    assert auditor.id == default_auditor.id


@pytest.mark.asyncio
async def test_raises_when_default_auditor_missing(db_session, test_afiliado):
    inc = Incapacidad(
        numero="SALUD-ASIG-002", tipo=TipoIncapacidad.SALUD, afiliado_id=test_afiliado.id,
        fecha_inicio=date(2026, 5, 3), fecha_fin=date(2026, 5, 10), dias_totales=7,
        estado=EstadoIncapacidad.EN_AUDITORIA, fecha_radicacion=datetime.utcnow(),
    )
    db_session.add(inc)
    await db_session.commit()

    with pytest.raises(RuntimeError, match="auditor_default"):
        await asignar_auditor(db_session, inc)
```

- [ ] **Step 2: Run to verify it fails**

Run: `docker exec incapacidades-api python -m pytest tests/test_auditor_assignment_service.py -v --no-cov`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.services.auditor_assignment_service'`

- [ ] **Step 3: Implement the service**

```python
# apps/backend/app/services/auditor_assignment_service.py
"""
Asignación automática de auditor a una incapacidad, según la sucursal del
siniestro activo y el balanceo de carga entre auditores de esa sucursal.

Ver docs/superpowers/specs/2026-07-25-asignacion-auditoria-sucursal-design.md
"""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.incapacidad import Incapacidad
from app.models.siniestro import Siniestro
from app.models.usuario import Usuario
from app.db.repositories.siniestro_repository import siniestro_repository
from app.utils.enums import TipoIncapacidad, RolUsuario, EstadoUsuario, SucursalSiniestro


async def asignar_auditor(db: AsyncSession, incapacidad: Incapacidad) -> Usuario:
    """
    Asigna un auditor a `incapacidad` (ya en estado EN_AUDITORIA) y persiste
    tanto `incapacidad.auditor_asignado_id` como el incremento de carga del
    auditor elegido. No hace commit — el caller controla la transacción.
    """
    siniestro = await _resolver_siniestro(db, incapacidad)

    auditor: Optional[Usuario] = None
    if siniestro is not None and siniestro.sucursal is not None:
        auditor = await _pick_by_sucursal(db, siniestro.sucursal)

    if auditor is None:
        auditor = await _get_auditor_default(db)

    incapacidad.auditor_asignado_id = auditor.id
    auditor.incapacidades_asignadas_activas += 1
    db.add(incapacidad)
    db.add(auditor)
    return auditor


async def _resolver_siniestro(db: AsyncSession, incapacidad: Incapacidad) -> Optional[Siniestro]:
    """Usa el siniestro ya vinculado si existe; si no, busca uno activo por fecha."""
    if incapacidad.siniestro_id is not None:
        result = await db.execute(select(Siniestro).where(Siniestro.id == incapacidad.siniestro_id))
        return result.scalars().first()

    if incapacidad.tipo != TipoIncapacidad.ARL or not incapacidad.empleado_id:
        return None

    return await siniestro_repository.get_activo_para_incapacidad(
        db, incapacidad.empleado_id, incapacidad.fecha_inicio
    )


async def _pick_by_sucursal(db: AsyncSession, sucursal: SucursalSiniestro) -> Optional[Usuario]:
    """Auditor ACTIVO de esa sucursal con menor carga activa (empate: id menor)."""
    query = (
        select(Usuario)
        .where(
            Usuario.rol == RolUsuario.AUDITOR,
            Usuario.estado == EstadoUsuario.ACTIVO,
            Usuario.sucursal == sucursal,
        )
        .order_by(Usuario.incapacidades_asignadas_activas.asc(), Usuario.id.asc())
        .limit(1)
    )
    result = await db.execute(query)
    return result.scalars().first()


async def _get_auditor_default(db: AsyncSession) -> Usuario:
    result = await db.execute(select(Usuario).where(Usuario.username == "auditor_default"))
    auditor = result.scalars().first()
    if auditor is None:
        raise RuntimeError(
            "El usuario 'auditor_default' no existe. Ejecuta scripts/seed_auditores.py "
            "antes de procesar auditorías."
        )
    return auditor
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `docker exec incapacidades-api python -m pytest tests/test_auditor_assignment_service.py -v --no-cov`
Expected: PASS (6 tests)

- [ ] **Step 5: Commit**

```bash
git add apps/backend/app/services/auditor_assignment_service.py apps/backend/tests/test_auditor_assignment_service.py
git commit -m "feat(auditoria): add auditor_assignment_service — sucursal pick, load balance, default fallback"
```

---

### Task 4: Wire `asignar_auditor` into `auditoria_service.auditar_incapacidad()`

**Files:**
- Modify: `apps/backend/app/services/auditoria_service.py`
- Test: `apps/backend/tests/test_auditoria_service.py`

**Interfaces:**
- Consumes: `asignar_auditor(db, inc)` (Task 3).

> Note (scope, documented in the spec's non-goals): this wires the assignment into the Celery-driven path (`enqueue_auditoria_incapacidad` → `auditar_incapacidad_task` → this module function), per the explicit source requirement. The separate `pre_incapacidad_promotion_service.py` path (which calls `IncapacidadService.radicar_incapacidad()` directly) does NOT go through this function and will NOT get an assigned auditor — flagged as a known gap, not fixed here since it wasn't part of the ask.

- [ ] **Step 1: Write the failing test**

Add to `apps/backend/tests/test_auditoria_service.py` (needs a `auditor_default` user to exist, since this incapacidad has no empleado siniestro — SALUD/no-siniestro case falls back):

```python
@pytest.mark.asyncio
async def test_audit_assigns_default_auditor_when_no_siniestro(db_session, test_empleado, test_empresa):
    from app.models.usuario import Usuario
    from app.utils.enums import RolUsuario, EstadoUsuario
    from app.core.security import get_password_hash

    default_auditor = Usuario(
        username="auditor_default", email="auditor.default@segurosalfa-test.com.co",
        password_hash=get_password_hash("Test123!"), nombre_completo="Auditor por Defecto",
        rol=RolUsuario.AUDITOR, estado=EstadoUsuario.ACTIVO,
    )
    db_session.add(default_auditor)
    await db_session.commit()

    inc = Incapacidad(
        numero="ARL-AUDIT-ASIG01", tipo=TipoIncapacidad.ARL,
        empleado_id=test_empleado.id, empresa_id=test_empresa.id,
        fecha_inicio=dt.date(2026, 6, 1), fecha_fin=dt.date(2026, 6, 5), dias_totales=5,
        diagnostico_cie10="S00.0", nombre_medico="Dr X", registro_medico="RM-ASIG1",
        estado=EstadoIncapacidad.RADICADA, fecha_radicacion=dt.datetime.utcnow(),
    )
    db_session.add(inc)
    await db_session.flush()

    await auditar_incapacidad(db_session, inc.id)

    refreshed = (await db_session.execute(select(Incapacidad).where(Incapacidad.id == inc.id))).scalar_one()
    assert refreshed.auditor_asignado_id == default_auditor.id
```

- [ ] **Step 2: Run to verify it fails**

Run: `docker exec incapacidades-api python -m pytest tests/test_auditoria_service.py::test_audit_assigns_default_auditor_when_no_siniestro -v --no-cov`
Expected: FAIL — `auditor_asignado_id` is `None`.

- [ ] **Step 3: Wire the call in `app/services/auditoria_service.py`**

Add the import at the top (alongside the existing `from app.utils.enums import EstadoIncapacidad`):

```python
from app.services.auditor_assignment_service import asignar_auditor
```

In `auditar_incapacidad()`, change:

```python
    # Transicionar estado RADICADA → EN_AUDITORIA
    estado_anterior = inc.estado
    inc.estado = EstadoIncapacidad.EN_AUDITORIA
    db.add(inc)
```

to:

```python
    # Transicionar estado RADICADA → EN_AUDITORIA
    estado_anterior = inc.estado
    inc.estado = EstadoIncapacidad.EN_AUDITORIA
    auditor_asignado = await asignar_auditor(db, inc)
    db.add(inc)
```

And update the closing log line to include the assignment:

```python
    logger.info(
        f"Auditoría completa para {inc.numero}: {len(REGLAS_ESPERADAS)} reglas evaluadas "
        f"({len(failed_by_code)} fallidas) → EN_AUDITORIA, asignada a {auditor_asignado.username}"
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `docker exec incapacidades-api python -m pytest tests/test_auditoria_service.py -v --no-cov`
Expected: PASS (all tests in the file, including the pre-existing ones — they'll now also need `auditor_default` seeded; if `test_audit_persists_results_and_transitions` fails because no `auditor_default` exists in that test's session, add the same `auditor_default` Usuario creation at the top of that test too).

- [ ] **Step 5: Commit**

```bash
git add apps/backend/app/services/auditoria_service.py apps/backend/tests/test_auditoria_service.py
git commit -m "feat(auditoria): assign auditor by sucursal when transitioning RADICADA to EN_AUDITORIA"
```

---

## Phase 3: Workload Counter Sync

### Task 5: Decrement/re-increment hook inside `IncapacidadService._cambiar_estado()`

**Files:**
- Modify: `apps/backend/app/services/incapacidad_service.py`
- Test: `apps/backend/tests/test_auditor_carga_sync.py`

**Interfaces:**
- Produces: `IncapacidadService._ajustar_carga_auditor(db, incapacidad, estado_anterior, nuevo_estado) -> None` — called from inside `_cambiar_estado` for every transition. No-ops if `incapacidad.auditor_asignado_id` is unset.

- [ ] **Step 1: Write the failing tests**

```python
# apps/backend/tests/test_auditor_carga_sync.py
import pytest
from datetime import date, datetime
from app.models.incapacidad import Incapacidad
from app.models.usuario import Usuario
from app.utils.enums import TipoIncapacidad, EstadoIncapacidad, RolUsuario, EstadoUsuario
from app.core.security import get_password_hash
from app.services.incapacidad_service import incapacidad_service


async def _make_auditor(db_session, carga):
    u = Usuario(
        username="test.carga.auditor", email="test.carga.auditor@segurosalfa-test.com.co",
        password_hash=get_password_hash("Test123!"), nombre_completo="Auditor Carga Test",
        rol=RolUsuario.AUDITOR, estado=EstadoUsuario.ACTIVO,
        incapacidades_asignadas_activas=carga,
    )
    db_session.add(u)
    await db_session.commit()
    await db_session.refresh(u)
    return u


@pytest.mark.asyncio
async def test_decrements_on_liquidacion(db_session, test_empleado, test_empresa):
    auditor = await _make_auditor(db_session, carga=3)
    inc = Incapacidad(
        numero="ARL-CARGA-001", tipo=TipoIncapacidad.ARL, empleado_id=test_empleado.id,
        empresa_id=test_empresa.id, fecha_inicio=date(2026, 6, 1), fecha_fin=date(2026, 6, 5),
        dias_totales=5, estado=EstadoIncapacidad.EN_AUDITORIA, fecha_radicacion=datetime.utcnow(),
        auditor_asignado_id=auditor.id, siniestro_id=None,
    )
    db_session.add(inc)
    await db_session.commit()

    await incapacidad_service.auditar_incapacidad(
        db=db_session, incapacidad_id=inc.id, accion="RECHAZAR", observaciones="Sin soporte médico",
    )

    await db_session.refresh(auditor)
    assert auditor.incapacidades_asignadas_activas == 2


@pytest.mark.asyncio
async def test_reincrements_on_devolution_to_en_auditoria(db_session, test_empleado, test_empresa):
    from app.services.liquidacion_service import liquidacion_service

    auditor = await _make_auditor(db_session, carga=2)
    inc = Incapacidad(
        numero="ARL-CARGA-002", tipo=TipoIncapacidad.ARL, empleado_id=test_empleado.id,
        empresa_id=test_empresa.id, fecha_inicio=date(2026, 6, 1), fecha_fin=date(2026, 6, 5),
        dias_totales=5, estado=EstadoIncapacidad.LIQUIDACION, fecha_radicacion=datetime.utcnow(),
        auditor_asignado_id=auditor.id,
    )
    db_session.add(inc)
    await db_session.commit()

    await liquidacion_service.devolver_a_auditoria(
        db=db_session, incapacidad_id=inc.id, observacion="Datos incompletos", liquidador_id=auditor.id,
    )

    await db_session.refresh(auditor)
    assert auditor.incapacidades_asignadas_activas == 3


@pytest.mark.asyncio
async def test_noop_when_no_auditor_assigned(db_session, test_empleado, test_empresa):
    inc = Incapacidad(
        numero="ARL-CARGA-003", tipo=TipoIncapacidad.ARL, empleado_id=test_empleado.id,
        empresa_id=test_empresa.id, fecha_inicio=date(2026, 6, 1), fecha_fin=date(2026, 6, 5),
        dias_totales=5, estado=EstadoIncapacidad.EN_AUDITORIA, fecha_radicacion=datetime.utcnow(),
    )
    db_session.add(inc)
    await db_session.commit()

    # Should not raise even with no auditor_asignado_id
    await incapacidad_service.auditar_incapacidad(
        db=db_session, incapacidad_id=inc.id, accion="RECHAZAR", observaciones="Sin soporte médico",
    )
```

- [ ] **Step 2: Run to verify it fails**

Run: `docker exec incapacidades-api python -m pytest tests/test_auditor_carga_sync.py -v --no-cov`
Expected: FAIL — first two tests fail because `auditor.incapacidades_asignadas_activas` stays at its initial value (no decrement/increment happens yet).

- [ ] **Step 3: Implement the hook in `app/services/incapacidad_service.py`**

Add two module-level sets right after the `ALLOWED_TRANSITIONS` dict:

```python
# Estados donde una incapacidad cuenta como carga activa del auditor asignado.
AUDITOR_ESTADOS_ACTIVOS = {
    EstadoIncapacidad.EN_AUDITORIA,
    EstadoIncapacidad.PENDIENTE,
    EstadoIncapacidad.CREACION_SINIESTRO,
}
# Estados terminales desde la perspectiva del auditor (ya no es su carga).
AUDITOR_ESTADOS_TERMINALES = {
    EstadoIncapacidad.LIQUIDACION,
    EstadoIncapacidad.LIQUIDACION_PARCIAL,
    EstadoIncapacidad.GLOSADA,
}
```

Add the method to the `IncapacidadService` class, right before `_cambiar_estado`:

```python
    async def _ajustar_carga_auditor(
        self,
        db: AsyncSession,
        incapacidad: "Incapacidad",
        estado_anterior: EstadoIncapacidad,
        nuevo_estado: EstadoIncapacidad,
    ) -> None:
        """
        Mantiene incapacidades_asignadas_activas del auditor asignado en sync:
        decrementa al salir de los estados activos hacia un terminal, re-incrementa
        si una devolución del liquidador regresa el caso a EN_AUDITORIA. No-op si
        la incapacidad no tiene auditor_asignado_id (p. ej. el path de
        pre_incapacidad_promotion_service, que no pasa por la asignación automática).
        """
        if not incapacidad.auditor_asignado_id:
            return

        delta = 0
        if estado_anterior in AUDITOR_ESTADOS_ACTIVOS and nuevo_estado in AUDITOR_ESTADOS_TERMINALES:
            delta = -1
        elif estado_anterior in AUDITOR_ESTADOS_TERMINALES and nuevo_estado == EstadoIncapacidad.EN_AUDITORIA:
            delta = 1

        if delta == 0:
            return

        from app.models.usuario import Usuario
        auditor = await db.get(Usuario, incapacidad.auditor_asignado_id)
        if auditor is None:
            return
        auditor.incapacidades_asignadas_activas = max(0, auditor.incapacidades_asignadas_activas + delta)
        db.add(auditor)
```

In `_cambiar_estado`, right after `estado_anterior = incapacidad.estado`, add the call:

```python
        estado_anterior = incapacidad.estado
        await self._ajustar_carga_auditor(db, incapacidad, estado_anterior, nuevo_estado)
        update_data: Dict[str, Any] = {"estado": nuevo_estado, **(extra_update or {})}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `docker exec incapacidades-api python -m pytest tests/test_auditor_carga_sync.py -v --no-cov`
Expected: PASS (3 tests)

- [ ] **Step 5: Run the wider incapacidad_service test file to check for regressions**

Run: `docker exec incapacidades-api python -m pytest tests/test_auditoria_service.py tests/test_creacion_siniestro.py tests/test_aprobar_en_auditoria.py -v --no-cov`
Expected: PASS (no regressions — the hook no-ops whenever `auditor_asignado_id` is unset, which is true for every pre-existing test's incapacidades).

- [ ] **Step 6: Commit**

```bash
git add apps/backend/app/services/incapacidad_service.py apps/backend/tests/test_auditor_carga_sync.py
git commit -m "feat(auditoria): sync auditor workload counter on state transitions in/out of active states"
```

---

## Phase 4: Seed Data

### Task 6: `scripts/seed_auditores.py` — 7 fictitious auditors + `auditor_default`

**Files:**
- Create: `apps/backend/scripts/seed_auditores.py`

**Interfaces:**
- Produces: a standalone idempotent script (run manually, like `scripts/seed_admin.py` — no production data exists yet, so this isn't an Alembic data migration).

- [ ] **Step 1: Write the script**

```python
# apps/backend/scripts/seed_auditores.py
"""
Script para crear los auditores ficticios (por sucursal) y el auditor por
defecto usados por la asignación automática de auditoría.

Nombres/correos son ficticios — deliberadamente distintos a los auditores
reales listados en docs/recursos_arl/Asignación Auditores - Incapacidades ARL.xlsx,
ya que esos usuarios reales aún no tienen cuentas en el sistema.

Idempotente: si un username ya existe, lo salta.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.db.session import AsyncSessionLocal
from app.core.security import pwd_context
from app.utils.enums import RolUsuario, EstadoUsuario, SucursalSiniestro

AUDITORES = [
    ("auditor.cali", "Camila Restrepo Vargas", "camila.restrepo@segurosalfa-test.com.co", SucursalSiniestro.CALI),
    ("auditor.medellin", "Santiago Zuluaga Marín", "santiago.zuluaga@segurosalfa-test.com.co", SucursalSiniestro.MEDELLIN),
    ("auditor.cartagena", "Valentina Cabrales Ibarra", "valentina.cabrales@segurosalfa-test.com.co", SucursalSiniestro.CARTAGENA),
    ("auditor.bogota1", "Andrés Felipe Rojas Peña", "andres.rojas@segurosalfa-test.com.co", SucursalSiniestro.BOGOTA),
    ("auditor.bogota2", "Laura Camila Torres Duque", "laura.torres@segurosalfa-test.com.co", SucursalSiniestro.BOGOTA),
    ("auditor.bogota3", "Juan Pablo Medina Salcedo", "juan.medina@segurosalfa-test.com.co", SucursalSiniestro.BOGOTA),
    ("auditor.bogota4", "Daniela Ríos Castañeda", "daniela.rios@segurosalfa-test.com.co", SucursalSiniestro.BOGOTA),
    ("auditor_default", "Auditor por Defecto", "auditor.default@segurosalfa-test.com.co", None),
]

DEFAULT_PASSWORD = "Auditor2026!"


async def seed_auditores() -> None:
    async with AsyncSessionLocal() as session:
        for username, nombre_completo, email, sucursal in AUDITORES:
            existing = await session.execute(
                text("SELECT id FROM usuario WHERE username = :username"),
                {"username": username},
            )
            if existing.fetchone():
                print(f"⏭️  {username} ya existe, se omite")
                continue

            import uuid
            await session.execute(
                text("""
                    INSERT INTO usuario (
                        id, username, email, password_hash, nombre_completo,
                        rol, estado, sucursal, incapacidades_asignadas_activas,
                        intentos_fallidos, must_change_password, created_at, updated_at
                    ) VALUES (
                        :id, :username, :email, :password_hash, :nombre_completo,
                        :rol, :estado, :sucursal, 0,
                        0, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                    )
                """),
                {
                    "id": uuid.uuid4(),
                    "username": username,
                    "email": email,
                    "password_hash": pwd_context.hash(DEFAULT_PASSWORD),
                    "nombre_completo": nombre_completo,
                    "rol": RolUsuario.AUDITOR.value,
                    "estado": EstadoUsuario.ACTIVO.value,
                    "sucursal": sucursal.value if sucursal else None,
                },
            )
            print(f"✅ {username} creado (sucursal={sucursal.value if sucursal else '—'})")

        await session.commit()

    print(f"\n🔐 Password temporal para todos: {DEFAULT_PASSWORD} (must_change_password=true)")


if __name__ == "__main__":
    asyncio.run(seed_auditores())
```

- [ ] **Step 2: Run it against the dev DB**

```bash
docker exec incapacidades-api python scripts/seed_auditores.py
```

Expected: 8 lines of `✅ ... creado`, then the password notice. Re-running should print `⏭️  ... ya existe, se omite` for all 8.

- [ ] **Step 3: Verify in the DB**

```bash
docker exec incapacidades-postgres psql -U postgres -d incapacidades -c "SELECT username, sucursal, rol FROM usuario WHERE rol='AUDITOR' ORDER BY username;"
```

Expected: 8 rows, sucursal populated for all except `auditor_default`.

- [ ] **Step 4: Commit**

```bash
git add apps/backend/scripts/seed_auditores.py
git commit -m "chore(seed): add fictitious per-sucursal auditors and auditor_default"
```

---

## Phase 5: Bandeja de Pendientes — Filter by Assigned Auditor

### Task 7: Backend — repository filter, eager load, response schema fields

**Files:**
- Modify: `apps/backend/app/db/repositories/incapacidad_repository.py`
- Modify: `apps/backend/app/services/incapacidad_service.py`
- Modify: `apps/backend/app/schemas/incapacidad.py`
- Modify: `apps/backend/app/api/v1/endpoints/incapacidades.py`
- Test: `apps/backend/tests/test_pendientes_filtro_auditor.py`

**Interfaces:**
- Produces: `incapacidad_repository.listar_pendientes(..., auditor_asignado_id: Optional[UUID] = None)`; `IncapacidadInDB.auditor_asignado_id`; `IncapacidadPendienteResponse.auditor_asignado: Optional[UsuarioSimple]`; `GET /incapacidades/pendientes?auditor_asignado_id=<uuid>`.

- [ ] **Step 1: Write the failing test**

```python
# apps/backend/tests/test_pendientes_filtro_auditor.py
import pytest
from datetime import date, datetime
from app.models.incapacidad import Incapacidad
from app.models.usuario import Usuario
from app.utils.enums import TipoIncapacidad, EstadoIncapacidad, RolUsuario, EstadoUsuario
from app.core.security import get_password_hash
from app.services.incapacidad_service import incapacidad_service


@pytest.mark.asyncio
async def test_listar_pendientes_filters_by_auditor_asignado(db_session, test_empleado, test_empresa):
    auditor_a = Usuario(
        username="test.filtro.a", email="test.filtro.a@segurosalfa-test.com.co",
        password_hash=get_password_hash("Test123!"), nombre_completo="Auditor A",
        rol=RolUsuario.AUDITOR, estado=EstadoUsuario.ACTIVO,
    )
    auditor_b = Usuario(
        username="test.filtro.b", email="test.filtro.b@segurosalfa-test.com.co",
        password_hash=get_password_hash("Test123!"), nombre_completo="Auditor B",
        rol=RolUsuario.AUDITOR, estado=EstadoUsuario.ACTIVO,
    )
    db_session.add_all([auditor_a, auditor_b])
    await db_session.commit()

    inc_a = Incapacidad(
        numero="ARL-FILTRO-A", tipo=TipoIncapacidad.ARL, empleado_id=test_empleado.id,
        empresa_id=test_empresa.id, fecha_inicio=date(2026, 6, 1), fecha_fin=date(2026, 6, 5),
        dias_totales=5, estado=EstadoIncapacidad.EN_AUDITORIA, fecha_radicacion=datetime.utcnow(),
        auditor_asignado_id=auditor_a.id,
    )
    inc_b = Incapacidad(
        numero="ARL-FILTRO-B", tipo=TipoIncapacidad.ARL, empleado_id=test_empleado.id,
        empresa_id=test_empresa.id, fecha_inicio=date(2026, 6, 1), fecha_fin=date(2026, 6, 5),
        dias_totales=5, estado=EstadoIncapacidad.EN_AUDITORIA, fecha_radicacion=datetime.utcnow(),
        auditor_asignado_id=auditor_b.id,
    )
    db_session.add_all([inc_a, inc_b])
    await db_session.commit()

    resultados = await incapacidad_service.listar_pendientes(
        db=db_session, auditor_asignado_id=auditor_a.id
    )

    numeros = {item['incapacidad'].numero for item in resultados}
    assert numeros == {"ARL-FILTRO-A"}
```

- [ ] **Step 2: Run to verify it fails**

Run: `docker exec incapacidades-api python -m pytest tests/test_pendientes_filtro_auditor.py -v --no-cov`
Expected: FAIL — `TypeError: listar_pendientes() got an unexpected keyword argument 'auditor_asignado_id'`

- [ ] **Step 3: Add the filter to the repository**

In `app/db/repositories/incapacidad_repository.py`, `listar_pendientes()` signature, add the parameter:

```python
    async def listar_pendientes(
        self,
        db: AsyncSession,
        tipo: Optional[TipoIncapacidad] = None,
        prioridad: Optional[Prioridad] = None,
        empresa_nit: Optional[str] = None,
        auditor_asignado_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Incapacidad]:
```

Add `selectinload(Incapacidad.auditor_asignado)` to the existing `.options(...)` block, and the filter next to the other optional `if` blocks:

```python
        if auditor_asignado_id:
            query = query.where(Incapacidad.auditor_asignado_id == auditor_asignado_id)
```

- [ ] **Step 4: Pass the parameter through the service**

In `app/services/incapacidad_service.py`, `listar_pendientes()` signature, add `auditor_asignado_id: Optional[UUID] = None` and pass it to `self.repository.listar_pendientes(...)`.

- [ ] **Step 5: Add the schema fields**

In `app/schemas/incapacidad.py`, add to `IncapacidadInDB` (next to the existing `auditado_por_id: Optional[UUID]` line):

```python
    auditor_asignado_id: Optional[UUID]
```

Add to `IncapacidadPendienteResponse` and to `IncapacidadResponse` (next to the existing `auditado_por: Optional["UsuarioSimple"] = None` in `IncapacidadResponse`, and as a new field in `IncapacidadPendienteResponse`):

```python
    auditor_asignado: Optional["UsuarioSimple"] = None
```

- [ ] **Step 6: Pass the query param through the endpoint**

In `app/api/v1/endpoints/incapacidades.py`, `listar_incapacidades_pendientes()`:

```python
    auditor_asignado_id: Optional[UUID] = Query(None, description="Filtrar por auditor asignado"),
```

(add to the function signature, alongside `dias_antiguedad_min`), then pass it through to `incapacidad_service.listar_pendientes(..., auditor_asignado_id=auditor_asignado_id)`, and populate the response field:

```python
        if incap.auditor_asignado:
            incap_dict['auditor_asignado'] = UsuarioSimple.model_validate(incap.auditor_asignado).model_dump()
```

(add next to the existing `if incap.empleado: ...` / `if incap.empresa: ...` block). `UsuarioSimple` is not currently imported in this file — add it to the existing `from app.schemas.incapacidad import (...)` block at the top (the one starting at line 20 with `IncapacidadCreate,` etc.):

```python
    UsuarioSimple,
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `docker exec incapacidades-api python -m pytest tests/test_pendientes_filtro_auditor.py -v --no-cov`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add apps/backend/app/db/repositories/incapacidad_repository.py apps/backend/app/services/incapacidad_service.py apps/backend/app/schemas/incapacidad.py apps/backend/app/api/v1/endpoints/incapacidades.py apps/backend/tests/test_pendientes_filtro_auditor.py
git commit -m "feat(pendientes): filter bandeja by assigned auditor"
```

---

### Task 8: Frontend — auditor filter in the bandeja

**Files:**
- Create: `apps/frontend/sistema-interno/src/services/auditorService.ts`
- Modify: `apps/frontend/sistema-interno/src/types/incapacidad.ts`
- Modify: `apps/frontend/sistema-interno/src/services/incapacidadService.ts`
- Modify: `apps/frontend/sistema-interno/src/components/incapacidades/PendientesFilters.tsx`
- Modify: `apps/frontend/sistema-interno/src/pages/incapacidades/PendientesPage.tsx`
- Test: `apps/frontend/sistema-interno/src/components/incapacidades/__tests__/PendientesFilters.test.tsx`

**Interfaces:**
- Produces: `auditorService.listActivos(): Promise<AuditorOption[]>` (`GET /usuarios?rol=AUDITOR&estado=ACTIVO`); `FiltrosPendientes.auditor_asignado_id?: string`.

- [ ] **Step 1: Create the frontend type additions**

In `src/types/incapacidad.ts`, add to `Incapacidad` (next to the existing `siniestro?: SiniestroBasic | null;` line):

```typescript
  auditor_asignado_id?: string | null;
  auditor_asignado?: { id: string; nombre_completo: string; rol: string } | null;
```

Add to `FiltrosPendientes`:

```typescript
  auditor_asignado_id?: string;
```

- [ ] **Step 2: Create `auditorService.ts`**

```typescript
// apps/frontend/sistema-interno/src/services/auditorService.ts
import api from '@/lib/api';

export interface AuditorOption {
  id: string;
  username: string;
  nombre_completo: string;
  sucursal: string | null;
  incapacidades_asignadas_activas: number;
}

class AuditorService {
  private readonly baseUrl = '/usuarios';

  async listActivos(): Promise<AuditorOption[]> {
    const { data } = await api.get<AuditorOption[]>(this.baseUrl, {
      params: { rol: 'AUDITOR', estado: 'ACTIVO', limit: 100 },
    });
    return data;
  }
}

export const auditorService = new AuditorService();
export default auditorService;
```

- [ ] **Step 3: Write the failing test for the filter select**

```typescript
// apps/frontend/sistema-interno/src/components/incapacidades/__tests__/PendientesFilters.test.tsx
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { PendientesFilters } from '../PendientesFilters';
import { auditorService } from '@/services/auditorService';

vi.mock('@/services/auditorService', () => ({
  auditorService: { listActivos: vi.fn() },
}));

function renderWithClient(ui: React.ReactElement) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe('PendientesFilters — auditor asignado', () => {
  beforeEach(() => {
    vi.mocked(auditorService.listActivos).mockResolvedValue([
      { id: 'aud-1', username: 'auditor.cali', nombre_completo: 'Camila Restrepo Vargas', sucursal: 'Cali', incapacidades_asignadas_activas: 2 },
    ]);
  });

  it('renders an auditor filter populated from auditorService', async () => {
    renderWithClient(<PendientesFilters onSearch={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByLabelText(/auditor asignado/i)).toBeInTheDocument();
    });

    const user = userEvent.setup();
    await user.click(screen.getByLabelText(/auditor asignado/i));
    expect(await screen.findByText('Camila Restrepo Vargas')).toBeInTheDocument();
  });
});
```

- [ ] **Step 4: Run to verify it fails**

Run: `cd apps/frontend/sistema-interno && npm test -- PendientesFilters --run`
Expected: FAIL — no element with label "auditor asignado" exists yet.

- [ ] **Step 5: Add the select to `PendientesFilters.tsx`**

Add the import and a `useQuery` fetch, then a new `<Select>` block. At the top of the file:

```typescript
import { useQuery } from '@tanstack/react-query';
import { auditorService } from '@/services/auditorService';
```

Inside the component, before `return`:

```typescript
  const { data: auditores = [] } = useQuery({
    queryKey: ['auditores-activos'],
    queryFn: () => auditorService.listActivos(),
    staleTime: 5 * 60 * 1000,
  });
```

Add a new filter block inside the `grid` (next to "Antigüedad mínima"):

```tsx
            {/* Auditor asignado */}
            <div className="space-y-2">
              <Label htmlFor="auditor_asignado_id">Auditor asignado</Label>
              <Select
                onValueChange={(value) => setValue('auditor_asignado_id', value === 'ALL' ? undefined : value)}
                defaultValue={watch('auditor_asignado_id')}
              >
                <SelectTrigger id="auditor_asignado_id">
                  <SelectValue placeholder="Todos" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ALL">Todos</SelectItem>
                  {auditores.map((auditor) => (
                    <SelectItem key={auditor.id} value={auditor.id}>
                      {auditor.nombre_completo}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
```

- [ ] **Step 6: Pass the filter through `incapacidadService.listarPendientes`**

In `src/services/incapacidadService.ts`, add `auditor_asignado_id: filtros.auditor_asignado_id` to the `paramsLimpios` object inside `listarPendientes`.

- [ ] **Step 7: Show the assigned auditor in the results table**

In `src/pages/incapacidades/PendientesPage.tsx`, add a column to the `columns` array (before the `actions` column):

```typescript
  {
    accessorKey: 'auditor_asignado',
    header: 'Auditor Asignado',
    cell: ({ row }) => {
      const auditor = row.original.auditor_asignado;
      return auditor ? (
        <span className="text-sm">{auditor.nombre_completo}</span>
      ) : (
        <span className="text-sm text-slate-400">Sin asignar</span>
      );
    },
  },
```

- [ ] **Step 8: Run tests to verify they pass**

Run: `cd apps/frontend/sistema-interno && npm test -- PendientesFilters --run`
Expected: PASS

- [ ] **Step 9: Commit**

```bash
git add apps/frontend/sistema-interno/src/services/auditorService.ts apps/frontend/sistema-interno/src/types/incapacidad.ts apps/frontend/sistema-interno/src/services/incapacidadService.ts apps/frontend/sistema-interno/src/components/incapacidades/PendientesFilters.tsx apps/frontend/sistema-interno/src/pages/incapacidades/PendientesPage.tsx apps/frontend/sistema-interno/src/components/incapacidades/__tests__/PendientesFilters.test.tsx
git commit -m "feat(pendientes): add auditor-asignado filter and column to the bandeja UI"
```

---

## Phase 6: Admin Module — Backend

### Task 9: Add `sucursal` + workload count to Usuario schemas; report endpoint

**Files:**
- Modify: `apps/backend/app/schemas/usuario.py`
- Modify: `apps/backend/app/services/usuario_service.py`
- Modify: `apps/backend/app/api/v1/endpoints/usuarios.py`
- Test: `apps/backend/tests/test_usuario_reporte_auditores.py`

**Interfaces:**
- Produces: `UsuarioService.reporte_auditores(db, admin_rol) -> List[Usuario]`; `GET /usuarios/reporte-auditores` (ADMIN-only, `List[UsuarioListItem]`).

- [ ] **Step 1: Write the failing test**

```python
# apps/backend/tests/test_usuario_reporte_auditores.py
import pytest
from app.core.exceptions import ForbiddenException
from app.utils.enums import RolUsuario, EstadoUsuario, SucursalSiniestro
from app.services.usuario_service import usuario_service


@pytest.mark.asyncio
async def test_reporte_auditores_returns_only_auditores(db_session, test_usuario, test_user_auditor):
    reporte = await usuario_service.reporte_auditores(db_session, admin_rol=RolUsuario.ADMIN)

    usernames = {u.username for u in reporte}
    assert "auditor" in usernames  # test_user_auditor
    assert "testuser" not in usernames  # test_usuario is ADMIN, excluded


@pytest.mark.asyncio
async def test_reporte_auditores_forbidden_for_non_admin():
    with pytest.raises(ForbiddenException):
        await usuario_service.reporte_auditores(None, admin_rol=RolUsuario.AUDITOR)
```

- [ ] **Step 2: Run to verify it fails**

Run: `docker exec incapacidades-api python -m pytest tests/test_usuario_reporte_auditores.py -v --no-cov`
Expected: FAIL — `AttributeError: 'UsuarioService' object has no attribute 'reporte_auditores'`

- [ ] **Step 3: Add `sucursal` + counter fields to schemas**

In `app/schemas/usuario.py`, add the import:

```python
from app.utils.enums import SucursalSiniestro
```

Add to `UsuarioBase` (covers both `UsuarioCreate` and `UsuarioResponse`, which inherit from it):

```python
    sucursal: Optional[SucursalSiniestro] = Field(None, description="Sucursal (solo aplica a rol=AUDITOR)")
```

Add to `UsuarioUpdate`:

```python
    sucursal: Optional[SucursalSiniestro] = None
```

Add to `UsuarioResponse` (the workload counter — read-only, not settable):

```python
    incapacidades_asignadas_activas: int
```

Add to `UsuarioListItem` (both fields, since the admin table and the report both read from this schema):

```python
    sucursal: Optional[SucursalSiniestro] = None
    incapacidades_asignadas_activas: int
```

- [ ] **Step 4: Add the service method**

In `app/services/usuario_service.py`, add after `deactivate_usuario`:

```python
    async def reporte_auditores(
        self,
        db: AsyncSession,
        admin_rol: RolUsuario,
    ) -> List[Usuario]:
        """
        Lista todos los usuarios AUDITOR con su sucursal y carga activa actual.

        Requiere rol ADMIN.
        """
        if admin_rol != RolUsuario.ADMIN:
            raise ForbiddenException("Solo los ADMIN pueden ver el reporte de auditores")

        return await self.repository.list_by_rol(db, RolUsuario.AUDITOR, skip=0, limit=1000)
```

- [ ] **Step 5: Add the endpoint**

In `app/api/v1/endpoints/usuarios.py`, add right after the `GET /me` endpoint and before `GET /{usuario_id}` (route ordering matters — a route registered after `/{usuario_id}` would never match, since FastAPI would try to parse `"reporte-auditores"` as the `usuario_id: UUID` path param first):

```python
@router.get(
    "/reporte-auditores",
    response_model=List[UsuarioListItem],
    summary="Reporte de carga de auditores",
    description="Cantidad de incapacidades actualmente asignadas a cada auditor (solo ADMIN)"
)
async def reporte_auditores(
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Retorna todos los usuarios AUDITOR con su sucursal e incapacidades_asignadas_activas.

    Requiere rol ADMIN.
    """
    return await usuario_service.reporte_auditores(db, admin_rol=current_user.rol)
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `docker exec incapacidades-api python -m pytest tests/test_usuario_reporte_auditores.py -v --no-cov`
Expected: PASS

- [ ] **Step 7: Run the wider usuarios test file to check for regressions**

Run: `docker exec incapacidades-api python -m pytest tests/ -k usuario -v --no-cov`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add apps/backend/app/schemas/usuario.py apps/backend/app/services/usuario_service.py apps/backend/app/api/v1/endpoints/usuarios.py apps/backend/tests/test_usuario_reporte_auditores.py
git commit -m "feat(usuarios): add sucursal field and GET /usuarios/reporte-auditores"
```

---

## Phase 7: Admin Module — Frontend

### Task 10: Extend `auditorService.ts` with CRUD + report

**Files:**
- Modify: `apps/frontend/sistema-interno/src/services/auditorService.ts`

**Interfaces:**
- Produces: `auditorService.create(data)`, `.update(id, data)`, `.deactivate(id)`, `.reporte()`.

- [ ] **Step 1: Extend the service**

```typescript
// apps/frontend/sistema-interno/src/services/auditorService.ts
import api from '@/lib/api';

export interface AuditorOption {
  id: string;
  username: string;
  email: string;
  nombre_completo: string;
  sucursal: string | null;
  incapacidades_asignadas_activas: number;
  estado: string;
}

export interface CreateAuditorData {
  username: string;
  email: string;
  nombre_completo: string;
  password: string;
  sucursal: string | null;
}

export interface UpdateAuditorData {
  nombre_completo?: string;
  email?: string;
  sucursal?: string | null;
}

class AuditorService {
  private readonly baseUrl = '/usuarios';

  async listActivos(): Promise<AuditorOption[]> {
    const { data } = await api.get<AuditorOption[]>(this.baseUrl, {
      params: { rol: 'AUDITOR', estado: 'ACTIVO', limit: 100 },
    });
    return data;
  }

  async listAll(): Promise<AuditorOption[]> {
    const { data } = await api.get<AuditorOption[]>(this.baseUrl, {
      params: { rol: 'AUDITOR', limit: 100 },
    });
    return data;
  }

  async create(payload: CreateAuditorData): Promise<AuditorOption> {
    const { data } = await api.post<AuditorOption>(`${this.baseUrl}/`, {
      ...payload,
      rol: 'AUDITOR',
    });
    return data;
  }

  async update(id: string, payload: UpdateAuditorData): Promise<AuditorOption> {
    const { data } = await api.put<AuditorOption>(`${this.baseUrl}/${id}`, payload);
    return data;
  }

  async deactivate(id: string): Promise<AuditorOption> {
    const { data } = await api.post<AuditorOption>(`${this.baseUrl}/${id}/desactivar`);
    return data;
  }

  async reporte(): Promise<AuditorOption[]> {
    const { data } = await api.get<AuditorOption[]>(`${this.baseUrl}/reporte-auditores`);
    return data;
  }
}

export const auditorService = new AuditorService();
export default auditorService;
```

- [ ] **Step 2: Commit**

```bash
git add apps/frontend/sistema-interno/src/services/auditorService.ts
git commit -m "feat(admin): extend auditorService with create/update/deactivate/reporte"
```

---

### Task 11: `AuditoresPage.tsx` — admin CRUD + workload report

**Files:**
- Create: `apps/frontend/sistema-interno/src/pages/admin/AuditoresPage.tsx`
- Test: `apps/frontend/sistema-interno/src/pages/admin/__tests__/AuditoresPage.test.tsx`
- Modify: `apps/frontend/sistema-interno/src/router/index.tsx`

**Interfaces:**
- Consumes: `auditorService.listAll/create/update/deactivate/reporte` (Task 10).

- [ ] **Step 1: Write the failing test**

```typescript
// apps/frontend/sistema-interno/src/pages/admin/__tests__/AuditoresPage.test.tsx
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuditoresPage } from '../AuditoresPage';
import { auditorService } from '@/services/auditorService';

vi.mock('@/services/auditorService', () => ({
  auditorService: {
    listAll: vi.fn(),
    reporte: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    deactivate: vi.fn(),
  },
}));

function renderWithClient(ui: React.ReactElement) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={client}>{ui}</QueryClientProvider>);
}

describe('AuditoresPage', () => {
  beforeEach(() => {
    vi.mocked(auditorService.listAll).mockResolvedValue([
      {
        id: 'aud-1', username: 'auditor.cali', email: 'camila.restrepo@segurosalfa-test.com.co',
        nombre_completo: 'Camila Restrepo Vargas', sucursal: 'Cali',
        incapacidades_asignadas_activas: 3, estado: 'ACTIVO',
      },
    ]);
    vi.mocked(auditorService.reporte).mockResolvedValue([]);
  });

  it('lists auditors with their sucursal and active workload', async () => {
    renderWithClient(<AuditoresPage />);

    await waitFor(() => {
      expect(screen.getByText('Camila Restrepo Vargas')).toBeInTheDocument();
    });
    expect(screen.getByText('Cali')).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument();
  });

  it('opens the create-auditor dialog', async () => {
    renderWithClient(<AuditoresPage />);

    await waitFor(() => screen.getByText('Camila Restrepo Vargas'));
    screen.getByRole('button', { name: /nuevo auditor/i }).click();

    expect(await screen.findByLabelText(/nombre completo/i)).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run to verify it fails**

Run: `cd apps/frontend/sistema-interno && npm test -- AuditoresPage --run`
Expected: FAIL — `Cannot find module '../AuditoresPage'`

- [ ] **Step 3: Implement the page**

```tsx
// apps/frontend/sistema-interno/src/pages/admin/AuditoresPage.tsx
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from '@/components/ui/table';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogTrigger,
} from '@/components/ui/dialog';
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select';
import { auditorService, type AuditorOption } from '@/services/auditorService';

const SUCURSALES = ['Cali', 'Medellín', 'Cartagena', 'Bogotá'];

interface FormState {
  username: string;
  nombre_completo: string;
  email: string;
  password: string;
  sucursal: string;
}

const emptyForm: FormState = { username: '', nombre_completo: '', email: '', password: '', sucursal: '' };

export function AuditoresPage() {
  const queryClient = useQueryClient();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editing, setEditing] = useState<AuditorOption | null>(null);
  const [form, setForm] = useState<FormState>(emptyForm);

  const { data: auditores = [], isLoading } = useQuery({
    queryKey: ['auditores-admin'],
    queryFn: () => auditorService.listAll(),
  });

  const createMutation = useMutation({
    mutationFn: () => auditorService.create({
      username: form.username,
      email: form.email,
      nombre_completo: form.nombre_completo,
      password: form.password,
      sucursal: form.sucursal || null,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['auditores-admin'] });
      setDialogOpen(false);
      setForm(emptyForm);
    },
  });

  const updateMutation = useMutation({
    mutationFn: () => {
      if (!editing) throw new Error('No hay auditor en edición');
      return auditorService.update(editing.id, {
        nombre_completo: form.nombre_completo,
        email: form.email,
        sucursal: form.sucursal || null,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['auditores-admin'] });
      setDialogOpen(false);
      setEditing(null);
      setForm(emptyForm);
    },
  });

  const deactivateMutation = useMutation({
    mutationFn: (id: string) => auditorService.deactivate(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['auditores-admin'] }),
  });

  const openCreate = () => {
    setEditing(null);
    setForm(emptyForm);
    setDialogOpen(true);
  };

  const openEdit = (auditor: AuditorOption) => {
    setEditing(auditor);
    setForm({
      username: auditor.username,
      nombre_completo: auditor.nombre_completo,
      email: auditor.email,
      password: '',
      sucursal: auditor.sucursal ?? '',
    });
    setDialogOpen(true);
  };

  const handleSubmit = () => {
    if (editing) {
      updateMutation.mutate();
    } else {
      createMutation.mutate();
    }
  };

  return (
    <div className="space-y-4 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Gestión de Auditores</h1>
          <p className="text-slate-500 mt-1">
            Auditores asignados por sucursal y su carga activa de incapacidades.
          </p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button onClick={openCreate}>Nuevo Auditor</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>{editing ? 'Editar Auditor' : 'Nuevo Auditor'}</DialogTitle>
            </DialogHeader>
            <div className="space-y-3">
              {!editing && (
                <div className="space-y-2">
                  <Label htmlFor="username">Username</Label>
                  <Input
                    id="username"
                    value={form.username}
                    onChange={(e) => setForm({ ...form, username: e.target.value })}
                  />
                </div>
              )}
              <div className="space-y-2">
                <Label htmlFor="nombre_completo">Nombre completo</Label>
                <Input
                  id="nombre_completo"
                  value={form.nombre_completo}
                  onChange={(e) => setForm({ ...form, nombre_completo: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  value={form.email}
                  onChange={(e) => setForm({ ...form, email: e.target.value })}
                />
              </div>
              {!editing && (
                <div className="space-y-2">
                  <Label htmlFor="password">Contraseña temporal</Label>
                  <Input
                    id="password"
                    type="password"
                    value={form.password}
                    onChange={(e) => setForm({ ...form, password: e.target.value })}
                  />
                </div>
              )}
              <div className="space-y-2">
                <Label htmlFor="sucursal">Sucursal</Label>
                <Select
                  value={form.sucursal || 'NONE'}
                  onValueChange={(value) => setForm({ ...form, sucursal: value === 'NONE' ? '' : value })}
                >
                  <SelectTrigger id="sucursal">
                    <SelectValue placeholder="Sin sucursal (auditor por defecto)" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="NONE">Sin sucursal</SelectItem>
                    {SUCURSALES.map((s) => (
                      <SelectItem key={s} value={s}>{s}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <DialogFooter>
              <Button
                onClick={handleSubmit}
                disabled={createMutation.isPending || updateMutation.isPending}
              >
                Guardar
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <div className="bg-white rounded-lg shadow">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Nombre</TableHead>
              <TableHead>Email</TableHead>
              <TableHead>Sucursal</TableHead>
              <TableHead>Carga Activa</TableHead>
              <TableHead>Estado</TableHead>
              <TableHead>Acciones</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {!isLoading && auditores.map((auditor) => (
              <TableRow key={auditor.id}>
                <TableCell className="font-medium">{auditor.nombre_completo}</TableCell>
                <TableCell>{auditor.email}</TableCell>
                <TableCell>{auditor.sucursal ?? <span className="text-slate-400">—</span>}</TableCell>
                <TableCell>{auditor.incapacidades_asignadas_activas}</TableCell>
                <TableCell>
                  <Badge variant={auditor.estado === 'ACTIVO' ? 'default' : 'secondary'}>
                    {auditor.estado}
                  </Badge>
                </TableCell>
                <TableCell className="space-x-2">
                  <Button variant="outline" size="sm" onClick={() => openEdit(auditor)}>Editar</Button>
                  {auditor.estado === 'ACTIVO' && (
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={() => deactivateMutation.mutate(auditor.id)}
                    >
                      Desactivar
                    </Button>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm text-blue-800">
        <strong>Pendiente:</strong> el módulo de reasignación de incapacidades entre auditores
        no está implementado en esta iteración.
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Wire the route**

In `src/router/index.tsx`, replace the `/usuarios` placeholder:

```typescript
import { AuditoresPage } from '@/pages/admin/AuditoresPage';
```

```tsx
          // Usuarios (Gestión de Auditores) - Solo ADMIN
          {
            path: '/usuarios',
            element: <ProtectedRoute allowedRoles={[RolUsuario.ADMIN]} />,
            children: [
              {
                index: true,
                element: <AuditoresPage />,
              },
            ],
          },
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd apps/frontend/sistema-interno && npm test -- AuditoresPage --run`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add apps/frontend/sistema-interno/src/pages/admin/AuditoresPage.tsx apps/frontend/sistema-interno/src/pages/admin/__tests__/AuditoresPage.test.tsx apps/frontend/sistema-interno/src/router/index.tsx
git commit -m "feat(admin): add AuditoresPage — CRUD + workload table, wired at /usuarios"
```

---

## Self-Review Notes

- **Spec coverage**: every section of `docs/superpowers/specs/2026-07-25-asignacion-auditoria-sucursal-design.md` maps to a task: data model → Task 1; siniestro date filter → Task 2; assignment algorithm → Tasks 3–4; counter sync → Task 5; seed → Task 6; bandeja filter → Tasks 7–8; admin module → Tasks 9–11.
- **Known, documented gap** (not a bug to fix here): `pre_incapacidad_promotion_service.py`'s RADICADA→EN_AUDITORIA path bypasses `auditoria_service.auditar_incapacidad()` and therefore won't get an assigned auditor. Flagged in Task 4's note. If this turns out to matter in practice, it's a follow-up plan, not a silent scope expansion of this one.
- **Reassignment-of-incapacidades module**: explicitly out of scope per the source requirement ("pendiente aplicación") — Task 11 renders a visible placeholder note instead of a fake/disabled control.

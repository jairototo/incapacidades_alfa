# RBAC + Empresa↔Usuario + Analítica + Carga Masiva (Backend) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Lock down Empresas/Empleados endpoints by role, auto-provision a login (Usuario) when an Empresa is created, add a server-aggregated analytics endpoint for two dashboard charts, and add an Excel dry-run/confirm bulk-upload flow for Empleados.

**Architecture:** FastAPI endpoints → services → repositories → SQLAlchemy async models, exactly as the rest of the backend is structured. RBAC reuses the existing `PermissionChecker`/`Permissions` mechanism (no new auth system). Empresa↔Usuario creation is one DB transaction using the repositories' existing `create_flushed`/`update_flushed` (flush-not-commit) methods, committed once at the end of the service call.

**Tech Stack:** FastAPI, SQLAlchemy 2.0 async, Pydantic v2, Alembic, openpyxl, pytest + pytest-asyncio (async-native, `asyncio_mode=auto`).

## Global Constraints

- Spec: `docs/superpowers/specs/2026-07-27-rbac-empresas-empleados-backend-design.md` — every task below implements one numbered section of that spec; cite the section in commit messages where useful.
- Run backend tests via `docker exec incapacidades-api pytest <path> -v` (the API runs in Docker; do not run pytest on the host). Only run the test file(s) touched by the current task, not the full suite, unless a task says otherwise.
- Reuse existing exceptions from `app/core/exceptions.py` (`DuplicateException`, `NotFoundException`, `ForbiddenException`, `BadRequestException`) — never raise raw `HTTPException`.
- Reuse `BaseRepository.create_flushed`/`update_flushed` for any multi-row transaction; `create`/`update` (which auto-commit) are only for single-row, single-statement operations.
- No new columns/migrations beyond the one explicit data-migration task (Task 7) — `Usuario.empresa_id` and `Usuario.must_change_password` already exist.
- `RolUsuario.LIQUIDADOR` does not exist yet in `app/utils/enums.py` — despite being referenced throughout the original requirements and CLAUDE.md's role table, it was never added to the codebase. Task 1 adds it. Since `Usuario.rol` is a plain `String(50)` column (not a Postgres native enum type), this needs **no migration**.
- Money/decimal handling: `salario_base` is `Decimal`, matching `Empleado.salario_base: Mapped[Optional[Decimal]]`.
- Banking fields (`cuenta_bancaria`, `banco`, `tipo_cuenta`) stay on the `Empleado` model but are excluded from every creation path touched by this plan (individual `EmpleadoCreate` already has them optional and unrelated to this plan; bulk upload never asks for them).

---

### Task 1: Add `RolUsuario.LIQUIDADOR` and its permission set

**Files:**
- Modify: `app/utils/enums.py:87-94` (`RolUsuario`)
- Modify: `app/core/security.py:239-280` (`PermissionChecker.PERMISSIONS`)
- Test: `tests/unit/test_permission_checker_liquidador.py`

**Interfaces:**
- Produces: `RolUsuario.LIQUIDADOR` (value `"LIQUIDADOR"`), and `PermissionChecker.PERMISSIONS["LIQUIDADOR"]` — consumed by Tasks 2 and 3.

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_permission_checker_liquidador.py
"""LIQUIDADOR role: read-only on Empresas and Empleados, no write permissions."""
from app.core.security import PermissionChecker
from app.utils.enums import RolUsuario


def test_liquidador_role_exists():
    assert RolUsuario.LIQUIDADOR == "LIQUIDADOR"


def test_liquidador_has_read_permissions():
    assert PermissionChecker.has_permission("LIQUIDADOR", "ver_empresa")
    assert PermissionChecker.has_permission("LIQUIDADOR", "ver_empleado")


def test_liquidador_has_no_write_permissions():
    assert not PermissionChecker.has_permission("LIQUIDADOR", "crear_empresa")
    assert not PermissionChecker.has_permission("LIQUIDADOR", "editar_empresa")
    assert not PermissionChecker.has_permission("LIQUIDADOR", "eliminar_empresa")
    assert not PermissionChecker.has_permission("LIQUIDADOR", "crear_empleado")
    assert not PermissionChecker.has_permission("LIQUIDADOR", "editar_empleado")
    assert not PermissionChecker.has_permission("LIQUIDADOR", "eliminar_empleado")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `docker exec incapacidades-api pytest tests/unit/test_permission_checker_liquidador.py -v`
Expected: FAIL — `AttributeError: LIQUIDADOR` (enum member doesn't exist yet).

- [ ] **Step 3: Add the enum value and permission set**

In `app/utils/enums.py`, in `RolUsuario`:

```python
class RolUsuario(str, Enum):
    """Roles de usuario."""
    ADMIN = "ADMIN"
    AUDITOR = "AUDITOR"
    APROBADOR = "APROBADOR"
    EMPRESA = "EMPRESA"
    EMPLEADO = "EMPLEADO"
    READONLY = "READONLY"
    LIQUIDADOR = "LIQUIDADOR"
```

In `app/core/security.py`, add a `"LIQUIDADOR"` key to `PermissionChecker.PERMISSIONS` (insert after the `"APROBADOR"` block):

```python
        "LIQUIDADOR": [
            "ver_empresa", "ver_empleado",
            "ver_reportes"
        ],
```

- [ ] **Step 4: Run test to verify it passes**

Run: `docker exec incapacidades-api pytest tests/unit/test_permission_checker_liquidador.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/utils/enums.py app/core/security.py tests/unit/test_permission_checker_liquidador.py
git commit -m "feat: add LIQUIDADOR role with read-only Empresa/Empleado permissions"
```

---

### Task 2: RBAC on `empresas.py` endpoints

**Files:**
- Modify: `app/api/v1/endpoints/empresas.py`
- Test: `tests/unit/test_rbac_empresas.py`

**Interfaces:**
- Consumes: `PermissionChecker`, `Permissions` from `app/core/security.py` (existing); `RolUsuario.LIQUIDADOR` from Task 1.
- Produces: every `empresas.py` route now 403s for roles outside the matrix — consumed by Task 4/5/6's new routes (they must follow the same gating pattern) and by the frontend spec (permission map must mirror this).

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_rbac_empresas.py
"""RBAC on /api/v1/empresas/*: read = ADMIN/AUDITOR/LIQUIDADOR, write = ADMIN only."""
import pytest
from httpx import AsyncClient

from app.core.security import create_access_token, get_password_hash
from app.models.usuario import Usuario
from app.utils.enums import RolUsuario, EstadoUsuario


async def _headers_for(db_session, rol: RolUsuario, username: str) -> dict:
    usuario = Usuario(
        username=username,
        email=f"{username}@example.com",
        password_hash=get_password_hash("Test1234"),
        nombre_completo=f"Test {rol.value}",
        rol=rol,
        estado=EstadoUsuario.ACTIVO,
    )
    db_session.add(usuario)
    await db_session.commit()
    await db_session.refresh(usuario)
    token = create_access_token(data={"sub": str(usuario.id), "token_version": usuario.token_version})
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
@pytest.mark.parametrize("rol", [RolUsuario.ADMIN, RolUsuario.AUDITOR, RolUsuario.LIQUIDADOR])
async def test_read_empresas_allowed_for_read_roles(client: AsyncClient, db_session, rol):
    headers = await _headers_for(db_session, rol, f"user_{rol.value.lower()}")
    resp = await client.get("/api/v1/empresas/", headers=headers)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_read_empresas_forbidden_unauthenticated(client: AsyncClient):
    resp = await client.get("/api/v1/empresas/")
    assert resp.status_code == 401


@pytest.mark.asyncio
@pytest.mark.parametrize("rol", [RolUsuario.AUDITOR, RolUsuario.LIQUIDADOR])
async def test_create_empresa_forbidden_for_non_admin(client: AsyncClient, db_session, rol):
    headers = await _headers_for(db_session, rol, f"writer_{rol.value.lower()}")
    resp = await client.post(
        "/api/v1/empresas/",
        headers=headers,
        json={
            "nit": "900999999",
            "razon_social": "Empresa RBAC Test",
            "email_contacto": "rbac@empresa.com",
        },
    )
    assert resp.status_code == 403
```

- [ ] **Step 2: Run test to verify it fails**

Run: `docker exec incapacidades-api pytest tests/unit/test_rbac_empresas.py -v`
Expected: FAIL — all requests currently return 200/201 (no gating), so `test_create_empresa_forbidden_for_non_admin` and `test_read_empresas_forbidden_unauthenticated` fail.

- [ ] **Step 3: Add RBAC dependencies to every endpoint**

In `app/api/v1/endpoints/empresas.py`, add imports:

```python
from app.core.security import get_current_user, PermissionChecker, Permissions
```

(`get_current_user` is already imported; add `PermissionChecker, Permissions` alongside it.)

Add `dependencies=[Depends(PermissionChecker([Permissions.X]))]` to each route decorator:

- `create_empresa` (`POST /`): `Permissions.EMPRESA_CREATE`
- `list_empresas` (`GET /`): `Permissions.EMPRESA_READ`
- `get_empresa` (`GET /{empresa_id}`): `Permissions.EMPRESA_READ`
- `update_empresa` (`PUT /{empresa_id}`): `Permissions.EMPRESA_UPDATE`
- `delete_empresa` (`DELETE /{empresa_id}`): `Permissions.EMPRESA_DELETE`
- `activate_empresa` (`POST /{empresa_id}/activate`): `Permissions.EMPRESA_UPDATE`
- `deactivate_empresa` (`POST /{empresa_id}/deactivate`): `Permissions.EMPRESA_UPDATE`
- `get_empresa_incapacidades` (`GET /{empresa_id}/incapacidades`): `Permissions.EMPRESA_READ`

`get_empresa_empleados` (`GET /{empresa_id}/empleados`) already has `current_user: Usuario = Depends(get_current_user)` for its manual EMPRESA-scoping check — add `Permissions.EMPLEADO_READ` gating alongside it (it returns Empleado data, so it should require empleado-read, not empresa-read):

```python
@router.get(
    "/{empresa_id}/empleados",
    response_model=List[EmpleadoListItem],
    summary="Obtener empleados de la empresa",
    description="...",
    dependencies=[Depends(PermissionChecker([Permissions.EMPLEADO_READ]))],
)
async def get_empresa_empleados(
    ...
```

Example of the pattern for one route (`create_empresa`):

```python
@router.post(
    "/",
    response_model=EmpresaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear empresa",
    description="Crear una nueva empresa con validación de NIT y razón social únicos",
    dependencies=[Depends(PermissionChecker([Permissions.EMPRESA_CREATE]))],
)
async def create_empresa(
    empresa_in: EmpresaCreate,
    db: AsyncSession = Depends(get_db)
) -> EmpresaResponse:
```

Apply the same `dependencies=[...]` addition to the other six routes listed above, each with its own permission constant.

- [ ] **Step 4: Run test to verify it passes**

Run: `docker exec incapacidades-api pytest tests/unit/test_rbac_empresas.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/api/v1/endpoints/empresas.py tests/unit/test_rbac_empresas.py
git commit -m "feat: gate empresas endpoints by role (ADMIN write, ADMIN/AUDITOR/LIQUIDADOR read)"
```

---

### Task 3: RBAC on `empleados.py` endpoints

**Files:**
- Modify: `app/api/v1/endpoints/empleados.py`
- Test: `tests/unit/test_rbac_empleados.py`

**Interfaces:**
- Consumes: same as Task 2.
- Produces: every `empleados.py` route now requires auth + role; every handler now has `current_user: Usuario = Depends(get_current_user)` available (none did before) — consumed by Tasks 9-11's new routes on the same router.

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_rbac_empleados.py
"""RBAC on /api/v1/empleados/*: read = ADMIN/AUDITOR/LIQUIDADOR, write = ADMIN/AUDITOR only."""
import pytest
from httpx import AsyncClient

from app.core.security import create_access_token, get_password_hash
from app.models.usuario import Usuario
from app.utils.enums import RolUsuario, EstadoUsuario


async def _headers_for(db_session, rol: RolUsuario, username: str) -> dict:
    usuario = Usuario(
        username=username,
        email=f"{username}@example.com",
        password_hash=get_password_hash("Test1234"),
        nombre_completo=f"Test {rol.value}",
        rol=rol,
        estado=EstadoUsuario.ACTIVO,
    )
    db_session.add(usuario)
    await db_session.commit()
    await db_session.refresh(usuario)
    token = create_access_token(data={"sub": str(usuario.id), "token_version": usuario.token_version})
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
@pytest.mark.parametrize("rol", [RolUsuario.ADMIN, RolUsuario.AUDITOR, RolUsuario.LIQUIDADOR])
async def test_read_empleados_allowed_for_read_roles(client: AsyncClient, db_session, rol):
    headers = await _headers_for(db_session, rol, f"eread_{rol.value.lower()}")
    resp = await client.get("/api/v1/empleados/", headers=headers)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_read_empleados_forbidden_unauthenticated(client: AsyncClient):
    resp = await client.get("/api/v1/empleados/")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_create_empleado_forbidden_for_liquidador(client: AsyncClient, db_session, test_empresa):
    headers = await _headers_for(db_session, RolUsuario.LIQUIDADOR, "liquidador_writer")
    resp = await client.post(
        "/api/v1/empleados/",
        headers=headers,
        json={
            "empresa_id": str(test_empresa.id),
            "numero_documento": "1112223334",
            "tipo_documento": "CC",
            "nombres": "Test",
            "apellidos": "Empleado",
            "fecha_ingreso": "2024-01-01",
        },
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_create_empleado_allowed_for_auditor(client: AsyncClient, db_session, test_empresa):
    headers = await _headers_for(db_session, RolUsuario.AUDITOR, "auditor_writer")
    resp = await client.post(
        "/api/v1/empleados/",
        headers=headers,
        json={
            "empresa_id": str(test_empresa.id),
            "numero_documento": "1112223335",
            "tipo_documento": "CC",
            "nombres": "Test",
            "apellidos": "Empleado",
            "fecha_ingreso": "2024-01-01",
        },
    )
    assert resp.status_code == 201
```

(`test_empresa` fixture already exists in `tests/conftest.py`.)

- [ ] **Step 2: Run test to verify it fails**

Run: `docker exec incapacidades-api pytest tests/unit/test_rbac_empleados.py -v`
Expected: FAIL — `test_read_empleados_forbidden_unauthenticated` and `test_create_empleado_forbidden_for_liquidador` fail (currently no gating at all).

- [ ] **Step 3: Add RBAC dependencies and `current_user` to every endpoint**

In `app/api/v1/endpoints/empleados.py`, add import:

```python
from app.core.security import get_current_user, PermissionChecker, Permissions
from app.models.usuario import Usuario
```

Add `dependencies=[Depends(PermissionChecker([Permissions.X]))]` to each route:

- `create_empleado` (`POST /`): `Permissions.EMPLEADO_CREATE`
- `list_empleados` (`GET /`): `Permissions.EMPLEADO_READ`
- `get_empleado` (`GET /{empleado_id}`): `Permissions.EMPLEADO_READ`
- `update_empleado` (`PUT /{empleado_id}`): `Permissions.EMPLEADO_UPDATE`
- `delete_empleado` (`DELETE /{empleado_id}`): `Permissions.EMPLEADO_DELETE`
- `activate_empleado` (`POST /{empleado_id}/activate`): `Permissions.EMPLEADO_UPDATE`
- `deactivate_empleado` (`POST /{empleado_id}/deactivate`): `Permissions.EMPLEADO_UPDATE`
- `get_incapacidades_empleado` (`GET /{empleado_id}/incapacidades`): `Permissions.EMPLEADO_READ`

None of these handlers currently take `current_user` — leave the signatures as-is for this task (no handler body needs the user yet); the `dependencies=[...]` gate is enough. Example for `create_empleado`:

```python
@router.post(
    "/",
    response_model=EmpleadoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear empleado",
    description="Crea un nuevo empleado con validaciones de negocio",
    dependencies=[Depends(PermissionChecker([Permissions.EMPLEADO_CREATE]))],
)
async def create_empleado(
    empleado_data: EmpleadoCreate,
    db: AsyncSession = Depends(get_db)
):
```

Apply the same `dependencies=[...]` line to the other six routes with their respective permission constants.

- [ ] **Step 4: Run test to verify it passes**

Run: `docker exec incapacidades-api pytest tests/unit/test_rbac_empleados.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/api/v1/endpoints/empleados.py tests/unit/test_rbac_empleados.py
git commit -m "feat: gate empleados endpoints by role (ADMIN/AUDITOR write, +LIQUIDADOR read)"
```

---

### Task 4: `POST /empresas` creates a linked Usuario atomically

**Files:**
- Modify: `app/schemas/empresa.py`
- Modify: `app/services/empresa_service.py`
- Modify: `app/api/v1/endpoints/empresas.py`
- Test: `tests/unit/test_empresa_usuario_creation.py`

**Interfaces:**
- Consumes: `usuario_repository.get_by_email`, `usuario_repository.create_flushed` (`app/db/repositories/usuario_repository.py`, `app/db/repositories/base_repository.py`); `usuario_service._generate_temp_password()` (`app/services/usuario_service.py:75`); `get_password_hash` (`app/core/security.py:44`).
- Produces: `EmpresaService.create_empresa(db, empresa_in) -> tuple[Empresa, dict]` where `dict` is `{"username": str, "password": str}` — the tuple shape is consumed directly by the endpoint in this task; no other task calls this method.
- Produces: `EmpresaCreate.email_contacto` is now **required** (was optional) — the frontend spec (written later) must treat it as a required form field.

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_empresa_usuario_creation.py
"""POST /empresas atomically creates a linked Usuario with a generated password."""
import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models.usuario import Usuario
from app.models.empresa import Empresa
from app.utils.enums import RolUsuario


@pytest.mark.asyncio
async def test_create_empresa_also_creates_usuario(client: AsyncClient, db_session, admin_token_headers):
    resp = await client.post(
        "/api/v1/empresas/",
        headers=admin_token_headers,
        json={
            "nit": "900555555",
            "razon_social": "Empresa Con Usuario SAS",
            "email_contacto": "contacto@conusuario.com",
        },
    )
    assert resp.status_code == 201
    body = resp.json()

    # Response includes the generated credentials exactly once, here.
    assert body["usuario_generado"]["username"] == "900555555"
    assert len(body["usuario_generado"]["password"]) >= 8

    result = await db_session.execute(
        select(Usuario).where(Usuario.empresa_id == body["id"])
    )
    usuario = result.scalar_one()
    assert usuario.username == "900555555"
    assert usuario.email == "contacto@conusuario.com"
    assert usuario.rol == RolUsuario.EMPRESA
    assert usuario.must_change_password is False


@pytest.mark.asyncio
async def test_create_empresa_duplicate_email_rejected(client: AsyncClient, db_session, admin_token_headers):
    # Create a Usuario with a given email directly, to simulate an already-taken login.
    from app.models.usuario import Usuario as UsuarioModel
    from app.utils.enums import EstadoUsuario
    from app.core.security import get_password_hash

    db_session.add(UsuarioModel(
        username="existing",
        email="ocupado@empresa.com",
        password_hash=get_password_hash("Test1234"),
        nombre_completo="Existing User",
        rol=RolUsuario.EMPRESA,
        estado=EstadoUsuario.ACTIVO,
    ))
    await db_session.commit()

    resp = await client.post(
        "/api/v1/empresas/",
        headers=admin_token_headers,
        json={
            "nit": "900666666",
            "razon_social": "Otra Empresa SAS",
            "email_contacto": "ocupado@empresa.com",
        },
    )
    assert resp.status_code == 409

    # No orphaned Empresa left behind.
    result = await db_session.execute(select(Empresa).where(Empresa.nit == "900666666"))
    assert result.scalar_one_or_none() is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `docker exec incapacidades-api pytest tests/unit/test_empresa_usuario_creation.py -v`
Expected: FAIL — `KeyError: 'usuario_generado'` (endpoint doesn't return it yet, no Usuario is created).

- [ ] **Step 3: Add `usuario_generado` schema, require `email_contacto`, implement atomic creation**

In `app/schemas/empresa.py`, make `email_contacto` required on `EmpresaCreate` and add the new response schemas:

```python
class EmpresaCreate(EmpresaBase):
    """Schema para crear una empresa."""
    email_contacto: EmailStr = Field(..., description="Email de contacto de la empresa; también será el login del usuario-empresa generado")
    sync_source: Optional[str] = Field(None, description="Fuente de sincronización")
    external_id: Optional[str] = Field(None, max_length=100, description="ID externo")
```

Add at the end of the file:

```python
class UsuarioGenerado(BaseModel):
    """Credenciales generadas al crear/regenerar el usuario-empresa. Se devuelven una sola vez."""
    username: str
    password: str


class EmpresaCreateResponse(EmpresaResponse):
    """Respuesta de creación de empresa, incluye las credenciales generadas una única vez."""
    usuario_generado: UsuarioGenerado
```

In `app/services/empresa_service.py`, add imports:

```python
from app.core.security import get_password_hash
from app.db.repositories.usuario_repository import usuario_repository
from app.services.usuario_service import usuario_service
from app.utils.enums import RolUsuario, EstadoUsuario
```

Replace the body of `create_empresa` (keep the existing NIT/razón-social/format checks, add the email check, and change the creation + return):

```python
    async def create_empresa(
        self,
        db: AsyncSession,
        empresa_in: EmpresaCreate
    ) -> tuple[Empresa, dict]:
        """
        Crear una nueva empresa junto con su usuario de login (transacción única).

        Valida:
        - NIT único
        - Razón social única
        - Tipo de empresa válido
        - email_contacto no está en uso por otro Usuario

        Returns:
            Tupla (Empresa creada, {"username": ..., "password": ...})

        Raises:
            DuplicateException: Si NIT, razón social o email ya existen
            ValidationException: Si los datos son inválidos
        """
        existing_nit = await self.repository.get_by_nit(db, empresa_in.nit)
        if existing_nit:
            logger.warning(f"Intento de crear empresa con NIT duplicado: {empresa_in.nit}")
            raise DuplicateException(
                f"Ya existe una empresa con NIT {empresa_in.nit}"
            )

        existing_razon = await self.repository.get_by_razon_social(
            db, empresa_in.razon_social
        )
        if existing_razon:
            logger.warning(
                f"Intento de crear empresa con razón social duplicada: {empresa_in.razon_social}"
            )
            raise DuplicateException(
                f"Ya existe una empresa con razón social '{empresa_in.razon_social}'"
            )

        existing_user = await usuario_repository.get_by_email(db, empresa_in.email_contacto)
        if existing_user:
            raise DuplicateException(
                f"El correo '{empresa_in.email_contacto}' ya está en uso por otro usuario"
            )

        self._validate_nit_format(empresa_in.nit)

        if empresa_in.tipo_empresa:
            self._validate_tipo_empresa(empresa_in.tipo_empresa)

        empresa_data = empresa_in.model_dump()
        empresa = await self.repository.create_flushed(db, empresa_data)

        temp_password = usuario_service._generate_temp_password()
        usuario_dict = {
            "username": empresa.nit,
            "email": empresa.email_contacto,
            "password_hash": get_password_hash(temp_password),
            "nombre_completo": empresa.razon_social,
            "rol": RolUsuario.EMPRESA,
            "estado": EstadoUsuario.ACTIVO,
            "empresa_id": empresa.id,
            "must_change_password": False,
        }
        await usuario_repository.create_flushed(db, usuario_dict)

        await db.commit()
        await db.refresh(empresa)

        logger.info(
            f"Empresa creada exitosamente: {empresa.id} - "
            f"NIT: {empresa.nit}, Razón Social: {empresa.razon_social}"
        )

        return empresa, {"username": empresa.nit, "password": temp_password}
```

In `app/api/v1/endpoints/empresas.py`, update the import and the `create_empresa` route:

```python
from app.schemas.empresa import (
    EmpresaCreate,
    EmpresaUpdate,
    EmpresaResponse,
    EmpresaCreateResponse,
    EmpresaListItem
)
```

```python
@router.post(
    "/",
    response_model=EmpresaCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear empresa",
    description="Crear una nueva empresa con validación de NIT y razón social únicos; genera un usuario de login para la empresa",
    dependencies=[Depends(PermissionChecker([Permissions.EMPRESA_CREATE]))],
)
async def create_empresa(
    empresa_in: EmpresaCreate,
    db: AsyncSession = Depends(get_db)
) -> EmpresaCreateResponse:
    logger.info(f"Solicitud de creación de empresa: NIT {empresa_in.nit}")

    empresa, usuario_generado = await empresa_service.create_empresa(db, empresa_in)

    return EmpresaCreateResponse(
        **EmpresaResponse.model_validate(empresa).model_dump(),
        usuario_generado=usuario_generado,
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `docker exec incapacidades-api pytest tests/unit/test_empresa_usuario_creation.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/schemas/empresa.py app/services/empresa_service.py app/api/v1/endpoints/empresas.py tests/unit/test_empresa_usuario_creation.py
git commit -m "feat: creating an Empresa now provisions a linked Usuario atomically"
```

---

### Task 5: `PATCH /empresas/{id}` keeps `email_contacto` and `Usuario.email` in sync

**Files:**
- Modify: `app/db/repositories/usuario_repository.py`
- Modify: `app/services/empresa_service.py`
- Test: `tests/unit/test_empresa_email_sync.py`

**Interfaces:**
- Consumes: `Task 4`'s creation flow (tests need an Empresa with a linked Usuario, created via the real `POST /empresas` endpoint, not the old fixture).
- Produces: `usuario_repository.get_by_empresa_id(db, empresa_id) -> Optional[Usuario]` — consumed by Task 6.

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_empresa_email_sync.py
"""PATCH /empresas/{id}: editing email_contacto updates the linked Usuario.email too."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_update_email_contacto_syncs_usuario_email(client: AsyncClient, admin_token_headers):
    create_resp = await client.post(
        "/api/v1/empresas/",
        headers=admin_token_headers,
        json={
            "nit": "900777777",
            "razon_social": "Empresa Sync SAS",
            "email_contacto": "viejo@sync.com",
        },
    )
    empresa_id = create_resp.json()["id"]

    update_resp = await client.put(
        f"/api/v1/empresas/{empresa_id}",
        headers=admin_token_headers,
        json={"email_contacto": "nuevo@sync.com"},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["email_contacto"] == "nuevo@sync.com"

    me_check = await client.post(
        "/api/v1/empresas/",
        headers=admin_token_headers,
        json={
            "nit": "900788888",
            "razon_social": "Otra Empresa SAS",
            "email_contacto": "nuevo@sync.com",
        },
    )
    # "nuevo@sync.com" is now the first empresa's login — creating a second
    # empresa with the same email must be rejected.
    assert me_check.status_code == 409


@pytest.mark.asyncio
async def test_update_email_contacto_conflict_with_other_empresa(client: AsyncClient, admin_token_headers):
    await client.post(
        "/api/v1/empresas/",
        headers=admin_token_headers,
        json={"nit": "900800001", "razon_social": "Empresa A", "email_contacto": "a@dup.com"},
    )
    resp_b = await client.post(
        "/api/v1/empresas/",
        headers=admin_token_headers,
        json={"nit": "900800002", "razon_social": "Empresa B", "email_contacto": "b@dup.com"},
    )
    empresa_b_id = resp_b.json()["id"]

    update_resp = await client.put(
        f"/api/v1/empresas/{empresa_b_id}",
        headers=admin_token_headers,
        json={"email_contacto": "a@dup.com"},
    )
    assert update_resp.status_code == 409
```

- [ ] **Step 2: Run test to verify it fails**

Run: `docker exec incapacidades-api pytest tests/unit/test_empresa_email_sync.py -v`
Expected: FAIL — email uniqueness isn't checked on update, and `Usuario.email` isn't updated, so both `409` assertions fail (both return 200/201).

- [ ] **Step 3: Add `get_by_empresa_id` and sync logic**

In `app/db/repositories/usuario_repository.py`, add:

```python
    async def get_by_empresa_id(
        self,
        db: AsyncSession,
        empresa_id
    ) -> Optional[Usuario]:
        """
        Obtiene el usuario de rol EMPRESA vinculado a una empresa.

        Args:
            db: Sesión de base de datos
            empresa_id: UUID de la empresa

        Returns:
            Usuario si existe, None si no
        """
        query = select(Usuario).where(
            and_(Usuario.empresa_id == empresa_id, Usuario.rol == RolUsuario.EMPRESA)
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()
```

(`and_` is already imported at the top of the file; `RolUsuario` needs adding to the existing `from app.utils.enums import RolUsuario, EstadoUsuario` import — it's already there.)

In `app/services/empresa_service.py`, update `update_empresa` — insert the email-uniqueness check after the existing razón-social check, and sync the linked Usuario after the empresa update:

```python
        # Validar razón social única si se está actualizando
        if 'razon_social' in update_data and update_data['razon_social'] != empresa.razon_social:
            existing = await self.repository.get_by_razon_social(
                db, update_data['razon_social']
            )
            if existing and existing.id != empresa_id:
                raise DuplicateException(
                    f"Ya existe una empresa con razón social '{update_data['razon_social']}'"
                )

        # Validar email único (contra Usuario.email) si se está actualizando
        if 'email_contacto' in update_data and update_data['email_contacto'] != empresa.email_contacto:
            existing_user = await usuario_repository.get_by_email(db, update_data['email_contacto'])
            if existing_user and existing_user.empresa_id != empresa_id:
                raise DuplicateException(
                    f"El correo '{update_data['email_contacto']}' ya está en uso por otro usuario"
                )
```

And after `updated_empresa = await self.repository.update(...)`, before the `return`:

```python
        if 'email_contacto' in update_data:
            linked_user = await usuario_repository.get_by_empresa_id(db, empresa_id)
            if linked_user:
                await usuario_repository.update(
                    db, id=linked_user.id, obj_in={'email': update_data['email_contacto']}
                )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `docker exec incapacidades-api pytest tests/unit/test_empresa_email_sync.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/db/repositories/usuario_repository.py app/services/empresa_service.py tests/unit/test_empresa_email_sync.py
git commit -m "feat: keep Empresa.email_contacto and linked Usuario.email in sync, enforce uniqueness"
```

---

### Task 6: Regenerate the empresa-user's password

**Files:**
- Modify: `app/services/empresa_service.py`
- Modify: `app/api/v1/endpoints/empresas.py`
- Test: `tests/unit/test_empresa_regenerar_password.py`

**Interfaces:**
- Consumes: `usuario_repository.get_by_empresa_id` (Task 5), `usuario_repository.increment_token_version` (existing, `app/db/repositories/usuario_repository.py:207`).
- Produces: `EmpresaService.regenerar_password(db, empresa_id) -> dict` (`{"username": str, "password": str}`) — no other task consumes this.

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_empresa_regenerar_password.py
"""POST /empresas/{id}/regenerar-password: new password, old sessions invalidated."""
import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models.usuario import Usuario


@pytest.mark.asyncio
async def test_regenerar_password_returns_new_credentials_and_bumps_token_version(
    client: AsyncClient, db_session, admin_token_headers
):
    create_resp = await client.post(
        "/api/v1/empresas/",
        headers=admin_token_headers,
        json={
            "nit": "900900001",
            "razon_social": "Empresa Regen SAS",
            "email_contacto": "regen@empresa.com",
        },
    )
    empresa_id = create_resp.json()["id"]
    old_password = create_resp.json()["usuario_generado"]["password"]

    result = await db_session.execute(select(Usuario).where(Usuario.empresa_id == empresa_id))
    usuario_before = result.scalar_one()
    token_version_before = usuario_before.token_version

    regen_resp = await client.post(
        f"/api/v1/empresas/{empresa_id}/regenerar-password",
        headers=admin_token_headers,
    )
    assert regen_resp.status_code == 200
    body = regen_resp.json()
    assert body["username"] == "900900001"
    assert body["password"] != old_password

    await db_session.refresh(usuario_before)
    assert usuario_before.token_version == token_version_before + 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `docker exec incapacidades-api pytest tests/unit/test_empresa_regenerar_password.py -v`
Expected: FAIL — `404 Not Found` (route doesn't exist yet).

- [ ] **Step 3: Add the service method and endpoint**

In `app/services/empresa_service.py`, add a new method (after `update_empresa`):

```python
    async def regenerar_password(self, db: AsyncSession, empresa_id: UUID) -> dict:
        """
        Regenera la contraseña del usuario vinculado a una empresa e invalida sus sesiones.

        Args:
            db: Sesión de base de datos
            empresa_id: UUID de la empresa

        Returns:
            {"username": str, "password": str}

        Raises:
            NotFoundException: Si la empresa no existe o no tiene usuario vinculado
        """
        await self.get_empresa(db, empresa_id)  # valida existencia de la empresa

        linked_user = await usuario_repository.get_by_empresa_id(db, empresa_id)
        if not linked_user:
            raise NotFoundException(f"La empresa {empresa_id} no tiene un usuario asociado")

        temp_password = usuario_service._generate_temp_password()
        await usuario_repository.update(
            db, id=linked_user.id, obj_in={'password_hash': get_password_hash(temp_password)}
        )
        await usuario_repository.increment_token_version(db, linked_user.id)

        logger.info(f"Password regenerada para usuario de empresa: {empresa_id}")

        return {"username": linked_user.username, "password": temp_password}
```

In `app/api/v1/endpoints/empresas.py`, add the route (after `deactivate_empresa`):

```python
@router.post(
    "/{empresa_id}/regenerar-password",
    summary="Regenerar contraseña del usuario-empresa",
    description="Genera una nueva contraseña temporal para el usuario vinculado a la empresa e invalida sus sesiones activas",
    dependencies=[Depends(PermissionChecker([Permissions.EMPRESA_UPDATE]))],
)
async def regenerar_password_empresa(
    empresa_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> dict:
    logger.info(f"Regeneración de password solicitada para empresa: {empresa_id}")

    resultado = await empresa_service.regenerar_password(db, empresa_id)

    return {
        "message": "Contraseña regenerada exitosamente",
        **resultado,
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `docker exec incapacidades-api pytest tests/unit/test_empresa_regenerar_password.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/services/empresa_service.py app/api/v1/endpoints/empresas.py tests/unit/test_empresa_regenerar_password.py
git commit -m "feat: add endpoint to regenerate an empresa-user's password"
```

---

### Task 7: Backfill Usuario for pre-existing Empresas — ⚠️ requires explicit confirmation before applying

**Files:**
- Create: `alembic/versions/<generated_timestamp>_backfill_usuario_empresa.py`

**Interfaces:**
- Consumes: nothing from earlier tasks (pure data migration, runs independently).
- Produces: nothing consumed by later tasks — this is a standalone operational step.

This task has no automated test — it is a one-time data migration. **Do not run `alembic upgrade head` / `make upgrade-db` against a real database without showing the generated file to the user first and getting explicit confirmation**, per this project's data-migration policy: it inserts real `Usuario` rows with real (bcrypt-hashed) passwords and writes the plaintext temporary passwords to a CSV file on disk so an admin can distribute them.

- [ ] **Step 1: Generate the revision skeleton**

Run: `docker exec incapacidades-api alembic revision -m "backfill usuario for empresas without one"`

This creates a new file in `alembic/versions/` with a fresh revision id and `down_revision` set to the current head (`4d58280019e6`, or whatever is head at execution time — check with `docker exec incapacidades-api alembic heads` first, since Tasks 1-6 added no migrations, this should still be `4d58280019e6`).

- [ ] **Step 2: Write the migration body**

Replace the generated file's `upgrade()`/`downgrade()` (keep the auto-generated header with `revision`/`down_revision` as-is):

```python
"""backfill usuario for empresas without one

Revision ID: <generated>
Revises: 4d58280019e6
Create Date: <generated>

"""
import csv
import secrets
import string
from datetime import datetime
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from passlib.context import CryptContext

# revision identifiers, used by Alembic.
revision: str = "<generated>"
down_revision: Union[str, None] = "4d58280019e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _generate_temp_password() -> str:
    alphabet = string.ascii_letters + string.digits
    password = list("".join(secrets.choice(alphabet) for _ in range(12)))
    password[0] = secrets.choice(string.ascii_uppercase)
    password[1] = secrets.choice(string.ascii_lowercase)
    password[2] = secrets.choice(string.digits)
    secrets.SystemRandom().shuffle(password)
    return "".join(password)


def upgrade() -> None:
    conn = op.get_bind()

    empresas_sin_usuario = conn.execute(sa.text("""
        SELECT e.id, e.nit, e.razon_social, e.email_contacto
        FROM empresa e
        LEFT JOIN usuario u ON u.empresa_id = e.id AND u.rol = 'EMPRESA'
        WHERE u.id IS NULL AND e.email_contacto IS NOT NULL
    """)).fetchall()

    report_rows = []
    for empresa in empresas_sin_usuario:
        temp_password = _generate_temp_password()
        conn.execute(
            sa.text("""
                INSERT INTO usuario (
                    id, username, email, password_hash, nombre_completo,
                    rol, estado, empresa_id, intentos_fallidos, token_version,
                    must_change_password, incapacidades_asignadas_activas,
                    created_at, updated_at
                ) VALUES (
                    gen_random_uuid(), :username, :email, :password_hash, :nombre_completo,
                    'EMPRESA', 'ACTIVO', :empresa_id, 0, 0,
                    false, 0,
                    now(), now()
                )
            """),
            {
                "username": empresa.nit,
                "email": empresa.email_contacto,
                "password_hash": pwd_context.hash(temp_password),
                "nombre_completo": empresa.razon_social,
                "empresa_id": str(empresa.id),
            },
        )
        report_rows.append((empresa.nit, empresa.razon_social, empresa.email_contacto, temp_password))

    if report_rows:
        report_path = f"backfill_usuario_empresa_{datetime.utcnow():%Y%m%d_%H%M%S}.csv"
        with open(report_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["nit", "razon_social", "email", "password_temporal"])
            writer.writerows(report_rows)
        print(f"[backfill] {len(report_rows)} usuarios creados. Credenciales en: {report_path}")

    total_sin_email = conn.execute(sa.text("""
        SELECT COUNT(*) FROM empresa e
        LEFT JOIN usuario u ON u.empresa_id = e.id AND u.rol = 'EMPRESA'
        WHERE u.id IS NULL AND e.email_contacto IS NULL
    """)).scalar()
    if total_sin_email:
        print(
            f"[backfill] AVISO: {total_sin_email} empresas sin email_contacto fueron "
            f"omitidas (no se les pudo crear usuario; requieren email_contacto primero)."
        )


def downgrade() -> None:
    # No-op: a backfilled Usuario is indistinguishable from one created normally
    # afterward via POST /empresas, so there is no safe way to identify and
    # remove only the backfilled rows. Reversing this migration is not supported.
    print("[backfill] downgrade is a no-op — backfilled usuarios are not distinguishable from later ones and are left in place.")
```

- [ ] **Step 3: Show the generated file to the user and stop**

Print the full path of the generated migration file and ask the user to confirm before running `docker exec incapacidades-api alembic upgrade head` (or `make upgrade-db`) against the real database. Do not run it as part of this task's automated execution — this step is manual/interactive by design.

- [ ] **Step 4: Commit (the migration file only, not its execution)**

```bash
git add alembic/versions/*_backfill_usuario_empresa.py
git commit -m "feat: add data migration to backfill Usuario for empresas without one"
```

---

### Task 8: Analytics endpoint (`GET /empresas/analitica`)

**Files:**
- Create: `app/schemas/analitica.py`
- Create: `app/db/repositories/analitica_repository.py`
- Create: `app/services/analitica_service.py`
- Modify: `app/api/v1/endpoints/empresas.py`
- Test: `tests/unit/test_analitica_empresas.py`

**Interfaces:**
- Produces: `AnaliticaEmpresasResponse` (`top_empresas: List[EmpresaTopItem]`, `tendencia_mensual: List[TendenciaMensualItem]`) — no other backend task consumes this; the (separate, future) frontend spec will.

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_analitica_empresas.py
"""GET /empresas/analitica: top-10 ranking + 12-month trend, both server-aggregated."""
from datetime import datetime, timedelta

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_analitica_top_empresas_ordered_desc_capped_at_10(
    client: AsyncClient, db_session, admin_token_headers
):
    from app.models.empresa import Empresa
    from app.models.incapacidad import Incapacidad
    from app.utils.enums import EstadoEmpresa, TipoIncapacidad, EstadoIncapacidad, Prioridad
    from decimal import Decimal

    empresas = []
    for i in range(3):
        empresa = Empresa(
            nit=f"90010000{i}",
            razon_social=f"Empresa Analitica {i}",
            email_contacto=f"analitica{i}@empresa.com",
            estado=EstadoEmpresa.ACTIVA,
        )
        db_session.add(empresa)
        empresas.append(empresa)
    await db_session.commit()
    for e in empresas:
        await db_session.refresh(e)

    # empresas[0] gets 3 incapacidades, empresas[1] gets 1, empresas[2] gets 0.
    counts = [3, 1, 0]
    numero = 0
    for empresa, count in zip(empresas, counts):
        for _ in range(count):
            numero += 1
            db_session.add(Incapacidad(
                numero=f"INC-ANALITICA-{numero}",
                empresa_id=empresa.id,
                tipo=TipoIncapacidad.ARL,
                fecha_inicio=datetime.utcnow().date(),
                fecha_fin=datetime.utcnow().date(),
                dias_totales=1,
                diagnostico_cie10="M545",
                descripcion_diagnostico="Test",
                valor_dia=Decimal("100000"),
                valor_total=Decimal("100000"),
                estado=EstadoIncapacidad.RADICADA,
                fecha_radicacion=datetime.utcnow(),
                prioridad=Prioridad.NORMAL,
            ))
    await db_session.commit()

    resp = await client.get("/api/v1/empresas/analitica", headers=admin_token_headers)
    assert resp.status_code == 200
    body = resp.json()

    top = body["top_empresas"]
    assert len(top) <= 10
    assert top[0]["nit"] == "900100000"
    assert top[0]["total_radicadas"] == 3
    assert top[1]["nit"] == "900100001"
    assert top[1]["total_radicadas"] == 1


@pytest.mark.asyncio
async def test_analitica_tendencia_mensual_has_12_zero_filled_months(
    client: AsyncClient, admin_token_headers
):
    resp = await client.get("/api/v1/empresas/analitica", headers=admin_token_headers)
    assert resp.status_code == 200
    tendencia = resp.json()["tendencia_mensual"]
    assert len(tendencia) == 12
    for item in tendencia:
        assert "periodo" in item and "total" in item
```

- [ ] **Step 2: Run test to verify it fails**

Run: `docker exec incapacidades-api pytest tests/unit/test_analitica_empresas.py -v`
Expected: FAIL — `404 Not Found` (route doesn't exist).

- [ ] **Step 3: Implement schemas, repository, service, endpoint**

`app/schemas/analitica.py`:

```python
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
```

`app/db/repositories/analitica_repository.py`:

```python
"""Repositorio de consultas agregadas para analítica de empresas."""
from datetime import datetime
from typing import Any, Sequence

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.empresa import Empresa
from app.models.incapacidad import Incapacidad


def _first_day_n_months_ago(n: int) -> datetime:
    """Primer día del mes que está `n - 1` meses antes del mes actual."""
    today = datetime.utcnow()
    year, month = today.year, today.month - (n - 1)
    while month <= 0:
        month += 12
        year -= 1
    return datetime(year, month, 1)


class AnaliticaRepository:
    """Consultas agregadas (server-side) para el dashboard de analítica de empresas."""

    async def top_empresas_radicadas(self, db: AsyncSession, limit: int = 10) -> Sequence[Any]:
        """Top `limit` empresas por total de incapacidades alguna vez radicadas (todo estado)."""
        query = (
            select(
                Empresa.id,
                Empresa.razon_social,
                Empresa.nit,
                func.count(Incapacidad.id).label("total"),
            )
            .join(Incapacidad, Incapacidad.empresa_id == Empresa.id)
            .group_by(Empresa.id, Empresa.razon_social, Empresa.nit)
            .order_by(func.count(Incapacidad.id).desc())
            .limit(limit)
        )
        result = await db.execute(query)
        return result.all()

    async def tendencia_mensual_radicadas(self, db: AsyncSession, meses: int = 12) -> Sequence[Any]:
        """Total de incapacidades radicadas por mes, para los últimos `meses` meses."""
        cutoff = _first_day_n_months_ago(meses)
        periodo = func.date_trunc("month", Incapacidad.fecha_radicacion)
        query = (
            select(periodo.label("periodo"), func.count(Incapacidad.id).label("total"))
            .where(Incapacidad.fecha_radicacion >= cutoff)
            .group_by(periodo)
            .order_by(periodo)
        )
        result = await db.execute(query)
        return result.all()


# Instancia singleton del repositorio
analitica_repository = AnaliticaRepository()
```

`app/services/analitica_service.py`:

```python
"""Servicio de analítica de empresas: arma la respuesta agregada para el dashboard."""
from datetime import datetime
from typing import Dict, List

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.analitica_repository import analitica_repository
from app.schemas.analitica import AnaliticaEmpresasResponse, EmpresaTopItem, TendenciaMensualItem


class AnaliticaService:
    """Lógica de negocio para el endpoint de analítica de empresas."""

    def __init__(self):
        self.repository = analitica_repository

    async def get_analitica_empresas(self, db: AsyncSession) -> AnaliticaEmpresasResponse:
        top_rows = await self.repository.top_empresas_radicadas(db, limit=10)
        top_empresas = [
            EmpresaTopItem(
                empresa_id=row.id,
                razon_social=row.razon_social,
                nit=row.nit,
                total_radicadas=row.total,
            )
            for row in top_rows
        ]

        tendencia_rows = await self.repository.tendencia_mensual_radicadas(db, meses=12)
        por_periodo: Dict[str, int] = {
            row.periodo.strftime("%Y-%m"): row.total for row in tendencia_rows
        }
        tendencia_mensual = self._rellenar_meses_faltantes(por_periodo)

        return AnaliticaEmpresasResponse(
            top_empresas=top_empresas,
            tendencia_mensual=tendencia_mensual,
        )

    def _rellenar_meses_faltantes(self, por_periodo: Dict[str, int]) -> List[TendenciaMensualItem]:
        """Genera los últimos 12 periodos (YYYY-MM) en orden cronológico, con 0 donde no hubo datos."""
        hoy = datetime.utcnow()
        year, month = hoy.year, hoy.month
        periodos = []
        for _ in range(12):
            periodos.append(f"{year:04d}-{month:02d}")
            month -= 1
            if month == 0:
                month = 12
                year -= 1
        periodos.reverse()
        return [
            TendenciaMensualItem(periodo=p, total=por_periodo.get(p, 0))
            for p in periodos
        ]


# Singleton
analitica_service = AnaliticaService()
```

In `app/api/v1/endpoints/empresas.py`, add the import and route. Insert the route **immediately after `list_empresas`, before `get_empresa`**, so it's visually and structurally distinct from the `/{empresa_id}` family:

```python
from app.schemas.analitica import AnaliticaEmpresasResponse
from app.services.analitica_service import analitica_service
```

```python
@router.get(
    "/analitica",
    response_model=AnaliticaEmpresasResponse,
    summary="Analítica de empresas",
    description="Top 10 empresas por incapacidades radicadas y tendencia mensual de los últimos 12 meses (agregado en servidor)",
    dependencies=[Depends(PermissionChecker([Permissions.EMPRESA_READ]))],
)
async def get_analitica_empresas(
    db: AsyncSession = Depends(get_db)
) -> AnaliticaEmpresasResponse:
    return await analitica_service.get_analitica_empresas(db)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `docker exec incapacidades-api pytest tests/unit/test_analitica_empresas.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/schemas/analitica.py app/db/repositories/analitica_repository.py app/services/analitica_service.py app/api/v1/endpoints/empresas.py tests/unit/test_analitica_empresas.py
git commit -m "feat: add server-aggregated analytics endpoint for empresas dashboard"
```

---

### Task 9: Bulk-upload plantilla (`GET /empleados/plantilla`)

**Files:**
- Create: `app/services/empleado_bulk_service.py`
- Modify: `app/api/v1/endpoints/empleados.py`
- Test: `tests/unit/test_empleado_bulk_plantilla.py`

**Interfaces:**
- Produces: `generar_plantilla_empleados() -> bytes` and `TEMPLATE_HEADERS: list[str]` (`app/services/empleado_bulk_service.py`) — `TEMPLATE_HEADERS` is consumed by Tasks 10 and 11 for parsing.

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_empleado_bulk_plantilla.py
"""GET /empleados/plantilla: downloadable .xlsx with the right headers, no banking columns."""
import io

import pytest
from httpx import AsyncClient
from openpyxl import load_workbook


@pytest.mark.asyncio
async def test_descargar_plantilla_empleados(client: AsyncClient, admin_token_headers):
    resp = await client.get("/api/v1/empleados/plantilla", headers=admin_token_headers)
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    wb = load_workbook(io.BytesIO(resp.content))
    ws = wb["Empleados"]
    headers = [cell.value for cell in next(ws.iter_rows(min_row=1, max_row=1))]

    assert headers == [
        "numero_documento", "tipo_documento", "nombres", "apellidos", "email",
        "telefono", "fecha_nacimiento", "genero", "cargo", "area",
        "fecha_ingreso", "salario_base", "nit_empresa",
    ]
    for banking_field in ("cuenta_bancaria", "banco", "tipo_cuenta"):
        assert banking_field not in headers

    assert "Instrucciones" in wb.sheetnames


@pytest.mark.asyncio
async def test_descargar_plantilla_forbidden_for_liquidador(client: AsyncClient, db_session):
    from app.core.security import create_access_token, get_password_hash
    from app.models.usuario import Usuario
    from app.utils.enums import RolUsuario, EstadoUsuario

    usuario = Usuario(
        username="liquidador_plantilla",
        email="liquidador_plantilla@example.com",
        password_hash=get_password_hash("Test1234"),
        nombre_completo="Test LIQUIDADOR",
        rol=RolUsuario.LIQUIDADOR,
        estado=EstadoUsuario.ACTIVO,
    )
    db_session.add(usuario)
    await db_session.commit()
    await db_session.refresh(usuario)
    token = create_access_token(data={"sub": str(usuario.id), "token_version": usuario.token_version})

    resp = await client.get(
        "/api/v1/empleados/plantilla", headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 403
```

- [ ] **Step 2: Run test to verify it fails**

Run: `docker exec incapacidades-api pytest tests/unit/test_empleado_bulk_plantilla.py -v`
Expected: FAIL — `404 Not Found` (route doesn't exist).

- [ ] **Step 3: Implement the service function and endpoint**

`app/services/empleado_bulk_service.py`:

```python
"""Servicio de carga masiva de empleados: plantilla Excel, parseo+validación, confirmación."""
import io

from openpyxl import Workbook

TEMPLATE_HEADERS = [
    "numero_documento", "tipo_documento", "nombres", "apellidos", "email",
    "telefono", "fecha_nacimiento", "genero", "cargo", "area",
    "fecha_ingreso", "salario_base", "nit_empresa",
]

TEMPLATE_INSTRUCCIONES = [
    ("numero_documento", "Número de documento de identidad. Obligatorio, único por empresa."),
    ("tipo_documento", "CC, CE, TI, PASAPORTE o PEP. Obligatorio."),
    ("nombres", "Nombres del empleado. Obligatorio."),
    ("apellidos", "Apellidos del empleado. Obligatorio."),
    ("email", "Correo del empleado. Opcional."),
    ("telefono", "Teléfono de contacto. Opcional."),
    ("fecha_nacimiento", "Formato YYYY-MM-DD. Opcional."),
    ("genero", "M, F u O. Opcional."),
    ("cargo", "Cargo del empleado. Opcional."),
    ("area", "Área de trabajo. Opcional."),
    ("fecha_ingreso", "Formato YYYY-MM-DD. Obligatorio."),
    ("salario_base", "Salario base numérico. Opcional."),
    ("nit_empresa", "NIT de la empresa a la que pertenece el empleado. Obligatorio, debe existir."),
]


def generar_plantilla_empleados() -> bytes:
    """Genera un .xlsx con encabezados, una fila de ejemplo y una hoja de instrucciones."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Empleados"
    ws.append(TEMPLATE_HEADERS)
    ws.append([
        "1234567890", "CC", "Juan", "Pérez", "juan.perez@correo.com",
        "3001234567", "1990-05-15", "M", "Analista", "Operaciones",
        "2024-01-15", "3000000", "900123456",
    ])

    ws_instrucciones = wb.create_sheet("Instrucciones")
    ws_instrucciones.append(["Columna", "Descripción"])
    for columna, descripcion in TEMPLATE_INSTRUCCIONES:
        ws_instrucciones.append([columna, descripcion])

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
```

In `app/api/v1/endpoints/empleados.py`, add imports:

```python
import io

from fastapi.responses import StreamingResponse

from app.services.empleado_bulk_service import generar_plantilla_empleados
```

Add the route **immediately after `list_empleados`, before `get_empleado`** (same reasoning as Task 8 — keep the static route visually separate from the `/{empleado_id}` family):

```python
@router.get(
    "/plantilla",
    summary="Descargar plantilla de carga masiva",
    description="Genera un archivo Excel con los encabezados esperados para la carga masiva de empleados",
    dependencies=[Depends(PermissionChecker([Permissions.EMPLEADO_CREATE]))],
)
async def descargar_plantilla_empleados():
    content = generar_plantilla_empleados()
    return StreamingResponse(
        io.BytesIO(content),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=plantilla_empleados.xlsx"},
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `docker exec incapacidades-api pytest tests/unit/test_empleado_bulk_plantilla.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/services/empleado_bulk_service.py app/api/v1/endpoints/empleados.py tests/unit/test_empleado_bulk_plantilla.py
git commit -m "feat: add downloadable bulk-upload template for empleados"
```

---

### Task 10: Bulk-upload dry-run validation (`POST /empleados/carga-masiva/validar`)

**Files:**
- Modify: `app/schemas/empleado.py` (add bulk-specific schemas in a new file instead — see below)
- Create: `app/schemas/empleado_bulk.py`
- Modify: `app/services/empleado_bulk_service.py`
- Modify: `app/api/v1/endpoints/empleados.py`
- Test: `tests/unit/test_empleado_bulk_validar.py`

**Interfaces:**
- Consumes: `TEMPLATE_HEADERS` (Task 9).
- Produces: `parsear_y_validar_empleados(db, file_bytes) -> tuple[list[tuple[int, dict]], list[FilaError]]` — the first element is `(fila_excel, empleado_dict)` pairs for valid rows, the second is `FilaError` objects for invalid rows. Consumed by Task 11.

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_empleado_bulk_validar.py
"""POST /empleados/carga-masiva/validar: dry-run, writes nothing to the DB."""
import io

import pytest
from httpx import AsyncClient
from openpyxl import Workbook
from sqlalchemy import select

from app.models.empleado import Empleado


def _build_xlsx(rows: list[list]) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.append([
        "numero_documento", "tipo_documento", "nombres", "apellidos", "email",
        "telefono", "fecha_nacimiento", "genero", "cargo", "area",
        "fecha_ingreso", "salario_base", "nit_empresa",
    ])
    for row in rows:
        ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


@pytest.mark.asyncio
async def test_validar_carga_masiva_detects_errors_and_writes_nothing(
    client: AsyncClient, db_session, admin_token_headers, test_empresa
):
    content = _build_xlsx([
        # Valid row
        ["1000000001", "CC", "Ana", "Gómez", "ana@correo.com", "3001111111",
         "1992-04-10", "F", "Analista", "RRHH", "2023-01-01", "3500000", test_empresa.nit],
        # Missing numero_documento
        ["", "CC", "Luis", "Ramírez", "", "", "", "", "", "", "2023-01-01", "", test_empresa.nit],
        # nit_empresa doesn't exist
        ["1000000002", "CC", "Marta", "Díaz", "", "", "", "", "", "", "2023-01-01", "", "999999999"],
        # Duplicate numero_documento within the file
        ["1000000001", "CC", "Ana", "Duplicada", "", "", "", "", "", "", "2023-01-01", "", test_empresa.nit],
    ])

    resp = await client.post(
        "/api/v1/empleados/carga-masiva/validar",
        headers=admin_token_headers,
        files={"file": ("empleados.xlsx", content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert resp.status_code == 200
    body = resp.json()

    assert body["validas"] == 1
    assert body["con_error"] == 3
    assert body["total_filas"] == 4

    mensajes = [e["mensaje"] for e in body["errores"]]
    assert any("obligatorio" in m.lower() for m in mensajes)
    assert any("999999999" in m for m in mensajes)
    assert any("duplicado" in m.lower() for m in mensajes)

    # Dry-run: nothing inserted.
    result = await db_session.execute(
        select(Empleado).where(Empleado.numero_documento == "1000000001")
    )
    assert result.scalar_one_or_none() is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `docker exec incapacidades-api pytest tests/unit/test_empleado_bulk_validar.py -v`
Expected: FAIL — `404 Not Found` (route doesn't exist).

- [ ] **Step 3: Implement schemas and the parse/validate function**

`app/schemas/empleado_bulk.py`:

```python
"""Schemas de Pydantic para la carga masiva de empleados."""
from typing import List, Optional

from pydantic import BaseModel


class FilaError(BaseModel):
    """Un error de validación en una fila específica del Excel de carga masiva."""
    fila: int
    columna: Optional[str] = None
    mensaje: str


class ValidacionMasivaResponse(BaseModel):
    """Resultado del dry-run de validación de carga masiva."""
    total_filas: int
    validas: int
    con_error: int
    errores: List[FilaError]


class ConfirmacionMasivaResponse(BaseModel):
    """Resultado de la confirmación de carga masiva (inserción parcial)."""
    total_filas: int
    insertadas: int
    con_error: int
    errores: List[FilaError]
```

In `app/services/empleado_bulk_service.py`, add (after `TEMPLATE_INSTRUCCIONES`, before `generar_plantilla_empleados`):

```python
import datetime as dt
from decimal import Decimal, InvalidOperation

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException
from app.models.empleado import Empleado
from app.models.empresa import Empresa
from app.schemas.empleado_bulk import FilaError
from app.utils.enums import EstadoEmpleado, Genero, TipoDocumento
```

(move these to the top of the file alongside the existing `import io` and `from openpyxl import Workbook`; add `load_workbook` to that import too: `from openpyxl import Workbook, load_workbook`)

Then add the parsing helpers and main function at the end of the file:

```python
def _parse_date(v) -> "dt.date | None":
    """Convierte un valor de celda Excel a date, o None si está vacío."""
    if v in (None, ""):
        return None
    if isinstance(v, dt.datetime):
        return v.date()
    if isinstance(v, dt.date):
        return v
    s = str(v).strip()
    try:
        return dt.date.fromisoformat(s[:10])
    except (ValueError, TypeError):
        raise ValueError(f"Fecha inválida: {s!r}. Use formato YYYY-MM-DD.")


def _text(v):
    """Convierte una celda Excel a texto limpio, o None si está vacía."""
    if v is None or (isinstance(v, str) and not v.strip()):
        return None
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v).strip()


def _is_empty(values) -> bool:
    """Retorna True si todos los valores de la fila son None, cadena vacía o solo espacios."""
    return all(v is None or (isinstance(v, str) and not v.strip()) or v == "" for v in values)


async def parsear_y_validar_empleados(
    db: AsyncSession, file_bytes: bytes
) -> tuple[list[tuple[int, dict]], list[FilaError]]:
    """Parsea el Excel de empleados y valida fila por fila. No escribe en BD.

    Retorna (filas_validas, errores):
    - filas_validas: lista de (numero_de_fila_excel, dict_listo_para_Empleado)
    - errores: lista de FilaError para las filas inválidas

    Filas completamente vacías son omitidas (no cuentan como error ni como válida).
    """
    try:
        wb = load_workbook(io.BytesIO(file_bytes), data_only=True)
    except Exception:
        raise BadRequestException("El archivo no es un Excel válido (.xlsx).")

    ws = wb.active
    if ws is None:
        raise BadRequestException("El archivo Excel no contiene hojas activas.")

    empresas_by_nit = {
        e.nit: e for e in (await db.execute(select(Empresa))).scalars().all()
    }
    documentos_existentes = {
        (doc, str(empresa_id))
        for doc, empresa_id in (
            await db.execute(select(Empleado.numero_documento, Empleado.empresa_id))
        ).all()
    }

    filas_validas: list[tuple[int, dict]] = []
    errores: list[FilaError] = []
    documentos_en_archivo: dict[str, int] = {}

    for idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        cells = list(row) + [None] * (len(TEMPLATE_HEADERS) - len(row))
        if _is_empty(cells):
            continue

        data = dict(zip(TEMPLATE_HEADERS, cells))
        fila_errores: list[FilaError] = []

        numero_documento = _text(data.get("numero_documento"))
        if not numero_documento:
            fila_errores.append(FilaError(fila=idx, columna="numero_documento", mensaje="Campo obligatorio"))

        tipo_documento = _text(data.get("tipo_documento"))
        if not tipo_documento:
            fila_errores.append(FilaError(fila=idx, columna="tipo_documento", mensaje="Campo obligatorio"))
        elif tipo_documento not in {t.value for t in TipoDocumento}:
            fila_errores.append(FilaError(fila=idx, columna="tipo_documento", mensaje=f"Valor inválido: {tipo_documento}"))

        nombres = _text(data.get("nombres"))
        if not nombres:
            fila_errores.append(FilaError(fila=idx, columna="nombres", mensaje="Campo obligatorio"))

        apellidos = _text(data.get("apellidos"))
        if not apellidos:
            fila_errores.append(FilaError(fila=idx, columna="apellidos", mensaje="Campo obligatorio"))

        nit_empresa = _text(data.get("nit_empresa"))
        empresa = None
        if not nit_empresa:
            fila_errores.append(FilaError(fila=idx, columna="nit_empresa", mensaje="Campo obligatorio"))
        else:
            empresa = empresas_by_nit.get(nit_empresa)
            if empresa is None:
                fila_errores.append(FilaError(fila=idx, columna="nit_empresa", mensaje=f"No existe una empresa con NIT {nit_empresa}"))

        fecha_ingreso_raw = data.get("fecha_ingreso")
        fecha_ingreso = None
        if fecha_ingreso_raw in (None, ""):
            fila_errores.append(FilaError(fila=idx, columna="fecha_ingreso", mensaje="Campo obligatorio"))
        else:
            try:
                fecha_ingreso = _parse_date(fecha_ingreso_raw)
            except ValueError as e:
                fila_errores.append(FilaError(fila=idx, columna="fecha_ingreso", mensaje=str(e)))

        fecha_nacimiento_raw = data.get("fecha_nacimiento")
        fecha_nacimiento = None
        if fecha_nacimiento_raw not in (None, ""):
            try:
                fecha_nacimiento = _parse_date(fecha_nacimiento_raw)
            except ValueError as e:
                fila_errores.append(FilaError(fila=idx, columna="fecha_nacimiento", mensaje=str(e)))

        genero = _text(data.get("genero"))
        if genero and genero not in {g.value for g in Genero}:
            fila_errores.append(FilaError(fila=idx, columna="genero", mensaje=f"Valor inválido: {genero}"))

        salario_base = None
        salario_raw = data.get("salario_base")
        if salario_raw not in (None, ""):
            try:
                salario_base = Decimal(str(salario_raw))
            except InvalidOperation:
                fila_errores.append(FilaError(fila=idx, columna="salario_base", mensaje=f"Valor no numérico: {salario_raw!r}"))

        if numero_documento:
            if numero_documento in documentos_en_archivo:
                fila_errores.append(FilaError(
                    fila=idx, columna="numero_documento",
                    mensaje=f"Documento duplicado en el archivo (también en fila {documentos_en_archivo[numero_documento]})",
                ))
            else:
                documentos_en_archivo[numero_documento] = idx

            if empresa and (numero_documento, str(empresa.id)) in documentos_existentes:
                fila_errores.append(FilaError(
                    fila=idx, columna="numero_documento",
                    mensaje=f"Ya existe un empleado con documento {numero_documento} en esta empresa",
                ))

        if fila_errores:
            errores.extend(fila_errores)
            continue

        filas_validas.append((idx, {
            "empresa_id": empresa.id,
            "numero_documento": numero_documento,
            "tipo_documento": tipo_documento,
            "nombres": nombres,
            "apellidos": apellidos,
            "email": _text(data.get("email")),
            "telefono": _text(data.get("telefono")),
            "fecha_nacimiento": fecha_nacimiento,
            "genero": genero,
            "cargo": _text(data.get("cargo")),
            "area": _text(data.get("area")),
            "fecha_ingreso": fecha_ingreso,
            "salario_base": salario_base,
            "estado": EstadoEmpleado.ACTIVO,
        }))

    return filas_validas, errores
```

In `app/api/v1/endpoints/empleados.py`, add imports and the route (placed after the `plantilla` route from Task 9):

```python
from fastapi import UploadFile, File

from app.schemas.empleado_bulk import ValidacionMasivaResponse
from app.services.empleado_bulk_service import parsear_y_validar_empleados
```

```python
@router.post(
    "/carga-masiva/validar",
    response_model=ValidacionMasivaResponse,
    summary="Validar archivo de carga masiva (dry-run)",
    description="Valida el archivo Excel de empleados fila por fila sin insertar nada en la base de datos",
    dependencies=[Depends(PermissionChecker([Permissions.EMPLEADO_CREATE]))],
)
async def validar_carga_masiva_empleados(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> ValidacionMasivaResponse:
    content = await file.read()
    filas_validas, errores = await parsear_y_validar_empleados(db, content)
    return ValidacionMasivaResponse(
        total_filas=len(filas_validas) + len(errores),
        validas=len(filas_validas),
        con_error=len(errores),
        errores=errores,
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `docker exec incapacidades-api pytest tests/unit/test_empleado_bulk_validar.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/schemas/empleado_bulk.py app/services/empleado_bulk_service.py app/api/v1/endpoints/empleados.py tests/unit/test_empleado_bulk_validar.py
git commit -m "feat: add dry-run validation endpoint for empleados bulk upload"
```

---

### Task 11: Bulk-upload confirm (`POST /empleados/carga-masiva/confirmar`)

**Files:**
- Modify: `app/services/empleado_bulk_service.py`
- Modify: `app/api/v1/endpoints/empleados.py`
- Test: `tests/unit/test_empleado_bulk_confirmar.py`

**Interfaces:**
- Consumes: `parsear_y_validar_empleados` (Task 10), `ConfirmacionMasivaResponse` (Task 10's schema file).
- Produces: `confirmar_carga_empleados(db, file_bytes) -> ConfirmacionMasivaResponse` — no other task consumes this; it's the terminal step of the bulk-upload flow.

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/test_empleado_bulk_confirmar.py
"""POST /empleados/carga-masiva/confirmar: inserts only valid rows (partial insert)."""
import io

import pytest
from httpx import AsyncClient
from openpyxl import Workbook
from sqlalchemy import select

from app.models.empleado import Empleado


def _build_xlsx(rows: list[list]) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.append([
        "numero_documento", "tipo_documento", "nombres", "apellidos", "email",
        "telefono", "fecha_nacimiento", "genero", "cargo", "area",
        "fecha_ingreso", "salario_base", "nit_empresa",
    ])
    for row in rows:
        ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


@pytest.mark.asyncio
async def test_confirmar_carga_masiva_inserts_only_valid_rows(
    client: AsyncClient, db_session, admin_token_headers, test_empresa
):
    content = _build_xlsx([
        ["2000000001", "CC", "Carlos", "Ruiz", "", "", "", "", "", "", "2023-01-01", "", test_empresa.nit],
        ["", "CC", "Sin Documento", "Test", "", "", "", "", "", "", "2023-01-01", "", test_empresa.nit],
    ])

    resp = await client.post(
        "/api/v1/empleados/carga-masiva/confirmar",
        headers=admin_token_headers,
        files={"file": ("empleados.xlsx", content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert resp.status_code == 200
    body = resp.json()

    assert body["insertadas"] == 1
    assert body["con_error"] == 1
    assert body["total_filas"] == 2

    result = await db_session.execute(
        select(Empleado).where(Empleado.numero_documento == "2000000001")
    )
    assert result.scalar_one_or_none() is not None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `docker exec incapacidades-api pytest tests/unit/test_empleado_bulk_confirmar.py -v`
Expected: FAIL — `404 Not Found` (route doesn't exist).

- [ ] **Step 3: Implement the confirm function and endpoint**

In `app/services/empleado_bulk_service.py`, add imports (`empleado_repository`) and the function at the end of the file:

```python
from app.db.repositories.empleado_repository import empleado_repository
from app.schemas.empleado_bulk import ConfirmacionMasivaResponse


async def confirmar_carga_empleados(db: AsyncSession, file_bytes: bytes) -> ConfirmacionMasivaResponse:
    """Re-valida el archivo desde cero e inserta únicamente las filas válidas (inserción parcial)."""
    filas_validas, errores = await parsear_y_validar_empleados(db, file_bytes)

    insertadas = 0
    for fila_excel, data in filas_validas:
        try:
            await empleado_repository.create(db, data)
            insertadas += 1
        except Exception as e:
            errores.append(FilaError(
                fila=fila_excel,
                mensaje=f"Error al insertar documento {data['numero_documento']}: {e}",
            ))

    return ConfirmacionMasivaResponse(
        total_filas=len(filas_validas) + len(errores),
        insertadas=insertadas,
        con_error=len(errores),
        errores=errores,
    )
```

In `app/api/v1/endpoints/empleados.py`, Task 10 already added `from app.schemas.empleado_bulk import ValidacionMasivaResponse` and `from app.services.empleado_bulk_service import parsear_y_validar_empleados` — extend those two lines in place rather than adding new ones:

```python
from app.schemas.empleado_bulk import ValidacionMasivaResponse, ConfirmacionMasivaResponse
from app.services.empleado_bulk_service import (
    parsear_y_validar_empleados,
    confirmar_carga_empleados,
)
```

Then add the route (after the `validar` route from Task 10):

```python
@router.post(
    "/carga-masiva/confirmar",
    response_model=ConfirmacionMasivaResponse,
    summary="Confirmar carga masiva de empleados",
    description="Re-valida el archivo Excel e inserta únicamente las filas válidas",
    dependencies=[Depends(PermissionChecker([Permissions.EMPLEADO_CREATE]))],
)
async def confirmar_carga_masiva_empleados(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> ConfirmacionMasivaResponse:
    content = await file.read()
    return await confirmar_carga_empleados(db, content)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `docker exec incapacidades-api pytest tests/unit/test_empleado_bulk_confirmar.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/services/empleado_bulk_service.py app/api/v1/endpoints/empleados.py tests/unit/test_empleado_bulk_confirmar.py
git commit -m "feat: add confirm endpoint for empleados bulk upload (partial insert)"
```

---

## Post-plan checklist (not a task — do after Task 11 lands)

- Run the full modified-file test sweep: `docker exec incapacidades-api pytest tests/unit/test_permission_checker_liquidador.py tests/unit/test_rbac_empresas.py tests/unit/test_rbac_empleados.py tests/unit/test_empresa_usuario_creation.py tests/unit/test_empresa_email_sync.py tests/unit/test_empresa_regenerar_password.py tests/unit/test_analitica_empresas.py tests/unit/test_empleado_bulk_plantilla.py tests/unit/test_empleado_bulk_validar.py tests/unit/test_empleado_bulk_confirmar.py -v`
- Task 7's migration is still unapplied at this point by design — surface it to the user before running against any real database.
- `make lint` (ruff + mypy) on the backend before considering the branch done.

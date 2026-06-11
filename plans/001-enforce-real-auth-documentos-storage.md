# Plan 001: Enforce real authentication on documentos and storage endpoints

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving to the
> next step. If anything in the "STOP conditions" section occurs, stop and
> report — do not improvise. When done, update the status row for this plan
> in `plans/README.md` — unless a reviewer dispatched you and told you they
> maintain the index.
>
> **Drift check (run first)**: `git diff --stat 7958670b..HEAD -- apps/backend/app/api/v1/endpoints/documentos.py apps/backend/app/api/v1/endpoints/storage.py apps/backend/app/api/v1/endpoints/incapacidades.py apps/frontend/sistema-interno/src/components/incapacidades/DocumentosViewer.tsx`
> If any in-scope file changed since this plan was written, compare the
> "Current state" excerpts against the live code before proceeding; on a
> mismatch, treat it as a STOP condition.

## Status

- **Priority**: P1
- **Effort**: M
- **Risk**: MED
- **Depends on**: none
- **Category**: security
- **Planned at**: commit `7958670b`, 2026-06-10

## Why this matters

Every document endpoint in the backend (`upload`, `get`, `view`, `download`, `delete`, `list`) is currently **unauthenticated**: `documentos.py` defines a local placeholder `get_current_user` that returns the first user in the database without checking any token, and a local `PermissionChecker` that always returns `True`. These placeholders shadow the real, working implementations that already exist in `app/core/security.py`. Separately, the filesystem file-serving endpoint in `storage.py` imports the real `get_current_user` but never applies it, so any anonymous client can download any stored file (medical records, identity documents). Finally, the `/incapacidades/pendientes` endpoint authenticates but does not check roles, so any logged-in user (including `EMPLEADO`/`READONLY`) can list the auditors' queue. This system stores health data; this is the highest-severity issue in the codebase.

## Current state

Relevant files:

- `apps/backend/app/api/v1/endpoints/documentos.py` — 7 document routes; lines 27–53 contain the placeholder auth that must be deleted.
- `apps/backend/app/api/v1/endpoints/storage.py` — `serve_file` endpoint at line 20; imports `get_current_user` at line 13 but the function signature (lines 21–23) does not use it.
- `apps/backend/app/api/v1/endpoints/incapacidades.py` — `/pendientes` route decorator at lines 318–324 lacks a `PermissionChecker` dependency. This file already imports and uses the real auth correctly elsewhere (see line 42 and line 566) — use it as the exemplar.
- `apps/backend/app/core/security.py` — the REAL implementations: `get_current_user` at line 180 (validates JWT, checks `is_active` and `token_version`), `PermissionChecker` at line 227 (role→permission map; raises `ForbiddenException`), `Permissions` constants class at line 129 (includes `DOCUMENTO_CREATE/READ/UPDATE/DELETE` with the same string values as the placeholder).
- `apps/frontend/sistema-interno/src/components/incapacidades/DocumentosViewer.tsx` — builds raw `/view` URLs and puts them in `<img src>` / `<iframe src>`; those browser-native requests carry no `Authorization` header, so they will break once auth is real. Must be switched to authenticated blob fetches.

### Placeholder to remove — `documentos.py:27-53` (exact current code)

```python
# Dummy function for get_current_user until auth is implemented
async def get_current_user(db: AsyncSession = Depends(get_db)) -> Usuario:
    """Placeholder para get_current_user."""
    from sqlalchemy import select
    result = await db.execute(select(Usuario).limit(1))
    return result.scalar_one()


# Dummy permission checker
class Permissions:
    """Permisos del sistema."""
    DOCUMENTO_CREATE = "documento_create"
    DOCUMENTO_READ = "documento_read"
    DOCUMENTO_UPDATE = "documento_update"
    DOCUMENTO_DELETE = "documento_delete"


class PermissionChecker:
    """Verificador de permisos (placeholder)."""

    def __init__(self, required_permissions: list[str]):
        """Inicializa el checker."""
        self.required_permissions = required_permissions

    async def __call__(self, current_user: Usuario = Depends(get_current_user)) -> bool:
        """Verifica permisos (siempre retorna True por ahora)."""
        return True
```

The route decorators in this file already use these names (e.g. line 60:
`dependencies=[Depends(PermissionChecker([Permissions.DOCUMENTO_CREATE]))]`), and the
real `Permissions` class uses identical string values, so swapping the import is
sufficient — no route decorator changes needed in `documentos.py`.

### Missing auth — `storage.py:20-23` (exact current code)

```python
@router.get("/files/{filepath:path}")
async def serve_file(
    filepath: str = PathParam(..., description="Ruta relativa del archivo")
):
```

`get_current_user` and `Usuario` are already imported at lines 13–14. The docstring
(line 28) already claims "Requiere autenticación" — the dependency was simply never added.

### Missing role check — `incapacidades.py:318-333` (excerpt)

```python
@router.get(
    "/pendientes",
    response_model=List[IncapacidadPendienteResponse],
    summary="Listar incapacidades pendientes de auditoría",
    ...
)
async def listar_incapacidades_pendientes(
    db: AsyncSession = Depends(get_db),
    ...
    current_user: Usuario = Depends(get_current_user)
) -> List[IncapacidadPendienteResponse]:
```

Exemplar of the correct pattern in the SAME file, line 566:

```python
dependencies=[Depends(PermissionChecker([Permissions.INCAPACIDAD_READ]))],
```

### Frontend preview loading — `DocumentosViewer.tsx:61-86` (excerpt)

```tsx
useEffect(() => {
    const loadPreviews = async () => {
      for (const documento of documentos) {
        if ((isImage(documento.nombre_original) || isPdf(documento.nombre_original)) &&
            !previewUrls.has(documento.id)) {
          setLoadingPreviewIds(prev => new Set(prev).add(documento.id));
          try {
            const baseURL = import.meta.env.VITE_API_URL || '/api/v1';
            const viewUrl = `${baseURL}/${viewUrlPrefix}/${documento.id}/view`;
            setPreviewUrls(prev => new Map(prev).set(documento.id, viewUrl));
          } ...
```

The sistema-interno app has a shared axios instance with a JWT interceptor at
`apps/frontend/sistema-interno/src/lib/api.ts` — use it for the blob fetch.

### Test conventions

- Backend tests run inside Docker: from `apps/backend/`, `docker compose exec api sh -c "python -m pytest tests/<file> -v --no-cov"` (container name `incapacidades-api` if using `docker exec` directly). Per repo convention, run only the test files related to what you changed.
- `tests/conftest.py:374-387` provides `admin_token_headers` — a fixture returning `{"Authorization": "Bearer <real JWT for test_usuario>"}`. `tests/test_validaciones_endpoint.py` uses it; model new auth-header usage after that file.
- `tests/test_documento_api.py` currently calls document endpoints WITHOUT auth headers (there is even a commented-out header at line 42). These tests will start failing with 401 after the swap — updating them is part of this plan.
- Frontend tests: from `apps/frontend/sistema-interno/`, `npx vitest run src/components/incapacidades/__tests__/DocumentosViewer.test.tsx`.

## Commands you will need

| Purpose | Command | Expected on success |
|---------|---------|---------------------|
| Backend tests (documentos) | from `apps/backend/`: `docker compose exec api sh -c "python -m pytest tests/test_documento_api.py tests/test_storage_endpoint.py -v --no-cov"` | all pass |
| Backend lint | from `apps/backend/`: `make lint` | exit 0 |
| Frontend tests | from `apps/frontend/sistema-interno/`: `npx vitest run src/components/incapacidades` | all pass |
| Frontend typecheck/build | from `apps/frontend/sistema-interno/`: `npm run build` | exit 0 |

## Scope

**In scope** (the only files you should modify):
- `apps/backend/app/api/v1/endpoints/documentos.py`
- `apps/backend/app/api/v1/endpoints/storage.py`
- `apps/backend/app/api/v1/endpoints/incapacidades.py` (ONLY the `/pendientes` decorator)
- `apps/backend/tests/test_documento_api.py`
- `apps/backend/tests/test_storage_endpoint.py` (and `tests/test_filesystem_storage.py` if it hits the endpoint)
- `apps/frontend/sistema-interno/src/components/incapacidades/DocumentosViewer.tsx`
- `apps/frontend/sistema-interno/src/components/incapacidades/__tests__/DocumentosViewer.test.tsx`

**Out of scope** (do NOT touch, even though they look related):
- The PUBLIC download endpoint `incapacidades.py:229-313` (`/{numero}/documentos/{documento_id}/download`) — it is intentionally unauthenticated for the public portal, gated by a document-type whitelist. Do not add auth there.
- `app/core/security.py` — the real implementations are correct; do not modify them.
- All endpoints in `pre_incapacidades.py` — the public ones are intentionally open; the internal ones already use the real `get_current_user`.
- `apps/frontend/portal-externo/**` — the public portal does not use `DocumentosViewer` or these authed endpoints.

## Git workflow

- Branch from current branch: `bugfix/enforce-documentos-auth` (repo convention: `feature/`, `bugfix/`, `hotfix/`).
- Conventional Commits, e.g. `fix: replace placeholder auth with real JWT validation on documentos endpoints` (matches repo history, e.g. `fix: add 404 guard to validaciones endpoint`).
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 1: Swap placeholder auth for real auth in documentos.py

Delete lines 27–53 of `apps/backend/app/api/v1/endpoints/documentos.py` (the placeholder
`get_current_user`, `Permissions`, and `PermissionChecker` shown in "Current state").
Add to the imports at the top:

```python
from app.core.security import get_current_user, PermissionChecker, Permissions
```

No other changes in this file — the route decorators already reference these names.

**Verify**: `grep -n "Placeholder para get_current_user\|siempre retorna True" apps/backend/app/api/v1/endpoints/documentos.py` → no matches. `grep -n "from app.core.security import" apps/backend/app/api/v1/endpoints/documentos.py` → one match.

### Step 2: Add auth dependency to storage.py serve_file

In `apps/backend/app/api/v1/endpoints/storage.py`, change the signature at lines 20–23 to:

```python
@router.get("/files/{filepath:path}")
async def serve_file(
    filepath: str = PathParam(..., description="Ruta relativa del archivo"),
    current_user: Usuario = Depends(get_current_user)
):
```

`Depends`, `get_current_user`, and `Usuario` are already imported.

**Verify**: `grep -n "current_user" apps/backend/app/api/v1/endpoints/storage.py` → shows the new parameter inside `serve_file`.

### Step 3: Add role check to /pendientes

In `apps/backend/app/api/v1/endpoints/incapacidades.py`, add to the `/pendientes` route
decorator (lines 318–324) a dependencies entry, matching the pattern at line 566:

```python
dependencies=[Depends(PermissionChecker([Permissions.INCAPACIDAD_READ]))],
```

`PermissionChecker` and `Permissions` are already imported at line 42.

**Verify**: `sed -n '318,330p' apps/backend/app/api/v1/endpoints/incapacidades.py` → decorator includes the `dependencies=` line.

### Step 4: Update backend tests to authenticate

In `tests/test_documento_api.py`: add `admin_token_headers` to each test's fixture
parameters and pass `headers=admin_token_headers` on every `client` request that hits a
document endpoint. Model after how `tests/test_validaciones_endpoint.py` uses the fixture.
Do the same for `tests/test_storage_endpoint.py` if it calls `/storage/files/...` via the
HTTP client. Add one new test per file asserting that a request WITHOUT headers returns 401.

Note: `admin_token_headers` depends on the `test_usuario` fixture (`conftest.py:300`), which
creates the user the token refers to — including it is enough; no manual user setup needed.

**Verify**: from `apps/backend/`: `docker compose exec api sh -c "python -m pytest tests/test_documento_api.py tests/test_storage_endpoint.py tests/test_filesystem_storage.py -v --no-cov"` → all pass, including the new 401 tests.

### Step 5: Switch DocumentosViewer previews to authenticated blob fetches

In `DocumentosViewer.tsx`, replace the raw-URL construction (lines 61–86) with a fetch
through the shared axios instance (`src/lib/api.ts`, which attaches the JWT):

- For each previewable documento: `const res = await api.get(`/${viewUrlPrefix}/${documento.id}/view`, { responseType: 'blob' })`, then `URL.createObjectURL(res.data)` into the `previewUrls` map.
- Keep the existing `loadingPreviewIds` handling and the `!previewUrls.has(documento.id)` guard.
- Add a cleanup `useEffect` return that calls `URL.revokeObjectURL` for every stored object URL on unmount.
- Check how the download button consumes `getDownloadUrl` in this component/service: if the returned URL points at `/storage/files/...` and is opened with `window.open` or an `<a href>`, downloads will now 401. If so, switch the download to the same authenticated blob pattern (fetch blob → object URL → programmatic `<a download>` click → revoke). If downloads use MinIO presigned URLs instead, leave them alone.

Match the component's existing state/style conventions; update
`__tests__/DocumentosViewer.test.tsx` to mock the axios instance's blob response instead
of asserting raw URL strings.

**Verify**: `npx vitest run src/components/incapacidades` → all pass. `npm run build` → exit 0.

### Step 6: Manual smoke check (if a dev stack is running)

If the Docker stack is up: log into sistema-interno, open an incapacidad with documents,
confirm previews render and an unauthenticated `curl http://localhost:8010/api/v1/documentos/<any-uuid>/view` returns 401.
If no stack is available, state that this step was skipped.

## Test plan

- `tests/test_documento_api.py`: all existing tests now send `admin_token_headers`; new test `test_documento_endpoints_require_auth` asserts 401 without headers (parametrize over get/view/download/delete if cheap).
- `tests/test_storage_endpoint.py`: existing tests authenticated; new test asserts 401 on `/storage/files/x` without headers.
- `DocumentosViewer.test.tsx`: previews assert object-URL flow via mocked axios blob response; loading state still covered.
- Verification: the backend command in Step 4 and the vitest command in Step 5 — all pass.

## Done criteria

Machine-checkable. ALL must hold:

- [ ] `grep -rn "Dummy\|Placeholder para get_current_user" apps/backend/app/api/v1/endpoints/documentos.py` → no matches
- [ ] `grep -c "PermissionChecker" apps/backend/app/api/v1/endpoints/documentos.py` ≥ 5 and `grep -n "from app.core.security import" apps/backend/app/api/v1/endpoints/documentos.py` → 1 match
- [ ] `serve_file` signature contains `Depends(get_current_user)`
- [ ] `/pendientes` decorator contains `PermissionChecker([Permissions.INCAPACIDAD_READ])`
- [ ] Backend tests pass: `docker compose exec api sh -c "python -m pytest tests/test_documento_api.py tests/test_storage_endpoint.py tests/test_filesystem_storage.py -v --no-cov"` exits 0
- [ ] `make lint` (backend) exits 0
- [ ] `npx vitest run src/components/incapacidades` exits 0; `npm run build` exits 0 (sistema-interno)
- [ ] No files outside the in-scope list modified (`git status`)
- [ ] `plans/README.md` status row updated

## STOP conditions

Stop and report back (do not improvise) if:

- `DocumentosViewer.tsx` has uncommitted modifications in the working tree when you start (it did at planning time, 2026-06-10). Ask the operator to commit or stash first — do not build on top of unknown edits.
- The placeholder block in `documentos.py` no longer matches the excerpt (someone may have partially fixed it).
- After Step 1, document tests fail for a reason OTHER than missing auth headers (e.g. `token_version` mismatch, JWT secret mismatch inside the container) — the real `get_current_user` checks `user.token_version` against the token claim; if the fixture token does not validate, report rather than weakening the check.
- You find sistema-interno code paths other than `DocumentosViewer` that embed `/view`, `/download`, or `/storage/files` URLs directly into the DOM (grep `src/` for `"/view"` and `storage/files` first) — list them and stop; fixing them may exceed scope.
- Portal-externo turns out to call `/api/v1/documentos/*` or `/api/v1/storage/files/*` (grep its `src/` to confirm it does not) — that would mean a public flow depends on these endpoints.

## Maintenance notes

- The real `PermissionChecker` maps roles to permission strings in `app/core/security.py:230-271`. Reviewers should confirm the chosen permissions (`DOCUMENTO_*`, `INCAPACIDAD_READ`) match the roles intended for each route (AUDITOR can read/create documents; EMPRESA/EMPLEADO can also create — verify this matches product intent for upload).
- Deferred follow-up (do NOT do here): a full sweep of `incapacidades.py` lines ~814, ~869, ~894 and the internal `pre_incapacidades.py` endpoints, which authenticate but apply no `PermissionChecker`. Same pattern, separate change.
- Deferred: ownership checks (IDOR) — `DOCUMENTO_READ` lets any authenticated internal role read any document by UUID; per-object ownership for EMPRESA/EMPLEADO roles is a larger design task.
- If MinIO (presigned URLs) becomes the default storage backend, the blob-fetch in DocumentosViewer still works (it goes through the API), but the download path may switch to presigned URLs — revisit then.

# Bulk Filing UX + Email Template Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the post-submit `navigate('/consulta')` call in `RadicacionMasivaPage` with a summary modal, and replace the bare HTML string in the bulk email with a branded template showing per-row radicado details.

**Architecture:** Two independent subsystems: (A) frontend modal that enriches `res.items[]` with local `filas` state data and shows a table before navigating, and (B) a `_build_bulk_email_html()` pure function added to `email_tasks.py` consumed by a new Celery task, which the endpoint calls instead of the old bare-string approach.

**Tech Stack:** React + Tailwind v4 (CSS-variable-based, no config file) + Vitest/Testing Library (frontend); FastAPI + Celery + pytest (backend).

## Global Constraints

- Tailwind v4 in `portal-externo`: use `className` with CSS-variable utilities (`text-foreground`, `bg-muted/40`, `border-border`, `text-primary`, etc.). No `tailwind.config` color classes.
- Inline styles only in email HTML — no external CSS, no class attributes inside the `<html>` body.
- Brand hex values for email (portal-externo palette): primary `#009966`, foreground/dark-teal `#004953`, muted bg `#F0FAF8`, muted border `#CEDFDC`, table header bg `#EBF7F5`, secondary text `#52706F`.
- No changes to the `RadicacionMasivaResponse` API schema or Pydantic models.
- Modal must not navigate automatically — navigation only on "Ir a consulta" click.
- The Celery task `send_resumen_radicacion_masiva_task` is fire-and-forget (fault-isolated, same pattern as existing `send_email_task` call).
- Tests run via `docker exec incapacidades-api sh -c "cd /app && /home/appuser/.local/bin/pytest <file> -v"` for backend. Frontend: `npm test` from `apps/frontend/portal-externo/`.
- Empresa name field is `current_user.empresa.razon_social` (not `.nombre`).

---

## File Map

### Created
- `apps/frontend/portal-externo/src/components/radicacion/masiva/ResumenRadicacionModal.tsx` — modal component + `ResultadoRadicacionItem` type export

### Modified
- `apps/frontend/portal-externo/src/components/radicacion/masiva/RadicacionMasivaPage.tsx` — add modal state, replace `navigate` + toast with `setResultadoModal`, render modal
- `apps/frontend/portal-externo/src/components/radicacion/masiva/__tests__/RadicacionMasivaPage.test.tsx` — add module-level mocks for `TablaValidacion` + `useNavigate`, add 1 new test
- `apps/backend/app/tasks/email_tasks.py` — add `_build_bulk_email_html()` pure function + `send_resumen_radicacion_masiva_task` Celery task
- `apps/backend/app/api/v1/endpoints/incapacidades.py` — replace lines 1106–1120 with new task call + enriched items

### Created (tests)
- `apps/backend/tests/test_bulk_email_html.py` — unit tests for `_build_bulk_email_html()`

---

## Task 1: Frontend — Post-submission summary modal

**Files:**
- Create: `apps/frontend/portal-externo/src/components/radicacion/masiva/ResumenRadicacionModal.tsx`
- Modify: `apps/frontend/portal-externo/src/components/radicacion/masiva/RadicacionMasivaPage.tsx`
- Test: `apps/frontend/portal-externo/src/components/radicacion/masiva/__tests__/RadicacionMasivaPage.test.tsx`

**Interfaces:**
- Produces: `export interface ResultadoRadicacionItem { empleado_id: string; numero: string | null; numero_documento: string; dias_totales: number; success: boolean; error?: string; }`
- Produces: `export function ResumenRadicacionModal({ open, items, onIrAConsulta }: Props): JSX.Element | null`

- [ ] **Step 1: Write the failing test**

Add these three additions to `apps/frontend/portal-externo/src/components/radicacion/masiva/__tests__/RadicacionMasivaPage.test.tsx`:

1. At the top of the file, after the existing `vi.mock('@/hooks/use-toast', ...)` call, add:

```typescript
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return { ...actual, useNavigate: () => mockNavigate };
});

vi.mock('@/components/radicacion/masiva/TablaValidacion', () => ({
  TablaValidacion: ({
    filas,
    onAddDoc,
  }: {
    filas: { fila: number; empleado_id: string | null }[];
    onAddDoc: (id: string, tipo: string, file: File) => void;
  }) => (
    <div data-testid="tabla-validacion">
      {filas.map(
        (f) =>
          f.empleado_id && (
            <button
              key={f.fila}
              data-testid={`add-doc-${f.empleado_id}`}
              onClick={() => onAddDoc(f.empleado_id!, 'INCAPACIDAD', new File(['x'], 'inc.pdf'))}
            >
              add doc
            </button>
          ),
      )}
    </div>
  ),
}));
```

2. Inside the `describe` block, add a `beforeEach`:

```typescript
  beforeEach(() => {
    mockNavigate.mockClear();
  });
```

3. Add this test inside the `describe` block:

```typescript
  it('shows summary modal after successful submit; "Ir a consulta" navigates to /consulta', async () => {
    const { radicarMasiva, validarExcel } = await import('@/services/bulkRadicacionService');
    (validarExcel as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      filas: [
        {
          fila: 2,
          empleado_id: 'emp-001',
          datos: { numero_documento: '10000001', dias_totales: 7 },
          errores: [],
          valida: true,
        },
      ],
      total: 1,
      validas: 1,
    });
    (radicarMasiva as ReturnType<typeof vi.fn>).mockResolvedValueOnce({
      total_radicadas: 1,
      items: [
        {
          empleado_id: 'emp-001',
          incapacidad_id: 'inc-uuid-001',
          numero: 'ARL-2026-001',
          success: true,
        },
      ],
      documentos_ignorados: [],
    });

    wrap();

    // Seed filas via mocked Excel upload
    fireEvent.change(screen.getByLabelText(/subir excel/i), {
      target: { files: [new File([new Uint8Array(10)], 'a.xlsx')] },
    });
    await screen.findByTestId('tabla-validacion');

    // Add required INCAPACIDAD document via the TablaValidacion mock's trigger button
    fireEvent.click(screen.getByTestId('add-doc-emp-001'));

    // Submit
    fireEvent.click(await screen.findByRole('button', { name: /radicar incapacidades/i }));

    // Summary modal appears
    const dialog = await screen.findByRole('dialog');
    expect(dialog).toBeInTheDocument();
    expect(screen.getByText('ARL-2026-001')).toBeInTheDocument();
    expect(screen.getByText('10000001')).toBeInTheDocument();
    expect(screen.getByText('7')).toBeInTheDocument();

    // Clicking "Ir a consulta" triggers navigation, not direct navigate on submit
    expect(mockNavigate).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole('button', { name: /ir a consulta/i }));
    expect(mockNavigate).toHaveBeenCalledWith('/consulta');
  });
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd apps/frontend/portal-externo && npm test -- --reporter=verbose src/components/radicacion/masiva/__tests__/RadicacionMasivaPage.test.tsx
```

Expected: the new test fails with "Cannot find module '@/components/radicacion/masiva/ResumenRadicacionModal'" or "getByRole('dialog') could not find element" — confirms the test is wired correctly.

- [ ] **Step 3: Create `ResumenRadicacionModal.tsx`**

Create `apps/frontend/portal-externo/src/components/radicacion/masiva/ResumenRadicacionModal.tsx`:

```typescript
import { Button } from '@/components/ui/Button';

export interface ResultadoRadicacionItem {
  empleado_id: string;
  numero: string | null;
  numero_documento: string;
  dias_totales: number;
  success: boolean;
  error?: string;
}

interface Props {
  open: boolean;
  items: ResultadoRadicacionItem[];
  onIrAConsulta: () => void;
}

export function ResumenRadicacionModal({ open, items, onIrAConsulta }: Props) {
  if (!open) return null;
  const exitosas = items.filter((i) => i.success);
  const fallidas = items.filter((i) => !i.success);

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="resumen-title"
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
    >
      <div className="w-full max-w-lg rounded-xl bg-white shadow-[0_8px_30px_rgba(0,73,83,0.15)] p-6 space-y-5">
        <div>
          <h2 id="resumen-title" className="text-xl font-bold text-foreground">
            Radicación completada
          </h2>
          <p className="mt-1 text-sm text-muted-foreground">
            {exitosas.length} de {items.length} incapacidad(es) radicada(s) exitosamente.
          </p>
        </div>

        {exitosas.length > 0 && (
          <div className="overflow-x-auto rounded-lg border border-border">
            <table className="w-full text-sm">
              <thead className="bg-muted/40">
                <tr>
                  <th className="py-2 px-3 text-left font-medium text-muted-foreground">
                    Nº Documento
                  </th>
                  <th className="py-2 px-3 text-left font-medium text-muted-foreground">
                    Número de Radicado
                  </th>
                  <th className="py-2 px-3 text-right font-medium text-muted-foreground">Días</th>
                </tr>
              </thead>
              <tbody>
                {exitosas.map((item) => (
                  <tr key={item.empleado_id} className="border-t border-border">
                    <td className="py-2 px-3 text-foreground">{item.numero_documento}</td>
                    <td className="py-2 px-3 font-mono text-foreground">{item.numero ?? '—'}</td>
                    <td className="py-2 px-3 text-right text-foreground">{item.dias_totales}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {fallidas.length > 0 && (
          <div className="rounded-lg border border-[#D92D20] bg-[#D92D20]/5 p-3">
            <p className="text-sm font-semibold text-[#D92D20]">
              {fallidas.length} registro(s) no radicado(s):
            </p>
            <ul className="mt-1 list-disc pl-4 text-sm text-[#D92D20]">
              {fallidas.map((item) => (
                <li key={item.empleado_id}>
                  Documento {item.numero_documento}: {item.error ?? 'error desconocido'}
                </li>
              ))}
            </ul>
          </div>
        )}

        <div className="flex justify-end pt-2">
          <Button onClick={onIrAConsulta}>Ir a consulta</Button>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Update `RadicacionMasivaPage.tsx`**

Make these changes to `apps/frontend/portal-externo/src/components/radicacion/masiva/RadicacionMasivaPage.tsx`:

**a) Add import at the top (after existing imports):**
```typescript
import { ResumenRadicacionModal, type ResultadoRadicacionItem } from './ResumenRadicacionModal';
```

**b) Add state variable inside `RadicacionMasivaPage()` function (after existing `useState` declarations):**
```typescript
const [resultadoModal, setResultadoModal] = useState<ResultadoRadicacionItem[] | null>(null);
```

**c) Replace the entire `try` block inside `onSubmitClick` (lines 151–167 in the original):**

Old code:
```typescript
      const res = await radicarMasiva(payload, docs);
      const ignorados = res.documentos_ignorados?.length
        ? ` (${res.documentos_ignorados.length} documento(s) no almacenado(s))` : '';
      toast({ title: 'Radicación masiva completa', description: `${res.total_radicadas} incapacidad(es) radicada(s)${ignorados}` });
      navigate('/consulta');
```

New code:
```typescript
      const res = await radicarMasiva(payload, docs);
      const enriched: ResultadoRadicacionItem[] = res.items.map((item) => {
        const fila = filas.find((f) => f.empleado_id === item.empleado_id);
        return {
          empleado_id: item.empleado_id,
          numero: item.numero ?? null,
          numero_documento: String(fila?.datos.numero_documento ?? ''),
          dias_totales: Number(fila?.datos.dias_totales ?? 0),
          success: item.success,
          error: item.error,
        };
      });
      setResultadoModal(enriched);
```

**d) Add modal render at the end of the returned JSX, just before the closing `</div>` of the root element:**
```typescript
      <ResumenRadicacionModal
        open={resultadoModal !== null}
        items={resultadoModal ?? []}
        onIrAConsulta={() => navigate('/consulta')}
      />
```

- [ ] **Step 5: Run test to verify it passes**

```bash
cd apps/frontend/portal-externo && npm test -- --reporter=verbose src/components/radicacion/masiva/__tests__/RadicacionMasivaPage.test.tsx
```

Expected: all tests pass (5 existing + 1 new = 6 total). Check output for 0 failures.

- [ ] **Step 6: Run full frontend test suite to check for regressions**

```bash
cd apps/frontend/portal-externo && npm test
```

Expected: same pass count as before + 1 additional test. No regressions.

- [ ] **Step 7: Commit**

```bash
git add apps/frontend/portal-externo/src/components/radicacion/masiva/ResumenRadicacionModal.tsx \
        apps/frontend/portal-externo/src/components/radicacion/masiva/RadicacionMasivaPage.tsx \
        apps/frontend/portal-externo/src/components/radicacion/masiva/__tests__/RadicacionMasivaPage.test.tsx
git commit -m "feat(masiva): show post-submission summary modal instead of immediate navigate"
```

---

## Task 2: Backend — Branded HTML email template for bulk filing

**Files:**
- Modify: `apps/backend/app/tasks/email_tasks.py`
- Modify: `apps/backend/app/api/v1/endpoints/incapacidades.py` (lines 1105–1122)
- Create: `apps/backend/tests/test_bulk_email_html.py`

**Interfaces:**
- Consumes: nothing from Task 1
- Produces: `_build_bulk_email_html(empresa_nombre: str, fecha: str, items: list[dict]) -> str` where each item is `{"numero": str, "numero_documento": str, "dias_totales": int}`
- Produces: `send_resumen_radicacion_masiva_task(to, empresa_nombre, fecha, items)` Celery task

- [ ] **Step 1: Write the failing test**

Create `apps/backend/tests/test_bulk_email_html.py`:

```python
"""Unit tests for _build_bulk_email_html() — verifies HTML structure and brand content."""
from app.tasks.email_tasks import _build_bulk_email_html


def test_html_contains_table_structure():
    items = [
        {"numero": "ARL-2026-001", "numero_documento": "10000001", "dias_totales": 7},
        {"numero": "ARL-2026-002", "numero_documento": "20000002", "dias_totales": 14},
    ]
    html = _build_bulk_email_html("TechCorp S.A.", "25/06/2026", items)

    # Valid HTML5 skeleton
    assert "<!DOCTYPE html>" in html
    assert 'lang="es"' in html

    # Header section
    assert "Seguros Alfa" in html
    assert "Confirmación de Radicación de Incapacidades" in html

    # Summary body line
    assert "TechCorp S.A." in html
    assert "25/06/2026" in html

    # Table structure with both rows
    assert "<table" in html
    assert "<thead" in html
    assert "<tbody" in html
    assert "ARL-2026-001" in html
    assert "10000001" in html
    assert ">7<" in html
    assert "ARL-2026-002" in html
    assert "20000002" in html
    assert ">14<" in html

    # Footer
    assert "generado automáticamente" in html

    # Inline styles required (no external CSS)
    assert 'style="' in html


def test_html_item_count_in_summary_line():
    items = [
        {"numero": "ARL-X", "numero_documento": "99", "dias_totales": 3},
        {"numero": "ARL-Y", "numero_documento": "88", "dias_totales": 5},
        {"numero": "ARL-Z", "numero_documento": "77", "dias_totales": 2},
    ]
    html = _build_bulk_email_html("Empresa Test", "01/01/2026", items)
    # The summary line mentions the count of items
    assert "<strong>3</strong>" in html


def test_html_single_item():
    items = [{"numero": "SALUD-001", "numero_documento": "55555", "dias_totales": 10}]
    html = _build_bulk_email_html("Empresa Única", "15/03/2026", items)
    assert "SALUD-001" in html
    assert "55555" in html
    assert ">10<" in html
    assert "<strong>1</strong>" in html
```

- [ ] **Step 2: Run test to confirm it fails**

```bash
docker exec incapacidades-api sh -c "cd /app && /home/appuser/.local/bin/pytest tests/test_bulk_email_html.py -v"
```

Expected: `ImportError` on `_build_bulk_email_html` (function doesn't exist yet).

- [ ] **Step 3: Add `_build_bulk_email_html` and `send_resumen_radicacion_masiva_task` to `email_tasks.py`**

At the end of `apps/backend/app/tasks/email_tasks.py`, append:

```python


def _build_bulk_email_html(empresa_nombre: str, fecha: str, items: list[dict]) -> str:
    """Build a branded HTML email body for bulk filing confirmation.

    items: list of {numero, numero_documento, dias_totales}
    """
    rows_html = ""
    for item in items:
        rows_html += (
            f'<tr style="border-bottom:1px solid #CEDFDC;">'
            f'<td style="padding:10px 14px;color:#004953;">{item["numero_documento"]}</td>'
            f'<td style="padding:10px 14px;font-family:monospace;color:#004953;">{item["numero"]}</td>'
            f'<td style="padding:10px 14px;text-align:right;color:#004953;">{item["dias_totales"]}</td>'
            f'</tr>'
        )
    year = datetime.utcnow().year
    count = len(items)
    return f"""<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#F0FAF8;font-family:Roboto,Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#F0FAF8;padding:32px 0;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" style="background:#FFFFFF;border-radius:12px;overflow:hidden;box-shadow:0 4px 24px rgba(0,73,83,0.08);">
        <tr>
          <td style="background:#004953;padding:24px 32px;">
            <h1 style="margin:0;font-size:20px;color:#FFFFFF;font-weight:700;">Seguros Alfa</h1>
            <p style="margin:6px 0 0;font-size:14px;color:rgba(255,255,255,0.75);">Confirmación de Radicación de Incapacidades</p>
          </td>
        </tr>
        <tr>
          <td style="padding:32px;">
            <p style="margin:0 0 8px;font-size:15px;color:#004953;">Empresa: <strong>{empresa_nombre}</strong></p>
            <p style="margin:0 0 24px;font-size:14px;color:#52706F;">
              Se radicaron exitosamente <strong>{count}</strong> incapacidad(es) el {fecha}.
            </p>
            <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;border:1px solid #CEDFDC;">
              <thead>
                <tr style="background:#EBF7F5;">
                  <th style="padding:10px 14px;text-align:left;font-size:12px;color:#52706F;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;">Nº Documento</th>
                  <th style="padding:10px 14px;text-align:left;font-size:12px;color:#52706F;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;">Número de Radicado</th>
                  <th style="padding:10px 14px;text-align:right;font-size:12px;color:#52706F;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;">Días</th>
                </tr>
              </thead>
              <tbody>
                {rows_html}
              </tbody>
            </table>
          </td>
        </tr>
        <tr>
          <td style="background:#F0FAF8;padding:20px 32px;border-top:1px solid #CEDFDC;">
            <p style="margin:0;font-size:12px;color:#8AA8A6;text-align:center;">
              © {year} Seguros Alfa — Este correo es generado automáticamente.
            </p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""


@celery_app.task(name="send_resumen_radicacion_masiva")
def send_resumen_radicacion_masiva_task(
    to: str,
    empresa_nombre: str,
    fecha: str,
    items: list[dict],
) -> dict:
    """Send a formatted bulk filing summary email.

    items: list of {numero, numero_documento, dias_totales}
    """
    logger.info(f"[EMAIL] Enviando resumen masivo ({len(items)} items) a {to}")
    try:
        html_body = _build_bulk_email_html(empresa_nombre, fecha, items)
        success = email_service.send_email(
            to=to,
            subject="Confirmación de radicación masiva de incapacidades",
            html_body=html_body,
        )
        return {"status": "sent" if success else "failed", "to": to}
    except Exception as exc:
        logger.error(f"[EMAIL] Error al enviar resumen masivo: {exc}")
        return {"status": "error", "to": to, "error": str(exc)}
```

- [ ] **Step 4: Run test to verify it passes**

```bash
docker exec incapacidades-api sh -c "cd /app && /home/appuser/.local/bin/pytest tests/test_bulk_email_html.py -v"
```

Expected: 3 tests pass.

- [ ] **Step 5: Update the bulk submit endpoint in `incapacidades.py`**

Replace lines 1105–1122 (the `# --- Fault-isolated summary email ---` block) in `apps/backend/app/api/v1/endpoints/incapacidades.py`:

Old code:
```python
    # --- Fault-isolated summary email -----------------------------------------
    if result.total_radicadas and current_user.empresa.email_contacto:
        from app.tasks.email_tasks import send_email_task
        numeros = [i.numero for i in result.items if i.success]
        cuerpo = (
            "Se radicaron las siguientes incapacidades:<br>"
            + "<br>".join(f"- {n}" for n in numeros)
        )
        try:
            send_email_task.delay(
                to=current_user.empresa.email_contacto,
                subject="Confirmación de radicación masiva de incapacidades",
                html_body=cuerpo,
            )
        except Exception as exc:
            logger.error(f"No se pudo encolar el correo de resumen masivo: {exc}")
```

New code:
```python
    # --- Fault-isolated summary email -----------------------------------------
    if result.total_radicadas and current_user.empresa.email_contacto:
        from app.tasks.email_tasks import send_resumen_radicacion_masiva_task
        row_by_empleado: dict = {str(r["empleado_id"]): r for r in raw_rows if isinstance(r, dict)}
        email_items = [
            {
                "numero": i.numero,
                "numero_documento": str(row_by_empleado.get(str(i.empleado_id), {}).get("numero_documento", "N/A")),
                "dias_totales": int(row_by_empleado.get(str(i.empleado_id), {}).get("dias_totales") or 0),
            }
            for i in result.items
            if i.success and i.numero
        ]
        try:
            send_resumen_radicacion_masiva_task.delay(
                to=current_user.empresa.email_contacto,
                empresa_nombre=current_user.empresa.razon_social,
                fecha=date.today().strftime("%d/%m/%Y"),
                items=email_items,
            )
        except Exception as exc:
            logger.error(f"No se pudo encolar el correo de resumen masivo: {exc}")
```

- [ ] **Step 6: Run the existing bulk submit test to check for regressions**

```bash
docker exec incapacidades-api sh -c "cd /app && /home/appuser/.local/bin/pytest tests/test_bulk_submit.py tests/test_bulk_email_html.py -v"
```

Expected: all tests pass with no failures.

- [ ] **Step 7: Commit**

```bash
git add apps/backend/app/tasks/email_tasks.py \
        apps/backend/app/api/v1/endpoints/incapacidades.py \
        apps/backend/tests/test_bulk_email_html.py
git commit -m "feat(email): branded HTML template for bulk filing confirmation"
```

---

## Self-Review Checklist

**Spec coverage:**
- ✅ Modal appears after successful submit (Task 1, Step 4c)
- ✅ Modal shows Nº documento, Número de radicado, Días (Step 3, `ResumenRadicacionModal.tsx`)
- ✅ Failed rows shown separately in modal (Step 3, `fallidas` section)
- ✅ Single "Ir a consulta" button triggers `navigate('/consulta')` (Steps 3–4)
- ✅ No `navigate('/consulta')` on raw submit success — only via modal button (Step 4c removes it)
- ✅ Rounded corners, soft shadow, existing palette via Tailwind CSS-var utilities (Step 3)
- ✅ HTML email with inline styles only (Task 2, Step 3)
- ✅ Brand hex values used (`#004953`, `#009966`, `#F0FAF8`, `#CEDFDC`, `#EBF7F5`, `#52706F`)
- ✅ Header "Seguros Alfa" + subtitle "Confirmación de Radicación de Incapacidades" (Step 3)
- ✅ Summary line: "Se radicaron exitosamente X incapacidad(es) el [date]." (Step 3)
- ✅ Table: Nº, Número de Radicado, Empleado doc, Días (Step 3)
- ✅ Footer: "© 2026 Seguros Alfa — Este correo es generado automáticamente." (Step 3)
- ✅ Endpoint passes per-row detail (doc number + dias) to email function (Task 2, Step 5)
- ✅ Backend test: HTML contains table structure and key fields (Task 2, Steps 1–4)
- ✅ Frontend test: modal appears with correct data, "Ir a consulta" navigates (Task 1, Steps 1–5)

**No placeholders found.**

**Type consistency:**
- `ResultadoRadicacionItem` exported from `ResumenRadicacionModal.tsx`, imported in `RadicacionMasivaPage.tsx` — consistent field names (`empleado_id`, `numero`, `numero_documento`, `dias_totales`, `success`, `error`)
- `_build_bulk_email_html(empresa_nombre, fecha, items)` — same signature in test (Task 2 Step 1) and implementation (Step 3)
- `send_resumen_radicacion_masiva_task.delay(to, empresa_nombre, fecha, items)` — same kwargs in endpoint (Step 5) as task definition (Step 3)

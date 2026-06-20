---
name: security
description: >
  Skill de seguridad para el sistema de incapacidades. Cubre el bridge JWT
  Laravel→FastAPI, validaciones Pydantic v2, RBAC, protección de endpoints
  y prácticas OWASP aplicadas al stack específico del proyecto.
---

# Seguridad — Sistema de Incapacidades

## Contexto

Sistema FastAPI que recibe JWT emitidos por Laravel y los valida con un `JWT_SECRET` compartido.
No hay login propio — la autenticación es un bridge, no un sistema independiente.

Referencia completa: [`docs/seguridad/MODULO_AUTENTICACION_STATUS.md`](../../../../docs/seguridad/MODULO_AUTENTICACION_STATUS.md)

---

## JWT Bridge Laravel → FastAPI

**Algoritmo**: HS256 con `JWT_SECRET` compartido en variable de entorno.

**Claims requeridos** (deben estar presentes o el token es rechazado):

| Claim | Descripción |
|---|---|
| `iss` | Emisor — Laravel |
| `iat` | Issued at — timestamp |
| `exp` | Expiración — 15 min para access token |
| `nbf` | Not before |
| `sub` | Subject — ID del usuario (integer como string) |
| `jti` | JWT ID — identificador único del token |

**Access token**: 15 minutos. **Refresh token**: 7 días, almacenado como SHA256 hash en DB (tabla `refresh_tokens`).

### Validación en FastAPI

```python
# El decorador estándar — aplica a todos los endpoints protegidos
@router.get("/ruta")
async def endpoint(current_user: User = Depends(get_current_user)):
    ...
```

`get_current_user` en `app/api/deps.py`:
1. Extrae `Authorization: Bearer <token>` del header
2. Decodifica con `jwt.decode(token, JWT_SECRET, algorithms=["HS256"])`
3. Valida claims: `exp`, `nbf`, `iss`, `sub`
4. Consulta usuario en DB por `sub` — rechaza si no existe o está inactivo
5. Retorna objeto `User` con rol

---

## RBAC — Roles y permisos

**Roles**: `ADMIN | AUDITOR | APROBADOR | EMPRESA | EMPLEADO | READONLY`

Nunca hardcodear IDs ni strings de rol en lógica — usar el enum:

```python
from app.utils.enums import RolUsuario

if current_user.rol == RolUsuario.ADMIN:
    ...
```

### Restricción por rol en endpoints

```python
from app.api.deps import require_roles

@router.post("/incapacidades/{id}/aprobar")
async def aprobar(
    id: int,
    current_user: User = Depends(require_roles([RolUsuario.ADMIN, RolUsuario.APROBADOR]))
):
    ...
```

### Mapa de acciones por rol

| Acción | Roles autorizados |
|---|---|
| Radicar (portal público) | Sin auth (endpoint público) |
| Listar pendientes / auditar | ADMIN, AUDITOR |
| Aprobar / Rechazar / Pagar | ADMIN, APROBADOR |
| Consulta pública (portal) | Sin auth |
| Gestión de usuarios | Solo ADMIN |
| Lectura general | ADMIN, AUDITOR, APROBADOR, READONLY |

---

## Validaciones Pydantic v2

```python
from pydantic import BaseModel, field_validator, model_validator

class RadicarIncapacidadSchema(BaseModel):
    tipo_incapacidad: str  # 'ARL' | 'SALUD'
    fecha_inicio: date
    fecha_fin: date
    codigo_cie10: str

    @field_validator('codigo_cie10')
    @classmethod
    def validar_cie10(cls, v: str) -> str:
        v = v.strip().upper()
        if not re.match(r'^[A-Z]\d{3}(\.\d{1,2})?$', v):
            raise ValueError('Formato CIE-10 inválido. Ejemplo: A09, J18.1')
        return v

    @model_validator(mode='after')
    def fechas_coherentes(self) -> 'RadicarIncapacidadSchema':
        if self.fecha_fin < self.fecha_inicio:
            raise ValueError('fecha_fin debe ser posterior a fecha_inicio')
        return self
```

**Reglas**:
- Siempre usar `field_validator` para sanitización (trim, uppercase)
- Nunca confiar en datos de entrada — validar formato Y semántica
- Usar `model_validator` para validaciones cruzadas entre campos

---

## Protección de endpoints FastAPI

### Rate limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/incapacidades/radicar")
@limiter.limit("10/minute")  # máximo 10 radicaciones por IP por minuto
async def radicar(request: Request, ...):
    ...
```

### Prevención de inyección SQL

- **Siempre usar SQLAlchemy ORM o Core** — nunca concatenar strings en queries
- Para búsqueda de texto: usar `ilike` de SQLAlchemy, no `LIKE` con f-strings
- Para full-text search (CIE-10): `func.to_tsvector` + `func.plainto_tsquery`

### Sanitización de archivos (MinIO upload)

Validar siempre las tres capas:
1. **Extensión**: `['pdf', 'jpg', 'jpeg', 'png']`
2. **MIME type**: verificar `content_type` del upload
3. **Firma binaria (magic bytes)**: leer primeros 8 bytes y comparar con firmas conocidas

```python
MAGIC_BYTES = {
    b'\x25\x50\x44\x46': 'pdf',     # %PDF
    b'\xff\xd8\xff':      'jpg',
    b'\x89\x50\x4e\x47': 'png',
}
```

---

## Checklist de seguridad por endpoint nuevo

- [ ] ¿Requiere autenticación? → agregar `Depends(get_current_user)`
- [ ] ¿Requiere rol específico? → usar `Depends(require_roles([...]))`
- [ ] ¿Recibe datos del usuario? → validar con schema Pydantic v2
- [ ] ¿Hace queries a DB? → solo ORM/Core, nunca strings raw
- [ ] ¿Acepta archivos? → validar extensión + MIME + magic bytes
- [ ] ¿Es un endpoint público de alta demanda? → agregar rate limit
- [ ] ¿Retorna datos sensibles? → verificar que el usuario solo accede a sus propios datos (o es ADMIN)

---

## Referencias

- [`docs/seguridad/MODULO_AUTENTICACION_STATUS.md`](../../../../docs/seguridad/MODULO_AUTENTICACION_STATUS.md) — módulo de auth completo
- [`docs/seguridad/AUTENTICACION_COMPLETADO.md`](../../../../docs/seguridad/AUTENTICACION_COMPLETADO.md) — tests de auth (20/20)
- [`docs/seguridad/FIX_ERROR_500_APROBACION.md`](../../../../docs/seguridad/FIX_ERROR_500_APROBACION.md) — bug de serialización Pydantic con ORM

# 🚀 INICIO RÁPIDO - Fase 1 Backend

**Tarea**: Implementar Solicitante + Campos Médico + Catálogo CIE-10  
**Duración estimada**: 2-3 días  
**Documento completo**: [`MEJORAS_SOLICITANTE_Y_CATALOGOS.md`](MEJORAS_SOLICITANTE_Y_CATALOGOS.md)

---

## 📋 Checklist de Implementación

### Paso 1: Crear Módulo Solicitante

- [ ] `app/models/solicitante.py` - Modelo SQLAlchemy
- [ ] `app/schemas/solicitante.py` - Schemas Pydantic (Create, Update, Response)
- [ ] `app/db/repositories/solicitante_repository.py` - Repository con búsqueda por correo
- [ ] `app/services/solicitante_service.py` - Service con validaciones
- [ ] `app/api/v1/endpoints/solicitantes.py` - Endpoints REST (POST, GET, GET/search)
- [ ] Registrar router en `app/api/v1/router.py`

### Paso 2: Modificar Módulo Incapacidad

- [ ] Agregar campos a `app/models/incapacidad.py`:
  - `solicitante_id` (FK UUID)
  - `nombre_medico` (String 200)
  - `registro_medico` (String 50)
  - Relación con `Solicitante`
- [ ] Actualizar `app/schemas/incapacidad.py` (Create, Response)

### Paso 3: Crear Módulo Catálogo CIE-10

- [ ] `app/models/catalogo_cie10.py` - Modelo (codigo PK, descripcion)
- [ ] `app/schemas/catalogo.py` - Schema CIE10Response
- [ ] `app/db/repositories/catalogo_repository.py` - Repository con búsqueda
- [ ] `app/services/catalogo_service.py` - Service
- [ ] `app/api/v1/endpoints/catalogos.py` - Endpoints (GET /cie10?q=, GET /cie10/{codigo})
- [ ] Registrar router en `app/api/v1/router.py`

### Paso 4: Migraciones y Datos

- [ ] Migración: `alembic revision --autogenerate -m "agregar_solicitante_y_campos_medico"`
- [ ] Migración: `alembic revision --autogenerate -m "crear_catalogo_cie10"`
- [ ] Aplicar: `alembic upgrade head`
- [ ] Script: `backend/scripts/seed_cie10.py` (poblar catálogo)
- [ ] Archivo: `backend/data/cie10.csv` con códigos oficiales

### Paso 5: Tests

- [ ] `tests/test_solicitante_service.py` (15+ tests)
- [ ] `tests/test_catalogo_service.py` (8+ tests)
- [ ] Actualizar tests de incapacidad
- [ ] Ejecutar: `pytest --cov=app`

### Paso 6: Documentación

- [ ] `backend/MODULO_SOLICITANTE_COMPLETADO.md`
- [ ] `backend/MODULO_CATALOGOS_COMPLETADO.md`
- [ ] Actualizar `docs/02_MODELO_DATOS.md`
- [ ] Actualizar `docs/03_API_ENDPOINTS.md`

---

## 🎯 Nuevos Endpoints

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/v1/solicitantes` | Crear solicitante |
| GET | `/api/v1/solicitantes` | Listar solicitantes |
| GET | `/api/v1/solicitantes/search?correo={email}` | Buscar por correo |
| GET | `/api/v1/solicitantes/{id}` | Obtener por ID |
| PUT | `/api/v1/solicitantes/{id}` | Actualizar solicitante |
| GET | `/api/v1/catalogos/cie10?q={query}` | Buscar CIE-10 |
| GET | `/api/v1/catalogos/cie10/{codigo}` | Obtener CIE-10 por código |

---

## 💻 Comandos Rápidos

```bash
# Crear migraciones
docker compose exec api alembic revision --autogenerate -m "agregar_solicitante_y_campos_medico"
docker compose exec api alembic revision --autogenerate -m "crear_catalogo_cie10"

# Aplicar migraciones
docker compose exec api alembic upgrade head

# Poblar catálogo
docker compose exec api python scripts/seed_cie10.py

# Tests
docker compose exec api pytest tests/test_solicitante_service.py -v
docker compose exec api pytest tests/test_catalogo_service.py -v

# Verificar Swagger
# http://localhost:8010/docs
```

---

## 📐 Modelo de Datos

### Tabla: solicitante

| Campo | Tipo | Constraints |
|-------|------|-------------|
| id | UUID | PK |
| correo | VARCHAR(100) | UNIQUE, NOT NULL, INDEX |
| nombres | VARCHAR(100) | NOT NULL |
| apellidos | VARCHAR(100) | NOT NULL |
| telefono | VARCHAR(20) | NULL |
| created_at | TIMESTAMP | NOT NULL |
| updated_at | TIMESTAMP | NOT NULL |

### Modificaciones a: incapacidad

| Campo | Tipo | Constraints |
|-------|------|-------------|
| solicitante_id | UUID | FK(solicitante.id), NULL, INDEX |
| nombre_medico | VARCHAR(200) | NULL |
| registro_medico | VARCHAR(50) | NULL |

### Tabla: catalogo_cie10

| Campo | Tipo | Constraints |
|-------|------|-------------|
| codigo | VARCHAR(10) | PK |
| descripcion | TEXT | NOT NULL |

---

## ✅ Criterios de Éxito

- [ ] 7 nuevos endpoints funcionando
- [ ] Búsqueda por correo retorna resultados
- [ ] Búsqueda CIE-10 por código y descripción
- [ ] Tests >80% cobertura
- [ ] Migraciones aplicadas sin errores
- [ ] Swagger actualizado
- [ ] Documentación completa

---

**Ver detalles completos**: [`MEJORAS_SOLICITANTE_Y_CATALOGOS.md`](MEJORAS_SOLICITANTE_Y_CATALOGOS.md)

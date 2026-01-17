# Mejoras: Solicitante y Catálogos CIE-10

**Fecha de creación**: 16 de enero de 2026  
**Versión**: 1.0.0  
**Estado**: Planificación

---

## 📋 Resumen Ejecutivo

Este documento organiza las mejoras necesarias para agregar:
1. **Solicitante**: Persona que radica la incapacidad (puede ser diferente al empleado/afiliado)
2. **Datos del Médico**: Nombre y registro médico en la incapacidad
3. **Catálogo CIE-10**: Búsqueda de diagnósticos por código o descripción

---

## 🎯 Objetivos

### Funcionales
- Capturar datos del solicitante (correo, nombres, apellidos, teléfono)
- Vincular solicitante con incapacidad radicada
- Permitir autocompletado de solicitante por correo
- Agregar campos de médico tratante a la incapacidad
- Facilitar búsqueda de códigos CIE-10

### Técnicos
- Mantener arquitectura Clean Architecture
- Tests >80% cobertura en nuevos módulos
- Documentación actualizada
- 0 errores TypeScript
- Build exitoso

---

## 📦 Fases del Proyecto

### Fase 1: Backend - Solicitante y Catálogos ⏳

**Duración estimada**: 2-3 días  
**Prioridad**: 🔴 Alta

#### Tareas:

1. **Crear módulo Solicitante**
   - [ ] Modelo SQLAlchemy `Solicitante`
   - [ ] Schema Pydantic `SolicitanteCreate`, `SolicitanteResponse`
   - [ ] Repository `SolicitanteRepository`
   - [ ] Service `SolicitanteService`
   - [ ] Endpoints REST:
     - `POST /api/v1/solicitantes` - Crear solicitante
     - `GET /api/v1/solicitantes` - Listar solicitantes
     - `GET /api/v1/solicitantes/search?correo={email}` - Buscar por correo
     - `GET /api/v1/solicitantes/{id}` - Obtener por ID
   - [ ] Migración Alembic para tabla `solicitante`
   - [ ] Tests (>80% cobertura)

2. **Modificar módulo Incapacidad**
   - [ ] Agregar campo `solicitante_id` (FK a solicitante)
   - [ ] Agregar campos `nombre_medico` y `registro_medico`
   - [ ] Actualizar schemas `IncapacidadCreate`, `IncapacidadResponse`
   - [ ] Actualizar repository y service
   - [ ] Migración Alembic para nuevos campos
   - [ ] Actualizar tests

3. **Crear módulo Catálogos**
   - [ ] Modelo SQLAlchemy `CatalogoCIE10` (si se persiste en BD)
   - [ ] O servicio que consuma archivo JSON/CSV con códigos CIE-10
   - [ ] Schema Pydantic `CIE10Response`
   - [ ] Service `CatalogoService`
   - [ ] Endpoints REST:
     - `GET /api/v1/catalogos/cie10?q={query}` - Buscar por código o descripción
     - `GET /api/v1/catalogos/cie10/{codigo}` - Obtener por código exacto
   - [ ] Tests (>80% cobertura)

4. **Documentación**
   - [ ] Actualizar `docs/02_MODELO_DATOS.md` con tabla Solicitante
   - [ ] Actualizar `docs/03_API_ENDPOINTS.md` con nuevos endpoints
   - [ ] Crear `backend/MODULO_SOLICITANTE_COMPLETADO.md`
   - [ ] Crear `backend/MODULO_CATALOGOS_COMPLETADO.md`

---

### Fase 2: Frontend - Integración Solicitante ⏳

**Duración estimada**: 2-3 días  
**Prioridad**: 🔴 Alta  
**Depende de**: Fase 1

#### Tareas:

1. **Crear módulo Solicitante**
   - [ ] Tipos TypeScript en `types/api.ts`
   - [ ] Servicio `solicitanteService.ts` con hooks React Query
   - [ ] Componente `SolicitanteForm.tsx` con autocompletado
   - [ ] Schema Zod `solicitanteSchema`
   - [ ] Tests (>70% cobertura)

2. **Modificar Wizard - Nuevo Paso 0**
   - [ ] Crear `DatosSolicitanteForm.tsx`
   - [ ] Integrar autocompletado por correo
   - [ ] Actualizar `RadicarIncapacidadWizard.tsx` para 6 pasos
   - [ ] Actualizar navegación (Paso 0 → 1 → 2 → 3 → 4 → 5)
   - [ ] Tests del nuevo paso

3. **Modificar Paso 3 - Datos Médico**
   - [ ] Agregar campos `nombre_medico` y `registro_medico` a `DatosIncapacidadForm.tsx`
   - [ ] Actualizar schema Zod `datosIncapacidadSchema`
   - [ ] Actualizar `ResumenRadicacionForm.tsx` para mostrar datos del médico
   - [ ] Tests actualizados

4. **Modificar búsqueda CIE-10**
   - [ ] Crear servicio `catalogoService.ts`
   - [ ] Crear componente `AutocompleteCIE10.tsx` con búsqueda
   - [ ] Integrar en `DatosIncapacidadForm.tsx`
   - [ ] Mostrar código + descripción completa
   - [ ] Tests

5. **Documentación**
   - [ ] Crear `frontend/portal-externo/WIZARD_MEJORAS_SOLICITANTE.md`
   - [ ] Actualizar `ESTADO_PROYECTO_FRONTEND.md`

---

### Fase 3: Testing y Documentación ⏳

**Duración estimada**: 1 día  
**Prioridad**: 🟡 Media  
**Depende de**: Fase 1, Fase 2

#### Tareas:

1. **Testing Integración**
   - [ ] Tests end-to-end del flujo completo
   - [ ] Verificar radicación con solicitante
   - [ ] Verificar búsqueda CIE-10
   - [ ] Verificar datos de médico se guardan correctamente

2. **Documentación Final**
   - [ ] Actualizar `ESTADO_PROYECTO.md`
   - [ ] Screenshots del nuevo wizard
   - [ ] Guía de uso para usuarios finales

---

## 📊 Modelo de Datos - Tabla Solicitante

### Tabla: `solicitante`

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| `id` | UUID | PK, NOT NULL, DEFAULT uuid_generate_v4() | ID único |
| `correo` | VARCHAR(100) | UNIQUE, NOT NULL, INDEX | Email del solicitante |
| `nombres` | VARCHAR(100) | NOT NULL | Nombres |
| `apellidos` | VARCHAR(100) | NOT NULL | Apellidos |
| `telefono` | VARCHAR(20) | NULL | Teléfono de contacto |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Fecha de creación |
| `updated_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Fecha de actualización |

### Modificaciones a `incapacidad`

Agregar campos:

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| `solicitante_id` | UUID | FK(solicitante.id), NULL, INDEX | Referencia al solicitante |
| `nombre_medico` | VARCHAR(200) | NULL | Nombre del médico tratante |
| `registro_medico` | VARCHAR(50) | NULL | Registro médico profesional |

### Relación

```
SOLICITANTE 1──N INCAPACIDAD
```

Un solicitante puede radicar múltiples incapacidades (para diferentes empleados/afiliados).

---

## 🔧 Catálogo CIE-10

### Opción 1: Tabla en Base de Datos (Recomendado para búsquedas rápidas)

```sql
CREATE TABLE catalogo_cie10 (
    codigo VARCHAR(10) PRIMARY KEY,
    descripcion TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_cie10_descripcion ON catalogo_cie10 USING GIN(to_tsvector('spanish', descripcion));
```

**Ventajas**:
- Búsquedas muy rápidas con índices full-text
- Fácil actualización
- Queries SQL nativas

**Desventajas**:
- Requiere migración inicial con ~14,000 códigos

### Opción 2: Archivo JSON (Más simple)

```json
[
  {
    "codigo": "A00",
    "descripcion": "Cólera"
  },
  {
    "codigo": "A00.0",
    "descripcion": "Cólera debido a Vibrio cholerae 01, biotipo cholerae"
  },
  ...
]
```

**Ventajas**:
- No requiere migración
- Fácil de actualizar el archivo
- Menor complejidad

**Desventajas**:
- Búsquedas más lentas (en memoria)
- Requiere cargar archivo en cada inicio

**Recomendación**: Opción 1 (Base de Datos) para mejor performance.

---

## 🎨 Cambios en UI - Wizard

### Nuevo Flujo (6 pasos)

```
Paso 0: Datos del Solicitante ⭐ NUEVO
   ┌────────────────────────────────┐
   │ • Correo (con autocompletado)  │
   │ • Nombres                      │
   │ • Apellidos                    │
   │ • Teléfono                     │
   └────────────────────────────────┘
            │
            ▼
Paso 1: Tipo de Incapacidad
   ┌─────────┐  ┌─────────┐
   │   ARL   │  │  SALUD  │
   └─────────┘  └─────────┘
            │
            ▼
Paso 2: Datos Personales
   (Empleado o Afiliado)
            │
            ▼
Paso 3: Datos de Incapacidad ⭐ MODIFICADO
   ┌────────────────────────────────┐
   │ • Fechas                       │
   │ • Diagnóstico CIE-10 (búsqueda)│
   │ • Nombre del Médico ⭐ NUEVO   │
   │ • Registro Médico ⭐ NUEVO     │
   └────────────────────────────────┘
            │
            ▼
Paso 4: Documentos
            │
            ▼
Paso 5: Resumen y Radicación
```

### Componente AutocompleteCIE10

**Características**:
- Input con búsqueda en tiempo real
- Debounce de 300ms para evitar requests excesivos
- Mostrar formato: `A00.0 - Cólera debido a Vibrio cholerae`
- Mínimo 3 caracteres para buscar
- Límite de 10 resultados
- Highlight del texto coincidente

---

## 📝 Endpoints API - Resumen

### Nuevos Endpoints

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `POST` | `/api/v1/solicitantes` | Crear solicitante |
| `GET` | `/api/v1/solicitantes` | Listar solicitantes |
| `GET` | `/api/v1/solicitantes/search?correo={email}` | Buscar por correo |
| `GET` | `/api/v1/solicitantes/{id}` | Obtener por ID |
| `GET` | `/api/v1/catalogos/cie10?q={query}&limit=10` | Buscar CIE-10 |
| `GET` | `/api/v1/catalogos/cie10/{codigo}` | Obtener CIE-10 por código |

### Endpoints Modificados

| Método | Endpoint | Cambios |
|--------|----------|---------|
| `POST` | `/api/v1/incapacidades` | Agregar: `solicitante_id`, `nombre_medico`, `registro_medico` |

---

## ✅ Criterios de Aceptación

### Backend

- [ ] Tabla `solicitante` creada con migración Alembic
- [ ] CRUD completo de solicitantes funcional
- [ ] Búsqueda por correo retorna resultados correctos
- [ ] Campo `solicitante_id` en `incapacidad` funciona
- [ ] Campos `nombre_medico` y `registro_medico` se guardan correctamente
- [ ] Endpoint de catálogo CIE-10 retorna resultados por código
- [ ] Endpoint de catálogo CIE-10 retorna resultados por descripción
- [ ] Tests >80% cobertura en nuevos módulos
- [ ] 0 errores en `pytest`
- [ ] Migración aplicada sin errores
- [ ] Swagger actualizado con nuevos endpoints

### Frontend

- [ ] Nuevo Paso 0 para datos del solicitante
- [ ] Autocompletado de solicitante funciona
- [ ] Campos de médico aparecen en Paso 3
- [ ] Búsqueda CIE-10 muestra código + descripción
- [ ] Resumen muestra datos del solicitante
- [ ] Resumen muestra datos del médico
- [ ] DTO enviado al backend incluye todos los campos
- [ ] Tests >70% cobertura en componentes modificados
- [ ] 0 errores TypeScript
- [ ] Build exitoso
- [ ] 217+ tests pasando

---

## 📚 Recursos

### Fuente de Datos CIE-10

**Oficial**:
- OPS/OMS: https://www.paho.org/es/temas/clasificacion-internacional-enfermedades
- Ministerio de Salud Colombia: https://www.minsalud.gov.co/

**Archivos descargables**:
- CSV con códigos CIE-10 en español
- JSON con estructura código + descripción

### Referencias Técnicas

- SQLAlchemy Full-Text Search: https://docs.sqlalchemy.org/en/20/dialects/postgresql.html#full-text-search
- React Query Autocomplete: https://tanstack.com/query/latest/docs/react/guides/queries
- Zod Email Validation: https://zod.dev/?id=strings

---

## 🚀 Siguiente Paso

**Ver prompt detallado para Fase 1 a continuación** ⬇️

---

# PROMPT PARA FASE 1 - BACKEND

## Contexto

Actualmente tenemos un sistema de gestión de incapacidades con backend al 100% funcional (FastAPI + PostgreSQL). Necesitamos agregar funcionalidad para capturar datos del **solicitante** (persona que radica la incapacidad), agregar información del **médico tratante**, y crear un **catálogo de búsqueda de códigos CIE-10**.

### Estado Actual
- 11 modelos SQLAlchemy implementados
- 11 repositories, services y endpoints
- Arquitectura Clean Architecture
- 149+ tests con 87% cobertura
- Migraciones con Alembic

---

## Objetivo

Implementar en el **backend** los siguientes módulos:

1. **Módulo Solicitante**: Tabla + CRUD + búsqueda por correo
2. **Modificación a Incapacidad**: Agregar FK solicitante + campos de médico
3. **Módulo Catálogos**: Endpoint para búsqueda de códigos CIE-10

---

## Requerimientos Específicos

### 1. Tabla Solicitante

**Ubicación**: `app/models/solicitante.py`

```python
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseModel
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.incapacidad import Incapacidad

class Solicitante(BaseModel):
    __tablename__ = "solicitante"
    
    correo: Mapped[str] = mapped_column(
        String(100), 
        unique=True, 
        nullable=False, 
        index=True,
        comment="Email del solicitante (único)"
    )
    nombres: Mapped[str] = mapped_column(
        String(100), 
        nullable=False,
        comment="Nombres del solicitante"
    )
    apellidos: Mapped[str] = mapped_column(
        String(100), 
        nullable=False,
        comment="Apellidos del solicitante"
    )
    telefono: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        comment="Teléfono de contacto"
    )
    
    # Relación con incapacidades
    incapacidades: Mapped[List["Incapacidad"]] = relationship(
        back_populates="solicitante",
        lazy="selectin"
    )
```

**Validaciones**:
- Correo: Formato email válido, único en la tabla
- Nombres: 2-100 caracteres, solo letras y espacios
- Apellidos: 2-100 caracteres, solo letras y espacios
- Teléfono: Opcional, 7-20 dígitos

### 2. Modificar Tabla Incapacidad

**Ubicación**: `app/models/incapacidad.py`

Agregar campos:

```python
from sqlalchemy import ForeignKey
from uuid import UUID

class Incapacidad(BaseModel):
    # ... campos existentes ...
    
    # NUEVO: Referencia al solicitante
    solicitante_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("solicitante.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Solicitante que radicó la incapacidad"
    )
    
    # NUEVO: Datos del médico tratante
    nombre_medico: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        comment="Nombre completo del médico tratante"
    )
    registro_medico: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Registro médico profesional"
    )
    
    # Relación con solicitante
    solicitante: Mapped["Solicitante"] = relationship(
        back_populates="incapacidades",
        lazy="selectin"
    )
```

### 3. Schemas Pydantic

**Ubicación**: `app/schemas/solicitante.py`

```python
from pydantic import BaseModel, EmailStr, field_validator, ConfigDict
from uuid import UUID
from datetime import datetime
import re

class SolicitanteBase(BaseModel):
    correo: EmailStr
    nombres: str
    apellidos: str
    telefono: str | None = None
    
    @field_validator('nombres', 'apellidos')
    @classmethod
    def validate_nombres(cls, v: str) -> str:
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]{2,100}$', v):
            raise ValueError('Solo letras y espacios, 2-100 caracteres')
        return v.strip()
    
    @field_validator('telefono')
    @classmethod
    def validate_telefono(cls, v: str | None) -> str | None:
        if v and not re.match(r'^\d{7,20}$', v):
            raise ValueError('Teléfono debe tener 7-20 dígitos')
        return v

class SolicitanteCreate(SolicitanteBase):
    pass

class SolicitanteUpdate(BaseModel):
    nombres: str | None = None
    apellidos: str | None = None
    telefono: str | None = None

class SolicitanteResponse(SolicitanteBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
```

**Actualizar**: `app/schemas/incapacidad.py`

```python
class IncapacidadCreate(BaseModel):
    # ... campos existentes ...
    
    # NUEVO
    solicitante_id: UUID | None = None
    nombre_medico: str | None = None
    registro_medico: str | None = None

class IncapacidadResponse(BaseModel):
    # ... campos existentes ...
    
    # NUEVO
    solicitante_id: UUID | None = None
    solicitante: SolicitanteResponse | None = None
    nombre_medico: str | None = None
    registro_medico: str | None = None
```

### 4. Repository

**Ubicación**: `app/db/repositories/solicitante_repository.py`

```python
from app.db.repositories.base import BaseRepository
from app.models.solicitante import Solicitante
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

class SolicitanteRepository(BaseRepository[Solicitante]):
    def __init__(self, db: AsyncSession):
        super().__init__(Solicitante, db)
    
    async def get_by_correo(self, correo: str) -> Solicitante | None:
        """Buscar solicitante por correo"""
        query = select(Solicitante).where(Solicitante.correo == correo.lower())
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def search_by_correo(self, correo_partial: str, limit: int = 10) -> list[Solicitante]:
        """Buscar solicitantes cuyo correo contenga el texto"""
        query = (
            select(Solicitante)
            .where(Solicitante.correo.ilike(f"%{correo_partial}%"))
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())
```

### 5. Service

**Ubicación**: `app/services/solicitante_service.py`

```python
from app.db.repositories.solicitante_repository import SolicitanteRepository
from app.schemas.solicitante import SolicitanteCreate, SolicitanteUpdate
from app.models.solicitante import Solicitante
from app.core.exceptions import NotFoundException, ValidationException
from uuid import UUID

class SolicitanteService:
    def __init__(self, repository: SolicitanteRepository):
        self.repository = repository
    
    async def create_solicitante(self, data: SolicitanteCreate) -> Solicitante:
        """Crear nuevo solicitante"""
        # Verificar si el correo ya existe
        existing = await self.repository.get_by_correo(data.correo)
        if existing:
            raise ValidationException(f"Ya existe un solicitante con el correo {data.correo}")
        
        solicitante = Solicitante(
            correo=data.correo.lower(),
            nombres=data.nombres,
            apellidos=data.apellidos,
            telefono=data.telefono
        )
        return await self.repository.create(solicitante)
    
    async def get_solicitante(self, solicitante_id: UUID) -> Solicitante:
        """Obtener solicitante por ID"""
        solicitante = await self.repository.get(solicitante_id)
        if not solicitante:
            raise NotFoundException(f"Solicitante {solicitante_id} no encontrado")
        return solicitante
    
    async def search_by_correo(self, correo: str, limit: int = 10) -> list[Solicitante]:
        """Buscar solicitantes por correo"""
        return await self.repository.search_by_correo(correo, limit)
    
    async def list_solicitantes(self, skip: int = 0, limit: int = 100) -> list[Solicitante]:
        """Listar solicitantes"""
        return await self.repository.list(skip=skip, limit=limit)
    
    async def update_solicitante(self, solicitante_id: UUID, data: SolicitanteUpdate) -> Solicitante:
        """Actualizar solicitante"""
        solicitante = await self.get_solicitante(solicitante_id)
        
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(solicitante, field, value)
        
        return await self.repository.update(solicitante)
```

### 6. Endpoints API

**Ubicación**: `app/api/v1/endpoints/solicitantes.py`

```python
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.db.repositories.solicitante_repository import SolicitanteRepository
from app.services.solicitante_service import SolicitanteService
from app.schemas.solicitante import SolicitanteCreate, SolicitanteResponse, SolicitanteUpdate
from typing import List
from uuid import UUID

router = APIRouter(prefix="/solicitantes", tags=["solicitantes"])

def get_solicitante_service(db: AsyncSession = Depends(get_db)) -> SolicitanteService:
    repository = SolicitanteRepository(db)
    return SolicitanteService(repository)

@router.post("/", response_model=SolicitanteResponse, status_code=201)
async def create_solicitante(
    solicitante: SolicitanteCreate,
    service: SolicitanteService = Depends(get_solicitante_service)
):
    """Crear nuevo solicitante"""
    return await service.create_solicitante(solicitante)

@router.get("/search", response_model=List[SolicitanteResponse])
async def search_solicitantes(
    correo: str = Query(..., min_length=3, description="Correo para buscar"),
    limit: int = Query(10, ge=1, le=50),
    service: SolicitanteService = Depends(get_solicitante_service)
):
    """Buscar solicitantes por correo"""
    return await service.search_by_correo(correo, limit)

@router.get("/", response_model=List[SolicitanteResponse])
async def list_solicitantes(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    service: SolicitanteService = Depends(get_solicitante_service)
):
    """Listar solicitantes"""
    return await service.list_solicitantes(skip, limit)

@router.get("/{id}", response_model=SolicitanteResponse)
async def get_solicitante(
    id: UUID,
    service: SolicitanteService = Depends(get_solicitante_service)
):
    """Obtener solicitante por ID"""
    return await service.get_solicitante(id)

@router.put("/{id}", response_model=SolicitanteResponse)
async def update_solicitante(
    id: UUID,
    data: SolicitanteUpdate,
    service: SolicitanteService = Depends(get_solicitante_service)
):
    """Actualizar solicitante"""
    return await service.update_solicitante(id, data)
```

Registrar router en `app/api/v1/router.py`:

```python
from app.api.v1.endpoints import solicitantes

api_router.include_router(solicitantes.router)
```

### 7. Catálogo CIE-10

**Opción A: Base de Datos (Recomendado)**

**Modelo**: `app/models/catalogo_cie10.py`

```python
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Index
from app.db.base_class import Base

class CatalogoCIE10(Base):
    __tablename__ = "catalogo_cie10"
    
    codigo: Mapped[str] = mapped_column(
        String(10), 
        primary_key=True,
        comment="Código CIE-10"
    )
    descripcion: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Descripción del diagnóstico"
    )
    
    __table_args__ = (
        Index('idx_cie10_descripcion_fts', 
              'descripcion', 
              postgresql_using='gin',
              postgresql_ops={'descripcion': 'gin_trgm_ops'}),
    )
```

**Repository**: `app/db/repositories/catalogo_repository.py`

```python
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.catalogo_cie10 import CatalogoCIE10

class CatalogoRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def search_cie10(self, query: str, limit: int = 10) -> list[CatalogoCIE10]:
        """Buscar CIE-10 por código o descripción"""
        stmt = (
            select(CatalogoCIE10)
            .where(
                or_(
                    CatalogoCIE10.codigo.ilike(f"%{query}%"),
                    CatalogoCIE10.descripcion.ilike(f"%{query}%")
                )
            )
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def get_by_codigo(self, codigo: str) -> CatalogoCIE10 | None:
        """Obtener CIE-10 por código exacto"""
        stmt = select(CatalogoCIE10).where(CatalogoCIE10.codigo == codigo.upper())
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
```

**Service**: `app/services/catalogo_service.py`

```python
from app.db.repositories.catalogo_repository import CatalogoRepository
from app.models.catalogo_cie10 import CatalogoCIE10

class CatalogoService:
    def __init__(self, repository: CatalogoRepository):
        self.repository = repository
    
    async def search_cie10(self, query: str, limit: int = 10) -> list[CatalogoCIE10]:
        """Buscar códigos CIE-10"""
        if len(query) < 2:
            return []
        return await self.repository.search_cie10(query, limit)
    
    async def get_cie10_by_codigo(self, codigo: str) -> CatalogoCIE10 | None:
        """Obtener CIE-10 por código"""
        return await self.repository.get_by_codigo(codigo)
```

**Schema**: `app/schemas/catalogo.py`

```python
from pydantic import BaseModel

class CIE10Response(BaseModel):
    codigo: str
    descripcion: str
    
    class Config:
        from_attributes = True
```

**Endpoint**: `app/api/v1/endpoints/catalogos.py`

```python
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.db.repositories.catalogo_repository import CatalogoRepository
from app.services.catalogo_service import CatalogoService
from app.schemas.catalogo import CIE10Response
from typing import List

router = APIRouter(prefix="/catalogos", tags=["catalogos"])

def get_catalogo_service(db: AsyncSession = Depends(get_db)) -> CatalogoService:
    repository = CatalogoRepository(db)
    return CatalogoService(repository)

@router.get("/cie10", response_model=List[CIE10Response])
async def search_cie10(
    q: str = Query(..., min_length=2, description="Código o descripción para buscar"),
    limit: int = Query(10, ge=1, le=50),
    service: CatalogoService = Depends(get_catalogo_service)
):
    """Buscar códigos CIE-10 por código o descripción"""
    return await service.search_cie10(q, limit)

@router.get("/cie10/{codigo}", response_model=CIE10Response)
async def get_cie10(
    codigo: str,
    service: CatalogoService = Depends(get_catalogo_service)
):
    """Obtener CIE-10 por código exacto"""
    result = await service.get_cie10_by_codigo(codigo)
    if not result:
        raise HTTPException(status_code=404, detail=f"Código CIE-10 {codigo} no encontrado")
    return result
```

### 8. Migraciones Alembic

**Migración 1**: Crear tabla solicitante y modificar incapacidad

```bash
cd backend
docker compose exec api alembic revision --autogenerate -m "agregar_solicitante_y_campos_medico"
```

Revisar y ajustar el archivo generado en `backend/alembic/versions/`.

**Migración 2**: Crear tabla catalogo_cie10

```bash
docker compose exec api alembic revision --autogenerate -m "crear_catalogo_cie10"
```

**Aplicar migraciones**:

```bash
docker compose exec api alembic upgrade head
```

### 9. Poblar Catálogo CIE-10

Crear script: `backend/scripts/seed_cie10.py`

```python
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import csv
from app.models.catalogo_cie10 import CatalogoCIE10
from app.core.config import settings

async def seed_cie10():
    engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URI)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Leer archivo CSV con códigos CIE-10
        with open('data/cie10.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                cie10 = CatalogoCIE10(
                    codigo=row['codigo'],
                    descripcion=row['descripcion']
                )
                session.add(cie10)
        
        await session.commit()
        print("✅ Catálogo CIE-10 poblado exitosamente")

if __name__ == "__main__":
    asyncio.run(seed_cie10())
```

Crear archivo `backend/data/cie10.csv` con los códigos (puedes usar una fuente oficial del Ministerio de Salud de Colombia).

### 10. Tests

**Tests Solicitante**: `backend/tests/test_solicitante_service.py`

Mínimo 15 tests:
- Crear solicitante exitoso
- Crear solicitante con correo duplicado (error)
- Validación de correo inválido
- Validación de nombres/apellidos (solo letras)
- Búsqueda por correo
- Búsqueda por correo parcial
- Listar solicitantes
- Obtener por ID
- Obtener ID inexistente (404)
- Actualizar solicitante

**Tests Catálogo**: `backend/tests/test_catalogo_service.py`

Mínimo 8 tests:
- Buscar por código exacto
- Buscar por código parcial
- Buscar por descripción
- Query muy corta (<2 chars) retorna vacío
- Límite de resultados
- Código inexistente (404)

---

## Criterios de Aceptación

### Backend

- [ ] Tabla `solicitante` creada con migración
- [ ] CRUD completo de solicitantes funcional
- [ ] Endpoint `/solicitantes/search?correo={email}` funciona
- [ ] Campo `solicitante_id` en incapacidad funciona (FK)
- [ ] Campos `nombre_medico` y `registro_medico` en incapacidad
- [ ] Tabla `catalogo_cie10` creada
- [ ] Endpoint `/catalogos/cie10?q={query}` busca por código
- [ ] Endpoint `/catalogos/cie10?q={query}` busca por descripción
- [ ] Tests solicitante >80% cobertura
- [ ] Tests catálogo >80% cobertura
- [ ] `pytest` 0 errores
- [ ] Migraciones aplicadas exitosamente
- [ ] Swagger actualizado

---

## Comandos para Ejecutar

```bash
# 1. Crear migraciones
cd backend
docker compose exec api alembic revision --autogenerate -m "agregar_solicitante_y_campos_medico"
docker compose exec api alembic revision --autogenerate -m "crear_catalogo_cie10"

# 2. Aplicar migraciones
docker compose exec api alembic upgrade head

# 3. Poblar catálogo CIE-10
docker compose exec api python scripts/seed_cie10.py

# 4. Tests
docker compose exec api pytest tests/test_solicitante_service.py -v
docker compose exec api pytest tests/test_catalogo_service.py -v
docker compose exec api pytest --cov=app --cov-report=html

# 5. Verificar en Swagger
# Abrir http://localhost:8010/docs
```

---

## Documentación a Crear

Al finalizar:
- `backend/MODULO_SOLICITANTE_COMPLETADO.md`
- `backend/MODULO_CATALOGOS_COMPLETADO.md`
- Actualizar `docs/02_MODELO_DATOS.md`
- Actualizar `docs/03_API_ENDPOINTS.md`

---

**Prompt creado**: 16 de enero de 2026  
**Estimación**: 2-3 días  
**Prioridad**: 🔴 Alta

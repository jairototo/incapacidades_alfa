# Pre-Incapacidad Promotion Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (or superpowers:executing-plans) to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement an async background task to promote pre-incapacidades to full incapacidades with comprehensive validation (field checks, business rules, fraud alerts, integration checks). If validation fails, pre-incapacidad stays unchanged. If passes, full incapacidad record is created.

**Architecture:** 
- New `validation_inconsistencia` table tracks all validation failures (linked to pre-incapacidad/incapacidad)
- `PromotePreIncapacidadService` orchestrates: fetch data → validate → persist issues → create incapacidad
- `PreIncapacidadValidationService` runs all 4 validation categories (field, business, fraud, integration)
- Celery task `promote_pre_incapacidad_task` fires async after radicación confirmation (fire-and-forget, no blocking)
- Trigger added to radicación endpoint to enqueue task

**Tech Stack:** Celery (existing), SQLAlchemy ORM (async sessions in FastAPI, sync in Celery), Pydantic validation, custom validation rules from business skills

---

## File Structure

```
apps/backend/app/
├── models/
│   └── validation_inconsistencia.py          [NEW] - validation issue tracking
├── schemas/
│   ├── validation_inconsistencia.py          [NEW] - DTO for validation issues
│   └── pre_incapacidad.py                    [MODIFY] - add PromotionResult schema
├── db/repositories/
│   ├── pre_incapacidad_repository.py         [NEW] - fetch pre-incapacidad with relationships
│   ├── empleado_repository.py                [MODIFY] - add lookup by documento
│   ├── empresa_repository.py                 [MODIFY] - add lookup by NIT
│   └── validation_inconsistencia_repository.py [NEW] - persist/query validation issues
├── services/
│   ├── pre_incapacidad_promotion_service.py  [NEW] - orchestrator
│   ├── pre_incapacidad_validation_service.py [NEW] - validation engine (all 4 categories)
│   └── incapacidad_service.py                [MODIFY] - expose create_incapacidad method
├── tasks/
│   └── incapacidad_tasks.py                  [MODIFY] - add promote_pre_incapacidad_task
├── api/v1/endpoints/
│   └── pre_incapacidad.py                    [MODIFY] - add task trigger in radicación endpoint
└── tests/
    ├── unit/
    │   ├── test_pre_incapacidad_validation_service.py [NEW]
    │   ├── test_promote_pre_incapacidad_service.py     [NEW]
    │   └── test_validation_inconsistencia_repository.py [NEW]
    └── integration/
        └── test_promote_pre_incapacidad_task.py        [NEW]
```

---

## Chunk 1: Database & Schemas

### Task 1: Create ValidationInconsistencia Model

**Files:**
- Create: `apps/backend/app/models/validation_inconsistencia.py`

- [ ] **Step 1: Write the model**

```python
"""
Modelo para almacenar inconsistencias de validación encontradas
durante la promoción de pre-incapacidades.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
from sqlalchemy import String, Text, ForeignKey, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from app.models.base import BaseModel


class ValidationInconsistencia(BaseModel):
    """
    Registro de inconsistencias encontradas en validación de pre-incapacidades.
    
    Puede estar vinculada a:
    - pre_incapacidad_id: durante validación previa a creación
    - incapacidad_id: después de creación si se encuentran issues
    """
    
    __tablename__ = "validation_inconsistencia"
    
    __table_args__ = (
        Index("idx_pre_incapacidad_id", "pre_incapacidad_id"),
        Index("idx_incapacidad_id", "incapacidad_id"),
        Index("idx_categoria", "categoria"),
        Index("idx_severidad", "severidad"),
    )
    
    # Relación con pre-incapacidad (siempre presente)
    pre_incapacidad_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("pre_incapacidad.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Relación con incapacidad (opcional, si se creó a pesar del issue)
    incapacidad_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("incapacidad.id", ondelete="CASCADE"),
        nullable=True
    )
    
    # Categoría de validación
    categoria: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="FIELD_VALIDATION | BUSINESS_RULE | FRAUD_ALERT | INTEGRATION_CHECK"
    )
    
    # Severidad del issue
    severidad: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="WARNING",
        comment="ERROR | WARNING | INFO"
    )
    
    # Código del issue (máquina-readable)
    codigo: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    
    # Descripción legible
    descripcion: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Campo afectado (si aplica)
    campo_afectado: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Valor encontrado
    valor_encontrado: Mapped[Optional[str]] = mapped_column(Text)
    
    # Valor esperado
    valor_esperado: Mapped[Optional[str]] = mapped_column(Text)
    
    # Fecha de detección
    fecha_deteccion: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow
    )
    
    # Relaciones
    pre_incapacidad: Mapped["PreIncapacidad"] = relationship(
        "PreIncapacidad",
        back_populates="validation_inconsistencias"
    )
    incapacidad: Mapped[Optional["Incapacidad"]] = relationship(
        "Incapacidad",
        back_populates="validation_inconsistencias",
        foreign_keys=[incapacidad_id]
    )
    
    def __repr__(self) -> str:
        return f"<ValidationInconsistencia [{self.severidad}] {self.codigo}>"
```

- [ ] **Step 2: Update PreIncapacidad model to add relationship**

Edit: `apps/backend/app/models/pre_incapacidad.py`

Add after the `documentos` relationship (around line 87):

```python
    validation_inconsistencias: Mapped[List["ValidationInconsistencia"]] = relationship(
        "ValidationInconsistencia",
        back_populates="pre_incapacidad",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
```

And add import at top:

```python
from typing import Optional, List
```

- [ ] **Step 3: Update Incapacidad model to add relationship**

Edit: `apps/backend/app/models/incapacidad.py`

Add after the `datos_aprobados` relationship (around line 136):

```python
    validation_inconsistencias: Mapped[list["ValidationInconsistencia"]] = relationship(
        "ValidationInconsistencia",
        back_populates="incapacidad",
        cascade="all, delete-orphan"
    )
```

- [ ] **Step 4: Update __init__.py to export new model**

Edit: `apps/backend/app/models/__init__.py`

Add to imports:

```python
from app.models.validation_inconsistencia import ValidationInconsistencia
```

And add to `__all__`:

```python
"ValidationInconsistencia",
```

- [ ] **Step 5: Create Alembic migration**

Run:
```bash
cd apps/backend
make migrate msg="Add validation_inconsistencia table for promotion tracking"
```

Expected: Generates `alembic/versions/xxxx_add_validation_inconsistencia_table.py`

- [ ] **Step 6: Verify migration**

Edit the generated migration file to ensure it includes both:
- New `validation_inconsistencia` table creation
- Add relationships to `pre_incapacidad` and `incapacidad` tables

Run to check:
```bash
make upgrade-db
```

Expected: Migration applies without errors

- [ ] **Step 7: Commit**

```bash
git add apps/backend/app/models/validation_inconsistencia.py \
        apps/backend/app/models/pre_incapacidad.py \
        apps/backend/app/models/incapacidad.py \
        apps/backend/app/models/__init__.py \
        apps/backend/alembic/versions/
git commit -m "feat: add validation_inconsistencia model for tracking promotion issues"
```

---

### Task 2: Create Validation Schemas

**Files:**
- Create: `apps/backend/app/schemas/validation_inconsistencia.py`
- Modify: `apps/backend/app/schemas/pre_incapacidad.py`

- [ ] **Step 1: Write validation inconsistencia schemas**

```python
"""
Pydantic schemas para ValidationInconsistencia.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class ValidationInconsistenciaBase(BaseModel):
    """Base schema para inconsistencia de validación."""
    categoria: str = Field(..., description="FIELD_VALIDATION | BUSINESS_RULE | FRAUD_ALERT | INTEGRATION_CHECK")
    severidad: str = Field(default="WARNING", description="ERROR | WARNING | INFO")
    codigo: str = Field(..., description="Machine-readable code")
    descripcion: str = Field(...)
    campo_afectado: Optional[str] = None
    valor_encontrado: Optional[str] = None
    valor_esperado: Optional[str] = None


class ValidationInconsistenciaCreate(ValidationInconsistenciaBase):
    """Schema para crear inconsistencia."""
    pre_incapacidad_id: UUID
    incapacidad_id: Optional[UUID] = None


class ValidationInconsistenciaRead(ValidationInconsistenciaBase):
    """Schema para leer inconsistencia."""
    id: UUID
    pre_incapacidad_id: UUID
    incapacidad_id: Optional[UUID]
    fecha_deteccion: datetime

    class Config:
        from_attributes = True


class ValidationSummary(BaseModel):
    """Resumen de validación."""
    total_issues: int
    errors: int
    warnings: int
    infos: int
    issues: list[ValidationInconsistenciaRead]


class PromotionResult(BaseModel):
    """Resultado de promoción de pre-incapacidad."""
    success: bool
    pre_incapacidad_id: UUID
    incapacidad_id: Optional[UUID] = None
    validation_summary: ValidationSummary
    error_message: Optional[str] = None
    timestamp: datetime
```

- [ ] **Step 2: Add promotion schemas to pre_incapacidad.py**

Edit: `apps/backend/app/schemas/pre_incapacidad.py`

Add at end of file:

```python
from app.schemas.validation_inconsistencia import ValidationSummary


class PreIncapacidadPromotionResponse(BaseModel):
    """Response para radicación exitosa con promoción encolada."""
    numero_radicacion: int
    estado: str  # "PENDIENTE"
    validation_enqueued: bool
    mensaje: str = "Radicación recibida. Procesamiento iniciado."

    class Config:
        from_attributes = True
```

- [ ] **Step 3: Update __init__.py to export schemas**

Edit: `apps/backend/app/schemas/__init__.py`

Add imports:

```python
from app.schemas.validation_inconsistencia import (
    ValidationInconsistenciaCreate,
    ValidationInconsistenciaRead,
    ValidationSummary,
    PromotionResult,
)
from app.schemas.pre_incapacidad import PreIncapacidadPromotionResponse
```

- [ ] **Step 4: Commit**

```bash
git add apps/backend/app/schemas/validation_inconsistencia.py \
        apps/backend/app/schemas/pre_incapacidad.py \
        apps/backend/app/schemas/__init__.py
git commit -m "feat: add validation inconsistencia and promotion schemas"
```

---

## Chunk 2: Repositories & Data Access

### Task 3: Create Repositories

**Files:**
- Create: `apps/backend/app/db/repositories/pre_incapacidad_repository.py`
- Create: `apps/backend/app/db/repositories/validation_inconsistencia_repository.py`
- Modify: `apps/backend/app/db/repositories/empleado_repository.py`
- Modify: `apps/backend/app/db/repositories/empresa_repository.py`

- [ ] **Step 1: Create PreIncapacidadRepository**

```python
"""
Repository para Pre-Incapacidades con métodos para promoción.
"""
from uuid import UUID
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.pre_incapacidad import PreIncapacidad
from app.core.exceptions import NotFoundException


class PreIncapacidadRepository:
    """Repository para Pre-Incapacidades."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, id: UUID) -> Optional[PreIncapacidad]:
        """Obtener pre-incapacidad por ID con relationships."""
        query = select(PreIncapacidad).where(PreIncapacidad.id == id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_numero_radicacion(self, numero: int) -> Optional[PreIncapacidad]:
        """Obtener pre-incapacidad por número de radicación."""
        query = select(PreIncapacidad).where(PreIncapacidad.numero_radicacion == numero)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def update_estado(self, id: UUID, nuevo_estado: str) -> PreIncapacidad:
        """Actualizar estado de pre-incapacidad."""
        pre_inc = await self.get_by_id(id)
        if not pre_inc:
            raise NotFoundException(f"PreIncapacidad {id} not found")
        
        pre_inc.estado = nuevo_estado
        self.db.add(pre_inc)
        await self.db.flush()
        return pre_inc
    
    async def update_error(self, id: UUID, error_msg: str) -> PreIncapacidad:
        """Registrar error de procesamiento."""
        pre_inc = await self.get_by_id(id)
        if not pre_inc:
            raise NotFoundException(f"PreIncapacidad {id} not found")
        
        pre_inc.error_procesamiento = error_msg
        self.db.add(pre_inc)
        await self.db.flush()
        return pre_inc
```

Save to: `apps/backend/app/db/repositories/pre_incapacidad_repository.py`

- [ ] **Step 2: Create ValidationInconsistenciaRepository**

```python
"""
Repository para almacenar y consultar inconsistencias de validación.
"""
from uuid import UUID
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.validation_inconsistencia import ValidationInconsistencia
from app.schemas.validation_inconsistencia import ValidationInconsistenciaCreate


class ValidationInconsistenciaRepository:
    """Repository para inconsistencias de validación."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, schema: ValidationInconsistenciaCreate) -> ValidationInconsistencia:
        """Crear nueva inconsistencia."""
        issue = ValidationInconsistencia(
            pre_incapacidad_id=schema.pre_incapacidad_id,
            incapacidad_id=schema.incapacidad_id,
            categoria=schema.categoria,
            severidad=schema.severidad,
            codigo=schema.codigo,
            descripcion=schema.descripcion,
            campo_afectado=schema.campo_afectado,
            valor_encontrado=schema.valor_encontrado,
            valor_esperado=schema.valor_esperado,
        )
        self.db.add(issue)
        await self.db.flush()
        return issue
    
    async def get_by_pre_incapacidad(self, pre_inc_id: UUID) -> list[ValidationInconsistencia]:
        """Obtener todas las inconsistencias de una pre-incapacidad."""
        query = select(ValidationInconsistencia).where(
            ValidationInconsistencia.pre_incapacidad_id == pre_inc_id
        )
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def count_by_severidad(self, pre_inc_id: UUID) -> dict[str, int]:
        """Contar issues por severidad."""
        issues = await self.get_by_pre_incapacidad(pre_inc_id)
        
        counts = {
            "ERROR": 0,
            "WARNING": 0,
            "INFO": 0,
            "total": len(issues)
        }
        
        for issue in issues:
            counts[issue.severidad] += 1
        
        return counts
    
    async def has_errors(self, pre_inc_id: UUID) -> bool:
        """Verificar si hay errores (no warnings/infos)."""
        query = select(ValidationInconsistencia).where(
            and_(
                ValidationInconsistencia.pre_incapacidad_id == pre_inc_id,
                ValidationInconsistencia.severidad == "ERROR"
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None
```

Save to: `apps/backend/app/db/repositories/validation_inconsistencia_repository.py`

- [ ] **Step 3: Add lookup methods to EmpleadoRepository**

Edit: `apps/backend/app/db/repositories/empleado_repository.py`

Add method:

```python
    async def get_by_documento(self, tipo_documento: str, numero_documento: str) -> Optional[Empleado]:
        """Obtener empleado por tipo y número de documento."""
        query = select(Empleado).where(
            and_(
                Empleado.tipo_documento == tipo_documento,
                Empleado.numero_documento == numero_documento
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
```

Add import `and_` if not present:

```python
from sqlalchemy import and_
```

- [ ] **Step 4: Add lookup method to EmpresaRepository**

Edit: `apps/backend/app/db/repositories/empresa_repository.py`

Add method:

```python
    async def get_by_nit(self, nit: str) -> Optional[Empresa]:
        """Obtener empresa por NIT."""
        query = select(Empresa).where(Empresa.nit == nit)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
```

- [ ] **Step 5: Update repositories __init__.py**

Edit: `apps/backend/app/db/repositories/__init__.py`

Add imports:

```python
from app.db.repositories.pre_incapacidad_repository import PreIncapacidadRepository
from app.db.repositories.validation_inconsistencia_repository import ValidationInconsistenciaRepository
```

- [ ] **Step 6: Commit**

```bash
git add apps/backend/app/db/repositories/pre_incapacidad_repository.py \
        apps/backend/app/db/repositories/validation_inconsistencia_repository.py \
        apps/backend/app/db/repositories/empleado_repository.py \
        apps/backend/app/db/repositories/empresa_repository.py \
        apps/backend/app/db/repositories/__init__.py
git commit -m "feat: add repositories for pre-incapacidad promotion"
```

---

## Chunk 3: Validation Services

### Task 4: Create PreIncapacidadValidationService

**Files:**
- Create: `apps/backend/app/services/pre_incapacidad_validation_service.py`
- Test: `apps/backend/tests/unit/test_pre_incapacidad_validation_service.py`

- [ ] **Step 1: Write unit tests for validation service**

```python
"""
Tests para PreIncapacidadValidationService.
"""
from datetime import date, datetime, timedelta
from uuid import uuid4
from pytest import mark, raises

from app.services.pre_incapacidad_validation_service import PreIncapacidadValidationService
from app.models.pre_incapacidad import PreIncapacidad
from app.models.empleado import Empleado
from app.models.empresa import Empresa
from app.schemas.validation_inconsistencia import ValidationInconsistenciaCreate


@mark.asyncio
async def test_field_validation_missing_required_fields():
    """Test: campo requerido vacío debe generar ERROR."""
    pre_inc = PreIncapacidad(
        numero_radicacion=202600001,
        estado="PENDIENTE",
        solicitante_correo="test@example.com",
        solicitante_nombres="Juan",
        empleado_tipo_documento="CC",
        empleado_numero_documento="",  # ← FALTA
        empleado_nombres="Carlos",
        tipo="ARL",
        tipo_enfermedad="ACCIDENTE_TRABAJO",
        fecha_inicio=date.today(),
        fecha_fin=date.today() + timedelta(days=3),
        dias_totales=3,
        diagnostico_cie10="M54.5",
        nombre_medico="Dr. García",
        registro_medico="12345",
    )
    
    service = PreIncapacidadValidationService(
        pre_incapacidad=pre_inc,
        empleado=None,
        empresa=None,
    )
    
    issues = await service.validate_field_level()
    
    assert len(issues) > 0
    assert any(i.codigo == "EMPTY_EMPLEADO_NUMERO" for i in issues)
    assert any(i.severidad == "ERROR" for i in issues)


@mark.asyncio
async def test_field_validation_invalid_date_range():
    """Test: fecha_fin < fecha_inicio debe generar ERROR."""
    pre_inc = PreIncapacidad(
        numero_radicacion=202600001,
        estado="PENDIENTE",
        solicitante_correo="test@example.com",
        solicitante_nombres="Juan",
        empleado_tipo_documento="CC",
        empleado_numero_documento="1234567",
        empleado_nombres="Carlos",
        tipo="ARL",
        tipo_enfermedad="ACCIDENTE_TRABAJO",
        fecha_inicio=date.today(),
        fecha_fin=date.today() - timedelta(days=1),  # ← INVÁLIDO
        dias_totales=-1,
        diagnostico_cie10="M54.5",
        nombre_medico="Dr. García",
        registro_medico="12345",
    )
    
    service = PreIncapacidadValidationService(
        pre_incapacidad=pre_inc,
        empleado=None,
        empresa=None,
    )
    
    issues = await service.validate_field_level()
    
    assert any(i.codigo == "INVALID_DATE_RANGE" for i in issues)


@mark.asyncio
async def test_business_rule_validation_dias_totales_mismatch():
    """Test: dias_totales no coincide con fecha_inicio/fin."""
    pre_inc = PreIncapacidad(
        numero_radicacion=202600001,
        estado="PENDIENTE",
        solicitante_correo="test@example.com",
        solicitante_nombres="Juan",
        empleado_tipo_documento="CC",
        empleado_numero_documento="1234567",
        empleado_nombres="Carlos",
        tipo="ARL",
        tipo_enfermedad="ACCIDENTE_TRABAJO",
        fecha_inicio=date(2024, 1, 1),
        fecha_fin=date(2024, 1, 10),  # 9 días
        dias_totales=5,  # ← INCORRECTO
        diagnostico_cie10="M54.5",
        nombre_medico="Dr. García",
        registro_medico="12345",
    )
    
    service = PreIncapacidadValidationService(
        pre_incapacidad=pre_inc,
        empleado=None,
        empresa=None,
    )
    
    issues = await service.validate_business_rules()
    
    assert any(i.codigo == "DIAS_TOTALES_MISMATCH" for i in issues)


@mark.asyncio
async def test_integration_check_empleado_not_found():
    """Test: empleado no existe en BD debe generar ERROR."""
    pre_inc = PreIncapacidad(
        numero_radicacion=202600001,
        estado="PENDIENTE",
        solicitante_correo="test@example.com",
        solicitante_nombres="Juan",
        empleado_tipo_documento="CC",
        empleado_numero_documento="9999999",  # No existe
        empleado_nombres="Carlos",
        tipo="ARL",
        tipo_enfermedad="ACCIDENTE_TRABAJO",
        fecha_inicio=date.today(),
        fecha_fin=date.today() + timedelta(days=3),
        dias_totales=3,
        diagnostico_cie10="M54.5",
        nombre_medico="Dr. García",
        registro_medico="12345",
    )
    
    service = PreIncapacidadValidationService(
        pre_incapacidad=pre_inc,
        empleado=None,  # Not found
        empresa=None,
    )
    
    issues = await service.validate_integration()
    
    assert any(i.codigo == "EMPLEADO_NOT_FOUND" for i in issues)
    assert any(i.severidad == "ERROR" for i in issues)


@mark.asyncio
async def test_complete_validation_all_categories():
    """Test: validar todas las categorías en una llamada."""
    pre_inc = PreIncapacidad(
        numero_radicacion=202600001,
        estado="PENDIENTE",
        solicitante_correo="test@example.com",
        solicitante_nombres="Juan",
        empleado_tipo_documento="CC",
        empleado_numero_documento="1234567",
        empleado_nombres="Carlos",
        tipo="ARL",
        tipo_enfermedad="ACCIDENTE_TRABAJO",
        fecha_inicio=date.today(),
        fecha_fin=date.today() + timedelta(days=3),
        dias_totales=3,
        diagnostico_cie10="M54.5",
        nombre_medico="Dr. García",
        registro_medico="12345",
    )
    
    service = PreIncapacidadValidationService(
        pre_incapacidad=pre_inc,
        empleado=None,  # Simular no encontrado
        empresa=None,
    )
    
    all_issues = await service.validate_all()
    
    # Debe haber issues de integración (empleado no encontrado)
    assert len(all_issues) > 0
```

Save to: `apps/backend/tests/unit/test_pre_incapacidad_validation_service.py`

- [ ] **Step 2: Write validation service implementation**

```python
"""
Servicio de validación para pre-incapacidades.

Ejecuta 4 categorías de validación:
1. FIELD_VALIDATION: tipos, campos requeridos, formato
2. BUSINESS_RULE: lógica de negocio (rangos de fecha, cálculos)
3. FRAUD_ALERT: alertas de fraude/anomalía
4. INTEGRATION_CHECK: existencia de entidades relacionadas
"""
from datetime import date, timedelta
from typing import Optional
from loguru import logger

from app.models.pre_incapacidad import PreIncapacidad
from app.models.empleado import Empleado
from app.models.empresa import Empresa
from app.schemas.validation_inconsistencia import ValidationInconsistenciaCreate


class PreIncapacidadValidationService:
    """Orquesta validación completa de pre-incapacidad."""
    
    def __init__(
        self,
        pre_incapacidad: PreIncapacidad,
        empleado: Optional[Empleado],
        empresa: Optional[Empresa],
    ):
        self.pre_inc = pre_incapacidad
        self.empleado = empleado
        self.empresa = empresa
    
    async def validate_field_level(self) -> list[ValidationInconsistenciaCreate]:
        """
        Validación de campos: tipos, requeridos, formato.
        
        Returns:
            Lista de inconsistencias encontradas
        """
        issues = []
        
        # ── Solicitante ─────────────────────────────────────────────────────
        if not self.pre_inc.solicitante_correo or len(self.pre_inc.solicitante_correo) == 0:
            issues.append(ValidationInconsistenciaCreate(
                pre_incapacidad_id=self.pre_inc.id,
                categoria="FIELD_VALIDATION",
                severidad="ERROR",
                codigo="EMPTY_SOLICITANTE_CORREO",
                descripcion="Correo del solicitante es requerido",
                campo_afectado="solicitante_correo",
            ))
        elif "@" not in self.pre_inc.solicitante_correo:
            issues.append(ValidationInconsistenciaCreate(
                pre_incapacidad_id=self.pre_inc.id,
                categoria="FIELD_VALIDATION",
                severidad="ERROR",
                codigo="INVALID_EMAIL_FORMAT",
                descripcion="Formato de correo inválido",
                campo_afectado="solicitante_correo",
                valor_encontrado=self.pre_inc.solicitante_correo,
            ))
        
        if not self.pre_inc.solicitante_nombres or len(self.pre_inc.solicitante_nombres) == 0:
            issues.append(ValidationInconsistenciaCreate(
                pre_incapacidad_id=self.pre_inc.id,
                categoria="FIELD_VALIDATION",
                severidad="ERROR",
                codigo="EMPTY_SOLICITANTE_NOMBRES",
                descripcion="Nombres del solicitante son requeridos",
                campo_afectado="solicitante_nombres",
            ))
        
        # ── Empleado ────────────────────────────────────────────────────────
        if not self.pre_inc.empleado_tipo_documento or len(self.pre_inc.empleado_tipo_documento) == 0:
            issues.append(ValidationInconsistenciaCreate(
                pre_incapacidad_id=self.pre_inc.id,
                categoria="FIELD_VALIDATION",
                severidad="ERROR",
                codigo="EMPTY_EMPLEADO_TIPO_DOC",
                descripcion="Tipo de documento del empleado es requerido",
                campo_afectado="empleado_tipo_documento",
            ))
        
        if not self.pre_inc.empleado_numero_documento or len(self.pre_inc.empleado_numero_documento) == 0:
            issues.append(ValidationInconsistenciaCreate(
                pre_incapacidad_id=self.pre_inc.id,
                categoria="FIELD_VALIDATION",
                severidad="ERROR",
                codigo="EMPTY_EMPLEADO_NUMERO",
                descripcion="Número de documento del empleado es requerido",
                campo_afectado="empleado_numero_documento",
            ))
        
        if not self.pre_inc.empleado_nombres or len(self.pre_inc.empleado_nombres) == 0:
            issues.append(ValidationInconsistenciaCreate(
                pre_incapacidad_id=self.pre_inc.id,
                categoria="FIELD_VALIDATION",
                severidad="ERROR",
                codigo="EMPTY_EMPLEADO_NOMBRES",
                descripcion="Nombres del empleado son requeridos",
                campo_afectado="empleado_nombres",
            ))
        
        # ── Incapacidad ─────────────────────────────────────────────────────
        if not self.pre_inc.tipo or self.pre_inc.tipo not in ["ARL", "SALUD"]:
            issues.append(ValidationInconsistenciaCreate(
                pre_incapacidad_id=self.pre_inc.id,
                categoria="FIELD_VALIDATION",
                severidad="ERROR",
                codigo="INVALID_TIPO",
                descripcion="Tipo de incapacidad debe ser ARL o SALUD",
                campo_afectado="tipo",
                valor_encontrado=self.pre_inc.tipo,
            ))
        
        if not self.pre_inc.tipo_enfermedad:
            issues.append(ValidationInconsistenciaCreate(
                pre_incapacidad_id=self.pre_inc.id,
                categoria="FIELD_VALIDATION",
                severidad="ERROR",
                codigo="EMPTY_TIPO_ENFERMEDAD",
                descripcion="Tipo de enfermedad es requerido",
                campo_afectado="tipo_enfermedad",
            ))
        
        if not self.pre_inc.fecha_inicio:
            issues.append(ValidationInconsistenciaCreate(
                pre_incapacidad_id=self.pre_inc.id,
                categoria="FIELD_VALIDATION",
                severidad="ERROR",
                codigo="EMPTY_FECHA_INICIO",
                descripcion="Fecha de inicio es requerida",
                campo_afectado="fecha_inicio",
            ))
        
        if not self.pre_inc.fecha_fin:
            issues.append(ValidationInconsistenciaCreate(
                pre_incapacidad_id=self.pre_inc.id,
                categoria="FIELD_VALIDATION",
                severidad="ERROR",
                codigo="EMPTY_FECHA_FIN",
                descripcion="Fecha de fin es requerida",
                campo_afectado="fecha_fin",
            ))
        
        # ── Validación de rangos de fecha ────────────────────────────────────
        if self.pre_inc.fecha_inicio and self.pre_inc.fecha_fin:
            if self.pre_inc.fecha_fin < self.pre_inc.fecha_inicio:
                issues.append(ValidationInconsistenciaCreate(
                    pre_incapacidad_id=self.pre_inc.id,
                    categoria="FIELD_VALIDATION",
                    severidad="ERROR",
                    codigo="INVALID_DATE_RANGE",
                    descripcion="Fecha de fin no puede ser anterior a fecha de inicio",
                    campo_afectado="fecha_fin",
                    valor_encontrado=str(self.pre_inc.fecha_fin),
                    valor_esperado=f">= {self.pre_inc.fecha_inicio}",
                ))
        
        if not self.pre_inc.diagnostico_cie10 or len(self.pre_inc.diagnostico_cie10) == 0:
            issues.append(ValidationInconsistenciaCreate(
                pre_incapacidad_id=self.pre_inc.id,
                categoria="FIELD_VALIDATION",
                severidad="ERROR",
                codigo="EMPTY_DIAGNOSTICO_CIE10",
                descripcion="Diagnóstico CIE-10 es requerido",
                campo_afectado="diagnostico_cie10",
            ))
        
        if not self.pre_inc.nombre_medico or len(self.pre_inc.nombre_medico) == 0:
            issues.append(ValidationInconsistenciaCreate(
                pre_incapacidad_id=self.pre_inc.id,
                categoria="FIELD_VALIDATION",
                severidad="ERROR",
                codigo="EMPTY_NOMBRE_MEDICO",
                descripcion="Nombre del médico es requerido",
                campo_afectado="nombre_medico",
            ))
        
        if not self.pre_inc.registro_medico or len(self.pre_inc.registro_medico) == 0:
            issues.append(ValidationInconsistenciaCreate(
                pre_incapacidad_id=self.pre_inc.id,
                categoria="FIELD_VALIDATION",
                severidad="ERROR",
                codigo="EMPTY_REGISTRO_MEDICO",
                descripcion="Registro médico es requerido",
                campo_afectado="registro_medico",
            ))
        
        logger.info(f"Field validation: {len(issues)} issues found")
        return issues
    
    async def validate_business_rules(self) -> list[ValidationInconsistenciaCreate]:
        """
        Validación de reglas de negocio: cálculos, lógica de dominio.
        
        Returns:
            Lista de inconsistencias encontradas
        """
        issues = []
        
        # ── Validar días totales vs fechas ───────────────────────────────────
        if self.pre_inc.fecha_inicio and self.pre_inc.fecha_fin:
            expected_days = (self.pre_inc.fecha_fin - self.pre_inc.fecha_inicio).days + 1
            if self.pre_inc.dias_totales != expected_days:
                issues.append(ValidationInconsistenciaCreate(
                    pre_incapacidad_id=self.pre_inc.id,
                    categoria="BUSINESS_RULE",
                    severidad="WARNING",
                    codigo="DIAS_TOTALES_MISMATCH",
                    descripcion="Días totales no coincide con rango de fechas",
                    campo_afectado="dias_totales",
                    valor_encontrado=str(self.pre_inc.dias_totales),
                    valor_esperado=str(expected_days),
                ))
        
        # ── Validar que la incapacidad no sea retroactiva > 30 días ──────────
        if self.pre_inc.fecha_inicio:
            max_retroactive_days = 30
            days_ago = (date.today() - self.pre_inc.fecha_inicio).days
            if days_ago > max_retroactive_days:
                issues.append(ValidationInconsistenciaCreate(
                    pre_incapacidad_id=self.pre_inc.id,
                    categoria="BUSINESS_RULE",
                    severidad="WARNING",
                    codigo="RETROACTIVE_BEYOND_LIMIT",
                    descripcion=f"Incapacidad es retroactiva más de {max_retroactive_days} días",
                    campo_afectado="fecha_inicio",
                    valor_encontrado=str(self.pre_inc.fecha_inicio),
                ))
        
        # ── Validar duración máxima (180 días) ───────────────────────────────
        if self.pre_inc.dias_totales and self.pre_inc.dias_totales > 180:
            issues.append(ValidationInconsistenciaCreate(
                pre_incapacidad_id=self.pre_inc.id,
                categoria="BUSINESS_RULE",
                severidad="WARNING",
                codigo="DURATION_EXCEEDS_LIMIT",
                descripcion="Duración excede 180 días (límite típico ARL)",
                campo_afectado="dias_totales",
                valor_encontrado=str(self.pre_inc.dias_totales),
                valor_esperado="<= 180",
            ))
        
        logger.info(f"Business rule validation: {len(issues)} issues found")
        return issues
    
    async def validate_fraud_alerts(self) -> list[ValidationInconsistenciaCreate]:
        """
        Detectar patrones de fraude o anomalías.
        
        Returns:
            Lista de inconsistencias encontradas
        """
        issues = []
        
        # ── Alerta: documentos coincidentes (empleado = solicitante) ─────────
        if (self.pre_inc.empleado_numero_documento == self.pre_inc.solicitante_correo.split("@")[0]):
            issues.append(ValidationInconsistenciaCreate(
                pre_incapacidad_id=self.pre_inc.id,
                categoria="FRAUD_ALERT",
                severidad="INFO",
                codigo="SOLICITANTE_SAME_AS_EMPLEADO",
                descripcion="Solicitante es el mismo empleado (requiere revisión en auditoría)",
                campo_afectado="empleado_numero_documento",
            ))
        
        # ── Alerta: valor diario muy alto (> 500k) ───────────────────────────
        if self.pre_inc.valor_dia and self.pre_inc.valor_dia > 500000:
            issues.append(ValidationInconsistenciaCreate(
                pre_incapacidad_id=self.pre_inc.id,
                categoria="FRAUD_ALERT",
                severidad="WARNING",
                codigo="UNUSUALLY_HIGH_DAILY_VALUE",
                descripcion="Valor diario inusualmente alto (> 500k)",
                campo_afectado="valor_dia",
                valor_encontrado=str(self.pre_inc.valor_dia),
            ))
        
        logger.info(f"Fraud alert validation: {len(issues)} issues found")
        return issues
    
    async def validate_integration(self) -> list[ValidationInconsistenciaCreate]:
        """
        Validar que las entidades relacionadas existan en la BD.
        
        Returns:
            Lista de inconsistencias encontradas
        """
        issues = []
        
        # ── Verificar que empleado exista ───────────────────────────────────
        if self.pre_inc.tipo == "ARL":
            if not self.empleado:
                issues.append(ValidationInconsistenciaCreate(
                    pre_incapacidad_id=self.pre_inc.id,
                    categoria="INTEGRATION_CHECK",
                    severidad="ERROR",
                    codigo="EMPLEADO_NOT_FOUND",
                    descripcion=f"Empleado {self.pre_inc.empleado_numero_documento} no encontrado en BD",
                    campo_afectado="empleado_id",
                    valor_encontrado=self.pre_inc.empleado_numero_documento,
                ))
            else:
                # Empleado encontrado, pero validar que esté activo
                if self.empleado.estado != "ACTIVO":
                    issues.append(ValidationInconsistenciaCreate(
                        pre_incapacidad_id=self.pre_inc.id,
                        categoria="INTEGRATION_CHECK",
                        severidad="WARNING",
                        codigo="EMPLEADO_INACTIVE",
                        descripcion=f"Empleado está en estado {self.empleado.estado}",
                        campo_afectado="empleado_id",
                        valor_encontrado=self.empleado.estado,
                    ))
        
        # ── Verificar que empresa exista (si se proporciona NIT) ───────────────
        if self.pre_inc.empresa_nit:
            if not self.empresa:
                issues.append(ValidationInconsistenciaCreate(
                    pre_incapacidad_id=self.pre_inc.id,
                    categoria="INTEGRATION_CHECK",
                    severidad="ERROR",
                    codigo="EMPRESA_NOT_FOUND",
                    descripcion=f"Empresa NIT {self.pre_inc.empresa_nit} no encontrada en BD",
                    campo_afectado="empresa_id",
                    valor_encontrado=self.pre_inc.empresa_nit,
                ))
            else:
                # Empresa encontrada, pero validar que esté activa
                if self.empresa.estado != "ACTIVA":
                    issues.append(ValidationInconsistenciaCreate(
                        pre_incapacidad_id=self.pre_inc.id,
                        categoria="INTEGRATION_CHECK",
                        severidad="WARNING",
                        codigo="EMPRESA_INACTIVE",
                        descripcion=f"Empresa está en estado {self.empresa.estado}",
                        campo_afectado="empresa_id",
                        valor_encontrado=self.empresa.estado,
                    ))
        
        logger.info(f"Integration validation: {len(issues)} issues found")
        return issues
    
    async def validate_all(self) -> list[ValidationInconsistenciaCreate]:
        """
        Ejecutar todas las validaciones en secuencia.
        
        Returns:
            Lista consolidada de todas las inconsistencias encontradas
        """
        all_issues = []
        
        all_issues.extend(await self.validate_field_level())
        all_issues.extend(await self.validate_business_rules())
        all_issues.extend(await self.validate_fraud_alerts())
        all_issues.extend(await self.validate_integration())
        
        logger.info(f"Complete validation: {len(all_issues)} total issues")
        return all_issues
```

Save to: `apps/backend/app/services/pre_incapacidad_validation_service.py`

- [ ] **Step 3: Run tests**

```bash
cd apps/backend
pytest tests/unit/test_pre_incapacidad_validation_service.py -v
```

Expected: All tests pass

- [ ] **Step 4: Update services __init__.py**

Edit: `apps/backend/app/services/__init__.py`

Add import:

```python
from app.services.pre_incapacidad_validation_service import PreIncapacidadValidationService
```

- [ ] **Step 5: Commit**

```bash
git add apps/backend/app/services/pre_incapacidad_validation_service.py \
        apps/backend/tests/unit/test_pre_incapacidad_validation_service.py \
        apps/backend/app/services/__init__.py
git commit -m "feat: add pre-incapacidad validation service with all 4 categories"
```

---

## Chunk 4: Promotion Service & Task

### Task 5: Create PromotePreIncapacidadService

**Files:**
- Create: `apps/backend/app/services/pre_incapacidad_promotion_service.py`
- Test: `apps/backend/tests/unit/test_promote_pre_incapacidad_service.py`

(Plan continues in next section...)

---

**[Plan Chunk 4-5 content too long — will be provided in next message after Chunk 3 approval]**

---

## Implementation Notes

- **Celery task pattern**: See existing `radicar_incapacidad_automatica_task` in `incapacidad_tasks.py` for sync session handling
- **Fire-and-forget**: Task enqueued from FastAPI endpoint without awaiting response
- **Validation failure**: Pre-incapacidad stays in "PENDIENTE", validation issues logged in DB, NOT created as incapacidad
- **Migration rollback**: If migration fails, use `make downgrade-db` to rollback
- **Dependencies**: No new external packages required (uses existing Celery, SQLAlchemy, Pydantic)

---

## Next Steps After Implementation

1. **Manual testing**: Use FastAPI Swagger UI to radicador pre-incapacidad and monitor Celery logs
2. **Monitoring**: Add Flower dashboard monitoring (already configured on port 5565)
3. **Frontend integration**: Portal-externo radicación endpoint triggers task; dashboard can show promotion status
4. **Future**: Management view (`gestión`) will handle edge cases (validation warnings with manual approval, etc.)

---

Plan complete and ready for implementation.

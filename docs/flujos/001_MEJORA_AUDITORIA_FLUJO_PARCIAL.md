# Plan de Desarrollo - Feature: Auditoría Mejorada con Aprobación Parcial

## ✅ ESTADO: COMPLETADO 100% (3 de febrero de 2026)

### Resumen de Cambios Implementados

**Backend (100% Completado - 2 de febrero):**
- ✅ **Modelo de Datos**: Tabla `auditoria_datos_aprobados` creada con todos los campos requeridos
- ✅ **Enums**: Agregados 3 nuevos estados (`APROBADA_PARCIALMENTE`, `EN_PAGO_PARCIAL`, `PAGADA_PARCIALMENTE`)
- ✅ **Matriz de Transiciones**: Actualizada con 4 nuevas transiciones para el flujo parcial
- ✅ **Schemas Pydantic**: Creado `auditoria_datos.py` con 4 schemas (Base, Create, Update, Response)
- ✅ **Schema Auditoría**: Actualizado `IncapacidadAuditar` con campos modificables y validaciones
- ✅ **Repository**: Creado `AuditoriaDatosRepository` con métodos específicos
- ✅ **Service**: Actualizado `auditar_incapacidad()` con lógica de aprobación parcial
- ✅ **Endpoints**: 
  - Actualizado `POST /{id}/auditar` para recibir datos aprobados
  - Creado `GET /{id}/datos-aprobados` para consultar datos aprobados
- ✅ **Migraciones**: 3 migraciones ejecutadas exitosamente
  - `5f0125256440`: Tabla auditoria_datos_aprobados
  - `566c94df42fa`: Enum estadoincapacidad actualizado
  - `cf0a432a3aa8`: CHECK constraint incapacidad actualizado
- ✅ **Documentación**: Actualizado `docs/04_FLUJO_ESTADOS.md`

**Frontend (100% Completado - 3 de febrero):**
- ✅ **Types**:
  - Actualizado `enums.ts` con 3 nuevos estados (`APROBADA_PARCIALMENTE`, `EN_PAGO_PARCIAL`, `PAGADA_PARCIALMENTE`)
  - Creada interfaz `AuditoriaDatosAprobados` en `incapacidad.ts` (12 campos)
  - Actualizada interfaz `IncapacidadAuditarRequest` con acción `APROBAR_PARA_PAGO_PARCIAL` y 5 campos opcionales
- ✅ **Service**:
  - Actualizado método `auditar()` para aceptar objeto `IncapacidadAuditarRequest` completo
  - Creado método `getDatosAprobados()` con manejo de errores 404
  - Actualizada llamada en `cambiarEstado()` para usar nueva firma
- ✅ **Componente AuditoriaFormulario**:
  - React Hook Form + Zod validation con 6 campos validados
  - Estado local: `selectedAction`, `diasCalculados`, `esAprobacionParcial`
  - useEffect para cálculo automático de días entre fechas
  - Date pickers (shadcn/ui Calendar) para fecha_inicio/fin_aprobada
  - Input CIE-10 con validación regex `/^[A-Z]\d{3}(\.\d{1,2})?$/`
  - Textarea diagnóstico aprobado (min 3 caracteres)
  - Campo observaciones siempre visible (min 10 caracteres)
  - 4 botones de acción con colores diferenciados
  - Alert de aprobación parcial cuando `dias_aprobados < dias_totales`
  - Mutation con invalidación de queries y toast success/error
- ✅ **Página GestionarPage**:
  - Layout split-screen: Sidebar documentos (50%) | Panel principal (50%)
  - Sidebar collapsible con toggle button
  - Tabs reorganizadas: **Auditoría**, Detalle Completo, Historial
  - Tab Auditoría: alert de datos aprobados previos + AuditoriaFormulario
  - Query adicional para `getDatosAprobados()`
  - Handler `handleAuditoriaSuccess()` con redirección
  - Función `getEstadoBadgeVariant()` actualizada con 3 nuevos estados

**Archivos Creados (Backend):**
- `backend/app/models/auditoria_datos_aprobados.py`
- `backend/app/schemas/auditoria_datos.py`
- `backend/app/db/repositories/auditoria_datos_repository.py`
- `backend/alembic/versions/20260202_1640_5f0125256440_*.py`
- `backend/alembic/versions/20260202_1923_566c94df42fa_*.py`
- `backend/alembic/versions/20260202_2136_cf0a432a3aa8_*.py`

**Archivos Creados (Frontend):**
- `frontend/sistema-interno/src/components/incapacidades/AuditoriaFormulario.tsx` (446 líneas)

**Archivos Modificados (Backend - 7 archivos):**
- `backend/app/models/__init__.py`
- `backend/app/models/incapacidad.py`
- `backend/app/utils/enums.py`
- `backend/app/schemas/incapacidad.py`
- `backend/app/services/incapacidad_service.py`
- `backend/app/api/v1/endpoints/incapacidades.py`
- `backend/app/middleware/error_handler.py`
- `docs/04_FLUJO_ESTADOS.md`

**Archivos Modificados (Frontend - 4 archivos):**
- `frontend/sistema-interno/src/types/enums.ts`
- `frontend/sistema-interno/src/types/incapacidad.ts`
- `frontend/sistema-interno/src/services/incapacidadService.ts`
- `frontend/sistema-interno/src/pages/incapacidades/GestionarPage.tsx`

**Base de Datos:**
- ✅ Tabla `auditoria_datos_aprobados` creada y operativa
- ✅ Relación ONE-TO-ONE con `incapacidad` establecida
- ✅ Índices y constraints configurados
- ✅ Enum `estadoincapacidad` actualizado con 11 valores
- ✅ CHECK constraint `chk_incapacidad_estado` actualizado con 11 estados

**Testing Realizado:**
- ✅ POST `/api/v1/incapacidades/{id}/auditar` con `APROBAR_PARA_PAGO_PARCIAL` → Estado `APROBADA_PARCIALMENTE`
- ✅ GET `/api/v1/incapacidades/{id}/datos-aprobados` → Retorna objeto completo con 12 campos
- ✅ Database query verificada: registro en `auditoria_datos_aprobados` con todos los campos
- ✅ Enum verificado: 11 valores en `pg_enum`
- ✅ CHECK constraint verificado: 11 estados permitidos

**Próximos Pasos - Testing y Validación:**
- 🔄 **Parte 2: Frontend** (Siguiente fase)

---

## 📋 Resumen del Feature

**Objetivo**: Permitir al auditor modificar datos de la incapacidad durante la auditoría (fechas, CIE-10, diagnóstico) sin alterar el registro original, con soporte para **aprobación parcial** cuando los días aprobados sean menores a los solicitados.

**Impacto**: Backend + Frontend + Documentación

---

## 🎯 Parte 1: Backend (Prioridad ALTA - Comenzar aquí)

### Paso 1.1: Crear Nueva Tabla `auditoria_datos_aprobados`

**Archivo**: `backend/app/models/auditoria_datos_aprobados.py` (NUEVO)

**Descripción**: Tabla para almacenar los datos aprobados por el auditor durante la auditoría.

**Campos**:
```python
class AuditoriaDatosAprobados(BaseModel):
    __tablename__ = "auditoria_datos_aprobados"
    
    id: UUID (PK)
    incapacidad_id: UUID (FK a incapacidad, UNIQUE)
    
    # Fechas aprobadas
    fecha_inicio_aprobada: date
    fecha_fin_aprobada: date
    dias_aprobados: int
    
    # Diagnóstico aprobado
    cie10_aprobado: str(10)
    diagnostico_aprobado: str(500)
    
    # Observación del auditor
    observacion_auditoria: str(1000)
    
    # Auditoría
    auditado_por_id: UUID (FK a usuario)
    fecha_auditoria: datetime
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
```

**Relación**:
- `incapacidad_id` → `incapacidad.id` (ONE-TO-ONE)
- `auditado_por_id` → `usuario.id`

---

### Paso 1.2: Actualizar Enums de Estado

**Archivo**: enums.py

**Modificar**:
```python
class EstadoIncapacidad(str, Enum):
    RADICADA = "RADICADA"
    EN_AUDITORIA = "EN_AUDITORIA"
    OBSERVADA = "OBSERVADA"
    APROBADA = "APROBADA"
    APROBADA_PARCIALMENTE = "APROBADA_PARCIALMENTE"  # ← NUEVO
    RECHAZADA = "RECHAZADA"
    EN_PAGO = "EN_PAGO"
    EN_PAGO_PARCIAL = "EN_PAGO_PARCIAL"  # ← NUEVO
    PAGADA = "PAGADA"
    PAGADA_PARCIALMENTE = "PAGADA_PARCIALMENTE"  # ← NUEVO
    CANCELADA = "CANCELADA"
```

---

### Paso 1.3: Actualizar Matriz de Transiciones

**Archivo**: incapacidad_service.py

**Modificar `ALLOWED_TRANSITIONS`**:
```python
ALLOWED_TRANSITIONS: Dict[EstadoIncapacidad, List[EstadoIncapacidad]] = {
    # ...existente...
    
    EstadoIncapacidad.EN_AUDITORIA: [
        EstadoIncapacidad.OBSERVADA,
        EstadoIncapacidad.APROBADA,
        EstadoIncapacidad.APROBADA_PARCIALMENTE,  # ← NUEVO
        EstadoIncapacidad.RECHAZADA,
        EstadoIncapacidad.CANCELADA
    ],
    
    EstadoIncapacidad.APROBADA_PARCIALMENTE: [  # ← NUEVO
        EstadoIncapacidad.EN_PAGO_PARCIAL,
        EstadoIncapacidad.CANCELADA
    ],
    
    EstadoIncapacidad.EN_PAGO_PARCIAL: [  # ← NUEVO
        EstadoIncapacidad.PAGADA_PARCIALMENTE,
        EstadoIncapacidad.CANCELADA
    ],
    
    EstadoIncapacidad.PAGADA_PARCIALMENTE: [  # ← NUEVO
        EstadoIncapacidad.CANCELADA
    ],
    
    # ...resto existente...
}
```

---

### Paso 1.4: Crear Schemas Pydantic

**Archivo**: `backend/app/schemas/auditoria_datos.py` (NUEVO)

```python
from pydantic import BaseModel, Field
from datetime import date, datetime
from uuid import UUID

class AuditoriaDatosAprobadosBase(BaseModel):
    """Schema base para datos aprobados en auditoría"""
    fecha_inicio_aprobada: date
    fecha_fin_aprobada: date
    dias_aprobados: int = Field(..., ge=1)
    cie10_aprobado: str = Field(..., max_length=10)
    diagnostico_aprobado: str = Field(..., max_length=500)
    observacion_auditoria: str = Field(..., max_length=1000)

class AuditoriaDatosAprobadosCreate(AuditoriaDatosAprobadosBase):
    """Schema para crear datos aprobados"""
    incapacidad_id: UUID
    auditado_por_id: UUID

class AuditoriaDatosAprobadosResponse(AuditoriaDatosAprobadosBase):
    """Schema de respuesta con datos completos"""
    id: UUID
    incapacidad_id: UUID
    auditado_por_id: UUID
    fecha_auditoria: datetime
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}
```

---

### Paso 1.5: Actualizar Schema de Auditoría

**Archivo**: incapacidad.py

**Modificar `IncapacidadAuditar`**:
```python
class IncapacidadAuditar(BaseModel):
    """Schema para auditar incapacidad con datos modificables"""
    accion: str = Field(
        ..., 
        description="SOLICITAR_INFORMACION, APROBAR_PARA_PAGO, APROBAR_PARA_PAGO_PARCIAL, RECHAZAR"
    )
    observaciones: str = Field(..., min_length=10)
    
    # Campos modificables por el auditor (opcionales)
    fecha_inicio_aprobada: Optional[date] = None
    fecha_fin_aprobada: Optional[date] = None
    dias_aprobados: Optional[int] = Field(None, ge=1)
    cie10_aprobado: Optional[str] = Field(None, max_length=10)
    diagnostico_aprobado: Optional[str] = Field(None, max_length=500)
    
    @field_validator("accion")
    @classmethod
    def validate_accion(cls, v):
        acciones_validas = [
            "SOLICITAR_INFORMACION", 
            "APROBAR_PARA_PAGO", 
            "APROBAR_PARA_PAGO_PARCIAL",  # ← NUEVO
            "RECHAZAR"
        ]
        if v not in acciones_validas:
            raise ValueError(f"Acción debe ser una de: {', '.join(acciones_validas)}")
        return v
    
    @model_validator(mode='after')
    def validate_aprobacion_parcial(self):
        """Validar que si es aprobación parcial, vengan los campos modificables"""
        if self.accion == "APROBAR_PARA_PAGO_PARCIAL":
            required_fields = [
                self.fecha_inicio_aprobada,
                self.fecha_fin_aprobada,
                self.dias_aprobados,
                self.cie10_aprobado,
                self.diagnostico_aprobado
            ]
            if not all(required_fields):
                raise ValueError(
                    "Para aprobación parcial se requieren todos los campos aprobados"
                )
        return self
```

---

### Paso 1.6: Crear Repository

**Archivo**: `backend/app/db/repositories/auditoria_datos_repository.py` (NUEVO)

```python
from app.db.repositories.base_repository import BaseRepository
from app.models.auditoria_datos_aprobados import AuditoriaDatosAprobados
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from typing import Optional

class AuditoriaDatosRepository(BaseRepository[AuditoriaDatosAprobados]):
    """Repository para AuditoriaDatosAprobados"""
    
    def __init__(self):
        super().__init__(AuditoriaDatosAprobados)
    
    async def get_by_incapacidad(
        self, 
        db: AsyncSession, 
        incapacidad_id: UUID
    ) -> Optional[AuditoriaDatosAprobados]:
        """Obtener datos aprobados de una incapacidad"""
        query = select(AuditoriaDatosAprobados).where(
            AuditoriaDatosAprobados.incapacidad_id == incapacidad_id
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()
```

---

### Paso 1.7: Actualizar Service de Incapacidad

**Archivo**: incapacidad_service.py

**Modificar método `auditar_incapacidad`**:

```python
async def auditar_incapacidad(
    self,
    db: AsyncSession,
    incapacidad_id: UUID,
    accion: str,
    observaciones: str,
    usuario_id: Optional[UUID] = None,
    # ← NUEVOS PARÁMETROS
    datos_aprobados: Optional[Dict[str, Any]] = None
) -> Incapacidad:
    """
    Audita una incapacidad con soporte para aprobación parcial.
    
    Args:
        db: Sesión de base de datos
        incapacidad_id: ID de la incapacidad
        accion: SOLICITAR_INFORMACION, APROBAR_PARA_PAGO, APROBAR_PARA_PAGO_PARCIAL, RECHAZAR
        observaciones: Observaciones de la auditoría
        usuario_id: ID del auditor
        datos_aprobados: Dict con campos modificados (solo para aprobación parcial)
    
    Returns:
        Incapacidad auditada
    """
    incapacidad = await self.get_incapacidad(db, incapacidad_id)
    
    if incapacidad.estado != EstadoIncapacidad.EN_AUDITORIA:
        raise InvalidStateException(
            f"Solo se pueden auditar incapacidades en estado EN_AUDITORIA. "
            f"Estado actual: {incapacidad.estado}"
        )
    
    nuevo_estado = None
    update_data = {
        'observaciones': observaciones,
        'fecha_auditoria': datetime.utcnow()
    }
    
    if usuario_id:
        update_data['auditado_por_id'] = usuario_id
    
    if accion == "SOLICITAR_INFORMACION":
        nuevo_estado = EstadoIncapacidad.OBSERVADA
    
    elif accion == "APROBAR_PARA_PAGO":
        nuevo_estado = EstadoIncapacidad.APROBADA
        update_data['fecha_aprobacion'] = datetime.utcnow()
        if usuario_id:
            update_data['aprobado_por_id'] = usuario_id
    
    elif accion == "APROBAR_PARA_PAGO_PARCIAL":  # ← NUEVO
        nuevo_estado = EstadoIncapacidad.APROBADA_PARCIALMENTE
        update_data['fecha_aprobacion'] = datetime.utcnow()
        if usuario_id:
            update_data['aprobado_por_id'] = usuario_id
        
        # Guardar datos aprobados en tabla separada
        if datos_aprobados:
            from app.db.repositories.auditoria_datos_repository import AuditoriaDatosRepository
            auditoria_repo = AuditoriaDatosRepository()
            
            # Verificar si ya existe registro
            datos_existentes = await auditoria_repo.get_by_incapacidad(db, incapacidad_id)
            
            datos_to_save = {
                'incapacidad_id': incapacidad_id,
                'fecha_inicio_aprobada': datos_aprobados.get('fecha_inicio_aprobada'),
                'fecha_fin_aprobada': datos_aprobados.get('fecha_fin_aprobada'),
                'dias_aprobados': datos_aprobados.get('dias_aprobados'),
                'cie10_aprobado': datos_aprobados.get('cie10_aprobado'),
                'diagnostico_aprobado': datos_aprobados.get('diagnostico_aprobado'),
                'observacion_auditoria': observaciones,
                'auditado_por_id': usuario_id,
                'fecha_auditoria': datetime.utcnow()
            }
            
            if datos_existentes:
                # Actualizar existente
                await auditoria_repo.update(db, id=datos_existentes.id, obj_in=datos_to_save)
            else:
                # Crear nuevo
                await auditoria_repo.create(db, obj_in=datos_to_save)
    
    elif accion == "RECHAZAR":
        nuevo_estado = EstadoIncapacidad.RECHAZADA
        update_data['fecha_rechazo'] = datetime.utcnow()
        update_data['motivo_rechazo'] = observaciones
    else:
        raise BadRequestException(f"Acción de auditoría inválida: {accion}")
    
    await self._validate_state_transition(incapacidad.estado, nuevo_estado)
    update_data['estado'] = nuevo_estado
    
    # Actualizar incapacidad
    estado_anterior = incapacidad.estado
    incapacidad_actualizada = await self.repository.update(
        db, id=incapacidad_id, obj_in=update_data
    )
    
    # Registrar en historial
    await historial_estado_service.create_historial_entry(
        db=db,
        entity_type="incapacidad",
        entity_id=incapacidad_id,
        estado_anterior=estado_anterior.value,
        estado_nuevo=nuevo_estado.value,
        observacion=f"Auditoría: {accion} - {observaciones}",
        cambiado_por_id=usuario_id
    )
    
    return incapacidad_actualizada
```

---

### Paso 1.8: Actualizar Endpoint de Auditoría

**Archivo**: incapacidades.py

**Modificar endpoint `auditar_incapacidad`**:

```python
@router.post(
    "/{incapacidad_id}/auditar",
    response_model=IncapacidadInDB,
    summary="Auditar incapacidad",
    description="Audita una incapacidad con soporte para aprobación parcial"
)
async def auditar_incapacidad(
    incapacidad_id: UUID,
    auditoria: IncapacidadAuditar,  # ← Schema actualizado
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Audita una incapacidad.
    
    Acciones disponibles:
    - SOLICITAR_INFORMACION: Pasa a OBSERVADA
    - APROBAR_PARA_PAGO: Pasa a APROBADA (100% de días)
    - APROBAR_PARA_PAGO_PARCIAL: Pasa a APROBADA_PARCIALMENTE (menos días)
    - RECHAZAR: Pasa a RECHAZADA
    
    Para APROBAR_PARA_PAGO_PARCIAL se requieren campos adicionales:
    - fecha_inicio_aprobada
    - fecha_fin_aprobada
    - dias_aprobados
    - cie10_aprobado
    - diagnostico_aprobado
    """
    
    # Preparar datos aprobados si es aprobación parcial
    datos_aprobados = None
    if auditoria.accion == "APROBAR_PARA_PAGO_PARCIAL":
        datos_aprobados = {
            'fecha_inicio_aprobada': auditoria.fecha_inicio_aprobada,
            'fecha_fin_aprobada': auditoria.fecha_fin_aprobada,
            'dias_aprobados': auditoria.dias_aprobados,
            'cie10_aprobado': auditoria.cie10_aprobado,
            'diagnostico_aprobado': auditoria.diagnostico_aprobado,
        }
    
    incap = await incapacidad_service.auditar_incapacidad(
        db,
        incapacidad_id,
        auditoria.accion,
        auditoria.observaciones,
        current_user.id,
        datos_aprobados=datos_aprobados  # ← NUEVO
    )
    return _serialize_incapacidad(incap)
```

---

### Paso 1.9: Agregar Endpoint para Obtener Datos Aprobados

**Archivo**: incapacidades.py

**Agregar nuevo endpoint**:

```python
@router.get(
    "/{incapacidad_id}/datos-aprobados",
    response_model=Optional[AuditoriaDatosAprobadosResponse],
    summary="Obtener datos aprobados en auditoría",
    description="Devuelve los datos aprobados si la incapacidad fue aprobada parcialmente"
)
async def get_datos_aprobados(
    incapacidad_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Obtener datos aprobados de una incapacidad con aprobación parcial"""
    from app.db.repositories.auditoria_datos_repository import AuditoriaDatosRepository
    
    repo = AuditoriaDatosRepository()
    datos = await repo.get_by_incapacidad(db, incapacidad_id)
    
    return datos
```

---

### Paso 1.10: Actualizar Documentación de Flujo

**Archivo**: 04_FLUJO_ESTADOS.md

**Agregar sección 2.9** (después de 2.8 CANCELADA):

```markdown
### 2.9 APROBADA_PARCIALMENTE

**Descripción**: La incapacidad ha sido aprobada **parcialmente** porque el auditor determinó que los días a aprobar son menores a los solicitados.

**Acciones permitidas**:
- Generar orden de pago parcial (→ EN_PAGO_PARCIAL)
- Anular aprobación parcial (solo Admin)

**Usuarios con permiso**:
- Admin
- Auditor (solo generar orden de pago)

**Diferencia con APROBADA**:
- Los datos aprobados (fechas, días, CIE-10) se guardan en la tabla `auditoria_datos_aprobados`
- El valor a pagar se calcula con base en `dias_aprobados` (no `dias_totales`)

**Notificaciones**:
- Email a la empresa indicando aprobación parcial
- Email al empleado indicando días aprobados vs solicitados

---

### 2.10 EN_PAGO_PARCIAL

**Descripción**: Se ha generado orden de pago **parcial** y está en proceso.

**Acciones permitidas**:
- Registrar pago efectuado (→ PAGADA_PARCIALMENTE)
- Anular orden de pago (→ APROBADA_PARCIALMENTE)

**Usuarios con permiso**:
- Admin
- Usuario con rol TESORERIA

**Cálculo de valor**:
- Se usa `dias_aprobados` en lugar de `dias_totales`
- Fórmula: `valor_pago = valor_dia * dias_aprobados`

---

### 2.11 PAGADA_PARCIALMENTE

**Descripción**: El pago **parcial** ha sido efectuado exitosamente.

**Acciones permitidas**:
- Consultar detalles
- Descargar comprobante de pago parcial
- Generar certificados

**Información visible**:
- Días solicitados vs días aprobados
- Valor solicitado vs valor pagado
- Motivo de la aprobación parcial (observación del auditor)

**Notificaciones**:
- Email a la empresa confirmando pago parcial
- Email al empleado confirmando pago parcial con detalle de días
```

**Actualizar diagrama de estados** (sección 1):

```markdown
## 1. Diagrama de Estados

```
                    ┌─────────────┐
                    │   INICIO    │
                    └──────┬──────┘
                           │
                           │ Radicación
                           ▼
                    ┌─────────────┐
              ┌─────┤  RADICADA   ├─────┐
              │     └──────┬──────┘     │
              │            │            │
              │            │ Asignar    │
              │            │ a auditoría│
              │            ▼            │
              │     ┌─────────────┐    │
              │     │EN_AUDITORIA │◄───┤
              │     └──────┬──────┘    │
              │            │            │
              │     ┌──────┴───────┬───┴─────────┬─────────────┐
              │     │              │             │             │
              │     │ Solicitar    │ Aprobar     │ Aprobar     │ Rechazar
              │     │ información  │ 100%        │ Parcial     │
              │     ▼              ▼             ▼             ▼
              │  ┌──────────┐  ┌─────────┐  ┌──────────────┐  ┌──────────┐
              │  │OBSERVADA │  │APROBADA │  │APROBADA_PARC.│  │RECHAZADA │
              │  └────┬─────┘  └────┬────┘  └──────┬───────┘  └──────────┘
              │       │             │               │                │
              │       │ Responder   │ Generar       │ Generar        │
              │       │ observac.   │ orden pago    │ orden pago     │
              │       │             │ completa      │ parcial        │
              │       │             ▼               ▼                │
              │       └────────►┌─────────┐     ┌────────────────┐  │
              │                 │ EN_PAGO │     │EN_PAGO_PARCIAL │  │
              │                 └────┬────┘     └───────┬────────┘  │
              │                      │                  │            │
              │                      │ Confirmar        │ Confirmar  │
              │                      │ pago 100%        │ pago parc. │
              │                      ▼                  ▼            │
              │                 ┌─────────┐      ┌──────────────┐   │
              │                 │ PAGADA  │      │PAGADA_PARC.  │   │
              │                 └─────────┘      └──────────────┘   │
              │                                                      │
              │ Cancelar                                             │
              └─────────────────────────────────────────────────────►│
                                                                     ▼
                                                              ┌──────────┐
                                                              │CANCELADA │
                                                              └──────────┘
```
```

**Actualizar matriz de transiciones** (sección 3):

```markdown
| Estado Actual           | Estado Destino         | Acción                  | Rol Permitido    | Validaciones                    |
|-------------------------|------------------------|-------------------------|------------------|---------------------------------|
| EN_AUDITORIA            | APROBADA_PARCIALMENTE  | Aprobar parcial         | Auditor, Admin   | Datos aprobados obligatorios    |
| APROBADA_PARCIALMENTE   | EN_PAGO_PARCIAL        | Generar orden parcial   | Admin, Auditor   | Datos bancarios completos       |
| EN_PAGO_PARCIAL         | PAGADA_PARCIALMENTE    | Registrar pago parcial  | Admin, Tesorería | Comprobante y referencia        |
```

---

### Paso 1.11: Crear Migración de Alembic

**Comando**:
```bash
cd backend
alembic revision --autogenerate -m "add_auditoria_datos_aprobados_table_and_estados_parciales"
```

**Revisar y ajustar** la migración generada para:
1. Crear tabla `auditoria_datos_aprobados`
2. Agregar índice en `incapacidad_id`
3. Agregar constraint UNIQUE en `incapacidad_id`
4. Agregar FK constraints

---

## 🎨 Parte 2: Frontend (Después de Backend completo)

### Paso 2.1: Actualizar Types

**Archivo**: incapacidad.ts

**Agregar tipos**:

```typescript
// Agregar nuevos estados
export enum EstadoIncapacidad {
  RADICADA = 'RADICADA',
  EN_AUDITORIA = 'EN_AUDITORIA',
  OBSERVADA = 'OBSERVADA',
  APROBADA = 'APROBADA',
  APROBADA_PARCIALMENTE = 'APROBADA_PARCIALMENTE', // ← NUEVO
  RECHAZADA = 'RECHAZADA',
  EN_PAGO = 'EN_PAGO',
  EN_PAGO_PARCIAL = 'EN_PAGO_PARCIAL', // ← NUEVO
  PAGADA = 'PAGADA',
  PAGADA_PARCIALMENTE = 'PAGADA_PARCIALMENTE', // ← NUEVO
  ANULADA = 'ANULADA',
}

// Datos aprobados en auditoría
export interface AuditoriaDatosAprobados {
  id: string;
  incapacidad_id: string;
  fecha_inicio_aprobada: string;
  fecha_fin_aprobada: string;
  dias_aprobados: number;
  cie10_aprobado: string;
  diagnostico_aprobado: string;
  observacion_auditoria: string;
  auditado_por_id: string;
  fecha_auditoria: string;
  created_at: string;
  updated_at: string;
}

// Request de auditoría con campos modificables
export interface IncapacidadAuditarRequest {
  accion: 'SOLICITAR_INFORMACION' | 'APROBAR_PARA_PAGO' | 'APROBAR_PARA_PAGO_PARCIAL' | 'RECHAZAR';
  observaciones: string;
  // Campos modificables (solo para aprobación parcial)
  fecha_inicio_aprobada?: string;
  fecha_fin_aprobada?: string;
  dias_aprobados?: number;
  cie10_aprobado?: string;
  diagnostico_aprobado?: string;
}
```

---

### Paso 2.2: Actualizar Service

**Archivo**: incapacidadService.ts

**Actualizar método `auditar`**:

```typescript
/**
 * WORKFLOW: Auditar incapacidad con soporte para aprobación parcial
 * POST /api/v1/incapacidades/{incapacidad_id}/auditar
 */
async auditar(
  id: string,
  data: IncapacidadAuditarRequest
): Promise<Incapacidad> {
  const { data: response } = await api.post<Incapacidad>(
    `/incapacidades/${id}/auditar`,
    data
  );
  return response;
}

/**
 * Obtener datos aprobados en auditoría
 * GET /api/v1/incapacidades/{id}/datos-aprobados
 */
async getDatosAprobados(id: string): Promise<AuditoriaDatosAprobados | null> {
  const { data } = await api.get<AuditoriaDatosAprobados>(
    `/incapacidades/${id}/datos-aprobados`
  );
  return data;
}
```

---

### Paso 2.3: Crear Componente de Formulario de Auditoría Mejorado

**Archivo**: `frontend/sistema-interno/src/components/incapacidades/AuditoriaFormulario.tsx` (NUEVO)

```tsx
import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Calendar, CheckCircle, XCircle, AlertCircle, Info } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import type { Incapacidad } from '@/types/incapacidad';

// Schema de validación
const auditoriaSchema = z.object({
  fecha_inicio_aprobada: z.string(),
  fecha_fin_aprobada: z.string(),
  cie10_aprobado: z.string().min(3, 'Código CIE-10 inválido'),
  diagnostico_aprobado: z.string().min(10, 'Mínimo 10 caracteres'),
  observacion: z.string().min(10, 'Mínimo 10 caracteres'),
});

type AuditoriaFormData = z.infer<typeof auditoriaSchema>;

interface AuditoriaFormularioProps {
  incapacidad: Incapacidad;
  onAction: (data: any) => void;
  isLoading?: boolean;
}

export function AuditoriaFormulario({ 
  incapacidad, 
  onAction, 
  isLoading 
}: AuditoriaFormularioProps) {
  const [selectedAction, setSelectedAction] = useState<string | null>(null);
  const [diasCalculados, setDiasCalculados] = useState(incapacidad.dias_totales);
  const [esAprobacionParcial, setEsAprobacionParcial] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
    watch,
    reset,
  } = useForm<AuditoriaFormData>({
    resolver: zodResolver(auditoriaSchema),
    defaultValues: {
      fecha_inicio_aprobada: incapacidad.fecha_inicio,
      fecha_fin_aprobada: incapacidad.fecha_fin,
      cie10_aprobado: incapacidad.diagnostico_cie10,
      diagnostico_aprobado: incapacidad.descripcion_diagnostico || '',
      observacion: '',
    },
  });

  // Watchers para cálculo automático de días
  const fechaInicioAprobada = watch('fecha_inicio_aprobada');
  const fechaFinAprobada = watch('fecha_fin_aprobada');

  // Calcular días cuando cambian las fechas
  useEffect(() => {
    if (fechaInicioAprobada && fechaFinAprobada) {
      const inicio = new Date(fechaInicioAprobada);
      const fin = new Date(fechaFinAprobada);
      const diffTime = Math.abs(fin.getTime() - inicio.getTime());
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1;
      setDiasCalculados(diffDays);
      
      // Verificar si es aprobación parcial
      setEsAprobacionParcial(diffDays < incapacidad.dias_totales);
    }
  }, [fechaInicioAprobada, fechaFinAprobada, incapacidad.dias_totales]);

  const onSubmit = (data: AuditoriaFormData) => {
    if (!selectedAction) return;

    // Determinar acción según días calculados
    let accion = selectedAction;
    if (selectedAction === 'APROBADA') {
      accion = esAprobacionParcial ? 'APROBAR_PARA_PAGO_PARCIAL' : 'APROBAR_PARA_PAGO';
    }

    const payload: any = {
      accion,
      observaciones: data.observacion,
    };

    // Si es aprobación (parcial o completa), agregar campos modificables
    if (accion === 'APROBAR_PARA_PAGO' || accion === 'APROBAR_PARA_PAGO_PARCIAL') {
      payload.fecha_inicio_aprobada = data.fecha_inicio_aprobada;
      payload.fecha_fin_aprobada = data.fecha_fin_aprobada;
      payload.dias_aprobados = diasCalculados;
      payload.cie10_aprobado = data.cie10_aprobado;
      payload.diagnostico_aprobado = data.diagnostico_aprobado;
    }

    onAction(payload);
  };

  const handleCancelAction = () => {
    setSelectedAction(null);
    reset();
  };

  const needsObservation = true; // Siempre mostrar observación

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      {/* Información del estado actual */}
      <Alert>
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          Estado actual: <strong>{incapacidad.estado}</strong>. 
          Modifique los datos si es necesario y seleccione una acción.
        </AlertDescription>
      </Alert>

      {/* Sección: Datos Modificables */}
      <div className="space-y-4 p-6 bg-blue-50 rounded-lg border-2 border-blue-200">
        <h3 className="font-semibold text-lg flex items-center gap-2">
          <Calendar className="h-5 w-5" />
          Datos de Auditoría (modificables)
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Fecha Inicio */}
          <div className="space-y-2">
            <Label htmlFor="fecha_inicio_aprobada">Fecha Inicio Aprobada *</Label>
            <Input
              id="fecha_inicio_aprobada"
              type="date"
              {...register('fecha_inicio_aprobada')}
              disabled={isLoading}
            />
            {errors.fecha_inicio_aprobada && (
              <p className="text-sm text-red-500">{errors.fecha_inicio_aprobada.message}</p>
            )}
          </div>

          {/* Fecha Fin */}
          <div className="space-y-2">
            <Label htmlFor="fecha_fin_aprobada">Fecha Fin Aprobada *</Label>
            <Input
              id="fecha_fin_aprobada"
              type="date"
              {...register('fecha_fin_aprobada')}
              disabled={isLoading}
            />
            {errors.fecha_fin_aprobada && (
              <p className="text-sm text-red-500">{errors.fecha_fin_aprobada.message}</p>
            )}
          </div>
        </div>

        {/* Días Calculados */}
        <div className="p-4 bg-white rounded-md border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-600">Días Solicitados</p>
              <p className="text-2xl font-bold text-slate-900">{incapacidad.dias_totales}</p>
            </div>
            <div>
              <p className="text-sm text-slate-600">Días Aprobados</p>
              <p className={`text-2xl font-bold ${esAprobacionParcial ? 'text-orange-600' : 'text-green-600'}`}>
                {diasCalculados}
              </p>
            </div>
            {esAprobacionParcial && (
              <div className="text-orange-600">
                <Info className="h-6 w-6" />
              </div>
            )}
          </div>
          
          {esAprobacionParcial && (
            <Alert className="mt-3 bg-orange-50 border-orange-200">
              <AlertCircle className="h-4 w-4 text-orange-600" />
              <AlertDescription className="text-orange-800">
                ⚠️ Aprobación Parcial: Los días aprobados ({diasCalculados}) son menores a los solicitados ({incapacidad.dias_totales})
              </AlertDescription>
            </Alert>
          )}
        </div>

        {/* CIE-10 */}
        <div className="space-y-2">
          <Label htmlFor="cie10_aprobado">Código CIE-10 Aprobado *</Label>
          <Input
            id="cie10_aprobado"
            {...register('cie10_aprobado')}
            placeholder="Ej: J02.9"
            disabled={isLoading}
          />
          {errors.cie10_aprobado && (
            <p className="text-sm text-red-500">{errors.cie10_aprobado.message}</p>
          )}
        </div>

        {/* Diagnóstico */}
        <div className="space-y-2">
          <Label htmlFor="diagnostico_aprobado">Descripción del Diagnóstico Aprobado *</Label>
          <Textarea
            id="diagnostico_aprobado"
            {...register('diagnostico_aprobado')}
            rows={3}
            placeholder="Descripción del diagnóstico según auditoría..."
            disabled={isLoading}
          />
          {errors.diagnostico_aprobado && (
            <p className="text-sm text-red-500">{errors.diagnostico_aprobado.message}</p>
          )}
        </div>
      </div>

      {/* Observación (SIEMPRE VISIBLE) */}
      <div className="space-y-2">
        <Label htmlFor="observacion">
          Observaciones de Auditoría <span className="text-red-500">*</span>
        </Label>
        <p className="text-sm text-slate-500">
          Describa los hallazgos de la auditoría y justifique su decisión
        </p>
        <Textarea
          id="observacion"
          {...register('observacion')}
          placeholder="Observaciones detalladas de la auditoría..."
          rows={5}
          className="resize-none"
          disabled={isLoading}
        />
        {errors.observacion && (
          <p className="text-sm text-red-500">{errors.observacion.message}</p>
        )}
      </div>

      {/* Botones de acción */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Aprobar (o Aprobar Parcialmente) */}
        <Button
          type="button"
          variant={selectedAction === 'APROBADA' ? 'default' : 'outline'}
          className={`h-32 flex flex-col items-center justify-center space-y-3 transition-all ${
            selectedAction === 'APROBADA' ? 'ring-2 ring-green-500 shadow-lg' : ''
          }`}
          onClick={() => setSelectedAction('APROBADA')}
          disabled={isLoading}
        >
          <CheckCircle className="h-10 w-10 text-green-600" />
          <div className="text-center">
            <p className="font-semibold">
              {esAprobacionParcial ? 'Aprobar Parcialmente' : 'Aprobar'}
            </p>
            <p className="text-xs text-slate-500 mt-1">
              {esAprobacionParcial 
                ? `${diasCalculados} de ${incapacidad.dias_totales} días`
                : 'Aprobar para pago completo'
              }
            </p>
          </div>
        </Button>

        {/* Observar */}
        <Button
          type="button"
          variant={selectedAction === 'OBSERVADA' ? 'default' : 'outline'}
          className={`h-32 flex flex-col items-center justify-center space-y-3 transition-all ${
            selectedAction === 'OBSERVADA' ? 'ring-2 ring-orange-500 shadow-lg' : ''
          }`}
          onClick={() => setSelectedAction('OBSERVADA')}
          disabled={isLoading}
        >
          <AlertCircle className="h-10 w-10 text-orange-600" />
          <div className="text-center">
            <p className="font-semibold">Observar</p>
            <p className="text-xs text-slate-500 mt-1">
              Solicitar información adicional
            </p>
          </div>
        </Button>

        {/* Rechazar */}
        <Button
          type="button"
          variant={selectedAction === 'RECHAZADA' ? 'destructive' : 'outline'}
          className={`h-32 flex flex-col items-center justify-center space-y-3 transition-all ${
            selectedAction === 'RECHAZADA' ? 'ring-2 ring-red-500 shadow-lg' : ''
          }`}
          onClick={() => setSelectedAction('RECHAZADA')}
          disabled={isLoading}
        >
          <XCircle className="h-10 w-10 text-red-600" />
          <div className="text-center">
            <p className="font-semibold">Rechazar</p>
            <p className="text-xs text-slate-500 mt-1">
              Rechazar incapacidad
            </p>
          </div>
        </Button>
      </div>

      {/* Botones de confirmación */}
      {selectedAction && (
        <div className="flex justify-end gap-3 pt-4 border-t border-slate-200">
          <Button
            type="button"
            variant="outline"
            onClick={handleCancelAction}
            disabled={isLoading}
          >
            Cancelar
          </Button>
          <Button 
            type="submit" 
            disabled={isLoading}
            className={
              selectedAction === 'APROBADA' ? 'bg-green-600 hover:bg-green-700' :
              selectedAction === 'OBSERVADA' ? 'bg-orange-600 hover:bg-orange-700' :
              'bg-red-600 hover:bg-red-700'
            }
          >
            {isLoading ? 'Procesando...' : `Confirmar ${selectedAction}`}
          </Button>
        </div>
      )}

      {/* Información adicional */}
      {selectedAction && (
        <Alert className="bg-blue-50 border-blue-200">
          <AlertCircle className="h-4 w-4 text-blue-600" />
          <AlertDescription className="text-blue-800">
            {selectedAction === 'APROBADA' && !esAprobacionParcial && 'La incapacidad quedará lista para generar orden de pago completa.'}
            {selectedAction === 'APROBADA' && esAprobacionParcial && 'Se generará orden de pago PARCIAL por los días aprobados.'}
            {selectedAction === 'OBSERVADA' && 'Se notificará al solicitante para que complete la información.'}
            {selectedAction === 'RECHAZADA' && 'Esta acción es definitiva y no se podrá revertir.'}
          </AlertDescription>
        </Alert>
      )}
    </form>
  );
}
```

---

### Paso 2.4: Rediseñar GestionarPage con Split Screen

**Archivo**: GestionarPage.tsx

**Modificar estructura**:

```tsx
import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ArrowLeft, FileText, ChevronLeft, ChevronRight } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/hooks/use-toast';

import { IncapacidadDetalle } from '@/components/incapacidades/IncapacidadDetalle';
import { DocumentosViewer } from '@/components/incapacidades/DocumentosViewer';
import { HistorialTimeline } from '@/components/incapacidades/HistorialTimeline';
import { AuditoriaFormulario } from '@/components/incapacidades/AuditoriaFormulario';

import { incapacidadService } from '@/services/incapacidadService';

export function GestionarPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  
  // Estado para mostrar/ocultar panel de documentos
  const [showDocumentPanel, setShowDocumentPanel] = useState(true);

  // ... queries existentes ...

  // Verificar si puede gestionar
  const canManage = incapacidad && 
    ['RADICADA', 'EN_AUDITORIA', 'OBSERVADA'].includes(incapacidad.estado);

  // Mutation: Auditar con nuevos campos
  const auditarMutation = useMutation({
    mutationFn: (data: any) => incapacidadService.auditar(id!, data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['incapacidad', id] });
      queryClient.invalidateQueries({ queryKey: ['incapacidad', id, 'historial'] });
      queryClient.invalidateQueries({ queryKey: ['incapacidades-pendientes'] });
      
      toast({
        title: '✅ Auditoría completada',
        description: `La incapacidad ahora está en estado: ${data.estado}`,
      });
      
      setTimeout(() => navigate('/incapacidades/pendientes'), 2000);
    },
    on Error: (error: any) => {
      toast({
        title: '❌ Error al auditar',
        description: error.response?.data?.detail || error.message,
        variant: 'destructive',
      });
    },
  });

  if (isLoading) {
    return <div className="flex justify-center p-12">Cargando...</div>;
  }

  if (!incapacidad) {
    return <div className="p-12 text-center">Incapacidad no encontrada</div>;
  }

  return (
    <div className="flex h-[calc(100vh-4rem)]">
      {/* Panel de Documentos (colapsable) */}
      {showDocumentPanel && (
        <div className="w-1/2 border-r bg-slate-50 overflow-y-auto p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <FileText className="h-5 w-5" />
              Documentos Adjuntos
            </h2>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowDocumentPanel(false)}
            >
              <ChevronLeft className="h-4 w-4" />
              Ocultar
            </Button>
          </div>
          
          <DocumentosViewer documentos={documentos || []} />
        </div>
      )}

      {/* Panel Principal */}
      <div className={`${showDocumentPanel ? 'w-1/2' : 'w-full'} overflow-y-auto`}>
        <div className="p-6 space-y-6">
          {/* Header */}
          <div className="flex items-center justify-between">
            <Button
              variant="ghost"
              onClick={() => navigate('/incapacidades/pendientes')}
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              Volver a Pendientes
            </Button>

            {!showDocumentPanel && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowDocumentPanel(true)}
              >
                <ChevronRight className="h-4 w-4 mr-2" />
                Mostrar Documentos
              </Button>
            )}
          </div>

          {/* Título */}
          <div>
            <h1 className="text-3xl font-bold">
              Auditoría de Incapacidad
            </h1>
            <p className="text-slate-500 mt-1">
              {incapacidad.numero}
            </p>
          </div>

          {/* Tabs */}
          <Tabs defaultValue="auditoria" className="w-full">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="auditoria">
                Auditoría
              </TabsTrigger>
              <TabsTrigger value="detalle">
                Detalle Completo
              </TabsTrigger>
              <TabsTrigger value="historial">
                Historial
              </TabsTrigger>
            </TabsList>

            {/* Tab: Auditoría */}
            <TabsContent value="auditoria" className="space-y-6">
              {canManage ? (
                <Card className="p-6">
                  <AuditoriaFormulario
                    incapacidad={incapacidad}
                    onAction={auditarMutation.mutate}
                    isLoading={auditarMutation.isPending}
                  />
                </Card>
              ) : (
                <Card className="p-6 bg-slate-50">
                  <div className="flex items-start gap-3">
                    <AlertCircle className="h-5 w-5 text-slate-500 mt-0.5" />
                    <div>
                      <p className="font-medium text-slate-700">
                        Esta incapacidad no se puede auditar en su estado actual
                      </p>
                      <p className="text-sm text-slate-500 mt-1">
                        Las acciones de auditoría solo están disponibles para incapacidades en estado 
                        RADICADA, EN_AUDITORIA u OBSERVADA.
                      </p>
                    </div>
                  </div>
                </Card>
              )}
            </TabsContent>

            {/* Tab: Detalle */}
            <TabsContent value="detalle">
              <IncapacidadDetalle incapacidad={incapacidad} />
            </TabsContent>

            {/* Tab: Historial */}
            <TabsContent value="historial">
              <HistorialTimeline historial={historial || []} />
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
}
```

---

## 📝 Parte 3: Testing

### Paso 3.1: Tests Backend

**Archivo**: `backend/tests/test_auditoria_parcial.py` (NUEVO)

```python
import pytest
from datetime import date

@pytest.mark.asyncio
async def test_aprobar_parcialmente(client, test_incapacidad, test_user_auditor):
    """Test de aprobación parcial con días menores"""
    
    response = await client.post(
        f"/api/v1/incapacidades/{test_incapacidad.id}/auditar",
        json={
            "accion": "APROBAR_PARA_PAGO_PARCIAL",
            "observaciones": "Aprobado solo 5 días de los 10 solicitados según auditoría médica",
            "fecha_inicio_aprobada": "2026-01-10",
            "fecha_fin_aprobada": "2026-01-14",  # 5 días
            "dias_aprobados": 5,
            "cie10_aprobado": "J02.9",
            "diagnostico_aprobado": "Faringitis aguda no especificada"
        },
        headers={"Authorization": f"Bearer {test_user_auditor.access_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["estado"] == "APROBADA_PARCIALMENTE"
    
    # Verificar que se guardaron los datos aprobados
    response_datos = await client.get(
        f"/api/v1/incapacidades/{test_incapacidad.id}/datos-aprobados",
        headers={"Authorization": f"Bearer {test_user_auditor.access_token}"}
    )
    
    assert response_datos.status_code == 200
    datos = response_datos.json()
    assert datos["dias_aprobados"] == 5
    assert datos["cie10_aprobado"] == "J02.9"
```

---

### Paso 3.2: Tests Frontend

**Archivo**: `frontend/sistema-interno/src/components/incapacidades/__tests__/AuditoriaFormulario.test.tsx` (NUEVO)

```tsx
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { AuditoriaFormulario } from '../AuditoriaFormulario';

describe('AuditoriaFormulario', () => {
  const mockIncapacidad = {
    id: '1',
    numero: 'INC-001',
    estado: 'EN_AUDITORIA',
    fecha_inicio: '2026-01-10',
    fecha_fin: '2026-01-20',
    dias_totales: 11,
    diagnostico_cie10: 'J02.9',
    descripcion_diagnostico: 'Faringitis',
  };

  it('debe calcular días automáticamente', async () => {
    const onAction = vi.fn();
    render(<AuditoriaFormulario incapacidad={mockIncapacidad} onAction={onAction} />);
    
    // Cambiar fecha fin a solo 5 días
    const fechaFinInput = screen.getByLabelText(/Fecha Fin Aprobada/i);
    fireEvent.change(fechaFinInput, { target: { value: '2026-01-14' } });
    
    // Debe mostrar 5 días calculados
    await waitFor(() => {
      expect(screen.getByText('5')).toBeInTheDocument();
    });
    
    // Debe mostrar alerta de aprobación parcial
    expect(screen.getByText(/Aprobación Parcial/i)).toBeInTheDocument();
  });

  it('debe enviar acción APROBAR_PARA_PAGO_PARCIAL cuando días < solicitados', async () => {
    const onAction = vi.fn();
    render(<AuditoriaFormulario incapacidad={mockIncapacidad} onAction={onAction} />);
    
    // Reducir días
    fireEvent.change(screen.getByLabelText(/Fecha Fin Aprobada/i), {
      target: { value: '2026-01-14' }
    });
    
    // Llenar observaciones
    fireEvent.change(screen.getByLabelText(/Observaciones/i), {
      target: { value: 'Solo se aprueban 5 días según auditoría médica' }
    });
    
    // Click en Aprobar
    fireEvent.click(screen.getByText(/Aprobar Parcialmente/i));
    
    // Confirmar
    fireEvent.click(screen.getByText(/Confirmar/i));
    
    await waitFor(() => {
      expect(onAction).toHaveBeenCalledWith(
        expect.objectContaining({
          accion: 'APROBAR_PARA_PAGO_PARCIAL',
          dias_aprobados: 5
        })
      );
    });
  });
});
```

---

## 📊 Parte 4: Documentación

### Paso 4.1: Actualizar README

**Archivo**: README.md

**Agregar sección**:

```markdown
### Aprobación Parcial de Incapacidades

El sistema soporta **aprobación parcial** cuando el auditor determina que los días a aprobar son menores a los solicitados:

**Flujo**:
1. Auditor modifica fechas, CIE-10 o diagnóstico durante la auditoría
2. Sistema calcula días automáticamente
3. Si `días_aprobados < días_solicitados` → Estado: **APROBADA_PARCIALMENTE**
4. Los datos aprobados se guardan en tabla separada
5. Orden de pago se genera con base en `días_aprobados`

**Estados del flujo parcial**:
```
EN_AUDITORIA → APROBADA_PARCIALMENTE → EN_PAGO_PARCIAL → PAGADA_PARCIALMENTE
```
```

---

## ✅ Checklist Final

### Backend
- [ ] Migración Alembic ejecutada
- [ ] Tabla `auditoria_datos_aprobados` creada
- [ ] Enums actualizados con estados parciales
- [ ] Matriz de transiciones actualizada
- [ ] Service `auditar_incapacidad` con soporte parcial
- [ ] Endpoint `/auditar` actualizado
- [ ] Endpoint `/datos-aprobados` creado
- [ ] Tests de aprobación parcial (>3 tests)
- [ ] Documentación 04_FLUJO_ESTADOS.md actualizada

### Frontend
- [ ] Types con estados parciales
- [ ] Service con método `auditar` actualizado
- [ ] Componente `AuditoriaFormulario` creado
- [ ] GestionarPage rediseñada (split screen)
- [ ] Cálculo automático de días
- [ ] Lógica de aprobación parcial
- [ ] Panel de documentos colapsable
- [ ] Tests del formulario (>5 tests)

### Validaciones
- [ ] Build backend sin errores
- [ ] Build frontend sin errores
- [ ] Migraciones aplicables sin errores
- [ ] Tests backend pasando (>80%)
- [ ] Tests frontend pasando (>75%)

---

## 🚀 Orden de Ejecución Recomendado

**Día 1-2: Backend Core**
1. Crear tabla y modelos (Paso 1.1)
2. Actualizar enums y transiciones (Pasos 1.2, 1.3)
3. Crear schemas (Pasos 1.4, 1.5)
4. Ejecutar migración

**Día 3: Backend Services & Endpoints**
5. Repository (Paso 1.6)
6. Service actualizado (Paso 1.7)
7. Endpoints (Pasos 1.8, 1.9)
8. Tests backend (Paso 3.1)

**Día 4: Documentación**
9. Actualizar 04_FLUJO_ESTADOS.md (Paso 1.10)

**Día 5-6: Frontend Components**
10. Actualizar types (Paso 2.1)
11. Actualizar service (Paso 2.2)
12. Componente AuditoriaFormulario (Paso 2.3)

**Día 7: Frontend Integration**
13. Rediseñar GestionarPage (Paso 2.4)
14. Tests frontend (Paso 3.2)

**Día 8: Testing & QA**
15. Validación manual completa
16. Ajustes finales
17. Documentación README (Paso 4.1)
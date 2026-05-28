# Cambios Arquitectónicos: Soporte para Incapacidades ARL y SALUD

**Fecha**: 6 de enero de 2026  
**Tipo**: Cambio Arquitectónico Mayor  
**Impacto**: Modelos, Schemas, Documentación

---

## 📋 Resumen del Cambio

El sistema ahora soporta **dos tipos diferentes de incapacidades**:

### 1. **Incapacidades ARL** (Riesgos Laborales)
- **Asociadas a**: Empleados de empresas
- **Requiere**: `empleado_id` + `empresa_id`
- **Puede tener**: `siniestro_id` + `numero_siniestro`
- **Caso de uso**: Accidentes laborales, enfermedades profesionales

### 2. **Incapacidades SALUD** (Pólizas de Salud)
- **Asociadas a**: Afiliados con póliza
- **Requiere**: `afiliado_id`
- **NO tiene**: empleado/empresa/siniestro
- **Caso de uso**: Enfermedades generales de asegurados

---

## 🔧 Cambios Implementados

### 1. Nuevo Modelo: `Afiliado`

**Archivo**: `backend/app/models/afiliado.py`

Representa personas aseguradas con pólizas de salud (no son empleados).

**Campos principales**:
- `numero_poliza` (unique): Identificador de la póliza
- `tipo_poliza`: INDIVIDUAL, FAMILIAR, COLECTIVA
- Datos personales: documento, nombres, apellidos, email, teléfono
- Vigencia: `fecha_inicio_poliza`, `fecha_fin_poliza`
- Datos bancarios: cuenta, banco, tipo_cuenta
- `estado`: ACTIVO, INACTIVO, SUSPENDIDO
- Sincronización: `sync_source`, `external_id`

**Relaciones**:
- `incapacidades`: Lista de incapacidades de salud del afiliado

### 2. Modelo Modificado: `Incapacidad`

**Archivo**: `backend/app/models/incapacidad.py`

**Cambios clave**:
- `empleado_id`: Ahora es **opcional** (NULL si tipo=SALUD)
- `empresa_id`: Ahora es **opcional** (NULL si tipo=SALUD)
- `afiliado_id`: **Nuevo campo** (NULL si tipo=ARL)

**Constraint de validación**:
```sql
CHECK (
    (tipo = 'ARL' AND empleado_id IS NOT NULL AND empresa_id IS NOT NULL AND afiliado_id IS NULL) OR
    (tipo = 'SALUD' AND afiliado_id IS NOT NULL AND empleado_id IS NULL AND empresa_id IS NULL)
)
```

**Relaciones actualizadas**:
- `empleado`: Opcional
- `empresa`: Opcional
- `afiliado`: Opcional (nueva)
- `siniestro`: Solo para ARL

### 3. Nuevo Schema: `Afiliado`

**Archivo**: `backend/app/schemas/afiliado.py`

**Schemas creados**:
- `AfiliadoBase`: Campos base
- `AfiliadoCreate`: Para POST (crear)
- `AfiliadoUpdate`: Para PUT/PATCH (actualizar)
- `AfiliadoResponse`: Para GET (respuesta completa)
- `AfiliadoListItem`: Para listados

### 4. Schemas Modificados: `Incapacidad`

**Archivo**: `backend/app/schemas/incapacidad.py`

**Nuevos schemas especializados**:
- `IncapacidadARLCreate`: Para crear incapacidades ARL
  - Requiere: `empleado_id`, `empresa_id`
  - Tipo fijo: `ARL`
  
- `IncapacidadSaludCreate`: Para crear incapacidades SALUD
  - Requiere: `afiliado_id`
  - Tipo fijo: `SALUD`

**Schema genérico actualizado**:
- `IncapacidadCreate`: Valida que campos requeridos estén presentes según tipo
- `AfiliadoSimple`: Nuevo schema para respuestas (nombre completo, número de póliza)

**Validación en Pydantic**:
```python
@model_validator(mode='after')
def validate_tipo_relacion(self):
    if self.tipo == TipoIncapacidad.ARL:
        if not self.empleado_id or not self.empresa_id:
            raise ValueError("empleado_id y empresa_id obligatorios para ARL")
        if self.afiliado_id:
            raise ValueError("afiliado_id no debe estar en ARL")
    elif self.tipo == TipoIncapacidad.SALUD:
        if not self.afiliado_id:
            raise ValueError("afiliado_id obligatorio para SALUD")
        if self.empleado_id or self.empresa_id:
            raise ValueError("empleado/empresa no deben estar en SALUD")
    return self
```

### 5. Enums Actualizados

**Archivo**: `backend/app/utils/enums.py`

**Nuevo enum**:
```python
class EstadoAfiliado(str, Enum):
    ACTIVO = "ACTIVO"
    INACTIVO = "INACTIVO"
    SUSPENDIDO = "SUSPENDIDO"
```

### 6. Exports Actualizados

**Archivos modificados**:
- `backend/app/models/__init__.py`: Agregado `Afiliado`
- `backend/app/schemas/__init__.py`: Agregados 5 schemas de `Afiliado`

---

## 📚 Documentación Actualizada

### 1. Modelo de Datos (`docs/02_MODELO_DATOS.md`)

**Cambios**:
- Diagrama ER actualizado con entidad `AFILIADO`
- Nueva sección 2.3: Tabla AFILIADO con DDL completo
- Sección 2.5 (antes 2.4): Tabla INCAPACIDAD actualizada
  - Nota explicativa sobre tipos ARL y SALUD
  - Campos `empleado_id`, `empresa_id`, `afiliado_id` documentados como opcionales
  - Nuevo constraint `chk_incapacidad_tipo_relacion`
  - Nuevo índice `idx_incapacidad_afiliado`

**SQL Agregado**:
```sql
CREATE TABLE afiliado (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    numero_poliza VARCHAR(50) UNIQUE NOT NULL,
    tipo_poliza VARCHAR(50) NOT NULL,
    -- ... más campos
    CONSTRAINT chk_afiliado_estado CHECK (estado IN ('ACTIVO', 'INACTIVO', 'SUSPENDIDO')),
    CONSTRAINT chk_afiliado_tipo_poliza CHECK (tipo_poliza IN ('INDIVIDUAL', 'FAMILIAR', 'COLECTIVA'))
);
```

### 2. Arquitectura (`docs/01_ARQUITECTURA.md`)

**Cambios en diagrama de servicios**:
- Agregado `Afiliado Service` en capa de aplicación
- Documentadas responsabilidades: Pólizas, Validación
- Actualizado servicio de Incapacidad para mencionar ARL/SALUD

### 3. API Endpoints (`docs/03_API_ENDPOINTS.md`)

**Nueva sección 5.5**: Módulo de Afiliados

**Endpoints agregados**:
1. `GET /afiliados` - Listar afiliados
2. `GET /afiliados/{afiliado_id}` - Obtener afiliado
3. `POST /afiliados` - Crear afiliado
4. `GET /afiliados/{afiliado_id}/incapacidades` - Incapacidades del afiliado

**Sección 6 actualizada**: Módulo de Incapacidades

**Cambios**:
- `GET /incapacidades`: Agregado filtro `afiliado_id`
- `POST /incapacidades`: Dos formatos de request (ARL y SALUD)
  - Request para ARL con `empleado_id`, `empresa_id`
  - Request para SALUD con `afiliado_id`
  - Validación documentada

---

## 🧪 Testing Requerido

### Tests Unitarios
- [ ] Modelo Afiliado: CRUD básico
- [ ] Modelo Incapacidad: Validación de constraint
- [ ] Schema Afiliado: Validación de campos
- [ ] Schema Incapacidad: Validación de tipo ARL/SALUD

### Tests de Integración
- [ ] Crear afiliado y vincular incapacidad SALUD
- [ ] Crear empleado y vincular incapacidad ARL
- [ ] Intentar crear incapacidad ARL con afiliado_id (debe fallar)
- [ ] Intentar crear incapacidad SALUD con empleado_id (debe fallar)

### Tests de API
- [ ] POST /afiliados - Crear afiliado
- [ ] POST /incapacidades - Crear incapacidad ARL
- [ ] POST /incapacidades - Crear incapacidad SALUD
- [ ] Validación de errores 400 en mezcla incorrecta

---

## 🗄️ Migraciones Pendientes

### Migración Alembic Requerida

**Acciones**:
1. Crear tabla `afiliado`
2. Modificar tabla `incapacidad`:
   - Cambiar `empleado_id` a NULLABLE
   - Cambiar `empresa_id` a NULLABLE
   - Agregar `afiliado_id` NULLABLE con FK
   - Agregar constraint `chk_incapacidad_tipo_relacion`
   - Crear índice en `afiliado_id`

**Comando**:
```bash
alembic revision --autogenerate -m "Add afiliado table and update incapacidad for ARL/SALUD support"
```

**IMPORTANTE**: Verificar la migración antes de aplicar, especialmente:
- Constraint de validación se crea correctamente
- Índices existentes no se eliminan
- Foreign keys se manejan apropiadamente

---

## 📊 Estadísticas del Cambio

### Archivos Creados: 2
- `backend/app/models/afiliado.py` (72 líneas)
- `backend/app/schemas/afiliado.py` (96 líneas)

### Archivos Modificados: 7
1. `backend/app/models/incapacidad.py` (+15 líneas)
2. `backend/app/models/__init__.py` (+1 import)
3. `backend/app/schemas/incapacidad.py` (+60 líneas cambio mayor)
4. `backend/app/schemas/__init__.py` (+5 exports)
5. `backend/app/utils/enums.py` (+6 líneas)
6. `docs/02_MODELO_DATOS.md` (+80 líneas)
7. `docs/03_API_ENDPOINTS.md` (+140 líneas)

### Total: ~470 líneas agregadas

---

## ✅ Checklist de Implementación

- [x] Crear modelo `Afiliado`
- [x] Modificar modelo `Incapacidad`
- [x] Crear schemas `Afiliado`
- [x] Actualizar schemas `Incapacidad`
- [x] Actualizar enums
- [x] Actualizar exports de modelos
- [x] Actualizar exports de schemas
- [x] Actualizar documentación: Modelo de Datos
- [x] Actualizar documentación: Arquitectura
- [x] Actualizar documentación: API Endpoints
- [ ] Crear migración Alembic
- [ ] Aplicar migración a base de datos
- [ ] Crear datos de prueba (afiliados)
- [ ] Implementar repositorio `AfiliadoRepository`
- [ ] Implementar servicio `AfiliadoService`
- [ ] Implementar endpoints `/afiliados/*`
- [ ] Actualizar endpoints `/incapacidades/*`
- [ ] Agregar tests unitarios
- [ ] Agregar tests de integración
- [ ] Actualizar documentación de usuario

---

## 🚀 Próximos Pasos

1. **Crear migración Alembic** (PRIORITARIO)
   ```bash
   cd backend
   alembic revision --autogenerate -m "Add afiliado support for SALUD incapacidades"
   alembic upgrade head
   ```

2. **Implementar Repository Layer**
   - `AfiliadoRepository` con CRUD básico
   - Actualizar `IncapacidadRepository` para joins opcionales

3. **Implementar Service Layer**
   - `AfiliadoService` para lógica de negocio
   - Actualizar `IncapacidadService` para validar tipo

4. **Implementar API Endpoints**
   - Router `/api/v1/afiliados`
   - Actualizar router `/api/v1/incapacidades`

5. **Testing**
   - Tests unitarios de modelos y schemas
   - Tests de integración de workflow ARL y SALUD

---

## 📝 Notas Técnicas

### Diferencias Clave ARL vs SALUD

| Aspecto | ARL | SALUD |
|---------|-----|-------|
| **Vinculado a** | Empleado de empresa | Afiliado con póliza |
| **Campos requeridos** | empleado_id, empresa_id | afiliado_id |
| **Puede tener siniestro** | ✅ Sí | ❌ No |
| **Número de radicación** | INC-YYYYMM-ARL-NNNNN | INC-YYYYMM-SALUD-NNNNN |
| **Workflow** | RADICADA → ... → PAGADA | RADICADA → ... → PAGADA |
| **Beneficiario pago** | Empleado | Afiliado |

### Consideraciones de Diseño

1. **Modelo Polimórfico**: Incapacidad puede relacionarse con Empleado O Afiliado
2. **Constraint a nivel DB**: Garantiza integridad referencial
3. **Validación en Schema**: Previene errores antes de llegar a DB
4. **Índices separados**: Optimización para consultas por empleado o afiliado
5. **Backward compatibility**: Datos existentes de ARL no se afectan

---

**Estado**: ✅ Cambios implementados y documentados  
**Pendiente**: Migración Alembic y capa de servicios

# Plan de Implementación: Consulta de Incapacidades

**Fecha de creación**: 17 de enero de 2026  
**Versión**: 1.0.0  
**Estado**: 📋 Planificación  
**Prioridad**: 🔴 CRÍTICA - Bloquea Fase 1

---

## 📋 Resumen Ejecutivo

### Objetivo

Completar el **Portal Externo - Fase 1** implementando la funcionalidad de **Consulta Pública de Incapacidades**, permitiendo a usuarios SIN AUTENTICACIÓN consultar el estado de sus radicaciones mediante:

1. **Número de radicación** (ej: `INC-202601-000001`)
2. **Documento de identidad + tipo** (ej: CC 1234567890)

### Contexto

- ✅ **Wizard de radicación**: 100% completado (217 tests)
- ⏳ **Módulo de consulta**: 0% implementado
- **Estado Fase 1**: 80% completo (INCOMPLETO)

### Entregables

1. **Backend**:
   - 1 endpoint público de consulta
   - 1 endpoint de descarga pública de documentos
   - Tests (13 nuevos)
   - Documentación Swagger

2. **Frontend**:
   - 6 componentes nuevos
   - 1 página de consulta
   - 1 Página para decidir si consultar o radicar
   - 60+ tests nuevos
   - Integración completa

3. **Documentación**:
   - Guía técnica completa
   - Guía de usuario
   - FAQ

### Estimación Total

- **Backend**: 1 día
- **Frontend**: 2-3 días
- **Documentación**: 0.5 día
- **Testing final**: 0.5 día

**Total**: 4-5 días de desarrollo

---

## 🎯 Fase 1: Backend - API Endpoints (1 día)

### 1.1 Endpoint de Consulta Pública

#### Especificación Técnica

**Archivo**: `backend/app/api/v1/endpoints/incapacidades.py`

**Endpoint**:
```python
@router.get(
    "/consultar",
    response_model=ConsultaIncapacidadPublicResponse,
    summary="Consultar incapacidad pública (sin autenticación)",
    description="Permite consultar el estado de una incapacidad por número o documento",
    tags=["incapacidades-publico"]
)
async def consultar_incapacidad_publica(
    numero: str | None = Query(None, description="Número de radicación (ej: INC-202601-000001)"),
    documento: str | None = Query(None, description="Número de documento de identidad"),
    tipo_documento: TipoDocumento | None = Query(None, description="Tipo de documento"),
    db: AsyncSession = Depends(get_db)
) -> ConsultaIncapacidadPublicResponse:
    """
    Consulta pública de incapacidad SIN AUTENTICACIÓN.
    
    Dos modos de búsqueda:
    1. Por número de radicación:
       - Parámetro: numero (ej: INC-202601-000001)
       
    2. Por documento de identidad:
       - Parámetros: documento + tipo_documento
       
    Retorna:
    - Información básica de la incapacidad
    - Timeline de estados (historial)
    - Lista de documentos descargables
    - Información de contacto para soporte
    
    Nota: 
    - Los datos sensibles están sanitizados
    - Solo se muestran documentos públicos
    - Rate limiting: 20 requests por minuto por IP
    """
```

#### Request Examples

```bash
# Búsqueda por número
GET /api/v1/incapacidades/consultar?numero=INC-202601-000001

# Búsqueda por documento
GET /api/v1/incapacidades/consultar?documento=1234567890&tipo_documento=CEDULA
```

#### Response Example

```json
{
  "numero": "INC-202601-000001",
  "estado": "EN_AUDITORIA",
  "tipo": "ARL",
  "fecha_inicio": "2026-01-10",
  "fecha_fin": "2026-01-20",
  "dias_totales": 11,
  "nombre_completo": "Juan Pérez García",
  "tipo_documento": "CEDULA",
  "historial_estados": [
    {
      "estado": "RADICADA",
      "fecha_cambio": "2026-01-10T09:00:00",
      "observaciones": null
    },
    {
      "estado": "EN_AUDITORIA",
      "fecha_cambio": "2026-01-11T14:30:00",
      "observaciones": "Asignado a auditor Juan López"
    }
  ],
  "documentos": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "nombre_archivo": "incapacidad_medica.pdf",
      "tipo_documento": "INCAPACIDAD_MEDICA",
      "tamanio_kb": 450,
      "fecha_upload": "2026-01-10T09:05:00"
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "nombre_archivo": "cedula.pdf",
      "tipo_documento": "CEDULA",
      "tamanio_kb": 120,
      "fecha_upload": "2026-01-10T09:06:00"
    }
  ],
  "observaciones_publicas": null,
  "created_at": "2026-01-10T09:00:00",
  "updated_at": "2026-01-11T14:30:00"
}
```

#### Implementación del Service

**Archivo**: `backend/app/services/incapacidad_service.py`

#### Validaciones

```python
# En el endpoint
if not numero and not (documento and tipo_documento):
    raise HTTPException(
        status_code=400,
        detail={
            "mensaje": "Parámetros inválidos",
            "error": "Debe proporcionar número de radicación O documento + tipo_documento",
            "ejemplos": {
                "por_numero": "/consultar?numero=INC-202601-000001",
                "por_documento": "/consultar?documento=1234567890&tipo_documento=CEDULA"
            }
        }
    )
```

#### Tests Backend

**Archivo**: `backend/tests/test_consulta_publica.py`

**Total tests backend**: 10 tests

---

### 1.2 Endpoint de Descarga Pública de Documentos

#### Especificación Técnica

**Endpoint**:
```python
@router.get(
    "/{numero}/documentos/{documento_id}/download",
    summary="Descargar documento público (sin autenticación)",
    description="Genera URL de descarga temporal para un documento público",
    tags=["incapacidades-publico"],
    response_model=PresignedUrlResponse
)
async def descargar_documento_publico(
    numero: str = Path(..., description="Número de radicación"),
    documento_id: UUID = Path(..., description="ID del documento"),
    db: AsyncSession = Depends(get_db)
) -> PresignedUrlResponse:
    """
    Genera URL de descarga temporal (15 minutos) para documento público.
    
    Validaciones:
    - El documento debe pertenecer a la incapacidad especificada
    - El tipo de documento debe ser público (no sensible)
    - Rate limiting: 10 descargas por hora por IP
    
    Retorna:
    - URL pre-firmada válida por 15 minutos
    - Metadata del documento
    """
```

#### Implementación

```python
async def descargar_documento_publico(
    self,
    db: AsyncSession,
    numero: str,
    documento_id: UUID
) -> PresignedUrlResponse:
    """
    Genera URL de descarga pública para documento.
    
    Validaciones:
    1. Incapacidad existe
    2. Documento pertenece a la incapacidad
    3. Tipo de documento es público
    """
    # Buscar incapacidad
    incapacidad = await self.repository.get_by_numero(db, numero)
    if not incapacidad:
        raise NotFoundException(f"Incapacidad {numero} no encontrada")
    
    # Buscar documento
    documento = await db.get(Documento, documento_id)
    if not documento:
        raise NotFoundException("Documento no encontrado")
    
    # Validar que pertenece a la incapacidad
    if documento.incapacidad_id != incapacidad.id:
        raise PermissionException("El documento no pertenece a esta incapacidad")
    
    # Validar tipo público
    tipos_publicos = [
        TipoDocumentoArchivo.INCAPACIDAD_MEDICA,
        TipoDocumentoArchivo.CEDULA,
        TipoDocumentoArchivo.HISTORIA_CLINICA
    ]
    if documento.tipo_documento not in tipos_publicos:
        raise PermissionException("Este tipo de documento no es público")
    
    # Generar presigned URL (15 minutos)
    presigned_url = await storage_service.generate_presigned_url(
        bucket=settings.MINIO_BUCKET_DOCUMENTOS,
        object_name=documento.storage_path,
        expires=900  # 15 minutos
    )
    
    return PresignedUrlResponse(
        url=presigned_url,
        expires_in=900,
        nombre_archivo=documento.nombre_archivo,
        tipo_documento=documento.tipo_documento
    )
```

#### Tests

**Total tests descarga**: 3 tests

---

### 1.3 Rate Limiting

**Archivo**: `backend/app/core/rate_limit.py`

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

# Aplicar en endpoints públicos
@limiter.limit("20/minute")  # Consulta
@limiter.limit("10/hour")     # Descarga
```

---

### 1.4 Documentación Swagger

Agregar ejemplos en OpenAPI:

```python
@router.get(
    "/consultar",
    # ...
    responses={
        200: {
            "description": "Incapacidad encontrada",
            "content": {
                "application/json": {
                    "example": {
                        "numero": "INC-202601-000001",
                        "estado": "EN_AUDITORIA",
                        # ... ejemplo completo
                    }
                }
            }
        },
        404: {
            "description": "Incapacidad no encontrada",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "No se encontró ninguna incapacidad con los datos proporcionados",
                        "mensaje": "Verifique el número de radicación o los datos del documento",
                        "contacto": {
                            "email": "[email protected]",
                            "telefono": "+57 (1) 234-5678"
                        }
                    }
                }
            }
        }
    }
)
```

---

## 🎨 Fase 2: Frontend - Componentes (2-3 días)

### 2.1 Routing y Estructura

**Archivo**: `frontend/portal-externo/src/main.tsx`

```typescript
import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import { HomePage } from '@/pages/HomePage';
import { RadicarIncapacidad } from '@/pages/RadicarIncapacidad';
import { ConsultarIncapacidad } from '@/pages/ConsultarIncapacidad';

const router = createBrowserRouter([
  {
    path: '/',
    element: <HomePage />,
  },
  {
    path: '/radicar',
    element: <RadicarIncapacidad />,
  },
  {
    path: '/consultar',
    element: <ConsultarIncapacidad />,
  },
]);

function App() {
  return <RouterProvider router={router} />;
}
```

---

### 2.2 Tipos TypeScript

**Archivo**: `frontend/portal-externo/src/types/consulta.ts`

---

### 2.3 Servicio API

**Archivo**: `frontend/portal-externo/src/services/consultaService.ts`

---

### 2.4 Schemas de Validación

**Archivo**: `frontend/portal-externo/src/schemas/consultaSchema.ts`

---

### 2.5 Componente de Búsqueda

**Archivo**: `frontend/portal-externo/src/components/consulta/BusquedaIncapacidad.tsx`

---

### 2.6 Vista Detallada de Incapacidad

**Archivo**: `frontend/portal-externo/src/components/consulta/DetalleIncapacidad.tsx`

---

### 2.7 Timeline de Estados

**Archivo**: `frontend/portal-externo/src/components/consulta/TimelineEstados.tsx`

---

### 2.8 Lista de Documentos Descargables

**Archivo**: `frontend/portal-externo/src/components/consulta/DocumentosDescargables.tsx`

### 2.9 Página Principal de Consulta

**Archivo**: `frontend/portal-externo/src/pages/ConsultarIncapacidad.tsx`

---

## 📝 Fase 3: Documentación (0.5 día)

### 3.1 Documentación Técnica

**Archivo**: `docs/10_CONSULTA_INCAPACIDADES.md`

---

### 3.2 Actualizar README Principal

Agregar sección de consulta en [`frontend/portal-externo/README.md`](frontend/portal-externo/README.md):

---

### 3.3 Guía de Usuario

**Archivo**: `docs/GUIA_USUARIO_CONSULTA.md`

---

## ✅ Checklist de Implementación

### Backend (1 día)

- [ ] Crear schema `ConsultaIncapacidadPublicResponse`
- [ ] Crear schema `HistorialEstadoSimple`
- [ ] Crear schema `DocumentoSimple`
- [ ] Crear schema `ContactoSoporte`
- [ ] Implementar `IncapacidadService.consultar_incapacidad_publica()`
- [ ] Implementar `IncapacidadService.descargar_documento_publico()`
- [ ] Crear endpoint `GET /incapacidades/consultar`
- [ ] Crear endpoint `GET /incapacidades/{numero}/documentos/{doc_id}/download`
- [ ] Implementar rate limiting
- [ ] Tests unitarios (10 tests)
- [ ] Tests de integración (3 tests)
- [ ] Documentación Swagger con ejemplos
- [ ] Verificar sanitización de datos sensibles

### Frontend (2-3 días)

- [ ] Crear tipos TypeScript (`consulta.ts`)
- [ ] Crear schema Zod (`consultaSchema.ts`)
- [ ] Crear servicio API (`consultaService.ts`)
- [ ] Crear hook `useConsultarIncapacidad()`
- [ ] Crear componente `BusquedaIncapacidad.tsx`
- [ ] Crear componente `DetalleIncapacidad.tsx`
- [ ] Crear componente `TimelineEstados.tsx`
- [ ] Crear componente `DocumentosDescargables.tsx`
- [ ] Crear componente `ContactoSoporte.tsx`
- [ ] Crear página `ConsultarIncapacidad.tsx`
- [ ] Agregar ruta `/consultar` en router
- [ ] Agregar link en homepage
- [ ] Tests BusquedaIncapacidad (10 tests)
- [ ] Tests DetalleIncapacidad (15 tests)
- [ ] Tests TimelineEstados (8 tests)
- [ ] Tests DocumentosDescargables (10 tests)
- [ ] Tests ContactoSoporte (3 tests)
- [ ] Tests página completa (5 tests E2E)
- [ ] Tests de integración con API mock (9 tests)
- [ ] Build exitoso
- [ ] Lighthouse score >90

### Documentación (0.5 día)

- [ ] Crear `docs/10_CONSULTA_INCAPACIDADES.md`
- [ ] Crear `docs/GUIA_USUARIO_CONSULTA.md`
- [ ] Actualizar `README.md` principal
- [ ] Actualizar `frontend/portal-externo/README.md`
- [ ] Crear `frontend/portal-externo/CONSULTA_COMPLETADO.md`
- [ ] Actualizar `ESTADO_PROYECTO.md`
- [ ] Screenshots de la funcionalidad

### Testing Final (0.5 día)

- [ ] Pruebas manuales de flujos completos
- [ ] Verificar responsive en mobile/tablet/desktop
- [ ] Verificar accesibilidad (a11y)
- [ ] Verificar performance (Lighthouse)
- [ ] Verificar que build funciona
- [ ] Pruebas de error handling
- [ ] Pruebas con datos reales

---

## 📊 Métricas de Éxito

### Backend
- ✅ 13 tests pasando (100%)
- ✅ Response time <100ms
- ✅ Rate limiting funcionando
- ✅ Datos sanitizados correctamente

### Frontend
- ✅ 60+ tests pasando (100%)
- ✅ Cobertura >70%
- ✅ Build exitoso
- ✅ 0 errores TypeScript
- ✅ Lighthouse score >90
- ✅ Responsive en todos los dispositivos

### Funcional
- ✅ Búsqueda por número funcional
- ✅ Búsqueda por documento funcional
- ✅ Timeline visual completo
- ✅ Descarga de documentos funcional
- ✅ Error handling robusto

---

## 🚀 Deployment

Una vez completado:

```bash
# Build producción
cd frontend/portal-externo
npm run build

# Verificar build
npm run preview

# Deploy a Vercel/Netlify
# Configurar variable: VITE_API_URL=https://api.produccion.com/api/v1
```

---

## 📞 Soporte

**Desarrollador**: Equipo Incapacidades  
**Fecha**: 17 de enero de 2026  
**Versión**: 1.0.0  
**Estimación**: 3-4 días

---

**Próximo paso**: Comenzar implementación backend (endpoint de consulta)
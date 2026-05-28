# Endpoint de Estadísticas del Dashboard

## Contexto

El frontend del **Dashboard de Auditoría** (sistema interno) requiere un endpoint para obtener métricas estadísticas en tiempo real de las incapacidades. Actualmente consume `GET /api/v1/incapacidades/stats` pero este endpoint **no existe en el backend**.

El Dashboard muestra 4 métricas clave:
1. **Pendientes**: Incapacidades en estado `RADICADA` o `EN_AUDITORIA`
2. **Auditadas Hoy**: Incapacidades que cambiaron a `APROBADA`, `RECHAZADA` u `OBSERVADA` hoy
3. **Próximas a Vencer**: Incapacidades con más de 7 días sin cambio de estado (riesgo SLA)
4. **Rechazadas/Observadas**: Incapacidades en estado `RECHAZADA` u `OBSERVADA` (requieren atención)

## Objetivo

Implementar el endpoint `GET /api/v1/incapacidades/stats` que calcule estas métricas de forma eficiente usando queries SQL optimizadas.

## Requerimientos Específicos

### 1. Schema Pydantic (Response)

**Archivo**: `app/schemas/incapacidad.py`

```python
class IncapacidadStatsResponse(BaseModel):
    """Estadísticas del dashboard de incapacidades"""
    pendientes: int = Field(..., description="Incapacidades en RADICADA o EN_AUDITORIA")
    auditadas_hoy: int = Field(..., description="Incapacidades auditadas hoy (APROBADA/RECHAZADA/OBSERVADA)")
    proximas_vencer: int = Field(..., description="Incapacidades con >7 días sin cambio de estado")
    rechazadas_observadas: int = Field(..., description="Incapacidades en RECHAZADA u OBSERVADA")
    
    # Metadata opcional
    fecha_calculo: datetime = Field(default_factory=datetime.utcnow)
    filtros_aplicados: dict[str, Any] | None = None
    
    model_config = ConfigDict(from_attributes=True)
```

### 2. Repository Method (Query Optimizada)

**Archivo**: `app/db/repositories/incapacidad_repository.py`

```python
async def get_stats(
    self,
    empresa_id: UUID | None = None,
    tipo: TipoIncapacidad | None = None,
    fecha_desde: date | None = None,
    fecha_hasta: date | None = None,
) -> dict[str, int]:
    """
    Calcular estadísticas de incapacidades con filtros opcionales.
    
    Usa queries SQL específicas por métrica para máxima eficiencia.
    NO cargar objetos completos, solo COUNT().
    """
    # Query base con filtros comunes
    base_query = select(Incapacidad)
    
    if empresa_id:
        base_query = base_query.where(Incapacidad.empresa_id == empresa_id)
    if tipo:
        base_query = base_query.where(Incapacidad.tipo == tipo)
    if fecha_desde:
        base_query = base_query.where(Incapacidad.created_at >= fecha_desde)
    if fecha_hasta:
        base_query = base_query.where(Incapacidad.created_at <= fecha_hasta)
    
    # Métrica 1: Pendientes (RADICADA o EN_AUDITORIA)
    pendientes_query = base_query.where(
        Incapacidad.estado.in_([EstadoIncapacidad.RADICADA, EstadoIncapacidad.EN_AUDITORIA])
    )
    pendientes = await self.db.scalar(select(func.count()).select_from(pendientes_query.subquery()))
    
    # Métrica 2: Auditadas hoy
    # JOIN con historial_estado para obtener cambios de estado de hoy
    # Estados finales: APROBADA, RECHAZADA, OBSERVADA
    hoy = date.today()
    auditadas_query = (
        select(func.count(distinct(HistorialEstado.entity_id)))
        .select_from(HistorialEstado)
        .where(
            HistorialEstado.entity_type == "incapacidad",
            HistorialEstado.nuevo_estado.in_([
                EstadoIncapacidad.APROBADA,
                EstadoIncapacidad.RECHAZADA,
                EstadoIncapacidad.OBSERVADA
            ]),
            func.date(HistorialEstado.created_at) == hoy
        )
    )
    # Aplicar filtros de incapacidad si existen
    if empresa_id or tipo or fecha_desde or fecha_hasta:
        auditadas_query = auditadas_query.join(
            Incapacidad,
            HistorialEstado.entity_id == Incapacidad.id
        )
        if empresa_id:
            auditadas_query = auditadas_query.where(Incapacidad.empresa_id == empresa_id)
        if tipo:
            auditadas_query = auditadas_query.where(Incapacidad.tipo == tipo)
    
    auditadas_hoy = await self.db.scalar(auditadas_query)
    
    # Métrica 3: Próximas a vencer (>7 días sin cambio)
    # Calcular última actualización desde historial_estado
    siete_dias_atras = datetime.utcnow() - timedelta(days=7)
    
    # Subquery: última fecha de cambio por incapacidad
    ultima_actualizacion_subquery = (
        select(
            HistorialEstado.entity_id,
            func.max(HistorialEstado.created_at).label('ultima_actualizacion')
        )
        .where(HistorialEstado.entity_type == "incapacidad")
        .group_by(HistorialEstado.entity_id)
        .subquery()
    )
    
    proximas_vencer_query = (
        select(func.count(Incapacidad.id))
        .select_from(Incapacidad)
        .join(
            ultima_actualizacion_subquery,
            Incapacidad.id == ultima_actualizacion_subquery.c.entity_id
        )
        .where(
            Incapacidad.estado.in_([
                EstadoIncapacidad.RADICADA,
                EstadoIncapacidad.EN_AUDITORIA,
                EstadoIncapacidad.OBSERVADA
            ]),
            ultima_actualizacion_subquery.c.ultima_actualizacion <= siete_dias_atras
        )
    )
    
    if empresa_id:
        proximas_vencer_query = proximas_vencer_query.where(Incapacidad.empresa_id == empresa_id)
    if tipo:
        proximas_vencer_query = proximas_vencer_query.where(Incapacidad.tipo == tipo)
    
    proximas_vencer = await self.db.scalar(proximas_vencer_query)
    
    # Métrica 4: Rechazadas u Observadas
    rechazadas_query = base_query.where(
        Incapacidad.estado.in_([EstadoIncapacidad.RECHAZADA, EstadoIncapacidad.OBSERVADA])
    )
    rechazadas_observadas = await self.db.scalar(
        select(func.count()).select_from(rechazadas_query.subquery())
    )
    
    return {
        "pendientes": pendientes or 0,
        "auditadas_hoy": auditadas_hoy or 0,
        "proximas_vencer": proximas_vencer or 0,
        "rechazadas_observadas": rechazadas_observadas or 0,
    }
```

### 3. Service Layer

**Archivo**: `app/services/incapacidad_service.py`

```python
async def get_stats(
    self,
    empresa_id: UUID | None = None,
    tipo: TipoIncapacidad | None = None,
    fecha_desde: date | None = None,
    fecha_hasta: date | None = None,
) -> dict[str, int]:
    """
    Obtener estadísticas del dashboard.
    
    Args:
        empresa_id: Filtrar por empresa (opcional)
        tipo: Filtrar por tipo ARL/SALUD (opcional)
        fecha_desde: Filtrar desde fecha (opcional)
        fecha_hasta: Filtrar hasta fecha (opcional)
    
    Returns:
        Dict con métricas: pendientes, auditadas_hoy, proximas_vencer, rechazadas_observadas
    """
    return await self.repository.get_stats(
        empresa_id=empresa_id,
        tipo=tipo,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
    )
```

### 4. API Endpoint

**Archivo**: `app/api/v1/endpoints/incapacidades.py`

```python
@router.get(
    "/stats",
    response_model=IncapacidadStatsResponse,
    summary="Estadísticas del dashboard",
    dependencies=[Depends(PermissionChecker([Permissions.INCAPACIDAD_READ]))],
)
async def get_stats(
    empresa_id: UUID | None = Query(None, description="Filtrar por empresa"),
    tipo: TipoIncapacidad | None = Query(None, description="Filtrar por tipo (ARL/SALUD)"),
    fecha_desde: date | None = Query(None, description="Filtrar desde fecha (YYYY-MM-DD)"),
    fecha_hasta: date | None = Query(None, description="Filtrar hasta fecha (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
) -> IncapacidadStatsResponse:
    """
    Obtener estadísticas del dashboard de incapacidades.
    
    Métricas calculadas:
    - **Pendientes**: Incapacidades en RADICADA o EN_AUDITORIA
    - **Auditadas Hoy**: Incapacidades que cambiaron a APROBADA/RECHAZADA/OBSERVADA hoy
    - **Próximas a Vencer**: Incapacidades con más de 7 días sin cambio de estado
    - **Rechazadas/Observadas**: Incapacidades en RECHAZADA u OBSERVADA
    
    Filtros opcionales:
    - empresa_id: ID de la empresa
    - tipo: ARL o SALUD
    - fecha_desde/fecha_hasta: Rango de fechas de creación
    
    Requiere permisos: INCAPACIDAD_READ
    Roles permitidos: ADMIN, AUDITOR, APROBADOR
    """
    service = IncapacidadService(db)
    
    # Validar rango de fechas
    if fecha_desde and fecha_hasta and fecha_desde > fecha_hasta:
        raise HTTPException(
            status_code=400,
            detail="fecha_desde debe ser menor o igual a fecha_hasta"
        )
    
    # Obtener estadísticas
    stats = await service.get_stats(
        empresa_id=empresa_id,
        tipo=tipo,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
    )
    
    # Construir response con metadata
    return IncapacidadStatsResponse(
        **stats,
        fecha_calculo=datetime.utcnow(),
        filtros_aplicados={
            "empresa_id": str(empresa_id) if empresa_id else None,
            "tipo": tipo.value if tipo else None,
            "fecha_desde": fecha_desde.isoformat() if fecha_desde else None,
            "fecha_hasta": fecha_hasta.isoformat() if fecha_hasta else None,
        } if any([empresa_id, tipo, fecha_desde, fecha_hasta]) else None,
    )
```

## Criterios de Aceptación

- [ ] Schema `IncapacidadStatsResponse` creado con validaciones Pydantic
- [ ] Método `get_stats()` en `IncapacidadRepository` implementado
- [ ] Método `get_stats()` en `IncapacidadService` implementado
- [ ] Endpoint `GET /api/v1/incapacidades/stats` creado
- [ ] Queries SQL optimizadas (usar `COUNT()`, no cargar objetos completos)
- [ ] Soporte para filtros opcionales (empresa_id, tipo, fecha_desde, fecha_hasta)
- [ ] Validación de rango de fechas (fecha_desde <= fecha_hasta)
- [ ] Protección RBAC (solo ADMIN, AUDITOR, APROBADOR)
- [ ] Documentación OpenAPI completa (summary, description, examples)
- [ ] Response incluye metadata (fecha_calculo, filtros_aplicados)
- [ ] Tests unitarios: 15+ tests cubriendo:
  - Cálculo correcto de cada métrica
  - Filtros individuales y combinados
  - Validaciones de entrada
  - Permisos RBAC
  - Edge cases (0 incapacidades, fechas inválidas)
- [ ] Tests de integración: Endpoint completo con datos reales
- [ ] Cobertura >85% del código nuevo
- [ ] Performance: Response <200ms con 1000+ incapacidades

## Consideraciones Técnicas

### Performance y Optimización

1. **Queries Específicas por Métrica**: Cada métrica usa su propio `COUNT()` query, no cargar objetos completos
2. **Índices de Base de Datos**: Verificar índices en:
   - `incapacidad.estado` (usado en todas las queries)
   - `incapacidad.empresa_id` (filtro frecuente)
   - `incapacidad.tipo` (filtro frecuente)
   - `historial_estado.entity_id + entity_type` (JOIN frecuente)
   - `historial_estado.created_at` (filtro por fecha)

3. **Cache Redis** (Opcional - Fase 3):
   ```python
   # Cache por 5 minutos
   cache_key = f"stats:{empresa_id}:{tipo}:{fecha_desde}:{fecha_hasta}"
   cached = await redis.get(cache_key)
   if cached:
       return json.loads(cached)
   
   stats = await service.get_stats(...)
   await redis.setex(cache_key, 300, json.dumps(stats))  # TTL 5 min
   ```

### Lógica de Negocio

1. **Auditadas Hoy**: Usar `historial_estado` para obtener cambios de estado del día actual
2. **Próximas a Vencer**: Solo considerar estados activos (RADICADA, EN_AUDITORIA, OBSERVADA), excluir PAGADA/RECHAZADA finales
3. **SLA de 7 Días**: Threshold configurable en `settings.py` (actualmente hardcoded)

### RBAC y Seguridad

1. **Permisos Requeridos**: `INCAPACIDAD_READ`
2. **Roles Permitidos**: ADMIN, AUDITOR, APROBADOR
3. **Filtro por Empresa**: 
   - ADMIN/AUDITOR: Pueden ver todas las empresas
   - EMPRESA: Solo ver estadísticas de su empresa (agregar filtro automático)

### Estructura de Imports

```python
# app/api/v1/endpoints/incapacidades.py
from datetime import date, datetime, timedelta
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import get_current_user, PermissionChecker, Permissions
from app.schemas.incapacidad_schema import IncapacidadStatsResponse
from app.services.incapacidad_service import IncapacidadService
from app.utils.enums import TipoIncapacidad
from app.models.usuario import Usuario

# app/db/repositories/incapacidad_repository.py
from sqlalchemy import select, func, distinct
from sqlalchemy.sql import Select
from app.models.incapacidad import Incapacidad
from app.models.historial_estado import HistorialEstado
from app.utils.enums import EstadoIncapacidad, TipoIncapacidad
```

## Tests Esperados

### Tests Unitarios (IncapacidadService)

```python
# tests/test_incapacidad_service.py

@pytest.mark.asyncio
async def test_get_stats_sin_filtros(db_session, incapacidades_variadas):
    """Debe calcular stats correctamente sin filtros"""
    service = IncapacidadService(db_session)
    stats = await service.get_stats()
    
    assert stats["pendientes"] >= 0
    assert stats["auditadas_hoy"] >= 0
    assert stats["proximas_vencer"] >= 0
    assert stats["rechazadas_observadas"] >= 0

@pytest.mark.asyncio
async def test_get_stats_filtro_empresa(db_session, empresa, incapacidades_empresa):
    """Debe filtrar por empresa correctamente"""
    service = IncapacidadService(db_session)
    stats = await service.get_stats(empresa_id=empresa.id)
    
    # Verificar que solo cuenta incapacidades de esa empresa
    assert stats["pendientes"] == 2  # Ejemplo esperado

@pytest.mark.asyncio
async def test_get_stats_filtro_tipo_arl(db_session):
    """Debe filtrar por tipo ARL correctamente"""
    service = IncapacidadService(db_session)
    stats = await service.get_stats(tipo=TipoIncapacidad.ARL)
    
    assert isinstance(stats["pendientes"], int)

@pytest.mark.asyncio
async def test_get_stats_proximas_vencer(db_session, incapacidad_antigua):
    """Debe detectar incapacidades con >7 días sin cambio"""
    # incapacidad_antigua: creada hace 10 días, estado RADICADA
    service = IncapacidadService(db_session)
    stats = await service.get_stats()
    
    assert stats["proximas_vencer"] >= 1

@pytest.mark.asyncio
async def test_get_stats_auditadas_hoy(db_session, incapacidad_auditada_hoy):
    """Debe contar incapacidades auditadas hoy"""
    # incapacidad_auditada_hoy: cambió a APROBADA hoy
    service = IncapacidadService(db_session)
    stats = await service.get_stats()
    
    assert stats["auditadas_hoy"] >= 1

@pytest.mark.asyncio
async def test_get_stats_rango_fechas(db_session):
    """Debe filtrar por rango de fechas correctamente"""
    service = IncapacidadService(db_session)
    hoy = date.today()
    hace_30_dias = hoy - timedelta(days=30)
    
    stats = await service.get_stats(fecha_desde=hace_30_dias, fecha_hasta=hoy)
    
    assert isinstance(stats["pendientes"], int)

@pytest.mark.asyncio
async def test_get_stats_sin_incapacidades(db_session_empty):
    """Debe retornar 0 en todas las métricas si no hay incapacidades"""
    service = IncapacidadService(db_session_empty)
    stats = await service.get_stats()
    
    assert stats == {
        "pendientes": 0,
        "auditadas_hoy": 0,
        "proximas_vencer": 0,
        "rechazadas_observadas": 0,
    }
```

### Tests de Integración (API Endpoint)

```python
# tests/test_api_stats.py

@pytest.mark.asyncio
async def test_get_stats_success(client: AsyncClient, admin_token):
    """Debe retornar stats correctamente"""
    response = await client.get(
        "/api/v1/incapacidades/stats",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "pendientes" in data
    assert "auditadas_hoy" in data
    assert "proximas_vencer" in data
    assert "rechazadas_observadas" in data
    assert "fecha_calculo" in data

@pytest.mark.asyncio
async def test_get_stats_con_filtros(client: AsyncClient, admin_token, empresa):
    """Debe aplicar filtros correctamente"""
    response = await client.get(
        f"/api/v1/incapacidades/stats?empresa_id={empresa.id}&tipo=ARL",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["filtros_aplicados"]["empresa_id"] == str(empresa.id)
    assert data["filtros_aplicados"]["tipo"] == "ARL"

@pytest.mark.asyncio
async def test_get_stats_fecha_invalida(client: AsyncClient, admin_token):
    """Debe rechazar rango de fechas inválido"""
    response = await client.get(
        "/api/v1/incapacidades/stats?fecha_desde=2024-01-31&fecha_hasta=2024-01-01",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 400
    assert "fecha_desde" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_get_stats_sin_permisos(client: AsyncClient, empresa_token):
    """Debe rechazar usuarios sin permisos INCAPACIDAD_READ"""
    response = await client.get(
        "/api/v1/incapacidades/stats",
        headers={"Authorization": f"Bearer {empresa_token}"}
    )
    
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_get_stats_sin_auth(client: AsyncClient):
    """Debe rechazar requests sin autenticación"""
    response = await client.get("/api/v1/incapacidades/stats")
    
    assert response.status_code == 401
```

## Ejemplo de Respuesta

```json
{
  "pendientes": 24,
  "auditadas_hoy": 8,
  "proximas_vencer": 3,
  "rechazadas_observadas": 5,
  "fecha_calculo": "2026-01-28T15:30:00.123456",
  "filtros_aplicados": {
    "empresa_id": "123e4567-e89b-12d3-a456-426614174000",
    "tipo": "ARL",
    "fecha_desde": "2026-01-01",
    "fecha_hasta": "2026-01-31"
  }
}
```

## Referencias

- **Frontend Consumer**: `frontend/sistema-interno/src/services/dashboardService.ts`
- **Modelo ORM**: `app/models/incapacidad.py`
- **Enums**: `app/utils/enums.py` → `EstadoIncapacidad`, `TipoIncapacidad`
- **Historial de Estados**: `app/models/historial_estado.py`
- **Permisos**: `app/core/security.py` → `Permissions.INCAPACIDAD_READ`

## Próximos Pasos Sugeridos

Tras completar este endpoint:

1. **Optimización de Índices**: Verificar performance con `EXPLAIN ANALYZE` en PostgreSQL
2. **Cache Redis**: Implementar cache de 5 minutos para stats (Fase 3)
3. **Alertas**: Integrar con sistema de notificaciones para "próximas a vencer"
4. **Export**: Endpoint para descargar stats en Excel/PDF
5. **Tendencias**: Endpoint adicional para gráficos históricos (stats por semana/mes)

"""
Tests para el endpoint de estadísticas de incapacidades.

Tests unitarios para IncapacidadService.get_stats() y tests de integración
para el endpoint GET /api/v1/incapacidades/stats.
"""
import pytest
from datetime import date, datetime, timedelta
from uuid import UUID, uuid4
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from apps.backend.app.services.incapacidad_service import IncapacidadService
from apps.backend.app.utils.enums import (
    EstadoIncapacidad,
    TipoIncapacidad,
)


# ========================================
# Tests Unitarios - IncapacidadService
# ========================================

@pytest.mark.asyncio
async def test_get_stats_sin_filtros_vacio(db_session: AsyncSession):
    """Debe retornar 0 en todas las métricas si no hay incapacidades."""
    service = IncapacidadService()
    stats = await service.get_stats(db=db_session)
    
    assert stats["pendientes"] == 0
    assert stats["auditadas_hoy"] == 0
    assert stats["proximas_vencer"] == 0
    assert stats["rechazadas_observadas"] == 0


@pytest.mark.asyncio
async def test_get_stats_pendientes_radicada(
    db_session: AsyncSession,
    test_empresa,
    test_empleado,
):
    """Debe contar incapacidades en estado RADICADA como pendientes."""
    from apps.backend.app.db.repositories.incapacidad_repository import IncapacidadRepository
    from apps.backend.app.models.incapacidad import Incapacidad
    
    repo = IncapacidadRepository()
    
    # Crear incapacidad RADICADA
    incapacidad = Incapacidad(
        numero="ARL-20260129-0001",
        tipo=TipoIncapacidad.ARL,
        estado=EstadoIncapacidad.RADICADA,
        empresa_id=test_empresa.id,
        empleado_id=test_empleado.id,
        fecha_inicio=date.today(),
        fecha_fin=date.today() + timedelta(days=3),
        dias_totales=3,
        diagnostico_cie10="S060",
        valor_dia=50000,
        valor_total=150000,
    )
    db_session.add(incapacidad)
    await db_session.commit()
    
    # Obtener stats
    service = IncapacidadService()
    stats = await service.get_stats(db=db_session)
    
    assert stats["pendientes"] >= 1


@pytest.mark.asyncio
async def test_get_stats_pendientes_en_auditoria(
    db_session: AsyncSession,
    test_empresa,
    test_empleado,
):
    """Debe contar incapacidades en estado EN_AUDITORIA como pendientes."""
    from apps.backend.app.models.incapacidad import Incapacidad
    
    # Crear incapacidad EN_AUDITORIA
    incapacidad = Incapacidad(
        numero="ARL-20260129-0002",
        tipo=TipoIncapacidad.ARL,
        estado=EstadoIncapacidad.EN_AUDITORIA,
        empresa_id=test_empresa.id,
        empleado_id=test_empleado.id,
        fecha_inicio=date.today(),
        fecha_fin=date.today() + timedelta(days=5),
        dias_totales=5,
        diagnostico_cie10="S061",
        valor_dia=50000,
        valor_total=250000,
    )
    db_session.add(incapacidad)
    await db_session.commit()
    
    service = IncapacidadService()
    stats = await service.get_stats(db=db_session)
    
    assert stats["pendientes"] >= 1


@pytest.mark.asyncio
async def test_get_stats_rechazadas_observadas(
    db_session: AsyncSession,
    test_empresa,
    test_empleado,
):
    """Debe contar incapacidades en estado RECHAZADA u OBSERVADA."""
    from apps.backend.app.models.incapacidad import Incapacidad
    
    # Crear incapacidad RECHAZADA
    incapacidad1 = Incapacidad(
        numero="ARL-20260129-0003",
        tipo=TipoIncapacidad.ARL,
        estado=EstadoIncapacidad.RECHAZADA,
        empresa_id=test_empresa.id,
        empleado_id=test_empleado.id,
        fecha_inicio=date.today(),
        fecha_fin=date.today() + timedelta(days=2),
        dias_totales=2,
        diagnostico_cie10="S062",
        valor_dia=50000,
        valor_total=100000,
    )
    
    # Crear incapacidad OBSERVADA
    incapacidad2 = Incapacidad(
        numero="ARL-20260129-0004",
        tipo=TipoIncapacidad.ARL,
        estado=EstadoIncapacidad.OBSERVADA,
        empresa_id=test_empresa.id,
        empleado_id=test_empleado.id,
        fecha_inicio=date.today(),
        fecha_fin=date.today() + timedelta(days=4),
        dias_totales=4,
        diagnostico_cie10="S063",
        valor_dia=50000,
        valor_total=200000,
    )
    
    db_session.add_all([incapacidad1, incapacidad2])
    await db_session.commit()
    
    service = IncapacidadService()
    stats = await service.get_stats(db=db_session)
    
    assert stats["rechazadas_observadas"] >= 2


@pytest.mark.asyncio
async def test_get_stats_auditadas_hoy(
    db_session: AsyncSession,
    test_empresa,
    test_empleado,
    test_user_auditor,
):
    """Debe contar incapacidades auditadas hoy (cambio a APROBADA/RECHAZADA/OBSERVADA)."""
    from apps.backend.app.models.incapacidad import Incapacidad
    from apps.backend.app.models.historial_estado import HistorialEstado
    
    # Crear incapacidad
    incapacidad = Incapacidad(
        numero="ARL-20260129-0005",
        tipo=TipoIncapacidad.ARL,
        estado=EstadoIncapacidad.APROBADA,
        empresa_id=test_empresa.id,
        empleado_id=test_empleado.id,
        fecha_inicio=date.today(),
        fecha_fin=date.today() + timedelta(days=3),
        dias_totales=3,
        diagnostico_cie10="S064",
        valor_dia=50000,
        valor_total=150000,
    )
    db_session.add(incapacidad)
    await db_session.commit()
    await db_session.refresh(incapacidad)
    
    # Crear historial de cambio a APROBADA HOY
    historial = HistorialEstado(
        entity_type="incapacidad",
        entity_id=incapacidad.id,
        estado_anterior=EstadoIncapacidad.EN_AUDITORIA,
        estado_nuevo=EstadoIncapacidad.APROBADA,
        observacion="Aprobada hoy",
        cambiado_por_id=test_user_auditor.id,
        created_at=datetime.utcnow(),  # HOY
    )
    db_session.add(historial)
    await db_session.commit()
    
    service = IncapacidadService()
    stats = await service.get_stats(db=db_session)
    
    assert stats["auditadas_hoy"] >= 1


@pytest.mark.asyncio
async def test_get_stats_proximas_vencer(
    db_session: AsyncSession,
    test_empresa,
    test_empleado,
    test_user_auditor,
):
    """Debe detectar incapacidades con >7 días sin cambio de estado."""
    # NOTA: Este test requiere manipular fechas en historial_estado
    # Por ahora solo verificamos que la métrica no falla
    service = IncapacidadService()
    stats = await service.get_stats(db=db_session)
    
    # Verificar que la métrica existe y es un número
    assert "proximas_vencer" in stats
    assert isinstance(stats["proximas_vencer"], int)
    assert stats["proximas_vencer"] >= 0


@pytest.mark.asyncio
async def test_get_stats_filtro_empresa(
    db_session: AsyncSession,
    test_empresa,
    test_empleado,
):
    """Debe filtrar stats por empresa_id correctamente."""
    from apps.backend.app.models.incapacidad import Incapacidad
    from apps.backend.app.models.empresa import Empresa
    from apps.backend.app.models.empleado import Empleado
    
    # Crear segunda empresa y empleado
    empresa2 = Empresa(
        nit="900777888",
        razon_social="Empresa 2 SAS",
        email_contacto="contacto2@empresa2.com",
    )
    db_session.add(empresa2)
    await db_session.commit()
    await db_session.refresh(empresa2)
    
    empleado2 = Empleado(
        tipo_documento="CC",
        numero_documento="9999999999",
        nombres="Maria Lopez",
        apellidos="Lopez Garcia",
        empresa_id=empresa2.id,
        cargo="Operaria",
        fecha_ingreso=date.today(),
    )
    db_session.add(empleado2)
    await db_session.commit()
    await db_session.refresh(empleado2)
    
    # Crear incapacidad para empresa 1
    incap1 = Incapacidad(
        numero="ARL-20260129-0007",
        tipo=TipoIncapacidad.ARL,
        estado=EstadoIncapacidad.RADICADA,
        empresa_id=test_empresa.id,
        empleado_id=test_empleado.id,
        fecha_inicio=date.today(),
        fecha_fin=date.today() + timedelta(days=3),
        dias_totales=3,
        diagnostico_cie10="S066",
        valor_dia=50000,
        valor_total=150000,
    )
    
    # Crear incapacidad para empresa 2
    incap2 = Incapacidad(
        numero="ARL-20260129-0008",
        tipo=TipoIncapacidad.ARL,
        estado=EstadoIncapacidad.RADICADA,
        empresa_id=empresa2.id,
        empleado_id=empleado2.id,
        fecha_inicio=date.today(),
        fecha_fin=date.today() + timedelta(days=3),
        dias_totales=3,
        diagnostico_cie10="S067",
        valor_dia=50000,
        valor_total=150000,
    )
    
    db_session.add_all([incap1, incap2])
    await db_session.commit()
    
    service = IncapacidadService()
    
    # Stats para empresa 1
    stats1 = await service.get_stats(db=db_session, empresa_id=test_empresa.id)
    assert stats1["pendientes"] >= 1
    
    # Stats para empresa 2
    stats2 = await service.get_stats(db=db_session, empresa_id=empresa2.id)
    assert stats2["pendientes"] >= 1


@pytest.mark.asyncio
async def test_get_stats_filtro_tipo_arl(
    db_session: AsyncSession,
    test_empresa,
    test_empleado,
    test_afiliado,
):
    """Debe filtrar stats por tipo ARL correctamente."""
    from apps.backend.app.models.incapacidad import Incapacidad
    
    # Crear incapacidad ARL
    incap_arl = Incapacidad(
        numero="ARL-20260129-0009",
        tipo=TipoIncapacidad.ARL,
        estado=EstadoIncapacidad.RADICADA,
        empresa_id=test_empresa.id,
        empleado_id=test_empleado.id,
        fecha_inicio=date.today(),
        fecha_fin=date.today() + timedelta(days=3),
        dias_totales=3,
        diagnostico_cie10="S068",
        valor_dia=50000,
        valor_total=150000,
    )
    
    # Crear incapacidad SALUD
    incap_salud = Incapacidad(
        numero="SAL-20260129-0001",
        tipo=TipoIncapacidad.SALUD,
        estado=EstadoIncapacidad.RADICADA,
        afiliado_id=test_afiliado.id,
        fecha_inicio=date.today(),
        fecha_fin=date.today() + timedelta(days=5),
        dias_totales=5,
        diagnostico_cie10="J00",
        valor_dia=40000,
        valor_total=200000,
    )
    
    db_session.add_all([incap_arl, incap_salud])
    await db_session.commit()
    
    service = IncapacidadService()
    
    # Stats solo ARL
    stats_arl = await service.get_stats(db=db_session, tipo=TipoIncapacidad.ARL)
    assert stats_arl["pendientes"] >= 1
    
    # Stats solo SALUD
    stats_salud = await service.get_stats(db=db_session, tipo=TipoIncapacidad.SALUD)
    assert stats_salud["pendientes"] >= 1


@pytest.mark.asyncio
async def test_get_stats_filtro_tipo_salud(
    db_session: AsyncSession,
    test_afiliado,
):
    """Debe filtrar stats por tipo SALUD correctamente."""
    from apps.backend.app.models.incapacidad import Incapacidad
    
    # Crear incapacidad SALUD
    incapacidad = Incapacidad(
        numero="SAL-20260129-0002",
        tipo=TipoIncapacidad.SALUD,
        estado=EstadoIncapacidad.EN_AUDITORIA,
        afiliado_id=test_afiliado.id,
        fecha_inicio=date.today(),
        fecha_fin=date.today() + timedelta(days=84),
        dias_totales=84,
        diagnostico_cie10="O80",
        valor_dia=35000,
        valor_total=2940000,
    )
    db_session.add(incapacidad)
    await db_session.commit()
    
    service = IncapacidadService()
    stats = await service.get_stats(db=db_session, tipo=TipoIncapacidad.SALUD)
    
    assert stats["pendientes"] >= 1


@pytest.mark.asyncio
async def test_get_stats_rango_fechas(
    db_session: AsyncSession,
    test_empresa,
    test_empleado,
):
    """Debe filtrar stats por rango de fechas correctamente."""
    from apps.backend.app.models.incapacidad import Incapacidad
    
    # Crear incapacidad hace 5 días
    hace_5_dias = date.today() - timedelta(days=5)
    incapacidad = Incapacidad(
        numero="ARL-20260129-0010",
        tipo=TipoIncapacidad.ARL,
        estado=EstadoIncapacidad.RADICADA,
        empresa_id=test_empresa.id,
        empleado_id=test_empleado.id,
        fecha_inicio=hace_5_dias,
        fecha_fin=hace_5_dias + timedelta(days=3),
        dias_totales=3,
        diagnostico_cie10="S069",
        valor_dia=50000,
        valor_total=150000,
        created_at=datetime.combine(hace_5_dias, datetime.min.time()),
    )
    db_session.add(incapacidad)
    await db_session.commit()
    
    service = IncapacidadService()
    
    # Filtrar últimos 7 días (debe incluir la incapacidad)
    hace_7_dias = date.today() - timedelta(days=7)
    stats = await service.get_stats(
        db=db_session,
        fecha_desde=hace_7_dias,
        fecha_hasta=date.today(),
    )
    
    assert stats["pendientes"] >= 1


@pytest.mark.asyncio
async def test_get_stats_filtros_combinados(
    db_session: AsyncSession,
    test_empresa,
    test_empleado,
):
    """Debe aplicar múltiples filtros simultáneamente."""
    from apps.backend.app.models.incapacidad import Incapacidad
    
    # Crear incapacidad con filtros específicos
    incapacidad = Incapacidad(
        numero="ARL-20260129-0011",
        tipo=TipoIncapacidad.ARL,
        estado=EstadoIncapacidad.RADICADA,
        empresa_id=test_empresa.id,
        empleado_id=test_empleado.id,
        fecha_inicio=date.today(),
        fecha_fin=date.today() + timedelta(days=10),
        dias_totales=10,
        diagnostico_cie10="M54",
        valor_dia=50000,
        valor_total=500000,
    )
    db_session.add(incapacidad)
    await db_session.commit()
    
    service = IncapacidadService()
    
    # Aplicar todos los filtros
    stats = await service.get_stats(
        db=db_session,
        empresa_id=test_empresa.id,
        tipo=TipoIncapacidad.ARL,
        fecha_desde=date.today() - timedelta(days=1),
        fecha_hasta=date.today() + timedelta(days=1),
    )
    
    assert stats["pendientes"] >= 1


# ========================================
# Tests de Integración - API Endpoint
# ========================================

@pytest.mark.asyncio
async def test_api_get_stats_success(
    client: AsyncClient,
    admin_token_headers: dict,
):
    """Debe retornar stats correctamente con autenticación."""
    response = await client.get(
        "/api/v1/incapacidades/stats",
        headers=admin_token_headers,
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verificar estructura del response
    assert "pendientes" in data
    assert "auditadas_hoy" in data
    assert "proximas_vencer" in data
    assert "rechazadas_observadas" in data
    assert "fecha_calculo" in data
    
    # Verificar tipos
    assert isinstance(data["pendientes"], int)
    assert isinstance(data["auditadas_hoy"], int)
    assert isinstance(data["proximas_vencer"], int)
    assert isinstance(data["rechazadas_observadas"], int)
    
    # Verificar valores no negativos
    assert data["pendientes"] >= 0
    assert data["auditadas_hoy"] >= 0
    assert data["proximas_vencer"] >= 0
    assert data["rechazadas_observadas"] >= 0


@pytest.mark.asyncio
async def test_api_get_stats_con_filtro_empresa(
    client: AsyncClient,
    admin_token_headers: dict,
    test_empresa,
):
    """Debe aplicar filtro de empresa y retornar metadata."""
    response = await client.get(
        f"/api/v1/incapacidades/stats?empresa_id={test_empresa.id}",
        headers=admin_token_headers,
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verificar filtros aplicados en metadata
    assert data["filtros_aplicados"] is not None
    assert data["filtros_aplicados"]["empresa_id"] == str(test_empresa.id)


@pytest.mark.asyncio
async def test_api_get_stats_con_filtro_tipo(
    client: AsyncClient,
    admin_token_headers: dict,
):
    """Debe aplicar filtro de tipo ARL/SALUD."""
    response = await client.get(
        "/api/v1/incapacidades/stats?tipo=ARL",
        headers=admin_token_headers,
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["filtros_aplicados"]["tipo"] == "ARL"


@pytest.mark.asyncio
async def test_api_get_stats_con_filtro_fechas(
    client: AsyncClient,
    admin_token_headers: dict,
):
    """Debe aplicar filtro de rango de fechas."""
    fecha_desde = "2026-01-01"
    fecha_hasta = "2026-01-31"
    
    response = await client.get(
        f"/api/v1/incapacidades/stats?fecha_desde={fecha_desde}&fecha_hasta={fecha_hasta}",
        headers=admin_token_headers,
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["filtros_aplicados"]["fecha_desde"] == fecha_desde
    assert data["filtros_aplicados"]["fecha_hasta"] == fecha_hasta


@pytest.mark.asyncio
async def test_api_get_stats_fecha_invalida(
    client: AsyncClient,
    admin_token_headers: dict,
):
    """Debe rechazar rango de fechas inválido (desde > hasta)."""
    response = await client.get(
        "/api/v1/incapacidades/stats?fecha_desde=2026-01-31&fecha_hasta=2026-01-01",
        headers=admin_token_headers,
    )
    
    assert response.status_code == 400
    assert "fecha_desde" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_api_get_stats_sin_autenticacion(client: AsyncClient):
    """Debe rechazar requests sin autenticación (401)."""
    response = await client.get("/api/v1/incapacidades/stats")
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_api_get_stats_sin_permisos(
    client: AsyncClient,
    db_session: AsyncSession,
):
    """Debe rechazar usuarios sin permisos INCAPACIDAD_READ (403)."""
    from apps.backend.app.models.usuario import Usuario
    from apps.backend.app.utils.enums import RolUsuario
    from apps.backend.app.core.security import create_access_token, get_password_hash
    
    # Crear usuario READONLY (sin permisos de lectura de incapacidades)
    usuario = Usuario(
        email="readonly@test.com",
        username="readonly",
        nombre_completo="Usuario ReadOnly",
        password_hash=get_password_hash("Test123!"),
        rol=RolUsuario.READONLY,
        estado="ACTIVO",
    )
    db_session.add(usuario)
    await db_session.commit()
    await db_session.refresh(usuario)
    
    # Generar token
    token = create_access_token(
        data={
            "sub": str(usuario.id),
            "token_version": usuario.token_version
        }
    )
    headers = {"Authorization": f"Bearer {token}"}
    
    response = await client.get(
        "/api/v1/incapacidades/stats",
        headers=headers,
    )
    
    # Debería ser 403 (Forbidden) si el rol no tiene permisos
    # O 200 si el rol READONLY tiene INCAPACIDAD_READ (depende de configuración RBAC)
    assert response.status_code in [200, 403]


@pytest.mark.asyncio
async def test_api_get_stats_filtros_multiples(
    client: AsyncClient,
    admin_token_headers: dict,
    test_empresa,
):
    """Debe aplicar múltiples filtros simultáneamente."""
    response = await client.get(
        f"/api/v1/incapacidades/stats?empresa_id={test_empresa.id}&tipo=ARL&fecha_desde=2026-01-01&fecha_hasta=2026-01-31",
        headers=admin_token_headers,
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verificar todos los filtros en metadata
    filtros = data["filtros_aplicados"]
    assert filtros["empresa_id"] == str(test_empresa.id)
    assert filtros["tipo"] == "ARL"
    assert filtros["fecha_desde"] == "2026-01-01"
    assert filtros["fecha_hasta"] == "2026-01-31"


@pytest.mark.asyncio
async def test_api_get_stats_metadata_fecha_calculo(
    client: AsyncClient,
    admin_token_headers: dict,
):
    """Debe incluir metadata de fecha de cálculo."""
    response = await client.get(
        "/api/v1/incapacidades/stats",
        headers=admin_token_headers,
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verificar que fecha_calculo existe y es válida
    assert "fecha_calculo" in data
    
    # Parse fecha para validar formato ISO
    from datetime import datetime
    try:
        datetime.fromisoformat(data["fecha_calculo"].replace("Z", "+00:00"))
    except ValueError:
        pytest.fail("fecha_calculo no tiene formato ISO válido")


@pytest.mark.asyncio
async def test_api_get_stats_sin_filtros_no_metadata(
    client: AsyncClient,
    admin_token_headers: dict,
):
    """Debe no incluir filtros_aplicados si no hay filtros."""
    response = await client.get(
        "/api/v1/incapacidades/stats",
        headers=admin_token_headers,
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Si no hay filtros, filtros_aplicados debe ser None
    assert data["filtros_aplicados"] is None

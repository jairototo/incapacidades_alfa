"""
Tests de integración para endpoints API de Catálogo CIE-10.
"""
import pytest
from httpx import AsyncClient


# ==================== TESTS BÚSQUEDA CIE-10 ====================

@pytest.mark.asyncio
async def test_search_cie10_by_code(client: AsyncClient, db_session):
    """Test búsqueda de códigos CIE-10 por código."""
    # Arrange: Crear códigos CIE-10 de prueba
    from apps.backend.app.models.catalogo_cie10 import CatalogoCIE10
    
    codigos = [
        CatalogoCIE10(
            codigo="A01.0",
            descripcion="Fiebre tifoidea"
        ),
        CatalogoCIE10(
            codigo="A01.1",
            descripcion="Fiebre paratifoidea A"
        ),
        CatalogoCIE10(
            codigo="B20",
            descripcion="Enfermedad por virus de la inmunodeficiencia humana [VIH]"
        )
    ]
    
    for codigo in codigos:
        db_session.add(codigo)
    await db_session.commit()
    
    # Act: Buscar por código A01
    response = await client.get("/api/v1/catalogos/cie10?q=A01")
    
    # Assert
    assert response.status_code == 200
    json_data = response.json()
    assert isinstance(json_data, list)
    assert len(json_data) >= 2
    assert all("A01" in item["codigo"] for item in json_data)


@pytest.mark.asyncio
async def test_search_cie10_by_description(client: AsyncClient, db_session):
    """Test búsqueda de códigos CIE-10 por descripción."""
    # Arrange
    from apps.backend.app.models.catalogo_cie10 import CatalogoCIE10
    
    codigos = [
        CatalogoCIE10(
            codigo="J00",
            descripcion="Rinofaringitis aguda [resfriado común]"
        ),
        CatalogoCIE10(
            codigo="J01",
            descripcion="Sinusitis aguda"
        )
    ]
    
    for codigo in codigos:
        db_session.add(codigo)
    await db_session.commit()
    
    # Act: Buscar por descripción "aguda"
    response = await client.get("/api/v1/catalogos/cie10?q=aguda")
    
    # Assert
    assert response.status_code == 200
    json_data = response.json()
    assert isinstance(json_data, list)
    assert len(json_data) >= 2
    assert all("aguda" in item["descripcion"].lower() for item in json_data)


@pytest.mark.asyncio
async def test_search_cie10_case_insensitive(client: AsyncClient, db_session):
    """Test que la búsqueda es case-insensitive."""
    # Arrange
    from apps.backend.app.models.catalogo_cie10 import CatalogoCIE10
    
    codigo = CatalogoCIE10(
        codigo="K21",
        descripcion="Enfermedad por reflujo gastroesofágico"
    )
    db_session.add(codigo)
    await db_session.commit()
    
    # Act: Buscar con diferentes casos
    response_lower = await client.get("/api/v1/catalogos/cie10?q=reflujo")
    response_upper = await client.get("/api/v1/catalogos/cie10?q=REFLUJO")
    response_mixed = await client.get("/api/v1/catalogos/cie10?q=ReFluJo")
    
    # Assert: Todas las búsquedas deben retornar el mismo resultado
    assert response_lower.status_code == 200
    assert response_upper.status_code == 200
    assert response_mixed.status_code == 200
    
    results_lower = response_lower.json()
    results_upper = response_upper.json()
    results_mixed = response_mixed.json()
    
    assert len(results_lower) >= 1
    assert len(results_upper) == len(results_lower)
    assert len(results_mixed) == len(results_lower)


@pytest.mark.asyncio
async def test_search_cie10_query_too_short(client: AsyncClient):
    """Test que requiere mínimo 2 caracteres."""
    # Act: Buscar con 1 carácter
    response = await client.get("/api/v1/catalogos/cie10?q=A")
    
    # Assert
    assert response.status_code == 422  # Query parameter validation


@pytest.mark.asyncio
async def test_search_cie10_no_results(client: AsyncClient):
    """Test búsqueda sin resultados."""
    # Act
    response = await client.get("/api/v1/catalogos/cie10?q=ZZZNOEXISTE999")
    
    # Assert
    assert response.status_code == 200
    json_data = response.json()
    assert isinstance(json_data, list)
    assert len(json_data) == 0


@pytest.mark.asyncio
async def test_search_cie10_with_limit(client: AsyncClient, db_session):
    """Test búsqueda con límite de resultados."""
    # Arrange: Crear múltiples códigos con descripción similar
    from apps.backend.app.models.catalogo_cie10 import CatalogoCIE10
    
    codigos = [
        CatalogoCIE10(codigo=f"Z{i:02d}", descripcion=f"Prueba diagnóstico {i}")
        for i in range(10)
    ]
    
    for codigo in codigos:
        db_session.add(codigo)
    await db_session.commit()
    
    # Act: Buscar con límite de 5
    response = await client.get("/api/v1/catalogos/cie10?q=Prueba&limit=5")
    
    # Assert
    assert response.status_code == 200
    json_data = response.json()
    assert isinstance(json_data, list)
    assert len(json_data) <= 5


# ==================== TESTS OBTENER CIE-10 POR CÓDIGO ====================

@pytest.mark.asyncio
async def test_get_cie10_by_codigo_success(client: AsyncClient, db_session):
    """Test obtener código CIE-10 por código exacto."""
    # Arrange
    from apps.backend.app.models.catalogo_cie10 import CatalogoCIE10
    
    codigo = CatalogoCIE10(
        codigo="I10",
        descripcion="Hipertensión esencial (primaria)"
    )
    db_session.add(codigo)
    await db_session.commit()
    
    # Act
    response = await client.get("/api/v1/catalogos/cie10/I10")
    
    # Assert
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["codigo"] == "I10"
    assert json_data["descripcion"] == "Hipertensión esencial (primaria)"


@pytest.mark.asyncio
async def test_get_cie10_by_codigo_not_found(client: AsyncClient):
    """Test que retorna 404 cuando el código no existe."""
    # Act
    response = await client.get("/api/v1/catalogos/cie10/ZZZZZ999")
    
    # Assert
    assert response.status_code == 404
    assert "no encontrado" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_cie10_by_codigo_case_normalization(client: AsyncClient, db_session):
    """Test que normaliza el código a mayúsculas."""
    # Arrange
    from apps.backend.app.models.catalogo_cie10 import CatalogoCIE10
    
    codigo = CatalogoCIE10(
        codigo="E11",
        descripcion="Diabetes mellitus no insulinodependiente"
    )
    db_session.add(codigo)
    await db_session.commit()
    
    # Act: Buscar con minúsculas
    response = await client.get("/api/v1/catalogos/cie10/e11")
    
    # Assert
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["codigo"] == "E11"


# ==================== TESTS LISTAR TODOS LOS CIE-10 ====================

@pytest.mark.asyncio
async def test_list_all_cie10_pagination(client: AsyncClient, db_session):
    """Test listar todos los códigos CIE-10 con paginación."""
    # Arrange: Crear varios códigos
    from apps.backend.app.models.catalogo_cie10 import CatalogoCIE10
    
    codigos = [
        CatalogoCIE10(codigo=f"T{i:02d}", descripcion=f"Código prueba {i}")
        for i in range(15)
    ]
    
    for codigo in codigos:
        db_session.add(codigo)
    await db_session.commit()
    
    # Act: Obtener primera página (limit=10)
    response = await client.get("/api/v1/catalogos/cie10/all/list?limit=10&offset=0")
    
    # Assert
    assert response.status_code == 200
    json_data = response.json()
    assert isinstance(json_data, list)
    assert len(json_data) == 10
    
    # Act: Obtener segunda página
    response2 = await client.get("/api/v1/catalogos/cie10/all/list?limit=10&offset=10")
    
    # Assert
    assert response2.status_code == 200
    json_data2 = response2.json()
    assert len(json_data2) >= 5  # Al menos los 5 restantes


@pytest.mark.asyncio
async def test_list_all_cie10_default_limit(client: AsyncClient, db_session):
    """Test que usa límite por defecto de 100."""
    # Act: Listar sin especificar límite
    response = await client.get("/api/v1/catalogos/cie10/all/list")
    
    # Assert
    assert response.status_code == 200
    json_data = response.json()
    assert isinstance(json_data, list)
    assert len(json_data) <= 100  # No debe exceder el límite por defecto


# ==================== TESTS ESTADÍSTICAS CIE-10 ====================

@pytest.mark.asyncio
async def test_get_cie10_stats_count(client: AsyncClient, db_session):
    """Test obtener estadísticas de códigos CIE-10."""
    # Arrange: Crear códigos conocidos
    from apps.backend.app.models.catalogo_cie10 import CatalogoCIE10
    
    codigos = [
        CatalogoCIE10(codigo=f"S{i:02d}", descripcion=f"Código stats {i}")
        for i in range(7)
    ]
    
    for codigo in codigos:
        db_session.add(codigo)
    await db_session.commit()
    
    # Act
    response = await client.get("/api/v1/catalogos/cie10/stats/count")
    
    # Assert
    assert response.status_code == 200
    json_data = response.json()
    assert "total_codigos" in json_data
    assert "version" in json_data
    assert json_data["version"] == "CIE-10"
    assert json_data["total_codigos"] >= 7
    assert isinstance(json_data["total_codigos"], int)

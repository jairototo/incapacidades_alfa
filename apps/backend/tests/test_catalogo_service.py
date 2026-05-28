"""
Tests unitarios para CatalogoService.
"""
import pytest
import pytest_asyncio
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.catalogo_service import catalogo_service
from app.models.catalogo_cie10 import CatalogoCIE10
from app.core.exceptions import NotFoundException, ValidationException


@pytest_asyncio.fixture
async def sample_cie10_codes(db_session: AsyncSession) -> List[CatalogoCIE10]:
    """Fixture que crea varios códigos CIE-10 de prueba."""
    codes_data = [
        ("A00.0", "Cólera debido a Vibrio cholerae 01, biotipo cholerae"),
        ("A00.1", "Cólera debido a Vibrio cholerae 01, biotipo El Tor"),
        ("J00", "Rinofaringitis aguda (resfriado común)"),
        ("J06.9", "Infección aguda de las vías respiratorias superiores, no especificada"),
        ("M545", "Dorsalgia"),
        ("M5456", "Dolor de espalda baja"),
        ("I10", "Hipertensión esencial (primaria)"),
        ("E11.9", "Diabetes mellitus no insulinodependiente, sin mención de complicación"),
        ("K30", "Dispepsia"),
    ]
    
    codes = []
    for codigo, descripcion in codes_data:
        code = await catalogo_service.create_cie10(db_session, codigo, descripcion)
        codes.append(code)
    
    return codes


# ==================== TESTS BÚSQUEDA ====================

@pytest.mark.asyncio
async def test_search_cie10_by_code_prefix(
    db_session: AsyncSession,
    sample_cie10_codes: List[CatalogoCIE10]
):
    """Test búsqueda de códigos CIE-10 por prefijo de código."""
    # Act
    results = await catalogo_service.search_cie10(db_session, "A00")
    
    # Assert
    assert len(results) >= 2
    assert all("A00" in r.codigo for r in results)


@pytest.mark.asyncio
async def test_search_cie10_by_description(
    db_session: AsyncSession,
    sample_cie10_codes: List[CatalogoCIE10]
):
    """Test búsqueda de códigos CIE-10 por descripción."""
    # Act
    results = await catalogo_service.search_cie10(db_session, "cólera")
    
    # Assert
    assert len(results) >= 2
    assert all("cólera" in r.descripcion.lower() for r in results)


@pytest.mark.asyncio
async def test_search_cie10_case_insensitive(
    db_session: AsyncSession,
    sample_cie10_codes: List[CatalogoCIE10]
):
    """Test que la búsqueda es case-insensitive."""
    # Act
    results_lower = await catalogo_service.search_cie10(db_session, "diabetes")
    results_upper = await catalogo_service.search_cie10(db_session, "DIABETES")
    results_mixed = await catalogo_service.search_cie10(db_session, "DiAbEtEs")
    
    # Assert
    assert len(results_lower) >= 1
    assert len(results_lower) == len(results_upper) == len(results_mixed)


@pytest.mark.asyncio
async def test_search_cie10_too_short(db_session: AsyncSession):
    """Test que lanza excepción si el query es muy corto (<2 caracteres)."""
    # Act & Assert
    with pytest.raises(ValidationException) as exc_info:
        await catalogo_service.search_cie10(db_session, "A")
    
    assert "al menos 2 caracteres" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_search_cie10_respects_limit(
    db_session: AsyncSession,
    sample_cie10_codes: List[CatalogoCIE10]
):
    """Test que respeta el límite de resultados."""
    # Act - usar un query válido de 2+ caracteres
    results = await catalogo_service.search_cie10(db_session, "A0", limit=2)
    
    # Assert
    assert len(results) <= 2


@pytest.mark.asyncio
async def test_search_cie10_prioritizes_exact_code_matches(
    db_session: AsyncSession,
    sample_cie10_codes: List[CatalogoCIE10]
):
    """Test que prioriza coincidencias exactas de código."""
    # Act
    results = await catalogo_service.search_cie10(db_session, "M54", limit=10)
    
    # Assert: El código que empieza con M54 debe venir primero
    assert len(results) >= 2
    # Los códigos M545 y M5456 deben estar en los primeros resultados
    first_codes = [r.codigo for r in results[:2]]
    assert any("M54" in code for code in first_codes)


# ==================== TESTS GET BY CODIGO ====================

@pytest.mark.asyncio
async def test_get_cie10_by_codigo_success(
    db_session: AsyncSession,
    sample_cie10_codes: List[CatalogoCIE10]
):
    """Test obtener código CIE-10 por código exacto."""
    # Act
    result = await catalogo_service.get_cie10_by_codigo(db_session, "J00")
    
    # Assert
    assert result is not None
    assert result.codigo == "J00"
    assert "resfriado" in result.descripcion.lower()


@pytest.mark.asyncio
async def test_get_cie10_by_codigo_not_found(db_session: AsyncSession):
    """Test que lanza NotFoundException si el código no existe."""
    # Act & Assert
    with pytest.raises(NotFoundException) as exc_info:
        await catalogo_service.get_cie10_by_codigo(db_session, "Z99.9")
    
    assert "no encontrado" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_get_cie10_by_codigo_case_sensitive(
    db_session: AsyncSession,
    sample_cie10_codes: List[CatalogoCIE10]
):
    """Test que el código se normaliza a mayúsculas."""
    # Act
    result = await catalogo_service.get_cie10_by_codigo(db_session, "j00")
    
    # Assert
    assert result is not None
    assert result.codigo == "J00"


# ==================== TESTS GET ALL ====================

@pytest.mark.asyncio
async def test_get_all_cie10_with_pagination(
    db_session: AsyncSession,
    sample_cie10_codes: List[CatalogoCIE10]
):
    """Test obtener todos los códigos con paginación."""
    # Act
    results_page1 = await catalogo_service.get_all(db_session, limit=5, offset=0)
    results_page2 = await catalogo_service.get_all(db_session, limit=5, offset=5)
    
    # Assert
    assert len(results_page1) <= 5
    assert len(results_page2) <= 5
    
    # No deben repetirse códigos
    codes_page1 = {r.codigo for r in results_page1}
    codes_page2 = {r.codigo for r in results_page2}
    assert codes_page1.isdisjoint(codes_page2)


# ==================== TESTS COUNT ====================

@pytest.mark.asyncio
async def test_count_cie10_codes(
    db_session: AsyncSession,
    sample_cie10_codes: List[CatalogoCIE10]
):
    """Test contar códigos CIE-10."""
    # Act
    count = await catalogo_service.count(db_session)
    
    # Assert
    assert count >= len(sample_cie10_codes)


# ==================== TESTS CREATE ====================

@pytest.mark.asyncio
async def test_create_cie10_success(db_session: AsyncSession):
    """Test crear un nuevo código CIE-10."""
    # Act
    result = await catalogo_service.create_cie10(
        db_session,
        "Z99.9",
        "Código de prueba"
    )
    
    # Assert
    assert result.codigo == "Z99.9"
    assert result.descripcion == "Código de prueba"


@pytest.mark.asyncio
async def test_create_cie10_normalizes_codigo(db_session: AsyncSession):
    """Test que el código se normaliza a mayúsculas."""
    # Act
    result = await catalogo_service.create_cie10(
        db_session,
        "z88.8",
        "Código minúscula"
    )
    
    # Assert
    assert result.codigo == "Z88.8"


# ==================== TESTS EDGE CASES ====================

@pytest.mark.asyncio
async def test_search_cie10_empty_results(db_session: AsyncSession):
    """Test que retorna lista vacía si no hay coincidencias."""
    # Act
    results = await catalogo_service.search_cie10(db_session, "ZZZZZ")
    
    # Assert
    assert len(results) == 0


@pytest.mark.asyncio
async def test_search_cie10_partial_description_match(
    db_session: AsyncSession,
    sample_cie10_codes: List[CatalogoCIE10]
):
    """Test búsqueda parcial en descripción."""
    # Act
    results = await catalogo_service.search_cie10(db_session, "vías respiratorias")
    
    # Assert
    assert len(results) >= 1
    assert any("vías respiratorias" in r.descripcion.lower() for r in results)


@pytest.mark.asyncio
async def test_count_after_create(
    db_session: AsyncSession,
    sample_cie10_codes: List[CatalogoCIE10]
):
    """Test que el conteo se actualiza después de crear."""
    # Arrange
    count_before = await catalogo_service.count(db_session)
    
    # Act
    await catalogo_service.create_cie10(db_session, "T88.8", "Nuevo código")
    count_after = await catalogo_service.count(db_session)
    
    # Assert
    assert count_after == count_before + 1

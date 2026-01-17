"""
Tests unitarios para SolicitanteService.
"""
import pytest
import pytest_asyncio
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.solicitante_service import solicitante_service
from app.models.solicitante import Solicitante
from app.schemas.solicitante import SolicitanteCreate, SolicitanteUpdate
from app.core.exceptions import NotFoundException, ValidationException


@pytest_asyncio.fixture
async def test_solicitante(db_session: AsyncSession) -> Solicitante:
    """Fixture que crea un solicitante de prueba."""
    data = SolicitanteCreate(
        correo="juan.perez@example.com",
        nombres="Juan Carlos",
        apellidos="Pérez Gómez",
        telefono="3001234567"
    )
    
    solicitante = await solicitante_service.create_solicitante(db_session, data)
    return solicitante


# ==================== TESTS CRUD ====================

@pytest.mark.asyncio
async def test_create_solicitante_success(db_session: AsyncSession):
    """Test creación exitosa de solicitante."""
    # Arrange
    data = SolicitanteCreate(
        correo="test@example.com",
        nombres="Test",
        apellidos="Usuario",
        telefono="3001111111"
    )
    
    # Act
    result = await solicitante_service.create_solicitante(db_session, data)
    
    # Assert
    assert result.id is not None
    assert result.correo == "test@example.com"
    assert result.nombres == "Test"
    assert result.apellidos == "Usuario"
    assert result.telefono == "3001111111"


@pytest.mark.asyncio
async def test_create_solicitante_duplicate_email(
    db_session: AsyncSession,
    test_solicitante: Solicitante
):
    """Test que no permite crear solicitante con correo duplicado."""
    # Arrange
    data = SolicitanteCreate(
        correo=test_solicitante.correo,  # Mismo correo
        nombres="Otro",
        apellidos="Usuario",
        telefono="3002222222"
    )
    
    # Act & Assert
    with pytest.raises(ValidationException) as exc_info:
        await solicitante_service.create_solicitante(db_session, data)
    
    assert "ya existe" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_create_solicitante_normalizes_email(db_session: AsyncSession):
    """Test que el correo se normaliza (lowercase y sin espacios)."""
    # Arrange
    data = SolicitanteCreate(
        correo="  TEST@EXAMPLE.COM  ",
        nombres="Test",
        apellidos="Normalización",
        telefono="3003333333"
    )
    
    # Act
    result = await solicitante_service.create_solicitante(db_session, data)
    
    # Assert
    assert result.correo == "test@example.com"


@pytest.mark.asyncio
async def test_get_solicitante_by_id_success(
    db_session: AsyncSession,
    test_solicitante: Solicitante
):
    """Test obtener solicitante por ID."""
    # Act
    result = await solicitante_service.get_solicitante(db_session, test_solicitante.id)
    
    # Assert
    assert result.id == test_solicitante.id
    assert result.correo == test_solicitante.correo
    assert result.nombres == test_solicitante.nombres


@pytest.mark.asyncio
async def test_get_solicitante_by_id_not_found(db_session: AsyncSession):
    """Test que lanza NotFoundException cuando el ID no existe."""
    # Arrange
    fake_id = uuid4()
    
    # Act & Assert
    with pytest.raises(NotFoundException):
        await solicitante_service.get_solicitante(db_session, fake_id)


@pytest.mark.asyncio
async def test_get_solicitante_by_correo_success(
    db_session: AsyncSession,
    test_solicitante: Solicitante
):
    """Test buscar solicitante por correo exacto."""
    # Act
    result = await solicitante_service.get_by_correo(
        db_session,
        test_solicitante.correo
    )
    
    # Assert
    assert result is not None
    assert result.id == test_solicitante.id
    assert result.correo == test_solicitante.correo


@pytest.mark.asyncio
async def test_get_solicitante_by_correo_not_found(db_session: AsyncSession):
    """Test que retorna None cuando el correo no existe."""
    # Act
    result = await solicitante_service.get_by_correo(
        db_session,
        "noexiste@example.com"
    )
    
    # Assert
    assert result is None


# ==================== TESTS BÚSQUEDA ====================

@pytest.mark.asyncio
async def test_search_by_correo_partial_match(
    db_session: AsyncSession,
    test_solicitante: Solicitante
):
    """Test búsqueda parcial por correo."""
    # Act
    results = await solicitante_service.search_by_correo(
        db_session,
        "juan.perez"
    )
    
    # Assert
    assert len(results) > 0
    assert any(r.id == test_solicitante.id for r in results)


@pytest.mark.asyncio
async def test_search_by_correo_too_short(db_session: AsyncSession):
    """Test que lanza excepción si el término de búsqueda es muy corto."""
    # Act & Assert
    with pytest.raises(ValidationException) as exc_info:
        await solicitante_service.search_by_correo(db_session, "ju")
    
    assert "al menos 3 caracteres" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_search_by_nombre_success(
    db_session: AsyncSession,
    test_solicitante: Solicitante
):
    """Test búsqueda por nombre o apellido."""
    # Act
    results = await solicitante_service.search_by_nombre(
        db_session,
        "Juan"
    )
    
    # Assert
    assert len(results) > 0
    assert any(r.id == test_solicitante.id for r in results)


@pytest.mark.asyncio
async def test_search_by_nombre_too_short(db_session: AsyncSession):
    """Test que lanza excepción si el término de búsqueda es muy corto."""
    # Act & Assert
    with pytest.raises(ValidationException) as exc_info:
        await solicitante_service.search_by_nombre(db_session, "Ju")
    
    assert "al menos 3 caracteres" in str(exc_info.value).lower()


# ==================== TESTS ACTUALIZACIÓN ====================

@pytest.mark.asyncio
async def test_update_solicitante_success(
    db_session: AsyncSession,
    test_solicitante: Solicitante
):
    """Test actualización exitosa de solicitante."""
    # Arrange
    data = SolicitanteUpdate(telefono="3009999999")
    
    # Act
    result = await solicitante_service.update_solicitante(
        db_session,
        test_solicitante.id,
        data
    )
    
    # Assert
    assert result.telefono == "3009999999"
    assert result.correo == test_solicitante.correo  # No cambió


@pytest.mark.asyncio
async def test_update_solicitante_not_found(db_session: AsyncSession):
    """Test que lanza NotFoundException al actualizar ID inexistente."""
    # Arrange
    fake_id = uuid4()
    data = SolicitanteUpdate(telefono="3001111111")
    
    # Act & Assert
    with pytest.raises(NotFoundException):
        await solicitante_service.update_solicitante(db_session, fake_id, data)


@pytest.mark.asyncio
async def test_update_solicitante_duplicate_email(
    db_session: AsyncSession,
    test_solicitante: Solicitante
):
    """Test que no permite actualizar a un correo que ya existe."""
    # Arrange: Crear otro solicitante
    data2 = SolicitanteCreate(
        correo="otro@example.com",
        nombres="Otro",
        apellidos="Usuario",
        telefono="3005555555"
    )
    solicitante2 = await solicitante_service.create_solicitante(db_session, data2)
    
    # Intentar cambiar el correo al del primero
    update_data = SolicitanteUpdate(correo=test_solicitante.correo)
    
    # Act & Assert
    with pytest.raises(ValidationException):
        await solicitante_service.update_solicitante(
            db_session,
            solicitante2.id,
            update_data
        )


# ==================== TESTS ELIMINACIÓN ====================

@pytest.mark.asyncio
async def test_delete_solicitante_success(
    db_session: AsyncSession,
    test_solicitante: Solicitante
):
    """Test eliminación exitosa de solicitante."""
    # Act
    await solicitante_service.delete_solicitante(db_session, test_solicitante.id)
    
    # Assert: Verificar que ya no existe
    with pytest.raises(NotFoundException):
        await solicitante_service.get_solicitante(db_session, test_solicitante.id)


@pytest.mark.asyncio
async def test_delete_solicitante_not_found(db_session: AsyncSession):
    """Test que lanza NotFoundException al eliminar ID inexistente."""
    # Arrange
    fake_id = uuid4()
    
    # Act & Assert
    with pytest.raises(NotFoundException):
        await solicitante_service.delete_solicitante(db_session, fake_id)


# ==================== TESTS PAGINACIÓN ====================

@pytest.mark.asyncio
async def test_list_solicitantes_pagination(db_session: AsyncSession):
    """Test listado de solicitantes con paginación."""
    # Arrange: Crear 3 solicitantes
    nombres_validos = ["Pablo", "María", "Carlos"]
    apellidos_validos = ["García", "López", "Martínez"]
    
    for i in range(3):
        data = SolicitanteCreate(
            correo=f"test{i}@example.com",
            nombres=nombres_validos[i],
            apellidos=apellidos_validos[i],
            telefono=f"300000000{i}"
        )
        await solicitante_service.create_solicitante(db_session, data)
    
    # Act
    results_page1 = await solicitante_service.list_solicitantes(
        db_session,
        skip=0,
        limit=2
    )
    results_page2 = await solicitante_service.list_solicitantes(
        db_session,
        skip=2,
        limit=2
    )
    
    # Assert
    assert len(results_page1) == 2
    assert len(results_page2) >= 1


# ==================== TESTS PROPIEDADES ====================

@pytest.mark.asyncio
async def test_solicitante_nombre_completo_property(
    db_session: AsyncSession,
    test_solicitante: Solicitante
):
    """Test que la propiedad nombre_completo funciona correctamente."""
    # Act
    nombre_completo = test_solicitante.nombre_completo
    
    # Assert
    assert nombre_completo == "Juan Carlos Pérez Gómez"

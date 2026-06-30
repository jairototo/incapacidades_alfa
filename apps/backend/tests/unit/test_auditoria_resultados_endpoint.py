"""
Unit tests for GET /incapacidades/{id}/auditoria-resultados endpoint.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.api.v1.endpoints.incapacidades import get_auditoria_resultados


def make_resultado(incapacidad_id, regla, aprobado=True, severidad="INFO", categoria="GENERAL", detalle=None):
    r = MagicMock()
    r.id = uuid4()
    r.incapacidad_id = incapacidad_id
    r.regla = regla
    r.categoria = categoria
    r.aprobado = aprobado
    r.severidad = severidad
    r.detalle = detalle
    return r


@pytest.mark.asyncio
async def test_get_auditoria_resultados_returns_list():
    """El endpoint devuelve la lista de resultados para la incapacidad."""
    incapacidad_id = uuid4()
    resultado1 = make_resultado(incapacidad_id, "DIAS_TOTALES", aprobado=True)
    resultado2 = make_resultado(incapacidad_id, "EMPLEADO_ACTIVO", aprobado=False, severidad="ERROR")

    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [resultado1, resultado2]

    mock_execute_result = MagicMock()
    mock_execute_result.scalars.return_value = mock_scalars

    db = AsyncMock()
    db.execute = AsyncMock(return_value=mock_execute_result)

    mock_user = MagicMock()

    with patch(
        "app.api.v1.endpoints.incapacidades.incapacidad_service"
    ) as mock_service:
        mock_service.get_incapacidad = AsyncMock()

        result = await get_auditoria_resultados(
            incapacidad_id=incapacidad_id,
            db=db,
            current_user=mock_user,
        )

    assert len(result) == 2
    db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_auditoria_resultados_empty_when_none():
    """El endpoint devuelve lista vacía si no hay resultados."""
    incapacidad_id = uuid4()

    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []

    mock_execute_result = MagicMock()
    mock_execute_result.scalars.return_value = mock_scalars

    db = AsyncMock()
    db.execute = AsyncMock(return_value=mock_execute_result)

    mock_user = MagicMock()

    with patch(
        "app.api.v1.endpoints.incapacidades.incapacidad_service"
    ) as mock_service:
        mock_service.get_incapacidad = AsyncMock()

        result = await get_auditoria_resultados(
            incapacidad_id=incapacidad_id,
            db=db,
            current_user=mock_user,
        )

    assert result == []


@pytest.mark.asyncio
async def test_get_auditoria_resultados_validates_incapacidad_exists():
    """El endpoint llama a get_incapacidad para validar que existe."""
    incapacidad_id = uuid4()

    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []

    mock_execute_result = MagicMock()
    mock_execute_result.scalars.return_value = mock_scalars

    db = AsyncMock()
    db.execute = AsyncMock(return_value=mock_execute_result)

    mock_user = MagicMock()

    with patch(
        "app.api.v1.endpoints.incapacidades.incapacidad_service"
    ) as mock_service:
        mock_service.get_incapacidad = AsyncMock()

        await get_auditoria_resultados(
            incapacidad_id=incapacidad_id,
            db=db,
            current_user=mock_user,
        )

        mock_service.get_incapacidad.assert_called_once_with(
            db, incapacidad_id, with_relations=False
        )


@pytest.mark.asyncio
async def test_get_auditoria_resultados_query_uses_incapacidad_id():
    """El endpoint construye la query filtrando por incapacidad_id."""
    incapacidad_id = uuid4()

    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []

    mock_execute_result = MagicMock()
    mock_execute_result.scalars.return_value = mock_scalars

    db = AsyncMock()
    db.execute = AsyncMock(return_value=mock_execute_result)

    mock_user = MagicMock()

    with patch(
        "app.api.v1.endpoints.incapacidades.incapacidad_service"
    ) as mock_service:
        mock_service.get_incapacidad = AsyncMock()

        await get_auditoria_resultados(
            incapacidad_id=incapacidad_id,
            db=db,
            current_user=mock_user,
        )

    # Verify db.execute was called with a query
    db.execute.assert_called_once()
    call_args = db.execute.call_args
    query_str = str(call_args[0][0])
    # The query should reference the auditoria_resultado table
    assert "auditoria_resultado" in query_str

"""Unit tests for IncapacidadService.create_from_pre_incapacidad()."""
import pytest
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.services.incapacidad_service import IncapacidadService
from app.utils.enums import EstadoIncapacidad, TipoIncapacidad


@pytest.fixture
def mock_pre_inc():
    m = MagicMock()
    m.id = uuid4()
    m.numero_radicacion = 202600042
    m.tipo = "ARL"
    m.fecha_inicio = date(2026, 1, 15)
    m.fecha_fin = date(2026, 1, 25)
    m.diagnostico_cie10 = "S62.0"
    m.descripcion_diagnostico = "Fractura muñeca"
    m.nombre_medico = "Dr. García"
    m.registro_medico = "RM12345"
    m.ips = "Clínica Norte"
    m.valor_dia = Decimal("50000.00")
    m.observaciones = None
    return m


@pytest.fixture
def mock_empleado():
    m = MagicMock()
    m.id = uuid4()
    return m


@pytest.fixture
def mock_empresa():
    m = MagicMock()
    m.id = uuid4()
    return m


@pytest.mark.asyncio
async def test_create_from_pre_incapacidad_with_empleado(mock_pre_inc, mock_empleado, mock_empresa):
    """Creates incapacidad with numero = str(pre_inc.numero_radicacion), empleado linked."""
    service = IncapacidadService()
    created = MagicMock()
    created.id = uuid4()
    mock_create = AsyncMock(return_value=created)
    mock_get = AsyncMock(return_value=created)

    with (
        patch.object(service.repository, "create", new=mock_create),
        patch.object(service.repository, "get_by_id_with_relations", new=mock_get),
    ):
        db = AsyncMock()
        result = await service.create_from_pre_incapacidad(
            db, mock_pre_inc, empleado=mock_empleado, empresa=mock_empresa
        )
        assert result == created
        call_args = mock_create.call_args[0][1]
        assert call_args["numero"] == "202600042"
        assert call_args["tipo"] == TipoIncapacidad.ARL
        assert call_args["estado"] == EstadoIncapacidad.RADICADA
        assert call_args["empleado_id"] == mock_empleado.id
        assert call_args["empresa_id"] == mock_empresa.id


@pytest.mark.asyncio
async def test_create_from_pre_incapacidad_without_empleado(mock_pre_inc):
    """Creates incapacidad with empleado_id=None, empresa_id=None — does not raise."""
    service = IncapacidadService()
    created = MagicMock()
    created.id = uuid4()
    mock_create = AsyncMock(return_value=created)
    mock_get = AsyncMock(return_value=created)

    with (
        patch.object(service.repository, "create", new=mock_create),
        patch.object(service.repository, "get_by_id_with_relations", new=mock_get),
    ):
        db = AsyncMock()
        result = await service.create_from_pre_incapacidad(db, mock_pre_inc)
        assert result == created
        call_args = mock_create.call_args[0][1]
        assert call_args["empleado_id"] is None
        assert call_args["empresa_id"] is None


@pytest.mark.asyncio
async def test_create_from_pre_incapacidad_calculates_dias_totales(mock_pre_inc):
    """dias_totales is calculated from fecha_inicio / fecha_fin."""
    service = IncapacidadService()
    created = MagicMock()
    created.id = uuid4()
    mock_create = AsyncMock(return_value=created)
    mock_get = AsyncMock(return_value=created)

    with (
        patch.object(service.repository, "create", new=mock_create),
        patch.object(service.repository, "get_by_id_with_relations", new=mock_get),
    ):
        db = AsyncMock()
        await service.create_from_pre_incapacidad(db, mock_pre_inc)
        call_args = mock_create.call_args[0][1]
        assert call_args["dias_totales"] == 11  # Jan 15–25 inclusive

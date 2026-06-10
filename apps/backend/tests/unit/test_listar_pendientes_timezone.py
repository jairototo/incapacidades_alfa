"""
Unit tests for IncapacidadService.listar_pendientes() timezone handling.

Root cause of bug: when created_at and updated_at are tz-aware (as returned by
asyncpg for DateTime(timezone=True) columns), the old code stripped tzinfo from
updated_at but left ahora_upd as ahora_local (tz-aware) → TypeError on subtraction.
"""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.services.incapacidad_service import IncapacidadService


def _make_incap(created_at: datetime, updated_at: datetime) -> MagicMock:
    m = MagicMock()
    m.id = uuid4()
    m.created_at = created_at
    m.updated_at = updated_at
    return m


@pytest.fixture
def service():
    svc = IncapacidadService.__new__(IncapacidadService)
    svc.repository = MagicMock()
    return svc


@pytest.mark.asyncio
async def test_listar_pendientes_tz_aware_timestamps_no_crash(service):
    """Tz-aware timestamps (asyncpg production path) must not raise TypeError."""
    now = datetime.now(timezone.utc)
    incap = _make_incap(
        created_at=now - timedelta(days=5),
        updated_at=now - timedelta(days=2),
    )
    service.repository.listar_pendientes = AsyncMock(return_value=[incap])

    db = AsyncMock()
    result = await service.listar_pendientes(db)

    assert len(result) == 1
    assert result[0]["dias_desde_radicacion"] == 5
    assert result[0]["dias_en_estado_actual"] == 2


@pytest.mark.asyncio
async def test_listar_pendientes_tz_naive_timestamps_no_crash(service):
    """Tz-naive timestamps (test DB path) must continue to work."""
    now = datetime.utcnow()
    incap = _make_incap(
        created_at=now - timedelta(days=3),
        updated_at=now - timedelta(days=1),
    )
    service.repository.listar_pendientes = AsyncMock(return_value=[incap])

    db = AsyncMock()
    result = await service.listar_pendientes(db)

    assert len(result) == 1
    assert result[0]["dias_desde_radicacion"] == 3
    assert result[0]["dias_en_estado_actual"] == 1


@pytest.mark.asyncio
async def test_listar_pendientes_dias_antiguedad_min_filters_correctly(service):
    """dias_antiguedad_min filter works correctly for tz-aware timestamps."""
    now = datetime.now(timezone.utc)
    old_incap = _make_incap(
        created_at=now - timedelta(days=10),
        updated_at=now - timedelta(days=3),
    )
    new_incap = _make_incap(
        created_at=now - timedelta(days=2),
        updated_at=now - timedelta(days=1),
    )
    service.repository.listar_pendientes = AsyncMock(return_value=[old_incap, new_incap])

    db = AsyncMock()
    result = await service.listar_pendientes(db, dias_antiguedad_min=5)

    assert len(result) == 1
    assert result[0]["dias_desde_radicacion"] == 10

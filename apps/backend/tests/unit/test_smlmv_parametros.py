"""
Tests for smlmv_parametros repository.

Verifica que el repositorio obtenga correctamente los valores
del SMLMV (Salario Mínimo Legal Mensual Vigente) por año.
"""
from datetime import date
from decimal import Decimal

import pytest
import pytest_asyncio

from app.db.repositories.smlmv_parametros_repository import smlmv_parametros_repository
from app.models.previsionales.smlmv_parametros import SmlmvParametros


@pytest_asyncio.fixture
async def seed_smlmv_parametros(db_session):
    """Seed smlmv_parametros table with known values before tests run."""
    seed_data = [
        SmlmvParametros(
            ano=2024,
            valor=Decimal("1300000.00"),
            vigente_desde=date(2024, 1, 1),
        ),
        SmlmvParametros(
            ano=2025,
            valor=Decimal("1423500.00"),
            vigente_desde=date(2025, 1, 1),
        ),
        SmlmvParametros(
            ano=2026,
            valor=Decimal("1750905.00"),
            vigente_desde=date(2026, 1, 1),
        ),
    ]
    db_session.add_all(seed_data)
    await db_session.commit()


@pytest.mark.asyncio
async def test_get_by_ano_2026(db_session, seed_smlmv_parametros):
    """get_by_ano(2026) should return Decimal('1750905')."""
    params = await smlmv_parametros_repository.get_by_ano(db_session, 2026)
    assert params is not None
    assert params.ano == 2026
    assert params.valor == Decimal("1750905.00")


@pytest.mark.asyncio
async def test_get_by_ano_2025(db_session, seed_smlmv_parametros):
    """get_by_ano(2025) should return Decimal('1423500')."""
    params = await smlmv_parametros_repository.get_by_ano(db_session, 2025)
    assert params is not None
    assert params.ano == 2025
    assert params.valor == Decimal("1423500.00")


@pytest.mark.asyncio
async def test_get_by_ano_2024(db_session, seed_smlmv_parametros):
    """get_by_ano(2024) should return Decimal('1300000')."""
    params = await smlmv_parametros_repository.get_by_ano(db_session, 2024)
    assert params is not None
    assert params.ano == 2024
    assert params.valor == Decimal("1300000.00")


@pytest.mark.asyncio
async def test_get_by_ano_nonexistent(db_session):
    """get_by_ano() for nonexistent year should return None."""
    params = await smlmv_parametros_repository.get_by_ano(db_session, 9999)
    assert params is None

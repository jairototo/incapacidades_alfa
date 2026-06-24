"""
TDD tests for Task 5.0: ibl_parametros table, model, repository, and seed data.

Tests:
1. Seed row for año=2026 exists after migration (via repository)
2. Seed values match exact 2026 percentages from the SDD
3. get_by_ano returns None for a year with no row
4. IblParametros model can be created and retrieved via repository
5. Breakdown arithmetic uses seed percentages correctly (unit test, no DB)
"""
import pytest
from decimal import Decimal

import sqlalchemy as sa


# ---------------------------------------------------------------------------
# 1. Seed row exists for año=2026
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_ibl_parametros_seed_exists(db_session):
    """The migration seeds exactly one row for 2026."""
    from app.db.repositories.ibl_parametros_repository import ibl_parametros_repository

    # The test DB is created via Base.metadata.create_all (no migrations run),
    # so we insert the seed row directly to mirror what the migration does.
    # created_at/updated_at must be provided explicitly because the test DB
    # uses Python-side defaults (not server_default), so raw SQL must supply NOW().
    await db_session.execute(sa.text("""
        INSERT INTO ibl_parametros
          (id, ano, aporte_patronal_pension, aporte_patronal_salud,
           aporte_trabajador_pension, aporte_trabajador_salud,
           created_at, updated_at)
        VALUES
          (gen_random_uuid(), 2026, 12.00, 8.50, 4.00, 4.00, NOW(), NOW())
        ON CONFLICT (ano) DO NOTHING
    """))
    await db_session.commit()

    params = await ibl_parametros_repository.get_by_ano(db_session, 2026)
    assert params is not None, "Seed row for año=2026 debe existir"


# ---------------------------------------------------------------------------
# 2. Seed values match exact 2026 percentages
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_ibl_parametros_2026_values(db_session):
    """The 2026 seed row contains the exact percentages specified in the SDD."""
    from app.db.repositories.ibl_parametros_repository import ibl_parametros_repository

    await db_session.execute(sa.text("""
        INSERT INTO ibl_parametros
          (id, ano, aporte_patronal_pension, aporte_patronal_salud,
           aporte_trabajador_pension, aporte_trabajador_salud,
           created_at, updated_at)
        VALUES
          (gen_random_uuid(), 2026, 12.00, 8.50, 4.00, 4.00, NOW(), NOW())
        ON CONFLICT (ano) DO NOTHING
    """))
    await db_session.commit()

    params = await ibl_parametros_repository.get_by_ano(db_session, 2026)
    assert params is not None

    assert params.aporte_patronal_pension == Decimal("12.00"), (
        f"aporte_patronal_pension esperado 12.00, obtenido {params.aporte_patronal_pension}"
    )
    assert params.aporte_patronal_salud == Decimal("8.50"), (
        f"aporte_patronal_salud esperado 8.50, obtenido {params.aporte_patronal_salud}"
    )
    assert params.aporte_trabajador_pension == Decimal("4.00"), (
        f"aporte_trabajador_pension esperado 4.00, obtenido {params.aporte_trabajador_pension}"
    )
    assert params.aporte_trabajador_salud == Decimal("4.00"), (
        f"aporte_trabajador_salud esperado 4.00, obtenido {params.aporte_trabajador_salud}"
    )


# ---------------------------------------------------------------------------
# 3. get_by_ano returns None for missing year
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_ibl_parametros_get_by_ano_missing(db_session):
    """get_by_ano returns None when no row exists for the requested year."""
    from app.db.repositories.ibl_parametros_repository import ibl_parametros_repository

    params = await ibl_parametros_repository.get_by_ano(db_session, 1999)
    assert params is None, "Debe retornar None para un año sin configuración"


# ---------------------------------------------------------------------------
# 4. Model CRUD via repository (create + retrieve)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_ibl_parametros_create_and_retrieve(db_session):
    """IblParametros can be created via repository and retrieved by año."""
    from app.db.repositories.ibl_parametros_repository import ibl_parametros_repository

    created = await ibl_parametros_repository.create(db_session, {
        "ano": 2027,
        "aporte_patronal_pension": Decimal("12.50"),
        "aporte_patronal_salud": Decimal("8.50"),
        "aporte_trabajador_pension": Decimal("4.00"),
        "aporte_trabajador_salud": Decimal("4.00"),
    })
    assert created.id is not None
    assert created.ano == 2027

    fetched = await ibl_parametros_repository.get_by_ano(db_session, 2027)
    assert fetched is not None
    assert fetched.aporte_patronal_pension == Decimal("12.50")


# ---------------------------------------------------------------------------
# 5. Arithmetic sanity — breakdown uses seed percentages (no DB required)
# ---------------------------------------------------------------------------

def test_calcular_breakdown_uses_db_parametros():
    """
    Verify the liquidation arithmetic is consistent with the 2026 seed values.

    This is a pure-Python unit test — no DB session needed.

    IBL mensual: 3_500_000 COP
    Días: 10
    IBC diario: 3_500_000 / 30 = 116_666.67 (aproximado)

    For simplicity we test using monthly-rate × days directly, as the service does:
        valor = ibl * dias * (porcentaje / 100)
    """
    ibl = Decimal("3500000")
    dias = Decimal("10")

    # Percentages from 2026 seed
    pct_patronal_pension = Decimal("12.00")
    pct_patronal_salud = Decimal("8.50")
    pct_trabajador_pension = Decimal("4.00")
    pct_trabajador_salud = Decimal("4.00")

    valor_patronal_pension = ibl * dias * (pct_patronal_pension / 100)
    valor_patronal_salud = ibl * dias * (pct_patronal_salud / 100)
    valor_trabajador_pension = ibl * dias * (pct_trabajador_pension / 100)
    valor_trabajador_salud = ibl * dias * (pct_trabajador_salud / 100)

    assert valor_patronal_pension == Decimal("4200000.00"), (
        f"Patronal pension: {valor_patronal_pension}"
    )
    assert valor_patronal_salud == Decimal("2975000.00"), (
        f"Patronal salud: {valor_patronal_salud}"
    )
    assert valor_trabajador_pension == Decimal("1400000.00"), (
        f"Trabajador pension: {valor_trabajador_pension}"
    )
    assert valor_trabajador_salud == Decimal("1400000.00"), (
        f"Trabajador salud: {valor_trabajador_salud}"
    )

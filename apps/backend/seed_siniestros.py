"""
seed_siniestros.py — One-off script to create a default siniestro for every
empleado that has no siniestros yet, so the SINIESTRO_REQUERIDO gate does not
lock out existing incapacidades históricas.

Usage (from inside the api container):
    python seed_siniestros.py
Or via docker-compose (from apps/backend/):
    docker compose exec api python seed_siniestros.py
"""
import asyncio
import sys
from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.db.repositories.siniestro_repository import siniestro_repository
from app.models.empleado import Empleado
from app.utils.enums import TipoSiniestro, GravedadSiniestro, EstadoSiniestro, SyncSource


async def seed(db: AsyncSession) -> None:
    """Seed siniestros for all empleados that have none."""
    # Fetch all empleados (no lazy-loads needed, just base fields)
    result = await db.execute(select(Empleado))
    empleados = list(result.scalars().all())

    created = 0
    skipped = 0
    warned = 0

    for emp in empleados:
        # Skip empleados without an empresa_id (shouldn't happen per model, but guard anyway)
        if emp.empresa_id is None:
            print(
                f"  WARN  empleado {emp.id} ({emp.numero_documento}) has no empresa_id — skipping",
                file=sys.stderr,
            )
            warned += 1
            continue

        # Check if they already have at least one siniestro
        existing = await siniestro_repository.get_by_empleado(db, emp.id, limit=1)
        if existing:
            skipped += 1
            continue

        # Build seed siniestro number (max 50 chars)
        numero = f"SIN-SEED-{emp.numero_documento}"
        if len(numero) > 50:
            numero = numero[:50]

        fecha = emp.fecha_ingreso if emp.fecha_ingreso is not None else date.today()

        await siniestro_repository.create(
            db,
            {
                "numero_siniestro": numero,
                "empleado_id": emp.id,
                "empresa_id": emp.empresa_id,
                "fecha_siniestro": fecha,
                "tipo_siniestro": TipoSiniestro.ACCIDENTE_TRABAJO,
                "descripcion": "Siniestro semilla — para no bloquear incapacidades históricas",
                "gravedad": GravedadSiniestro.LEVE,
                "estado": EstadoSiniestro.REPORTADO,
                "sync_source": SyncSource.MANUAL,
                "fecha_reporte": datetime.utcnow(),
                "reportado_por": "sistema-seed",
            },
        )
        print(f"  CREATE siniestro {numero} for empleado {emp.numero_documento}")
        created += 1

    print(
        f"\nSummary: Created {created} siniestros, "
        f"skipped {skipped} (already had siniestros), "
        f"warned {warned} (no empresa_id)."
    )


async def main() -> None:
    async with AsyncSessionLocal() as db:
        await seed(db)


if __name__ == "__main__":
    asyncio.run(main())

"""
Script para crear los auditores ficticios (por sucursal) y el auditor por
defecto usados por la asignación automática de auditoría.

Nombres/correos son ficticios — deliberadamente distintos a los auditores
reales listados en docs/recursos_arl/Asignación Auditores - Incapacidades ARL.xlsx,
ya que esos usuarios reales aún no tienen cuentas en el sistema.

Idempotente: si un username ya existe, lo salta.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.db.session import AsyncSessionLocal
from app.core.security import pwd_context
from app.utils.enums import RolUsuario, EstadoUsuario, SucursalSiniestro

AUDITORES = [
    ("auditor.cali", "Camila Restrepo Vargas", "camila.restrepo@segurosalfa-test.com.co", SucursalSiniestro.CALI),
    ("auditor.medellin", "Santiago Zuluaga Marín", "santiago.zuluaga@segurosalfa-test.com.co", SucursalSiniestro.MEDELLIN),
    ("auditor.cartagena", "Valentina Cabrales Ibarra", "valentina.cabrales@segurosalfa-test.com.co", SucursalSiniestro.CARTAGENA),
    ("auditor.bogota1", "Andrés Felipe Rojas Peña", "andres.rojas@segurosalfa-test.com.co", SucursalSiniestro.BOGOTA),
    ("auditor.bogota2", "Laura Camila Torres Duque", "laura.torres@segurosalfa-test.com.co", SucursalSiniestro.BOGOTA),
    ("auditor.bogota3", "Juan Pablo Medina Salcedo", "juan.medina@segurosalfa-test.com.co", SucursalSiniestro.BOGOTA),
    ("auditor.bogota4", "Daniela Ríos Castañeda", "daniela.rios@segurosalfa-test.com.co", SucursalSiniestro.BOGOTA),
    ("auditor_default", "Auditor por Defecto", "auditor.default@segurosalfa-test.com.co", None),
]

DEFAULT_PASSWORD = "Auditor2026!"


async def seed_auditores() -> None:
    async with AsyncSessionLocal() as session:
        for username, nombre_completo, email, sucursal in AUDITORES:
            existing = await session.execute(
                text("SELECT id FROM usuario WHERE username = :username"),
                {"username": username},
            )
            if existing.fetchone():
                print(f"⏭️  {username} ya existe, se omite")
                continue

            import uuid
            await session.execute(
                text("""
                    INSERT INTO usuario (
                        id, username, email, password_hash, nombre_completo,
                        rol, estado, sucursal, incapacidades_asignadas_activas,
                        intentos_fallidos, token_version, must_change_password, created_at, updated_at
                    ) VALUES (
                        :id, :username, :email, :password_hash, :nombre_completo,
                        :rol, :estado, :sucursal, 0,
                        0, 0, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                    )
                """),
                {
                    "id": uuid.uuid4(),
                    "username": username,
                    "email": email,
                    "password_hash": pwd_context.hash(DEFAULT_PASSWORD),
                    "nombre_completo": nombre_completo,
                    "rol": RolUsuario.AUDITOR.value,
                    "estado": EstadoUsuario.ACTIVO.value,
                    "sucursal": sucursal.value if sucursal else None,
                },
            )
            print(f"✅ {username} creado (sucursal={sucursal.value if sucursal else '—'})")

        await session.commit()

    print(f"\n🔐 Password temporal para todos: {DEFAULT_PASSWORD} (must_change_password=true)")


if __name__ == "__main__":
    asyncio.run(seed_auditores())

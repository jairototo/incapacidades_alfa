"""
Script para crear los auditores previsionales y jurídicos ficticios usados
por el módulo de Incapacidades Previsionales.

Nombres/correos son ficticios, siguiendo el mismo patrón de
scripts/seed_auditores.py.

Idempotente: si un username ya existe, lo salta.
"""
import asyncio
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.db.session import AsyncSessionLocal
from app.core.security import pwd_context
from app.utils.enums import RolUsuario, EstadoUsuario

AUDITORES_PREVISIONALES = [
    (
        "auditor.previsional1",
        "Mariana Osorio Gil",
        "mariana.osorio@segurosalfa-test.com.co",
        RolUsuario.AUDITOR_PREVISIONALES,
    ),
    (
        "auditor.previsional2",
        "Felipe Herrera Nieto",
        "felipe.herrera@segurosalfa-test.com.co",
        RolUsuario.AUDITOR_PREVISIONALES,
    ),
    (
        "auditor.juridico1",
        "Isabel Cristina Prada",
        "isabel.prada@segurosalfa-test.com.co",
        RolUsuario.AUDITOR_JURIDICO,
    ),
]

DEFAULT_PASSWORD = "Previsional2026!"


async def seed_auditores_previsionales() -> None:
    async with AsyncSessionLocal() as session:
        for username, nombre_completo, email, rol in AUDITORES_PREVISIONALES:
            existing = await session.execute(
                text("SELECT id FROM usuario WHERE username = :username"),
                {"username": username},
            )
            if existing.fetchone():
                print(f"⏭️  {username} ya existe, se omite")
                continue

            await session.execute(
                text("""
                    INSERT INTO usuario (
                        id, username, email, password_hash, nombre_completo,
                        rol, estado, incapacidades_asignadas_activas,
                        intentos_fallidos, token_version, must_change_password, created_at, updated_at
                    ) VALUES (
                        :id, :username, :email, :password_hash, :nombre_completo,
                        :rol, :estado, 0,
                        0, 0, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                    )
                """),
                {
                    "id": uuid.uuid4(),
                    "username": username,
                    "email": email,
                    "password_hash": pwd_context.hash(DEFAULT_PASSWORD),
                    "nombre_completo": nombre_completo,
                    "rol": rol.value,
                    "estado": EstadoUsuario.ACTIVO.value,
                },
            )
            print(f"✅ {username} creado (rol={rol.value})")

        await session.commit()

    print(f"\n🔐 Password temporal para todos: {DEFAULT_PASSWORD} (must_change_password=true)")


if __name__ == "__main__":
    asyncio.run(seed_auditores_previsionales())

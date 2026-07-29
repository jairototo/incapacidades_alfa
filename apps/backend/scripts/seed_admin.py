"""
Script para crear usuario administrador inicial.
"""
import asyncio
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal

# Importar todos los modelos para que SQLAlchemy los registre
from app.models import (
    Usuario, Empresa, Empleado, Afiliado, Incapacidad, 
    Siniestro, Documento, HistorialEstado,
    OrdenPago, AuditoriaLog
)
from app.models.refresh_token import RefreshToken
from app.utils.enums import RolUsuario, EstadoUsuario
from app.core.security import pwd_context


async def create_admin_user():
    """Crea el usuario administrador inicial."""
    
    async with AsyncSessionLocal() as session:
        # Verificar si ya existe el admin usando SQL directo
        from sqlalchemy import text
        result = await session.execute(
            text("SELECT id, email, username FROM usuario WHERE email = :email"),
            {"email": "admin@incapacidades.com"}
        )
        existing_user = result.fetchone()
        
        if existing_user:
            print("❌ El usuario admin ya existe")
            print(f"   ID: {existing_user[0]}")
            print(f"   Email: {existing_user[1]}")
            print(f"   Username: {existing_user[2]}")
            return
        
        # Crear usuario admin usando SQL directo para evitar problemas con relaciones
        import uuid
        admin_id = uuid.uuid4()
        
        await session.execute(
            text("""
                INSERT INTO usuario (
                    id, username, email, password_hash, nombre_completo,
                    rol, estado, intentos_fallidos, created_at, updated_at, 
                    token_version, must_change_password
                ) VALUES (
                    :id, :username, :email, :password_hash, :nombre_completo,
                    :rol, :estado, :intentos_fallidos, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 
                    :token_version, :must_change_password
                )
            """),
            {
                "id": admin_id,
                "username": "admin",
                "email": "admin@incapacidades.com",
                "password_hash": pwd_context.hash("admin123"),
                "nombre_completo": "Administrador del Sistema",
                "rol": RolUsuario.ADMIN.value,
                "estado": EstadoUsuario.ACTIVO.value,
                "intentos_fallidos": 0,
                "token_version":0,
                "must_change_password":False
            }
        )
        
        await session.commit()
        
        print("✅ Usuario administrador creado exitosamente")
        print(f"   ID: {admin_id}")
        print(f"   Email: admin@incapacidades.com")
        print(f"   Username: admin")
        print(f"   Password: admin123")
        print(f"   Rol: {RolUsuario.ADMIN.value}")
        print(f"   Estado: {EstadoUsuario.ACTIVO.value}")
        print("\n🔐 Credenciales para login:")
        print(f"   username: admin")
        print(f"   password: admin123")


if __name__ == "__main__":
    asyncio.run(create_admin_user())

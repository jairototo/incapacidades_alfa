#!/usr/bin/env python3
"""
Script para verificar el estado de las migraciones de Alembic.

Uso:
    python scripts/check_migrations.py
"""
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.runtime.migration import MigrationContext
from sqlalchemy import create_engine, text

from app.core.config import Settings


def check_migrations():
    """Verifica el estado de las migraciones."""
    
    settings = Settings()
    
    # Create alembic config
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
    
    # Get script directory
    script = ScriptDirectory.from_config(alembic_cfg)
    
    # Get all revisions
    revisions = list(script.walk_revisions())
    
    print("=" * 60)
    print("VERIFICACIÓN DE MIGRACIONES ALEMBIC")
    print("=" * 60)
    print()
    
    print(f"📁 Total de migraciones: {len(revisions)}")
    print()
    
    if revisions:
        print("📋 Lista de migraciones:")
        for rev in reversed(revisions):
            print(f"  • {rev.revision[:12]} - {rev.doc}")
        print()
    
    # Check database status
    try:
        # Create sync engine for checking
        engine = create_engine(settings.DATABASE_URL.replace('+asyncpg', ''))
        
        with engine.connect() as conn:
            # Check if alembic_version table exists
            result = conn.execute(text(
                "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
                "WHERE table_name = 'alembic_version')"
            ))
            table_exists = result.scalar()
            
            if table_exists:
                # Get current version
                result = conn.execute(text("SELECT version_num FROM alembic_version"))
                current = result.scalar()
                
                if current:
                    print(f"✅ Base de datos inicializada")
                    print(f"📍 Revisión actual: {current}")
                    
                    # Check if up to date
                    head = script.get_current_head()
                    if current == head:
                        print("✅ Base de datos está actualizada (en HEAD)")
                    else:
                        print(f"⚠️  Base de datos desactualizada")
                        print(f"   Actual: {current}")
                        print(f"   HEAD:   {head}")
                        print()
                        print("💡 Ejecuta: alembic upgrade head")
                else:
                    print("⚠️  Tabla alembic_version existe pero está vacía")
                    print("💡 Ejecuta: alembic stamp head")
            else:
                print("❌ Base de datos NO inicializada")
                print("💡 Ejecuta: alembic upgrade head")
        
        engine.dispose()
        
    except Exception as e:
        print(f"❌ Error conectando a base de datos: {e}")
        print("💡 Verifica que PostgreSQL esté corriendo y DATABASE_URL sea correcto")
    
    print()
    print("=" * 60)
    print("COMANDOS ÚTILES:")
    print("=" * 60)
    print("  alembic current              - Ver revisión actual")
    print("  alembic history              - Ver historial")
    print("  alembic upgrade head         - Aplicar migraciones")
    print("  alembic downgrade -1         - Revertir última migración")
    print("  alembic revision --autogenerate -m 'msg' - Crear migración")
    print()


if __name__ == "__main__":
    check_migrations()

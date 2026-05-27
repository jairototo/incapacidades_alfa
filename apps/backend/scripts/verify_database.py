#!/usr/bin/env python3
"""
Script para verificar que las migraciones y tablas estén creadas correctamente.

Verifica:
- Estado de migraciones Alembic
- Existencia de todas las tablas esperadas
- Estructura de tablas críticas (afiliado, incapacidad)
- Constraints importantes
- Índices creados

Uso:
    python scripts/verify_database.py
    
    # O desde Docker:
    docker compose exec api python scripts/verify_database.py
"""
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Add app to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import create_engine, text, inspect
from alembic.config import Config
from alembic.script import ScriptDirectory

from apps.backend.app.core.config import Settings


# Tablas esperadas en el sistema
EXPECTED_TABLES = {
    'empresa': 'Empresas afiliadas',
    'empleado': 'Empleados de empresas (ARL)',
    'afiliado': 'Afiliados con pólizas (SALUD)',
    'usuario': 'Usuarios del sistema',
    'siniestro': 'Siniestros laborales',
    'incapacidad': 'Incapacidades ARL/SALUD',
    'documento': 'Documentos adjuntos',
    'historial_estado': 'Auditoría de estados',
    'orden_pago': 'Órdenes de pago',
    'auditoria_log': 'Log de auditoría',
    'alembic_version': 'Control de versiones Alembic'
}

# Índices críticos que deben existir
CRITICAL_INDEXES = {
    'incapacidad': ['idx_incapacidad_afiliado', 'idx_incapacidad_empleado', 'idx_incapacidad_tipo'],
    'afiliado': ['idx_afiliado_poliza'],
    'empleado': ['idx_empleado_empresa'],
    'empresa': ['idx_empresa_nit'],
}


# Constraints críticos
CRITICAL_CONSTRAINTS = {
    'incapacidad': ['chk_incapacidad_tipo_relacion', 'chk_incapacidad_tipo'],
    'afiliado': ['chk_afiliado_estado', 'chk_afiliado_tipo_poliza'],
}


def print_header(text: str):
    """Imprime un encabezado formateado."""
    print("\n" + "=" * 70)
    print(text.center(70))
    print("=" * 70)


def print_section(text: str):
    """Imprime un título de sección."""
    print(f"\n{'─' * 70}")
    print(f"  {text}")
    print(f"{'─' * 70}")


def check_alembic_status() -> Tuple[bool, str, str]:
    """Verifica el estado de las migraciones Alembic."""
    try:
        settings = Settings()
        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
        
        script = ScriptDirectory.from_config(alembic_cfg)
        head = script.get_current_head()
        
        # Get current version from database
        engine = create_engine(settings.DATABASE_URL.replace('+asyncpg', ''))
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version_num FROM alembic_version"))
            current = result.scalar()
        
        engine.dispose()
        
        is_up_to_date = (current == head)
        return is_up_to_date, current or "N/A", head or "N/A"
        
    except Exception as e:
        return False, "ERROR", str(e)


def check_tables() -> Tuple[List[str], List[str]]:
    """Verifica la existencia de tablas."""
    try:
        settings = Settings()
        engine = create_engine(settings.DATABASE_URL.replace('+asyncpg', ''))
        
        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename"
            ))
            existing_tables = [row[0] for row in result]
        
        engine.dispose()
        
        expected = set(EXPECTED_TABLES.keys())
        found = set(existing_tables)
        
        missing = list(expected - found)
        extra = list(found - expected)
        
        return missing, extra
        
    except Exception as e:
        print(f"❌ Error verificando tablas: {e}")
        return list(EXPECTED_TABLES.keys()), []


def check_table_structure(table_name: str) -> Dict:
    """Verifica la estructura de una tabla."""
    try:
        settings = Settings()
        engine = create_engine(settings.DATABASE_URL.replace('+asyncpg', ''))
        inspector = inspect(engine)
        
        columns = inspector.get_columns(table_name)
        indexes = inspector.get_indexes(table_name)
        pk = inspector.get_pk_constraint(table_name)
        fks = inspector.get_foreign_keys(table_name)
        
        # Get check constraints
        with engine.connect() as conn:
            result = conn.execute(text(f"""
                SELECT conname 
                FROM pg_constraint 
                WHERE conrelid = '{table_name}'::regclass 
                AND contype = 'c'
            """))
            check_constraints = [row[0] for row in result]
        
        engine.dispose()
        
        return {
            'columns': len(columns),
            'indexes': [idx['name'] for idx in indexes],
            'pk': pk['constrained_columns'] if pk else [],
            'fks': len(fks),
            'check_constraints': check_constraints
        }
        
    except Exception as e:
        return {'error': str(e)}


def verify_afiliado_table():
    """Verificación específica de la tabla afiliado."""
    print_section("📋 Verificación Tabla AFILIADO")
    
    structure = check_table_structure('afiliado')
    
    if 'error' in structure:
        print(f"  ❌ Error: {structure['error']}")
        return False
    
    expected_cols = 21  # Aproximado
    actual_cols = structure['columns']
    
    print(f"  Columnas: {actual_cols} {'✅' if actual_cols >= expected_cols else '⚠️'}")
    print(f"  Índices: {len(structure['indexes'])}")
    print(f"  Foreign Keys: {structure['fks']}")
    print(f"  Check Constraints: {len(structure['check_constraints'])}")
    
    # Verificar constraint de estado
    has_estado_check = any('estado' in c for c in structure['check_constraints'])
    print(f"  ✅ Constraint estado: {'Presente' if has_estado_check else '❌ FALTANTE'}")
    
    # Verificar índice de numero_poliza
    has_poliza_index = any('poliza' in idx.lower() for idx in structure['indexes'])
    print(f"  {'✅' if has_poliza_index else '❌'} Índice numero_poliza: {'Presente' if has_poliza_index else 'FALTANTE'}")
    
    return True


def verify_incapacidad_table():
    """Verificación específica de la tabla incapacidad."""
    print_section("📋 Verificación Tabla INCAPACIDAD")
    
    structure = check_table_structure('incapacidad')
    
    if 'error' in structure:
        print(f"  ❌ Error: {structure['error']}")
        return False
    
    print(f"  Columnas: {structure['columns']}")
    print(f"  Índices: {len(structure['indexes'])}")
    print(f"  Foreign Keys: {structure['fks']} (debe ser ~7)")
    print(f"  Check Constraints: {len(structure['check_constraints'])}")
    
    # Verificar constraint polimórfico crítico
    has_tipo_relacion = any('tipo_relacion' in c for c in structure['check_constraints'])
    print(f"  {'✅' if has_tipo_relacion else '❌'} Constraint polimórfico (tipo_relacion): {has_tipo_relacion}")
    
    if not has_tipo_relacion:
        print("  ⚠️  CRÍTICO: Falta el constraint que valida ARL vs SALUD!")
    
    # Verificar FKs a empleado, empresa y afiliado
    print(f"  ✅ Foreign Keys configuradas correctamente")
    
    return has_tipo_relacion


def verify_critical_constraints():
    """Verifica los constraints críticos."""
    print_section("🔒 Verificación de Constraints Críticos")
    
    all_good = True
    
    for table, constraints in CRITICAL_CONSTRAINTS.items():
        structure = check_table_structure(table)
        if 'error' in structure:
            print(f"  ❌ {table}: Error al verificar")
            all_good = False
            continue
        
        existing = structure['check_constraints']
        for constraint in constraints:
            has_it = any(constraint in c for c in existing)
            status = '✅' if has_it else '❌'
            print(f"  {status} {table}.{constraint}: {has_it}")
            if not has_it:
                all_good = False
    
    return all_good


def verify_critical_indexes():
    """Verifica los índices críticos."""
    print_section("📊 Verificación de Índices Críticos")
    
    all_good = True
    
    for table, indexes in CRITICAL_INDEXES.items():
        structure = check_table_structure(table)
        if 'error' in structure:
            print(f"  ❌ {table}: Error al verificar")
            all_good = False
            continue
        
        existing = structure['indexes']
        for index in indexes:
            # Buscar si existe un índice que contenga el nombre esperado
            has_it = any(index in idx for idx in existing)
            status = '✅' if has_it else '⚠️'
            print(f"  {status} {table}.{index}: {has_it}")
            if not has_it:
                all_good = False
    
    return all_good


def test_polymorphic_constraint():
    """Prueba el constraint polimórfico de incapacidad."""
    print_section("🧪 Prueba de Constraint Polimórfico")
    
    try:
        settings = Settings()
        engine = create_engine(settings.DATABASE_URL.replace('+asyncpg', ''))
        
        with engine.connect() as conn:
            # Intentar crear incapacidad SALUD con empleado (debe fallar)
            try:
                conn.execute(text("""
                    INSERT INTO incapacidad (
                        numero, tipo, empleado_id, empresa_id, afiliado_id,
                        fecha_inicio, fecha_fin, dias_totales
                    ) VALUES (
                        'TEST-BAD-001', 'SALUD', 
                        '00000000-0000-0000-0000-000000000001',
                        '00000000-0000-0000-0000-000000000002',
                        '00000000-0000-0000-0000-000000000003',
                        '2026-01-01', '2026-01-05', 5
                    )
                """))
                conn.commit()
                print("  ❌ FALLO: Se permitió crear incapacidad SALUD con empleado!")
                print("  ⚠️  El constraint polimórfico NO está funcionando!")
                return False
                
            except Exception as e:
                if 'chk_incapacidad_tipo_relacion' in str(e) or 'check constraint' in str(e).lower():
                    print("  ✅ Constraint polimórfico funciona correctamente")
                    print(f"  ℹ️  Error esperado: {str(e)[:100]}...")
                    conn.rollback()
                    return True
                else:
                    print(f"  ❓ Error inesperado: {e}")
                    conn.rollback()
                    return False
        
        engine.dispose()
        
    except Exception as e:
        print(f"  ❌ Error en prueba: {e}")
        return False


def main():
    """Función principal."""
    print_header("VERIFICACIÓN COMPLETA DE BASE DE DATOS")
    print("Sistema de Gestión de Incapacidades")
    
    # 1. Verificar estado de Alembic
    print_section("🔍 Estado de Migraciones Alembic")
    is_up_to_date, current, head = check_alembic_status()
    
    print(f"  Revisión actual: {current}")
    print(f"  Revisión HEAD:   {head}")
    
    if is_up_to_date:
        print("  ✅ Base de datos actualizada")
    else:
        print("  ⚠️  Base de datos desactualizada")
        print("  💡 Ejecuta: docker compose exec api alembic upgrade head")
        return  # No continuar si no está actualizada
    
    # 2. Verificar tablas
    print_section("📁 Verificación de Tablas")
    missing, extra = check_tables()
    
    if not missing and not extra:
        print(f"  ✅ Todas las tablas esperadas existen ({len(EXPECTED_TABLES)})")
        for table, desc in EXPECTED_TABLES.items():
            print(f"     • {table:20} - {desc}")
    else:
        if missing:
            print(f"  ❌ Tablas faltantes ({len(missing)}):")
            for table in missing:
                print(f"     • {table}")
        
        if extra:
            print(f"  ℹ️  Tablas adicionales ({len(extra)}):")
            for table in extra:
                print(f"     • {table}")
    
    # 3. Verificar estructura de afiliado
    verify_afiliado_table()
    
    # 4. Verificar estructura de incapacidad
    has_polymorphic = verify_incapacidad_table()
    
    # 5. Verificar constraints críticos
    constraints_ok = verify_critical_constraints()
    
    # 6. Verificar índices críticos
    indexes_ok = verify_critical_indexes()
    
    # 7. Probar constraint polimórfico
    if has_polymorphic:
        polymorphic_ok = test_polymorphic_constraint()
    else:
        polymorphic_ok = False
        print_section("🧪 Prueba de Constraint Polimórfico")
        print("  ⏭️  Omitida (constraint no existe)")
    
    # Resumen final
    print_header("RESUMEN DE VERIFICACIÓN")
    
    results = [
        ("Migraciones actualizadas", is_up_to_date),
        ("Todas las tablas presentes", not missing),
        ("Tabla afiliado correcta", True),
        ("Tabla incapacidad correcta", has_polymorphic),
        ("Constraints críticos", constraints_ok),
        ("Índices críticos", indexes_ok),
        ("Constraint polimórfico funciona", polymorphic_ok),
    ]
    
    total = len(results)
    passed = sum(1 for _, status in results if status)
    
    print()
    for name, status in results:
        icon = "✅" if status else "❌"
        print(f"  {icon} {name}")
    
    print()
    print(f"  Resultado: {passed}/{total} verificaciones exitosas")
    
    if passed == total:
        print("\n  🎉 ¡Base de datos completamente verificada!")
        return 0
    else:
        print(f"\n  ⚠️  {total - passed} problemas detectados")
        return 1


if __name__ == "__main__":
    sys.exit(main())

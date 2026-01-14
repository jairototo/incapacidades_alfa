#!/bin/bash
# Script para aplicar migraciones pendientes y verificar la base de datos
# Uso: ./scripts/migrate_and_verify.sh

set -e

echo "======================================================================"
echo "  APLICAR MIGRACIONES Y VERIFICAR BASE DE DATOS"
echo "======================================================================"
echo ""

# Verificar que estemos en el directorio correcto
if [ ! -f "alembic.ini" ]; then
    echo "❌ Error: Debes ejecutar este script desde la carpeta backend/"
    exit 1
fi

echo "📋 Paso 1: Verificar estado actual de migraciones..."
echo "----------------------------------------------------------------------"
docker compose exec api alembic current || {
    echo "❌ Error: No se pudo conectar al contenedor 'api'"
    echo "💡 Asegúrate de que los contenedores estén corriendo: docker compose up -d"
    exit 1
}

echo ""
echo "📋 Paso 2: Aplicar migraciones pendientes..."
echo "----------------------------------------------------------------------"
docker compose exec api alembic upgrade head

echo ""
echo "📋 Paso 3: Verificar que se aplicaron correctamente..."
echo "----------------------------------------------------------------------"
docker compose exec api alembic current

echo ""
echo "📋 Paso 4: Verificación completa de base de datos..."
echo "----------------------------------------------------------------------"
docker compose exec api python scripts/verify_database.py

echo ""
echo "======================================================================"
echo "  ✅ PROCESO COMPLETADO"
echo "======================================================================"

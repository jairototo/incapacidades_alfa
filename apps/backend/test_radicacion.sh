#!/bin/bash
# Script para probar la radicación automática y envío de correo

echo "🧪 === TEST DE RADICACIÓN AUTOMÁTICA Y NOTIFICACIÓN POR CORREO ==="
echo ""

# Verificar servicios
echo "1️⃣ Verificando servicios..."
docker compose ps | grep -E "(api|celery-worker|rabbitmq|redis)" | grep -E "(Up|healthy)"
echo ""

# Limpiar logs anteriores
echo "2️⃣ Preparando logs..."
echo ""

# Instrucciones
echo "3️⃣ INSTRUCCIONES:"
echo "   a) Desde el frontend (http://localhost:3000/radicar):"
echo "      - Completar wizard de radicación"
echo "      - Ingresar email válido del solicitante"
echo "      - Enviar radicación"
echo ""
echo "   b) O usar curl (ajustar UUIDs según tu BD):"
echo "      curl -X POST 'http://localhost:8010/api/v1/incapacidades' \\"
echo "        -H 'Content-Type: application/json' \\"
echo "        -d '{ ... }'"
echo ""

# Monitorear logs
echo "4️⃣ Monitoreando logs del worker..."
echo "   (Presiona Ctrl+C para salir)"
echo ""
echo "⏳ Esperando actividad..."
echo ""

docker compose logs -f celery-worker 2>&1 | grep -E "(CELERY|EMAIL)" --line-buffered

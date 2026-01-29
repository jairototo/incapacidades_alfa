# Sistema de Notificación por Correo - Radicación de Incapacidades

## 📧 Implementación Completada

Se ha implementado un sistema completo de notificación por correo electrónico que se activa automáticamente después de radicar una incapacidad.

## 🔄 Flujo Completo

```
1. Usuario radica incapacidad desde frontend
   ↓
2. Backend guarda incapacidad (estado: RADICADA)
   ↓
3. Responde al frontend inmediatamente
   ↓
4. Lanza tarea Celery en background: radicar_incapacidad_automatica_task
   ↓
5. Worker procesa: Cambia estado RADICADA → EN_AUDITORIA
   ↓
6. Lanza tarea de email: send_incapacidad_radicada_email_task
   ↓
7. Worker envía correo HTML profesional al solicitante
   ✓ Proceso completado
```

## 📋 Componentes Implementados

### 1. Template HTML Profesional
- **Ubicación**: `app/templates/email/incapacidad_radicada.html`
- **Diseño**: Responsive, estilo empresarial con gradientes
- **Contenido**:
  - Número de radicación destacado
  - Datos del beneficiario
  - Información de la incapacidad (fechas, días, diagnóstico)
  - Datos médicos (IPS, médico, EPS)
  - Timeline del proceso
  - Botón CTA para consultar estado
  - Información de contacto

### 2. Servicio de Email
- **Ubicación**: `app/core/email.py`
- **Clase**: `EmailService`
- **Funcionalidades**:
  - Renderizado de templates con Jinja2
  - Envío de correos HTML con SMTP
  - Soporte para modo desarrollo (mock) y producción
  - Manejo de errores robusto

### 3. Tareas de Celery
- **Archivo**: `app/tasks/email_tasks.py`
- **Tareas**:
  - `send_email_task`: Envío genérico de correos
  - `send_bulk_emails_task`: Envío masivo
  - `send_incapacidad_radicada_email_task`: Notificación específica de radicación

### 4. Integración con Radicación
- **Archivo**: `app/tasks/incapacidad_tasks.py`
- **Función**: `_radicar_incapacidad_async`
- **Comportamiento**:
  - Radica la incapacidad
  - Obtiene datos del solicitante, empleado/afiliado, empresa
  - Lanza tarea de email (no espera, fire-and-forget)
  - Si falla el correo, NO falla la radicación

## ⚙️ Configuración SMTP

### Variables de Entorno

Editar `.env`:

```bash
# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu-email@gmail.com
SMTP_PASSWORD=tu-app-password  # Ver instrucciones abajo
SMTP_TLS=True
EMAIL_FROM=noreply@incapacidades.com
```

### Configurar Gmail (Desarrollo)

1. **Crear App Password**:
   - Ir a: https://myaccount.google.com/apppasswords
   - Nombre: "Incapacidades Sistema"
   - Copiar la contraseña generada (16 caracteres)
   - Usar en `SMTP_PASSWORD`

2. **Alternativa**: Usar Mailtrap (desarrollo)
   ```bash
   SMTP_HOST=smtp.mailtrap.io
   SMTP_PORT=2525
   SMTP_USER=tu-username-mailtrap
   SMTP_PASSWORD=tu-password-mailtrap
   ```

### Modo Desarrollo (Sin SMTP)

Si `SMTP_USER` y `SMTP_PASSWORD` están vacíos:
- El sistema NO falla
- Los correos se loggean en consola
- Puedes ver el contenido del correo en los logs

```bash
# Ver logs del correo en desarrollo
docker compose logs celery-worker -f | grep "EMAIL MOCK"
```

## 🧪 Pruebas

### 1. Crear Incapacidad desde Frontend

Desde el portal externo (`http://localhost:3000/radicar`):
1. Completar wizard de radicación
2. Ingresar email del solicitante
3. Radicar incapacidad
4. Verificar respuesta inmediata
5. Esperar 5-10 segundos
6. **Revisar correo del solicitante**

### 2. Prueba Manual con curl

```bash
# 1. Crear incapacidad (ajustar IDs según tu BD)
curl -X POST "http://localhost:8010/api/v1/incapacidades" \
  -H "Content-Type: application/json" \
  -d '{
    "tipo": "ARL",
    "empleado_id": "UUID_EMPLEADO",
    "empresa_id": "UUID_EMPRESA",
    "solicitante_id": "UUID_SOLICITANTE",
    "fecha_inicio": "2026-01-29",
    "fecha_fin": "2026-02-10",
    "diagnostico_cie10": "S06.0",
    "descripcion_diagnostico": "Conmoción cerebral",
    "nombre_medico": "Dr. Juan Pérez",
    "registro_medico": "RM-12345",
    "ips": "IPS Salud Total",
    "eps": "EPS Sanitas",
    "valor_total": 500000
  }'

# 2. Verificar logs
docker compose logs celery-worker -f

# Deberías ver:
# [CELERY] Iniciando radicación automática para incapacidad ...
# [CELERY] Incapacidad ... radicada exitosamente
# [CELERY] Enviando notificación por correo a ...
# [EMAIL] Enviando notificación de radicación ... a ...
# [EMAIL] Notificación enviada exitosamente a ...
```

### 3. Verificar en Flower (Monitor Celery)

```bash
# Acceder a Flower
open http://localhost:5565

# Ver:
# - Tareas ejecutadas
# - Estado de cada tarea
# - Tiempos de ejecución
# - Errores (si los hay)
```

## 📊 Monitoreo

### Logs de Celery Worker

```bash
# Todos los logs
docker compose logs celery-worker -f

# Solo emails
docker compose logs celery-worker -f | grep EMAIL

# Solo radicaciones
docker compose logs celery-worker -f | grep CELERY
```

### Logs del API

```bash
docker compose logs api -f | grep "Tarea de radicación"
```

## 🎨 Personalización del Template

Editar `app/templates/email/incapacidad_radicada.html`:

```html
<!-- Cambiar colores del gradiente -->
<div class="header" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">

<!-- Cambiar URL del frontend -->
'url_consulta': f"https://tudominio.com/consultar?numero={numero_radicacion}"

<!-- Agregar logo -->
<img src="https://tudominio.com/logo.png" alt="Logo" style="max-width: 200px;">
```

## 🔐 Seguridad

### Datos Sensibles
- ❌ NO se incluyen valores monetarios en el correo
- ❌ NO se incluyen datos bancarios
- ❌ NO se incluyen IDs internos
- ✅ Solo información necesaria para el seguimiento

### SMTP
- ✅ Usar TLS/SSL en producción
- ✅ Nunca commitear credenciales SMTP
- ✅ Usar variables de entorno
- ✅ Rotar contraseñas periódicamente

## 🐛 Troubleshooting

### El correo no llega

1. **Verificar configuración SMTP**:
   ```bash
   docker compose exec api python -c "from app.core.config import settings; print(f'SMTP: {settings.SMTP_USER}')"
   ```

2. **Verificar logs de error**:
   ```bash
   docker compose logs celery-worker | grep "Error SMTP"
   ```

3. **Probar conexión SMTP**:
   ```python
   # En el contenedor API
   docker compose exec api python
   
   >>> from app.core.email import email_service
   >>> email_service.send_email(
   ...     to="tu-email@gmail.com",
   ...     subject="Test",
   ...     html_body="<h1>Test</h1>"
   ... )
   ```

### La tarea no se ejecuta

1. **Verificar worker activo**:
   ```bash
   docker compose ps celery-worker
   # Debe estar "Up"
   ```

2. **Verificar tarea registrada**:
   ```bash
   docker compose logs celery-worker | grep send_incapacidad_radicada_email
   ```

3. **Reiniciar worker**:
   ```bash
   docker compose restart celery-worker
   ```

### Correo en spam

- Configurar SPF, DKIM, DMARC en producción
- Usar servicio profesional (SendGrid, AWS SES, Mailgun)
- Calentar IP progresivamente

## 📈 Métricas

### Tareas a Monitorear

1. **Tasa de éxito de radicación**: >98%
2. **Tasa de envío de correos**: >95%
3. **Tiempo promedio de procesamiento**: <10 segundos
4. **Reintentos necesarios**: <5%

### Dashboard Flower

- Tasks succeeded/failed
- Task runtime
- Worker status
- Queue length

## 🚀 Próximos Pasos

### Mejoras Sugeridas

1. **Templates adicionales**:
   - Cambio de estado (EN_AUDITORIA → APROBADA)
   - Incapacidad rechazada
   - Solicitud de información adicional
   - Pago procesado

2. **Notificaciones multicanal**:
   - SMS (Twilio)
   - WhatsApp Business API
   - Push notifications

3. **Personalización avanzada**:
   - Logo de la empresa
   - Colores corporativos
   - Firmas personalizadas

4. **Analytics**:
   - Tasa de apertura (tracking pixel)
   - Clicks en botones
   - Tiempo de lectura

## 📞 Soporte

Si tienes problemas:
- Revisar logs: `docker compose logs -f celery-worker`
- Verificar Flower: http://localhost:5565
- Documentación Celery: https://docs.celeryq.dev

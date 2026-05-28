# Configuración de Puertos - Sistema de Incapacidades

Este documento detalla los puertos utilizados por el sistema para evitar conflictos con otros servicios en el servidor.

## Puertos Configurados

| Servicio | Puerto Host | Puerto Interno | Descripción |
|----------|-------------|----------------|-------------|
| **PostgreSQL** | `5442` | `5432` | Base de datos principal |
| **Redis** | `6389` | `6379` | Cache y result backend de Celery |
| **MinIO API** | `9010` | `9000` | Storage de documentos (S3-compatible) |
| **MinIO Console** | `9011` | `9001` | Interfaz web de MinIO |
| **RabbitMQ AMQP** | `5682` | `5672` | Message broker para Celery |
| **RabbitMQ Management** | `15682` | `15672` | Interfaz web de RabbitMQ |
| **FastAPI** | `8010` | `8000` | API REST principal |
| **Flower** | `5565` | `5555` | Monitor de tareas Celery |

## URLs de Acceso

### Aplicación Principal
- **API REST**: http://localhost:8010
- **API Docs (Swagger)**: http://localhost:8010/docs
- **API Docs (ReDoc)**: http://localhost:8010/redoc

### Herramientas de Administración
- **MinIO Console**: http://localhost:9011
  - Usuario: `minioadmin`
  - Contraseña: `minioadmin`

- **RabbitMQ Management**: http://localhost:15682
  - Usuario: `guest`
  - Contraseña: `guest`

- **Flower (Celery Monitor)**: http://localhost:5565

### Conexiones a Base de Datos
```bash
# Conexión PostgreSQL desde host
psql -h localhost -p 5442 -U postgres -d incapacidades

# Conexión Redis desde host
redis-cli -h localhost -p 6389
```

## Conexión desde la Aplicación

Las variables de entorno en `.env` deben usar los puertos **internos** cuando los servicios se conectan entre sí dentro de Docker:

```env
# Correcto - para comunicación entre contenedores
DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/incapacidades
REDIS_URL=redis://redis:6379/0
STORAGE_ENDPOINT=minio:9000
CELERY_BROKER_URL=amqp://guest:guest@rabbitmq:5672//

# Los puertos del host (5442, 6389, etc.) solo se usan para acceso externo
```

## Verificar Puertos Disponibles

Antes de iniciar los servicios, verifica que los puertos estén libres:

```bash
# Linux/Mac
netstat -tulpn | grep -E '5442|6389|9010|9011|5682|15682|8010|5565'

# O usando ss
ss -tulpn | grep -E '5442|6389|9010|9011|5682|15682|8010|5565'

# O usando lsof
lsof -i :5442
lsof -i :6389
lsof -i :9010
lsof -i :8010
```

## Modificar Puertos

Si algún puerto todavía presenta conflicto, edita `docker-compose.yml`:

```yaml
services:
  api:
    ports:
      - "PUERTO_HOST:8000"  # Cambia PUERTO_HOST al deseado
```

**Importante**: Solo modifica el puerto del **host** (lado izquierdo), nunca el puerto interno del contenedor (lado derecho).

## Firewall

Si usas firewall, asegúrate de abrir los puertos necesarios:

```bash
# UFW (Ubuntu/Debian)
sudo ufw allow 8010/tcp comment 'Incapacidades API'
sudo ufw allow 5442/tcp comment 'Incapacidades PostgreSQL'

# firewalld (RHEL/CentOS)
sudo firewall-cmd --permanent --add-port=8010/tcp
sudo firewall-cmd --permanent --add-port=5442/tcp
sudo firewall-cmd --reload
```

## Troubleshooting

### Error: "Port is already allocated"

Si al ejecutar `docker-compose up` aparece este error:

1. Verifica qué proceso usa el puerto:
   ```bash
   sudo lsof -i :PUERTO
   ```

2. Detén el servicio conflictivo o cambia el puerto en `docker-compose.yml`

3. Limpia contenedores huérfanos:
   ```bash
   docker-compose down
   docker ps -a | grep incapacidades
   ```

### Verificar Servicios Activos

```bash
# Ver todos los servicios corriendo
docker-compose ps

# Ver logs de un servicio específico
docker-compose logs -f api
docker-compose logs -f postgres
```

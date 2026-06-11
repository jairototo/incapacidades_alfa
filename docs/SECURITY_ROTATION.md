# Runbook de Rotación de Credenciales — Sistema Incapacidades

> **Estado**: Lectura obligatoria antes de cualquier despliegue en producción.
> Última actualización: 2026-06-11

---

## 1. Por qué es urgente

El archivo `apps/backend/.env` fue añadido al historial de git en el commit `000e3063`
y eliminado en el commit `999109b7`. El archivo ya no está en el árbol de trabajo,
**pero permanece visible en el historial** para cualquier persona con acceso al repositorio
(incluidos posibles clones anteriores).

Los valores que contenía ese archivo deben considerarse comprometidos y deben rotarse
antes de cualquier despliegue en producción, independientemente de cualquier otra acción.

---

## 2. Credenciales que deben rotarse

### Tabla de verificación

| # | Variable de entorno | Tipo de credencial | Servicio externo | Impacto de rotación | Rotado |
|---|--------------------|--------------------|------------------|---------------------|--------|
| 1 | `SECRET_KEY` | Clave de firma JWT (HS256) | Interno — compartido con Laravel | Invalida **todos** los JWT activos; coordinar con el equipo Laravel antes de rotar | ☐ |
| 2 | `SMTP_USER` | Usuario SMTP | Mailtrap (u otro proveedor SMTP) | Correos salientes fallan hasta actualizar | ☐ |
| 3 | `SMTP_PASSWORD` | Contraseña SMTP | Mailtrap (u otro proveedor SMTP) | Ídem anterior | ☐ |
| 4 | `MINIO_ROOT_USER` | Usuario raíz MinIO | MinIO (instancia propia) | Acceso a almacenamiento de objetos; sincronizar con `STORAGE_ACCESS_KEY` en `.env` | ☐ |
| 5 | `MINIO_ROOT_PASSWORD` | Contraseña raíz MinIO | MinIO (instancia propia) | Ídem anterior; sincronizar con `STORAGE_SECRET_KEY` en `.env` | ☐ |
| 6 | `POSTGRES_PASSWORD` | Contraseña PostgreSQL | PostgreSQL | Conexiones a la base de datos fallan; también actualizar `DATABASE_URL` | ☐ |
| 7 | `API_RRHH_API_KEY` | API key del sistema de RRHH | API externa de RRHH | Solo si el valor llegó a tener un secreto real; verificar con el proveedor | ☐ |

---

## 3. Cómo rotar cada credencial

### 3.1 `SECRET_KEY` (Clave JWT)

**Precaución**: Esta clave es compartida con el sistema Laravel a través del «JWT Bridge»
(variable `JWT_SECRET` en Laravel). Rotar sin coordinar causará que todos los tokens
activos sean inválidos de inmediato y los usuarios serán desconectados.

**Pasos**:
1. Coordinar una ventana de mantenimiento con el equipo Laravel.
2. Generar un nuevo valor de al menos 64 caracteres aleatorios:
   ```bash
   python3 -c "import secrets; print(secrets.token_hex(64))"
   ```
3. Actualizar `SECRET_KEY` en el `.env` de producción del backend.
4. Actualizar `JWT_SECRET` en la configuración de producción de Laravel.
5. Reiniciar ambos servicios en la misma ventana de mantenimiento.

### 3.2 `SMTP_USER` y `SMTP_PASSWORD`

1. Acceder al panel de Mailtrap (o el proveedor SMTP configurado en producción).
2. Revocar las credenciales actuales y generar nuevas.
3. Actualizar `SMTP_USER` y `SMTP_PASSWORD` en el `.env` de producción.
4. Verificar envío de correo con una prueba manual.

### 3.3 `MINIO_ROOT_USER` y `MINIO_ROOT_PASSWORD`

1. Acceder a la consola de administración de MinIO.
2. Cambiar las credenciales del usuario raíz.
3. Actualizar en el `.env` de producción:
   - `MINIO_ROOT_USER` / `MINIO_ROOT_PASSWORD` (usados por docker-compose)
   - `STORAGE_ACCESS_KEY` / `STORAGE_SECRET_KEY` (usados por la API FastAPI)
4. Reiniciar los servicios `minio` y `api`.

### 3.4 `POSTGRES_PASSWORD`

1. Conectarse al servidor PostgreSQL con privilegios de superusuario.
2. Cambiar la contraseña del usuario de la base de datos:
   ```sql
   ALTER USER nombre_usuario WITH PASSWORD 'nueva-contraseña-segura';
   ```
3. Actualizar `POSTGRES_PASSWORD` en el `.env` de producción.
4. Actualizar `DATABASE_URL` si contiene la contraseña embebida.
5. Reiniciar los servicios `api`, `celery-worker`, `celery-beat` y `flower`.

### 3.5 `API_RRHH_API_KEY`

1. Contactar al proveedor de la API de RRHH y solicitar la revocación de la clave anterior.
2. Obtener una nueva clave.
3. Actualizar `API_RRHH_API_KEY` en el `.env` de producción.

---

## 4. Reescritura de historial git (opcional)

Rotar las credenciales hace que los valores filtrados sean inútiles, incluso si
permanecen en el historial. Sin embargo, si el repositorio es público o si las
políticas de seguridad lo exigen, es posible eliminar los commits problemáticos del
historial.

**Herramientas disponibles**:
- [`git filter-repo`](https://github.com/newren/git-filter-repo) (recomendada)
- [BFG Repo Cleaner](https://rtyley.github.io/bfg-repo-cleaner/)

**Advertencias importantes**:
- Requiere un `git push --force` a todas las ramas afectadas.
- Todos los colaboradores deben clonar el repositorio de nuevo o hacer `git fetch --all` y rebasar.
- Los commits afectados obtendrán nuevos SHAs: referencias externas (PRs, issues) quedarán desconectadas.
- **Coordinar con todo el equipo antes de ejecutar**.

El commit con el archivo añadido es `000e3063` y el commit que lo elimina es `999109b7`.
La reescritura debe eliminar el archivo de todos los commits en ese rango.

---

## 5. Verificación final

Antes de dar por completada la rotación:

```bash
# Verificar conectividad de base de datos
curl -sf http://localhost:8010/api/v1/health

# Verificar que los JWT de Laravel son aceptados por FastAPI
# (hacer login desde el sistema interno y confirmar que no se recibe 401)

# Verificar que no hay credenciales del historial git expuestas activamente
# (este comando debe ajustarse a la ruta real del .env de producción)
cat /ruta/al/.env.produccion | grep -v "^#" | grep -v "^$"
```

---

## 6. Notas de arquitectura relevantes

- El secreto JWT es **compartido** entre Laravel y FastAPI. Ver `CLAUDE.md` sección
  «JWT Bridge» para el detalle del flujo de autenticación.
- Los valores por defecto en `docker-compose.yml` (ej. `minioadmin`, `guest`) están
  parametrizados como `${VAR:-valor_por_defecto}` — son seguros para desarrollo local
  pero **nunca deben usarse en producción**.
- El archivo `.env` de producción nunca debe commitearse al repositorio. El `.gitignore`
  ya lo excluye; verificar antes de cada push con `git status`.

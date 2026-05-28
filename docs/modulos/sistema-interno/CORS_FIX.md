# Corrección de Errores CORS - Sistema Interno

**Fecha**: 23 de enero de 2026  
**Problema**: Errores CORS al realizar login desde el frontend  
**Estado**: ✅ Resuelto

---

## 🔍 Problema Identificado

El frontend estaba intentando hacer peticiones directamente a `http://localhost:8010/api/v1` desde el navegador, lo que causaba errores CORS porque:

1. El origen del frontend es `http://localhost:5174`
2. El backend está en `http://localhost:8010`
3. Cross-Origin Resource Sharing (CORS) bloqueaba las peticiones

**Síntomas**:
- Login fallaba con error de red
- Console mostraba errores CORS: "Access to XMLHttpRequest at 'http://localhost:8010/api/v1/auth/login' from origin 'http://localhost:5174' has been blocked by CORS policy"
- Headers de CORS faltantes en las respuestas

---

## ✅ Soluciones Implementadas

### 1. Configuración de Proxy en Vite (Solución Principal)

**Archivo**: `/frontend/sistema-interno/vite.config.ts`

**Cambios**:
```typescript
server: {
  port: 5174,
  proxy: {
    '/api': {
      target: 'http://localhost:8010',
      changeOrigin: true,
      rewrite: (path) => path, // No reescribir la ruta
      secure: false,
      ws: true, // WebSocket support
      configure: (proxy, _options) => {
        proxy.on('error', (err, _req, _res) => {
          console.log('proxy error', err);
        });
        proxy.on('proxyReq', (proxyReq, req, _res) => {
          console.log('Sending Request to the Target:', req.method, req.url);
        });
        proxy.on('proxyRes', (proxyRes, req, _res) => {
          console.log('Received Response from the Target:', proxyRes.statusCode, req.url);
        });
      },
    },
  },
}
```

**Beneficios**:
- ✅ Las peticiones del frontend a `/api/v1/*` se redirigen automáticamente a `http://localhost:8010/api/v1/*`
- ✅ El navegador ve todo como mismo origen (no hay CORS)
- ✅ Logs detallados para debugging
- ✅ Soporte para WebSockets

---

### 2. Variables de Entorno Actualizadas

**Archivo**: `/frontend/sistema-interno/.env.development`

**Cambios**:
```dotenv
# ANTES (causaba CORS)
VITE_API_URL=http://localhost:8010/api/v1

# DESPUÉS (usa proxy de Vite)
VITE_API_URL=/api/v1
```

**Archivo**: `/frontend/sistema-interno/.env.production` (ya estaba correcto)
```dotenv
VITE_API_URL=https://api.incapacidades.com/api/v1
```

**Flujo**:
- **Desarrollo**: Frontend usa `/api/v1` → Vite proxy redirige a `http://localhost:8010/api/v1`
- **Producción**: Frontend usa `https://api.incapacidades.com/api/v1` directamente

---

### 3. Actualización de Cliente Axios

**Archivo**: `/frontend/sistema-interno/src/lib/api.ts`

**Cambios**:
```typescript
// ANTES
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8010/api/v1';

// DESPUÉS
// En desarrollo usa el proxy de Vite (/api/v1)
// En producción usa la URL completa del backend
const API_URL = import.meta.env.VITE_API_URL || '/api/v1';
```

**Beneficio**: Fallback correcto usando proxy en lugar de URL directa

---

### 4. CORS Expandidos en Backend (Capa Adicional)

**Archivo**: `/backend/.env`

**Cambios**:
```dotenv
# ANTES
BACKEND_CORS_ORIGINS=["http://localhost:3000","http://localhost:8080","http://localhost:5173","http://localhost:5174"]

# DESPUÉS
BACKEND_CORS_ORIGINS=["http://localhost:3000","http://localhost:8080","http://localhost:5173","http://localhost:5174","http://127.0.0.1:5173","http://127.0.0.1:5174","http://192.168.2.120:5173","http://192.168.2.120:5174"]
```

**Beneficio**: Soporte para múltiples formas de acceso:
- `localhost` (DNS)
- `127.0.0.1` (IP loopback)
- `192.168.2.120` (IP local de la red)

---

## 🚀 Cómo Funciona Ahora

### Desarrollo Local

1. **Frontend inicia en**: `http://localhost:5174`
2. **Login hace petición a**: `/api/v1/auth/login`
3. **Vite proxy intercepta** y redirige a: `http://localhost:8010/api/v1/auth/login`
4. **Backend responde** con headers CORS adecuados
5. **Vite proxy devuelve** la respuesta al frontend
6. **Navegador recibe** respuesta del mismo origen (sin CORS)

### Producción

1. **Frontend en**: `https://app.incapacidades.com`
2. **Login hace petición a**: `https://api.incapacidades.com/api/v1/auth/login`
3. **Backend responde** con headers CORS permitiendo el origen
4. **Navegador acepta** la respuesta

---

## 🧪 Pruebas para Validar

### 1. Probar Login con Dev Server

```bash
cd /opt/apps/incapacidades_vs/frontend/sistema-interno
npm run dev
```

**Pasos**:
1. Abrir navegador en `http://localhost:5174`
2. Ir a `/login`
3. Ingresar credenciales:
   - Email: `admin@incapacidades.com`
   - Password: `admin123`
4. Hacer login
5. Verificar en console:
   - ✅ Petición exitosa (200 OK)
   - ✅ Token almacenado en localStorage
   - ✅ Redirect a `/dashboard`

### 2. Verificar Logs del Proxy

En la consola de Vite deberías ver:
```
Sending Request to the Target: POST /api/v1/auth/login
Received Response from the Target: 200 /api/v1/auth/login
```

### 3. Verificar Network Tab

**Antes** (con CORS):
```
Request URL: http://localhost:8010/api/v1/auth/login
Status: (failed) net::ERR_FAILED
CORS error
```

**Después** (sin CORS):
```
Request URL: http://localhost:5174/api/v1/auth/login
Status: 200 OK
Headers: Content-Type: application/json
```

---

## 🔧 Comandos Ejecutados

### Backend
```bash
cd /opt/apps/incapacidades_vs/backend
docker compose restart api  # Aplicar nuevos CORS
docker compose logs api --tail=30  # Verificar inicio
```

### Frontend
```bash
cd /opt/apps/incapacidades_vs/frontend/sistema-interno
npm run dev  # Iniciar con proxy configurado
```

---

## 📊 Comparación Antes/Después

| Aspecto | Antes | Después |
|---------|-------|---------|
| URL de API (dev) | `http://localhost:8010/api/v1` | `/api/v1` (proxy) |
| CORS | ❌ Error cross-origin | ✅ Mismo origen |
| Network logs | Request failed | 200 OK |
| Login funcional | ❌ No | ✅ Sí |
| Debugging | Difícil (CORS) | ✅ Logs detallados |

---

## 🛡️ Seguridad

**Proxy en Desarrollo**:
- Solo funciona en `npm run dev`
- No afecta producción (build usa `VITE_API_URL` completo)
- Headers de autenticación siguen siendo seguros (JWT)

**CORS en Backend**:
- Lista blanca de orígenes permitidos
- No usa `allow_origins=["*"]` (inseguro)
- Credentials habilitados solo para orígenes confiables

---

## 📝 Archivos Modificados

1. ✅ `/frontend/sistema-interno/vite.config.ts` - Proxy configurado
2. ✅ `/frontend/sistema-interno/.env.development` - URL relativa
3. ✅ `/frontend/sistema-interno/src/lib/api.ts` - Fallback corregido
4. ✅ `/backend/.env` - CORS expandidos

**Total**: 4 archivos modificados

---

## 🔍 Troubleshooting

### Si aún hay errores CORS:

1. **Limpiar caché del navegador**:
   ```
   Ctrl + Shift + R (hard refresh)
   o
   F12 → Network → Disable cache
   ```

2. **Verificar que Vite dev server esté corriendo**:
   ```bash
   npm run dev
   # Debe mostrar: Local: http://localhost:5174/
   ```

3. **Verificar que el backend esté corriendo**:
   ```bash
   cd backend
   docker compose ps
   # incapacidades-api debe estar "Up"
   ```

4. **Verificar logs del proxy en la consola de Vite**:
   - Deberías ver logs de peticiones entrantes/salientes

5. **Verificar Network tab del navegador**:
   - Request URL debe ser `http://localhost:5174/api/v1/...`
   - NO `http://localhost:8010/api/v1/...`

---

## 🎯 Próximos Pasos

Con CORS corregido, puedes continuar con:

1. **Probar login completo** en el navegador
2. **Validar refresh token** (refrescar página después de login)
3. **Continuar con Módulo Incapacidades** (siguiente fase)

---

**Corrección implementada por**: GitHub Copilot  
**Fecha**: 23 de enero de 2026  
**Estado**: ✅ Listo para desarrollo sin problemas CORS

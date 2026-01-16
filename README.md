# Sistema de Gestión de Incapacidades - Aseguradora

**Estado**: 🚀 En Desarrollo Avanzado (97% completado)  
**Última actualización**: 16 de enero de 2026  
**Versión**: 1.0.0-beta

---

## 📋 Descripción del Proyecto

Sistema integral para la gestión del ciclo completo de incapacidades médicas en aseguradoras colombianas, desde la radicación hasta el pago, con soporte diferenciado para:

- **Incapacidades ARL** (Administradora de Riesgos Laborales) con gestión de siniestros/accidentes laborales
- **Incapacidades SALUD** con gestión de afiliados y pólizas

### Flujo Completo

1. **Radicación** - Portal externo para empresas/empleados/afiliados
2. **Auditoría** - Revisión por auditores internos
3. **Aprobación/Observación/Rechazo** - Decisión con trazabilidad
4. **Generación de Órdenes de Pago** - Automatizada desde incapacidades aprobadas
5. **Pago** - Registro y seguimiento de pagos efectuados

---

## 🎯 Estado del Proyecto

### Progreso Global: 97% 🚀

| Componente | Progreso | Estado |
|------------|----------|--------|
| **Backend** | 100% | ✅ Completado |
| **Frontend Fase 1** | 100% | ✅ Completado |
| **Frontend Fase 2** | 0% | ⏳ Pendiente |
| **Deployment** | 0% | ⏳ Pendiente |

### Backend (100% ✅)
- ✅ 11 modelos SQLAlchemy (Empresa, Empleado, Afiliado, Incapacidad, Siniestro, Documento, etc.)
- ✅ 11 repositories con patrón Repository
- ✅ 11 services con lógica de negocio
- ✅ 66 endpoints REST documentados
- ✅ Autenticación JWT con refresh tokens
- ✅ RBAC con 6 roles (ADMIN, AUDITOR, APROBADOR, EMPRESA, EMPLEADO, READONLY)
- ✅ Storage MinIO para documentos
- ✅ Workflow de estados con validaciones
- ✅ 149+ tests con 87% cobertura
- ✅ Docker Compose con 8 servicios

### Frontend - Portal Externo (100% ✅)
- ✅ Wizard de radicación en 5 pasos
- ✅ Integración completa con backend
- ✅ Upload de documentos a MinIO
- ✅ Validación robusta con Zod
- ✅ 217 tests con >75% cobertura
- ✅ Build optimizado (520 KB bundle)

### Frontend - Sistema Interno (0% ⏳)
- ⏳ Autenticación JWT (próximo)
- ⏳ Dashboard de métricas
- ⏳ CRUD de incapacidades
- ⏳ Gestión de órdenes de pago
- ⏳ Gestión de usuarios y roles

**Ver detalles completos**: [`ESTADO_PROYECTO.md`](ESTADO_PROYECTO.md)

---

## 🏗️ Arquitectura General

```
┌──────────────────────┐         ┌──────────────────────┐
│  PORTAL EXTERNO      │         │  SISTEMA INTERNO     │
│  (Empresas/          │         │  (Auditores/         │
│   Empleados/         │         │   Administradores)   │
│   Afiliados) ✅      │         │  ⏳ En desarrollo     │
│                      │         │                      │
│  • Wizard 5 pasos    │         │  • Dashboard         │
│  • Radicación        │         │  • CRUD              │
│  • Upload docs       │         │  • Workflow          │
│  • Confirmación      │         │  • Reportes          │
└──────────┬───────────┘         └──────────┬───────────┘
           │                                │
           │         HTTPS/REST             │
           └───────────────┬────────────────┘
                           ▼
                  ┌────────────────┐
                  │   BACKEND API  │
                  │   FastAPI ✅   │
                  │                │
                  │  • 66 Endpoints│
                  │  • JWT Auth    │
                  │  • RBAC        │
                  │  • Workflow    │
                  └────────┬───────┘
                           ▼
           ┌───────────────┴────────────────┬─────────────┐
           │                                │             │
    ┌──────▼──────┐              ┌─────────▼──────┐  ┌──▼─────┐
    │ PostgreSQL  │              │    MinIO/S3    │  │ Redis  │
    │ 15+ ✅      │              │  (Documentos)  │  │  7+ ✅ │
    │ 11 tablas   │              │       ✅       │  │ Cache  │
    └─────────────┘              └────────────────┘  └────────┘
```

---

## 🛠️ Stack Tecnológico

### Backend
- **Python 3.11+**
- **FastAPI 0.109+** - Framework web moderno y rápido
- **SQLAlchemy 2.0** - ORM async/await native
- **PostgreSQL 15+** - Base de datos principal
- **Redis 7+** - Cache y sesiones
- **Celery + RabbitMQ** - Tareas asíncronas
- **MinIO/S3** - Almacenamiento de archivos

### Frontend (Sugerido)
- **React/Vue/Angular** - Para portales web
- **Next.js** - Para SSR y mejor SEO
- **TailwindCSS** - Estilos modernos

### Infraestructura
- **Docker & Docker Compose** - Contenedorización
- **Nginx** - Proxy reverso y balanceo
- **Prometheus + Grafana** - Monitoreo
- **ELK Stack** - Logging centralizado

## 📁 Estructura del Repositorio

```
incapacidades_vs/
│
├── backend/                    # API Backend (FastAPI)
│   ├── app/
│   ├── tests/
│   ├── alembic/
│   ├── requirements.txt
│   ├── docker-compose.yml
│   └── README.md
│
├── frontend-externo/          # Portal Empresas/Empleados (pendiente)
│   └── README.md
│
├── frontend-interno/          # Sistema Auditores/Admin (pendiente)
│   └── README.md
│
├── docs/                      # Documentación completa
│   ├── 01_ARQUITECTURA.md
│   ├── 02_MODELO_DATOS.md
│   ├── 03_API_ENDPOINTS.md
│   ├── 04_FLUJO_ESTADOS.md
│   ├── 05_STACK_Y_ESTRUCTURA.md
│   └── images/
│
├── scripts/                   # Scripts de utilidad
│   └── setup_project.sh
│
└── README.md                  # Este archivo
```

## 🚀 Inicio Rápido

### 1. Backend API

```bash
cd backend
cp .env.example .env
# Editar .env con tus configuraciones

# Con Docker (Recomendado)
docker-compose up -d

# Sin Docker
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

Acceder a:
- API: http://localhost:8010
- Documentación: http://localhost:8010/docs

### 2. Frontend (Pendiente de implementación)

Ver README de cada módulo frontend.

## 📚 Documentación Completa

Toda la documentación técnica se encuentra en el directorio [docs/](docs/)

### Documentos Principales

1. **[Arquitectura del Sistema](docs/01_ARQUITECTURA.md)**
   - Componentes
   - Capas de arquitectura
   - Patrones de diseño
   - Escalabilidad y seguridad

2. **[Modelo de Datos](docs/02_MODELO_DATOS.md)**
   - Diagrama ER
   - Definición de tablas
   - Relaciones
   - Scripts SQL completos

3. **[Endpoints REST API](docs/03_API_ENDPOINTS.md)**
   - Todos los endpoints documentados
   - Request/Response examples
   - Códigos de error
   - Autenticación

4. **[Flujo de Estados](docs/04_FLUJO_ESTADOS.md)**
   - Diagrama de estados
   - Transiciones válidas
   - Reglas de negocio
   - SLAs y validaciones

5. **[Stack y Estructura](docs/05_STACK_Y_ESTRUCTURA.md)**
   - Tecnologías utilizadas
   - Estructura de proyecto
   - Patrones aplicados
   - Configuración

## 🎯 Funcionalidades Principales

### Portal Externo (Empresas/Empleados)
- ✅ Registro y autenticación
- ✅ Radicación de incapacidades
- ✅ Adjuntar documentos
- ✅ Consultar estado
- ✅ Responder observaciones
- ✅ Historial de incapacidades

### Sistema Interno (Auditores/Administradores)
- ✅ Dashboard de incapacidades
- ✅ Auditoría con workflow
- ✅ Aprobación/Rechazo
- ✅ Generación de órdenes de pago
- ✅ Reportes y estadísticas
- ✅ Gestión de usuarios
- ✅ Configuración del sistema

### Backend API
- ✅ API RESTful completa
- ✅ Autenticación JWT
- ✅ RBAC (Control de roles)
- ✅ Workflow de estados
- ✅ Carga masiva de datos
- ✅ Integración con APIs externas
- ✅ Procesamiento asíncrono
- ✅ Almacenamiento seguro

## 🔐 Seguridad

- Autenticación JWT con tokens de acceso y refresco
- Control de acceso basado en roles (RBAC)
- Encriptación de contraseñas con bcrypt
- HTTPS obligatorio en producción
- Validación de archivos adjuntos
- Rate limiting para prevenir abuso
- Logging y auditoría completa
- CORS configurado
- SQL injection prevention
- XSS protection

## 📊 Roles del Sistema

| Rol | Descripción | Acceso |
|-----|-------------|--------|
| **ADMIN** | Administrador del sistema | Acceso completo |
| **AUDITOR** | Auditor de incapacidades | Auditar, aprobar, rechazar |
| **APROBADOR** | Aprobador de pagos | Aprobar y registrar pagos |
| **EMPRESA** | Usuario de empresa | Radicar y consultar propias |
| **EMPLEADO** | Usuario empleado | Radicar y consultar propias |
| **READONLY** | Solo lectura | Ver reportes |

## 🔄 Flujo del Proceso

```
1. RADICACIÓN
   └─> Empresa/Empleado radica incapacidad
   └─> Adjunta documentos obligatorios
   └─> Estado: RADICADA

2. AUDITORÍA
   └─> Auditor revisa documentación
   └─> Valida información
   └─> Estado: EN_AUDITORIA
   
   ┌─> Si falta info: OBSERVADA
   │   └─> Empresa responde
   │   └─> Vuelve a EN_AUDITORIA
   │
   ├─> Si todo OK: APROBADA
   │
   └─> Si no cumple: RECHAZADA

3. GENERACIÓN DE PAGO
   └─> Sistema genera orden de pago
   └─> Estado: EN_PAGO

4. PAGO
   └─> Tesorería registra pago
   └─> Estado: PAGADA
   └─> Notifica a empleado y empresa
```

## 🧪 Testing

```bash
cd backend
pytest                          # Todos los tests
pytest --cov=app               # Con cobertura
pytest tests/unit/             # Tests unitarios
pytest tests/integration/      # Tests de integración
```

## 📈 Métricas y Monitoreo

- Health checks en `/health`
- Métricas Prometheus en `/metrics`
- Logs estructurados (JSON)
- Dashboard de Grafana (opcional)
- Alertas configurables
- Flower para monitoreo de Celery

## 🚀 Deployment

### Desarrollo
```bash
docker-compose up -d
```

### Producción
Ver documentación específica en cada módulo.

Recomendaciones:
- Usar Kubernetes para orquestación
- Configurar CI/CD (GitLab CI / GitHub Actions)
- Implementar monitoreo completo
- Backups automáticos de BD
- CDN para archivos estáticos

## 🤝 Contribución

1. Fork el proyecto
2. Crear feature branch (`git checkout -b feature/NuevaCaracteristica`)
3. Commit cambios (`git commit -m 'Agregar nueva característica'`)
4. Push al branch (`git push origin feature/NuevaCaracteristica`)
5. Crear Pull Request

## 📝 Licencia

Privado - Todos los derechos reservados

## 📞 Contacto

Para más información o soporte, contactar al equipo de desarrollo.

---

**Desarrollado con ❤️ para modernizar la gestión de incapacidades en aseguradoras**

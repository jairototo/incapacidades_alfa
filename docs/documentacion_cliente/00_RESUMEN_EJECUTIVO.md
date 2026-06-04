# RESUMEN EJECUTIVO

## Sistema de Gestión de Incapacidades Médicas

**Versión**: 1.0  
**Fecha**: Junio 2026  
**Estado**: Fase 1 Completa, Fase 2 En Desarrollo  
**Cliente**: Seguros Bolívar / Seguros Alfa

---

## 1. DESCRIPCIÓN DEL SISTEMA

El **Sistema de Gestión de Incapacidades Médicas** es una plataforma integral desarrollada para automatizar y optimizar el ciclo completo de gestión de incapacidades médicas, desde la radicación inicial hasta el pago final.

El sistema está diseñado específicamente para aseguradoras que operan en el mercado colombiano, con soporte para:

- **Incapacidades ARL** (Administradora de Riesgos Laborales)
- **Incapacidades SALUD** (Seguros de Salud)

---

## 2. PROPÓSITO Y PROBLEMA RESUELTO

### Problema

Antes de esta solución, la gestión de incapacidades era:

- **Fragmentada**: Múltiples sistemas sin integración
- **Manual**: Procesos manuales propensos a errores
- **Ineficiente**: Ciclos de tramitación lentos
- **No auditable**: Falta de trazabilidad completa
- **Inconsistente**: Información dispersa y duplicada

### Solución

Este sistema proporciona:

✅ **Radicación centralizada** - Portal público 24/7 para radicación de incapacidades  
✅ **Auditoría automática** - Validaciones y análisis programado  
✅ **Aprobación workflow** - Proceso de aprobación controlado por roles  
✅ **Liquidación automática** - Cálculo de valores y generación de órdenes de pago  
✅ **Trazabilidad completa** - Auditoría exhaustiva de cada transición  
✅ **Gestión de documentos** - Almacenamiento seguro y validado de soportes  

---

## 3. MÓDULOS Y FUNCIONALIDADES PRINCIPALES

### 3.1 Portal de Radicación Pública (100% Completo)

**Usuarios**: Solicitantes (empresas, empleados, asegurados)

**Funciones**:
- Radicación de incapacidades ARL en 6 pasos
- Radicación de incapacidades SALUD
- Consulta pública del estado de radicaciones
- Carga de documentos (incapacidad médica, historia clínica, soportes)
- Validación automática de datos
- Generación de número de radicado

**Tecnología**: React 19, TypeScript, TailwindCSS v4, Vite  
**Tests**: 358 tests, 75%+ cobertura

### 3.2 Sistema Interno de Auditoría y Aprobación (En Desarrollo)

**Usuarios**: Auditores, Aprobadores, Administradores

**Funciones**:
- Dashboard de métricas en tiempo real
- Módulo de auditoría médica
- Validación de documentación
- Detección de inconsistencias
- Módulo de aprobación/rechazo
- Gestión de órdenes de pago
- Reportes y análisis
- Administración de catálogos

**Tecnología**: React 19, TypeScript, TailwindCSS v3, Vitest  

### 3.3 Backend API (100% Completo)

**Capacidades**:
- 200+ endpoints RESTful
- Autenticación JWT
- Control de acceso por roles (6 roles)
- Validación exhaustiva de datos
- Almacenamiento de documentos en MinIO/S3
- Tareas asíncronas con Celery
- Auditoría exhaustiva de operaciones
- Base de datos transaccional

**Tecnología**: FastAPI, SQLAlchemy 2.0 async, PostgreSQL  
**Tests**: 87% cobertura, integración completa

---

## 4. CICLO DE VIDA DE UNA INCAPACIDAD

```
RADICADA (Portal Público)
    ↓
EN_AUDITORIA (Auditor valida documentación y diagnóstico)
    ↓
├─ OBSERVADA (Requiere correcciones) → Retorna a solicitante
│  └─ Solicitante envía correcciones → EN_AUDITORIA (ciclo)
│
├─ APROBADA (Auditor aprueba) → Pasa a Aprobador
│  └─ Aprobador genera orden de pago
│     ├─ EN_PAGO (En proceso de pago)
│     └─ PAGADA (Pagado exitosamente)
│
└─ RECHAZADA (Auditor rechaza con justificación)
   └─ Fin del trámite
```

**Tiempo promedio**: 3-5 días hábiles  
**SLA de auditoría**: 48 horas  
**Trazabilidad**: 100% de cambios auditados

---

## 5. ACTORES Y ROLES

| Rol | Descripción | Funciones |
|-----|-------------|-----------|
| **SOLICITANTE** | Empresas o empleados | Radicar incapacidades, subir documentos, consultar estado |
| **AUDITOR** | Personal ARL/Aseguradora | Validar documentación, determinar origen, aprobar/rechazar |
| **APROBADOR** | Supervisor | Aprobar decisiones de auditoría, generar órdenes de pago |
| **ADMIN** | Administrador sistema | Gestionar usuarios, catálogos, configuraciones |
| **EMPRESA** | Rol asignado a empresas | Acceso limitado a radicaciones propias |
| **EMPLEADO** | Rol asignado a empleados | Consultar propias incapacidades |

---

## 6. ENTIDADES DE DATOS CLAVE

| Entidad | Propósito | Registros |
|---------|----------|-----------|
| **Usuario** | Autenticación y autorización | 50+ (estimado) |
| **Empresa** | Información de empresas ARL | 10+ |
| **Empleado** | Personal de empresas | 100+ |
| **Afiliado** | Asegurados con pólizas | 1000+ (estimado) |
| **Incapacidad** | Solicitudes de incapacidad | Volumen anual |
| **Siniestro** | Accidentes laborales ARL | Relacionados |
| **Documento** | Archivos adjuntos | Por incapacidad |
| **OrdenPago** | Órdenes de pago generadas | Relacionadas |
| **HistorialEstado** | Auditoría de cambios | Todos los cambios |
| **AuditoriaLog** | Log exhaustivo del sistema | Todas las acciones |

---

## 7. ARQUITECTURA TÉCNICA

### 7.1 Stack Tecnológico

#### Backend
- **Framework**: FastAPI 0.109+
- **ORM**: SQLAlchemy 2.0 (async)
- **Base de Datos**: PostgreSQL 15+
- **Cache/Sesiones**: Redis 7+
- **Storage**: MinIO/S3 compatible
- **Task Queue**: Celery + RabbitMQ
- **Auth**: JWT (HS256)

#### Frontend - Portal Público
- **Framework**: React 19
- **Build**: Vite 5
- **Styling**: TailwindCSS 4.1
- **Formularios**: React Hook Form + Zod v4
- **HTTP**: Axios
- **Testing**: Vitest + Testing Library

#### Frontend - Sistema Interno
- **Framework**: React 19
- **Styling**: TailwindCSS 3.4
- **Validación**: Zod v3
- **Estado**: Zustand
- **Testing**: Vitest

#### Infraestructura
- **Containerización**: Docker 24+
- **Orquestación**: Docker Compose (8 servicios)
- **Proxy**: Nginx 1.25+
- **CI/CD**: GitHub Actions

### 7.2 Componentes Principales

```
┌─────────────────────────────────────────────────┐
│         CLIENTE (Navegador)                     │
│  ┌─────────────────┐  ┌──────────────────┐    │
│  │ Portal Público  │  │ Sistema Interno  │    │
│  │ (React 19)      │  │ (React 19)       │    │
│  └────────┬────────┘  └────────┬─────────┘    │
└──────────┼──────────────────────┼──────────────┘
           │                      │
           │     HTTPS/JWT        │
           ├──────────────────────┤
           ↓                      ↓
┌─────────────────────────────────────────────────┐
│         API GATEWAY (Nginx)                     │
└──────────────┬────────────────────────────────┘
               │
               ↓
┌─────────────────────────────────────────────────┐
│      BACKEND (FastAPI)                          │
│  ┌─────────────────────────────────────┐       │
│  │  Controllers/Endpoints              │       │
│  │  ├─ Auth                            │       │
│  │  ├─ Incapacidades                   │       │
│  │  ├─ Siniestros                      │       │
│  │  ├─ Auditoría                       │       │
│  │  ├─ Documentos                      │       │
│  │  └─ Reportes                        │       │
│  └──────┬────────────────────────────┬─┘       │
│         │                            │         │
│    ┌────┴─────────────────────────┬─┴─────┐   │
│    ↓                              ↓       ↓   │
│ ┌────────────┐  ┌──────────┐  ┌──────────┐   │
│ │ Services   │  │ Celery   │  │ MinIO    │   │
│ │ (Business  │  │ Tasks    │  │ Storage  │   │
│ │ Logic)     │  │          │  │          │   │
│ └──────┬─────┘  └────┬─────┘  └──────────┘   │
│        │             │                       │
│    ┌───┴─────────────┴───┐                   │
│    ↓                     ↓                   │
│  ┌──────────────┐  ┌──────────────────┐    │
│  │ Repositories │  │ RabbitMQ/Redis   │    │
│  │ (Data Access)│  │ (Queues/Cache)   │    │
│  └──────┬───────┘  └──────────────────┘    │
│         │                                  │
└─────────┼──────────────────────────────────┘
          │
          ↓
┌─────────────────────────────────────────────────┐
│      PostgreSQL Database                        │
│  ├─ usuario                                    │
│  ├─ incapacidad                               │
│  ├─ siniestro                                 │
│  ├─ documento                                 │
│  ├─ orden_pago                                │
│  ├─ auditoria_log                             │
│  └─ historial_estado                          │
└─────────────────────────────────────────────────┘
```

---

## 8. SEGURIDAD

- **Autenticación**: JWT HS256 con refresh tokens
- **Autorización**: RBAC (Role-Based Access Control) - 6 roles
- **Encriptación**: HTTPS, datos sensibles encriptados
- **Almacenamiento**: Documentos validados y hasheados (MD5/SHA256)
- **Auditoría**: Trazabilidad completa de operaciones
- **Rate Limiting**: Protección contra abuso
- **Validación**: Input validation exhaustiva (40+ validaciones por módulo)

---

## 9. ESTADO Y PRÓXIMOS PASOS

### Completado (Fase 1)
- ✅ Backend API completamente funcional
- ✅ Portal público de radicación
- ✅ Módulo de consulta pública
- ✅ Autenticación JWT
- ✅ Almacenamiento de documentos
- ✅ Tests exhaustivos (87% backend, 75%+ frontend)

### En Desarrollo (Fase 2)
- 🔄 Sistema interno para auditores (70% completo)
- 🔄 Dashboards y reportes
- 🔄 Integración de catálogos
- 🔄 Notificaciones por email

### Próximo (Fase 3)
- ⏳ Storybook para componentes
- ⏳ Reportes avanzados
- ⏳ Integración con terceros
- ⏳ Optimización de performance

---

## 10. MÉTRICAS DE CALIDAD

| Métrica | Valor |
|---------|-------|
| **Test Coverage (Backend)** | 87% |
| **Test Coverage (Frontend)** | 75%+ |
| **Lines of Code (Backend)** | ~19,000 |
| **Lines of Code (Frontend)** | ~2,000 |
| **Endpoints Implementados** | 200+ |
| **Componentes React** | 80+ |
| **Tablas de BD** | 17 |
| **Migraciones** | 14 |
| **Documentación** | 40+ archivos |

---

## 11. REQUERIMIENTOS PARA OPERACIÓN

### Hardware Mínimo
- **Servidor**: 2 CPUs, 4GB RAM
- **Almacenamiento**: 50GB (escalable)
- **Base de Datos**: PostgreSQL 15+
- **Cache**: Redis 7+
- **Storage**: MinIO compatible con S3

### Software Requerido
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+
- Docker 24+ (recomendado)

### Configuración
- Variables de entorno: 25+ configurables
- Secretos: JWT_SECRET, Database credentials
- Certificados SSL/TLS: HTTPS requerido

---

## 12. SOPORTE Y MANTENIMIENTO

- **Logs Estructurados**: Loguru con niveles DEBUG/INFO/WARNING/ERROR
- **Monitoreo**: Endpoints de health check
- **Backup**: PostgreSQL + MinIO
- **Escalabilidad**: Diseño horizontal con Kubernetes (futuro)
- **CI/CD**: GitHub Actions automático
- **Actualizaciones**: Alembic migrations versionadas

---

## 13. CONCLUSIÓN

El Sistema de Gestión de Incapacidades es una solución moderna, escalable y segura que automatiza completamente el ciclo de vida de incapacidades médicas. Con arquitectura de capas limpias, exhaustiva auditoría y soporte para múltiples tipos de incapacidades (ARL/SALUD), proporciona la base sólida para una operación eficiente y segura de la gestión de incapacidades en la aseguradora.

---

**Contacto**: [equipo@segurosbolivar.com]  
**Documentación Completa**: Ver carpeta `/docs/`  
**Licencia**: [Según contrato con cliente]

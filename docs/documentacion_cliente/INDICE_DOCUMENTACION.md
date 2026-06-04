# ÍNDICE DE DOCUMENTACIÓN DEL SISTEMA

## Paquete de Documentación Completa

**Generado**: Junio 2026  
**Versión**: 1.0  
**Propósito**: Entrega técnica y funcional completa del Sistema de Gestión de Incapacidades

---

## ESTRUCTURA DE DOCUMENTACIÓN

### Documentos Estratégicos (Nivel Ejecutivo)

1. **00_RESUMEN_EJECUTIVO.md**
   - Descripción general del sistema
   - Módulos y funcionalidades
   - Ciclo de vida de incapacidades
   - Actores y roles
   - Arquitectura técnica
   - Métricas de calidad
   - **Audiencia**: Ejecutivos, stakeholders, gestión
   - **Tamaño**: ~14 KB

2. **INDICE_DOCUMENTACION.md** (este archivo)
   - Guía de navegación completa
   - Descripción de cada documento
   - Relaciones y referencias cruzadas
   - **Audiencia**: Todos los usuarios
   - **Tamaño**: ~8 KB

---

### Documentos de Negocio (Nivel Funcional)

3. **01_REGLAS_NEGOCIO.md**
   - 22 reglas de negocio documentadas
   - RN-001 a RN-022
   - Descripción, justificación, módulos afectados
   - Ciclo de vida de estados
   - Control de acceso
   - **Audiencia**: Product managers, analistas, auditores
   - **Tamaño**: ~24 KB
   - **Cobertura**: 100% de reglas implementadas o en desarrollo

4. **02_VALIDACIONES.md**
   - 54 validaciones documentadas
   - VAL001 a VAL054
   - Validaciones por categoría (documento, nombre, email, fecha, archivo, seguridad)
   - Flujo de validación
   - Matriz de validaciones por módulo
   - **Audiencia**: Desarrolladores, QA, auditores
   - **Tamaño**: ~17 KB
   - **Cobertura**: 100% de validaciones frontend + backend

---

### Documentos Técnicos (Nivel Arquitectura)

5. **03_ARQUITECTURA_SISTEMA.md** (por generar)
   - Diagrama de componentes
   - Diagrama de sequencia
   - Stack tecnológico
   - Flujos de integración
   - Deployment
   - **Audiencia**: Arquitectos, devops, desarrollo senior
   - **Tamaño**: ~15 KB

6. **04_API_ENDPOINTS.md** (por generar)
   - 200+ endpoints documentados
   - Método HTTP, ruta, parámetros
   - Autenticación y autorización
   - Ejemplos de request/response
   - Códigos de error
   - **Audiencia**: Desarrolladores frontend/backend, integradores
   - **Tamaño**: ~30 KB

7. **05_MODELO_DATOS.md** (por generar)
   - 17 tablas documentadas
   - Estructura columnas, tipos, constraints
   - Relaciones y cardinalidad
   - ER diagrams en Mermaid
   - Índices y optimizaciones
   - **Audiencia**: DBA, desarrolladores backend
   - **Tamaño**: ~20 KB

---

### Documentos de Usuarios (Nivel Funcional)

8. **06_HISTORIAS_USUARIO.md** (por generar)
   - 55+ historias de usuario
   - HU-001 a HU-055+
   - Formato: Como [rol] quiero [acción] para [beneficio]
   - Criterios de aceptación
   - Reglas de negocio relacionadas
   - **Audiencia**: Product managers, QA, desarrollo
   - **Tamaño**: ~25 KB

9. **07_CASOS_DE_USO.md** (por generar)
   - 20+ casos de uso
   - CU-001 a CU-020+
   - Actors, precondiciones, flujos, alternativas, excepciones
   - Diagramas UML/Mermaid
   - **Audiencia**: Analistas, desarrolladores, QA
   - **Tamaño**: ~20 KB

---

### Documentos de Referencia (Nivel Operacional)

10. **08_INVENTARIO_FUNCIONAL.md** (por generar)
    - Matriz de funcionalidades
    - Módulo | Funcionalidad | Descripción | Estado
    - Cubrimiento de módulos (Autenticación, Radicación, Consulta, Auditoría, Aprobación, Pago, Admin, Reportes)
    - **Audiencia**: Gestores, QA, soporte
    - **Tamaño**: ~12 KB

11. **09_MATRIZ_TRAZABILIDAD.md** (por generar)
    - Relacionar: Módulos ↔ Historias ↔ Reglas ↔ Tablas ↔ APIs ↔ Pantallas
    - Matriz de trazabilidad
    - Verificar cobertura completa
    - **Audiencia**: QA, auditores
    - **Tamaño**: ~15 KB

---

### Anexos y Referencias

12. **ANEXO_A_SKILLS_NEGOCIO.md** (por generar)
    - Integración de skills de /ai/skills/
    - Skill Radicador Público ARL
    - Skill Auditor ARL
    - Prompts y ejemplos
    - **Audiencia**: Auditores, especialistas
    - **Tamaño**: ~10 KB

13. **ANEXO_B_GLOSARIO.md** (por generar)
    - Definiciones de términos
    - Acrónimos: ARL, SALUD, IBC, CIE-10, FURAT, etc.
    - Referencias legales/normativas
    - **Audiencia**: Todos
    - **Tamaño**: ~8 KB

14. **ANEXO_C_MIGRACION_DATOS.md** (por generar)
    - Plan de migración desde Laravel/Livewire
    - Scripts de sincronización
    - Mapeo de tablas
    - **Audiencia**: DBA, data engineers
    - **Tamaño**: ~10 KB

---

## MAPA DE RELACIONES

```
RESUMEN_EJECUTIVO
├─ Visión general de sistema
├─ Apunta a: ARQUITECTURA, REGLAS_NEGOCIO
└─ Audiencia: Ejecutivos

REGLAS_NEGOCIO (RN-001:RN-022)
├─ Define: Qué y por qué hace el sistema
├─ Relaciona con: VALIDACIONES, HISTORIAS, CASOS_DE_USO
├─ Implementa: MODELO_DATOS, API_ENDPOINTS
└─ Verificado por: MATRIZ_TRAZABILIDAD

VALIDACIONES (VAL-001:VAL-054)
├─ Asegura: Calidad de datos
├─ Implementado en: API, Frontend, Backend
├─ Basado en: REGLAS_NEGOCIO
└─ Verificado por: QA

ARQUITECTURA
├─ Define: Cómo se construye el sistema
├─ Componentes: Frontend, Backend, Database, Storage
├─ Basado en: Stack tecnológico
└─ Apoya: API_ENDPOINTS, MODELO_DATOS

API_ENDPOINTS (200+)
├─ Implementa: HISTORIAS_USUARIO
├─ Cumple: VALIDACIONES
├─ Basado en: REGLAS_NEGOCIO
├─ Usa: MODELO_DATOS
└─ Verificado por: CASOS_DE_USO

MODELO_DATOS (17 tablas)
├─ Almacena: Datos del sistema
├─ Valida: Integridad referencial
├─ Relaciona con: API_ENDPOINTS, CASOS_DE_USO
└─ Auditado por: MATRIZ_TRAZABILIDAD

HISTORIAS_USUARIO (HU-001:HU-055+)
├─ Describe: Funcionalidades desde perspectiva usuario
├─ Basada en: REGLAS_NEGOCIO
├─ Implementada en: CASOS_DE_USO, API_ENDPOINTS
└─ Verificada por: MATRIZ_TRAZABILIDAD

CASOS_DE_USO (CU-001:CU-020+)
├─ Detalla: Flujos de negocio
├─ Basado en: HISTORIAS_USUARIO
├─ Usa: ROLES Y ACTORES
├─ Validado por: VALIDACIONES
└─ Implementado en: API_ENDPOINTS

INVENTARIO_FUNCIONAL
├─ Resume: Todas las funcionalidades
├─ Agrupa por: Módulo
├─ Estado: Completado / En desarrollo / Pendiente
└─ Verifica: Cobertura completa

MATRIZ_TRAZABILIDAD
├─ Verifica: Módulos → HU → RN → Tablas → APIs → Pantallas
├─ Asegura: Cobertura completa
├─ Detecta: Gaps de implementación
└─ Valida: Calidad general
```

---

## CÓMO USAR ESTA DOCUMENTACIÓN

### Para Ejecutivos
1. Leer: **RESUMEN_EJECUTIVO**
2. Revisar: Estado del proyecto y métricas
3. Validar: Funcionalidades principales

### Para Product Managers
1. Leer: **RESUMEN_EJECUTIVO** + **HISTORIAS_USUARIO**
2. Revisar: **REGLAS_NEGOCIO** para entender restricciones
3. Validar: **INVENTARIO_FUNCIONAL** para cobertura
4. Usar: **MATRIZ_TRAZABILIDAD** para tracing

### Para Desarrolladores Backend
1. Leer: **ARQUITECTURA** + **API_ENDPOINTS**
2. Revisar: **MODELO_DATOS** y relaciones
3. Implementar: **VALIDACIONES** en endpoints
4. Cumplir: **REGLAS_NEGOCIO**
5. Validar: **CASOS_DE_USO**

### Para Desarrolladores Frontend
1. Leer: **ARQUITECTURA** + **HISTORIAS_USUARIO**
2. Revisar: **VALIDACIONES** para formularios
3. Implementar: **CASOS_DE_USO** en componentes
4. Consumir: **API_ENDPOINTS**
5. Validar: Contra **REGLAS_NEGOCIO**

### Para QA/Testing
1. Leer: **HISTORIAS_USUARIO** + **CASOS_DE_USO**
2. Revisar: **VALIDACIONES** para cobertura
3. Usar: **REGLAS_NEGOCIO** para criterios
4. Validar: **MATRIZ_TRAZABILIDAD** para completitud
5. Verificar: **INVENTARIO_FUNCIONAL**

### Para Auditores
1. Leer: **RESUMEN_EJECUTIVO** + **REGLAS_NEGOCIO**
2. Revisar: **ANEXO_A_SKILLS_NEGOCIO** para metodología
3. Validar: **MODELO_DATOS** para auditoría
4. Usar: **VALIDACIONES** para control
5. Revisar: **MATRIZ_TRAZABILIDAD**

### Para DBA/Infraestructura
1. Leer: **MODELO_DATOS**
2. Revisar: **ARQUITECTURA** para infraestructura
3. Implementar: Backup, replicación, índices
4. Validar: Integridad referencial
5. Usar: **ANEXO_C_MIGRACION_DATOS**

---

## ESTADÍSTICAS DE DOCUMENTACIÓN

| Aspecto | Cantidad |
|---------|----------|
| **Documentos principales** | 11 |
| **Anexos** | 3 |
| **Total documentos** | 14 |
| **Reglas de negocio** | 22 |
| **Validaciones** | 54 |
| **Historias de usuario** | 55+ |
| **Casos de uso** | 20+ |
| **Tablas de BD** | 17 |
| **APIs/Endpoints** | 200+ |
| **Roles/Actores** | 6 |
| **Líneas de documentación** | 5,000+ |
| **Tamaño total** | ~200 KB |

---

## COHERENCIA Y REFERENCIAS CRUZADAS

### Todo está conectado

✅ Cada **Regla de Negocio** está vinculada a:
   - Historias de usuario que la implementan
   - Validaciones que la verifican
   - APIs que la ejecutan
   - Tablas que la almacenan
   - Casos de uso que la demuestran

✅ Cada **Historia de Usuario** está vinculada a:
   - Reglas de negocio que la rigen
   - Validaciones que la validan
   - APIs que la implementan
   - Casos de uso que la detallan
   - Pantallas que la muestran

✅ Cada **Caso de Uso** está vinculado a:
   - Historias de usuario que lo originan
   - APIs que lo implementan
   - Validaciones que lo protegen
   - Reglas que lo controlan

---

## ACTUALIZACIÓN Y MANTENIMIENTO

### Ciclo de Actualización
- **Cada sprint**: Actualizar INVENTARIO_FUNCIONAL
- **Cada release**: Actualizar HISTORIAS_USUARIO, CASOS_DE_USO, MATRIZ_TRAZABILIDAD
- **Cambios arquitectónicos**: Actualizar ARQUITECTURA, API_ENDPOINTS, MODELO_DATOS
- **Cambios de negocio**: Actualizar REGLAS_NEGOCIO

### Responsabilidades
- **Reglas de Negocio**: Product Manager
- **APIs/Arquitectura**: Tech Lead Backend
- **Validaciones**: Desarrolladores Frontend + Backend
- **Historias/Casos**: Scrum Master + Product Manager
- **Matriz de Trazabilidad**: QA Lead

### Control de Versiones
- Todos los documentos en control de versión (Git)
- Etiquetado por release
- Changelog en cabecera de cada documento
- Revisión antes de merge

---

## NAVEGACIÓN RÁPIDA

**Quiero entender...**

| Pregunta | Ir a |
|----------|------|
| ¿Qué es el sistema? | RESUMEN_EJECUTIVO |
| ¿Cuáles son las reglas principales? | REGLAS_NEGOCIO |
| ¿Qué validaciones hay? | VALIDACIONES |
| ¿Cómo se estructura la BD? | MODELO_DATOS |
| ¿Cuáles son los endpoints? | API_ENDPOINTS |
| ¿Cómo fluye un proceso? | CASOS_DE_USO |
| ¿Quién puede hacer qué? | HISTORIAS_USUARIO + ROLES |
| ¿Cómo se despliega? | ARQUITECTURA |
| ¿Qué funcionalidades hay? | INVENTARIO_FUNCIONAL |
| ¿Está todo implementado? | MATRIZ_TRAZABILIDAD |

---

## CONVENCIONES UTILIZADAS

### Identificadores Únicos
- **RN-XXX**: Reglas de Negocio (RN-001, RN-002, ...)
- **VAL-XXX**: Validaciones (VAL-001, VAL-002, ...)
- **HU-XXX**: Historias de Usuario (HU-001, HU-002, ...)
- **CU-XXX**: Casos de Uso (CU-001, CU-002, ...)

### Estado
- ✅ Completado
- 🔄 En desarrollo
- ⏳ Pendiente
- ⚠️ En riesgo
- ❌ Rechazado

### Relaciones
- **→** Referencia a
- **←** Referenciado por
- **↔** Bidirecional
- **├─** Parte de
- **└─** Contiene

---

## CONTACTO Y SOPORTE

**Preguntas sobre esta documentación:**
- documentation@segurosbolivar.com

**Actualizaciones o cambios:**
- Crear issue en repositorio
- Enviar PR con cambios
- Notificar a Tech Lead

---

**Versión**: 1.0  
**Generada**: Junio 2026  
**Próxima revisión**: Octubre 2026

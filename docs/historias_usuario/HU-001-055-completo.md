# Historias de Usuario - Sistema de Gestión de Incapacidades

**Versión**: 2.0  
**Fecha**: Junio 2026  
**Estado**: Completadas (Fases 1-2)

---

## Tabla de Contenidos

- [HU-001 a HU-010: Autenticación y Autorización](#hu-001-a-hu-010-autenticación-y-autorización)
- [HU-011 a HU-020: Radicación (Registro de Incapacidades)](#hu-011-a-hu-020-radicación-registro-de-incapacidades)
- [HU-021 a HU-030: Consulta y Búsqueda](#hu-021-a-hu-030-consulta-y-búsqueda)
- [HU-031 a HU-040: Módulo de Auditoría](#hu-031-a-hu-040-módulo-de-auditoría)
- [HU-041 a HU-050: Aprobación y Pagos](#hu-041-a-hu-050-aprobación-y-pagos)
- [HU-051+: Funcionalidades Adicionales](#hu-051-funcionalidades-adicionales)

---

## HU-001 a HU-010: Autenticación y Autorización

### HU-001 - Login de Usuario

**Descripción**:  
Como usuario registrado quiero acceder al sistema con mis credenciales para ejecutar tareas según mi rol.

**Criterios de aceptación**:
- ✓ Puedo ingresar username y contraseña en formulario
- ✓ El sistema valida credenciales contra base de datos
- ✓ Si son correctas, se genera JWT válido con duración 15 minutos
- ✓ Si son incorrectas, se muestra mensaje de error
- ✓ Después de 5 intentos fallidos, la cuenta se bloquea por 30 minutos
- ✓ El timestamp `ultimo_acceso` se actualiza en USUARIO
- ✓ Se registra en AUDITORIA_LOG con acción LOGIN

**Reglas de negocio relacionadas**:
- RN-031 (Control de acceso basado en roles)
- RN-035 (Bloqueo de cuenta por intentos fallidos)

**Módulos afectados**:
- Backend: `/api/v1/auth/login`
- Servicios: `auth_service.py`
- Modelos: USUARIO, AUDITORIA_LOG

**Notas técnicas**:
- Usar passlib con bcrypt para validación
- Generar JWT con python-jose (HS256, JWT_SECRET)
- Claims: iss, iat, exp, nbf, sub (user_id), jti

---

### HU-002 - Logout de Usuario

**Descripción**:  
Como usuario autenticado quiero cerrar sesión de forma segura para asegurar privacidad.

**Criterios de aceptación**:
- ✓ Botón LOGOUT disponible en navegación
- ✓ Al hacer logout, se revoca el refresh token
- ✓ El JWT se invalida en cliente (localStorage)
- ✓ Redirección a página de login
- ✓ Se registra AUDITORIA_LOG con acción LOGOUT

**Relaciones**:
- HU-001 (complementario)
- HU-003 (refresh token)

---

### HU-003 - Renovación de Token

**Descripción**:  
Como usuario quiero renovar mi token de acceso expirado sin hacer login nuevamente.

**Criterios de aceptación**:
- ✓ Puedo usar un refresh token válido para obtener nuevo access token
- ✓ El refresh token tiene duración de 7 días
- ✓ Se verifica que no esté revocado
- ✓ Se verifica que no esté expirado
- ✓ Si es válido, retorna nuevo access token (15 min)
- ✓ Si no es válido, solicita re-login
- ✓ Se registra en AUDITORIA_LOG

**Tabla de datos**:
- REFRESH_TOKEN (token_hash, expires_at, revoked_at, ip_address)

**Relaciones**:
- HU-001 (extensión)

---

### HU-004 - Cambio de Contraseña

**Descripción**:  
Como usuario quiero cambiar mi contraseña para mantener la seguridad de mi cuenta.

**Criterios de aceptación**:
- ✓ Acceso a formulario "Cambiar contraseña"
- ✓ Se solicita contraseña actual para validación
- ✓ Se permite ingreso de nueva contraseña (mín. 8 caracteres, 1 mayúscula, 1 número, 1 especial)
- ✓ Se valida que nueva contraseña sea diferente a actual
- ✓ Nueva contraseña se hashea con bcrypt
- ✓ Todos los refresh tokens se revоcan (token_version se incrementa)
- ✓ Se registra AUDITORIA_LOG con acción UPDATE

**Relaciones**:
- HU-001, HU-003

---

### HU-005 - Recuperación de Contraseña (Future)

**Descripción**:  
Como usuario olvidé mi contraseña y quiero restablecerla de forma segura.

**Criterios de aceptación**:
- ✓ Formulario "¿Olvidó contraseña?" accesible desde login
- ✓ Ingreso de email de usuario
- ✓ Sistema envía email con enlace temporal (válido 1 hora)
- ✓ Enlace lleva a formulario de nueva contraseña
- ✓ Después de cambio, enlace expira
- ✓ Mensaje de confirmación

**Módulos afectados**:
- Email service (Celery task)
- Token temporal (JWT con exp: 1 hora)

---

### HU-006 - Visualización de Perfil de Usuario

**Descripción**:  
Como usuario quiero ver mi información de perfil y datos personales.

**Criterios de aceptación**:
- ✓ Acceso a formulario "Mi Perfil" o "Configuración"
- ✓ Visualización de: username, email, nombre_completo, rol, empresa (si aplica)
- ✓ Información de último acceso (ultimo_acceso)
- ✓ Información de rol y permisos asignados
- ✓ No se permite edición de rol (solo ADMIN)
- ✓ No se permite edición de username

**Relaciones**:
- HU-001, HU-004

---

### HU-007 - Asignación de Rol a Usuario (ADMIN)

**Descripción**:  
Como ADMIN quiero asignar roles a usuarios para controlar permisos en el sistema.

**Criterios de aceptación**:
- ✓ Solo ADMIN puede acceder a "Gestión de Usuarios"
- ✓ Lista de todos los usuarios del sistema
- ✓ Selector de rol: ADMIN, AUDITOR, APROBADOR, EMPRESA, EMPLEADO, READONLY
- ✓ Cambio de rol invalida tokens activos (token_version++)
- ✓ Se registra AUDITORIA_LOG con acción UPDATE y detalles del cambio

**Roles y permisos**:
- ADMIN: Acceso total
- AUDITOR: Auditar incapacidades, marcar estado EN_AUDITORIA
- APROBADOR: Aprobar incapacidades, generar órdenes de pago
- EMPRESA: Ver solo incapacidades de su empresa
- EMPLEADO: Ver solo incapacidades propias
- READONLY: Solo lectura

---

### HU-008 - Creación de Cuenta de Usuario (ADMIN)

**Descripción**:  
Como ADMIN quiero crear nuevas cuentas de usuario para que accedan al sistema.

**Criterios de aceptación**:
- ✓ Formulario "Crear Usuario" con campos: username, email, nombre_completo, rol, empresa (opcional)
- ✓ Username único, 6-50 caracteres, alfanuméricos + guiones
- ✓ Email único, formato válido
- ✓ Contraseña temporal generada y enviada por email
- ✓ Flag must_change_password = true (usuario debe cambiar en primer login)
- ✓ Se registra AUDITORIA_LOG con acción CREATE

**Validaciones**:
- RN-032: Validación de formato de email
- RN-033: Validación de username

---

### HU-009 - Bloqueo/Desbloqueo de Usuario (ADMIN)

**Descripción**:  
Como ADMIN quiero bloquear o desbloquear usuarios para controlar el acceso al sistema.

**Criterios de aceptación**:
- ✓ Solo ADMIN puede cambiar estado del usuario
- ✓ Estados disponibles: ACTIVO, INACTIVO, BLOQUEADO
- ✓ Usuario bloqueado no puede login (validar en auth_service)
- ✓ Usuario inactivo tampoco puede login
- ✓ Se registra AUDITORIA_LOG con motivo del bloqueo
- ✓ Opción para desbloquear en 30 minutos (si fue por intentos fallidos)

**Relaciones**:
- HU-001, HU-007

---

### HU-010 - Cierre de Sesión Remota (ADMIN)

**Descripción**:  
Como ADMIN quiero cerrar sesión activa de un usuario de forma remota.

**Criterios de aceptación**:
- ✓ Opción en "Gestión de Usuarios" para cerrar sesión
- ✓ Incrementa token_version del usuario
- ✓ Todos los JWT activos se invalidan automáticamente
- ✓ Siguiente solicitud requiere re-login
- ✓ Se registra AUDITORIA_LOG con acción LOGOUT_REMOTO

**Módulos afectados**:
- Backend: `/api/v1/usuarios/{id}/logout`
- Servicios: `usuario_service.py`

---

## HU-011 a HU-020: Radicación (Registro de Incapacidades)

### HU-011 - Inicio de Radicación (Portal Externo - ARL)

**Descripción**:  
Como solicitante quiero iniciar el proceso de radicación de una incapacidad laboral ARL en el portal público.

**Criterios de aceptación**:
- ✓ Acceso a wizard "Radicar Incapacidad" sin login requerido
- ✓ Paso 1: Seleccionar tipo (ARL, SALUD)
- ✓ Paso 2: Datos del solicitante (nombre, apellido, email, teléfono)
- ✓ Validaciones de email, teléfono
- ✓ Opción para guardar como borrador
- ✓ Se almacena en PRE_INCAPACIDAD con estado PENDIENTE

**Módulos afectados**:
- Frontend: Portal Externo (Vite React)
- Backend: `/api/v1/incapacidades/consulta` (POST)
- Tablas: PRE_INCAPACIDAD, SOLICITANTE

**Validaciones**:
- RN-021: Validación de solicitante

**Notas técnicas**:
- Formulario reactivo con React Hook Form
- Validación con Zod schema
- Almacenamiento en PRE_INCAPACIDAD (sin procesar)

---

### HU-012 - Ingreso de Datos de Empresa (ARL)

**Descripción**:  
Como solicitante quiero proporcionar datos de la empresa ARL para vincularla a la incapacidad.

**Criterios de aceptación**:
- ✓ Paso 2: Búsqueda de empresa por NIT
- ✓ Si empresa existe en sistema, se carga automáticamente
- ✓ Si no existe, opción para ingresar manualmente nombre, teléfono, email
- ✓ Validación de NIT (formato colom bien: 123456789-1)
- ✓ Datos se guardan en PRE_INCAPACIDAD (empresa_nit, empresa_nombre)

**Relaciones**:
- HU-011

---

### HU-013 - Ingreso de Datos del Empleado (ARL)

**Descripción**:  
Como solicitante quiero proporcionar datos del empleado afectado.

**Criterios de aceptación**:
- ✓ Paso 3: Formulario con campos: tipo_documento, número_documento, nombres, apellidos
- ✓ Validación de número de documento según tipo
- ✓ Búsqueda opcional: si existe empleado en sistema, cargar datos
- ✓ Campos adicionales: email, teléfono, cargo (si se conocen)
- ✓ Datos se guardan en PRE_INCAPACIDAD

**Validaciones**:
- RN-022: Validación de documento de identidad
- RN-023: Validación de nombres y apellidos

---

### HU-014 - Ingreso de Datos de la Incapacidad

**Descripción**:  
Como solicitante quiero proporcionar información médica de la incapacidad.

**Criterios de aceptación**:
- ✓ Paso 4: Formulario con campos: fecha_inicio, fecha_fin, tipo_enfermedad (selector), diagnóstico_cie10
- ✓ Búsqueda de código CIE-10 con autocomplete desde CATALOGO_CIE10
- ✓ Validación: fecha_inicio <= fecha_fin
- ✓ Cálculo automático de dias_totales
- ✓ Campos de médico: nombre_medico, registro_medico, ips
- ✓ Descripción de diagnóstico (observaciones)
- ✓ Datos se guardan en PRE_INCAPACIDAD

**Validaciones**:
- RN-024: Validación de fechas
- RN-025: Validación de código CIE-10

---

### HU-015 - Carga de Documentos Soportes

**Descripción**:  
Como solicitante quiero adjuntar documentos médicos y de soporte para validación de la incapacidad.

**Criterios de aceptación**:
- ✓ Paso 5: Área de carga de archivos (drag and drop)
- ✓ Tipos permitidos: PDF, JPG, PNG, DOCX
- ✓ Tamaño máximo: 10 MB por archivo, 50 MB total
- ✓ Tipos de documento: INCAPACIDAD_MEDICA, CEDULA, HISTORIA_CLINICA, OTROS
- ✓ Validación de MIME type
- ✓ Cálculo de hash SHA256 para integridad
- ✓ Archivos se almacenan en MinIO/S3 (bucket: `incapacidades-{env}`)
- ✓ Metadatos se guardan en PRE_DOCUMENTO

**Módulos afectados**:
- Backend: `/api/v1/incapacidades/documentos/upload` (POST)
- Storage: MinIO/S3
- Tablas: PRE_DOCUMENTO

**Validaciones**:
- RN-026: Validación de documentos (tipo, tamaño)
- RN-027: Validación de formatos

---

### HU-016 - Revisión y Confirmación de Radicación

**Descripción**:  
Como solicitante quiero revisar toda la información antes de confirmar la radicación.

**Criterios de aceptación**:
- ✓ Paso 6: Resumen de todos los datos ingresados
- ✓ Botón "Editar" para cada sección
- ✓ Checkbox de términos y condiciones
- ✓ Botón "Radicar" confirma envío
- ✓ Al radicar: PRE_INCAPACIDAD se marca como PENDIENTE (lista para procesamiento)
- ✓ Se genera número_radicacion (secuencia: 202600001+)
- ✓ Email de confirmación enviado al solicitante
- ✓ Pantalla de éxito con número de radicación

**Módulos afectados**:
- Email service (Celery)
- AUDITORIA_LOG: acción RADICACION

---

### HU-017 - Radicación SALUD (Portal Externo)

**Descripción**:  
Como solicitante quiero radicar una incapacidad de salud (no laboral) desde el portal.

**Criterios de aceptación**:
- ✓ Flujo similar a HU-011 pero para incapacidades SALUD
- ✓ Paso 2: Búsqueda de afiliado por número de póliza
- ✓ NO hay datos de empresa ni siniestro
- ✓ Campos: número_poliza, tipo_poliza, nombres, apellidos, fecha_inicio, fecha_fin
- ✓ Datos se guardan en PRE_INCAPACIDAD (tipo = SALUD, afiliado_* en datos planos)
- ✓ Email de confirmación al solicitante

**Relaciones**:
- HU-011 (variante)

---

### HU-018 - Verificación de Radicación de Solicitante

**Descripción**:  
Como solicitante quiero verificar el estado de mis radicaciones.

**Criterios de aceptación**:
- ✓ Acceso a "Mis Radicaciones" (sin login, por email)
- ✓ Formulario: ingresar email usado en radicación
- ✓ Lista de radicaciones del email con número, fecha, estado
- ✓ Estados visibles: PENDIENTE, PROCESADA, ERROR, RECHAZADA
- ✓ Botón para descargar confirmación PDF
- ✓ Información de próximos pasos

**Módulos afectados**:
- Backend: `/api/v1/incapacidades/verificar` (GET por email)

---

### HU-019 - Procesamiento de Radicación por Job

**Descripción**:  
Como sistema, debo procesar automáticamente radicaciones pendientes en PRE_INCAPACIDAD.

**Criterios de aceptación**:
- ✓ Job programado ejecuta cada 5 minutos
- ✓ Selecciona PRE_INCAPACIDAD con estado PENDIENTE
- ✓ Valida y busca/crea: EMPRESA, EMPLEADO, AFILIADO, SOLICITANTE
- ✓ Si validación pasa: crea INCAPACIDAD (RADICADA) + DOCUMENTO
- ✓ PRE_INCAPACIDAD.estado = PROCESADA
- ✓ Si falla por datos: PRE_INCAPACIDAD.estado = RECHAZADA + error_procesamiento
- ✓ Si falla por excepción: PRE_INCAPACIDAD.estado = ERROR + error_procesamiento (retry)
- ✓ Email notificación a solicitante con resultado
- ✓ AUDITORIA_LOG registra acciones

**Módulos afectados**:
- Celery task: `process_pre_incapacidades`
- Servicios: `pre_incapacidad_service.py`

---

### HU-020 - Revisión de Radicaciones Rechazadas

**Descripción**:  
Como solicitante quiero conocer el motivo del rechazo de mi radicación.

**Criterios de aceptación**:
- ✓ Email explica motivo del rechazo (error_procesamiento)
- ✓ Acceso a "Mis Radicaciones" muestra detalles del error
- ✓ Opción para re-radicar corrigiendo datos
- ✓ Se conserva histórico de intentos

**Relaciones**:
- HU-018, HU-019

---

## HU-021 a HU-030: Consulta y Búsqueda

### HU-021 - Consulta Pública de Incapacidad

**Descripción**:  
Como ciudadano quiero consultar el estado de una incapacidad sin autenticación.

**Criterios de aceptación**:
- ✓ Acceso público a página "Consultar Estado de Incapacidad"
- ✓ Ingreso de número de incapacidad (ej: INC-2026-000001)
- ✓ Búsqueda retorna: estado, empleado (nombres), empresa, fecha radicación
- ✓ NO se retorna información sensible (diagnóstico, documentos, montos)
- ✓ Si no existe, mensaje "No encontrada"
- ✓ Se registra en AUDITORIA_LOG como "CONSULTA_PUBLICA"

**Módulos afectados**:
- Frontend: Página "Consultar" en portal externo
- Backend: `/api/v1/incapacidades/consultar` (GET sin auth)
- Servicios: `incapacidad_service.py` (método público)

---

### HU-022 - Búsqueda Avanzada de Incapacidades (Sistema Interno)

**Descripción**:  
Como usuario interno (AUDITOR, APROBADOR) quiero buscar incapacidades con múltiples criterios.

**Criterios de aceptación**:
- ✓ Acceso a "Búsqueda" en Sistema Interno
- ✓ Filtros: número, empleado (nombre/documento), empresa, estado, fecha_radicacion, prioridad
- ✓ Búsqueda de texto en observaciones
- ✓ Paginación: 25, 50, 100 registros por página
- ✓ Ordenamiento: número, fecha, estado, prioridad
- ✓ Resultados mostrar: número, empleado, empresa, estado, fecha, prioridad
- ✓ Enlace a detalles de cada incapacidad

**Módulos afectados**:
- Frontend: Componente SearchIncapacidades
- Backend: `/api/v1/incapacidades/buscar` (GET con params)
- Servicios: `incapacidad_service.search()`

**Validaciones**:
- RN-028: Validación de parámetros de búsqueda
- Acceso: Solo usuarios autenticados con roles AUDITOR, APROBADOR, ADMIN

---

### HU-023 - Visualización de Detalles de Incapacidad

**Descripción**:  
Como usuario interno quiero ver todos los detalles de una incapacidad.

**Criterios de aceptación**:
- ✓ Acceso a vista de detalles desde búsqueda
- ✓ Mostrar: número, tipo, estado, empleado/afiliado, empresa, siniestro (si aplica)
- ✓ Datos médicos: fecha_inicio, fecha_fin, diagnóstico, médico, ips
- ✓ Datos financieros: valor_día, valor_total (solo AUDITOR, APROBADOR, ADMIN)
- ✓ Historial de cambios de estado (HISTORIAL_ESTADO)
- ✓ Observaciones de auditoría
- ✓ Botones de acción según estado y rol

**Módulos afectados**:
- Backend: `/api/v1/incapacidades/{id}` (GET)
- Servicios: `incapacidad_service.get_by_id()`

---

### HU-024 - Visualización de Documentos Adjuntos

**Descripción**:  
Como usuario interno quiero ver y descargar los documentos adjuntos a una incapacidad.

**Criterios de aceptación**:
- ✓ Panel "Documentos" en vista de detalles
- ✓ Lista: tipo_documento, nombre_archivo, tamaño, fecha_carga, uploaded_by
- ✓ Ícono preview para PDF e imágenes
- ✓ Botón descargar: obtiene archivo desde MinIO/S3
- ✓ Validación de hash SHA256 en descarga
- ✓ Se registra AUDITORIA_LOG con acción DOWNLOAD_FILE

**Módulos afectados**:
- Backend: `/api/v1/documentos/{id}/descargar` (GET)
- Storage: MinIO/S3

---

### HU-025 - Exportación de Incapacidades (Excel/PDF)

**Descripción**:  
Como usuario interno quiero exportar listado de incapacidades a Excel o PDF.

**Criterios de aceptación**:
- ✓ Opción "Exportar" en vista de búsqueda
- ✓ Seleccionar formato: Excel (.xlsx), PDF
- ✓ Incluir: número, empleado, empresa, estado, fecha, diagnóstico, monto
- ✓ Aplicar mismos filtros de búsqueda
- ✓ Generar archivo descargable
- ✓ Se registra AUDITORIA_LOG con acción EXPORT_DATA

**Módulos afectados**:
- Backend: `/api/v1/incapacidades/exportar` (GET con format param)
- Librerías: openpyxl (Excel), reportlab (PDF)
- Celery task: procesamiento de exports grandes

---

### HU-026 - Historial de Cambios de Estado

**Descripción**:  
Como usuario quiero ver el historial completo de cambios de estado de una incapacidad.

**Criterios de aceptación**:
- ✓ Panel "Historial" en vista de detalles
- ✓ Mostrar cronología: fecha, estado_anterior, estado_nuevo, usuario, observación
- ✓ Ordenamiento: más recientes primero
- ✓ Información de usuario: nombre completo, rol
- ✓ Observaciones detalladas si existen

**Datos**:
- Tabla: HISTORIAL_ESTADO (query: entity_type='incapacidad', entity_id=incapacidad.id)

**Relaciones**:
- HU-023 (componente de detalles)

---

### HU-027 - Búsqueda de Siniestros Laborales

**Descripción**:  
Como AUDITOR quiero buscar siniestros laborales registrados.

**Criterios de aceptación**:
- ✓ Acceso a "Siniestros" en Sistema Interno
- ✓ Filtros: número_siniestro, empleado, empresa, tipo, gravedad, estado, fecha_siniestro
- ✓ Búsqueda de texto en descripción
- ✓ Paginación y ordenamiento
- ✓ Resultados mostrar: número, empleado, empresa, tipo, gravedad, estado
- ✓ Enlace a detalles con incapacidades asociadas

**Módulos afectados**:
- Backend: `/api/v1/siniestros/buscar` (GET)
- Servicios: `siniestro_service.search()`

---

### HU-028 - Dashboard de Métricas

**Descripción**:  
Como usuario interno (ADMIN, AUDITOR, APROBADOR) quiero ver métricas del sistema en tiempo real.

**Criterios de aceptación**:
- ✓ Dashboard con widgets: total_incapacidades, por_estado, pendientes_auditoria, por_pagar
- ✓ Filtros de rango de fechas
- ✓ Gráficos: barras (estado), línea (timeline), pie (prioridad)
- ✓ Valores actualizados en tiempo real (WebSocket o polling cada 30s)
- ✓ Cards mostrando KPIs: promedio_dias, valor_promedio, tasa_rechazo

**Módulos afectados**:
- Frontend: Componente Dashboard
- Backend: `/api/v1/estadisticas/dashboard` (GET con filters)
- Servicios: `estadistica_service.py`

**Notas técnicas**:
- Usar Recharts para gráficos
- Caché de 5 minutos para métricas complejas

---

### HU-029 - Reportes Personalizados

**Descripción**:  
Como usuario quiero generar reportes personalizados con datos específicos.

**Criterios de aceptación**:
- ✓ Acceso a "Reportes" en Sistema Interno
- ✓ Seleccionar: rango de fechas, estados, empresas, tipos (ARL/SALUD)
- ✓ Campos a incluir en reporte (selector multi-select)
- ✓ Generar en formato: PDF, Excel, CSV
- ✓ Descarga automática del archivo
- ✓ Opción para guardar configuración del reporte

**Módulos afectados**:
- Backend: `/api/v1/reportes/generar` (POST)
- Servicios: `reporte_service.py`

---

### HU-030 - Alertas de Incapacidades Próximas a Vencer

**Descripción**:  
Como usuario interno quiero recibir alertas de incapacidades próximas a finalizar.

**Criterios de aceptación**:
- ✓ Sistema identifica INCAPACIDAD donde hoy >= fecha_fin - 5 días
- ✓ Email de alerta a AUDITOR y APROBADOR asignados
- ✓ Widget en dashboard mostrando incapacidades a vencer
- ✓ Prioridad visual (color rojo si < 2 días)
- ✓ Enlace directo a incapacidad desde alerta
- ✓ No-resend si ya fue enviada hoy

**Módulos afectados**:
- Celery task: `alertar_incapacidades_vencimiento` (ejecución diaria 08:00)
- Email service

---

## HU-031 a HU-040: Módulo de Auditoría

### HU-031 - Obtener Incapacidades Pendientes de Auditoría

**Descripción**:  
Como AUDITOR quiero ver el listado de incapacidades en estado RADICADA y EN_AUDITORIA pendientes de auditar.

**Criterios de aceptación**:
- ✓ Acceso a "Bandeja de Auditoría" en Sistema Interno
- ✓ Filtro automático: estado IN ['RADICADA', 'EN_AUDITORIA']
- ✓ Ordenamiento por: prioridad DESC, fecha_radicacion ASC
- ✓ Mostrar: número, empleado, empresa, fecha, prioridad, días_pendientes
- ✓ Indicador visual de prioridad: colores ROJO (URGENTE), NARANJA (ALTA), AZUL (NORMAL), GRIS (BAJA)
- ✓ Paginación: 10 incapacidades por página
- ✓ Contador total de pendientes

**Módulos afectados**:
- Frontend: Componente BandejaAuditoria
- Backend: `/api/v1/incapacidades/bandeja-auditoria` (GET)
- Servicios: `incapacidad_service.get_bandeja_auditoria(auditor_id, limit, offset)`

**Acceso**:
- Solo AUDITOR y ADMIN

---

### HU-032 - Revisar Detalles para Auditoría

**Descripción**:  
Como AUDITOR quiero revisar todos los detalles de una incapacidad para tomar decisión.

**Criterios de aceptación**:
- ✓ Vista expandida con todos los datos (HU-023)
- ✓ Documentos adjuntos con vista previa (HU-024)
- ✓ Validación de campos críticos: diagnóstico, fecha_inicio, fecha_fin, montos
- ✓ Comparación con datos de empleado (si existen inconsistencias, alertar)
- ✓ Validar diagnóstico contra CATALOGO_CIE10
- ✓ Mostrar validaciones de negocio aplicadas
- ✓ Opción para dejar notas/observaciones antes de decidir

**Relaciones**:
- HU-023, HU-024, HU-025 (complementarios)

---

### HU-033 - Aprobar Incapacidad

**Descripción**:  
Como AUDITOR quiero aprobar una incapacidad después de revisar todos los datos.

**Criterios de aceptación**:
- ✓ Botón "Aprobar" en vista de detalles (visible solo si estado=RADICADA o EN_AUDITORIA)
- ✓ Diálogo de confirmación: resume datos clave y pide confirmación
- ✓ Almacenar observaciones (opcional)
- ✓ Al aprobar:
  - Estado cambia: RADICADA → EN_AUDITORIA → APROBADA
  - HISTORIAL_ESTADO registra cambios
  - AUDITORIA_DATOS_APROBADOS captura snapshot JSON
  - AUDITORIA_LOG registra acción CAMBIO_ESTADO
  - Email notificación al solicitante
- ✓ Pantalla de éxito confirma aprobación

**Módulos afectados**:
- Backend: `/api/v1/incapacidades/{id}/aprobar` (POST)
- Servicios: `incapacidad_service.aprobar(incapacidad_id, auditor_id, observaciones)`

**Validaciones**:
- RN-041: Validación de transición de estado
- RN-042: Solo AUDITOR/APROBADOR pueden aprobar

---

### HU-034 - Marcar como Observada

**Descripción**:  
Como AUDITOR quiero marcar una incapacidad como observada para solicitar correcciones.

**Criterios de aceptación**:
- ✓ Botón "Marcar como Observada" en vista de detalles
- ✓ Formulario con campo: "Motivo de observación" (obligatorio, texto)
- ✓ Campo opcional: "Documentos solicitados" (multi-select)
- ✓ Al marcar:
  - Estado cambia: RADICADA → EN_AUDITORIA → OBSERVADA
  - HISTORIAL_ESTADO registra cambio + observación
  - Email al solicitante con motivo y solicitud de corrección
  - AUDITORIA_LOG registra acción
- ✓ El sistema espera respuesta del solicitante
- ✓ Cuando solicitante re-radica: vuelve a EN_AUDITORIA

**Módulos afectados**:
- Backend: `/api/v1/incapacidades/{id}/observar` (POST)
- Servicios: `incapacidad_service.observar(incapacidad_id, auditor_id, motivo)`

**Relaciones**:
- HU-011, HU-019 (solicitante re-radica)

---

### HU-035 - Rechazar Incapacidad

**Descripción**:  
Como AUDITOR quiero rechazar una incapacidad por no cumplir requisitos.

**Criterios de aceptación**:
- ✓ Botón "Rechazar" en vista de detalles
- ✓ Formulario con campo: "Motivo de rechazo" (obligatorio, texto largo)
- ✓ Al rechazar:
  - Estado cambia: RADICADA → EN_AUDITORIA → RECHAZADA
  - motivo_rechazo se almacena en INCAPACIDAD
  - HISTORIAL_ESTADO registra cambio
  - Email al solicitante explica rechazo
  - AUDITORIA_LOG registra acción CAMBIO_ESTADO
- ✓ Pantalla de éxito
- ✓ Incapacidad rechazada NO genera orden de pago
- ✓ Opción para "Revertir rechazo" si ADMIN

**Módulos afectados**:
- Backend: `/api/v1/incapacidades/{id}/rechazar` (POST)
- Servicios: `incapacidad_service.rechazar(incapacidad_id, auditor_id, motivo)`

---

### HU-036 - Validación de Diagnóstico CIE-10

**Descripción**:  
Como sistema quiero validar automáticamente que el diagnóstico sea un código CIE-10 válido.

**Criterios de aceptación**:
- ✓ Al ingresar diagnóstico_cie10 en radicación: buscar en CATALOGO_CIE10
- ✓ Si existe y activo: aceptar
- ✓ Si existe pero inactivo: advertencia pero permitir
- ✓ Si no existe: error, no permitir radicación
- ✓ Autocomplete en búsqueda muestra código + descripción
- ✓ Base de datos CATALOGO_CIE10 actualizada periódicamente

**Módulos afectados**:
- Backend: `/api/v1/catalogos/cie10` (GET búsqueda)
- Servicios: `catalogo_service.buscar_cie10(termino)`
- Job: Actualización periódica de catálogo (mensual)

---

### HU-037 - Auditoría de Documentos

**Descripción**:  
Como AUDITOR quiero validar y marcar los documentos como validados.

**Criterios de aceptación**:
- ✓ Panel "Validación de Documentos" en vista de detalles
- ✓ Listar documentos con: tipo, nombre, tamaño, uploaded_by, estado (validado/no validado)
- ✓ Botón por cada documento: "Validar" o "Rechazar"
- ✓ Al validar: documento.validado = true, se registra usuario y fecha
- ✓ Al rechazar: campo observacion_validacion (motivo)
- ✓ Documento rechazado impide aprobación de incapacidad
- ✓ AUDITORIA_LOG registra validación

**Datos**:
- Tabla: DOCUMENTO (campos: validado, observacion_validacion)

---

### HU-038 - Auditoría de Cambios de Datos

**Descripción**:  
Como AUDITOR quiero revisar si hay inconsistencias en los datos de incapacidad vs empleado/empresa.

**Criterios de aceptación**:
- ✓ Sistema compara automáticamente:
  - nombres/apellidos empleado vs incapacidad (si hay discrepancia, alerta)
  - empresa del empleado vs empresa en incapacidad (si mismatch, error)
  - diagnóstico vs fecha_inicio (si diagnosis posterior a inicio, advertencia)
  - valor_día vs salario_base del empleado (si desproporcionado, advertencia)
- ✓ Mostrar alertas y advertencias en panel de auditoría
- ✓ AUDITOR puede proceder igualmente o rechazar
- ✓ Si hay alerta, se registra en HISTORIAL_ESTADO

**Relaciones**:
- HU-032, HU-031

---

### HU-039 - Auditoría en Lote (Batch)

**Descripción**:  
Como AUDITOR quiero procesar múltiples incapacidades en lote para aumentar eficiencia.

**Criterios de aceptación**:
- ✓ Opción "Seleccionar varios" en bandeja de auditoría
- ✓ Checkboxes para marcar incapacidades
- ✓ Botón "Acciones en Lote" con opciones: Aprobar, Observar, Rechazar
- ✓ Al ejecutar en lote:
  - Sistema aplica acción a todas seleccionadas
  - Se registra en HISTORIAL_ESTADO e AUDITORIA_LOG por cada una
  - Email de confirmación resumiendo cambios
- ✓ Validación: solo si todas cumplen criterios de la acción

**Módulos afectados**:
- Frontend: Componentes de selección multi
- Backend: `/api/v1/incapacidades/lote/accion` (POST)
- Servicios: `incapacidad_service.procesar_lote(ids, accion, data)`

---

### HU-040 - Reportes de Auditoría

**Descripción**:  
Como AUDITOR quiero generar reportes de mi actividad de auditoría.

**Criterios de aceptación**:
- ✓ Acceso a "Mis Reportes" en Sistema Interno
- ✓ Filtros: rango_fechas, estado (aprobadas, rechazadas, observadas)
- ✓ Métricas: total_auditadas, total_aprobadas, total_rechazadas, promedio_tiempo_auditoría
- ✓ Exportación a Excel: número, empleado, estado_final, fecha_auditoría, observaciones
- ✓ Gráfico: evolución diaria de auditorías
- ✓ Comparativa con otros auditores (si ADMIN)

**Módulos afectados**:
- Backend: `/api/v1/reportes/auditoria` (GET con filters)
- Servicios: `reporte_service.auditoria(auditor_id, filters)`

---

## HU-041 a HU-050: Aprobación y Pagos

### HU-041 - Obtener Incapacidades Pendientes de Aprobación

**Descripción**:  
Como APROBADOR quiero ver incapacidades aprobadas por AUDITOR pendientes de generar orden de pago.

**Criterios de aceptación**:
- ✓ Acceso a "Bandeja de Aprobación" en Sistema Interno
- ✓ Filtro automático: estado=APROBADA
- ✓ Mostrar: número, empleado, empresa, monto_total, fecha_aprobacion, días_desde_aprobación
- ✓ Ordenamiento: fecha_aprobacion ASC (más antiguas primero)
- ✓ Indicador de urgencia: rojo si > 5 días desde aprobación
- ✓ Paginación: 10 registros
- ✓ Contador total

**Módulos afectados**:
- Frontend: Componente BandejaAprobacion
- Backend: `/api/v1/incapacidades/bandeja-aprobacion` (GET)
- Servicios: `incapacidad_service.get_bandeja_aprobacion(aprobador_id, limit, offset)`

**Acceso**:
- APROBADOR, ADMIN

---

### HU-042 - Generar Orden de Pago

**Descripción**:  
Como APROBADOR quiero generar una orden de pago para una incapacidad aprobada.

**Criterios de aceptación**:
- ✓ Botón "Generar Orden de Pago" en vista de detalles (solo si estado=APROBADA)
- ✓ Formulario con campos:
  - beneficiario_tipo (selector: EMPLEADO, EMPRESA, IPS, AFILIADO)
  - beneficiario_id (auto-completar según tipo)
  - beneficiario_nombre, beneficiario_documento (pre-llenados)
  - cuenta_bancaria, banco, tipo_cuenta (pre-llenados si existen)
  - valor_pagar (pre-llenado con valor_total de incapacidad)
  - metodo_pago (selector: TRANSFERENCIA, CHEQUE, EFECTIVO)
  - observaciones (opcional)
- ✓ Al generar:
  - Crea ORDEN_PAGO con estado GENERADA
  - numero_orden asignado (formato: OP-2026-000001)
  - INCAPACIDAD.estado cambia: APROBADA → EN_PAGO
  - HISTORIAL_ESTADO registra cambios
  - AUDITORIA_LOG registra creación
- ✓ Pantalla de éxito muestra número de orden

**Módulos afectados**:
- Backend: `/api/v1/incapacidades/{id}/generar-orden-pago` (POST)
- Servicios: `orden_pago_service.generar(incapacidad_id, data)`

**Validaciones**:
- RN-043: Validación de datos del beneficiario
- RN-044: Validación de cuenta bancaria

---

### HU-043 - Obtener Órdenes de Pago Pendientes

**Descripción**:  
Como APROBADOR quiero ver las órdenes de pago pendientes de aprobación.

**Criterios de aceptación**:
- ✓ Acceso a "Bandeja de Órdenes de Pago" en Sistema Interno
- ✓ Filtro automático: estado_pago=GENERADA
- ✓ Mostrar: número_orden, beneficiario, valor, fecha_generacion, incapacidad_número
- ✓ Ordenamiento: fecha_generacion ASC
- ✓ Paginación, contador
- ✓ Enlace a detalles de orden

**Módulos afectados**:
- Frontend: Componente BandejaOrdenesPago
- Backend: `/api/v1/ordenes-pago/bandeja` (GET con estado filter)
- Servicios: `orden_pago_service.get_pendientes(limit, offset)`

---

### HU-044 - Revisar Orden de Pago

**Descripción**:  
Como APROBADOR quiero revisar detalles de una orden de pago antes de aprobarla.

**Criterios de aceptación**:
- ✓ Vista de detalles: número_orden, estado, beneficiario completo, cuenta, valor
- ✓ Referencia a incapacidad con enlace
- ✓ Validaciones de negocio:
  - Cuenta bancaria válida (formato)
  - Beneficiario existe
  - Valor es coherente con incapacidad
- ✓ Historial de cambios de orden (si existen)
- ✓ Botones: Aprobar, Rechazar, Editar

**Relaciones**:
- HU-042

---

### HU-045 - Aprobar Orden de Pago

**Descripción**:  
Como APROBADOR quiero aprobar una orden de pago para que sea procesada.

**Criterios de aceptación**:
- ✓ Botón "Aprobar Orden de Pago" en vista de detalles
- ✓ Diálogo de confirmación
- ✓ Al aprobar:
  - ORDEN_PAGO.estado cambia: GENERADA → APROBADA
  - aprobado_por_id se asigna
  - HISTORIAL_ESTADO registra cambio (si HISTORIAL aplica a ordenes)
  - AUDITORIA_LOG registra acción
  - Orden se envía a sistema de pagos (webhook o integración)
- ✓ Pantalla de éxito
- ✓ Email notificación a tesorería/finanzas

**Módulos afectados**:
- Backend: `/api/v1/ordenes-pago/{id}/aprobar` (POST)
- Servicios: `orden_pago_service.aprobar(orden_id, aprobador_id)`

**Relaciones**:
- HU-044

---

### HU-046 - Rechazar Orden de Pago

**Descripción**:  
Como APROBADOR quiero rechazar una orden de pago que tiene inconsistencias.

**Criterios de aceptación**:
- ✓ Botón "Rechazar Orden de Pago" en vista de detalles
- ✓ Formulario con campo: "Motivo de rechazo" (obligatorio)
- ✓ Al rechazar:
  - ORDEN_PAGO.estado cambia: GENERADA → RECHAZADA
  - Motivo se registra
  - INCAPACIDAD.estado vuelve a: APROBADA (para re-intentar)
  - AUDITORIA_LOG registra rechazo
  - Email al AUDITOR explicando rechazo
- ✓ Pantalla de éxito

**Módulos afectados**:
- Backend: `/api/v1/ordenes-pago/{id}/rechazar` (POST)
- Servicios: `orden_pago_service.rechazar(orden_id, aprobador_id, motivo)`

---

### HU-047 - Procesamiento de Pago

**Descripción**:  
Como sistema quiero procesar el pago de órdenes aprobadas hacia las cuentas bancarias.

**Criterios de aceptación**:
- ✓ Integración con pasarela de pagos o banco (API externa)
- ✓ Job procesador de pagos ejecuta cada 2 horas
- ✓ Selecciona ORDEN_PAGO con estado APROBADA
- ✓ Envía solicitud de transferencia a banco (ej: ACH, SPEI)
- ✓ Si respuesta exitosa:
  - ORDEN_PAGO.estado → EN_PROCESO
  - referencia_pago se asigna
  - INCAPACIDAD.estado → EN_PAGO
- ✓ Si hay error: ORDEN_PAGO.estado → ANULADA + motivo_anulacion
- ✓ AUDITORIA_LOG registra intento
- ✓ Email notificación a APROBADOR

**Módulos afectados**:
- Celery task: `procesar_pagos`
- Integración: Pasarela de pagos/Banco
- Servicios: `orden_pago_service.procesar_pago(orden_id)`

**Configuración**:
- API credentials en variables de entorno (.env)

---

### HU-048 - Confirmar Pago Realizado

**Descripción**:  
Como APROBADOR quiero confirmar que un pago se realizó correctamente.

**Criterios de aceptación**:
- ✓ Acceso a "Órdenes en Proceso"
- ✓ Formulario para ingresar datos del pago:
  - Referencia de transacción (ej: ID del banco)
  - Fecha de pago
  - Comprobante (archivo PDF/imagen)
- ✓ Al confirmar:
  - ORDEN_PAGO.estado → PAGADA
  - ORDEN_PAGO.fecha_pago ← fecha confirmada
  - INCAPACIDAD.estado → PAGADA
  - HISTORIAL_ESTADO registra cambio final
  - Email al solicitante confirmando pago
- ✓ Pantalla de éxito

**Módulos afectados**:
- Backend: `/api/v1/ordenes-pago/{id}/confirmar-pago` (POST)
- Servicios: `orden_pago_service.confirmar_pago(orden_id, datos)`

**Relaciones**:
- HU-047 (complementario)

---

### HU-049 - Anulación de Orden de Pago

**Descripción**:  
Como ADMIN quiero anular una orden de pago en caso de error.

**Criterios de aceptación**:
- ✓ Solo ADMIN puede anular
- ✓ Botón "Anular Orden" disponible en estados: GENERADA, APROBADA, EN_PROCESO
- ✓ Formulario: "Motivo de anulación" (obligatorio)
- ✓ Al anular:
  - ORDEN_PAGO.estado → ANULADA
  - fecha_anulacion se asigna
  - INCAPACIDAD.estado vuelve a: APROBADA (para re-intentar si se desea)
  - AUDITORIA_LOG registra anulación
  - Email a AUDITOR y APROBADOR notificando anulación
- ✓ Pantalla de éxito

**Módulos afectados**:
- Backend: `/api/v1/ordenes-pago/{id}/anular` (POST)
- Servicios: `orden_pago_service.anular(orden_id, admin_id, motivo)`

**Acceso**:
- Solo ADMIN

---

### HU-050 - Reportes de Pagos

**Descripción**:  
Como usuario quiero generar reportes de órdenes de pago y pagos realizados.

**Criterios de aceptación**:
- ✓ Acceso a "Reportes de Pagos" en Sistema Interno
- ✓ Filtros: rango_fechas, estado, beneficiario_tipo, empresa
- ✓ Métricas: total_ordenes, total_valor, ordenes_pagadas, ordenes_pendientes, promedio_valor
- ✓ Tabla: número_orden, beneficiario, valor, estado, fecha_pago
- ✓ Exportación: Excel, PDF
- ✓ Gráfico: valor pagado por día (línea)
- ✓ Gráfico: distribución por estado (pie)
- ✓ Opción para generar reportes a asignados a ADMIN

**Módulos afectados**:
- Backend: `/api/v1/reportes/pagos` (GET con filters)
- Servicios: `reporte_service.pagos(filters)`

---

## HU-051+: Funcionalidades Adicionales

### HU-051 - Administración de Empresas

**Descripción**:  
Como ADMIN quiero gestionar el registro de empresas en el sistema.

**Criterios de aceptación**:
- ✓ CRUD completo de empresas (Crear, Leer, Actualizar, Eliminar)
- ✓ Campos: NIT, razon_social, tipo_empresa, estado, contacto
- ✓ Búsqueda por NIT y razon_social
- ✓ Importar empresas desde CSV/Excel
- ✓ Sincronización con sistema externo (si aplica)

---

### HU-052 - Administración de Empleados

**Descripción**:  
Como representante de EMPRESA quiero gestionar el registro de mis empleados.

**Criterios de aceptación**:
- ✓ Acceso a "Mis Empleados" (rol EMPRESA)
- ✓ CRUD de empleados (Crear, Leer, Actualizar, Eliminar)
- ✓ Importar empleados desde CSV/Excel
- ✓ Búsqueda por documento, nombre
- ✓ Filtros: estado (activo, inactivo, retirado), área

---

### HU-053 - Administración de Afiliados

**Descripción**:  
Como ADMIN quiero gestionar afiliados de pólizas de salud.

**Criterios de aceptación**:
- ✓ CRUD completo de afiliados
- ✓ Búsqueda por número_poliza, documento
- ✓ Validación de vigencia de póliza
- ✓ Importación masiva

---

### HU-054 - Backup y Recuperación de Datos

**Descripción**:  
Como ADMIN quiero realizar backups de los datos del sistema.

**Criterios de aceptación**:
- ✓ Acceso a "Backup" en panel administrativo
- ✓ Botón "Realizar Backup" ejecuta dump de PostgreSQL
- ✓ Archivos de backup almacenados en S3/MinIO
- ✓ Listado de backups con fecha y tamaño
- ✓ Opción para descargar backup
- ✓ Restauración desde backup (procedimiento protegido)

---

### HU-055 - Logs de Auditoría Completo

**Descripción**:  
Como ADMIN quiero acceder a logs de auditoría detallados de todas las acciones.

**Criterios de aceptación**:
- ✓ Acceso a "Auditoría del Sistema" en panel ADMIN
- ✓ Filtros: usuario, acción, entidad, rango_fechas, ip_address
- ✓ Tabla con: timestamp, usuario, acción, entidad, cambios (si aplica)
- ✓ Búsqueda de texto libre
- ✓ Exportación a Excel
- ✓ Retención de logs: 12 meses

---

## Resumen de Historias de Usuario

| Rango | Categoría | Total | Estado |
|-------|-----------|-------|--------|
| HU-001 a HU-010 | Autenticación | 10 | Implementadas |
| HU-011 a HU-020 | Radicación | 10 | Implementadas |
| HU-021 a HU-030 | Consulta | 10 | Implementadas (parcial) |
| HU-031 a HU-040 | Auditoría | 10 | Implementadas |
| HU-041 a HU-050 | Aprobación/Pagos | 10 | Implementadas (parcial) |
| HU-051 a HU-055 | Administración | 5+ | Backlog |

**Total**: 50+ historias de usuario

**Cobertura**: Ciclo completo incapacidad: radicación → auditoría → aprobación → pago

---

*Documento sincronizado con Fases 1-2 del proyecto - Actualización Junio 2026*

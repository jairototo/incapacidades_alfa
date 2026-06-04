# HISTORIAS DE USUARIO

**Versión**: 1.0  
**Última Actualización**: Junio 2026  
**Propósito**: Especificación funcional detallada de 55+ historias de usuario

---

## FORMATO ESTÁNDAR

```
HU-XXX — [Nombre corto]

**Como** [rol]  
**Quiero** [acción]  
**Para** [beneficio]

**Criterios de Aceptación**:
1. Criterio 1
2. Criterio 2
3. Criterio 3
4. Criterio 4

**Reglas de Negocio Relacionadas**: RN-XXX, RN-YYY

**Story Points**: X  
**Prioridad**: Alta / Media / Baja  
**Estado**: Completada / En Desarrollo / Pendiente

**Notas Adicionales**: (si aplica)
```

---

## MÓDULO 1: AUTENTICACIÓN Y AUTORIZACIÓN (HU-001 a HU-010)

### HU-001 — Iniciar Sesión Exitosa

**Como** usuario del sistema  
**Quiero** iniciar sesión con email y contraseña  
**Para** acceder a las funcionalidades correspondientes a mi rol

**Criterios de Aceptación**:
1. El sistema valida email y contraseña contra base de datos
2. Si son correctos, genera tokens JWT (access + refresh)
3. El access token tiene validez de 15 minutos
4. El refresh token tiene validez de 7 días
5. Se registra el login en auditoria_log con IP y navegador

**Reglas de Negocio Relacionadas**: RN-040 (Autenticación), RN-041 (Tokens JWT)

**Story Points**: 5  
**Prioridad**: Alta  
**Estado**: Completada ✅

---

### HU-002 — Bloqueo de Cuenta por Intentos Fallidos

**Como** administrador del sistema  
**Quiero** que el sistema bloquee cuentas tras 5 intentos fallidos  
**Para** proteger contra ataques de fuerza bruta

**Criterios de Aceptación**:
1. Contador de intentos fallidos se incrementa en cada login incorrecto
2. Tras 5 intentos, la cuenta se bloquea automáticamente
3. Bloqueo dura 30 minutos o hasta desbloquearlo manualmente
4. Se registra el bloqueo en auditoria
5. Usuario recibe email notificando bloqueo

**Reglas de Negocio Relacionadas**: RN-042 (Seguridad de acceso)

**Story Points**: 8  
**Prioridad**: Alta  
**Estado**: Completada ✅

---

### HU-003 — Logout y Revocación de Sesión

**Como** usuario  
**Quiero** cerrar sesión y revocar mis tokens activos  
**Para** asegurar que nadie más pueda usar mi cuenta

**Criterios de Aceptación**:
1. Endpoint POST /auth/logout revoca tokens
2. Tokens revocados no pueden ser usados nuevamente
3. Logout exitoso redirige a página de login
4. Se registra logout en auditoria

**Story Points**: 5  
**Prioridad**: Alta  
**Estado**: Completada ✅

---

### HU-004 — Logout de Todas las Sesiones

**Como** usuario que sospecha acceso no autorizado  
**Quiero** cerrar todas mis sesiones activas de una vez  
**Para** evitar acceso desde otras ubicaciones

**Criterios de Aceptación**:
1. Endpoint POST /auth/logout-all revoca todos los refresh tokens
2. Todos los dispositivos se desconectan inmediatamente
3. Usuario recibe email confirmando revocación en masa
4. Se registra en auditoria

**Story Points**: 3  
**Prioridad**: Media  
**Estado**: Completada ✅

---

### HU-005 — Refresh de Token Expirado

**Como** usuario con token expirado  
**Quiero** usar mi refresh token para obtener un nuevo access token  
**Para** continuar usando el sistema sin reauthenticar

**Criterios de Aceptación**:
1. Endpoint POST /auth/refresh acepta refresh token válido
2. Genera nuevo access token con validez de 15 minutos
3. Si refresh token está expirado (>7 días), rechaza
4. Si refresh token fue revocado, rechaza

**Story Points**: 5  
**Prioridad**: Alta  
**Estado**: Completada ✅

---

### HU-006 — Cambiar Contraseña Propia

**Como** usuario  
**Quiero** cambiar mi contraseña actual  
**Para** mantener mi cuenta segura

**Criterios de Aceptación**:
1. Endpoint PUT /auth/cambiar-password requiere contraseña actual
2. Valida que contraseña actual sea correcta
3. Contraseña nueva no puede ser igual a anterior
4. Contraseña nueva se valida (min 8 caracteres, complejidad)
5. Se hashea con bcrypt cost 12
6. Se registra cambio en auditoria

**Story Points**: 5  
**Prioridad**: Media  
**Estado**: Completada ✅

---

### HU-007 — Resetear Contraseña por Olvido

**Como** usuario que olvidó su contraseña  
**Quiero** solicitar un reset de contraseña  
**Para** acceder nuevamente sin contactar soporte

**Criterios de Aceptación**:
1. Existe endpoint público de "¿Olvidó contraseña?"
2. Usuario proporciona email
3. Sistema genera token temporal (válido 1 hora)
4. Envía email con link de reset
5. Link contiene token seguro (URL-safe)
6. Usuario accede a formulario para establecer nueva contraseña

**Story Points**: 8  
**Prioridad**: Media  
**Estado**: Pendiente ⏳

---

### HU-008 — Rol y Permisos por Usuario

**Como** administrador  
**Quiero** asignar roles específicos a cada usuario  
**Para** controlar qué funcionalidades pueden usar

**Criterios de Aceptación**:
1. 6 roles disponibles: ADMIN, AUDITOR, APROBADOR, EMPRESA, EMPLEADO, READONLY
2. Cada rol tiene permisos específicos predefinidos
3. ADMIN: Acceso total a todas las funciones
4. AUDITOR: Ver incapacidades, auditar, cambiar estado EN_AUDITORIA→APROBADA/OBSERVADA
5. APROBADOR: Aprobar órdenes de pago
6. EMPRESA: Radicar y ver propias incapacidades
7. EMPLEADO: Consultar estado de propias incapacidades
8. READONLY: Solo lectura
9. Cambios de rol se registran en auditoria

**Reglas de Negocio Relacionadas**: RN-045 (RBAC)

**Story Points**: 13  
**Prioridad**: Alta  
**Estado**: Completada ✅

---

### HU-009 — Validación de Permisos en Cada Endpoint

**Como** desarrollador  
**Quiero** que cada endpoint valide permisos antes de ejecutar  
**Para** prevenir accesos no autorizados

**Criterios de Aceptación**:
1. Middleware de RBAC intercepta todas las requests
2. Valida token JWT válido
3. Verifica rol del usuario tiene permiso para el endpoint
4. Si sin permiso, retorna 403 Forbidden
5. Se registra intento de acceso no autorizado

**Story Points**: 8  
**Prioridad**: Alta  
**Estado**: Completada ✅

---

### HU-010 — Auditoría de Accesos

**Como** auditor de seguridad  
**Quiero** revisar log de todos los accesos al sistema  
**Para** detectar actividades sospechosas

**Criterios de Aceptación**:
1. Tabla auditoria_log registra: usuario, acción, timestamp, IP, navegador
2. Endpoint GET /auditoria-log retorna logs filtrados por fecha, usuario, acción
3. Se guarda quién cambió qué y cuándo
4. Cambios sensibles (crear usuario, aprobar incapacidad): registrados
5. Logs no pueden ser eliminados (solo consulta)

**Story Points**: 8  
**Prioridad**: Alta  
**Estado**: Completada ✅

---

## MÓDULO 2: RADICACIÓN DE INCAPACIDADES (HU-011 a HU-020)

### HU-011 — Radicar Incapacidad ARL

**Como** empresa o gestor de RR.HH.  
**Quiero** radicar una incapacidad de un empleado  
**Para** que sea procesada y pagada

**Criterios de Aceptación**:
1. Wizard de 6 pasos guía al usuario
2. Paso 1: Seleccionar tipo (ARL o SALUD)
3. Paso 2: Datos del empleado/afiliado
4. Paso 3: Fechas de incapacidad (inicio, fin)
5. Paso 4: Diagnóstico (CIE-10 con autocomplete)
6. Paso 5: Documentos (subir certificado médico, etc)
7. Paso 6: Revisión y confirmación
8. Sistema genera número único de radicado (AAAAMMNNNNNN)
9. Estado inicial: RADICADA
10. Se registra en historial_estado

**Reglas de Negocio Relacionadas**: RN-001 (Tipos), RN-002 (Radicado único), RN-003 (Ciclo de vida)

**Story Points**: 21  
**Prioridad**: Alta  
**Estado**: Completada ✅

---

### HU-012 — Validar Datos Obligatorios

**Como** sistema  
**Quiero** validar que todos los campos obligatorios estén presentes  
**Para** evitar incapacidades incompletas

**Criterios de Aceptación**:
1. Campos obligatorios:
   - Tipo (ARL o SALUD)
   - Empleado/Afiliado (según tipo)
   - Fechas inicio/fin
   - Diagnóstico CIE-10
   - Al menos 1 documento
   - Solicitante (quién radica)
2. Frontend valida con Zod antes de enviar
3. Backend revalida con Pydantic antes de guardar
4. Si falta alguno, retorna error 400 especificando cuál

**Reglas de Negocio Relacionadas**: RN-005 (Validación)

**Story Points**: 5  
**Prioridad**: Alta  
**Estado**: Completada ✅

---

### HU-013 — Calcular Días Totales Automáticamente

**Como** usuario  
**Quiero** que el sistema calcule automáticamente la cantidad de días  
**Para** evitar errores manuales

**Criterios de Aceptación**:
1. Formula: días = fecha_fin - fecha_inicio + 1
2. Se calcula cuando se ingresan ambas fechas
3. Se muestra en tiempo real en el formulario
4. Se valida que sea mayor a 0
5. Se guarda en BD como campo dias_totales

**Reglas de Negocio Relacionadas**: RN-010 (Cálculos)

**Story Points**: 3  
**Prioridad**: Media  
**Estado**: Completada ✅

---

### HU-014 — Calcular Valor Total Automáticamente

**Como** usuario  
**Quiero** que el sistema calcule el valor total (días × valor_dia)  
**Para** mostrar la cantidad a pagar

**Criterios de Aceptación**:
1. Formula: valor_total = dias_totales × valor_dia
2. Se actualiza en tiempo real
3. Se valida que ambos valores sean positivos
4. Si valor_dia no se proporciona, se puede dejar en blanco
5. Se muestra con 2 decimales y separador de miles

**Story Points**: 3  
**Prioridad**: Media  
**Estado**: Completada ✅

---

### HU-015 — Buscar CIE-10 con Autocomplete

**Como** usuario  
**Quiero** seleccionar diagnóstico CIE-10 con autocompletar  
**Para** agilizar el ingreso

**Criterios de Aceptación**:
1. Campo de entrada con búsqueda en tiempo real
2. Busca en código y descripción
3. Muestra máximo 10 resultados
4. Seleccionar resultado rellena el código
5. Backend valida que código CIE-10 exista

**Story Points**: 8  
**Prioridad**: Media  
**Estado**: Completada ✅

---

### HU-016 — Guardar Radicación en Borrador

**Como** usuario  
**Quiero** guardar mi progreso sin enviar aún  
**Para** continuar después sin empezar de nuevo

**Criterios de Aceptación**:
1. Botón "Guardar como Borrador" en cada paso
2. Datos se guardan en tabla pre_incapacidad
3. Estado: BORRADOR
4. Usuario puede reabrir borrador y continuar
5. Borradores expiran después de 30 días sin cambios
6. Se muestra lista de mis borradores

**Reglas de Negocio Relacionadas**: RN-008 (Pre-radicación)

**Story Points**: 13  
**Prioridad**: Media  
**Estado**: En Desarrollo 🔄

---

### HU-017 — Editar Radicación Antes de Radicar

**Como** usuario  
**Quiero** editar datos de una radicación en borrador  
**Para** corregir errores

**Criterios de Aceptación**:
1. Solo puede editar si está en estado BORRADOR
2. Todos los campos son editables
3. Cambios se guardan en pre_incapacidad
4. Timestamp de actualizado_en se registra
5. No puede radicar si algún campo es inválido

**Story Points**: 5  
**Prioridad**: Media  
**Estado**: En Desarrollo 🔄

---

### HU-018 — Cancelar Radicación

**Como** usuario  
**Quiero** cancelar una radicación en borrador  
**Para** descartarla sin enviarla

**Criterios de Aceptación**:
1. Botón "Descartar" en formulario
2. Pide confirmación
3. Marca pre_incapacidad como eliminado_en = NOW()
4. Documentos subidos se marcan como eliminados
5. No se puede recuperar

**Story Points**: 3  
**Prioridad**: Media  
**Estado**: Pendiente ⏳

---

### HU-019 — Radicar Incapacidad SALUD

**Como** usuario de portal de salud  
**Quiero** radicar una incapacidad SALUD (no laboral)  
**Para** que sea procesada

**Criterios de Aceptación**:
1. Tipo = SALUD en formulario
2. En lugar de empleado/empresa, se solicita afiliado
3. No hay campo de siniestro (solo para ARL)
4. Resto del flujo igual
5. Se valida que afiliado exista en BD

**Reglas de Negocio Relacionadas**: RN-001 (Tipos), RN-004 (SALUD vs ARL)

**Story Points**: 8  
**Prioridad**: Alta  
**Estado**: Completada ✅

---

### HU-020 — Comprobante de Radicación

**Como** solicitante  
**Quiero** recibir comprobante con mi número de radicado  
**Para** hacer seguimiento

**Criterios de Aceptación**:
1. Tras radicar exitosamente, se muestra comprobante en pantalla
2. Comprobante contiene:
   - Número de radicado (AAAAMMNNNNNN)
   - Fecha/hora de radicación
   - Tipo de incapacidad
   - Diagnóstico
   - Email de confirmación
3. Usuario puede descargar como PDF
4. Email se envía automáticamente
5. Número de radicado válido para consulta pública

**Story Points**: 8  
**Prioridad**: Alta  
**Estado**: Completada ✅

---

## MÓDULO 3: CONSULTA Y SEGUIMIENTO (HU-021 a HU-030)

### HU-021 — Consultar Estado Públicamente

**Como** público/solicitante  
**Quiero** consultar el estado de una incapacidad sin autenticarme  
**Para** conocer el progreso sin contraseña

**Criterios de Aceptación**:
1. Endpoint GET /incapacidades/consultar acepta número radicado
2. No requiere autenticación
3. Retorna solo información pública:
   - Estado actual (RADICADA, EN_AUDITORIA, APROBADA, PAGADA, etc)
   - Tipo de incapacidad
   - Fechas inicio/fin
   - Mensaje amigable del estado
4. No retorna datos sensibles (médico, empresa, documento)
5. Caché de 5 minutos para evitar hammering

**Story Points**: 5  
**Prioridad**: Alta  
**Estado**: Completada ✅

---

### HU-022 — Listar Mis Incapacidades

**Como** empresa/empleado  
**Quiero** ver un listado de mis incapacidades radicadas  
**Para** administrar mis casos

**Criterios de Aceptación**:
1. Endpoint GET /incapacidades retorna listado filtrado por usuario
2. Paginación: skip/limit
3. Campos mostrados: número, estado, tipo, fechas, valor
4. Ordenable por: número, fecha_inicio, estado, creado_en
5. Filtrable por: estado, tipo, fecha_inicio
6. Total de registros mostrado
7. 20 resultados por página por defecto

**Story Points**: 8  
**Prioridad**: Alta  
**Estado**: Completada ✅

---

### HU-023 — Ver Detalles de Incapacidad

**Como** usuario  
**Quiero** ver todos los detalles de una incapacidad  
**Para** revisar información completa

**Criterios de Aceptación**:
1. GET /incapacidades/{id} retorna objeto completo
2. Incluye:
   - Datos básicos (número, estado, tipo, fechas)
   - Empleado/Afiliado vinculado
   - Empresa vinculada
   - Diagnóstico y médico tratante
   - Documentos adjuntos (lista con links)
   - Historial de estado (quién cambió cuándo)
   - Observaciones (si existen)
3. Usuario solo ve si es el creador o tiene rol ADMIN/AUDITOR

**Story Points**: 8  
**Prioridad**: Alta  
**Estado**: Completada ✅

---

### HU-024 — Descargar Documentos

**Como** usuario  
**Quiero** descargar los documentos adjuntos a una incapacidad  
**Para** revisarlos sin ir al sistema

**Criterios de Aceptación**:
1. GET /documentos/{id}/descargar retorna archivo binario
2. Valida permisos del usuario
3. Content-Type correcto (PDF, image/jpeg, etc)
4. Content-Disposition: attachment; filename="..."
5. Log de descarga en auditoria

**Story Points**: 5  
**Prioridad**: Media  
**Estado**: Completada ✅

---

### HU-025 — Ver Historial de Cambios

**Como** auditor  
**Quiero** ver quién cambió qué y cuándo en cada incapacidad  
**Para** auditar completamente

**Criterios de Aceptación**:
1. GET /historial-estado?entidad_id={id} retorna lista
2. Muestra:
   - Estado anterior
   - Estado nuevo
   - Quién lo cambió (email del usuario)
   - Cuándo lo cambió (timestamp)
   - Razón/observaciones
3. Ordenado cronológicamente (reciente primero)
4. Sin paginación (mostrar todos)

**Story Points**: 5  
**Prioridad**: Media  
**Estado**: Completada ✅

---

### HU-026 — Buscar Incapacidades Avanzado

**Como** auditor/admin  
**Quiero** buscar incapacidades con filtros complejos  
**Para** encontrar casos específicos rápidamente

**Criterios de Aceptación**:
1. Filtros disponibles:
   - Estado (multiselect)
   - Tipo (ARL, SALUD)
   - Empresa (si ARL)
   - Fecha inicio (rango)
   - Valor total (rango)
   - Diagnóstico (autocomplete CIE-10)
   - Auditor asignado
   - Solicitante
2. Combinación de filtros (AND lógico)
3. Búsqueda por número radicado o documento
4. Resultados actualizados en tiempo real
5. Opción de guardar búsqueda

**Story Points**: 13  
**Prioridad**: Media  
**Estado**: En Desarrollo 🔄

---

### HU-027 — Exportar Listado a Excel

**Como** admin/auditor  
**Quiero** exportar listado de incapacidades a Excel  
**Para** usar en reportes externos

**Criterios de Aceptación**:
1. Botón "Exportar" en listado
2. Descarga archivo .xlsx
3. Columnas: número, estado, tipo, empresa, fechas, valor, etc
4. Formato con estilos (headers en negrita, alturas ajustadas)
5. Números formatados con separadores de miles
6. Se exportan los resultados filtrados actuales

**Story Points**: 8  
**Prioridad**: Media  
**Estado**: Pendiente ⏳

---

### HU-028 — Rastrear Estado en Tiempo Real

**Como** solicitante  
**Quiero** recibir notificaciones cuando el estado cambie  
**Para** saber inmediatamente qué pasó

**Criterios de Aceptación**:
1. Cada cambio de estado genera notificación
2. Email automático con mensaje amigable
3. Dashboard muestra actualización en tiempo real (WebSocket o polling)
4. Notificación contiene:
   - Número radicado
   - Estado anterior y nuevo
   - Razón (si aplica)
   - Próximo paso recomendado
5. Enlace a consultar estado

**Story Points**: 13  
**Prioridad**: Media  
**Estado**: En Desarrollo 🔄

---

### HU-029 — Historial de Pre-radicaciones

**Como** usuario  
**Quiero** ver mis radicaciones guardadas en borrador  
**Para** continuar o eliminarlas

**Criterios de Aceptación**:
1. Dashboard muestra sección "Mis borradores"
2. Lista pre_incapacidades con estado BORRADOR
3. Muestra: paso completado (0-5), fecha creación, tipo
4. Botones: Continuar, Eliminar, Duplicar
5. Borradores se ordenan por fecha (recientes primero)
6. Indicador visual de antigüedad (si >15 días, con aviso)

**Story Points**: 8  
**Prioridad**: Media  
**Estado**: En Desarrollo 🔄

---

### HU-030 — Estadísticas de Mis Incapacidades

**Como** empresa  
**Quiero** ver estadísticas de mis incapacidades  
**Para** analizar tendencias

**Criterios de Aceptación**:
1. Dashboard con gráficos:
   - Total de incapacidades por estado (pie chart)
   - Evolución temporal (línea: mes vs cantidad)
   - Valor total radicado vs pagado
   - Promedio de días por caso
   - Tasa de aprobación
2. Período seleccionable (último mes, trimestre, año, custom)
3. Exportable a PDF
4. Datos actualizados diariamente

**Story Points**: 13  
**Prioridad**: Baja  
**Estado**: Pendiente ⏳

---

## MÓDULO 4: AUDITORÍA (HU-031 a HU-040)

### HU-031 — Ver Incapacidades Pendientes de Auditoría

**Como** auditor  
**Quiero** ver un listado de incapacidades esperando auditoría  
**Para** saber qué revisar

**Criterios de Aceptación**:
1. GET /incapacidades?estado=EN_AUDITORIA retorna listado
2. Muestra solo incapacidades EN_AUDITORIA
3. Ordenadas por fecha de radicación (más antiguas primero)
4. Indica urgencia (color rojo si >5 días sin auditar)
5. Total de pendientes mostrado en un badge
6. Filtrable por empresa, tipo, etc

**Story Points**: 5  
**Prioridad**: Alta  
**Estado**: Completada ✅

---

### HU-032 — Asignar Incapacidad a Auditor

**Como** coordinador de auditoría  
**Quiero** asignar incapacidades a auditores específicos  
**Para** distribuir carga de trabajo

**Criterios de Aceptación**:
1. Endpoint PATCH /incapacidades/{id}/asignar-auditor
2. Parámetro: usuario_id del auditor
3. Transición: RADICADA → EN_AUDITORIA
4. Registra en historial_estado
5. Auditor recibe notificación email
6. Solo ADMIN o COORDINADOR puede asignar

**Story Points**: 8  
**Prioridad**: Media  
**Estado**: Pendiente ⏳

---

### HU-033 — Revisar Documentación de Incapacidad

**Como** auditor  
**Quiero** revisar todos los documentos de una incapacidad  
**Para** validar que cumpla requisitos

**Criterios de Aceptación**:
1. GET /incapacidades/{id}/detalles incluye documentos
2. Previsualizaciones inline (PDF, imágenes)
3. Botón para descargar cada documento
4. Verificación de integridad (checksum MD5/SHA256)
5. Indicador de virus scan (si aplica)
6. Posibilidad de rechazar documentos específicos

**Story Points**: 13  
**Prioridad**: Alta  
**Estado**: Completada ✅

---

### HU-034 — Solicitar Documentos Faltantes

**Como** auditor  
**Quiero** solicitar documentos adicionales al solicitante  
**Para** completar la auditoría

**Criterios de Aceptación**:
1. Endpoint POST /incapacidades/{id}/solicitar-documentos
2. Parámetro: lista de tipos de documentos faltantes
3. Sistema genera mensaje y envía email
4. Estado sigue EN_AUDITORIA pero con flag "documentos_solicitados"
5. Solicitante recibe link para subir documentos
6. Auditor recibe notificación cuando se suben

**Story Points**: 13  
**Prioridad**: Media  
**Estado**: Pendiente ⏳

---

### HU-035 — Aprobar Incapacidad

**Como** auditor  
**Quiero** aprobar una incapacidad después de validarla  
**Para** avanzarla a la siguiente etapa

**Criterios de Aceptación**:
1. Endpoint PATCH /incapacidades/{id}/auditar
2. Parámetros: nuevo_estado=APROBADA, observaciones opcionales
3. Valida transición: EN_AUDITORIA → APROBADA (RN-003)
4. Registra en historial_estado
5. Crea entrada en auditoria_datos_aprobados con snapshot
6. Solicitante recibe email de aprobación
7. Incapacidad lista para generar orden de pago

**Reglas de Negocio Relacionadas**: RN-003 (Transiciones), RN-025 (Auditoría)

**Story Points**: 8  
**Prioridad**: Alta  
**Estado**: Completada ✅

---

### HU-036 — Observar Incapacidad (Solicitar Correcciones)

**Como** auditor  
**Quiero** marcar una incapacidad como OBSERVADA si tiene problemas  
**Para** que el solicitante haga correcciones

**Criterios de Aceptación**:
1. Endpoint PATCH /incapacidades/{id}/observar
2. Parámetros: lista de observaciones (array)
3. Transición: EN_AUDITORIA → OBSERVADA
4. Registra observaciones en historial_estado
5. Solicitante recibe email con lista de problemas
6. Solicitante puede corregir y resubmitir
7. Cuando reenvía, vuelve a EN_AUDITORIA
8. Contador de intentos se incrementa

**Story Points**: 8  
**Prioridad**: Alta  
**Estado**: Completada ✅

---

### HU-037 — Rechazar Incapacidad

**Como** auditor  
**Quiero** rechazar una incapacidad que no cumple requisitos  
**Para** terminar el caso

**Criterios de Aceptación**:
1. Endpoint PATCH /incapacidades/{id}/rechazar
2. Parámetros: motivo_rechazo (texto obligatorio)
3. Transición: EN_AUDITORIA → RECHAZADA
4. Estado es terminal (no se puede reaprovechar)
5. Registra motivo completo
6. Solicitante recibe email con razón del rechazo
7. Historial de estado registra rechazado y por quién

**Reglas de Negocio Relacionadas**: RN-003 (Estados terminales)

**Story Points**: 5  
**Prioridad**: Alta  
**Estado**: Completada ✅

---

### HU-038 — Registrar Datos Aprobados

**Como** auditor  
**Quiero** confirmar y registrar datos específicos aprobados  
**Para** dejar constancia

**Criterios de Aceptación**:
1. Al aprobar incapacidad, se registra snapshot en auditoria_datos_aprobados
2. Snapshot contiene:
   - Nombre beneficiario, documento
   - Valor aprobado (puede ser distinto del solicitado)
   - Días aprobados (puede ser distinto del solicitado)
   - Observaciones finales
3. Es inmutable (no se puede editar después)
4. Se usa para generar orden de pago

**Story Points**: 5  
**Prioridad**: Media  
**Estado**: Completada ✅

---

### HU-039 — Auditoría por Muestreo Aleatorio

**Como** jefe de auditoría  
**Quiero** seleccionar incapacidades al azar para auditoria secundaria  
**Para** garantizar calidad

**Criterios de Aceptación**:
1. Endpoint POST /auditorias/muestreo-aleatorio
2. Parámetros: cantidad, filtro (ej: solo PAGADAS)
3. Selecciona al azar según condiciones
4. Genera segunda auditoría paralela
5. Compara resultados de ambos auditores
6. Reporta discrepancias

**Story Points**: 13  
**Prioridad**: Baja  
**Estado**: Pendiente ⏳

---

### HU-040 — Reporte de Auditoría

**Como** jefe de auditoría  
**Quiero** generar reporte con métricas de auditoría  
**Para** evaluar performance de equipo

**Criterios de Aceptación**:
1. GET /reportes/auditoria con parámetros:
   - Fecha inicio/fin
   - Auditor (opcional, filtro)
2. Métricas:
   - Total revisadas
   - Aprobadas, observadas, rechazadas (conteos y %)
   - Tiempo promedio de auditoría
   - Tasa de observaciones vs aprobaciones
   - Documentos más rechazados
3. Exportable a PDF/Excel
4. Gráficos incluidos

**Story Points**: 13  
**Prioridad**: Media  
**Estado**: Pendiente ⏳

---

## MÓDULO 5: APROBACIÓN Y PAGO (HU-041 a HU-050)

### HU-041 — Generar Orden de Pago

**Como** administrador  
**Quiero** crear una orden de pago para incapacidad aprobada  
**Para** procesarla

**Criterios de Aceptación**:
1. Incapacidad debe estar en estado APROBADA
2. Endpoint POST /ordenes-pago
3. Parámetros: incapacidad_id, monto (puede ser diferente al solicitado)
4. Genera número único (OP-YYYY-NNNNN)
5. Estado inicial: GENERADA
6. Registra en historial_estado
7. Se calcula automáticamente:
   - Monto total = valor_total de incapacidad
   - Impuestos retenidos (si aplica)
   - Monto neto = total - impuestos

**Story Points**: 8  
**Prioridad**: Alta  
**Estado**: Completada ✅

---

### HU-042 — Aprobar Orden de Pago

**Como** aprobador  
**Quiero** revisar y aprobar una orden de pago  
**Para** autorizarla para pago

**Criterios de Aceptación**:
1. Endpoint PATCH /ordenes-pago/{id}/aprobar
2. Parámetros: observaciones opcionales
3. Transición: GENERADA → APROBADA
4. Registra quién aprobó y cuándo
5. Se valida monto no sea anómalo (compara con histórico)
6. Registra en historial_estado
7. Siguiente paso: Pagador ejecuta pago

**Story Points**: 5  
**Prioridad**: Alta  
**Estado**: Completada ✅

---

### HU-043 — Rechazar Orden de Pago

**Como** aprobador  
**Quiero** rechazar una orden de pago si hay problema  
**Para** evitar pagos incorrectos

**Criterios de Aceptación**:
1. Endpoint PATCH /ordenes-pago/{id}/rechazar
2. Parámetros: motivo obligatorio
3. Transición: GENERADA → ANULADA (o APROBADA → ANULADA)
4. Incapacidad vuelve a APROBADA (no cambia estado)
5. Se registra motivo en historial
6. Notificación a generador de orden

**Story Points**: 5  
**Prioridad**: Media  
**Estado**: Completada ✅

---

### HU-044 — Ejecutar Pago

**Como** pagador  
**Quiero** registrar que el pago fue ejecutado  
**Para** cerrar el caso

**Criterios de Aceptación**:
1. Orden debe estar APROBADA
2. Endpoint PATCH /ordenes-pago/{id}/pagar
3. Parámetros:
   - metodo_pago: TRANSFERENCIA_BANCARIA, CHEQUE, EFECTIVO
   - banco_destino
   - numero_cuenta
   - numero_comprobante (referencia de pago)
4. Transición: APROBADA → PAGADA
5. Registra fecha_pago = NOW()
6. Incapacidad cambia a PAGADA
7. Notificación al solicitante con comprobante

**Story Points**: 8  
**Prioridad**: Alta  
**Estado**: Completada ✅

---

### HU-045 — Pago Parcial

**Como** pagador  
**Quiero** registrar un pago parcial cuando no se puede pagar todo  
**Para** dejar constancia

**Criterios de Aceptación**:
1. Endpoint PATCH /ordenes-pago/{id}/pago-parcial
2. Parámetros: monto_pagado, fecha_pago, comprobante
3. Transición: APROBADA → EN_PAGO_PARCIAL
4. Incapacidad: APROBADA → EN_PAGO_PARCIAL
5. Genera nueva orden por saldo pendiente
6. Se registra en historial
7. Próximo pago completa la orden

**Story Points**: 13  
**Prioridad**: Media  
**Estado**: Completada ✅

---

### HU-046 — Anular Orden de Pago

**Como** admin  
**Quiero** anular una orden de pago si hubo error  
**Para** corregir

**Criterios de Aceptación**:
1. Solo ADMIN puede anular
2. Endpoint PATCH /ordenes-pago/{id}/anular
3. Parámetros: motivo
4. Cualquier estado → ANULADA
5. Incapacidad vuelve a APROBADA
6. Se puede generar nueva orden correcto

**Story Points**: 5  
**Prioridad**: Media  
**Estado**: Completada ✅

---

### HU-047 — Ver Órdenes de Pago Pendientes

**Como** pagador  
**Quiero** ver órdenes aprobadas esperando pago  
**Para** saber qué pagar

**Criterios de Aceptación**:
1. GET /ordenes-pago?estado=APROBADA
2. Muestra ordenes APROBADAS sin pagar
3. Ordenadas por antigüedad (más viejas primero)
4. Muestra: número, incapacidad número, monto, fecha creación
5. Total de órdenes pendientes
6. Filtrable por fecha, monto, empresa

**Story Points**: 5  
**Prioridad**: Alta  
**Estado**: Completada ✅

---

### HU-048 — Reconciliación de Pagos

**Como** contador  
**Quiero** reconciliar pagos registrados vs realmente ejecutados  
**Para** auditar financiero

**Criterios de Aceptación**:
1. Endpoint GET /reportes/reconciliacion-pagos
2. Parámetros: fecha_inicio, fecha_fin
3. Compara:
   - Órdenes PAGADAS en BD
   - vs Transferencias en cuenta bancaria (integración futura)
4. Reporte con:
   - Total pagado según BD
   - Total según banco
   - Discrepancias (falta pagar, pagado extra, etc)
5. Exportable

**Story Points**: 21  
**Prioridad**: Baja  
**Estado**: Pendiente ⏳

---

### HU-049 — Crear Orden de Pago Manual

**Como** admin  
**Quiero** crear orden de pago manualmente sin incapacidad  
**Para** casos especiales

**Criterios de Aceptación**:
1. Endpoint POST /ordenes-pago/manual
2. Sin parámetro incapacidad_id
3. Parámetros: nombre beneficiario, documento, monto, razón
4. Se registra como "manual" en tipo_orden
5. Requiere doble aprobación (ADMIN + APROBADOR)
6. Auditable completamente

**Story Points**: 8  
**Prioridad**: Baja  
**Estado**: Pendiente ⏳

---

### HU-050 — Comprobante de Pago

**Como** beneficiario  
**Quiero** descargar comprobante de pago  
**Para** tener constancia

**Criterios de Aceptación**:
1. GET /ordenes-pago/{id}/comprobante retorna PDF
2. Contiene:
   - Orden número
   - Incapacidad número
   - Monto pagado, fecha
   - Método de pago, comprobante
   - Datos beneficiario (parcialmente enmascarado por seguridad)
3. Firmado digitalmente (hash o similar)
4. Logo de empresa
5. Email automático con comprobante

**Story Points**: 8  
**Prioridad**: Media  
**Estado**: Pendiente ⏳

---

## MÓDULO 6: ADMINISTRACIÓN Y REPORTES (HU-051 a HU-055)

### HU-051 — Crear Usuario Admin

**Como** superadmin  
**Quiero** crear nuevos usuarios en el sistema  
**Para** que accedan

**Criterios de Aceptación**:
1. Endpoint POST /usuarios
2. Parámetros: email, nombre, rol, password_temporal
3. Email debe ser único
4. Password temporal generado seguro (16 caracteres)
5. Usuario debe cambiar password en primer login
6. Se registra en auditoria_log
7. Email de bienvenida enviado

**Story Points**: 5  
**Prioridad**: Alta  
**Estado**: Completada ✅

---

### HU-052 — Bloquear Usuario Manualmente

**Como** admin  
**Quiero** bloquear acceso de un usuario  
**Para** suspender por motivos de seguridad

**Criterios de Aceptación**:
1. Endpoint PATCH /usuarios/{id}/bloquear
2. Parámetros: motivo (auditoria)
3. Usuario no puede hacer login
4. Usuario recibe email de notificación
5. Se registra en auditoria_log
6. Admin puede desbloquear luego

**Story Points**: 3  
**Prioridad**: Alta  
**Estado**: Completada ✅

---

### HU-053 — Reporte de Incapacidades por Estado

**Como** director  
**Quiero** ver reporte de incapacidades agrupadas por estado  
**Para** saber el progreso general

**Criterios de Aceptación**:
1. GET /reportes/por-estado
2. Parámetros: fecha_inicio, fecha_fin
3. Datos:
   - Cantidad por estado
   - Porcentaje del total
   - Valor total por estado
   - Tiempo promedio en estado
4. Gráfico pie chart
5. Exportable PDF/Excel

**Story Points**: 8  
**Prioridad**: Media  
**Estado**: Pendiente ⏳

---

### HU-054 — Reporte de Incapacidades por Empresa

**Como** director  
**Quiero** analizar incapacidades por empresa  
**Para** identificar patrones

**Criterios de Aceptación**:
1. GET /reportes/por-empresa
2. Parámetros: fecha_inicio, fecha_fin, tipo_incapacidad
3. Datos por empresa:
   - Total radicadas
   - Total aprobadas, rechazadas
   - Valor promedio
   - Tasa de aprobación
4. Top 10 empresas con más incapacidades
5. Gráfico barra horizontal

**Story Points**: 8  
**Prioridad**: Media  
**Estado**: Pendiente ⏳

---

### HU-055 — Dashboard Ejecutivo

**Como** director ejecutivo  
**Quiero** ver dashboard con KPIs principales  
**Para** monitorear salud del sistema

**Criterios de Aceptación**:
1. Widget con totales:
   - Incapacidades este mes
   - Incapacidades pendientes (por estado)
   - Valor total pagado este mes
   - Órdenes de pago pendientes
2. Gráficos:
   - Evolución de radicaciones (línea últimos 12 meses)
   - Tasa de aprobación (gauge)
   - Tiempo promedio auditoría (KPI)
3. Alertas (rojo): Órdenes >30 días sin pagar
4. Actualizable (refresh manual o automático 5 min)
5. Exportable a PDF

**Story Points**: 21  
**Prioridad**: Baja  
**Estado**: Pendiente ⏳

---

## RESUMEN DE ESTADOS

**Completadas**: 28 ✅  
**En Desarrollo**: 8 🔄  
**Pendientes**: 19 ⏳

**Total**: 55 historias de usuario

---

## MATRICES DE RELACIÓN

### Por Prioridad

| Prioridad | Count | % |
|-----------|-------|---|
| Alta | 26 | 47% |
| Media | 22 | 40% |
| Baja | 7 | 13% |

### Por Story Points

| Rango | Count |
|-------|-------|
| 3-5 | 18 |
| 8 | 18 |
| 13 | 12 |
| 21 | 2 |

**Total Story Points**: 411

---

**Documento de referencia** - Usar en planificación de sprints y seguimiento de progreso.

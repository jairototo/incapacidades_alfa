# Reglas de Negocio - Sistema de Gestión de Incapacidades

**Versión**: 2.0  
**Fecha**: Junio 2026  
**Formato**: Especificación de reglas de validación, transición y restricción

---

## Tabla de Contenidos

- [RN-001 a RN-010: Tipos y Ciclo de Vida](#rn-001-a-rn-010-tipos-y-ciclo-de-vida)
- [RN-011 a RN-020: Transiciones de Estado](#rn-011-a-rn-020-transiciones-de-estado)
- [RN-021 a RN-030: Validaciones de Datos](#rn-021-a-rn-030-validaciones-de-datos)
- [RN-031 a RN-040: Control de Acceso](#rn-031-a-rn-040-control-de-acceso)
- [RN-041 a RN-050: Reglas de Pago](#rn-041-a-rn-050-reglas-de-pago)
- [RN-051+: Reglas Adicionales](#rn-051-reglas-adicionales)

---

## RN-001 a RN-010: Tipos y Ciclo de Vida

### RN-001 - Tipos de Incapacidad Exclusiva

**Descripción**:  
Una incapacidad DEBE ser de tipo ARL o SALUD, nunca ambos.

**Justificación**:  
Los flujos de negocio, datos relacionados y validaciones son completamente diferentes. Un tipo "MIXTO" crearías ambigüedad.

**Regla**:
```sql
CHECK (
  (tipo = 'ARL' AND empleado_id IS NOT NULL AND empresa_id IS NOT NULL AND afiliado_id IS NULL)
  OR
  (tipo = 'SALUD' AND afiliado_id IS NOT NULL AND empleado_id IS NULL AND empresa_id IS NULL)
)
```

**Módulos afectados**:
- Modelo: `incapacidad.py`
- Servicios: `incapacidad_service.crear()`

**Casos relacionados**:
- HU-011, HU-017

---

### RN-002 - Incapacidad ARL Requiere Empleado y Empresa

**Descripción**:  
Toda incapacidad ARL DEBE tener referencia a empleado_id y empresa_id obligatorios.

**Justificación**:  
La cadena de pago y auditoría depende de la identificación clara del empleado y empresa.

**Validación**:
- `empleado_id` NOT NULL
- `empresa_id` NOT NULL
- El empleado DEBE pertenecer a la empresa indicada

---

### RN-003 - Incapacidad SALUD Requiere Afiliado

**Descripción**:  
Toda incapacidad SALUD DEBE tener referencia a afiliado_id obligatorio.

**Justificación**:  
El beneficiario es el afiliado, no hay empleador.

**Validación**:
- `afiliado_id` NOT NULL
- `empleado_id` IS NULL
- `empresa_id` IS NULL

---

### RN-004 - Ciclo de Vida de Incapacidad ARL

**Descripción**:  
Toda incapacidad ARL sigue un flujo de estados predefinido desde radicación hasta pago.

**Máquina de estados**:
```
RADICADA (inicial)
    ↓ Auditoría
EN_AUDITORIA
    ├→ OBSERVADA (solicita correcciones, vuelve a EN_AUDITORIA al re-radicar)
    ├→ APROBADA (éxito auditoría)
    └→ RECHAZADA (final - no genera orden)
        ↓ Si APROBADA
EN_PAGO (orden generada)
    ↓ Sistema de pagos procesa
PAGADA (final - orden pagada)

CANCELADA (final - cancelación manual por ADMIN)
```

**Justificación**:  
Asegura que cada incapacidad pase por validaciones antes de pago.

**Módulos afectados**:
- Servicios: `incapacidad_service.py`
- Modelos: `HistorialEstado`

---

### RN-005 - Fecha de Inicio Anterior o Igual a Fecha de Fin

**Descripción**:  
Para toda incapacidad, `fecha_inicio` DEBE ser menor o igual a `fecha_fin`.

**Validación**:
```sql
CHECK (fecha_inicio <= fecha_fin)
```

**Justificación**:  
Validación lógica básica - no puede haber una incapacidad que termina antes de empezar.

**Cálculo dependiente**:
- `dias_totales = fecha_fin - fecha_inicio + 1` (siempre >= 1)

---

### RN-006 - Cálculo Automático de Días Totales

**Descripción**:  
El sistema DEBE calcular automáticamente `dias_totales` como `fecha_fin - fecha_inicio + 1`.

**Justificación**:  
Evita errores manuales en conteo de días. El "+1" incluye ambos días extremos.

**Ejemplo**:
- Fecha inicio: 2026-06-01
- Fecha fin: 2026-06-10
- Días totales: 10 (incluye 1 y 10)

**Módulos afectados**:
- Backend: Validadores de POST/PUT
- Servicios: `incapacidad_service.crear()`, `.actualizar()`

---

### RN-007 - No se Permite Edición de Incapacidad Radicada

**Descripción**:  
Una vez radicada (estado RADICADA), una incapacidad NO se puede editar.

**Excepciones**:
- ADMIN puede hacer cambios (registrado como UPDATE en AUDITORIA_LOG)
- El estado SI puede transicionar según RN-004

**Justificación**:  
Preservar integridad de datos e historial de auditoría.

**Módulos afectados**:
- Servicios: `incapacidad_service.actualizar()` - validar estado antes de UPDATE

---

### RN-008 - Siniestro Opcional en Incapacidad ARL

**Descripción**:  
Una incapacidad ARL PUEDE estar vinculada a un siniestro (accidente laboral), pero es opcional.

**Validación**:
- `siniestro_id` NULL o referencia válida a SINIESTRO
- Si está presente, el SINIESTRO DEBE estar en estado REPORTADO o EN_INVESTIGACION (no CERRADO)
- El empleado del SINIESTRO DEBE coincidir con el empleado de INCAPACIDAD

**Justificación**:  
No todas las incapacidades tienen un siniestro (enfermedad general, consulta). Pero si existe, debe haber coherencia.

---

### RN-009 - Pre-Incapacidad Requiere Solicitante

**Descripción**:  
Toda PRE_INCAPACIDAD DEBE estar vinculada a un SOLICITANTE válido.

**Validación**:
- SOLICITANTE.correo único
- SOLICITANTE.nombres y apellidos requeridos
- SOLICITANTE.telefono opcional

**Justificación**:  
Trazabilidad de quién radica la incapacidad.

**Módulos afectados**:
- Servicios: `solicitante_service.crear_o_actualizar()`

---

### RN-010 - Prioridad Default NORMAL

**Descripción**:  
Toda incapacidad recibe prioridad NORMAL al radicar, a menos que se especifique explícitamente.

**Validación**:
- Valores permitidos: BAJA, NORMAL, ALTA, URGENTE
- Default: NORMAL

**Justificación**:  
Clasificación para auditoría - permite priorizar casos urgentes.

**Módulos afectados**:
- Modelo: `incapacidad.py` (default=Prioridad.NORMAL)

---

## RN-011 a RN-020: Transiciones de Estado

### RN-011 - Transición: RADICADA → EN_AUDITORIA

**Descripción**:  
Cuando un AUDITOR inicia auditoría, la incapacidad transiciona de RADICADA a EN_AUDITORIA.

**Precondiciones**:
- Estado actual: RADICADA
- Usuario: AUDITOR o APROBADOR
- Todos los DOCUMENTO deben estar cargados (al menos 1)

**Acción**:
- Cambiar estado a EN_AUDITORIA
- Registrar HISTORIAL_ESTADO
- Registrar AUDITORIA_LOG con acción CAMBIO_ESTADO

**Postcondiciones**:
- Email notificación al solicitante: "Su incapacidad está siendo auditada"

**Módulos afectados**:
- Servicios: `incapacidad_service.iniciar_auditoria()`

---

### RN-012 - Transición: EN_AUDITORIA → APROBADA

**Descripción**:  
El AUDITOR aprueba la incapacidad después de revisión.

**Precondiciones**:
- Estado actual: RADICADA o EN_AUDITORIA
- Usuario: AUDITOR o APROBADOR
- Todos los documentos validados (documento.validado = true)
- Validaciones de negocio pasadas (RN-038)

**Acción**:
- Cambiar estado a APROBADA
- Registrar HISTORIAL_ESTADO
- Crear AUDITORIA_DATOS_APROBADOS (snapshot JSON)
- Registrar AUDITORIA_LOG

**Postcondiciones**:
- Email: "Incapacidad aprobada"
- Siguiente paso: generar ORDEN_PAGO

**Módulos afectados**:
- Servicios: `incapacidad_service.aprobar()`

---

### RN-013 - Transición: EN_AUDITORIA → OBSERVADA

**Descripción**:  
El AUDITOR marca como OBSERVADA solicitando correcciones.

**Precondiciones**:
- Estado actual: RADICADA o EN_AUDITORIA
- Usuario: AUDITOR o APROBADOR
- Campo "motivo_observacion" obligatorio

**Acción**:
- Cambiar estado a OBSERVADA
- Registrar motivo en HISTORIAL_ESTADO.observacion
- Email al solicitante con motivo

**Postcondiciones**:
- Solicitante puede re-radicar
- Si re-radica: vuelve a EN_AUDITORIA (ciclo)

**Módulos afectados**:
- Servicios: `incapacidad_service.observar()`

---

### RN-014 - Transición: EN_AUDITORIA → RECHAZADA

**Descripción**:  
El AUDITOR rechaza la incapacidad por no cumplir requisitos.

**Precondiciones**:
- Estado actual: RADICADA o EN_AUDITORIA
- Usuario: AUDITOR o APROBADOR
- Campo "motivo_rechazo" obligatorio (mínimo 20 caracteres)

**Acción**:
- Cambiar estado a RECHAZADA
- Guardar motivo en `incapacidad.motivo_rechazo`
- Registrar HISTORIAL_ESTADO
- Email explicando rechazo
- NO genera ORDEN_PAGO

**Postcondiciones**:
- Estado final - no puede volver atrás
- AUDIT:  registro completo del rechazo

**Módulos afectados**:
- Servicios: `incapacidad_service.rechazar()`

---

### RN-015 - Transición: APROBADA → EN_PAGO

**Descripción**:  
Al generar ORDEN_PAGO, la incapacidad transiciona a EN_PAGO.

**Precondiciones**:
- Estado actual: APROBADA
- Usuario: APROBADOR o ADMIN
- ORDEN_PAGO creada exitosamente

**Acción**:
- Cambiar INCAPACIDAD.estado a EN_PAGO
- Registrar HISTORIAL_ESTADO
- AUDITORIA_LOG: acción GENERACION_ORDEN_PAGO

**Postcondiciones**:
- ORDEN_PAGO.estado = GENERADA
- Siguiente: APROBADOR aprueba orden → PAGADA

**Módulos afectados**:
- Servicios: `orden_pago_service.generar()`

---

### RN-016 - Transición: EN_PAGO → PAGADA

**Descripción**:  
Una vez que la ORDEN_PAGO se procesa exitosamente, la INCAPACIDAD va a PAGADA.

**Precondiciones**:
- Estado actual: EN_PAGO
- ORDEN_PAGO.estado = PAGADA
- Confirmación de pago realizado

**Acción**:
- Cambiar INCAPACIDAD.estado a PAGADA
- Registrar HISTORIAL_ESTADO
- Email: "Incapacidad pagada"
- AUDITORIA_LOG: acción PAGO_COMPLETADO

**Postcondiciones**:
- Estado final (completado)

**Módulos afectados**:
- Servicios: `orden_pago_service.confirmar_pago()`

---

### RN-017 - Transición: * → CANCELADA

**Descripción**:  
ADMIN puede cancelar una incapacidad desde cualquier estado (excepto PAGADA).

**Precondiciones**:
- Usuario: ADMIN solo
- Estado actual: NO es PAGADA
- Campo "motivo_cancelacion" obligatorio

**Acción**:
- Cambiar estado a CANCELADA
- Registrar HISTORIAL_ESTADO
- Si hay ORDEN_PAGO: anularla también
- Email: "Incapacidad cancelada"
- Auditoría: acción CANCELACION + motivo

**Postcondiciones**:
- Estado final

**Módulos afectados**:
- Servicios: `incapacidad_service.cancelar()`

---

### RN-018 - Validación de Transición de Estado

**Descripción**:  
El sistema DEBE validar que toda transición de estado sea legal según la máquina de estados (RN-004).

**Transiciones permitidas**:
```
RADICADA → EN_AUDITORIA
EN_AUDITORIA → {OBSERVADA, APROBADA, RECHAZADA}
OBSERVADA → EN_AUDITORIA (re-radicación)
APROBADA → EN_PAGO
EN_PAGO → PAGADA
Cualquier → CANCELADA (si no está PAGADA)
```

**Validación**:
- Función: `es_transicion_valida(estado_actual, estado_nuevo) → bool`
- Si NO es válida: lanzar excepción `InvalidStateTransition`

**Módulos afectados**:
- Servicios: validador en cada método de transición

---

### RN-019 - Registro de Cambio de Estado

**Descripción**:  
Toda transición de estado DEBE registrarse en HISTORIAL_ESTADO inmediatamente.

**Datos capturados**:
- entity_type: 'incapacidad'
- entity_id: UUID de la incapacidad
- estado_anterior: estado antes del cambio
- estado_nuevo: nuevo estado
- observacion: motivo o notas (si aplica)
- fecha_cambio: NOW()
- cambiado_por_id: UUID del usuario

**Justificación**:  
Trazabilidad completa e inmutable del ciclo de vida.

**Módulos afectados**:
- Servicio: `historial_estado_service.registrar_cambio()`

---

### RN-020 - Auditoría de Cambio de Estado

**Descripción**:  
Toda transición de estado TAMBIÉN se registra en AUDITORIA_LOG.

**Datos capturados**:
- usuario_id: usuario que realizó cambio
- accion: 'CAMBIO_ESTADO'
- entidad: 'incapacidad'
- entidad_id: UUID de la incapacidad
- detalles: JSON con estado_anterior, estado_nuevo, motivo

**Justificación**:  
Auditoría de seguridad y compliance.

**Módulos afectados**:
- Servicio: `auditoria_service.registrar_cambio_estado()`

---

## RN-021 a RN-030: Validaciones de Datos

### RN-021 - Validación del Solicitante

**Descripción**:  
Los datos del solicitante DEBEN cumplir validaciones básicas.

**Validaciones**:
- email: formato válido (RFC 5322), único en SOLICITANTE
- nombres: alfanuméricos + espacios, 2-100 caracteres
- apellidos: alfanuméricos + espacios, 2-100 caracteres
- telefono: formato internacional opcional (10-15 dígitos si se proporciona)

**Módulos afectados**:
- Servicios: `solicitante_service.validar()`
- Schemas: Pydantic `SolicitanteCreate`

---

### RN-022 - Validación de Documento de Identidad

**Descripción**:  
Los números de documento DEBEN cumplir validación de tipo.

**Validaciones por tipo**:
- CC (Cédula Colombiana): 5-10 dígitos
- CE (Cédula Extranjería): 6-10 dígitos
- TI (Tarjeta de Identidad): 8-10 dígitos
- PASAPORTE: 6-20 caracteres alfanuméricos
- PEP (Documento temporal): 6-10 dígitos

**Módulos afectados**:
- Servicios: `documento_validator.validar_numero_documento(tipo, numero)`

---

### RN-023 - Validación de Nombres y Apellidos

**Descripción**:  
Nombres y apellidos DEBEN cumplir formato y longitud.

**Validaciones**:
- Caracteres: A-Z, a-z, acentos (á,é,í,ó,ú,ñ), espacios, guiones (O'Brien)
- Mínimo: 2 caracteres
- Máximo: 100 caracteres
- No permitido: números, caracteres especiales (excepto guion y apóstrofo)

**Módulos afectados**:
- Schemas: Pydantic validadores custom

---

### RN-024 - Validación de Fechas

**Descripción**:  
Las fechas de incapacidad DEBEN cumplir reglas de lógica y negocio.

**Validaciones**:
- fecha_inicio: NO puede ser futura (>HOY)
- fecha_fin: NO puede ser futura (>HOY)
- fecha_inicio <= fecha_fin
- Máximo 365 días de duración (RN-006, excepción: ADMIN puede override)

**Módulos afectados**:
- Servicios: `validadores.validar_rango_fechas(inicio, fin)`

---

### RN-025 - Validación de Código CIE-10

**Descripción**:  
El código de diagnóstico DEBE existir en CATALOGO_CIE10.

**Validaciones**:
- Formato: letra + 2 dígitos + punto + 1 dígito (ej: M54.5)
- Debe existir en CATALOGO_CIE10.codigo
- CATALOGO_CIE10.activo = true

**Excepciones**:
- Si código inactivo: advertencia pero permitir (con confirmación)
- Si código no existe: ERROR - no permitir radicación

**Módulos afectados**:
- Servicios: `catalogo_service.validar_cie10(codigo)`
- Backend: endpoint POST incapacidad valida CIE-10

---

### RN-026 - Validación de Documentos Adjuntos

**Descripción**:  
Los archivos adjuntos DEBEN cumplir validaciones de tipo y tamaño.

**Validaciones**:
- Tipos permitidos: PDF, JPG, PNG, DOCX, XLSX
- MIME type validado: application/pdf, image/jpeg, image/png, application/vnd.openxmlformats-officedocument*
- Tamaño máximo por archivo: 10 MB
- Tamaño total máximo por incapacidad: 50 MB
- Mínimo 1 documento (INCAPACIDAD_MEDICA)

**Validación adicional**:
- Calcular hash SHA256 del archivo
- Detectar duplicados: si hash existe en DOCUMENTO, verificar
- Virus scan (si antivirus disponible)

**Módulos afectados**:
- Servicios: `documento_service.validar_archivo()`
- Backend: endpoint POST documentos/upload

---

### RN-027 - Validación de Formato de Archivo

**Descripción**:  
El sistema DEBE validar que el contenido del archivo coincida con su tipo MIME declarado.

**Validaciones**:
- PDF: magic bytes %PDF
- JPG: magic bytes FF D8 FF
- PNG: magic bytes 89 50 4E 47
- DOCX: ZIP con estructura OOXML
- XLSX: ZIP con estructura OOXML

**Justificación**:  
Prevenir ataques de tipo archivo malicioso disfrazado.

**Módulos afectados**:
- Librerías: python-magic para validación
- Servicios: `documento_service.validar_contenido_archivo()`

---

### RN-028 - Validación de Parámetros de Búsqueda

**Descripción**:  
Los parámetros de búsqueda DEBEN ser válidos para prevenir SQL injection e inyección de código.

**Validaciones**:
- Parámetros de filtro: whitelist de campos permitidos
- Valores de enum: validar contra valores permitidos
- Rangos de fecha: formato ISO 8601 (YYYY-MM-DD)
- Texto de búsqueda: máximo 255 caracteres, sanitizar
- Paginación: limit máximo 100, offset >= 0

**Módulos afectados**:
- Schemas: Pydantic `SearchIncapacidadParams`
- Middleware: validación en endpoint

---

### RN-029 - Validación de Montos

**Descripción**:  
Los montos de dinero DEBEN ser positivos y coherentes.

**Validaciones**:
- valor_dia: > 0, máximo 10,000,000 COP (límite razonable)
- valor_total: = valor_dia * dias_totales (verificación)
- Si valor_día es NULL: permitir (será ingresado posteriormente)
- Comparación con salario del empleado:
  - Si valor_día > salario mensual: ADVERTENCIA (pero permitir)
  - Si valor_día < salario_mínimo legal: ERROR

**Módulos afectados**:
- Servicios: `validadores.validar_montos(valor_dia, dias_totales, salario)`

---

### RN-030 - Validación de Datos Bancarios

**Descripción**:  
Los datos bancarios DEBEN ser válidos para procesamiento de pagos.

**Validaciones**:
- cuenta_bancaria: 10-20 dígitos, no contiene letras
- banco: debe existir en lista de bancos autorizados
- tipo_cuenta: AHORROS o CORRIENTE
- Si alguno falta: ERROR al generar ORDEN_PAGO

**Módulos afectados**:
- Servicios: `validadores.validar_datos_bancarios()`
- Backend: endpoint POST generar-orden-pago

---

## RN-031 a RN-040: Control de Acceso

### RN-031 - Control de Acceso Basado en Roles (RBAC)

**Descripción**:  
El acceso a funcionalidades DEBE estar restringido por rol del usuario.

**Roles y permisos**:
- ADMIN: Acceso total, gestión de usuarios
- AUDITOR: Auditar incapacidades, marcar estados
- APROBADOR: Aprobar órdenes de pago, generar órdenes
- EMPRESA: Ver solo incapacidades de su empresa
- EMPLEADO: Ver solo incapacidades propias
- READONLY: Solo lectura, sin operaciones

**Implementación**:
- Función `PermissionChecker([permission1, permission2])` en FastAPI dependencies
- Validación en cada endpoint
- AUDITORIA_LOG registra intentos de acceso denegado

**Módulos afectados**:
- Middleware: `security.py`
- Decoradores: `Depends(PermissionChecker(permissions))`

---

### RN-032 - Validación de Formato de Email

**Descripción**:  
Los emails DEBEN ser válidos según RFC 5322.

**Validación**:
- Regex: `^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`
- Longitud: 6-255 caracteres
- Unicidad: por tabla (USUARIO.email, SOLICITANTE.correo, etc.)

**Módulos afectados**:
- Schemas: Pydantic `EmailStr`
- Validadores custom

---

### RN-033 - Validación de Username

**Descripción**:  
Los usernames DEBEN seguir formato consistente.

**Validación**:
- Caracteres: a-z, 0-9, guión bajo (_), punto (.)
- Mínimo: 6 caracteres
- Máximo: 50 caracteres
- Debe ser único en USUARIO
- No puede contener espacios

**Ejemplos válidos**:
- juan.garcia
- jgarcia_2026
- user.123

---

### RN-034 - Contraseña Segura

**Descripción**:  
Las contraseñas DEBEN cumplir criterios de seguridad.

**Criterios**:
- Mínimo: 8 caracteres
- Debe contener: 1 mayúscula, 1 minúscula, 1 número, 1 especial (!@#$%^&*)
- No puede contener username del usuario
- No puede ser igual a contraseña anterior
- No permitidas contraseñas comunes (top 10000 weak passwords)

**Almacenamiento**:
- Hash con bcrypt (cost factor 12)
- NUNCA se almacena en texto plano

**Módulos afectados**:
- Servicios: `auth_service.validar_contrasena_segura()`
- Librerías: passlib, bcrypt

---

### RN-035 - Bloqueo de Cuenta por Intentos Fallidos

**Descripción**:  
Una cuenta se bloquea automáticamente después de 5 intentos fallidos de login.

**Mecánica**:
- Cada fallo de login: `usuario.intentos_fallidos++`
- Si `intentos_fallidos >= 5`: `usuario.bloqueado_hasta = NOW + 30 minutos`
- Usuario bloqueado: NO puede hacer login
- Después de 30 minutos: auto-desbloqueo o ADMIN desbloquea manualmente
- Login exitoso: `intentos_fallidos = 0`, `bloqueado_hasta = NULL`

**Justificación**:  
Prevención de fuerza bruta / ataques de diccionario.

**Módulos afectados**:
- Servicios: `auth_service.login()`, `.increment_failed_attempts()`
- Modelo: USUARIO (intentos_fallidos, bloqueado_hasta)

---

### RN-036 - Token Version para Invalidación en Masa

**Descripción**:  
El campo `token_version` se incrementa al cambiar contraseña o rol, invalidando todos los JWT activos.

**Mecánica**:
- Cada usuario tiene `token_version` (default: 0)
- Al generar JWT: incluir `token_version` en payload
- Al validar JWT: verificar `token_version` en BD vs JWT
- Si no coinciden: JWT es inválido, requiere re-login
- Incrementar `token_version`: cambio contraseña, cambio rol, logout remoto

**Justificación**:  
Control fine-grained de sesiones sin eliminar tokens de BD.

**Módulos afectados**:
- Servicios: `auth_service.generar_jwt()`, `.validar_jwt()`

---

### RN-037 - Segregación de Datos por Empresa

**Descripción**:  
Usuarios con rol EMPRESA solo pueden ver datos de su empresa.

**Implementación**:
- USUARIO.empresa_id: referencia a su empresa
- En todas las queries: filtrar por `empresa_id`
- Ejemplo: `GET /api/v1/incapacidades` filtra solo incapacidades de su empresa
- ADMIN ve todo, sin filtro

**Justificación**:  
Multi-tenancy - datos privados entre empresas.

**Módulos afectados**:
- Servicios: cada método de búsqueda/lectura
- Middleware: inyectar empresa_id del usuario

---

### RN-038 - Validaciones de Negocio en Auditoría

**Descripción**:  
Al auditar una incapacidad, el sistema DEBE validar ciertos criterios de negocio antes de permitir aprobación.

**Validaciones**:
1. Empleado existe y está activo (estado != RETIRADO)
2. Empresa está activa (estado = ACTIVA)
3. Diagnóstico CIE-10 existe y está activo
4. Documentos requeridos están cargados (mínimo 1)
5. Todos los documentos están validados (documento.validado = true)
6. Rango de fechas es lógico y dentro de límites
7. Montos son coherentes con salario
8. Datos del médico son válidos (nombre y registro)

**Si alguna falla**: mostrar lista de errores al AUDITOR, no permitir aprobación.

**Módulos afectados**:
- Servicios: `incapacidad_service.validar_para_aprobacion()`

---

### RN-039 - Auditoria Logs de Acciones Críticas

**Descripción**:  
Todas las acciones críticas se registran en AUDITORIA_LOG.

**Acciones críticas**:
- LOGIN / LOGOUT (exitoso y fallido)
- CREAR / ACTUALIZAR / ELIMINAR usuario
- CAMBIO_ESTADO de incapacidad
- GENERAR orden de pago
- APROBAR / RECHAZAR orden de pago
- DESCARGAR documento
- EXPORTAR datos
- CAMBIO_CONTRASEÑA

**Datos capturados**:
- usuario_id, accion, entidad, entidad_id
- detalles (JSON)
- ip_address, user_agent, request_id
- created_at

**Retención**:
- Mínimo 12 meses
- GDPR: borrar si usuario lo solicita (cuidado con auditoría)

**Módulos afectados**:
- Middleware: `audit_middleware.py`
- Servicios: `auditoria_service.registrar_accion()`

---

### RN-040 - Sensibilidad de Datos - No Exponer Información

**Descripción**:  
Ciertos datos NO se deben exponer en consultas públicas o a roles no autorizados.

**Restricciones**:
- Consulta pública (HU-021): NO mostrar diagnóstico, documentos, montos
- EMPLEADO (rol): NO puede ver montos de incapacidad (pago es confidencial)
- Público general: NO acceso a USUARIO, EMPLEADO, EMPRESA
- Solo ADMIN y AUDITOR: acceso a AUDITORIA_LOG completo

**Implementación**:
- Schemas Pydantic diferentes según rol
- Ejemplo: `IncapacidadPublicResponse` vs `IncapacidadInternaResponse`

**Módulos afectados**:
- Schemas: múltiples response models
- Endpoints: `depends(get_current_user)` + rol check

---

## RN-041 a RN-050: Reglas de Pago

### RN-041 - Generación Automática de Orden de Pago

**Descripción**:  
Una vez aprobada una incapacidad, ADMIN DEBE generar una ORDEN_PAGO manual (no automático).

**Precondiciones**:
- INCAPACIDAD.estado = APROBADA
- INCAPACIDAD tiene AUDITORIA_DATOS_APROBADOS (snapshot)
- Beneficiario tiene datos bancarios (empleado.cuenta_bancaria)

**Generación**:
- Sistema asigna `numero_orden` secuencial único (OP-2026-000001+)
- Crea ORDEN_PAGO con estado GENERADA
- Transiciona INCAPACIDAD.estado a EN_PAGO
- Registra HISTORIAL_ESTADO

**Justificación**:  
Validar beneficiario y datos bancarios antes de generar orden.

**Módulos afectados**:
- Servicios: `orden_pago_service.generar()`
- Backend: endpoint POST `/api/v1/incapacidades/{id}/generar-orden-pago`

---

### RN-042 - Aprobación de Orden de Pago

**Descripción**:  
Una ORDEN_PAGO DEBE ser aprobada por APROBADOR antes de procesarse.

**Precondiciones**:
- ORDEN_PAGO.estado = GENERADA
- Usuario: APROBADOR o ADMIN
- Beneficiario válido (existe, tiene datos bancarios)
- Monto > 0

**Aprobación**:
- Cambiar estado: GENERADA → APROBADA
- Asignar `aprobado_por_id` y fecha
- Registrar AUDITORIA_LOG
- Generar archivo para envío a banco (integración)

**Postcondiciones**:
- ORDEN_PAGO lista para procesamiento

**Módulos afectados**:
- Servicios: `orden_pago_service.aprobar()`

---

### RN-043 - Validación de Datos del Beneficiario

**Descripción**:  
Los datos del beneficiario DEBEN ser válidos para procesamiento de pago.

**Validaciones**:
- Beneficiario existe (EMPLEADO, AFILIADO, IPS, etc.)
- Beneficiario tiene documento de identidad
- Beneficiario tiene cuenta bancaria (No NULL)
- Cuenta bancaria: formato válido, 10-20 dígitos
- Banco: debe existir en lista de bancos
- Tipo cuenta: AHORROS o CORRIENTE

**Si faltan datos**:
- Estado: ORDEN_PAGO se queda GENERADA
- Error: "Faltan datos bancarios del beneficiario"
- Acción: AUDITOR debe completar datos del beneficiario

**Módulos afectados**:
- Validadores: `orden_pago_service.validar_beneficiario()`

---

### RN-044 - Validación de Cuenta Bancaria

**Descripción**:  
La cuenta bancaria DEBE cumplir formato y validación adicional.

**Validación**:
- Formato: 10-20 dígitos, sin guiones ni espacios
- Banco: código válido (ej: 001 Banco de Bogotá)
- Tipo cuenta: AHORROS o CORRIENTE
- Validación de dígito verificador (si el banco lo requiere)

**Validación externa** (opcional):
- Integración con servicio de validación de cuentas
- Verificar que cuenta existe y es activa

**Módulos afectados**:
- Librerías: validadores de cuenta según banco
- Servicios: `validadores.validar_cuenta_bancaria()`

---

### RN-045 - Procesamiento de Pago por Sistema Externo

**Descripción**:  
El pago es procesado por sistema externo (banco, pasarela de pagos).

**Flujo**:
1. ORDEN_PAGO aprobada se envía a banco (ACH, SPEI, transferencia)
2. Sistema espera respuesta del banco
3. Si exitoso: ORDEN_PAGO.estado = EN_PROCESO, después PAGADA
4. Si falla: ORDEN_PAGO.estado = ANULADA + motivo_anulacion
5. Integración: REST API o archivo batch diario

**Justificación**:  
El dinero es responsabilidad del banco, no del sistema.

**Módulos afectados**:
- Job: `procesar_pagos` (cada 2 horas)
- Integración: API banco

---

### RN-046 - Confirmación Manual de Pago

**Descripción**:  
APROBADOR DEBE confirmar manualmente que el pago se realizó.

**Precondiciones**:
- ORDEN_PAGO.estado = EN_PROCESO
- Usuario: APROBADOR o ADMIN
- Comprobante de pago (número de transacción, recibo)

**Confirmación**:
- Ingresar número de transacción
- Subir comprobante PDF/imagen
- Cambiar estado: EN_PROCESO → PAGADA
- Registrar fecha_pago
- Email: "Pago completado"

**Postcondiciones**:
- INCAPACIDAD.estado = PAGADA
- Ciclo completado

**Módulos afectados**:
- Servicios: `orden_pago_service.confirmar_pago()`
- Backend: endpoint POST `/api/v1/ordenes-pago/{id}/confirmar-pago`

---

### RN-047 - Anulación de Orden de Pago

**Descripción**:  
Una ORDEN_PAGO puede ser anulada si hay error antes de completar el pago.

**Precondiciones**:
- ORDEN_PAGO.estado: GENERADA, APROBADA, o EN_PROCESO
- Usuario: ADMIN solo
- Motivo de anulación (obligatorio)

**Anulación**:
- Cambiar estado: * → ANULADA
- Registrar fecha_anulacion
- Grabar motivo_anulacion
- Revertir INCAPACIDAD.estado a APROBADA (para re-intentar si se desea)
- AUDITORIA_LOG: acción ANULACION_ORDEN_PAGO

**Justificación**:  
Corrección de errores antes de pago definitivo.

**Módulos afectados**:
- Servicios: `orden_pago_service.anular()`

---

### RN-048 - Pago Parcial de Incapacidad

**Descripción**:  
El sistema DEBE soportar pago parcial de una incapacidad (futuro).

**Escenario**:
- Incapacidad por 1,000,000 COP
- Pago inicial: 700,000 COP
- Estado: PAGADA_PARCIALMENTE
- Pendiente: 300,000 COP (orden futura)

**Estados relacionados**:
- APROBADA_PARCIALMENTE
- EN_PAGO_PARCIAL
- PAGADA_PARCIALMENTE

**Justificación**:  
Flexibilidad para casos de revisión y ajuste de montos.

**Módulos afectados**:
- Modelos: ORDEN_PAGO (campo amount_pago_parcial)
- Servicios: lógica de pago parcial

---

### RN-049 - Retención de Comprobantes de Pago

**Descripción**:  
Los comprobantes de pago DEBEN ser retenidos por 7 años (cumplimiento legal).

**Implementación**:
- Archivos de comprobante almacenados en MinIO/S3
- Ruta: `comprobantes/{año}/{mes}/{numero_orden}.pdf`
- Hash SHA256 para integridad
- Backup automático a almacenamiento secundario
- Política de retención: 7 años + 1 mes

**Justificación**:  
Cumplimiento normativo (auditoría fiscal, SOX).

**Módulos afectados**:
- Servicios: `documento_service.guardar_comprobante()`
- Storage: MinIO/S3

---

### RN-050 - Auditoría de Transacciones de Pago

**Descripción**:  
Todas las transacciones de pago se auditan completamente.

**Datos capturados**:
- AUDITORIA_LOG: cada cambio de estado de ORDEN_PAGO
- HISTORIAL_ESTADO: transiciones de INCAPACIDAD
- Detalles: usuario, fecha, monto, beneficiario, cuenta, referencia de transacción
- IP address y user_agent del usuario

**Retención**:
- Indefinida (requerimiento legal)

**Acceso**:
- ADMIN y AUDITOR: acceso completo
- APROBADOR: solo sus propias aprobaciones
- EMPLEADO: solo sus propios pagos (información básica)

**Módulos afectados**:
- Servicios: auditoría en cada acción de pago

---

## RN-051+: Reglas Adicionales

### RN-051 - Validación de Vigencia de Póliza

**Descripción**:  
Para INCAPACIDAD SALUD, el afiliado DEBE tener póliza vigente en la fecha de inicio.

**Validación**:
```sql
CHECK (
  tipo = 'SALUD' 
  AND afiliado.fecha_inicio_poliza <= incapacidad.fecha_inicio 
  AND (afiliado.fecha_fin_poliza IS NULL OR afiliado.fecha_fin_poliza >= incapacidad.fecha_inicio)
)
```

**Justificación**:  
No se puede cobrar incapacidad si no había cobertura.

---

### RN-052 - Notificaciones por Email

**Descripción**:  
El sistema DEBE enviar notificaciones por email en eventos clave.

**Eventos**:
- Radicación recibida (a solicitante)
- Radicación procesada (a solicitante)
- Incapacidad aprobada (a solicitante)
- Incapacidad observada (a solicitante + motivo)
- Incapacidad rechazada (a solicitante + motivo)
- Pago realizado (a solicitante + beneficiario)

**Implementación**:
- Celery task: `enviar_email_notificacion`
- Template: HTML con estilos
- Desuscripción: opción para opt-out

**Módulos afectados**:
- Servicios: `email_service.py`
- Celery: `tasks/email_tasks.py`

---

### RN-053 - Números Secuenciales Únicos

**Descripción**:  
Todos los números de registro (incapacidad, orden de pago, siniestro) son secuenciales únicos.

**Formato**:
- Incapacidad: INC-{YYYY}-{NNNNNN} (ej: INC-2026-000001)
- Orden de pago: OP-{YYYY}-{NNNNNN} (ej: OP-2026-000042)
- Siniestro: SIN-{YYYY}-{NNNNNN}
- Pre-radicación: {YYYYNNNNNN} (202600001+)

**Implementación**:
- Secuencias PostgreSQL
- Reseteadas anualmente (o manual)

---

### RN-054 - Integridad de Datos JSON

**Descripción**:  
Los datos almacenados en campos JSONB (AUDITORIA_DATOS_APROBADOS, detalles, metadata) DEBEN ser válidos.

**Validación**:
- Validar estructura JSON antes de INSERT
- Máximo tamaño: 10 MB por registro
- Campos requeridos según contexto

**Módulos afectados**:
- Validadores Pydantic para JSONB

---

### RN-055 - Backup y Recuperación

**Descripción**:  
La base de datos se debe hacer backup automáticamente y permitir recuperación.

**Política**:
- Backup diario a las 23:00 (horario del servidor)
- Almacenamiento: S3/MinIO con 30 días de retención
- Pruebas de recuperación: mensual
- Documentación de procedimiento RTO/RPO

**Módulos afectados**:
- Infrastructure: script de backup en Docker
- Job: Celery task de backup diario

---

## Matriz de Relaciones HU ↔ RN

| Regla | Historia relacionada | Impacto |
|-------|----------------------|--------|
| RN-001-003 | HU-011, HU-017 | Validación de tipo en radicación |
| RN-004 | HU-011, HU-032, HU-033, HU-041, HU-048 | Máquina de estados |
| RN-031 | HU-001, HU-007 | RBAC en todas las operaciones |
| RN-041-050 | HU-041, HU-042, HU-045, HU-048 | Proceso de pago |

---

*Documento sincronizado con especificación de negocio - Actualización Junio 2026*

# CASOS DE USO

**Versión**: 1.0  
**Última Actualización**: Junio 2026  
**Propósito**: Descripción detallada de 20+ casos de uso del sistema

---

## FORMATO ESTÁNDAR DE CASO DE USO

```
CU-XXX — [Nombre del caso de uso]

**Actores**:
- Actor primario (quién inicia)
- Actores secundarios (sistemas, etc)

**Precondiciones**:
- Condición que debe ser verdadera antes de ejecutar
- ...

**Flujo Principal**:
1. Actor hace algo
2. Sistema responde
3. ...

**Flujos Alternativos**:
A1. Si condición X:
   1. Paso diferente
   2. ...

**Flujos de Excepción**:
E1. Si error Y:
   1. Recuperación

**Postcondiciones**:
- Estado esperado después de completar

**Historias de Usuario Relacionadas**: HU-XXX, HU-YYY

**Reglas de Negocio Relacionadas**: RN-XXX, RN-YYY
```

---

## CU-001 — Autenticación del Usuario

**Actores**:
- Usuario del sistema (primario)
- Sistema de autenticación (secundario)
- Base de datos (secundario)

**Precondiciones**:
- Usuario existe en BD con email registrado
- Usuario no está bloqueado
- Usuario está activo (no eliminado)

**Flujo Principal**:
1. Usuario ingresa a la aplicación
2. Sistema muestra pantalla de login
3. Usuario proporciona email y contraseña
4. Usuario hace click en "Iniciar sesión"
5. Sistema valida formato de email
6. Sistema busca usuario por email en BD
7. Sistema compara contraseña (bcrypt) con hash almacenado
8. Coinciden → Contraseña es correcta
9. Sistema genera JWT access token (15 min validez)
10. Sistema genera JWT refresh token (7 días validez)
11. Sistema guarda refresh_token_hash en BD (SHA256)
12. Sistema reinicia contador de intentos fallidos
13. Sistema registra login en auditoria_log (timestamp, IP, user-agent)
14. Sistema retorna tokens + user data al frontend
15. Frontend almacena access_token en localStorage
16. Sistema redirige a dashboard

**Flujos Alternativos**:

A1. Si email no existe:
   1. Sistema muestra error "Email o contraseña incorrectos"
   2. Incrementa contador de intentos fallidos
   3. Si contador ≥ 5 → (ir a A3)
   4. Usuario puede reintentar

A2. Si contraseña es incorrecta:
   1. Sistema muestra error "Email o contraseña incorrectos" (mismo mensaje, no revela cuál)
   2. Incrementa contador de intentos fallidos
   3. Si contador ≥ 5 → (ir a A3)

A3. Si contador de intentos fallidos ≥ 5:
   1. Sistema bloquea cuenta automáticamente
   2. Establece fecha_bloqueo = NOW()
   3. Establece bloqueado = true
   4. Sistema envía email de seguridad: "Tu cuenta fue bloqueada"
   5. Usuario ve mensaje "Cuenta bloqueada por seguridad. Contacta soporte"
   6. Usuario debe contactar admin o esperar 30 minutos

A4. Si usuario está bloqueado:
   1. Sistema rechaza login
   2. Muestra "Cuenta bloqueada. Contacta soporte"
   3. No intenta validar contraseña

**Flujos de Excepción**:

E1. Si BD está inaccesible:
   1. Sistema registra error en logs
   2. Muestra "Servicio temporalmente no disponible"
   3. Sugiere reintentar en unos momentos

E2. Si email es inválido:
   1. Frontend valida formato antes de enviar (Zod)
   2. Si invalido, muestra "Email inválido" sin llamar API

E3. Si contraseña es vacía:
   1. Frontend valida que no sea vacía
   2. Muestra "Contraseña requerida"

**Postcondiciones**:
- Usuario está autenticado (token válido)
- Puede acceder a recursos protegidos
- Su rol determina qué recursos ve
- Login registrado en auditoria_log
- Timestamp de último_login actualizado

**Historias de Usuario Relacionadas**: HU-001

**Reglas de Negocio Relacionadas**: RN-040 (Autenticación), RN-042 (Bloqueo de cuenta)

---

## CU-002 — Registrar Nueva Incapacidad (Radicación)

**Actores**:
- Empresa/Gestor de RR.HH. (primario) — rol EMPRESA
- Sistema de radicación (secundario)
- Base de datos (secundario)
- Celery task queue (secundario) — para notificaciones

**Precondiciones**:
- Actor está autenticado (tiene token JWT válido)
- Actor tiene rol EMPRESA o EMPLEADO
- Empresa/Empleado existe en BD
- Empleado pertenece a la empresa

**Flujo Principal**:
1. Actor accede a Portal Externo (http://localhost:5173)
2. Sistema muestra página HOME
3. Actor hace click en botón "Radicar Incapacidad"
4. Sistema redirige a ruta /radicar
5. Sistema muestra Wizard de 6 pasos

**Paso 1: Seleccionar Tipo**:
6. Sistema muestra opciones: ARL, SALUD
7. Actor selecciona tipo
8. Actor hace click "Siguiente"
9. Wizard avanza a paso 2

**Paso 2: Datos del Trabajador**:
10. Si tipo=ARL:
    - Sistema muestra campo autocomplete de empleados
    - Actor busca empleado por nombre/documento
    - Sistema retorna lista de empleados de su empresa
    - Actor selecciona empleado
    - Sistema auto-completa datos (empresa, etc)
11. Si tipo=SALUD:
    - Sistema muestra campo autocomplete de afiliados
    - Actor busca afiliado por nombre/documento
    - Actor selecciona afiliado

**Paso 3: Fechas de Incapacidad**:
12. Sistema muestra campos: Fecha Inicio, Fecha Fin
13. Actor selecciona fecha inicio (date picker con validación: no futura)
14. Actor selecciona fecha fin (debe ser ≥ fecha inicio)
15. Sistema calcula automáticamente: días_totales = fin - inicio + 1
16. Sistema muestra días totales calculados

**Paso 4: Diagnóstico**:
17. Sistema muestra campo autocomplete de CIE-10
18. Actor busca código o descripción
19. Sistema retorna resultados (max 10)
20. Actor selecciona diagnóstico
21. Sistema valida que código CIE-10 exista

**Paso 5: Documentos**:
22. Sistema muestra área de upload (drag-drop o click)
23. Actor carga archivo (PDF, PNG, JPG — max 10MB)
24. Sistema valida tipo y tamaño
25. Sistema carga archivo a MinIO/filesystem
26. Sistema calcula hashes MD5, SHA256
27. Sistema muestra confirmación: "Documento subido"
28. Actor puede subir múltiples documentos
29. Actor hace click "Siguiente" cuando termina

**Paso 6: Revisión y Confirmación**:
30. Sistema muestra resumen de todos los datos
31. Actor revisa información
32. Actor hace click "Radicar"
33. Frontend valida con Zod todos los campos
34. Frontend envía POST /api/v1/incapacidades/radicar
35. Backend recibe solicitud
36. Backend valida token JWT → Usuario autenticado
37. Backend valida rol → Tiene permiso
38. Backend valida RN-001 a RN-020 (todas las reglas)
39. Backend genera número radicado único (AAAAMMNNNNNN)
40. Backend crea transacción DB BEGIN
41. Backend INSERT en tabla incapacidad
42. Backend INSERT en tabla documento (para cada archivo)
43. Backend INSERT en tabla historial_estado (estado=RADICADA)
44. Backend COMMIT transacción
45. Trigger en BD: registra evento en historial_estado
46. Backend invalida cache Redis
47. Backend publica tarea Celery: radicar_incapacidad_automatica_task
48. Backend retorna 201 CREATED con:
    - número de radicado
    - ID incapacidad
    - timestamp radicación
    - estado RADICADA
49. Frontend muestra pantalla de ÉXITO
50. Pantalla contiene:
    - "¡Radicación Exitosa!"
    - Número radicado (destacado)
    - Botón "Descargar Comprobante"
    - Botón "Hacer Nueva Radicación"
    - Enlace "Consultar Estado"
51. Sistema envía email al solicitante con:
    - Número radicado
    - Enlace de consulta
    - Próximos pasos
52. Celery Worker ejecuta tarea asíncrona:
    - Inserta auditoria_log
    - Envía notificaciones adicionales

**Flujos Alternativos**:

A1. Si actor hace click "Atrás" en cualquier paso:
   1. Wizard retrocede al paso anterior
   2. Datos se mantienen en memoria/localStorage

A2. Si actor quiere guardar en borrador:
   1. En cualquier paso, hace click "Guardar como Borrador"
   2. Frontend envía datos a POST /api/v1/pre-incapacidades
   3. Backend crea registro en tabla pre_incapacidad
   4. Estado = BORRADOR
   5. Paso completado = índice actual
   6. Datos se guardan en JSON
   7. Documentos se vinculan con pre_incapacidad
   8. Usuario puede volver después y continuar desde donde dejó

A3. Si actor cancela:
   1. Hace click "Cancelar"
   2. Sistema pide confirmación
   3. Si confirma: Borra datos en memoria, redirige a home
   4. Si tenía pre_incapacidad sin radicar: queda guardada (expira en 30 días)

**Flujos de Excepción**:

E1. Si número radicado ya existe:
   1. Backend detecta constraint UNIQUE violation
   2. Retorna 409 Conflict
   3. Sistema reintentan generación de número
   4. Si problema persiste: retorna 500 Internal Server Error

E2. Si documento no se puede subir a MinIO:
   1. Backend retorna error de almacenamiento
   2. Frontend muestra: "Error al subir documento, reintente"
   3. Usuario puede reintentar

E3. Si validación Pydantic falla en backend:
   1. Backend retorna 400 Bad Request
   2. Especifica qué campo es inválido
   3. Frontend muestra error específico
   4. Usuario puede corregir

E4. Si usuario pierde conexión durante upload:
   1. Usuario hace click "Guardar como Borrador"
   2. Progreso se preserva
   3. Cuando reconecta, continúa desde donde dejó

E5. Si empleado no existe en BD:
   1. Backend rechaza: 404 Not Found
   2. Frontend muestra error
   3. Usuario debe revisar datos del empleado

**Postcondiciones**:
- Incapacidad creada en BD con estado RADICADA
- Número radicado asignado (único)
- Documentos guardados en almacenamiento (MinIO/FS)
- Entrada en historial_estado registrada
- Email de confirmación enviado
- Tarea Celery encolada
- Usuario redirigido a página de éxito
- Puede consultar estado con número radicado

**Historias de Usuario Relacionadas**: HU-011 (ARL), HU-019 (SALUD), HU-012 (Validación), HU-020 (Comprobante)

**Reglas de Negocio Relacionadas**: RN-001 (Tipos), RN-002 (Radicado único), RN-003 (Ciclo vida), RN-005 (Validación)

---

## CU-003 — Consultar Estado Públicamente

**Actores**:
- Público / Solicitante (primario) — sin autenticación
- Sistema de consulta (secundario)
- Redis Cache (secundario)

**Precondiciones**:
- Incapacidad existe en BD
- Tiene número radicado válido (AAAAMMNNNNNN)

**Flujo Principal**:
1. Usuario accede a Portal Externo
2. Hace click en "Consultar Estado"
3. Sistema redirige a /consultar
4. Sistema muestra formulario con campo "Número Radicado"
5. Usuario ingresa número (ej: 202606001234)
6. Usuario hace click "Buscar"
7. Frontend valida formato
8. Frontend envía GET /api/v1/incapacidades/consultar?numero_radicado=202606001234
9. Backend NO requiere autenticación (endpoint público)
10. Backend busca en Redis cache primero (TTL 5 min)
11. Si en cache → Retorna resultado cached
12. Si no en cache:
    - Backend consulta PostgreSQL: SELECT * FROM incapacidad WHERE numero = ?
    - Si no existe → Retorna 404
    - Si existe → Prepara respuesta
13. Backend retorna JSON con:
    - número_radicado: 202606001234
    - estado: EN_AUDITORIA
    - tipo: ARL
    - fecha_radicacion: 2026-06-03T10:30:00Z
    - fecha_inicio: 2026-06-01
    - fecha_fin: 2026-06-15
    - dias_totales: 15
    - mensaje_amigable: "Su incapacidad está siendo revisada por nuestro equipo de auditoría"
    - estimado_dias: 3 (estimado de cuántos días falta)
14. Backend guarda en Redis con TTL 5 minutos
15. Frontend recibe respuesta 200 OK
16. Sistema muestra:
    - Número radicado ingresado
    - Estado actual con icono y color
    - Fechas de incapacidad
    - Mensaje amigable sobre estado
    - Barra de progreso del workflow
    - Botón "Volver a buscar"

**Flujos Alternativos**:

A1. Si número radicado no existe:
   1. Backend retorna 404 Not Found
   2. Frontend muestra: "No encontramos incapacidad con este número"
   3. Sugiere verificar número o contactar
   4. Ofrece búsqueda alternativa por documento (si se pasa)

A2. Si usuario proporciona documento también:
   1. Endpoint GET /incapacidades/consultar?numero=X&documento=Y
   2. Backend valida también que documento coincida
   3. Si no coincide → 403 Forbidden (protección de privacidad)
   4. Si coincide → Retorna información

**Flujos de Excepción**:

E1. Si número está en formato inválido:
   1. Frontend valida antes de enviar
   2. Muestra: "Formato inválido. Debe ser AAAAMMNNNNNN"

E2. Si BD está caída:
   1. Backend retorna 500 Internal Server Error
   2. Frontend muestra: "Servicio temporalmente no disponible"

E3. Si cache (Redis) está caído:
   1. Backend continúa sin cache (sin retornar error)
   2. Consulta directamente BD
   3. Tarda un poco más pero funciona

**Postcondiciones**:
- Usuario conoce estado actual de su incapacidad
- No necesita autenticación
- Información pública (no datos sensibles)
- Consulta registrada para analytics (opcional)

**Historias de Usuario Relacionadas**: HU-021 (Consulta pública)

**Reglas de Negocio Relacionadas**: RN-002 (Radicado único)

---

## CU-004 — Auditar Incapacidad

**Actores**:
- Auditor (primario) — rol AUDITOR
- Sistema de auditoría (secundario)
- Base de datos (secundario)

**Precondiciones**:
- Incapacidad existe en BD
- Estado de incapacidad = EN_AUDITORIA
- Auditor está autenticado (rol AUDITOR)
- Documentos están disponibles

**Flujo Principal**:
1. Auditor accede a Sistema Interno
2. Hace login con email/password
3. Sistema redirige a dashboard
4. Auditor hace click en "Auditorías Pendientes"
5. Sistema muestra lista de incapacidades EN_AUDITORIA
6. Auditor busca y selecciona una incapacidad
7. Auditor hace click en "Ver Detalles"
8. Sistema carga GET /incapacidades/{id} (con token AUDITOR)
9. Backend valida token AUDITOR tiene permiso
10. Backend retorna incapacidad completa:
    - Datos básicos
    - Empleado/Afiliado
    - Empresa
    - Documentos (lista con nombres, tamaños)
    - Historial estado anterior
    - Siniestro (si aplica)
11. Frontend muestra panel con:
    - Información del caso
    - Botones "Aprobar", "Observar", "Rechazar"
    - Área de documentos con previsualizaciones
    - Área de observaciones
12. Auditor revisa documentos (click para ver, descargar)
13. Auditor lee los documentos
14. Auditor valida contra reglas de negocio (RN-003 a RN-015 mentalmente)
15. Auditor decide: Aprobar, Observar, o Rechazar

**Subproceso: Si Auditor Aprueba**:
16a. Auditor hace click "Aprobar"
17a. Sistema muestra modal de confirmación
18a. Auditor ingresa observaciones opcionales
19a. Auditor hace click "Confirmar Aprobación"
20a. Frontend envía PATCH /incapacidades/{id}/auditar
20b. Body: {nuevo_estado: "APROBADA", observaciones: "..."}
21a. Backend valida transición EN_AUDITORIA → APROBADA (RN-003)
22a. Backend crea transacción DB BEGIN
23a. Backend UPDATE incapacidad SET estado = APROBADA
24a. Backend INSERT historial_estado (EN_AUDITORIA → APROBADA)
25a. Backend INSERT auditoria_datos_aprobados (snapshot de datos aprobados)
26a. Backend COMMIT
27a. Trigger en BD registra nuevo historial
28a. Backend invalida cache
29a. Backend publica tarea: aprobacion_automatica_task
30a. Backend retorna 200 OK
31a. Frontend muestra: "Aprobación registrada exitosamente"
32a. Auditor redirigido a lista de pendientes

**Subproceso: Si Auditor Observa**:
16b. Auditor hace click "Observar"
17b. Sistema muestra modal con lista de observaciones
18b. Auditor selecciona problemas encontrados (checkboxes):
    - Certificado médico vencido
    - Falta firma del empleador
    - Datos inconsistentes
    - Etc.
19b. Auditor puede agregar observaciones libres
20b. Auditor hace click "Enviar Observaciones"
21b. Frontend envía PATCH /incapacidades/{id}/observar
22b. Body: {nuevo_estado: "OBSERVADA", observaciones: [...]}
23b. Backend valida y actualiza
24b. Incapacidad estado = OBSERVADA
25b. Sistema envía email al solicitante:
    - "Tu incapacidad tiene observaciones"
    - Lista de problemas
    - "Debes corregir y reenviar dentro de 5 días"
    - Link para reenviar
26b. Auditor ve confirmación

**Subproceso: Si Auditor Rechaza**:
16c. Auditor hace click "Rechazar"
17c. Sistema muestra modal con motivo de rechazo
18c. Auditor selecciona motivo (dropdown):
    - Documentación insuficiente
    - Datos no coinciden
    - Incapacidad no aplica
    - Etc.
19c. Auditor ingresa descripción completa del rechazo
20c. Auditor hace click "Rechazar Incapacidad"
21c. Frontend envía PATCH /incapacidades/{id}/rechazar
22c. Body: {nuevo_estado: "RECHAZADA", motivo_rechazo: "..."}
23c. Backend valida y actualiza
24c. Incapacidad estado = RECHAZADA (terminal)
25c. Sistema envía email:
    - "Tu incapacidad fue rechazada"
    - Motivo específico
    - No hay posibilidad de corrección/reenvío
26c. Auditor ve confirmación

**Flujos Alternativos**:

A1. Si incapacidad tiene documentos faltantes:
   1. Auditor hace click "Solicitar Documentos"
   2. Sistema muestra checklist de tipos de documentos
   3. Auditor selecciona cuáles faltan
   4. Auditor hace click "Enviar Solicitud"
   5. Sistema envía email: "Se requieren documentos adicionales"
   6. Incapacidad sigue EN_AUDITORIA pero con flag
   7. Auditor puede continuar con otros casos
   8. Cuando solicitante envía documentos → Auditor recibe notificación

A2. Si auditor necesita más tiempo:
   1. Auditor puede "Posponer" auditoría
   2. Incapacidad se mueve al final de la cola
   3. Auditor continúa con otros casos

A3. Si auditor necesita consultar:
   1. Puede agregar nota privada (solo para equipo)
   2. Puede asignar a otro auditor para segunda opinión

**Flujos de Excepción**:

E1. Si documento no se carga:
   1. Frontend muestra: "No se pudo cargar documento"
   2. Auditor puede reintentar o descargar

E2. Si token JWT expira durante auditoría:
   1. Sistema lo redirige a login
   2. Datos no se pierden (frontend tiene guardado)
   3. Después de login, continúa

E3. Si BD falla al guardar:
   1. Backend retorna error
   2. Frontend muestra: "Error al guardar, reintente"
   3. Cambios no se aplican
   4. Auditor puede reintentar

**Postcondiciones**:
- Incapacidad cambió de estado (APROBADA, OBSERVADA o RECHAZADA)
- Historial_estado actualizado
- Solicitante notificado por email
- Auditor redirigido a lista pendiente
- Caso completado o en espera de correcciones

**Historias de Usuario Relacionadas**: HU-031 (Ver pendientes), HU-035 (Aprobar), HU-036 (Observar), HU-037 (Rechazar)

**Reglas de Negocio Relacionadas**: RN-003 (Transiciones), RN-025 (Auditoría)

---

## CU-005 — Subir Documento

**Actores**:
- Usuario autenticado (primario)
- Sistema de almacenamiento (secundario)
- MinIO/Filesystem (secundario)

**Precondiciones**:
- Usuario autenticado (token JWT válido)
- Archivo ≤ 10MB
- Tipo de archivo permitido (PDF, PNG, JPG)

**Flujo Principal**:
1. Usuario está en formulario de radicación (Paso 5)
2. Usuario hace click en área de upload o "Seleccionar Archivo"
3. Se abre selector de archivos del SO
4. Usuario selecciona archivo (ej: certificado_medico.pdf — 2MB)
5. Frontend valida:
   - Tamaño ≤ 10MB ✓
   - Extensión permitida ✓
   - MIME type es válido ✓
6. Frontend muestra preview/ícono
7. Usuario hace click "Subir" (o automático al seleccionar)
8. Frontend envía multipart/form-data a POST /documentos/subir
9. Body:
   - archivo: [binary content]
   - tipo: CERTIFICADO_MEDICO
   - descripcion: "Certificado de médico tratante"
10. Backend recibe solicitud
11. Backend valida token JWT → Autenticado
12. Backend valida permisos → Puede subir
13. Backend valida tamaño y tipo nuevamente
14. Backend genera nombre sanitizado: {uuid}.pdf
15. Backend envía archivo a MinIO:
    - Bucket: "incapacidades"
    - Key: "documents/{uuid}.pdf"
    - ACL: private
    - Metadata: {original_name, uploaded_by_id, created_at}
16. MinIO confirma almacenamiento
17. Backend calcula hashes:
    - MD5: abc123def456...
    - SHA256: xyzabc123...
18. Backend crea INSERT en tabla documento:
    - nombre_original: "certificado_medico.pdf"
    - nombre_almacenado: "{uuid}.pdf"
    - tipo: CERTIFICADO_MEDICO
    - tamanio: 2097152
    - ruta: "incapacidades/documents/{uuid}.pdf"
    - hash_md5: "abc123def456..."
    - hash_sha256: "xyzabc123..."
    - subido_por_id: {user_id}
    - creado_en: NOW()
19. Backend retorna 201 CREATED con:
    - id: {document_id}
    - nombre_original: "certificado_medico.pdf"
    - tipo: CERTIFICADO_MEDICO
    - tamanio: 2097152
    - url_descarga: "/api/v1/documentos/{document_id}/descargar"
20. Frontend recibe respuesta
21. Frontend muestra: "Documento subido exitosamente"
22. Frontend agrega documento a lista de documentos del wizard
23. Usuario puede subir más documentos o continuar

**Flujos Alternativos**:

A1. Si usuario selecciona con drag-drop:
   1. Usuario arrastra archivo al área especial
   2. Se activa evento ondrop
   3. Se comporta igual que selección manual

A2. Si usuario cancela upload a mitad:
   1. Frontend detiene transmisión
   2. Archivo no se guarda en MinIO
   3. DB tampoco tiene registro

A3. Si usuario sube documento duplicado (mismo MD5):
   1. Backend detecta hash_md5 igual
   2. Puede: Rechazar ("Ya existe este documento") o
   3. Permitir con advertencia

**Flujos de Excepción**:

E1. Si archivo supera 10MB:
   1. Frontend valida antes de enviar
   2. Muestra: "Archivo demasiado grande (máx 10MB)"

E2. Si tipo de archivo no permitido (ej: .exe):
   1. Frontend rechaza por extensión
   2. Muestra: "Tipo de archivo no permitido"

E3. Si MinIO está caído:
   1. Backend retorna 503 Service Unavailable
   2. Frontend muestra: "Error de almacenamiento, reintente"
   3. Usuario puede reintentar

E4. Si BD falla:
   1. Archivo se guardó en MinIO pero no se registró en BD
   2. Backend retorna error
   3. Se dispara task de limpieza asincróna
   4. Archivo se elimina de MinIO después de 1 hora (sin referencia en BD)

E5. Si conexión se cae:
   1. Upload se interrumpe
   2. Frontend puede reintentar

**Postcondiciones**:
- Documento guardado en MinIO/Filesystem
- Registro en tabla documento creado
- Usuario ve documento en lista del wizard
- Hash calculado y almacenado para verificación
- Documento vinculado con pre_incapacidad (o incapacidad después)

**Historias de Usuario Relacionadas**: HU-011 (Radicación)

**Reglas de Negocio Relacionadas**: RN-020 (Documentos)

---

## CU-006 — Generar Orden de Pago

**Actores**:
- Administrador (primario) — rol ADMIN
- Sistema de órdenes de pago (secundario)
- Base de datos (secundario)

**Precondiciones**:
- Incapacidad existe en BD
- Estado = APROBADA
- Admin está autenticado

**Flujo Principal**:
1. Admin accede a Sistema Interno
2. Navega a "Órdenes de Pago" > "Crear"
3. Sistema muestra formulario de creación
4. Admin ingresa:
   - Número radicado o ID incapacidad (autocomplete)
   - Backend busca incapacidad: GET /incapacidades?numero=X
   - Si estado ≠ APROBADA → Error
   - Si estado = APROBADA → Carga datos
5. Sistema auto-completa:
   - Monto total = valor_total de incapacidad
   - Beneficiario = nombre empleado/afiliado
   - Fecha radicación
6. Admin revisa datos
7. Admin puede ajustar:
   - Monto (si es pago parcial): cambiar a 50% del total
   - Descuentos (retenciones): 20% por impuesto, 5% por otro concepto
8. Sistema calcula automáticamente:
   - Monto neto = Monto total - Descuentos
   - Impuestos retenidos = Suma de descuentos
9. Admin hace click "Generar Orden"
10. Frontend envía POST /ordenes-pago
11. Body:
    - incapacidad_id: {id}
    - monto_total: 750000.00
    - monto_neto: 600000.00
    - detalles_descuentos: [
        {concepto: "Retención 20%", valor: 150000.00}
      ]
12. Backend valida:
    - Incapacidad existe
    - Estado = APROBADA
    - Monto ≤ valor_total
13. Backend genera número único: OP-2026-00001
14. Backend crea INSERT en orden_pago:
    - numero_orden: "OP-2026-00001"
    - incapacidad_id: {id}
    - estado: GENERADA
    - monto_total: 750000.00
    - monto_neto: 600000.00
    - impuestos_retenidos: 150000.00
    - creado_en: NOW()
15. Backend INSERT en historial_estado:
    - entidad_tipo: ORDEN_PAGO
    - entidad_id: {order_id}
    - estado_anterior: NULL
    - estado_nuevo: GENERADA
    - razon: "Orden generada por admin"
16. Backend invalida cache
17. Backend retorna 201 CREATED con orden completa
18. Frontend muestra: "Orden generada exitosamente"
19. Sistema muestra número de orden (OP-2026-00001)
20. Admin puede:
    - Imprimir orden
    - Enviar a aprobador
    - Crear otra orden

**Flujos Alternativos**:

A1. Si es pago parcial:
   1. Admin ingresa monto < valor_total
   2. Sistema acepta
   3. Incapacidad estado se convierte a EN_PAGO_PARCIAL
   4. Se genera nueva orden por saldo restante (automático o manual)

A2. Si hay líneas de descuento complejas:
   1. Admin hace click "Agregar Descuento"
   2. Ingresa concepto y valor
   3. Se calcula automáticamente monto_neto

**Flujos de Excepción**:

E1. Si incapacidad no está APROBADA:
   1. Backend rechaza: "Incapacidad debe estar APROBADA"
   2. Frontend muestra error

E2. Si monto_total supera presupuesto (regla de negocio):
   1. Backend valida contra límite
   2. Si supera → Requiere aprobación adicional (doble click)

E3. Si BD falla:
   1. Transacción se revierte
   2. Error al usuario

**Postcondiciones**:
- Orden de pago creada con estado GENERADA
- Número de orden asignado
- Historial_estado registrado
- Orden lista para aprobación por APROBADOR
- Incapacidad puede cambiar a EN_PAGO (después de aprobación de orden)

**Historias de Usuario Relacionadas**: HU-041 (Crear orden)

**Reglas de Negocio Relacionadas**: RN-030 (Órdenes de pago)

---

## CU-007 — Procesar Pago

**Actores**:
- Pagador (primario) — rol ADMIN, PAGADOR
- Banco (secundario) — sistema externo
- Sistema de pago (secundario)

**Precondiciones**:
- Orden de pago existe en BD
- Estado = APROBADA
- Pagador está autenticado

**Flujo Principal**:
1. Pagador accede a Sistema Interno
2. Navega a "Órdenes de Pago" > "Pendientes"
3. Sistema muestra listado de órdenes APROBADAS
4. Pagador selecciona orden (ej: OP-2026-00001)
5. Pagador hace click "Procesar Pago"
6. Sistema muestra formulario:
   - Número orden: OP-2026-00001
   - Monto: 600000.00
   - Beneficiario: Juan Pérez (parcialmente enmascarado: Juan P****)
   - Fecha: 2026-06-03
7. Pagador ingresa detalles de pago:
   - Método: TRANSFERENCIA_BANCARIA (dropdown)
   - Banco destino: Banco Bogotá
   - Número de cuenta: 123456789 (parcialmente enmascarado)
   - Número de comprobante: REF-2026-001 (referencia del banco)
8. Pagador revisa datos
9. Pagador hace click "Confirmar Pago"
10. Sistema pide confirmación adicional (double-check)
11. Pagador confirma
12. Frontend envía PATCH /ordenes-pago/{id}/pagar
13. Body:
    - metodo_pago: "TRANSFERENCIA_BANCARIA"
    - banco_destino: "Banco Bogotá"
    - numero_cuenta: "123456789"
    - numero_comprobante: "REF-2026-001"
14. Backend valida:
    - Orden existe
    - Estado = APROBADA
    - Monto válido
15. Backend crea transacción DB BEGIN
16. Backend UPDATE orden_pago:
    - estado: PAGADA
    - metodo_pago: "TRANSFERENCIA_BANCARIA"
    - banco_destino: "Banco Bogotá"
    - numero_cuenta: "123456789"
    - numero_comprobante: "REF-2026-001"
    - fecha_pago: NOW()
17. Backend INSERT historial_estado:
    - entidad_tipo: ORDEN_PAGO
    - entidad_id: {order_id}
    - estado_anterior: APROBADA
    - estado_nuevo: PAGADA
    - razon: "Pago procesado por transferencia"
18. Backend UPDATE incapacidad (vinculada):
    - estado: PAGADA
19. Backend INSERT historial_estado (incapacidad):
    - APROBADA → PAGADA
20. Backend COMMIT
21. Backend invalida cache
22. Backend publica tarea Celery: pago_completado_task
23. Backend retorna 200 OK
24. Frontend muestra: "Pago procesado exitosamente"
25. Celery task ejecuta:
    - Inserta auditoria_log
    - Genera comprobante PDF
    - Envía email a beneficiario con comprobante
    - Email contiene: orden número, monto, referencia banco
26. Beneficiario recibe email con link de descarga

**Flujos Alternativos**:

A1. Si es pago parcial:
   1. Pagador ingresa monto_pagado < monto_total_orden
   2. Backend crea segundo transición: EN_PAGO_PARCIAL
   3. Genera nueva orden por saldo restante
   4. Usuario vuelve a procesar segundo pago después

A2. Si hay problema con cuenta bancaria:
   1. Banco rechaza transferencia (número de cuenta inválido)
   2. Sistema retorna: "Error en transferencia, verificar cuenta"
   3. Pagador rectifica datos
   4. Reintentar

**Flujos de Excepción**:

E1. Si orden ya fue pagada (race condition):
   1. Backend detecta estado ≠ APROBADA
   2. Retorna 409 Conflict: "Esta orden ya fue pagada"

E2. Si BD falla:
   1. Transacción revierte
   2. Orden sigue APROBADA
   3. Usuario puede reintentar

E3. Si email no se envía:
   1. Pago se registra igual
   2. Task de reenvío encolada (retry exponencial)
   3. Beneficiario puede descargar comprobante manualmente

**Postcondiciones**:
- Orden de pago estado = PAGADA
- Incapacidad estado = PAGADA
- Historial_estado actualizado (ambas entidades)
- Comprobante PDF generado
- Email enviado a beneficiario
- Auditoria_log registrado

**Historias de Usuario Relacionadas**: HU-044 (Ejecutar pago), HU-050 (Comprobante)

**Reglas de Negocio Relacionadas**: RN-030 (Órdenes), RN-035 (Cierre de casos)

---

*Más casos de uso disponibles: CU-008 (Importación de empleados), CU-009 (Búsqueda avanzada), CU-010 (Exportar reportes), etc.*

**Total de casos de uso**: 20+

---

**Documento de referencia** - Usar para validación de flujos, testing, y capacitación de usuarios.

# VALIDACIONES DEL SISTEMA

**Versión**: 1.0  
**Categorías**: 5 módulos x 40+ validaciones  
**Cobertura**: Frontend + Backend

---

## 1. VALIDACIONES GENERALES

### VAL001: Campo Obligatorio
**Aplica**: Todos los campos requeridos  
**Tipo**: Validación de presencia  
**Implementación**: Frontend (React Hook Form) + Backend (Pydantic)

```
Si campo.value === "" o null o undefined:
  → Error: "[Campo] es obligatorio"
  → Mostrar alerta roja en UI
  → Bloquear envío de formulario
```

### VAL002: Eliminación de Espacios
**Aplica**: Todos los campos de texto  
**Tipo**: Normalización  
**Implementación**: Backend (middleware)

```
valor_recibido = "  Juan Pérez  "
valor_procesado = "Juan Pérez"
```

### VAL003: Longitud Máxima
**Aplica**: Todos los campos texto  
**Tipo**: Restricción de tamaño

| Campo | Mínimo | Máximo |
|-------|--------|--------|
| Nombres | 2 | 100 |
| Apellidos | 2 | 100 |
| Razón Social | 3 | 255 |
| Email | 5 | 254 |
| Teléfono | 7 | 15 |
| Descripción Accidente | 30 | 2000 |
| Observaciones | 0 | 1000 |

### VAL004: Caracteres Válidos
**Aplica**: Todos los campos  
**Tipo**: Restricción de contenido

| Tipo de Campo | Caracteres Permitidos |
|---------------|----------------------|
| Nombre/Apellido | A-Z, a-z, ñ, tildes, espacios, guión |
| Número | 0-9 |
| Email | a-z, 0-9, ., -, _ , @ |
| Teléfono | 0-9, +, - |
| Descripción | A-Z, a-z, números, puntuación básica |

---

## 2. VALIDACIONES DE DOCUMENTO DE IDENTIDAD

### VAL005: Tipo de Documento Obligatorio
**Aplica**: Todos los solicitantes, trabajadores, afiliados  
**Tipo**: Selección requerida  
**Valores permitidos**:
- CC: Cédula de Ciudadanía
- CE: Cédula de Extranjería
- TI: Tarjeta de Identidad
- PAS: Pasaporte
- NIT: Número de Identificación Tributaria
- PEP: Permiso Especial de Permanencia
- PPT: Permiso de Protección Temporal

```
Si tipo_documento.value === "":
  → Error: "Tipo de documento es obligatorio"
  → Habilitar búsqueda en catálogo
```

### VAL006: Número de Documento Obligatorio
**Aplica**: Todos los solicitantes, trabajadores, afiliados  
**Tipo**: Validación de presencia

### VAL007: Número de Documento - Solo Numérico
**Aplica**: Documento numérico  
**Tipo**: Formato

```
Si documento.valor contiene caracteres no numéricos:
  → Error: "El número de documento debe contener solo números"
  → Bloquear entrada no numérica
```

### VAL008: Longitud de Documento Según Tipo
**Aplica**: Validación cruzada  
**Tipo**: Regla de negocio

| Tipo | Longitud | Formato |
|------|----------|---------|
| CC | 8-12 | Numérico |
| CE | 8-12 | Numérico |
| TI | 5-10 | Numérico |
| PAS | 5-15 | Alfanumérico |
| NIT | 9 | Numérico + dígito verificador |
| PEP | 11 | Numérico |
| PPT | 12 | Alfanumérico |

---

## 3. VALIDACIONES DE NOMBRE

### VAL009: Primer Nombre Obligatorio
**Aplica**: Solicitantes, trabajadores, afiliados  
**Tipo**: Presencia

### VAL010: Apellidos Obligatorios
**Aplica**: Solicitantes, trabajadores, afiliados  
**Tipo**: Presencia  
**Nota**: Algunos casos especiales permiten sin apellido (futuro)

### VAL011: Solo Letras Válidas en Nombre
**Aplica**: Nombres y apellidos  
**Tipo**: Validación de caracteres

```
Permitidos:
- Letras mayúsculas A-Z
- Letras minúsculas a-z
- Ñ, ñ
- Acentos: á, é, í, ó, ú, Á, É, Í, Ó, Ú
- Espacios (múltiples permitidos, se normalizan)
- Guiones (para apellidos compuestos)

No permitidos:
- Números 0-9
- Símbolos especiales @#$%^&*()
- Caracteres de control
```

---

## 4. VALIDACIONES DE EMAIL

### VAL012: Email Obligatorio
**Aplica**: Solicitante  
**Tipo**: Presencia

### VAL013: Formato Email Válido
**Aplica**: Email  
**Tipo**: Formato RFC 5322

```
Regex validación:
^[a-zA-Z0-9._%-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$

Ejemplos válidos:
- usuario@dominio.com ✅
- juan.perez@empresa.co ✅
- nombre+tag@dominio.org ✅

Ejemplos inválidos:
- usuario@.com ❌
- @dominio.com ❌
- usuario.dominio.com ❌
- usuario@dominio ❌
```

### VAL014: Longitud Email
**Aplica**: Email  
**Tipo**: Restricción de tamaño  
**Valor**: Máximo 254 caracteres (estándar RFC)

---

## 5. VALIDACIONES DE TELÉFONO

### VAL015: Teléfono Obligatorio
**Aplica**: Solicitante  
**Tipo**: Presencia

### VAL016: Solo Números
**Aplica**: Teléfono  
**Tipo**: Validación de formato

```
Permitido:
- Dígitos 0-9
- Prefijo internacional: +57

No permitido:
- Letras
- Caracteres especiales excepto + (solo inicio)
- Espacios, guiones, paréntesis
```

### VAL017: Longitud Teléfono
**Aplica**: Teléfono  
**Tipo**: Restricción de tamaño

```
Mínimo: 7 caracteres
Máximo: 15 caracteres

Ejemplos válidos:
- 3012345678 (10 dígitos, celular colombiano)
- +573012345678 (con código país)
- 16025551234 (10 dígitos, otros países)
```

---

## 6. VALIDACIONES DE FECHA

### VAL018: Fecha Obligatoria
**Aplica**: Fecha evento, fecha inicio, fecha fin incapacidad  
**Tipo**: Presencia

### VAL019: Formato Fecha Válido
**Aplica**: Fechas  
**Tipo**: Formato  
**Formato requerido**: YYYY-MM-DD (ISO 8601)

```
Ejemplos válidos:
- 2026-03-15 ✅
- 2025-12-31 ✅

Ejemplos inválidos:
- 15/03/2026 ❌
- 15-03-2026 ❌
- 03/15/2026 ❌
```

### VAL020: Fechas Imposibles - Validación de Calendario
**Aplica**: Fechas  
**Tipo**: Validación de existencia

```
Rechazar fechas que no existen:
- 2026-02-29 (no es año bisiesto) ❌
- 2026-02-30 ❌
- 2026-04-31 ❌
- 2026-13-01 ❌ (mes 13)

Usar librería de fecha (date-fns, moment) para validación
```

### VAL021: Fecha Evento No Puede Ser Futura
**Aplica**: Fecha del evento (accidente)  
**Tipo**: Validación lógica

```
Si fecha_evento > fecha_hoy:
  → Error: "La fecha del evento no puede ser futura"
  → Bloquear envío

Excepción: Para eventos programados (se valida en auditoría)
```

### VAL022: Fecha Inicio ≤ Fecha Fin
**Aplica**: Incapacidad (rango de fechas)  
**Tipo**: Validación cruzada

```
Si fecha_inicio > fecha_fin:
  → Error: "La fecha de inicio debe ser anterior a la fecha de fin"
  → Bloquear envío
```

### VAL023: Coherencia de Fechas en Secuencia
**Aplica**: Incapacidades consecutivas  
**Tipo**: Validación lógica

```
Si múltiples incapacidades del mismo trabajador:
  Validar: fecha_fin_incapacidad_1 < fecha_inicio_incapacidad_2
  Tolerancia: 1 día sin brecha
```

---

## 7. VALIDACIONES DE INFORMACIÓN DEL ACCIDENTE

### VAL024: Fecha Accidente Obligatoria
**Aplica**: Incapacidades ARL  
**Tipo**: Presencia

### VAL025: Hora Accidente Obligatoria
**Aplica**: Incapacidades ARL  
**Tipo**: Presencia  
**Formato**: HH:mm (24 horas)

```
Ejemplos válidos:
- 08:30 ✅
- 14:45 ✅
- 23:59 ✅

Ejemplos inválidos:
- 8:30 ❌ (sin cero)
- 25:00 ❌ (hora inválida)
- 14:60 ❌ (minuto inválido)
```

### VAL026: Descripción Accidente Obligatoria
**Aplica**: Incapacidades ARL  
**Tipo**: Presencia + Longitud mínima

```
Validaciones:
- Obligatorio
- Mínimo 30 caracteres
- Máximo 2000 caracteres
- Descripción clara del evento
```

### VAL027: Lugar Accidente Obligatorio
**Aplica**: Incapacidades ARL  
**Tipo**: Presencia

```
Debe describir:
- Ubicación física (en empresa o lugar de trabajo)
- Detalles de ubicación
```

### VAL028: Actividad Realizada Obligatoria
**Aplica**: Incapacidades ARL  
**Tipo**: Presencia

```
Debe describir:
- La actividad que realizaba el trabajador
- Contexto del accidente
```

---

## 8. VALIDACIONES DE EMPRESA

### VAL029: NIT Obligatorio
**Aplica**: Empresa  
**Tipo**: Presencia

### VAL030: Formato NIT Válido
**Aplica**: NIT  
**Tipo**: Validación de formato

```
Formato: 9 dígitos + 1 dígito verificador (opcional en captura)

Ejemplo: 860123456-7 o 8601234567

Validación de dígito verificador:
- Usar algoritmo estándar NIT colombiano
- Backend valida obligatoriamente
- Frontend puede validar para UX
```

### VAL031: Razón Social Obligatoria
**Aplica**: Empresa  
**Tipo**: Presencia + Longitud

```
Validaciones:
- Obligatorio
- Mínimo 3 caracteres
- Máximo 255 caracteres
- Caracteres válidos para nombre empresa
```

---

## 9. VALIDACIONES DE ARCHIVO

### VAL032: Archivo Presente - Mínimo Requerido
**Aplica**: Documentos  
**Tipo**: Presencia

```
Validación:
- Mínimo 1 documento debe estar cargado
- Error si intenta radicar sin documentos

Excepción: Radicación parcial (si RN-005 aplica)
```

### VAL033: Tipo de Archivo Permitido
**Aplica**: Documentos  
**Tipo**: Restricción de tipo  
**Formatos permitidos**:
- PDF
- JPG
- JPEG
- PNG

```
Validación doble:
1. Frontend: Validar extensión
2. Backend: Validar MIME type + firma binaria

Rechazar:
- EXE, COM, BAT, SCR (ejecutables)
- ZIP, RAR (comprimidos)
- DOCX, XLSX (office, si no está permitido)
```

### VAL034: Archivo No Vacío
**Aplica**: Documentos  
**Tipo**: Validación de contenido

```
Validación:
- Archivo debe tener > 0 bytes
- Tamaño mínimo: 1 KB (imagen legible mínima)
```

### VAL035: Tamaño Máximo Archivo
**Aplica**: Documentos  
**Tipo**: Restricción de tamaño

```
Máximo: 20 MB por archivo

Mensaje de error:
"El archivo es muy grande. Máximo permitido: 20 MB"

Implementación:
- Frontend: Validar antes de cargar
- Backend: Validar al recibir
- Rechazar uploads que excedan límite
```

### VAL036: Cantidad Máxima de Archivos
**Aplica**: Documentos  
**Tipo**: Restricción de cantidad

```
Máximo: 10 archivos por radicación

Validación:
- Frontend: Habilitar/deshabilitar botón de carga
- Backend: Rechazar si count > 10
```

### VAL037: Nombre Archivo Válido
**Aplica**: Documentos  
**Tipo**: Validación de nombre

```
No permitidos:
- Nombres vacíos
- Caracteres de control
- Caracteres muy especiales: < > : " / \ | ? *

Recomendación:
- Sanitizar nombre de archivo en backend
- Generar nombre único: {timestamp}_{uuid}_{original_name}
```

### VAL038: Firma Binaria de Archivo (MIME Magic)
**Aplica**: Documentos  
**Tipo**: Validación de contenido

```
Para PDF:
- Primeros bytes: 25 50 44 46 (%PDF)

Para JPG:
- Primeros bytes: FF D8 FF

Para PNG:
- Primeros bytes: 89 50 4E 47 (‰PNG)

Validación en backend:
- Leer primeros bytes
- Comparar con firma conocida
- Rechazar si no coincide
```

---

## 10. VALIDACIONES DE SEGURIDAD

### VAL039: Captcha Válido
**Aplica**: Radicación pública  
**Tipo**: Validación de verificación

```
Implementación: Google reCAPTCHA v3 o similar

Validación:
- Score mínimo: 0.5 (no es bot)
- Si score < 0.5: Rechazar con captcha
- Registrar intentos fallidos
```

### VAL040: Habeas Data Aceptado
**Aplica**: Radicación  
**Tipo**: Validación de consentimiento

```
Validación:
- Checkbox debe estar marcado
- No puede radicarse sin aceptar
- Registro: guardar que fue aceptado + timestamp + IP
```

### VAL041: Declaración de Veracidad Aceptada
**Aplica**: Radicación  
**Tipo**: Validación de consentimiento

```
Validación:
- Checkbox debe estar marcado
- Mensaje: "Declaro que la información suministrada es verídica"
- No puede radicarse sin aceptar
- Registro: guardar que fue aceptado + timestamp + IP

Implicación legal:
- Incumplimiento = motivo de rechazo
```

### VAL042: Rate Limiting - Protección Contra Radicaciones Masivas
**Aplica**: Endpoint de radicación  
**Tipo**: Control de abuso

```
Límites:
- Por IP: Máximo 10 radicaciones por hora
- Por email: Máximo 5 radicaciones por día
- Global: Máximo 1000 radicaciones por hora

Implementación:
- Redis para contadores
- Bloqueo temporal si se excede
- Whitelist de IPs si aplica

Mensaje:
"Ha excedido el límite de radicaciones. Intente más tarde."
```

### VAL043: Validación de JWT - Token Válido
**Aplica**: Todas las rutas autenticadas  
**Tipo**: Validación de seguridad

```
Para cada solicitud autenticada:
- Token presente en header Authorization
- Token no expirado (exp > ahora)
- Firma válida (verificar con JWT_SECRET)
- Claims requeridos presentes (sub, iss, iat, exp, nbf, jti)

Si falla:
- Return 401 Unauthorized
- Redirigir a login
```

### VAL044: Protección XSS - Escape de Contenido
**Aplica**: Todo contenido renderizado  
**Tipo**: Validación de seguridad

```
Implementación:
- Frontend: React escapa automáticamente JSX
- Backend: Validar entrada, escapar salida
- Database: Usar parameterized queries

Ejemplos:
- <script>alert('xss')</script> → Escapado
- ' OR '1'='1 → Escapado
```

### VAL045: Protección SQL Injection
**Aplica**: Todas las consultas database  
**Tipo**: Validación de seguridad

```
Implementación:
- Usar ORM (SQLAlchemy) con queries parametrizadas
- NUNCA concatenar strings en SQL
- Validar tipos de datos esperados
- Usar prepared statements

Ejemplo correcto:
session.query(Usuario).filter(Usuario.email == email).first()

Ejemplo incorrecto (❌):
session.execute(f"SELECT * FROM usuario WHERE email = '{email}'")
```

---

## 11. VALIDACIONES DE DATOS MÉDICOS

### VAL046: Código CIE-10 Obligatorio
**Aplica**: Incapacidad  
**Tipo**: Presencia

```
Validación:
- Código debe estar presente
- Código debe existir en catálogo_cie10
- Búsqueda en base de datos
```

### VAL047: Diagnóstico Válido
**Aplica**: Incapacidad  
**Tipo**: Validación de coherencia

```
Validación:
- Diagnóstico obligatorio (descripción)
- Debe coincidir con código CIE-10 seleccionado
- Coherente con la incapacidad médica adjunta
```

### VAL048: Nombre Médico Obligatorio
**Aplica**: Incapacidad  
**Tipo**: Presencia

### VAL049: Registro Médico (Cédula) Obligatorio
**Aplica**: Incapacidad  
**Tipo**: Presencia + Formato

```
Validación:
- Obligatorio
- Formato: Numérico
- Mínimo 5 dígitos
```

---

## 12. VALIDACIONES DE DATOS FINANCIEROS

### VAL050: Valor Día Obligatorio
**Aplica**: Liquidación  
**Tipo**: Presencia + Validación numérica

```
Validación:
- Mayor que cero
- Numérico con máximo 2 decimales
- Mínimo: salario mínimo diario / 30
- Máximo: tope anual / 360
```

### VAL051: Días Totales - Cálculo
**Aplica**: Incapacidad  
**Tipo**: Validación cruzada

```
Validación automática:
dias_totales = (fecha_fin - fecha_inicio).days + 1

Validación manual:
- Mayor que 0
- Menor que 730 (máximo 2 años)
- Coherente con diagnóstico
```

---

## 13. VALIDACIONES CRUZADAS

### VAL052: Coherencia Diagnóstico-Días
**Aplica**: Auditoría  
**Tipo**: Validación de lógica médica

```
Criterios de alerta (se registra pero puede continuar):
- Diagnóstico menor + muchos días (e.j. resfriado + 90 días)
- Diagnóstico grave + pocos días (e.j. fractura + 3 días)

Tabla de rangos esperados:
- Esguince: 5-30 días
- Fractura: 30-90 días
- Quemadura: 10-60 días
```

### VAL053: Coherencia Evento-Diagnóstico
**Aplica**: Auditoría  
**Tipo**: Validación de relación causal

```
Validación:
- Diagnóstico debe ser coherente con evento reportado
- Auditor evalúa relación causal
- Se registra como observación si hay duda
```

### VAL054: No Traslape de Períodos
**Aplica**: Auditoría  
**Tipo**: Validación de no duplicidad

```
Validación:
Para incapacidades del mismo trabajador:
- NO deben traslaparse fechas
- Tolerancia: 1 día entre fin de una e inicio de otra

Ejemplo inválido:
Incapacidad 1: 01-03 al 15-03
Incapacidad 2: 10-03 al 20-03 ❌ (traslape)

Ejemplo válido:
Incapacidad 1: 01-03 al 15-03
Incapacidad 2: 16-03 al 30-03 ✅ (consecutivas)
```

---

## 14. MATRIZ DE VALIDACIONES POR MÓDULO

| Validación | Radicación | Auditoría | Aprobación | Consulta |
|-----------|-----------|----------|-----------|----------|
| VAL001-004 | ✅ Frontend+Backend | ✅ Backend | ✅ Backend | ❌ |
| VAL005-011 | ✅ Frontend+Backend | ✅ Backend | ❌ | ❌ |
| VAL012-014 | ✅ Frontend+Backend | ❌ | ❌ | ❌ |
| VAL015-017 | ✅ Frontend+Backend | ❌ | ❌ | ❌ |
| VAL018-023 | ✅ Frontend+Backend | ✅ Backend | ❌ | ❌ |
| VAL024-028 | ✅ Frontend+Backend | ✅ Backend | ❌ | ❌ |
| VAL029-031 | ✅ Frontend+Backend | ✅ Backend | ❌ | ❌ |
| VAL032-038 | ✅ Frontend+Backend | ✅ Backend | ❌ | ❌ |
| VAL039-045 | ✅ Backend | ✅ Backend | ✅ Backend | ❌ |
| VAL046-049 | ✅ Frontend+Backend | ✅ Backend | ❌ | ❌ |
| VAL050-051 | ❌ | ✅ Backend | ✅ Backend | ❌ |
| VAL052-054 | ❌ | ✅ Backend | ❌ | ❌ |

---

## 15. FLUJO DE VALIDACIÓN

### En Frontend (Portal de Radicación)
```
1. Usuario ingresa datos
2. React Hook Form valida en tiempo real (VAL001-VAL045)
3. Mostrar errores específicos para cada campo
4. Habilitar botón de envío solo si TODO es válido
5. Al enviar: Validar captcha (VAL039)
6. Validar términos (VAL040-VAL041)
7. Enviar datos al backend
```

### En Backend (API)
```
1. Recibir solicitud POST
2. Rate limiting (VAL042)
3. Validar JWT (VAL043)
4. Validar todos los datos (VAL001-VAL054)
5. Si falla: Return 422 Unprocessable Entity con detalles
6. Si pasa: Procesar, guardar, generar radicado
7. Retornar confirmación con número de radicado
```

### En Auditoría
```
1. Auditor recibe incapacidad
2. Sistema ejecuta validaciones automáticas (VAL046-VAL054)
3. Mostrar alertas y warnings
4. Auditor revisa manualmente
5. Auditor marca como APROBADA o OBSERVADA
```

---

**Última actualización**: Junio 2026  
**Cobertura**: 54 validaciones documentadas

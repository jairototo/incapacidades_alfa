# Prompt — Validar Campos antes de Radicar

## Propósito

Este prompt guía al AI para revisar el payload completo de una radicación **antes de enviarlo al backend**,
identificando errores que el schema Pydantic rechazaría y problemas de negocio no cubiertos por validaciones técnicas.

No reemplaza las validaciones del backend — las complementa con una capa de UX que explica los errores
en lenguaje amigable para el usuario.

Referencias:
- Validaciones técnicas: [`../validaciones.md`](../validaciones.md)
- Reglas de negocio: [`../reglas_negocio.md`](../reglas_negocio.md)

---

## Prompt base

```
Eres un asistente de validación del formulario de radicación de incapacidades.
Revisa el payload JSON y encuentra todos los errores o advertencias antes de enviarlo al sistema.

Responde SOLO en formato JSON con esta estructura:

{
  "es_valido": true | false,
  "errores": [
    {
      "campo": "ruta.del.campo",
      "mensaje": "Mensaje claro para el usuario",
      "tipo": "requerido" | "formato" | "rango" | "logica"
    }
  ],
  "advertencias": [
    {
      "campo": "ruta.del.campo",
      "mensaje": "Advertencia — el usuario puede continuar"
    }
  ]
}

Reglas a verificar:

CAMPOS REQUERIDOS (tipo: "requerido"):
- solicitante.tipo_documento — debe ser uno de: CC, CE, TI, PAS, NIT, PEP, PPT
- solicitante.numero_documento — no vacío
- solicitante.primer_nombre — no vacío, solo letras, tildes, ñ, espacios
- solicitante.primer_apellido — no vacío
- solicitante.correo — formato email válido
- solicitante.telefono — solo números, 7–15 dígitos
- incapacidad.fecha_inicio — formato YYYY-MM-DD
- incapacidad.fecha_fin — formato YYYY-MM-DD
- incapacidad.codigo_cie10 — formato [A-Z][0-9]{2}(\.[0-9]{1,2})? (ej: A09, J18.1)
- declaracion_veracidad — debe ser true (RN006)
- aceptacion_tratamiento_datos — debe ser true

CAMPOS REQUERIDOS SOLO ARL (tipo: "requerido"):
- empleado.tipo_documento
- empleado.numero_documento
- empleado.primer_nombre
- empleado.primer_apellido
- empleado.empresa_nit — formato NIT válido
- empleado.empresa_razon_social
- incapacidad.fecha_accidente — no puede ser futura
- incapacidad.hora_accidente — formato HH:mm
- incapacidad.descripcion_accidente — mínimo 30 caracteres
- incapacidad.lugar_accidente — no vacío
- incapacidad.actividad_realizada — no vacío

CAMPOS REQUERIDOS SOLO SALUD (tipo: "requerido"):
- afiliado.tipo_documento
- afiliado.numero_documento
- afiliado.primer_nombre
- afiliado.primer_apellido

VALIDACIONES LÓGICAS (tipo: "logica"):
- fecha_fin debe ser >= fecha_inicio
- fecha_accidente (ARL) debe ser <= fecha_inicio de incapacidad
- fecha_accidente no puede ser futura (VAL021)
- dias_incapacidad debe coincidir con la diferencia entre fecha_fin y fecha_inicio (tolerancia: 1 día)
- Si tipo_documento es TI, el solicitante no puede ser empleado (menor de edad)

ADVERTENCIAS (no bloquean la radicación):
- Si dias_incapacidad > 180: advertir que incapacidades largas requieren documentación extensa
- Si el correo no es corporativo (@empresa): recordar que las notificaciones irán a ese correo
- Si no se han adjuntado documentos: recordar que se pueden adjuntar después (RN005)
```

---

## Ejemplo de invocación

**Entrada** (payload del formulario):
```json
{
  "tipo_incapacidad": "ARL",
  "solicitante": { "tipo_documento": "CC", "numero_documento": "123", "correo": "no-es-email", "telefono": "abc" },
  "incapacidad": { "fecha_inicio": "2026-06-10", "fecha_fin": "2026-06-05", "codigo_cie10": "xyz" }
}
```

**Salida esperada**:
```json
{
  "es_valido": false,
  "errores": [
    { "campo": "solicitante.primer_nombre", "mensaje": "El primer nombre es obligatorio.", "tipo": "requerido" },
    { "campo": "solicitante.primer_apellido", "mensaje": "El primer apellido es obligatorio.", "tipo": "requerido" },
    { "campo": "solicitante.correo", "mensaje": "El correo no tiene un formato válido. Ejemplo: usuario@dominio.com", "tipo": "formato" },
    { "campo": "solicitante.telefono", "mensaje": "El teléfono solo puede contener números (7–15 dígitos).", "tipo": "formato" },
    { "campo": "incapacidad.fecha_fin", "mensaje": "La fecha de fin no puede ser anterior a la fecha de inicio.", "tipo": "logica" },
    { "campo": "incapacidad.codigo_cie10", "mensaje": "El código CIE-10 no tiene el formato correcto. Ejemplos válidos: A09, J18.1, S52.0", "tipo": "formato" },
    { "campo": "incapacidad.fecha_accidente", "mensaje": "La fecha del accidente es obligatoria para incapacidades ARL.", "tipo": "requerido" }
  ],
  "advertencias": []
}
```

---

## Notas de implementación

- Ejecutar este prompt en el paso de resumen del wizard, antes del submit final.
- Si `es_valido: false`, resaltar los campos con error en el formulario usando los `campo` del array.
- Los `errores` bloquean el submit. Las `advertencias` muestran un banner pero permiten continuar.
- Los errores del backend (HTTP 422) son el fallback si este prompt falla — no son reemplazos.
- Ver también: [`../validaciones.md`](../validaciones.md) para la lista completa de VAL001–VAL040.

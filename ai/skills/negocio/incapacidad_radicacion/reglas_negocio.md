# Reglas de Negocio - Radicación de Incapacidades ARL

## Objetivo

Permitir la recepción de solicitudes de incapacidades y eventos laborales
mediante un portal público, generando un número de radicado para posterior
validación por parte de la ARL.

La radicación NO implica aprobación, reconocimiento económico ni aceptación
de responsabilidad por parte de la ARL.

---

## RN001 - Recepción de solicitudes

El sistema debe permitir la radicación de solicitudes las 24 horas del día.

---

## RN002 - Generación de radicado

Toda solicitud recibida exitosamente debe generar:

- Número único de radicado.
- Fecha y hora de radicación.
- Estado inicial.

Estado inicial:

RADICADA

---

## RN003 - Unicidad del radicado

El número de radicado debe ser único.

No pueden existir dos solicitudes con el mismo consecutivo.

---

## RN004 - Trazabilidad

Toda modificación realizada sobre una radicación debe quedar registrada.

Registrar:

- Usuario.
- Fecha.
- Hora.
- Acción ejecutada.

---

## RN005 - Recepción parcial

La radicación podrá recibirse aun cuando no existan todos los documentos
requeridos para auditoría.

La validación documental se realizará posteriormente.

---

## RN006 - Declaración de veracidad

El solicitante debe aceptar que la información suministrada es veraz.

Sin aceptación no puede radicarse la solicitud.

---

## RN007 - Recepción de documentos

El sistema debe permitir anexar documentos electrónicos.

Ejemplos:

- Incapacidad médica.
- Documento de identidad.
- Historia clínica.
- Epicrisis.
- FURAT.
- Otros soportes.

---

## RN008 - Estado inicial

Toda solicitud radicada inicia en:

RADICADA

---

## RN009 - Confirmación al solicitante

Después de radicar exitosamente se debe informar:

- Número de radicado.
- Fecha de radicación.
- Canales de consulta.

---

## RN010 - No validación médica

El portal no realiza:

- Auditoría médica.
- Determinación de origen.
- Liquidación.
- Aprobación.

Estas actividades corresponden a procesos posteriores.

---

## RN011 - Conservación de evidencia

Los documentos cargados deben almacenarse sin alteración.

---

## RN012 - Integridad de la información

La información registrada en el formulario debe coincidir con la información
almacenada en el expediente electrónico.

---

# Otras reglas de negocio relacionadas pero no contempladas para este desarrollo

## RN013 - Recepción de accidentes laborales 

El sistema podrá recibir reportes de accidente laboral para posterior
validación por la ARL.

Los reportes deben incluir información mínima del trabajador,
empleador y evento reportado.
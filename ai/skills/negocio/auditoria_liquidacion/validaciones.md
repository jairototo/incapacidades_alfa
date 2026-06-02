# Validaciones Automáticas

## Datos del trabajador

### VAL001

Documento obligatorio.

Campos:
- Tipo documento.
- Número documento.

---

### VAL002

El trabajador debe existir en la base de afiliados.

---

### VAL003

La afiliación debe encontrarse activa.

---

## Validaciones de fechas

### VAL004

Fecha accidente obligatoria.

---

### VAL005

Fecha accidente >= fecha afiliación

---

### VAL006

Fecha inicio incapacidad >= fecha accidente

---

### VAL007

Fecha fin incapacidad >= fecha inicio incapacidad

---

### VAL008

Número días incapacidad > 0

---

## Validaciones documentales

### VAL009

Debe existir certificado de incapacidad.

---

### VAL010

Debe existir identificación del trabajador.

---

### VAL011

Debe existir soporte del evento.

Ejemplos:
- FURAT.
- Investigación accidente.
- Calificación origen.

---

## Validaciones médicas

### VAL012

Debe existir código CIE10.

---

### VAL013

Debe existir médico emisor.

---

### VAL014

Debe existir IPS emisora.

---

### VAL015

Diagnóstico obligatorio.

---

### VAL016

Diagnóstico coherente con días otorgados.

Generar alerta cuando supere umbrales definidos.

---

## Validaciones de duplicidad

### VAL017

No debe existir misma incapacidad registrada previamente.

Criterios:
- Documento.
- Diagnóstico.
- Fechas.
- Número incapacidad.

---

### VAL018

No debe existir traslape de períodos.

Ejemplo inválido:

01-01 al 15-01
10-01 al 20-01

---

## Validaciones financieras

### VAL019

Debe existir IBC.

---

### VAL020

IBC mayor a cero.

---

### VAL021

Valor liquidado mayor a cero.

---

### VAL022

Días reconocidos coinciden con cálculo.

---

## Validaciones antifraude

### VAL023

Documento PDF legible.

---

### VAL024

No presentar alteraciones visibles.

---

### VAL025

Metadatos coherentes.

---

### VAL026

No existir múltiples radicaciones iguales.

---

## Validaciones de proceso

### VAL027

Estado actual permite auditoría.

---

### VAL028

Estado actual permite liquidación.

---

### VAL029

No puede liquidarse un caso rechazado.

---

### VAL030

No puede pagarse un caso sin aprobación.
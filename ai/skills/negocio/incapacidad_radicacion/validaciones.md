# Validaciones de Captura

## Validaciones Generales

### VAL001

Campo obligatorio.

No puede estar vacío.

---

### VAL002

Eliminar espacios al inicio y final.

---

### VAL003

Longitud máxima permitida.

---

### VAL004

Caracteres válidos según tipo de dato.

---

## Validaciones Documento

### VAL005

Tipo documento obligatorio.

Valores permitidos:

- CC
- CE
- TI
- PAS
- NIT
- PEP
- PPT

---

### VAL006

Número documento obligatorio.

---

### VAL007

Número documento solo numérico.

---

### VAL008

Longitud documento válida según tipo.

---

## Validaciones Nombre

### VAL009

Primer nombre obligatorio.

---

### VAL010

Apellidos obligatorios.

---

### VAL011

Solo letras válidas.

Permitir:

- A-Z
- tildes
- ñ
- espacios

---

## Validaciones Correo

### VAL012

Correo obligatorio.

---

### VAL013

Formato email válido.

Ejemplo válido:

usuario@dominio.com

---

### VAL014

Longitud máxima 254 caracteres.

---

## Validaciones Teléfono

### VAL015

Teléfono obligatorio.

---

### VAL016

Solo números.

---

### VAL017

Longitud entre 7 y 15 caracteres.

---

## Validaciones Fecha

### VAL018

Fecha obligatoria.

---

### VAL019

Formato válido.

YYYY-MM-DD

---

### VAL020

No permitir fechas imposibles.

Ejemplo:

2026-02-31

---

### VAL021

Fecha evento no puede ser futura.

---

## Validaciones Información Accidente

### VAL022

Fecha accidente obligatoria.

---

### VAL023

Hora accidente obligatoria.

Formato:

HH:mm

---

### VAL024

Descripción accidente obligatoria.

Mínimo 30 caracteres.

---

### VAL025

Lugar accidente obligatorio.

---

### VAL026

Actividad realizada obligatoria.

---

## Validaciones Empresa

### VAL027

NIT obligatorio.

---

### VAL028

NIT formato válido.

---

### VAL029

Razón social obligatoria.

---

## Validaciones Archivos

### VAL030

Debe existir al menos un documento adjunto.

---

### VAL031

Tipos permitidos:

- PDF
- JPG
- JPEG
- PNG

---

### VAL032

Archivo no vacío.

---

### VAL033

Tamaño máximo permitido.

Ejemplo:

20 MB

---

### VAL034

Nombre archivo válido.

---

### VAL035

Cantidad máxima de archivos permitida.

---

## Validaciones Seguridad

### VAL036

Captcha válido.

---

### VAL037

Aceptación de tratamiento de datos.

Obligatoria.

---

### VAL038

Aceptación declaración de veracidad.

Obligatoria.

---

### VAL039

Protección contra radicaciones masivas.

Rate limit.

---

### VAL040

Prevención de archivos maliciosos.

Validar:

- Extensión.
- MIME Type.
- Firma binaria.
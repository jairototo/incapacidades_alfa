"""Fuente única de verdad para las reglas de dominio de una incapacidad.

Estos valores son compartidos por:
- el esquema de radicación individual (``app.schemas.pre_incapacidad``), y
- las reglas de validación puras reutilizadas por la radicación masiva y el job
  de auditoría (``app.services.incapacidad_validation_rules``).

Mantenerlos aquí evita que las dos rutas se desincronicen.
"""
import re

# Tipos de enfermedad ARL válidos (catálogo cerrado de 3 opciones).
TIPOS_ENFERMEDAD = ["ACCIDENTE_TRABAJO", "ENFERMEDAD_LABORAL", "ACCIDENTE_TRAYECTO"]

# Formato CIE-10 (estándar colombiano — Resolución 1273 / cuarto carácter):
# una letra + 2 dígitos + un cuarto carácter que es un dígito o la ``X`` de relleno.
# SIN punto separador (no se usa el formato internacional con punto ``A04.8``).
# Ejemplos válidos: ``A048``, ``M545``, ``A09X``.
REGEX_CIE10 = re.compile(r"^[A-Z]\d{2}[0-9X]$")

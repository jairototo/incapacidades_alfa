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

# Formato CIE-10: una letra + tres dígitos, opcionalmente ``.`` + 1-2 dígitos.
# Ejemplos válidos: ``A000``, ``M54.5``, ``S00.0``.
REGEX_CIE10 = re.compile(r"^[A-Z]\d{3}(\.\d{1,2})?$")

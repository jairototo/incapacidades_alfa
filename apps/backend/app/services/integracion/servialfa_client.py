"""Cliente ServiAlfa (Centro de Operaciones de Servicio al Cliente).

STUB: hoy retorna un número mock. Sustituir `enviar` por la llamada HTTP real
cuando lleguen las specs, manteniendo la firma.
"""
from datetime import datetime
from app.models.incapacidad import Incapacidad


class ServiAlfaClient:
    async def enviar(self, incapacidad: Incapacidad) -> dict:
        numero = f"SA-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{str(incapacidad.id)[:8]}"
        return {
            "estado": "SUCCESS",
            "numero_radicacion_servialfa": numero,
            "payload_resumen": {"numero": incapacidad.numero, "empleado_id": str(incapacidad.empleado_id)},
            "respuesta": {"ok": True, "stub": True},
        }

"""Cliente Sicat (Centro de Gestión Documental).

STUB: hoy retorna éxito. Cada envío referencia el numero_radicacion_servialfa.
NOTE: no acceder a incapacidad.documentos — es lazy y dispara MissingGreenlet en async.
"""
from app.models.incapacidad import Incapacidad


class SicatClient:
    async def enviar(self, incapacidad: Incapacidad, numero_radicacion_servialfa: str) -> dict:
        return {
            "estado": "SUCCESS",
            "payload_resumen": {
                "numero": incapacidad.numero,
                "numero_radicacion_servialfa": numero_radicacion_servialfa,
            },
            "respuesta": {"ok": True, "stub": True},
        }

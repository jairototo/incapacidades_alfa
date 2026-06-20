"""Orquesta ServiAlfa → Sicat y registra cada intento en communication_log."""
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.logging import logger

from app.models.incapacidad import Incapacidad
from app.models.communication_log import CommunicationLog
from app.services.integracion.servialfa_client import ServiAlfaClient
from app.services.integracion.sicat_client import SicatClient


class IntegracionService:
    def __init__(
        self,
        db: AsyncSession,
        servialfa: ServiAlfaClient | None = None,
        sicat: SicatClient | None = None,
    ):
        self.servialfa = servialfa or ServiAlfaClient()
        self.sicat = sicat or SicatClient()

    def _log(self, db: AsyncSession, inc: Incapacidad, sistema: str, result: dict) -> None:
        db.add(CommunicationLog(
            incapacidad_id=inc.id,
            sistema=sistema,
            estado=result.get("estado", "FAILURE"),
            payload_resumen=result.get("payload_resumen"),
            respuesta=result.get("respuesta"),
            mensaje=result.get("mensaje"),
        ))

    async def procesar(self, db: AsyncSession, inc: Incapacidad) -> None:
        """Hook compatible con RadicacionPipelineService.integracion."""
        try:
            sa = await self.servialfa.enviar(inc)
        except Exception as exc:
            logger.error(f"ServiAlfa falló para {inc.id}: {exc}")
            self._log(db, inc, "SERVIALFA", {"estado": "FAILURE", "mensaje": str(exc)})
            return
        inc.numero_radicacion_servialfa = sa["numero_radicacion_servialfa"]
        self._log(db, inc, "SERVIALFA", sa)

        try:
            sk = await self.sicat.enviar(inc, inc.numero_radicacion_servialfa)
            self._log(db, inc, "SICAT", sk)
        except Exception as exc:
            logger.error(f"Sicat falló para {inc.id}: {exc}")
            self._log(db, inc, "SICAT", {
                "estado": "FAILURE",
                "mensaje": str(exc),
                "payload_resumen": {"numero_radicacion_servialfa": inc.numero_radicacion_servialfa},
            })
        await db.flush()

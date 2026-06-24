"""
Servicio para Plantilla de Auditoría.

Orquesta la creación/actualización de plantillas de auditoría
y genera el texto copiable para pegar en Arpis.
"""
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.db.repositories.incapacidad_repository import incapacidad_repository
from app.db.repositories.plantilla_auditoria_repository import (
    plantilla_auditoria_repository,
)
from app.models.plantilla_auditoria import PlantillaAuditoria
from app.schemas.plantilla_auditoria import PlantillaAuditoriaCreate


class PlantillaAuditoriaService:
    """Servicio de negocio para plantillas de auditoría."""

    async def create_or_update(
        self,
        db: AsyncSession,
        incapacidad_id: UUID,
        data: PlantillaAuditoriaCreate,
        usuario_id: UUID,
    ) -> PlantillaAuditoria:
        """
        Crear o actualizar la plantilla de auditoría de una incapacidad.

        Valida que la incapacidad exista, luego realiza un upsert.

        Args:
            db: Sesión de base de datos
            incapacidad_id: ID de la incapacidad
            data: Datos validados de la plantilla
            usuario_id: ID del auditor que guarda la plantilla

        Returns:
            Plantilla creada o actualizada

        Raises:
            NotFoundException: Si la incapacidad no existe
        """
        incapacidad = await incapacidad_repository.get_by_id(db, incapacidad_id)
        if incapacidad is None:
            raise NotFoundException(f"Incapacidad {incapacidad_id} no encontrada")

        payload = data.model_dump(exclude_none=False)
        payload["auditado_por_id"] = usuario_id

        return await plantilla_auditoria_repository.upsert(
            db=db,
            incapacidad_id=incapacidad_id,
            data=payload,
        )

    async def get_by_incapacidad(
        self,
        db: AsyncSession,
        incapacidad_id: UUID,
    ) -> PlantillaAuditoria:
        """
        Obtener la plantilla de una incapacidad.

        Args:
            db: Sesión de base de datos
            incapacidad_id: ID de la incapacidad

        Returns:
            Plantilla de la incapacidad

        Raises:
            NotFoundException: Si la incapacidad o la plantilla no existe
        """
        incapacidad = await incapacidad_repository.get_by_id(db, incapacidad_id)
        if incapacidad is None:
            raise NotFoundException(f"Incapacidad {incapacidad_id} no encontrada")

        plantilla = await plantilla_auditoria_repository.get_by_incapacidad(
            db, incapacidad_id
        )
        if plantilla is None:
            raise NotFoundException(
                f"No existe plantilla de auditoría para la incapacidad {incapacidad_id}"
            )

        return plantilla

    def build_texto_copiable(self, plantilla: PlantillaAuditoria) -> str:
        """
        Construye el texto formateado para pegar en Arpis.

        Args:
            plantilla: Objeto PlantillaAuditoria

        Returns:
            Texto plano formateado
        """
        partes = []

        # Línea principal de autorización
        if plantilla.linea_autorizacion:
            partes.append(plantilla.linea_autorizacion)

        # Diagnóstico CIE-10
        if plantilla.diagnostico_cie10:
            cie10_line = f"CIE-10: {plantilla.diagnostico_cie10}"
            if plantilla.descripcion_cie10:
                cie10_line += f" - {plantilla.descripcion_cie10}"
            partes.append(cie10_line)

        # Médico
        if plantilla.nombre_medico:
            medico_line = f"Médico: {plantilla.nombre_medico}"
            if plantilla.especialidad_medico:
                medico_line += f" ({plantilla.especialidad_medico})"
            partes.append(medico_line)

        # IPS
        if plantilla.nombre_ips:
            partes.append(f"IPS: {plantilla.nombre_ips}")

        # Canal de recepción
        partes.append(f"Canal recepción: {plantilla.canal_recepcion}")

        # Datos de aprobación parcial si aplica
        if plantilla.dias_documento is not None:
            partes.append(f"Días en documento: {plantilla.dias_documento}")

        if plantilla.rango_pagado_inicio and plantilla.rango_pagado_fin:
            partes.append(
                f"Rango pagado: {plantilla.rango_pagado_inicio.isoformat()} "
                f"a {plantilla.rango_pagado_fin.isoformat()}"
            )

        return "\n".join(partes)


plantilla_auditoria_service = PlantillaAuditoriaService()

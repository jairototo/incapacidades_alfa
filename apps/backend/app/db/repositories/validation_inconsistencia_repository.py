"""
Repository para almacenar y consultar inconsistencias de validación.
"""
from uuid import UUID
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.validation_inconsistencia import ValidationInconsistencia
from app.schemas.validation_inconsistencia import ValidationInconsistenciaCreate


class ValidationInconsistenciaRepository:
    """Repository para inconsistencias de validación."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, schema: ValidationInconsistenciaCreate) -> ValidationInconsistencia:
        """Crear nueva inconsistencia."""
        issue = ValidationInconsistencia(
            pre_incapacidad_id=schema.pre_incapacidad_id,
            incapacidad_id=schema.incapacidad_id,
            categoria=schema.categoria,
            severidad=schema.severidad,
            codigo=schema.codigo,
            descripcion=schema.descripcion,
            campo_afectado=schema.campo_afectado,
            valor_encontrado=schema.valor_encontrado,
            valor_esperado=schema.valor_esperado,
        )
        self.db.add(issue)
        await self.db.flush()
        return issue

    async def get_by_pre_incapacidad(self, pre_inc_id: UUID) -> list[ValidationInconsistencia]:
        """Obtener todas las inconsistencias de una pre-incapacidad."""
        query = select(ValidationInconsistencia).where(
            ValidationInconsistencia.pre_incapacidad_id == pre_inc_id
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def count_by_severidad(self, pre_inc_id: UUID) -> dict[str, int]:
        """Contar issues por severidad."""
        issues = await self.get_by_pre_incapacidad(pre_inc_id)

        counts = {
            "ERROR": 0,
            "WARNING": 0,
            "INFO": 0,
            "total": len(issues)
        }

        for issue in issues:
            counts[issue.severidad] += 1

        return counts

    async def has_errors(self, pre_inc_id: UUID) -> bool:
        """Verificar si hay errores (no warnings/infos)."""
        query = select(ValidationInconsistencia).where(
            and_(
                ValidationInconsistencia.pre_incapacidad_id == pre_inc_id,
                ValidationInconsistencia.severidad == "ERROR"
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None

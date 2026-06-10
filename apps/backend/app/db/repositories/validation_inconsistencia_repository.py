"""
Repository para almacenar y consultar inconsistencias de validación.
"""
from uuid import UUID
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, delete, or_

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
            counts[issue.severidad] = counts.get(issue.severidad, 0) + 1

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
        # Use scalars().first() instead of scalar_one_or_none() to handle multiple rows
        return result.scalars().first() is not None

    async def delete_by_pre_incapacidad(self, pre_inc_id: UUID) -> int:
        """Elimina todas las inconsistencias de una pre-incapacidad. Retorna el número eliminado."""
        stmt = delete(ValidationInconsistencia).where(
            ValidationInconsistencia.pre_incapacidad_id == pre_inc_id
        ).execution_options(synchronize_session=False)
        result = await self.db.execute(stmt)
        return result.rowcount

    async def get_by_incapacidad(self, incapacidad_id: UUID) -> list[ValidationInconsistencia]:
        """Retorna todos los issues de una incapacidad:
        - issues con incapacidad_id directo, O
        - issues cuya pre_incapacidad apunta a esta incapacidad."""
        from app.models.pre_incapacidad import PreIncapacidad

        subq = select(PreIncapacidad.id).where(
            PreIncapacidad.incapacidad_id == incapacidad_id
        )
        query = (
            select(ValidationInconsistencia)
            .where(
                or_(
                    ValidationInconsistencia.incapacidad_id == incapacidad_id,
                    ValidationInconsistencia.pre_incapacidad_id.in_(subq),
                )
            )
            .order_by(ValidationInconsistencia.fecha_deteccion)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

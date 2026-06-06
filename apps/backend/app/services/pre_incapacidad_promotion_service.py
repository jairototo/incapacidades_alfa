"""
Servicio de promoción de pre-incapacidades a incapacidades completas.
Orquesta validación, persistencia de issues, y creación de incapacidad.
"""
from datetime import datetime
from uuid import UUID
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pre_incapacidad import PreIncapacidad
from app.db.repositories.pre_incapacidad_repository import PreIncapacidadRepository
from app.db.repositories.validation_inconsistencia_repository import ValidationInconsistenciaRepository
from app.db.repositories.empleado_repository import empleado_repository
from app.db.repositories.empresa_repository import empresa_repository
from app.services.pre_incapacidad_validation_service import PreIncapacidadValidationService
from app.schemas.validation_inconsistencia import ValidationSummary, PromotionResult


class PromotePreIncapacidadService:
    """Servicio para promocionar pre-incapacidades a incapacidades."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.pre_inc_repo = PreIncapacidadRepository()
        self.validation_repo = ValidationInconsistenciaRepository(db)

    async def promote_pre_incapacidad(
        self,
        pre_incapacidad_id: UUID,
    ) -> PromotionResult:
        """
        Promocionar una pre-incapacidad a incapacidad.

        Flujo:
        1. Fetch pre-incapacidad
        2. Fetch empleado/empresa relacionados
        3. Validar con todas las categorías
        4. Persistir issues a DB
        5. Si hay ERRORs: no crear incapacidad, retornar resultado con issues
        6. Si válida: crear incapacidad y retornar resultado exitoso

        Args:
            pre_incapacidad_id: ID de la pre-incapacidad a promocionar

        Returns:
            PromotionResult con status, issues, e incapacidad_id si se creó
        """
        try:
            # 1. Fetch pre-incapacidad
            pre_inc = await self.pre_inc_repo.get_by_id(self.db, pre_incapacidad_id)
            if not pre_inc:
                logger.error(f"Pre-incapacidad {pre_incapacidad_id} not found")
                return PromotionResult(
                    success=False,
                    pre_incapacidad_id=pre_incapacidad_id,
                    validation_summary=ValidationSummary(
                        total_issues=0,
                        errors=0,
                        warnings=0,
                        infos=0,
                        issues=[],
                    ),
                    error_message="Pre-incapacidad no encontrada",
                    timestamp=datetime.utcnow(),
                )

            # 2. Fetch related entities
            empleado = None
            empresa = None

            # Fetch empresa first (by NIT)
            if pre_inc.empresa_nit:
                empresa = await empresa_repository.get_by_nit(
                    self.db,
                    pre_inc.empresa_nit,
                )

            # Fetch empleado (requires empresa_id, not NIT)
            if pre_inc.tipo == "ARL" and empresa:
                empleado = await empleado_repository.get_by_documento(
                    self.db,
                    pre_inc.empleado_numero_documento,
                    empresa.id,  # ← Use empresa.id (UUID), not empresa_nit (string)
                )

            # 3. Validar
            validation_service = PreIncapacidadValidationService(
                pre_incapacidad=pre_inc,
                empleado=empleado,
                empresa=empresa,
            )
            issues = await validation_service.validate_all()

            # 4. Persistir issues a DB
            for issue_schema in issues:
                await self.validation_repo.create(issue_schema)

            # Contar issues por severidad
            counts = await self.validation_repo.count_by_severidad(pre_incapacidad_id)

            # Construir summary
            validation_summary = ValidationSummary(
                total_issues=counts["total"],
                errors=counts["ERROR"],
                warnings=counts["WARNING"],
                infos=counts["INFO"],
                issues=[],  # Por ahora empty, se pueden cargar si es necesario
            )

            # 5. Verificar si hay ERRORs
            has_errors = await self.validation_repo.has_errors(pre_incapacidad_id)

            if has_errors:
                logger.warning(
                    f"Pre-incapacidad {pre_incapacidad_id} validation failed - "
                    f"has {counts['ERROR']} errors. Not creating incapacidad."
                )
                await self.pre_inc_repo.update_estado(self.db, pre_incapacidad_id, "RECHAZADA")

                return PromotionResult(
                    success=False,
                    pre_incapacidad_id=pre_incapacidad_id,
                    validation_summary=validation_summary,
                    error_message=f"Validación fallida: {counts['ERROR']} errores encontrados",
                    timestamp=datetime.utcnow(),
                )

            # 6. Crear incapacidad (MOCK para ahora)
            # TODO: Implementar creación de incapacidad cuando service esté disponible
            logger.info(
                f"Pre-incapacidad {pre_incapacidad_id} validation passed - "
                f"creating incapacidad..."
            )
            await self.pre_inc_repo.update_estado(self.db, pre_incapacidad_id, "PROCESADA")

            return PromotionResult(
                success=True,
                pre_incapacidad_id=pre_incapacidad_id,
                incapacidad_id=None,  # TODO: set when created
                validation_summary=validation_summary,
                timestamp=datetime.utcnow(),
            )

        except Exception as e:
            logger.error(f"Error promoting pre-incapacidad {pre_incapacidad_id}: {str(e)}")
            await self.pre_inc_repo.update_error(
                self.db,
                pre_incapacidad_id,
                f"Error durante promoción: {str(e)}"
            )

            return PromotionResult(
                success=False,
                pre_incapacidad_id=pre_incapacidad_id,
                validation_summary=ValidationSummary(
                    total_issues=0,
                    errors=0,
                    warnings=0,
                    infos=0,
                    issues=[],
                ),
                error_message=f"Error durante promoción: {str(e)}",
                timestamp=datetime.utcnow(),
            )

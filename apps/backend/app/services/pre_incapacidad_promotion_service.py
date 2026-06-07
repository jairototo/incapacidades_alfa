"""
Servicio de promoción de pre-incapacidades a incapacidades completas.
Orquesta validación, persistencia de issues, y creación de incapacidad.
"""
from datetime import datetime
from typing import Optional
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
        clear_existing_issues: bool = False,
        usuario_id: Optional[UUID] = None,
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

            # 1b. Optionally clear existing validation issues (for manual re-promotion)
            if clear_existing_issues:
                deleted = await self.validation_repo.delete_by_pre_incapacidad(pre_incapacidad_id)
                await self.db.commit()
                await self.db.refresh(pre_inc)  # re-load after commit to avoid expired ORM object
                logger.info(f"Cleared {deleted} existing issues for {pre_incapacidad_id}")

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
            try:
                logger.debug(f"Starting validation for pre-incapacidad {pre_incapacidad_id}")
                validation_service = PreIncapacidadValidationService(
                    pre_incapacidad=pre_inc,
                    empleado=empleado,
                    empresa=empresa,
                )
                issues = await validation_service.validate_all()
                logger.debug(f"Validation produced {len(issues)} issues")
            except Exception as e:
                logger.error(f"Validation failed for {pre_incapacidad_id}: {str(e)}")
                raise

            # 4. Persistir issues a DB
            try:
                logger.debug(f"Persisting {len(issues)} validation issues")
                for issue_schema in issues:
                    await self.validation_repo.create(issue_schema)
                # Commit transaction explicitly to ensure issues are persisted to DB
                await self.db.commit()
                logger.debug(f"Issues persisted successfully")
            except Exception as e:
                logger.error(f"Failed to persist validation issues for {pre_incapacidad_id}: {str(e)}")
                raise

            # Contar issues por severidad
            try:
                logger.debug(f"Counting issues by severidad for {pre_incapacidad_id}")
                counts = await self.validation_repo.count_by_severidad(pre_incapacidad_id)
                logger.debug(f"Issue counts: {counts}")
            except Exception as e:
                logger.error(f"Failed to count issues for {pre_incapacidad_id}: {str(e)}")
                raise

            # Construir summary
            validation_summary = ValidationSummary(
                total_issues=counts["total"],
                errors=counts["ERROR"],
                warnings=counts["WARNING"],
                infos=counts["INFO"],
                issues=[],  # Por ahora empty, se pueden cargar si es necesario
            )

            # 5. Verificar si hay ERRORs
            try:
                logger.debug(f"Checking for errors in {pre_incapacidad_id}")
                has_errors = await self.validation_repo.has_errors(pre_incapacidad_id)
                logger.debug(f"Has errors: {has_errors}")
            except Exception as e:
                logger.error(f"Failed to check errors for {pre_incapacidad_id}: {str(e)}")
                raise

            if has_errors:
                logger.warning(
                    f"Pre-incapacidad {pre_incapacidad_id} validation failed - "
                    f"has {counts['ERROR']} errors. Not creating incapacidad."
                )
                await self.pre_inc_repo.update_estado(self.db, pre_incapacidad_id, "RECHAZADA")
                await self.db.commit()  # Commit estado change

                return PromotionResult(
                    success=False,
                    pre_incapacidad_id=pre_incapacidad_id,
                    validation_summary=validation_summary,
                    error_message=f"Validación fallida: {counts['ERROR']} errores encontrados",
                    timestamp=datetime.utcnow(),
                )

            # 6. Crear incapacidad real
            logger.info(
                f"Pre-incapacidad {pre_incapacidad_id} validation passed - "
                f"creating incapacidad..."
            )
            incapacidad_id = None
            try:
                from app.services.incapacidad_service import incapacidad_service
                from app.schemas.incapacidad import IncapacidadCreate
                from app.utils.enums import TipoIncapacidad

                inc_tipo = TipoIncapacidad(pre_inc.tipo)

                if inc_tipo == TipoIncapacidad.ARL:
                    # ARL requires empleado_id and empresa_id (UUID) from resolved entities
                    if not empleado or not empresa:
                        raise ValueError(
                            "empleado y empresa son requeridos para crear incapacidad ARL"
                        )
                    inc_data = IncapacidadCreate(
                        tipo=inc_tipo,
                        empleado_id=empleado.id,
                        empresa_id=empresa.id,
                        fecha_inicio=pre_inc.fecha_inicio,
                        fecha_fin=pre_inc.fecha_fin,
                        diagnostico_cie10=pre_inc.diagnostico_cie10,
                        descripcion_diagnostico=pre_inc.descripcion_diagnostico,
                        nombre_medico=pre_inc.nombre_medico,
                        registro_medico=pre_inc.registro_medico,
                        ips=pre_inc.ips,
                        valor_dia=pre_inc.valor_dia,
                        observaciones=pre_inc.observaciones,
                    )
                else:
                    # SALUD — not yet supported via pre-incapacidad flow
                    raise ValueError(
                        f"Tipo de incapacidad '{pre_inc.tipo}' no soportado en flujo de promoción"
                    )

                incapacidad = await incapacidad_service.create_incapacidad(
                    self.db,
                    inc_data,
                    usuario_id=usuario_id,
                )
                incapacidad_id = incapacidad.id
                logger.info(
                    f"Created incapacidad {incapacidad_id} from pre-incapacidad {pre_incapacidad_id}"
                )
            except Exception as e:
                logger.error(f"Failed to create incapacidad from {pre_incapacidad_id}: {e}")
                raise

            await self.pre_inc_repo.update_estado(self.db, pre_incapacidad_id, "PROCESADA")
            await self.db.commit()

            return PromotionResult(
                success=True,
                pre_incapacidad_id=pre_incapacidad_id,
                incapacidad_id=incapacidad_id,
                validation_summary=validation_summary,
                timestamp=datetime.utcnow(),
            )

        except Exception as e:
            # Re-raise infrastructure exceptions so Celery retry mechanism fires
            from sqlalchemy.exc import SQLAlchemyError
            try:
                from asyncpg import PostgresError as _PgError
            except ImportError:
                _PgError = None
            is_infra = isinstance(e, SQLAlchemyError) or (_PgError and isinstance(e, _PgError))
            if is_infra:
                raise
            logger.error(f"Error promoting pre-incapacidad {pre_incapacidad_id}: {str(e)}")
            await self.pre_inc_repo.update_error(
                self.db,
                pre_incapacidad_id,
                f"Error durante promoción: {str(e)}"
            )
            await self.db.commit()  # Commit error state change

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

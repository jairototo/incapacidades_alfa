"""
Servicio de promoción unificada: pre-incapacidad → incapacidad en un solo paso.

El job siempre crea una Incapacidad, incluso si empleado/empresa no se encuentran en BD.
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pre_incapacidad import PreIncapacidad
from app.db.repositories.pre_incapacidad_repository import PreIncapacidadRepository
from app.db.repositories.validation_inconsistencia_repository import ValidationInconsistenciaRepository
from app.db.repositories.empleado_repository import empleado_repository
from app.db.repositories.empresa_repository import empresa_repository
from app.services.pre_incapacidad_validation_service import PreIncapacidadValidationService
from app.schemas.validation_inconsistencia import (
    ValidationSummary,
    PromotionResult,
    ValidationInconsistenciaCreate,
)

# Module-level import so tests can patch it (use direct module import to avoid circular)
from app.services.incapacidad_service import incapacidad_service


class PromotePreIncapacidadService:
    """Servicio para promoción unificada de pre-incapacidades a incapacidades."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.pre_inc_repo = PreIncapacidadRepository()
        self.validation_repo = ValidationInconsistenciaRepository(db)

    async def promote_pre_incapacidad(
        self,
        pre_incapacidad_id: UUID,
        clear_existing_issues: bool = True,
        usuario_id: Optional[UUID] = None,
    ) -> PromotionResult:
        """
        Flujo unificado — siempre crea Incapacidad, maneja empleado faltante sin error.

        1. Fetch pre-incapacidad
        2. Clear existing issues (default: True)
        3. Resolve empresa + empleado (may be None)
        4. Run all validations — EMPLEADO/EMPRESA_NOT_FOUND now WARNING, not ERROR
        5. Create Incapacidad via create_from_pre_incapacidad()
        6. Link pre_incapacidad.incapacidad_id
        7. If empleado found: run audit business rules
        8. Transition incapacidad RADICADA → EN_AUDITORIA via radicar_incapacidad()
        9. Set pre_incapacidad.estado = PROCESADA
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
                        total_issues=0, errors=0, warnings=0, infos=0, issues=[],
                    ),
                    error_message="Pre-incapacidad no encontrada",
                    timestamp=datetime.utcnow(),
                )

            # Idempotency guard: never promote twice
            if pre_inc.estado == "PROCESADA" or pre_inc.incapacidad_id is not None:
                logger.info(
                    f"Pre-incapacidad {pre_incapacidad_id} already promoted "
                    f"(estado={pre_inc.estado}, incapacidad_id={pre_inc.incapacidad_id}); skipping"
                )
                counts = await self.validation_repo.count_by_severidad(pre_incapacidad_id)
                return PromotionResult(
                    success=True,
                    pre_incapacidad_id=pre_incapacidad_id,
                    incapacidad_id=pre_inc.incapacidad_id,
                    validation_summary=ValidationSummary(
                        total_issues=counts["total"],
                        errors=counts["ERROR"],
                        warnings=counts["WARNING"],
                        infos=counts["INFO"],
                        issues=[],
                    ),
                    timestamp=datetime.utcnow(),
                )

            # 2. Clear existing validation issues for idempotent re-runs
            if clear_existing_issues:
                deleted = await self.validation_repo.delete_by_pre_incapacidad(pre_incapacidad_id)
                await self.db.commit()
                await self.db.refresh(pre_inc)
                if deleted:
                    logger.info(f"Cleared {deleted} existing issues for {pre_incapacidad_id}")

            # 3. Resolve entities (may be None — no longer blocking)
            empresa = None
            empleado = None
            if pre_inc.empresa_nit:
                empresa = await empresa_repository.get_by_nit(self.db, pre_inc.empresa_nit)
            if pre_inc.tipo == "ARL" and empresa:
                empleado = await empleado_repository.get_by_documento(
                    self.db, pre_inc.empleado_numero_documento, empresa.id
                )

            # 4. Run all validations (EMPLEADO/EMPRESA_NOT_FOUND are now WARNING)
            validation_service = PreIncapacidadValidationService(pre_inc, empleado, empresa)
            issues = await validation_service.validate_all()

            for issue_schema in issues:
                await self.validation_repo.create(issue_schema)
            await self.db.commit()
            logger.debug(f"Persisted {len(issues)} validation issues for {pre_incapacidad_id}")

            # 5. Create Incapacidad unconditionally
            inc = await incapacidad_service.create_from_pre_incapacidad(
                self.db, pre_inc, empleado=empleado, empresa=empresa, usuario_id=usuario_id
            )
            incapacidad_id = inc.id
            logger.info(f"Created incapacidad {incapacidad_id} from pre-incapacidad {pre_incapacidad_id}")
            await self.db.commit()

            # 5b. Copy documents from pre_incapacidad → incapacidad
            copied = await self._copy_documents(pre_inc.id, incapacidad_id, usuario_id)
            if copied:
                await self.db.commit()
                logger.info(f"Copied {copied} documents to incapacidad {incapacidad_id}")

            # 6. Link pre_incapacidad → incapacidad
            pre_inc.incapacidad_id = incapacidad_id
            self.db.add(pre_inc)
            await self.db.commit()
            await self.db.refresh(pre_inc)

            # 7. Run additional audit rules when empleado is found
            if empleado:
                audit_issues = await self._run_audit_business_rules(pre_inc, inc, empleado)
                for issue in audit_issues:
                    await self.validation_repo.create(issue)
                if audit_issues:
                    await self.db.commit()
                    logger.info(f"Added {len(audit_issues)} audit rule issues for {pre_incapacidad_id}")

            # 8. Transition to EN_AUDITORIA
            await incapacidad_service.radicar_incapacidad(self.db, incapacidad_id, usuario_id)
            await self.db.commit()
            logger.info(f"Incapacidad {incapacidad_id} transitioned to EN_AUDITORIA")

            # 9. Mark pre-incapacidad as PROCESADA
            await self.pre_inc_repo.update_estado(self.db, pre_incapacidad_id, "PROCESADA")
            await self.db.commit()

            counts = await self.validation_repo.count_by_severidad(pre_incapacidad_id)
            validation_summary = ValidationSummary(
                total_issues=counts["total"],
                errors=counts["ERROR"],
                warnings=counts["WARNING"],
                infos=counts["INFO"],
                issues=[],
            )

            logger.success(
                f"Unified promotion complete for {pre_incapacidad_id}. "
                f"Incapacidad: {incapacidad_id}. Issues: {counts}"
            )

            return PromotionResult(
                success=True,
                pre_incapacidad_id=pre_incapacidad_id,
                incapacidad_id=incapacidad_id,
                validation_summary=validation_summary,
                timestamp=datetime.utcnow(),
            )

        except Exception as e:
            from sqlalchemy.exc import SQLAlchemyError
            try:
                from asyncpg import PostgresError as _PgError
            except ImportError:
                _PgError = None
            is_infra = isinstance(e, SQLAlchemyError) or (_PgError and isinstance(e, _PgError))
            if is_infra:
                raise

            logger.error(f"Error in unified promotion for {pre_incapacidad_id}: {e}")
            try:
                await self.pre_inc_repo.update_error(self.db, pre_incapacidad_id, str(e))
                await self.db.commit()
            except Exception:
                pass

            return PromotionResult(
                success=False,
                pre_incapacidad_id=pre_incapacidad_id,
                validation_summary=ValidationSummary(
                    total_issues=0, errors=0, warnings=0, infos=0, issues=[],
                ),
                error_message=f"Error durante promoción unificada: {str(e)}",
                timestamp=datetime.utcnow(),
            )

    async def _run_audit_business_rules(
        self,
        pre_inc: PreIncapacidad,
        incapacidad: object,
        empleado: object,
    ) -> List[ValidationInconsistenciaCreate]:
        """
        Additional audit checks from ai/skills/negocio/auditoria_liquidacion/ — only run when
        the employee record exists in the DB. Issues are INFO/WARNING, never blocking.

        Checks: RN008/VAL018 overlapping periods, RN009/VAL017 possible duplicate.
        """
        issues = []
        incapacidad_id = getattr(incapacidad, 'id', None)
        empleado_id = getattr(empleado, 'id', None)
        if not empleado_id:
            return issues

        try:
            from sqlalchemy import select, extract
            from app.models.incapacidad import Incapacidad
            from app.utils.enums import EstadoIncapacidad

            # RN008/VAL018 — overlapping periods
            overlap_query = select(Incapacidad).where(
                Incapacidad.empleado_id == empleado_id,
                Incapacidad.id != incapacidad_id,
                Incapacidad.estado != EstadoIncapacidad.CANCELADA,
                Incapacidad.fecha_inicio <= pre_inc.fecha_fin,
                Incapacidad.fecha_fin >= pre_inc.fecha_inicio,
            )
            overlap_result = await self.db.execute(overlap_query)
            overlapping = overlap_result.scalars().all()

            if overlapping:
                numeros = ", ".join(str(i.numero) for i in overlapping)
                issues.append(ValidationInconsistenciaCreate(
                    pre_incapacidad_id=pre_inc.id,
                    incapacidad_id=incapacidad_id,
                    categoria="BUSINESS_RULE",
                    severidad="WARNING",
                    codigo="OVERLAPPING_PERIOD",
                    descripcion=f"Período se traslapa con incapacidades existentes: {numeros}",
                    campo_afectado="fecha_inicio,fecha_fin",
                    valor_encontrado=f"{pre_inc.fecha_inicio} al {pre_inc.fecha_fin}",
                ))

            # RN009/VAL017 — possible duplicate (same employee + CIE10 + same month)
            duplicate_query = select(Incapacidad).where(
                Incapacidad.empleado_id == empleado_id,
                Incapacidad.id != incapacidad_id,
                Incapacidad.diagnostico_cie10 == pre_inc.diagnostico_cie10,
                extract('year', Incapacidad.fecha_inicio) == pre_inc.fecha_inicio.year,
                extract('month', Incapacidad.fecha_inicio) == pre_inc.fecha_inicio.month,
            )
            dup_result = await self.db.execute(duplicate_query)
            duplicates = dup_result.scalars().all()

            if duplicates:
                issues.append(ValidationInconsistenciaCreate(
                    pre_incapacidad_id=pre_inc.id,
                    incapacidad_id=incapacidad_id,
                    categoria="FRAUD_ALERT",
                    severidad="WARNING",
                    codigo="POSSIBLE_DUPLICATE",
                    descripcion="Posible duplicado: mismo empleado + CIE10 en el mismo mes",
                    campo_afectado="diagnostico_cie10",
                    valor_encontrado=pre_inc.diagnostico_cie10,
                ))

        except Exception as e:
            logger.warning(f"Audit rule check failed for {pre_inc.id}: {e}")

        return issues

    async def _copy_documents(
        self,
        pre_incapacidad_id: UUID,
        incapacidad_id: UUID,
        usuario_id: Optional[UUID],
    ) -> int:
        """Copy successful PreDocumento records into Documento for the new incapacidad."""
        from sqlalchemy import select
        from app.models.pre_documento import PreDocumento
        from app.models.documento import Documento
        from app.utils.enums import TipoDocumentoArchivo

        _TIPO_MAP = {
            "INCAPACIDAD_MEDICA": TipoDocumentoArchivo.INCAPACIDAD_MEDICA,
            "HISTORIA_CLINICA": TipoDocumentoArchivo.HISTORIA_CLINICA,
        }

        result = await self.db.execute(
            select(PreDocumento).where(
                PreDocumento.pre_incapacidad_id == pre_incapacidad_id,
                PreDocumento.estado_subida == "OK",
            )
        )
        pre_docs = result.scalars().all()

        for pre_doc in pre_docs:
            tipo = _TIPO_MAP.get(pre_doc.tipo_documento, TipoDocumentoArchivo.OTROS)
            doc = Documento(
                incapacidad_id=incapacidad_id,
                tipo_documento=tipo,
                nombre_archivo=pre_doc.nombre_original,
                nombre_original=pre_doc.nombre_original,
                ruta_storage=pre_doc.ruta_storage,
                bucket=pre_doc.bucket,
                mime_type=pre_doc.mime_type,
                tamanio_bytes=pre_doc.tamanio_bytes,
                uploaded_by_id=usuario_id,
                validado=False,
            )
            self.db.add(doc)

        if pre_docs:
            await self.db.flush()

        return len(pre_docs)

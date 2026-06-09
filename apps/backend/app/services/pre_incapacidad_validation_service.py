"""
Servicio de validación para pre-incapacidades.

Ejecuta 4 categorías de validación:
1. FIELD_VALIDATION: tipos, campos requeridos, formato
2. BUSINESS_RULE: lógica de negocio (rangos de fecha, cálculos)
3. FRAUD_ALERT: alertas de fraude/anomalía
4. INTEGRATION_CHECK: existencia de entidades relacionadas
"""
from datetime import date
from typing import Optional
from loguru import logger

from app.models.pre_incapacidad import PreIncapacidad
from app.models.empleado import Empleado
from app.models.empresa import Empresa
from app.schemas.validation_inconsistencia import ValidationInconsistenciaCreate


class PreIncapacidadValidationService:
    """Orquesta validación completa de pre-incapacidad."""

    def __init__(
        self,
        pre_incapacidad: PreIncapacidad,
        empleado: Optional[Empleado],
        empresa: Optional[Empresa],
    ):
        self.pre_inc = pre_incapacidad
        self.empleado = empleado
        self.empresa = empresa

    async def validate_field_level(self) -> list[ValidationInconsistenciaCreate]:
        """Validación de campos: tipos, requeridos, formato."""
        issues = []

        # Solicitante
        if not self.pre_inc.solicitante_correo or len(self.pre_inc.solicitante_correo) == 0:
            issues.append(ValidationInconsistenciaCreate(
                pre_incapacidad_id=self.pre_inc.id,
                categoria="FIELD_VALIDATION",
                severidad="ERROR",
                codigo="EMPTY_SOLICITANTE_CORREO",
                descripcion="Correo del solicitante es requerido",
                campo_afectado="solicitante_correo",
            ))
        elif "@" not in self.pre_inc.solicitante_correo:
            issues.append(ValidationInconsistenciaCreate(
                pre_incapacidad_id=self.pre_inc.id,
                categoria="FIELD_VALIDATION",
                severidad="ERROR",
                codigo="INVALID_EMAIL_FORMAT",
                descripcion="Formato de correo inválido",
                campo_afectado="solicitante_correo",
                valor_encontrado=self.pre_inc.solicitante_correo,
            ))

        if not self.pre_inc.solicitante_nombres or len(self.pre_inc.solicitante_nombres) == 0:
            issues.append(ValidationInconsistenciaCreate(
                pre_incapacidad_id=self.pre_inc.id,
                categoria="FIELD_VALIDATION",
                severidad="ERROR",
                codigo="EMPTY_SOLICITANTE_NOMBRES",
                descripcion="Nombres del solicitante son requeridos",
                campo_afectado="solicitante_nombres",
            ))

        # Empleado
        if not self.pre_inc.empleado_tipo_documento or len(self.pre_inc.empleado_tipo_documento) == 0:
            issues.append(ValidationInconsistenciaCreate(
                pre_incapacidad_id=self.pre_inc.id,
                categoria="FIELD_VALIDATION",
                severidad="ERROR",
                codigo="EMPTY_EMPLEADO_TIPO_DOC",
                descripcion="Tipo de documento del empleado es requerido",
                campo_afectado="empleado_tipo_documento",
            ))

        if not self.pre_inc.empleado_numero_documento or len(self.pre_inc.empleado_numero_documento) == 0:
            issues.append(ValidationInconsistenciaCreate(
                pre_incapacidad_id=self.pre_inc.id,
                categoria="FIELD_VALIDATION",
                severidad="ERROR",
                codigo="EMPTY_EMPLEADO_NUMERO",
                descripcion="Número de documento del empleado es requerido",
                campo_afectado="empleado_numero_documento",
            ))

        if not self.pre_inc.empleado_nombres or len(self.pre_inc.empleado_nombres) == 0:
            issues.append(ValidationInconsistenciaCreate(
                pre_incapacidad_id=self.pre_inc.id,
                categoria="FIELD_VALIDATION",
                severidad="ERROR",
                codigo="EMPTY_EMPLEADO_NOMBRES",
                descripcion="Nombres del empleado son requeridos",
                campo_afectado="empleado_nombres",
            ))

        # Incapacidad
        if not self.pre_inc.tipo or self.pre_inc.tipo not in ["ARL", "SALUD"]:
            issues.append(ValidationInconsistenciaCreate(
                pre_incapacidad_id=self.pre_inc.id,
                categoria="FIELD_VALIDATION",
                severidad="ERROR",
                codigo="INVALID_TIPO",
                descripcion="Tipo de incapacidad debe ser ARL o SALUD",
                campo_afectado="tipo",
                valor_encontrado=self.pre_inc.tipo,
            ))

        if not self.pre_inc.tipo_enfermedad:
            issues.append(ValidationInconsistenciaCreate(
                pre_incapacidad_id=self.pre_inc.id,
                categoria="FIELD_VALIDATION",
                severidad="ERROR",
                codigo="EMPTY_TIPO_ENFERMEDAD",
                descripcion="Tipo de enfermedad es requerido",
                campo_afectado="tipo_enfermedad",
            ))

        if not self.pre_inc.fecha_inicio:
            issues.append(ValidationInconsistenciaCreate(
                pre_incapacidad_id=self.pre_inc.id,
                categoria="FIELD_VALIDATION",
                severidad="ERROR",
                codigo="EMPTY_FECHA_INICIO",
                descripcion="Fecha de inicio es requerida",
                campo_afectado="fecha_inicio",
            ))

        if not self.pre_inc.fecha_fin:
            issues.append(ValidationInconsistenciaCreate(
                pre_incapacidad_id=self.pre_inc.id,
                categoria="FIELD_VALIDATION",
                severidad="ERROR",
                codigo="EMPTY_FECHA_FIN",
                descripcion="Fecha de fin es requerida",
                campo_afectado="fecha_fin",
            ))

        # Validación de rangos de fecha
        if self.pre_inc.fecha_inicio and self.pre_inc.fecha_fin:
            if self.pre_inc.fecha_fin < self.pre_inc.fecha_inicio:
                issues.append(ValidationInconsistenciaCreate(
                    pre_incapacidad_id=self.pre_inc.id,
                    categoria="FIELD_VALIDATION",
                    severidad="ERROR",
                    codigo="INVALID_DATE_RANGE",
                    descripcion="Fecha de fin no puede ser anterior a fecha de inicio",
                    campo_afectado="fecha_fin",
                    valor_encontrado=str(self.pre_inc.fecha_fin),
                    valor_esperado=f">= {self.pre_inc.fecha_inicio}",
                ))

        if not self.pre_inc.diagnostico_cie10 or len(self.pre_inc.diagnostico_cie10) == 0:
            issues.append(ValidationInconsistenciaCreate(
                pre_incapacidad_id=self.pre_inc.id,
                categoria="FIELD_VALIDATION",
                severidad="ERROR",
                codigo="EMPTY_DIAGNOSTICO_CIE10",
                descripcion="Diagnóstico CIE-10 es requerido",
                campo_afectado="diagnostico_cie10",
            ))

        if not self.pre_inc.nombre_medico or len(self.pre_inc.nombre_medico) == 0:
            issues.append(ValidationInconsistenciaCreate(
                pre_incapacidad_id=self.pre_inc.id,
                categoria="FIELD_VALIDATION",
                severidad="ERROR",
                codigo="EMPTY_NOMBRE_MEDICO",
                descripcion="Nombre del médico es requerido",
                campo_afectado="nombre_medico",
            ))

        if not self.pre_inc.registro_medico or len(self.pre_inc.registro_medico) == 0:
            issues.append(ValidationInconsistenciaCreate(
                pre_incapacidad_id=self.pre_inc.id,
                categoria="FIELD_VALIDATION",
                severidad="ERROR",
                codigo="EMPTY_REGISTRO_MEDICO",
                descripcion="Registro médico es requerido",
                campo_afectado="registro_medico",
            ))

        logger.info(f"Field validation: {len(issues)} issues found")
        return issues

    async def validate_business_rules(self) -> list[ValidationInconsistenciaCreate]:
        """Validación de reglas de negocio: cálculos, lógica de dominio."""
        issues = []

        # Validar días totales vs fechas
        if self.pre_inc.fecha_inicio and self.pre_inc.fecha_fin:
            expected_days = (self.pre_inc.fecha_fin - self.pre_inc.fecha_inicio).days + 1
            if self.pre_inc.dias_totales != expected_days:
                issues.append(ValidationInconsistenciaCreate(
                    pre_incapacidad_id=self.pre_inc.id,
                    categoria="BUSINESS_RULE",
                    severidad="WARNING",
                    codigo="DIAS_TOTALES_MISMATCH",
                    descripcion="Días totales no coincide con rango de fechas",
                    campo_afectado="dias_totales",
                    valor_encontrado=str(self.pre_inc.dias_totales),
                    valor_esperado=str(expected_days),
                ))

        # Validar que la incapacidad no sea retroactiva > 30 días
        if self.pre_inc.fecha_inicio:
            max_retroactive_days = 30
            days_ago = (date.today() - self.pre_inc.fecha_inicio).days
            if days_ago > max_retroactive_days:
                issues.append(ValidationInconsistenciaCreate(
                    pre_incapacidad_id=self.pre_inc.id,
                    categoria="BUSINESS_RULE",
                    severidad="WARNING",
                    codigo="RETROACTIVE_BEYOND_LIMIT",
                    descripcion=f"Incapacidad es retroactiva más de {max_retroactive_days} días",
                    campo_afectado="fecha_inicio",
                    valor_encontrado=str(self.pre_inc.fecha_inicio),
                ))

        # Validar duración máxima (180 días)
        if self.pre_inc.dias_totales and self.pre_inc.dias_totales > 180:
            issues.append(ValidationInconsistenciaCreate(
                pre_incapacidad_id=self.pre_inc.id,
                categoria="BUSINESS_RULE",
                severidad="WARNING",
                codigo="DURATION_EXCEEDS_LIMIT",
                descripcion="Duración excede 180 días (límite típico ARL)",
                campo_afectado="dias_totales",
                valor_encontrado=str(self.pre_inc.dias_totales),
                valor_esperado="<= 180",
            ))

        logger.info(f"Business rule validation: {len(issues)} issues found")
        return issues

    async def validate_fraud_alerts(self) -> list[ValidationInconsistenciaCreate]:
        """Detectar patrones de fraude o anomalías."""
        issues = []

        # Alerta: valor diario muy alto (> 500k)
        if self.pre_inc.valor_dia and self.pre_inc.valor_dia > 500000:
            issues.append(ValidationInconsistenciaCreate(
                pre_incapacidad_id=self.pre_inc.id,
                categoria="FRAUD_ALERT",
                severidad="WARNING",
                codigo="UNUSUALLY_HIGH_DAILY_VALUE",
                descripcion="Valor diario inusualmente alto (> 500k)",
                campo_afectado="valor_dia",
                valor_encontrado=str(self.pre_inc.valor_dia),
            ))

        logger.info(f"Fraud alert validation: {len(issues)} issues found")
        return issues

    async def validate_integration(self) -> list[ValidationInconsistenciaCreate]:
        """Validar que las entidades relacionadas existan en la BD."""
        issues = []

        # Verificar que empleado exista
        if self.pre_inc.tipo == "ARL":
            if not self.empleado:
                issues.append(ValidationInconsistenciaCreate(
                    pre_incapacidad_id=self.pre_inc.id,
                    categoria="INTEGRATION_CHECK",
                    severidad="WARNING",
                    codigo="EMPLEADO_NOT_FOUND",
                    descripcion=f"Empleado {self.pre_inc.empleado_numero_documento} no encontrado en BD. La incapacidad se crea pendiente de resolución.",
                    campo_afectado="empleado_id",
                    valor_encontrado=self.pre_inc.empleado_numero_documento,
                ))
            else:
                if self.empleado.estado != "ACTIVO":
                    issues.append(ValidationInconsistenciaCreate(
                        pre_incapacidad_id=self.pre_inc.id,
                        categoria="INTEGRATION_CHECK",
                        severidad="WARNING",
                        codigo="EMPLEADO_INACTIVE",
                        descripcion=f"Empleado está en estado {self.empleado.estado}",
                        campo_afectado="empleado_id",
                        valor_encontrado=self.empleado.estado,
                    ))

        # Verificar que empresa exista (si se proporciona NIT)
        if self.pre_inc.empresa_nit:
            if not self.empresa:
                issues.append(ValidationInconsistenciaCreate(
                    pre_incapacidad_id=self.pre_inc.id,
                    categoria="INTEGRATION_CHECK",
                    severidad="WARNING",
                    codigo="EMPRESA_NOT_FOUND",
                    descripcion=f"Empresa NIT {self.pre_inc.empresa_nit} no encontrada en BD. La incapacidad se crea pendiente de resolución.",
                    campo_afectado="empresa_id",
                    valor_encontrado=self.pre_inc.empresa_nit,
                ))
            else:
                if self.empresa.estado != "ACTIVA":
                    issues.append(ValidationInconsistenciaCreate(
                        pre_incapacidad_id=self.pre_inc.id,
                        categoria="INTEGRATION_CHECK",
                        severidad="WARNING",
                        codigo="EMPRESA_INACTIVE",
                        descripcion=f"Empresa está en estado {self.empresa.estado}",
                        campo_afectado="empresa_id",
                        valor_encontrado=self.empresa.estado,
                    ))

        logger.info(f"Integration validation: {len(issues)} issues found")
        return issues

    async def validate_all(self) -> list[ValidationInconsistenciaCreate]:
        """Ejecutar todas las validaciones en secuencia."""
        all_issues = []

        all_issues.extend(await self.validate_field_level())
        all_issues.extend(await self.validate_business_rules())
        all_issues.extend(await self.validate_fraud_alerts())
        all_issues.extend(await self.validate_integration())

        logger.info(f"Complete validation: {len(all_issues)} total issues")
        return all_issues

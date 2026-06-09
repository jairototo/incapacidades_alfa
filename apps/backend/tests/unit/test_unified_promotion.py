"""Tests for unified PromotePreIncapacidadService flow."""
import pytest
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.services.pre_incapacidad_promotion_service import PromotePreIncapacidadService


def make_pre_inc(estado="PENDIENTE", empresa_nit="900123456", tipo="ARL"):
    m = MagicMock()
    m.id = uuid4()
    m.numero_radicacion = 202600001
    m.tipo = tipo
    m.estado = estado
    m.empresa_nit = empresa_nit
    m.empleado_numero_documento = "12345678"
    m.fecha_inicio = date(2026, 1, 1)
    m.fecha_fin = date(2026, 1, 10)
    m.diagnostico_cie10 = "S00.0"
    m.descripcion_diagnostico = None
    m.nombre_medico = "Dr. Test"
    m.registro_medico = "RM001"
    m.ips = None
    m.valor_dia = Decimal("60000")
    m.observaciones = None
    m.incapacidad_id = None
    return m


@pytest.mark.asyncio
async def test_unified_always_creates_incapacidad_even_without_empleado():
    """Incapacidad is created even when empleado/empresa are not in the DB."""
    db = AsyncMock()
    service = PromotePreIncapacidadService(db)
    pre_inc = make_pre_inc()

    mock_incapacidad = MagicMock()
    mock_incapacidad.id = uuid4()

    service.pre_inc_repo = MagicMock()
    service.pre_inc_repo.get_by_id = AsyncMock(return_value=pre_inc)
    service.pre_inc_repo.update_estado = AsyncMock()
    service.pre_inc_repo.update_error = AsyncMock()
    service.validation_repo = MagicMock()
    service.validation_repo.delete_by_pre_incapacidad = AsyncMock(return_value=0)
    service.validation_repo.create = AsyncMock()
    service.validation_repo.count_by_severidad = AsyncMock(
        return_value={"total": 1, "ERROR": 0, "WARNING": 1, "INFO": 0}
    )

    with (
        patch("app.services.pre_incapacidad_promotion_service.empresa_repository") as mock_empresa_repo,
        patch("app.services.pre_incapacidad_promotion_service.empleado_repository") as mock_empleado_repo,
        patch("app.services.pre_incapacidad_promotion_service.incapacidad_service") as mock_inc_service,
        patch("app.services.pre_incapacidad_promotion_service.PreIncapacidadValidationService") as mock_val,
    ):
        mock_empresa_repo.get_by_nit = AsyncMock(return_value=None)
        mock_empleado_repo.get_by_documento = AsyncMock(return_value=None)
        mock_inc_service.create_from_pre_incapacidad = AsyncMock(return_value=mock_incapacidad)
        mock_inc_service.radicar_incapacidad = AsyncMock(return_value=mock_incapacidad)
        mock_val_instance = MagicMock()
        mock_val_instance.validate_all = AsyncMock(return_value=[])
        mock_val.return_value = mock_val_instance

        result = await service.promote_pre_incapacidad(pre_inc.id)

    assert result.success is True
    assert result.incapacidad_id == mock_incapacidad.id
    mock_inc_service.create_from_pre_incapacidad.assert_called_once()
    mock_inc_service.radicar_incapacidad.assert_called_once()
    service.pre_inc_repo.update_estado.assert_called_with(db, pre_inc.id, "PROCESADA")


@pytest.mark.asyncio
async def test_unified_links_incapacidad_id_on_pre_inc():
    """pre_incapacidad.incapacidad_id is set after incapacidad creation."""
    db = AsyncMock()
    service = PromotePreIncapacidadService(db)
    pre_inc = make_pre_inc()

    mock_incapacidad = MagicMock()
    mock_incapacidad.id = uuid4()

    service.pre_inc_repo = MagicMock()
    service.pre_inc_repo.get_by_id = AsyncMock(return_value=pre_inc)
    service.pre_inc_repo.update_estado = AsyncMock()
    service.pre_inc_repo.update_error = AsyncMock()
    service.validation_repo = MagicMock()
    service.validation_repo.delete_by_pre_incapacidad = AsyncMock(return_value=0)
    service.validation_repo.create = AsyncMock()
    service.validation_repo.count_by_severidad = AsyncMock(
        return_value={"total": 0, "ERROR": 0, "WARNING": 0, "INFO": 0}
    )

    with (
        patch("app.services.pre_incapacidad_promotion_service.empresa_repository") as mock_empresa_repo,
        patch("app.services.pre_incapacidad_promotion_service.empleado_repository") as mock_empleado_repo,
        patch("app.services.pre_incapacidad_promotion_service.incapacidad_service") as mock_inc_service,
        patch("app.services.pre_incapacidad_promotion_service.PreIncapacidadValidationService") as mock_val,
    ):
        mock_empresa_repo.get_by_nit = AsyncMock(return_value=None)
        mock_empleado_repo.get_by_documento = AsyncMock(return_value=None)
        mock_inc_service.create_from_pre_incapacidad = AsyncMock(return_value=mock_incapacidad)
        mock_inc_service.radicar_incapacidad = AsyncMock(return_value=mock_incapacidad)
        mock_val_instance = MagicMock()
        mock_val_instance.validate_all = AsyncMock(return_value=[])
        mock_val.return_value = mock_val_instance

        await service.promote_pre_incapacidad(pre_inc.id)

    assert pre_inc.incapacidad_id == mock_incapacidad.id


@pytest.mark.asyncio
async def test_unified_runs_audit_rules_when_empleado_found():
    """When empleado is found, _run_audit_business_rules is called."""
    db = AsyncMock()
    service = PromotePreIncapacidadService(db)
    pre_inc = make_pre_inc()
    mock_empresa = MagicMock()
    mock_empresa.id = uuid4()
    mock_empleado = MagicMock()
    mock_empleado.id = uuid4()
    mock_incapacidad = MagicMock()
    mock_incapacidad.id = uuid4()

    service.pre_inc_repo = MagicMock()
    service.pre_inc_repo.get_by_id = AsyncMock(return_value=pre_inc)
    service.pre_inc_repo.update_estado = AsyncMock()
    service.pre_inc_repo.update_error = AsyncMock()
    service.validation_repo = MagicMock()
    service.validation_repo.delete_by_pre_incapacidad = AsyncMock(return_value=0)
    service.validation_repo.create = AsyncMock()
    service.validation_repo.count_by_severidad = AsyncMock(
        return_value={"total": 0, "ERROR": 0, "WARNING": 0, "INFO": 0}
    )

    with (
        patch("app.services.pre_incapacidad_promotion_service.empresa_repository") as mock_empresa_repo,
        patch("app.services.pre_incapacidad_promotion_service.empleado_repository") as mock_empleado_repo,
        patch("app.services.pre_incapacidad_promotion_service.incapacidad_service") as mock_inc_service,
        patch("app.services.pre_incapacidad_promotion_service.PreIncapacidadValidationService") as mock_val,
        patch.object(service, "_run_audit_business_rules", new=AsyncMock(return_value=[])) as mock_audit,
    ):
        mock_empresa_repo.get_by_nit = AsyncMock(return_value=mock_empresa)
        mock_empleado_repo.get_by_documento = AsyncMock(return_value=mock_empleado)
        mock_inc_service.create_from_pre_incapacidad = AsyncMock(return_value=mock_incapacidad)
        mock_inc_service.radicar_incapacidad = AsyncMock(return_value=mock_incapacidad)
        mock_val_instance = MagicMock()
        mock_val_instance.validate_all = AsyncMock(return_value=[])
        mock_val.return_value = mock_val_instance

        await service.promote_pre_incapacidad(pre_inc.id)

    mock_audit.assert_called_once()

"""
Unit tests for creacion_siniestro endpoint — role-based access control.

Tests:
1. AUDITOR calling the endpoint → returns the incapacidad (not 403)
2. EMPRESA calling the endpoint → raises ForbiddenException (403)
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.core.exceptions import ForbiddenException
from app.utils.enums import RolUsuario, TipoIncapacidad, EstadoIncapacidad


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_user(rol: RolUsuario):
    user = MagicMock()
    user.id = uuid4()
    user.rol = rol
    user.nombre_completo = f"Test {rol.value}"
    return user


def make_incapacidad():
    inc = MagicMock()
    inc.id = uuid4()
    inc.tipo = TipoIncapacidad.ARL
    inc.estado = EstadoIncapacidad.CREACION_SINIESTRO
    inc.numero_siniestro = "PENDIENTE"
    return inc


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_auditor_can_iniciar_creacion_siniestro():
    """AUDITOR must be allowed to trigger creacion-siniestro (no ForbiddenException)."""
    from app.api.v1.endpoints.creacion_siniestro import (
        iniciar_creacion_siniestro,
        CreacionSiniestroRequest,
    )

    incapacidad_id = uuid4()
    mock_inc = make_incapacidad()
    mock_inc.id = incapacidad_id

    body = CreacionSiniestroRequest(
        numero_siniestro="PENDIENTE",
        observacion="Auditor solicitó creación de siniestro: no se encontraron candidatos locales",
    )
    current_user = make_user(RolUsuario.AUDITOR)
    db = AsyncMock()

    with (
        patch(
            "app.api.v1.endpoints.creacion_siniestro.incapacidad_service"
        ) as mock_service,
        patch(
            "app.api.v1.endpoints.creacion_siniestro.vincular_siniestro_externo_task"
        ) as mock_task,
    ):
        mock_service.iniciar_creacion_siniestro = AsyncMock(return_value=mock_inc)
        mock_task.delay = MagicMock()

        result = await iniciar_creacion_siniestro(
            incapacidad_id=incapacidad_id,
            body=body,
            current_user=current_user,
            db=db,
        )

    # No ForbiddenException raised — AUDITOR is allowed
    assert result is mock_inc
    mock_service.iniciar_creacion_siniestro.assert_awaited_once()


@pytest.mark.asyncio
async def test_empresa_cannot_iniciar_creacion_siniestro():
    """EMPRESA role must be rejected with ForbiddenException."""
    from app.api.v1.endpoints.creacion_siniestro import (
        iniciar_creacion_siniestro,
        CreacionSiniestroRequest,
    )

    incapacidad_id = uuid4()
    body = CreacionSiniestroRequest(
        numero_siniestro="PENDIENTE",
        observacion="Intento no autorizado",
    )
    current_user = make_user(RolUsuario.EMPRESA)
    db = AsyncMock()

    with pytest.raises(ForbiddenException):
        await iniciar_creacion_siniestro(
            incapacidad_id=incapacidad_id,
            body=body,
            current_user=current_user,
            db=db,
        )


@pytest.mark.asyncio
async def test_admin_can_iniciar_creacion_siniestro():
    """ADMIN must still be allowed (regression check)."""
    from app.api.v1.endpoints.creacion_siniestro import (
        iniciar_creacion_siniestro,
        CreacionSiniestroRequest,
    )

    incapacidad_id = uuid4()
    mock_inc = make_incapacidad()
    mock_inc.id = incapacidad_id

    body = CreacionSiniestroRequest(
        numero_siniestro="SINX-2026-001",
        observacion="Admin vinculando siniestro externo",
    )
    current_user = make_user(RolUsuario.ADMIN)
    db = AsyncMock()

    with (
        patch(
            "app.api.v1.endpoints.creacion_siniestro.incapacidad_service"
        ) as mock_service,
        patch(
            "app.api.v1.endpoints.creacion_siniestro.vincular_siniestro_externo_task"
        ) as mock_task,
    ):
        mock_service.iniciar_creacion_siniestro = AsyncMock(return_value=mock_inc)
        mock_task.delay = MagicMock()

        result = await iniciar_creacion_siniestro(
            incapacidad_id=incapacidad_id,
            body=body,
            current_user=current_user,
            db=db,
        )

    assert result is mock_inc
    mock_service.iniciar_creacion_siniestro.assert_awaited_once()

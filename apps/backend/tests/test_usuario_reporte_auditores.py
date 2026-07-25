import pytest
from app.core.exceptions import ForbiddenException
from app.utils.enums import RolUsuario, EstadoUsuario, SucursalSiniestro
from app.services.usuario_service import usuario_service


@pytest.mark.asyncio
async def test_reporte_auditores_returns_only_auditores(db_session, test_usuario, test_user_auditor):
    reporte = await usuario_service.reporte_auditores(db_session, admin_rol=RolUsuario.ADMIN)

    usernames = {u.username for u in reporte}
    assert "auditor" in usernames  # test_user_auditor
    assert "testuser" not in usernames  # test_usuario is ADMIN, excluded


@pytest.mark.asyncio
async def test_reporte_auditores_forbidden_for_non_admin():
    with pytest.raises(ForbiddenException):
        await usuario_service.reporte_auditores(None, admin_rol=RolUsuario.AUDITOR)

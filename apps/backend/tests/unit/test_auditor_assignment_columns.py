import pytest
from app.utils.enums import RolUsuario, EstadoUsuario, SucursalSiniestro


@pytest.mark.asyncio
async def test_usuario_has_sucursal_and_carga_columns(db_session):
    from app.models.usuario import Usuario
    from app.core.security import get_password_hash

    usuario = Usuario(
        username="test.auditor.col",
        email="test.auditor.col@example.com",
        password_hash=get_password_hash("Test123!"),
        nombre_completo="Auditor Columnas Test",
        rol=RolUsuario.AUDITOR,
        estado=EstadoUsuario.ACTIVO,
        sucursal=SucursalSiniestro.CALI,
    )
    db_session.add(usuario)
    await db_session.commit()
    await db_session.refresh(usuario)

    assert usuario.sucursal == SucursalSiniestro.CALI
    assert usuario.incapacidades_asignadas_activas == 0


@pytest.mark.asyncio
async def test_incapacidad_has_auditor_asignado_column(db_session, test_incapacidad, test_user_auditor):
    test_incapacidad.auditor_asignado_id = test_user_auditor.id
    db_session.add(test_incapacidad)
    await db_session.commit()
    await db_session.refresh(test_incapacidad)

    assert test_incapacidad.auditor_asignado_id == test_user_auditor.id

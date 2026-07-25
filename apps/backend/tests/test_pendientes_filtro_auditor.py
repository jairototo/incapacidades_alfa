import pytest
from datetime import date, datetime
from app.models.incapacidad import Incapacidad
from app.models.usuario import Usuario
from app.utils.enums import TipoIncapacidad, EstadoIncapacidad, RolUsuario, EstadoUsuario
from app.core.security import get_password_hash
from app.services.incapacidad_service import incapacidad_service


@pytest.mark.asyncio
async def test_listar_pendientes_filters_by_auditor_asignado(db_session, test_empleado, test_empresa):
    auditor_a = Usuario(
        username="test.filtro.a", email="test.filtro.a@segurosalfa-test.com.co",
        password_hash=get_password_hash("Test123!"), nombre_completo="Auditor A",
        rol=RolUsuario.AUDITOR, estado=EstadoUsuario.ACTIVO,
    )
    auditor_b = Usuario(
        username="test.filtro.b", email="test.filtro.b@segurosalfa-test.com.co",
        password_hash=get_password_hash("Test123!"), nombre_completo="Auditor B",
        rol=RolUsuario.AUDITOR, estado=EstadoUsuario.ACTIVO,
    )
    db_session.add_all([auditor_a, auditor_b])
    await db_session.commit()

    inc_a = Incapacidad(
        numero="ARL-FILTRO-A", tipo=TipoIncapacidad.ARL, empleado_id=test_empleado.id,
        empresa_id=test_empresa.id, fecha_inicio=date(2026, 6, 1), fecha_fin=date(2026, 6, 5),
        dias_totales=5, estado=EstadoIncapacidad.EN_AUDITORIA, fecha_radicacion=datetime.utcnow(),
        auditor_asignado_id=auditor_a.id,
    )
    inc_b = Incapacidad(
        numero="ARL-FILTRO-B", tipo=TipoIncapacidad.ARL, empleado_id=test_empleado.id,
        empresa_id=test_empresa.id, fecha_inicio=date(2026, 6, 1), fecha_fin=date(2026, 6, 5),
        dias_totales=5, estado=EstadoIncapacidad.EN_AUDITORIA, fecha_radicacion=datetime.utcnow(),
        auditor_asignado_id=auditor_b.id,
    )
    db_session.add_all([inc_a, inc_b])
    await db_session.commit()

    resultados = await incapacidad_service.listar_pendientes(
        db=db_session, auditor_asignado_id=auditor_a.id
    )

    numeros = {item['incapacidad'].numero for item in resultados}
    assert numeros == {"ARL-FILTRO-A"}

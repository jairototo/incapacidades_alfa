import datetime as dt
import re
import pytest
from app.services.radicacion_pipeline_service import RadicacionPipelineService
from app.schemas.radicacion import RadicacionRowInput
from app.models.empresa import Empresa
from app.models.empleado import Empleado
from app.utils.enums import EstadoIncapacidad


async def _seed(db):
    empresa = Empresa(nit="900333", razon_social="GAMMA SA", email_contacto="rrhh@gamma.com", estado="ACTIVA")
    db.add(empresa); await db.flush()
    empleado = Empleado(empresa_id=empresa.id, numero_documento="123456", tipo_documento="CC",
                        nombres="Juan", apellidos="Pérez", fecha_ingreso=dt.date(2020, 1, 1), estado="ACTIVO")
    db.add(empleado); await db.flush()
    return empresa, empleado


@pytest.mark.asyncio
async def test_pipeline_creates_incapacidad_radicada(db_session):
    empresa, empleado = await _seed(db_session)
    enqueued = []
    svc = RadicacionPipelineService(db_session, enqueue_auditoria=lambda iid: enqueued.append(iid))
    row = RadicacionRowInput(
        empleado_id=empleado.id, tipo_enfermedad="ACCIDENTE_TRABAJO",
        fecha_inicio=dt.date(2026, 6, 1), fecha_fin=dt.date(2026, 6, 5), dias_totales=5,
        diagnostico_cie10="S00.0", nombre_medico="Dr X", registro_medico="RM-1", prorroga=True,
    )
    resp = await svc.radicar([row], empresa=empresa, radicado_por_id=None)
    assert resp.total_radicadas == 1
    item = resp.items[0]
    assert item.success and item.numero
    assert re.match(r"^ARL-\d{8}-\d{4}$", item.numero)
    assert len(enqueued) == 1
    from app.models.incapacidad import Incapacidad
    from sqlalchemy import select
    inc = (await db_session.execute(select(Incapacidad).where(Incapacidad.id == item.incapacidad_id))).scalar_one()
    assert inc.prorroga is True
    assert inc.estado == EstadoIncapacidad.RADICADA
    assert inc.solicitante_id is not None
    assert inc.empresa_id == empresa.id


@pytest.mark.asyncio
async def test_pipeline_rejects_employee_of_other_company(db_session):
    empresa, empleado = await _seed(db_session)
    other = Empresa(nit="900999", razon_social="OTHER SA", email_contacto="o@o.com", estado="ACTIVA")
    db_session.add(other); await db_session.flush()
    svc = RadicacionPipelineService(db_session, enqueue_auditoria=lambda iid: None)
    row = RadicacionRowInput(
        empleado_id=empleado.id, tipo_enfermedad="ACCIDENTE_TRABAJO",
        fecha_inicio=dt.date(2026, 6, 1), fecha_fin=dt.date(2026, 6, 5), dias_totales=5,
        diagnostico_cie10="S00.0", nombre_medico="Dr X", registro_medico="RM-1",
    )
    resp = await svc.radicar([row], empresa=other, radicado_por_id=None)
    assert resp.items[0].success is False
    assert "empresa" in (resp.items[0].error or "").lower()


@pytest.mark.asyncio
async def test_pipeline_numbers_increment_within_batch(db_session):
    empresa, empleado = await _seed(db_session)
    svc = RadicacionPipelineService(db_session, enqueue_auditoria=lambda iid: None)
    def _row():
        return RadicacionRowInput(
            empleado_id=empleado.id, tipo_enfermedad="ACCIDENTE_TRABAJO",
            fecha_inicio=dt.date(2026, 6, 1), fecha_fin=dt.date(2026, 6, 5), dias_totales=5,
            diagnostico_cie10="S00.0", nombre_medico="Dr X", registro_medico="RM-1")
    resp = await svc.radicar([_row(), _row()], empresa=empresa, radicado_por_id=None)
    assert resp.total_radicadas == 2
    numeros = sorted(i.numero for i in resp.items)
    assert numeros[0].endswith("-0001") and numeros[1].endswith("-0002")

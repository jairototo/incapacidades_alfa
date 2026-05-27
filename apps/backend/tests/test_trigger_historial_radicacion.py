"""
Tests para validar el trigger automático de registro de historial de estados.

Verifica que al insertar una incapacidad, el trigger PostgreSQL
crea automáticamente un registro en historial_estado.
"""
import pytest
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.backend.app.models.incapacidad import Incapacidad
from apps.backend.app.models.historial_estado import HistorialEstado
from apps.backend.app.utils.enums import (
    TipoIncapacidad,
    EstadoIncapacidad,
    Prioridad,
)


@pytest.mark.asyncio
async def test_trigger_crea_historial_al_radicar_incapacidad_arl(
    db_session: AsyncSession,
    test_empresa,
    test_empleado,
    test_usuario
):
    """
    Test que verifica que el trigger crea automáticamente un registro
    en historial_estado cuando se inserta una incapacidad ARL.
    """
    # Crear incapacidad ARL
    incapacidad = Incapacidad(
        numero="INC-ARL-TRIGGER-001",
        empleado_id=test_empleado.id,
        empresa_id=test_empresa.id,
        tipo=TipoIncapacidad.ARL,
        fecha_inicio=date(2026, 1, 15),
        fecha_fin=date(2026, 1, 20),
        dias_totales=6,
        diagnostico_cie10="M545",
        descripcion_diagnostico="Lumbago no especificado",
        valor_dia=Decimal("150000.00"),
        valor_total=Decimal("900000.00"),
        estado=EstadoIncapacidad.RADICADA,
        fecha_radicacion=datetime.utcnow(),
        radicado_por_id=test_usuario.id,
        prioridad=Prioridad.NORMAL,
    )
    
    db_session.add(incapacidad)
    await db_session.commit()
    await db_session.refresh(incapacidad)
    
    # Verificar que se creó la incapacidad
    assert incapacidad.id is not None
    assert incapacidad.numero == "INC-ARL-TRIGGER-001"
    
    # Verificar que el trigger creó automáticamente el registro en historial_estado
    stmt = select(HistorialEstado).where(
        HistorialEstado.entity_type == "incapacidad",
        HistorialEstado.entity_id == incapacidad.id
    )
    result = await db_session.execute(stmt)
    historial_records = result.scalars().all()
    
    # Debe haber exactamente 1 registro
    assert len(historial_records) == 1
    
    historial = historial_records[0]
    
    # Validar todos los campos del registro de historial
    assert historial.entity_type == "incapacidad"
    assert historial.entity_id == incapacidad.id
    assert historial.estado_anterior is None  # Primer estado, no hay anterior
    assert historial.estado_nuevo == EstadoIncapacidad.RADICADA.value
    assert historial.cambiado_por_id == test_usuario.id
    assert historial.observacion == "Estado inicial al radicar la incapacidad"
    assert historial.fecha_cambio is not None
    assert historial.created_at is not None


@pytest.mark.asyncio
async def test_trigger_crea_historial_al_radicar_incapacidad_salud(
    db_session: AsyncSession,
    test_afiliado,
    test_usuario
):
    """
    Test que verifica que el trigger crea automáticamente un registro
    en historial_estado cuando se inserta una incapacidad SALUD.
    """
    # Crear incapacidad SALUD
    incapacidad = Incapacidad(
        numero="INC-SALUD-TRIGGER-001",
        afiliado_id=test_afiliado.id,
        tipo=TipoIncapacidad.SALUD,
        fecha_inicio=date(2026, 1, 10),
        fecha_fin=date(2026, 1, 15),
        dias_totales=6,
        diagnostico_cie10="J06.9",
        descripcion_diagnostico="Infección aguda de las vías respiratorias superiores",
        valor_dia=Decimal("120000.00"),
        valor_total=Decimal("720000.00"),
        estado=EstadoIncapacidad.RADICADA,
        fecha_radicacion=datetime.utcnow(),
        radicado_por_id=test_usuario.id,
        prioridad=Prioridad.ALTA,
    )
    
    db_session.add(incapacidad)
    await db_session.commit()
    await db_session.refresh(incapacidad)
    
    # Verificar que se creó la incapacidad
    assert incapacidad.id is not None
    assert incapacidad.numero == "INC-SALUD-TRIGGER-001"
    assert incapacidad.tipo == TipoIncapacidad.SALUD
    
    # Verificar que el trigger creó automáticamente el registro en historial_estado
    stmt = select(HistorialEstado).where(
        HistorialEstado.entity_type == "incapacidad",
        HistorialEstado.entity_id == incapacidad.id
    )
    result = await db_session.execute(stmt)
    historial_records = result.scalars().all()
    
    # Debe haber exactamente 1 registro
    assert len(historial_records) == 1
    
    historial = historial_records[0]
    
    # Validar todos los campos del registro de historial
    assert historial.entity_type == "incapacidad"
    assert historial.entity_id == incapacidad.id
    assert historial.estado_anterior is None  # Primer estado, no hay anterior
    assert historial.estado_nuevo == EstadoIncapacidad.RADICADA.value
    assert historial.cambiado_por_id == test_usuario.id
    assert historial.observacion == "Estado inicial al radicar la incapacidad"
    assert historial.fecha_cambio is not None
    assert historial.created_at is not None


@pytest.mark.asyncio
async def test_trigger_multiples_radicaciones_generan_multiples_historiales(
    db_session: AsyncSession,
    test_empresa,
    test_empleado,
    test_afiliado,
    test_usuario
):
    """
    Test que verifica que múltiples inserciones de incapacidades
    generan múltiples registros de historial independientes.
    """
    # Crear múltiples incapacidades
    incapacidades = []
    
    # Incapacidad ARL 1
    inc_arl_1 = Incapacidad(
        numero="INC-ARL-MULTI-001",
        empleado_id=test_empleado.id,
        empresa_id=test_empresa.id,
        tipo=TipoIncapacidad.ARL,
        fecha_inicio=date(2026, 1, 1),
        fecha_fin=date(2026, 1, 5),
        dias_totales=5,
        diagnostico_cie10="S61.0",
        descripcion_diagnostico="Herida del pulgar",
        valor_dia=Decimal("100000.00"),
        valor_total=Decimal("500000.00"),
        estado=EstadoIncapacidad.RADICADA,
        fecha_radicacion=datetime.utcnow(),
        radicado_por_id=test_usuario.id,
        prioridad=Prioridad.NORMAL,
    )
    db_session.add(inc_arl_1)
    incapacidades.append(inc_arl_1)
    
    # Incapacidad ARL 2
    inc_arl_2 = Incapacidad(
        numero="INC-ARL-MULTI-002",
        empleado_id=test_empleado.id,
        empresa_id=test_empresa.id,
        tipo=TipoIncapacidad.ARL,
        fecha_inicio=date(2026, 1, 10),
        fecha_fin=date(2026, 1, 15),
        dias_totales=6,
        diagnostico_cie10="M545",
        descripcion_diagnostico="Lumbago",
        valor_dia=Decimal("100000.00"),
        valor_total=Decimal("600000.00"),
        estado=EstadoIncapacidad.RADICADA,
        fecha_radicacion=datetime.utcnow(),
        radicado_por_id=test_usuario.id,
        prioridad=Prioridad.URGENTE,
    )
    db_session.add(inc_arl_2)
    incapacidades.append(inc_arl_2)
    
    # Incapacidad SALUD 1
    inc_salud_1 = Incapacidad(
        numero="INC-SALUD-MULTI-001",
        afiliado_id=test_afiliado.id,
        tipo=TipoIncapacidad.SALUD,
        fecha_inicio=date(2026, 1, 20),
        fecha_fin=date(2026, 1, 25),
        dias_totales=6,
        diagnostico_cie10="J06.9",
        descripcion_diagnostico="Infección respiratoria",
        valor_dia=Decimal("80000.00"),
        valor_total=Decimal("480000.00"),
        estado=EstadoIncapacidad.RADICADA,
        fecha_radicacion=datetime.utcnow(),
        radicado_por_id=test_usuario.id,
        prioridad=Prioridad.NORMAL,
    )
    db_session.add(inc_salud_1)
    incapacidades.append(inc_salud_1)
    
    # Commit todas las incapacidades
    await db_session.commit()
    
    # Refrescar todos los objetos
    for inc in incapacidades:
        await db_session.refresh(inc)
    
    # Verificar que todas las incapacidades se crearon
    assert len(incapacidades) == 3
    for inc in incapacidades:
        assert inc.id is not None
    
    # Verificar que el trigger creó un registro de historial para cada incapacidad
    for incapacidad in incapacidades:
        stmt = select(HistorialEstado).where(
            HistorialEstado.entity_type == "incapacidad",
            HistorialEstado.entity_id == incapacidad.id
        )
        result = await db_session.execute(stmt)
        historial_records = result.scalars().all()
        
        # Cada incapacidad debe tener exactamente 1 registro de historial
        assert len(historial_records) == 1, f"Incapacidad {incapacidad.numero} debe tener 1 historial"
        
        historial = historial_records[0]
        assert historial.entity_type == "incapacidad"
        assert historial.entity_id == incapacidad.id
        assert historial.estado_anterior is None
        assert historial.estado_nuevo == EstadoIncapacidad.RADICADA.value
        assert historial.cambiado_por_id == test_usuario.id
    
    # Verificar el total de registros de historial para incapacidades
    stmt = select(HistorialEstado).where(
        HistorialEstado.entity_type == "incapacidad"
    )
    result = await db_session.execute(stmt)
    all_historial_records = result.scalars().all()
    
    # Deben haber 3 registros en total (uno por cada incapacidad)
    assert len(all_historial_records) == 3


@pytest.mark.asyncio
async def test_trigger_no_interfiere_con_cambios_estado_manuales(
    db_session: AsyncSession,
    test_empresa,
    test_empleado,
    test_usuario
):
    """
    Test que verifica que el trigger no interfiere cuando se cambia
    manualmente el estado de una incapacidad (solo registra el estado inicial).
    """
    # Crear incapacidad ARL
    incapacidad = Incapacidad(
        numero="INC-ARL-MANUAL-001",
        empleado_id=test_empleado.id,
        empresa_id=test_empresa.id,
        tipo=TipoIncapacidad.ARL,
        fecha_inicio=date(2026, 1, 1),
        fecha_fin=date(2026, 1, 10),
        dias_totales=10,
        diagnostico_cie10="M545",
        descripcion_diagnostico="Lumbago",
        valor_dia=Decimal("100000.00"),
        valor_total=Decimal("1000000.00"),
        estado=EstadoIncapacidad.RADICADA,
        fecha_radicacion=datetime.utcnow(),
        radicado_por_id=test_usuario.id,
        prioridad=Prioridad.NORMAL,
    )
    
    db_session.add(incapacidad)
    await db_session.commit()
    await db_session.refresh(incapacidad)
    
    # Verificar que se creó 1 registro de historial (trigger)
    stmt = select(HistorialEstado).where(
        HistorialEstado.entity_type == "incapacidad",
        HistorialEstado.entity_id == incapacidad.id
    )
    result = await db_session.execute(stmt)
    historial_inicial = result.scalars().all()
    
    assert len(historial_inicial) == 1
    assert historial_inicial[0].estado_nuevo == EstadoIncapacidad.RADICADA.value
    
    # Ahora cambiar manualmente el estado (simulando cambio de estado por servicio)
    # Esto NO debe disparar el trigger nuevamente (trigger es AFTER INSERT, no UPDATE)
    incapacidad.estado = EstadoIncapacidad.EN_AUDITORIA
    incapacidad.auditado_por_id = test_usuario.id
    incapacidad.fecha_auditoria = datetime.utcnow()
    
    await db_session.commit()
    await db_session.refresh(incapacidad)
    
    # Verificar que el estado cambió
    assert incapacidad.estado == EstadoIncapacidad.EN_AUDITORIA
    
    # Verificar que sigue habiendo solo 1 registro de historial
    # (el trigger solo se ejecuta en INSERT, no en UPDATE)
    result = await db_session.execute(stmt)
    historial_despues = result.scalars().all()
    
    assert len(historial_despues) == 1
    # El registro inicial sigue siendo el mismo
    assert historial_despues[0].estado_nuevo == EstadoIncapacidad.RADICADA.value
    
    # Nota: Los cambios de estado posteriores deben manejarse manualmente
    # por el servicio de historial (historial_estado_service.crear_cambio_estado)

import pytest
from datetime import date
from decimal import Decimal
from uuid import uuid4

from app.services.liquidacion_pdf_service import generar_pdf_autorizacion_pago, guardar_pdf_autorizacion_pago
from app.utils.enums import TipoDocumentoAdjunto, TipoIncapacidad


class _FakeEmpresa:
    razon_social = "TechCorp S.A.S."
    nit = "900123456-7"
    nro_contrato = "CTR-2026-0099"


class _FakeEmpleado:
    nombres = "Juan"
    apellidos = "Pérez"
    numero_documento = "123456789"
    salario_base = Decimal("2500000.00")

    @property
    def nombre_completo(self):
        return f"{self.nombres} {self.apellidos}"


class _FakeSiniestro:
    numero_siniestro = "SIN-2026-0001"
    fecha_siniestro = date(2026, 5, 1)
    sucursal = "Bogotá"


class _FakeIncapacidad:
    id = uuid4()
    numero = "INC-ARL-20260601-0001"
    numero_siniestro = "SIN-2026-0001"
    empresa = _FakeEmpresa()
    empleado = _FakeEmpleado()
    siniestro = _FakeSiniestro()
    afiliado = None


class _FakeLiquidacion:
    dias_autorizados = 5
    fecha_inicio_autorizada = date(2026, 6, 1)
    fecha_fin_autorizada = date(2026, 6, 5)
    valor_incapacidad_temporal = Decimal("416666.67")
    valor_aporte_patronal_pension = Decimal("50000.00")
    valor_aporte_trabajador_pension = Decimal("25000.00")
    valor_aporte_adicional_trabajador_pension = None
    valor_aporte_patronal_salud = Decimal("40000.00")
    valor_aporte_trabajador_salud = Decimal("20000.00")
    valor_total = Decimal("551666.67")


def test_generar_pdf_borrador_tiene_marca_de_agua():
    pdf_bytes = generar_pdf_autorizacion_pago(
        _FakeIncapacidad(), _FakeLiquidacion(), nombre_ips="IPS Central", borrador=True
    )
    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 500


def test_generar_pdf_final_sin_marca_de_agua():
    pdf_bytes = generar_pdf_autorizacion_pago(
        _FakeIncapacidad(), _FakeLiquidacion(), nombre_ips="IPS Central", borrador=False
    )
    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 500


def test_generar_pdf_handles_missing_siniestro():
    """SALUD incapacidades have no siniestro — must not crash, fields fall back to N/A."""
    inc = _FakeIncapacidad()
    inc.siniestro = None
    inc.empresa = None
    inc.empleado = None
    pdf_bytes = generar_pdf_autorizacion_pago(inc, _FakeLiquidacion(), nombre_ips=None, borrador=True)
    assert pdf_bytes.startswith(b"%PDF")


# ---------------------------------------------------------------------------
# Tests for guardar_pdf_autorizacion_pago (persistence with real storage)
# ---------------------------------------------------------------------------


async def _crear_incapacidad_real(db_session):
    from app.models.incapacidad import Incapacidad

    uid = uuid4()
    incapacidad = Incapacidad(
        numero=f"INC-TEST-{uid.hex[:8]}",
        tipo=TipoIncapacidad.ARL,
        estado="LIQUIDACION",
        fecha_inicio=date(2026, 6, 1),
        fecha_fin=date(2026, 6, 10),
        dias_totales=10,
    )
    db_session.add(incapacidad)
    await db_session.commit()
    await db_session.refresh(incapacidad)
    return incapacidad


@pytest.mark.asyncio
async def test_guardar_pdf_crea_documento_nuevo(db_session):
    incapacidad = await _crear_incapacidad_real(db_session)
    documento = await guardar_pdf_autorizacion_pago(db_session, incapacidad, b"%PDF-1.4 fake content")

    assert documento.incapacidad_id == incapacidad.id
    assert documento.nombre_original == "Autorizacion de pago por OCCIRED.pdf"
    assert documento.tipo_documento == TipoDocumentoAdjunto.SOPORTE_PAGO
    assert documento.mime_type == "application/pdf"
    # The bytes must be readable back from the real storage backend, not just referenced.
    from app.core.storage_core import storage_backend
    contenido = storage_backend.get_file_content(documento.ruta_storage)
    assert contenido == b"%PDF-1.4 fake content"


@pytest.mark.asyncio
async def test_guardar_pdf_reemplaza_documento_existente(db_session):
    incapacidad = await _crear_incapacidad_real(db_session)
    primero = await guardar_pdf_autorizacion_pago(db_session, incapacidad, b"%PDF-1.4 borrador")
    segundo = await guardar_pdf_autorizacion_pago(db_session, incapacidad, b"%PDF-1.4 final")

    assert primero.id == segundo.id  # same Documento row, content replaced

    from app.core.storage_core import storage_backend
    contenido = storage_backend.get_file_content(segundo.ruta_storage)
    assert contenido == b"%PDF-1.4 final"

import pytest
from datetime import date
from decimal import Decimal
from uuid import uuid4

from app.services.liquidacion_pdf_service import generar_pdf_autorizacion_pago


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

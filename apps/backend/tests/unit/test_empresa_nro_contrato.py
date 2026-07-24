from app.schemas.empresa import EmpresaUpdate


def test_empresa_update_accepts_nro_contrato():
    data = EmpresaUpdate(nro_contrato="CTR-2026-0001")
    assert data.nro_contrato == "CTR-2026-0001"

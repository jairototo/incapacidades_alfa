from app.utils.enums import SucursalSiniestro


def test_sucursal_siniestro_values():
    assert SucursalSiniestro.CALI == "Cali"
    assert SucursalSiniestro.MEDELLIN == "Medellín"
    assert SucursalSiniestro.CARTAGENA == "Cartagena"
    assert SucursalSiniestro.BOGOTA == "Bogotá"

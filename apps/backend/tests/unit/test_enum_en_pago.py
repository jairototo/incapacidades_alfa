from app.utils.enums import EstadoIncapacidad


def test_en_pago_states_exist():
    assert EstadoIncapacidad.EN_PAGO == "EN_PAGO"
    assert EstadoIncapacidad.EN_PAGO_PARCIAL == "EN_PAGO_PARCIAL"

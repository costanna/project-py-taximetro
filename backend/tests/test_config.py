from config import TARIFA_MOVIMIENTO_DEFECTO, TARIFA_PARADO_DEFECTO, cargar_tarifas


def test_sin_variables_de_entorno_usa_valores_por_defecto(monkeypatch):
    monkeypatch.delenv("TARIFA_PARADO", raising=False)
    monkeypatch.delenv("TARIFA_MOVIMIENTO", raising=False)
    tarifas = cargar_tarifas()
    assert tarifas == {
        "tarifa_parado": TARIFA_PARADO_DEFECTO,
        "tarifa_movimiento": TARIFA_MOVIMIENTO_DEFECTO,
    }


def test_variables_de_entorno_validas_se_respetan(monkeypatch):
    monkeypatch.setenv("TARIFA_PARADO", "0.03")
    monkeypatch.setenv("TARIFA_MOVIMIENTO", "0.07")
    tarifas = cargar_tarifas()
    assert tarifas == {"tarifa_parado": 0.03, "tarifa_movimiento": 0.07}


def test_variable_no_numerica_cae_a_valor_por_defecto(monkeypatch):
    monkeypatch.setenv("TARIFA_PARADO", "no-es-un-numero")
    tarifas = cargar_tarifas()
    assert tarifas["tarifa_parado"] == TARIFA_PARADO_DEFECTO


def test_variable_negativa_cae_a_valor_por_defecto(monkeypatch):
    monkeypatch.setenv("TARIFA_MOVIMIENTO", "-1")
    tarifas = cargar_tarifas()
    assert tarifas["tarifa_movimiento"] == TARIFA_MOVIMIENTO_DEFECTO

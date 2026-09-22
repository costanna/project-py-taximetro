import json

from config import TARIFA_MOVIMIENTO_DEFECTO, TARIFA_PARADO_DEFECTO, cargar_tarifas


def test_config_ausente_devuelve_valores_por_defecto(tmp_path):
    tarifas = cargar_tarifas(tmp_path / "no_existe.json")
    assert tarifas == {
        "tarifa_parado": TARIFA_PARADO_DEFECTO,
        "tarifa_movimiento": TARIFA_MOVIMIENTO_DEFECTO,
    }


def test_config_valida_se_respeta(tmp_path):
    ruta = tmp_path / "tarifas.json"
    ruta.write_text(json.dumps({"tarifa_parado": 0.03, "tarifa_movimiento": 0.07}))
    tarifas = cargar_tarifas(ruta)
    assert tarifas == {"tarifa_parado": 0.03, "tarifa_movimiento": 0.07}


def test_config_con_json_corrupto_cae_a_valores_por_defecto(tmp_path):
    ruta = tmp_path / "tarifas.json"
    ruta.write_text("{ esto no es json")
    tarifas = cargar_tarifas(ruta)
    assert tarifas["tarifa_parado"] == TARIFA_PARADO_DEFECTO


def test_config_con_clave_faltante_cae_a_valores_por_defecto(tmp_path):
    ruta = tmp_path / "tarifas.json"
    ruta.write_text(json.dumps({"tarifa_parado": 0.03}))
    tarifas = cargar_tarifas(ruta)
    assert tarifas["tarifa_movimiento"] == TARIFA_MOVIMIENTO_DEFECTO


def test_config_con_tarifa_negativa_cae_a_valores_por_defecto(tmp_path):
    ruta = tmp_path / "tarifas.json"
    ruta.write_text(json.dumps({"tarifa_parado": -1, "tarifa_movimiento": 0.05}))
    tarifas = cargar_tarifas(ruta)
    assert tarifas["tarifa_parado"] == TARIFA_PARADO_DEFECTO

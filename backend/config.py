import os

TARIFA_PARADO_DEFECTO = 0.02
TARIFA_MOVIMIENTO_DEFECTO = 0.05


def _leer_tarifa(nombre_env, defecto):
    valor = os.environ.get(nombre_env)
    if valor is None:
        return defecto
    try:
        tarifa = float(valor)
    except ValueError:
        return defecto
    return tarifa if tarifa > 0 else defecto


def cargar_tarifas():
    return {
        "tarifa_parado": _leer_tarifa("TARIFA_PARADO", TARIFA_PARADO_DEFECTO),
        "tarifa_movimiento": _leer_tarifa("TARIFA_MOVIMIENTO", TARIFA_MOVIMIENTO_DEFECTO),
    }

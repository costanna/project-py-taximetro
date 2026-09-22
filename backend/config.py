import json
from pathlib import Path

from logger import get_logger

logger = get_logger(__name__)

TARIFA_PARADO_DEFECTO = 0.02
TARIFA_MOVIMIENTO_DEFECTO = 0.05

RUTA_CONFIG_DEFECTO = Path(__file__).resolve().parent / "tarifas.json"


def cargar_tarifas(ruta_config=RUTA_CONFIG_DEFECTO):
    tarifas_defecto = {
        "tarifa_parado": TARIFA_PARADO_DEFECTO,
        "tarifa_movimiento": TARIFA_MOVIMIENTO_DEFECTO,
    }

    ruta_config = Path(ruta_config)
    if not ruta_config.exists():
        logger.warning("No existe %s; se usan las tarifas por defecto.", ruta_config)
        return tarifas_defecto

    try:
        contenido = json.loads(ruta_config.read_text(encoding="utf-8"))
        tarifa_parado = float(contenido["tarifa_parado"])
        tarifa_movimiento = float(contenido["tarifa_movimiento"])
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        logger.error(
            "Configuración inválida en %s (%s); se usan las tarifas por defecto.", ruta_config, exc
        )
        return tarifas_defecto

    if tarifa_parado <= 0 or tarifa_movimiento <= 0:
        logger.error("Tarifas no positivas en %s; se usan las tarifas por defecto.", ruta_config)
        return tarifas_defecto

    logger.info(
        "Tarifas cargadas desde %s: parado=%.3f movimiento=%.3f",
        ruta_config,
        tarifa_parado,
        tarifa_movimiento,
    )
    return {"tarifa_parado": tarifa_parado, "tarifa_movimiento": tarifa_movimiento}

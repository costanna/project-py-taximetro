import logging
from pathlib import Path

DIRECTORIO_LOGS = Path(__file__).resolve().parent.parent / "logs"
RUTA_LOG = DIRECTORIO_LOGS / "taximetro.log"

_FORMATO = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"

_configurado = False


def _configurar_una_vez():
    global _configurado
    if _configurado:
        return
    DIRECTORIO_LOGS.mkdir(parents=True, exist_ok=True)

    formateador = logging.Formatter(_FORMATO)

    manejador_fichero = logging.FileHandler(RUTA_LOG, encoding="utf-8")
    manejador_fichero.setFormatter(formateador)

    manejador_consola = logging.StreamHandler()
    manejador_consola.setFormatter(formateador)

    raiz = logging.getLogger("taximetro")
    raiz.setLevel(logging.INFO)
    raiz.addHandler(manejador_fichero)
    raiz.addHandler(manejador_consola)
    raiz.propagate = False

    _configurado = True


def get_logger(nombre):
    _configurar_una_vez()
    return logging.getLogger(nombre)

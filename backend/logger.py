import logging
import sys

_FORMATO = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"

_configurado = False


def _configurar_una_vez():
    global _configurado
    if _configurado:
        return
    manejador = logging.StreamHandler(sys.stdout)
    manejador.setFormatter(logging.Formatter(_FORMATO))

    raiz = logging.getLogger("taximetro_backend")
    raiz.setLevel(logging.INFO)
    raiz.addHandler(manejador)
    raiz.propagate = False

    _configurado = True


def get_logger(nombre):
    _configurar_una_vez()
    return logging.getLogger(nombre)

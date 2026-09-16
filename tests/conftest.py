import pytest


class RelojFalso:
    def __init__(self, inicio=1_000_000.0):
        self._ahora = inicio

    def __call__(self):
        return self._ahora

    def avanzar(self, segundos):
        self._ahora += segundos


@pytest.fixture
def reloj_falso():
    return RelojFalso()

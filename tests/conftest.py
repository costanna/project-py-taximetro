import pytest

from taximetro.api import create_app


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


@pytest.fixture
def app(tmp_path):
    aplicacion = create_app(
        ruta_bd=tmp_path / "taximetro.db",
        ruta_usuarios=tmp_path / "usuarios.json",
        ruta_config=tmp_path / "config_inexistente.json",
    )
    aplicacion.config.update(TESTING=True)
    return aplicacion


@pytest.fixture
def cliente(app):
    return app.test_client()

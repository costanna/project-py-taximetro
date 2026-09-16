import socket
import threading
import time

import pytest
import requests
from werkzeug.serving import make_server

from taximetro.api import create_app


def _puerto_libre():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class ServidorDePruebas(threading.Thread):
    def __init__(self, app, puerto):
        super().__init__(daemon=True)
        self._servidor = make_server("127.0.0.1", puerto, app)

    def run(self):
        self._servidor.serve_forever()

    def detener(self):
        self._servidor.shutdown()


@pytest.fixture
def servidor_en_marcha(tmp_path):
    app = create_app(
        ruta_bd=tmp_path / "e2e.db",
        ruta_usuarios=tmp_path / "e2e_usuarios.json",
        ruta_config=tmp_path / "no_existe.json",
    )
    puerto = _puerto_libre()
    servidor = ServidorDePruebas(app, puerto)
    servidor.start()

    base_url = f"http://127.0.0.1:{puerto}"
    for _ in range(50):
        try:
            requests.get(base_url, timeout=0.2)
            break
        except requests.exceptions.ConnectionError:
            time.sleep(0.05)

    yield base_url
    servidor.detener()
    servidor.join(timeout=5)


def test_viaje_completo_de_un_turno_de_taxi(servidor_en_marcha):
    base_url = servidor_en_marcha

    pagina = requests.get(base_url)
    assert pagina.status_code == 200
    assert "Taxímetro" in pagina.text

    requests.post(
        f"{base_url}/api/auth/registro", json={"username": "flota", "password": "clave-flota-2025"}
    )
    login = requests.post(
        f"{base_url}/api/auth/login", json={"username": "flota", "password": "clave-flota-2025"}
    )
    assert login.status_code == 200
    token = login.json()["token"]
    auth = {"Authorization": f"Bearer {token}"}

    inicio = requests.post(f"{base_url}/api/carreras/iniciar", headers=auth)
    assert inicio.json()["estado"] == "parado"

    cambio = requests.post(
        f"{base_url}/api/carreras/estado", headers=auth, json={"estado": "movimiento"}
    )
    assert cambio.json()["estado"] == "movimiento"

    actual = requests.get(f"{base_url}/api/carreras/actual", headers=auth)
    assert actual.json()["en_curso"] is True

    fin = requests.post(f"{base_url}/api/carreras/finalizar", headers=auth)
    assert fin.status_code == 200
    assert fin.json()["importe_total"] >= 0

    requests.post(f"{base_url}/api/carreras/iniciar", headers=auth)
    requests.post(f"{base_url}/api/carreras/finalizar", headers=auth)

    historial = requests.get(f"{base_url}/api/carreras/historial", headers=auth)
    assert historial.status_code == 200
    assert len(historial.json()["carreras"]) == 2

    sin_token = requests.get(f"{base_url}/api/carreras/historial")
    assert sin_token.status_code == 401

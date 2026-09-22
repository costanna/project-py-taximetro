import json

import pytest

from taximetro.auth import CredencialesInvalidasError, GestorUsuarios, TokenInvalidoError


@pytest.fixture
def gestor(tmp_path):
    return GestorUsuarios(tmp_path / "usuarios.json", clave_secreta="clave-de-test")


def test_password_nunca_se_guarda_en_texto_plano(gestor, tmp_path):
    gestor.crear_usuario("taxista1", "supersecreta")
    contenido = json.loads((tmp_path / "usuarios.json").read_text())
    hash_guardado = contenido["taxista1"]["password_hash"]
    assert hash_guardado != "supersecreta"
    assert "supersecreta" not in hash_guardado


def test_existe_usuario_distingue_por_username(gestor):
    gestor.crear_usuario("taxista1", "supersecreta")
    assert gestor.existe_usuario("taxista1") is True
    assert gestor.existe_usuario("taxista2") is False


def test_primer_usuario_creado_es_responsable(gestor):
    rol = gestor.crear_usuario("taxista1", "supersecreta")
    assert rol == "responsable"


def test_segundo_usuario_creado_es_taxista(gestor):
    gestor.crear_usuario("taxista1", "supersecreta")
    rol = gestor.crear_usuario("taxista2", "otra-clave-1234")
    assert rol == "taxista"


def test_verificar_credenciales_correctas_devuelve_el_rol(gestor):
    gestor.crear_usuario("taxista1", "supersecreta")
    assert gestor.verificar_credenciales("taxista1", "supersecreta") == "responsable"


def test_verificar_password_incorrecta_lanza(gestor):
    gestor.crear_usuario("taxista1", "supersecreta")
    with pytest.raises(CredencialesInvalidasError):
        gestor.verificar_credenciales("taxista1", "otra-cosa")


def test_verificar_usuario_inexistente_lanza(gestor):
    with pytest.raises(CredencialesInvalidasError):
        gestor.verificar_credenciales("fantasma", "lo-que-sea")


def test_token_emitido_se_puede_validar(gestor):
    gestor.crear_usuario("taxista1", "supersecreta")
    token = gestor.emitir_token("taxista1", "taxista")
    assert gestor.datos_del_token(token) == {"username": "taxista1", "rol": "taxista"}


def test_token_manipulado_es_invalido(gestor):
    gestor.crear_usuario("taxista1", "supersecreta")
    token = gestor.emitir_token("taxista1", "taxista")
    mitad = len(token) // 2
    token_manipulado = token[:mitad] + ("a" if token[mitad] != "a" else "b") + token[mitad + 1 :]
    with pytest.raises(TokenInvalidoError):
        gestor.datos_del_token(token_manipulado)


def test_token_de_otro_gestor_con_otra_clave_es_invalido(gestor, tmp_path):
    gestor.crear_usuario("taxista1", "supersecreta")
    token = gestor.emitir_token("taxista1", "taxista")

    otro_gestor = GestorUsuarios(tmp_path / "usuarios.json", clave_secreta="otra-clave")
    with pytest.raises(TokenInvalidoError):
        otro_gestor.datos_del_token(token)

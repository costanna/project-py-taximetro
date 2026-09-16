import json

import pytest

from taximetro.auth import CredencialesInvalidasError, GestorUsuarios, TokenInvalidoError


@pytest.fixture
def gestor(tmp_path):
    return GestorUsuarios(tmp_path / "usuarios.json", clave_secreta="clave-de-test")


def test_password_nunca_se_guarda_en_texto_plano(gestor, tmp_path):
    gestor.crear_usuario("taxista1", "supersecreta")
    contenido = json.loads((tmp_path / "usuarios.json").read_text())
    assert contenido["taxista1"] != "supersecreta"
    assert "supersecreta" not in contenido["taxista1"]


def test_verificar_credenciales_correctas_no_lanza(gestor):
    gestor.crear_usuario("taxista1", "supersecreta")
    gestor.verificar_credenciales("taxista1", "supersecreta")


def test_verificar_password_incorrecta_lanza(gestor):
    gestor.crear_usuario("taxista1", "supersecreta")
    with pytest.raises(CredencialesInvalidasError):
        gestor.verificar_credenciales("taxista1", "otra-cosa")


def test_verificar_usuario_inexistente_lanza(gestor):
    with pytest.raises(CredencialesInvalidasError):
        gestor.verificar_credenciales("fantasma", "lo-que-sea")


def test_token_emitido_se_puede_validar(gestor):
    gestor.crear_usuario("taxista1", "supersecreta")
    token = gestor.emitir_token("taxista1")
    assert gestor.usuario_del_token(token) == "taxista1"


def test_token_manipulado_es_invalido(gestor):
    gestor.crear_usuario("taxista1", "supersecreta")
    token = gestor.emitir_token("taxista1")
    token_manipulado = token[:-1] + ("a" if token[-1] != "a" else "b")
    with pytest.raises(TokenInvalidoError):
        gestor.usuario_del_token(token_manipulado)


def test_token_de_otro_gestor_con_otra_clave_es_invalido(gestor, tmp_path):
    gestor.crear_usuario("taxista1", "supersecreta")
    token = gestor.emitir_token("taxista1")

    otro_gestor = GestorUsuarios(tmp_path / "usuarios.json", clave_secreta="otra-clave")
    with pytest.raises(TokenInvalidoError):
        otro_gestor.usuario_del_token(token)

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import auth
import database


@pytest.fixture
def db(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'auth_test.db'}")
    database.Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    sesion = SessionLocal()
    try:
        yield sesion
    finally:
        sesion.close()


def test_existe_usuario_distingue_por_username(db):
    auth.crear_usuario(db, "taxista1", "supersecreta")
    assert auth.existe_usuario(db, "taxista1") is True
    assert auth.existe_usuario(db, "taxista2") is False


def test_password_nunca_se_guarda_en_texto_plano(db):
    usuario = auth.crear_usuario(db, "taxista1", "supersecreta")
    assert usuario.password_hash != "supersecreta"
    assert "supersecreta" not in usuario.password_hash


def test_verificar_credenciales_correctas_no_lanza(db):
    auth.crear_usuario(db, "taxista1", "supersecreta")
    auth.verificar_credenciales(db, "taxista1", "supersecreta")


def test_verificar_password_incorrecta_lanza(db):
    auth.crear_usuario(db, "taxista1", "supersecreta")
    with pytest.raises(auth.CredencialesInvalidasError):
        auth.verificar_credenciales(db, "taxista1", "otra-cosa")


def test_verificar_usuario_inexistente_lanza(db):
    with pytest.raises(auth.CredencialesInvalidasError):
        auth.verificar_credenciales(db, "fantasma", "lo-que-sea")


def test_token_emitido_se_puede_validar(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "clave-de-test")
    token = auth.emitir_token("taxista1")
    assert auth.usuario_del_token(token) == "taxista1"


def test_token_manipulado_es_invalido(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "clave-de-test")
    token = auth.emitir_token("taxista1")
    token_manipulado = token[:-1] + ("a" if token[-1] != "a" else "b")
    with pytest.raises(auth.TokenInvalidoError):
        auth.usuario_del_token(token_manipulado)


def test_token_con_otra_clave_secreta_es_invalido(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "clave-a")
    token = auth.emitir_token("taxista1")
    monkeypatch.setenv("SECRET_KEY", "clave-b")
    with pytest.raises(auth.TokenInvalidoError):
        auth.usuario_del_token(token)

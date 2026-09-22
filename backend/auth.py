import os
import secrets

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from sqlalchemy.orm import Session
from werkzeug.security import check_password_hash, generate_password_hash

from logger import get_logger
from models import Usuario

logger = get_logger(__name__)

DURACION_TOKEN_SEGUNDOS = 8 * 60 * 60
_CLAVE_SECRETA_PROCESO = secrets.token_hex(32)


class CredencialesInvalidasError(Exception):
    pass


class TokenInvalidoError(Exception):
    pass


def _clave_secreta():
    clave = os.environ.get("SECRET_KEY")
    if not clave:
        logger.warning(
            "SECRET_KEY no configurada: se usa una clave aleatoria por proceso. "
            "Los tokens dejaran de ser validos en cada reinicio/redeploy y no se "
            "compartiran entre instancias. Fijala en las variables de entorno de Render."
        )
        return _CLAVE_SECRETA_PROCESO
    return clave


def _serializador():
    return URLSafeTimedSerializer(_clave_secreta())


def existe_usuario(db: Session, username: str) -> bool:
    return db.query(Usuario).filter(Usuario.username == username).first() is not None


def crear_usuario(db: Session, username: str, password: str) -> Usuario:
    usuario = Usuario(username=username, password_hash=generate_password_hash(password))
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    logger.info("Usuario creado: %s", username)
    return usuario


def verificar_credenciales(db: Session, username: str, password: str) -> Usuario:
    usuario = db.query(Usuario).filter(Usuario.username == username).first()
    if usuario is None or not check_password_hash(usuario.password_hash, password):
        logger.warning("Intento de login fallido para usuario=%s", username)
        raise CredencialesInvalidasError("Usuario o contraseña incorrectos.")
    logger.info("Login correcto: %s", username)
    return usuario


def emitir_token(username: str) -> str:
    return _serializador().dumps({"username": username})


def usuario_del_token(token: str) -> str:
    try:
        datos = _serializador().loads(token, max_age=DURACION_TOKEN_SEGUNDOS)
    except SignatureExpired as exc:
        raise TokenInvalidoError("El token ha caducado, vuelve a iniciar sesión.") from exc
    except BadSignature as exc:
        raise TokenInvalidoError("Token inválido.") from exc
    return datos["username"]

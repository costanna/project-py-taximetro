from functools import wraps
from pathlib import Path

from flask import Flask, current_app, g, jsonify, request, send_from_directory

from taximetro.auth import CredencialesInvalidasError, GestorUsuarios, TokenInvalidoError
from taximetro.config import cargar_tarifas
from taximetro.core import ESTADOS_VALIDOS, CarreraNoIniciadaError, Taximetro
from taximetro.logger import get_logger
from taximetro.storage import AlmacenCarreras

logger = get_logger(__name__)

RUTA_WEB = Path(__file__).resolve().parent.parent / "web"


def requiere_token(vista):
    @wraps(vista)
    def envoltura(*args, **kwargs):
        cabecera = request.headers.get("Authorization", "")
        if not cabecera.startswith("Bearer "):
            return jsonify(error="Falta el token de autenticación."), 401
        token = cabecera.removeprefix("Bearer ").strip()
        gestor_usuarios = current_app.config["gestor_usuarios"]
        try:
            datos = gestor_usuarios.datos_del_token(token)
        except TokenInvalidoError as exc:
            return jsonify(error=str(exc)), 401
        g.username = datos["username"]
        g.rol = datos["rol"]
        return vista(*args, **kwargs)

    return envoltura


def create_app(ruta_bd=None, ruta_usuarios=None, ruta_config=None, servir_web=True):
    app = Flask(__name__)

    tarifas = cargar_tarifas(ruta_config) if ruta_config else cargar_tarifas()
    taximetro = Taximetro(**tarifas)
    almacen = AlmacenCarreras(ruta_bd) if ruta_bd else AlmacenCarreras()
    gestor_usuarios = GestorUsuarios(ruta_usuarios) if ruta_usuarios else GestorUsuarios()

    app.config["taximetro"] = taximetro
    app.config["almacen"] = almacen
    app.config["gestor_usuarios"] = gestor_usuarios

    @app.post("/api/auth/registro")
    def registro():
        datos = request.get_json(silent=True) or {}
        username, password = datos.get("username"), datos.get("password")
        if not username or not password:
            return jsonify(error="username y password son obligatorios."), 400
        if gestor_usuarios.existe_usuario(username):
            return jsonify(error="Ese usuario ya existe."), 409
        gestor_usuarios.crear_usuario(username, password)
        return jsonify(mensaje="Usuario creado."), 201

    @app.post("/api/auth/login")
    def login():
        datos = request.get_json(silent=True) or {}
        username, password = datos.get("username"), datos.get("password")
        try:
            rol = gestor_usuarios.verificar_credenciales(username, password)
        except CredencialesInvalidasError as exc:
            return jsonify(error=str(exc)), 401
        token = gestor_usuarios.emitir_token(username, rol)
        return jsonify(token=token)

    def _estado_json():
        return jsonify(
            en_curso=taximetro.en_curso,
            estado=taximetro.estado,
            importe_actual=round(taximetro.importe_actual(), 2),
            duracion_actual=round(taximetro.duracion_actual(), 1),
        )

    @app.post("/api/carreras/iniciar")
    @requiere_token
    def iniciar():
        taximetro.iniciar_carrera()
        logger.info("[%s] Carrera iniciada vía API.", g.username)
        return _estado_json()

    @app.post("/api/carreras/estado")
    @requiere_token
    def cambiar_estado():
        datos = request.get_json(silent=True) or {}
        nuevo_estado = datos.get("estado")
        if nuevo_estado not in ESTADOS_VALIDOS:
            return jsonify(error=f"Estado inválido. Usa uno de: {sorted(ESTADOS_VALIDOS)}"), 400
        try:
            cambiado = taximetro.cambiar_estado(nuevo_estado)
        except CarreraNoIniciadaError as exc:
            return jsonify(error=str(exc)), 409
        if cambiado:
            logger.info("[%s] Estado -> %s", g.username, nuevo_estado)
        return _estado_json()

    @app.get("/api/carreras/actual")
    @requiere_token
    def actual():
        return _estado_json()

    @app.post("/api/carreras/finalizar")
    @requiere_token
    def finalizar():
        try:
            resumen = taximetro.finalizar_carrera()
        except CarreraNoIniciadaError as exc:
            return jsonify(error=str(exc)), 409
        id_carrera = almacen.guardar_carrera(resumen, usuario=g.username)
        logger.info(
            "[%s] Carrera #%s finalizada: %.2f €", g.username, id_carrera, resumen["importe_total"]
        )
        return jsonify(id=id_carrera, **resumen)

    @app.get("/api/carreras/historial")
    @requiere_token
    def historial():
        limite = request.args.get("limite", type=int)
        usuario_filtro = None if g.rol == "responsable" else g.username
        return jsonify(
            carreras=almacen.historial(usuario=usuario_filtro, limite=limite),
            total_recaudado_hoy=round(almacen.total_recaudado_hoy(usuario=usuario_filtro), 2),
        )

    if servir_web and RUTA_WEB.exists():

        @app.get("/")
        def index():
            return send_from_directory(RUTA_WEB, "index.html")

        @app.get("/<path:nombre_fichero>")
        def estaticos(nombre_fichero):
            return send_from_directory(RUTA_WEB, nombre_fichero)

    return app


if __name__ == "__main__":
    create_app().run(debug=True, host="0.0.0.0", port=5000)

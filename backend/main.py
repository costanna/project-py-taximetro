import datetime
import os
from dataclasses import dataclass

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

import auth
from config import cargar_tarifas
from database import Base, engine, get_db
from logger import get_logger
from models import Carrera
from schemas import CambioEstado, CarreraOut, LoginUsuario, RegistroUsuario, TokenOut

logger = get_logger(__name__)

TARIFAS = cargar_tarifas()

app = FastAPI(title="TaxiTech Solutions — Taxímetro API")

allowed_origins = [
    origin.strip() for origin in os.environ.get("ALLOWED_ORIGINS", "*").split(",") if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@dataclass
class Identidad:
    username: str
    rol: str


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    logger.info(
        "Taximetro API arrancada. Tarifas: parado=%.3f movimiento=%.3f",
        TARIFAS["tarifa_parado"],
        TARIFAS["tarifa_movimiento"],
    )


def _tarifa(estado: str) -> float:
    return TARIFAS["tarifa_parado"] if estado == "parado" else TARIFAS["tarifa_movimiento"]


def _acumular_hasta_ahora(carrera: Carrera) -> None:
    ahora = datetime.datetime.utcnow()
    segundos_transcurridos = (ahora - carrera.ultimo_cambio).total_seconds()
    carrera.importe_acumulado += segundos_transcurridos * _tarifa(carrera.estado)
    carrera.ultimo_cambio = ahora


def _con_importe_en_vivo(carrera: Carrera) -> Carrera:
    if carrera.en_curso:
        ahora = datetime.datetime.utcnow()
        segundos_transcurridos = (ahora - carrera.ultimo_cambio).total_seconds()
        carrera.importe_en_vivo = round(
            carrera.importe_acumulado + segundos_transcurridos * _tarifa(carrera.estado), 2
        )
    else:
        carrera.importe_en_vivo = round(carrera.importe_acumulado, 2)
    return carrera


def _obtener_carrera_propia(carrera_id: int, db: Session, identidad: Identidad) -> Carrera:
    carrera = db.get(Carrera, carrera_id)
    es_ajena = carrera is not None and carrera.usuario != identidad.username
    if carrera is None or (es_ajena and identidad.rol != "responsable"):
        raise HTTPException(status_code=404, detail="Carrera no encontrada")
    return carrera


def _obtener_carrera_activa(carrera_id: int, db: Session, identidad: Identidad) -> Carrera:
    carrera = _obtener_carrera_propia(carrera_id, db, identidad)
    if not carrera.en_curso:
        raise HTTPException(status_code=409, detail="La carrera ya ha finalizado")
    return carrera


def requiere_token(authorization: str = Header(default="")) -> Identidad:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Falta el token de autenticación.")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        datos = auth.datos_del_token(token)
    except auth.TokenInvalidoError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    return Identidad(username=datos["username"], rol=datos["rol"])


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/auth/registro", status_code=201)
def registro(datos: RegistroUsuario, db: Session = Depends(get_db)):
    if auth.existe_usuario(db, datos.username):
        raise HTTPException(status_code=409, detail="Ese usuario ya existe.")
    auth.crear_usuario(db, datos.username, datos.password)
    return {"mensaje": "Usuario creado."}


@app.post("/auth/login", response_model=TokenOut)
def login(datos: LoginUsuario, db: Session = Depends(get_db)):
    try:
        usuario_db = auth.verificar_credenciales(db, datos.username, datos.password)
    except auth.CredencialesInvalidasError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    return {"token": auth.emitir_token(usuario_db.username, usuario_db.rol)}


@app.post("/carreras", response_model=CarreraOut, status_code=201)
def iniciar_carrera(db: Session = Depends(get_db), identidad: Identidad = Depends(requiere_token)):
    ahora = datetime.datetime.utcnow()
    carrera = Carrera(
        usuario=identidad.username,
        estado="parado",
        importe_acumulado=0.0,
        en_curso=True,
        inicio=ahora,
        ultimo_cambio=ahora,
    )
    db.add(carrera)
    db.commit()
    db.refresh(carrera)
    logger.info("[%s] Carrera #%s iniciada.", identidad.username, carrera.id)
    return _con_importe_en_vivo(carrera)


@app.patch("/carreras/{carrera_id}/estado", response_model=CarreraOut)
def cambiar_estado(
    carrera_id: int,
    cambio: CambioEstado,
    db: Session = Depends(get_db),
    identidad: Identidad = Depends(requiere_token),
):
    carrera = _obtener_carrera_activa(carrera_id, db, identidad)
    if cambio.estado != carrera.estado:
        _acumular_hasta_ahora(carrera)
        carrera.estado = cambio.estado
        db.commit()
        db.refresh(carrera)
        logger.info("[%s] Carrera #%s -> %s", identidad.username, carrera_id, cambio.estado)
    return _con_importe_en_vivo(carrera)


@app.post("/carreras/{carrera_id}/finalizar", response_model=CarreraOut)
def finalizar_carrera(
    carrera_id: int,
    db: Session = Depends(get_db),
    identidad: Identidad = Depends(requiere_token),
):
    carrera = _obtener_carrera_activa(carrera_id, db, identidad)
    _acumular_hasta_ahora(carrera)
    carrera.en_curso = False
    carrera.fin = datetime.datetime.utcnow()
    db.commit()
    db.refresh(carrera)
    logger.info(
        "[%s] Carrera #%s finalizada: %.2f €",
        identidad.username,
        carrera_id,
        carrera.importe_acumulado,
    )
    return _con_importe_en_vivo(carrera)


@app.get("/carreras", response_model=list[CarreraOut])
def listar_carreras(db: Session = Depends(get_db), identidad: Identidad = Depends(requiere_token)):
    consulta = db.query(Carrera)
    if identidad.rol != "responsable":
        consulta = consulta.filter(Carrera.usuario == identidad.username)
    carreras = consulta.order_by(Carrera.inicio.desc()).all()
    return [_con_importe_en_vivo(c) for c in carreras]


@app.get("/carreras/{carrera_id}", response_model=CarreraOut)
def obtener_carrera(
    carrera_id: int,
    db: Session = Depends(get_db),
    identidad: Identidad = Depends(requiere_token),
):
    carrera = _obtener_carrera_propia(carrera_id, db, identidad)
    return _con_importe_en_vivo(carrera)

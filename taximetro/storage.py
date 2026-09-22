import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from taximetro.logger import get_logger

logger = get_logger(__name__)

RUTA_BD_DEFECTO = Path(__file__).resolve().parent.parent / "data" / "taximetro.db"

_ESQUEMA = """
CREATE TABLE IF NOT EXISTS carreras (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario TEXT,
    fecha_inicio TEXT NOT NULL,
    fecha_fin TEXT NOT NULL,
    duracion_segundos REAL NOT NULL CHECK (duracion_segundos >= 0),
    importe_total REAL NOT NULL CHECK (importe_total >= 0)
);
"""


class AlmacenCarreras:
    def __init__(self, ruta_bd=RUTA_BD_DEFECTO):
        self.ruta_bd = Path(ruta_bd)
        self.ruta_bd.parent.mkdir(parents=True, exist_ok=True)
        self._inicializar_esquema()

    @contextmanager
    def _conexion(self):
        conexion = sqlite3.connect(self.ruta_bd)
        conexion.row_factory = sqlite3.Row
        try:
            yield conexion
            conexion.commit()
        finally:
            conexion.close()

    def _inicializar_esquema(self):
        with self._conexion() as conexion:
            conexion.execute(_ESQUEMA)
            columnas = {fila["name"] for fila in conexion.execute("PRAGMA table_info(carreras)")}
            if "usuario" not in columnas:
                conexion.execute("ALTER TABLE carreras ADD COLUMN usuario TEXT")

    def guardar_carrera(self, resumen, usuario=None):
        fecha_inicio = datetime.fromtimestamp(resumen["instante_inicio"], tz=timezone.utc)
        fecha_fin = datetime.fromtimestamp(resumen["instante_fin"], tz=timezone.utc)
        with self._conexion() as conexion:
            cursor = conexion.execute(
                "INSERT INTO carreras (usuario, fecha_inicio, fecha_fin, duracion_segundos, "
                "importe_total) VALUES (?, ?, ?, ?, ?)",
                (
                    usuario,
                    fecha_inicio.isoformat(),
                    fecha_fin.isoformat(),
                    resumen["duracion_segundos"],
                    resumen["importe_total"],
                ),
            )
            logger.info("Carrera #%s guardada: %.2f €", cursor.lastrowid, resumen["importe_total"])
            return cursor.lastrowid

    def historial(self, usuario=None, limite=None):
        consulta = "SELECT * FROM carreras"
        parametros = []
        if usuario is not None:
            consulta += " WHERE usuario = ?"
            parametros.append(usuario)
        consulta += " ORDER BY id DESC"
        if limite is not None:
            consulta += " LIMIT ?"
            parametros.append(limite)
        with self._conexion() as conexion:
            filas = conexion.execute(consulta, parametros).fetchall()
        return [dict(fila) for fila in filas]

    def total_recaudado_hoy(self, usuario=None):
        hoy = datetime.now(timezone.utc).date().isoformat()
        consulta = (
            "SELECT COALESCE(SUM(importe_total), 0) AS total FROM carreras "
            "WHERE substr(fecha_fin, 1, 10) = ?"
        )
        parametros = [hoy]
        if usuario is not None:
            consulta += " AND usuario = ?"
            parametros.append(usuario)
        with self._conexion() as conexion:
            fila = conexion.execute(consulta, parametros).fetchone()
        return fila["total"]

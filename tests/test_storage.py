import pytest

from taximetro.storage import AlmacenCarreras


@pytest.fixture
def almacen(tmp_path):
    return AlmacenCarreras(tmp_path / "carreras.db")


def resumen(instante_inicio, instante_fin, importe_total):
    return {
        "instante_inicio": instante_inicio,
        "instante_fin": instante_fin,
        "duracion_segundos": instante_fin - instante_inicio,
        "importe_total": importe_total,
    }


def test_historial_vacio_al_principio(almacen):
    assert almacen.historial() == []


def test_guardar_carrera_devuelve_id_incremental(almacen):
    id1 = almacen.guardar_carrera(resumen(1_000, 1_060, 3.0))
    id2 = almacen.guardar_carrera(resumen(1_100, 1_160, 2.5))
    assert id2 == id1 + 1


def test_historial_devuelve_mas_reciente_primero(almacen):
    almacen.guardar_carrera(resumen(1_000, 1_060, 3.0))
    almacen.guardar_carrera(resumen(1_100, 1_160, 2.5))
    historial = almacen.historial()
    assert [carrera["importe_total"] for carrera in historial] == [2.5, 3.0]


def test_historial_respeta_el_limite(almacen):
    for i in range(5):
        almacen.guardar_carrera(resumen(1_000 + i, 1_060 + i, 1.0))
    assert len(almacen.historial(limite=2)) == 2


def test_persistencia_sobrevive_a_reabrir_el_almacen(tmp_path):
    ruta = tmp_path / "carreras.db"
    AlmacenCarreras(ruta).guardar_carrera(resumen(1_000, 1_060, 3.0))

    almacen_reabierto = AlmacenCarreras(ruta)
    assert len(almacen_reabierto.historial()) == 1


def test_total_recaudado_hoy_suma_solo_carreras_de_hoy(almacen):
    import time

    ahora = time.time()
    almacen.guardar_carrera(resumen(ahora - 60, ahora, 4.5))
    almacen.guardar_carrera(resumen(ahora - 30, ahora - 10, 2.0))
    assert almacen.total_recaudado_hoy() == pytest.approx(6.5)

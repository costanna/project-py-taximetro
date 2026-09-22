def registrar_y_loguear(cliente, username="responsable", password="clave-segura-123"):
    cliente.post("/auth/registro", json={"username": username, "password": password})
    respuesta = cliente.post("/auth/login", json={"username": username, "password": password})
    return respuesta.json()["token"]


def cabeceras(token):
    return {"Authorization": f"Bearer {token}"}


def test_health_no_requiere_token(cliente):
    respuesta = cliente.get("/health")
    assert respuesta.status_code == 200


def test_endpoints_de_carrera_requieren_token(cliente):
    respuesta = cliente.post("/carreras")
    assert respuesta.status_code == 401


def test_registro_login_y_flujo_completo_de_carrera(cliente):
    token = registrar_y_loguear(cliente)

    respuesta = cliente.post("/carreras", headers=cabeceras(token))
    assert respuesta.status_code == 201
    carrera = respuesta.json()
    assert carrera["estado"] == "parado"

    respuesta = cliente.patch(
        f"/carreras/{carrera['id']}/estado", headers=cabeceras(token), json={"estado": "movimiento"}
    )
    assert respuesta.status_code == 200
    assert respuesta.json()["estado"] == "movimiento"

    respuesta = cliente.post(f"/carreras/{carrera['id']}/finalizar", headers=cabeceras(token))
    assert respuesta.status_code == 200
    assert respuesta.json()["en_curso"] is False


def test_historial_incluye_carreras_finalizadas(cliente):
    token = registrar_y_loguear(cliente)
    carrera = cliente.post("/carreras", headers=cabeceras(token)).json()
    cliente.post(f"/carreras/{carrera['id']}/finalizar", headers=cabeceras(token))

    respuesta = cliente.get("/carreras", headers=cabeceras(token))
    assert respuesta.status_code == 200
    assert len(respuesta.json()) == 1


def test_no_se_puede_registrar_el_mismo_username_dos_veces(cliente):
    registrar_y_loguear(cliente)
    respuesta = cliente.post(
        "/auth/registro", json={"username": "responsable", "password": "otra-clave-123"}
    )
    assert respuesta.status_code == 409


def test_se_pueden_registrar_varios_usuarios_distintos(cliente):
    registrar_y_loguear(cliente)
    respuesta = cliente.post(
        "/auth/registro", json={"username": "otro", "password": "otra-clave-123"}
    )
    assert respuesta.status_code == 201


def test_login_con_password_incorrecta_devuelve_401(cliente):
    registrar_y_loguear(cliente)
    respuesta = cliente.post("/auth/login", json={"username": "responsable", "password": "mal"})
    assert respuesta.status_code == 401


def test_cambiar_estado_de_carrera_finalizada_devuelve_409(cliente):
    token = registrar_y_loguear(cliente)
    carrera = cliente.post("/carreras", headers=cabeceras(token)).json()
    cliente.post(f"/carreras/{carrera['id']}/finalizar", headers=cabeceras(token))

    respuesta = cliente.patch(
        f"/carreras/{carrera['id']}/estado", headers=cabeceras(token), json={"estado": "movimiento"}
    )
    assert respuesta.status_code == 409


def test_carrera_inexistente_devuelve_404(cliente):
    token = registrar_y_loguear(cliente)
    respuesta = cliente.get("/carreras/9999", headers=cabeceras(token))
    assert respuesta.status_code == 404


def test_token_invalido_es_rechazado(cliente):
    respuesta = cliente.get("/carreras", headers={"Authorization": "Bearer token-falso"})
    assert respuesta.status_code == 401

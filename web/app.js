(() => {
  "use strict";

  const $ = (id) => document.getElementById(id);

  const bannerConexion = $("banner-conexion");
  const pantallaLogin = $("pantalla-login");
  const pantallaTaximetro = $("pantalla-taximetro");
  const formLogin = $("form-login");
  const botonLogin = $("boton-login");
  const botonLoginTexto = botonLogin.querySelector(".boton__texto");
  const botonLoginSpinner = botonLogin.querySelector(".spinner");
  const errorLogin = $("error-login");
  const errorAccion = $("error-accion");
  const chipEstado = $("chip-estado");
  const botonLogout = $("boton-logout");
  const importeActual = $("importe-actual");
  const duracionActual = $("duracion-actual");
  const totalHoy = $("total-hoy");
  const listaHistorial = $("lista-historial");

  const botonIniciar = $("boton-iniciar");
  const botonParado = $("boton-parado");
  const botonMovimiento = $("boton-movimiento");
  const botonFinalizar = $("boton-finalizar");

  let token = null;
  let intervaloActualizacion = null;
  let fallosConsecutivos = 0;
  let errorAccionTimeout = null;
  let ultimoEstado = { en_curso: false, estado: null, importe_actual: 0, duracion_actual: 0 };

  const UMBRAL_FALLOS_PARA_AVISO = 3;

  class ErrorApi extends Error {
    constructor(mensaje, { status = null, esErrorRed = false } = {}) {
      super(mensaje);
      this.status = status;
      this.esErrorRed = esErrorRed;
    }
  }

  try {
    token = sessionStorage.getItem("taximetro_token");
  } catch {
    token = null;
  }

  function guardarToken(valor) {
    token = valor;
    try {
      sessionStorage.setItem("taximetro_token", valor);
    } catch {
    }
  }

  function limpiarToken() {
    token = null;
    try {
      sessionStorage.removeItem("taximetro_token");
    } catch {
    }
  }

  async function llamarApi(ruta, opciones = {}) {
    let respuesta;
    try {
      respuesta = await fetch(ruta, {
        ...opciones,
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
          ...(opciones.headers || {}),
        },
      });
    } catch {
      throw new ErrorApi("Sin conexión con el taxímetro.", { esErrorRed: true });
    }
    const cuerpo = await respuesta.json().catch(() => ({}));
    if (!respuesta.ok) {
      if (respuesta.status === 401) {
        limpiarToken();
        mostrarLogin();
      }
      throw new ErrorApi(cuerpo.error || `Error ${respuesta.status}`, { status: respuesta.status });
    }
    return cuerpo;
  }

  function formatearDuracion(segundos) {
    const total = Math.max(0, Math.round(segundos));
    const mm = Math.floor(total / 60).toString().padStart(2, "0");
    const ss = (total % 60).toString().padStart(2, "0");
    return `${mm}:${ss}`;
  }

  function pulsarImporte() {
    importeActual.classList.remove("actualizado");
    void importeActual.offsetWidth;
    importeActual.classList.add("actualizado");
  }

  function actualizarEstadoUI(estado) {
    const { en_curso: enCurso, estado: estadoTaxi, importe_actual: importe, duracion_actual: duracion = 0 } = estado;
    ultimoEstado = { en_curso: enCurso, estado: estadoTaxi, importe_actual: importe, duracion_actual: duracion };

    const nuevoValor = Number(importe).toFixed(2);
    if (importeActual.textContent !== nuevoValor) {
      importeActual.textContent = nuevoValor;
      pulsarImporte();
    }

    duracionActual.hidden = !enCurso;
    if (enCurso) duracionActual.textContent = formatearDuracion(duracion);

    botonIniciar.disabled = enCurso;
    botonParado.disabled = !enCurso || estadoTaxi === "parado";
    botonMovimiento.disabled = !enCurso || estadoTaxi === "movimiento";
    botonFinalizar.disabled = !enCurso;

    if (enCurso && estadoTaxi) {
      chipEstado.hidden = false;
      chipEstado.textContent = estadoTaxi.toUpperCase();
      chipEstado.className = `chip chip--${estadoTaxi}`;
    } else {
      chipEstado.hidden = true;
    }
  }

  function mostrarBannerConexion(mensaje) {
    bannerConexion.textContent = mensaje;
    bannerConexion.hidden = false;
  }

  function ocultarBannerConexion() {
    bannerConexion.hidden = true;
  }

  function mostrarErrorAccion(mensaje) {
    errorAccion.textContent = mensaje;
    errorAccion.hidden = false;
    clearTimeout(errorAccionTimeout);
    errorAccionTimeout = setTimeout(() => {
      errorAccion.hidden = true;
    }, 4000);
  }

  function mostrarLogin() {
    detenerActualizacionEnVivo();
    pantallaTaximetro.hidden = true;
    pantallaLogin.hidden = false;
    chipEstado.hidden = true;
    botonLogout.hidden = true;
    ocultarBannerConexion();
  }

  async function mostrarTaximetro() {
    pantallaLogin.hidden = true;
    pantallaTaximetro.hidden = false;
    botonLogout.hidden = false;
    await sincronizarEstadoActual();
    cargarHistorial();
  }

  async function sincronizarEstadoActual() {
    pantallaTaximetro.setAttribute("aria-busy", "true");
    try {
      const datos = await llamarApi("/api/carreras/actual");
      fallosConsecutivos = 0;
      ocultarBannerConexion();
      actualizarEstadoUI(datos);
      if (datos.en_curso) iniciarActualizacionEnVivo();
    } catch (error) {
      if (error.esErrorRed) mostrarBannerConexion("No se pudo conectar con el taxímetro.");
    } finally {
      pantallaTaximetro.removeAttribute("aria-busy");
    }
  }

  function iniciarActualizacionEnVivo() {
    detenerActualizacionEnVivo();
    intervaloActualizacion = setInterval(async () => {
      try {
        const datos = await llamarApi("/api/carreras/actual");
        fallosConsecutivos = 0;
        ocultarBannerConexion();
        actualizarEstadoUI(datos);
        if (!datos.en_curso) detenerActualizacionEnVivo();
      } catch (error) {
        if (error.esErrorRed) {
          fallosConsecutivos += 1;
          if (fallosConsecutivos >= UMBRAL_FALLOS_PARA_AVISO) {
            mostrarBannerConexion("Sin conexión con el taxímetro. Reintentando…");
          }
        } else if (error.status !== 401) {
          detenerActualizacionEnVivo();
        }
      }
    }, 1000);
  }

  function detenerActualizacionEnVivo() {
    if (intervaloActualizacion) {
      clearInterval(intervaloActualizacion);
      intervaloActualizacion = null;
    }
  }

  async function cargarHistorial() {
    try {
      const { carreras, total_recaudado_hoy: totalHoyValor } = await llamarApi(
        "/api/carreras/historial?limite=10"
      );
      totalHoy.textContent = Number(totalHoyValor).toFixed(2);
      listaHistorial.innerHTML = "";
      carreras.forEach((carrera) => {
        const item = document.createElement("li");
        const hora = new Date(carrera.fecha_fin).toLocaleTimeString("es-ES", {
          hour: "2-digit",
          minute: "2-digit",
        });
        item.innerHTML = `<span>${hora}</span><span>${carrera.importe_total.toFixed(2)} €</span>`;
        listaHistorial.appendChild(item);
      });
    } catch {
    }
  }

  async function manejarAccion(boton, accion) {
    boton.disabled = true;
    try {
      await accion();
    } catch (error) {
      mostrarErrorAccion(error.message || "No se ha podido completar la acción.");
      actualizarEstadoUI(ultimoEstado);
    }
  }

  formLogin.addEventListener("submit", async (evento) => {
    evento.preventDefault();
    errorLogin.hidden = true;
    botonLogin.disabled = true;
    botonLoginSpinner.hidden = false;
    botonLoginTexto.textContent = "Entrando…";
    try {
      const { token: nuevoToken } = await llamarApi("/api/auth/login", {
        method: "POST",
        body: JSON.stringify({
          username: $("input-usuario").value.trim(),
          password: $("input-password").value,
        }),
      });
      guardarToken(nuevoToken);
      await mostrarTaximetro();
    } catch (error) {
      errorLogin.textContent = error.message;
      errorLogin.hidden = false;
    } finally {
      botonLogin.disabled = false;
      botonLoginSpinner.hidden = true;
      botonLoginTexto.textContent = "Entrar";
    }
  });

  botonLogout.addEventListener("click", () => {
    limpiarToken();
    mostrarLogin();
  });

  botonIniciar.addEventListener("click", () =>
    manejarAccion(botonIniciar, async () => {
      const datos = await llamarApi("/api/carreras/iniciar", { method: "POST" });
      actualizarEstadoUI(datos);
      iniciarActualizacionEnVivo();
    })
  );

  botonParado.addEventListener("click", () =>
    manejarAccion(botonParado, async () => {
      const datos = await llamarApi("/api/carreras/estado", {
        method: "POST",
        body: JSON.stringify({ estado: "parado" }),
      });
      actualizarEstadoUI(datos);
    })
  );

  botonMovimiento.addEventListener("click", () =>
    manejarAccion(botonMovimiento, async () => {
      const datos = await llamarApi("/api/carreras/estado", {
        method: "POST",
        body: JSON.stringify({ estado: "movimiento" }),
      });
      actualizarEstadoUI(datos);
    })
  );

  botonFinalizar.addEventListener("click", () =>
    manejarAccion(botonFinalizar, async () => {
      await llamarApi("/api/carreras/finalizar", { method: "POST" });
      detenerActualizacionEnVivo();
      actualizarEstadoUI({ en_curso: false, estado: null, importe_actual: 0, duracion_actual: 0 });
      cargarHistorial();
    })
  );

  window.addEventListener("offline", () => mostrarBannerConexion("Sin conexión a internet."));
  window.addEventListener("online", () => {
    fallosConsecutivos = 0;
    if (token) sincronizarEstadoActual();
    else ocultarBannerConexion();
  });

  if (token) {
    mostrarTaximetro();
  } else {
    mostrarLogin();
  }
})();

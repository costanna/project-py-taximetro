const pantallaLogin = document.getElementById("pantalla-login");
const pantallaTaximetro = document.getElementById("pantalla-taximetro");
const formLogin = document.getElementById("form-login");
const formRegistro = document.getElementById("form-registro");
const btnMostrarRegistro = document.getElementById("btn-mostrar-registro");
const mensajeLoginEl = document.getElementById("mensaje-login");
const btnLogout = document.getElementById("btn-logout");

const estadoEl = document.getElementById("estado");
const importeEl = document.getElementById("importe");
const mensajeEl = document.getElementById("mensaje");
const historialBody = document.getElementById("historial-body");

const btnIniciar = document.getElementById("btn-iniciar");
const btnParado = document.getElementById("btn-parado");
const btnMovimiento = document.getElementById("btn-movimiento");
const btnFinalizar = document.getElementById("btn-finalizar");

document.querySelectorAll(".boton-ver-clave").forEach((boton) => {
  const input = document.getElementById(boton.dataset.input);
  if (!input) return;
  boton.addEventListener("click", () => {
    const mostrar = input.type === "password";
    input.type = mostrar ? "text" : "password";
    boton.setAttribute("aria-pressed", String(mostrar));
    boton.setAttribute("aria-label", mostrar ? "Ocultar contraseña" : "Mostrar contraseña");
    boton.title = mostrar ? "Ocultar contraseña" : "Mostrar contraseña";
    boton.querySelector(".icono-ver").hidden = mostrar;
    boton.querySelector(".icono-ocultar").hidden = !mostrar;
  });
});

let token = null;
let carreraId = null;
let intervalo = null;

try {
  token = sessionStorage.getItem("taximetro_token");
} catch {
  token = null;
}

function guardarToken(valor) {
  token = valor;
  try {
    sessionStorage.setItem("taximetro_token", valor);
  } catch {}
}

function limpiarToken() {
  token = null;
  try {
    sessionStorage.removeItem("taximetro_token");
  } catch {}
}

function mostrarMensaje(texto) {
  mensajeEl.textContent = texto || "";
}

function actualizarPanel(carrera) {
  estadoEl.textContent = carrera.en_curso ? carrera.estado.toUpperCase() : "FINALIZADA";
  estadoEl.className = "estado " + (carrera.en_curso ? carrera.estado : "inactivo");
  importeEl.textContent = `${carrera.importe_en_vivo.toFixed(2)} €`;
}

function activarControles(enCurso) {
  btnIniciar.disabled = enCurso;
  btnParado.disabled = !enCurso;
  btnMovimiento.disabled = !enCurso;
  btnFinalizar.disabled = !enCurso;
}

function mostrarLogin() {
  clearInterval(intervalo);
  carreraId = null;
  pantallaTaximetro.hidden = true;
  pantallaLogin.hidden = false;
}

function mostrarTaximetro() {
  pantallaLogin.hidden = true;
  pantallaTaximetro.hidden = false;
  cargarHistorial();
}

async function llamarApi(path, options = {}) {
  const respuesta = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {}),
    },
  });
  if (!respuesta.ok) {
    if (respuesta.status === 401) {
      limpiarToken();
      mostrarLogin();
    }
    const detalle = await respuesta.json().catch(() => ({}));
    throw new Error(detalle.detail || `Error ${respuesta.status}`);
  }
  return respuesta.json();
}

async function iniciarCarrera() {
  try {
    mostrarMensaje("");
    const carrera = await llamarApi("/carreras", { method: "POST" });
    carreraId = carrera.id;
    actualizarPanel(carrera);
    activarControles(true);
    intervalo = setInterval(refrescarCarreraActual, 1000);
    await cargarHistorial();
  } catch (error) {
    mostrarMensaje(`No se pudo iniciar la carrera: ${error.message}`);
  }
}

async function cambiarEstado(nuevoEstado) {
  if (!carreraId) return;
  try {
    const carrera = await llamarApi(`/carreras/${carreraId}/estado`, {
      method: "PATCH",
      body: JSON.stringify({ estado: nuevoEstado }),
    });
    actualizarPanel(carrera);
  } catch (error) {
    mostrarMensaje(`No se pudo cambiar de estado: ${error.message}`);
  }
}

async function finalizarCarrera() {
  if (!carreraId) return;
  try {
    const carrera = await llamarApi(`/carreras/${carreraId}/finalizar`, { method: "POST" });
    actualizarPanel(carrera);
    activarControles(false);
    clearInterval(intervalo);
    carreraId = null;
    await cargarHistorial();
  } catch (error) {
    mostrarMensaje(`No se pudo finalizar la carrera: ${error.message}`);
  }
}

async function refrescarCarreraActual() {
  if (!carreraId) return;
  try {
    const carrera = await llamarApi(`/carreras/${carreraId}`);
    actualizarPanel(carrera);
  } catch (error) {
    clearInterval(intervalo);
    mostrarMensaje(`Se perdió la conexión con la carrera: ${error.message}`);
  }
}

async function cargarHistorial() {
  try {
    const carreras = await llamarApi("/carreras");
    historialBody.innerHTML = "";
    carreras.forEach((carrera) => {
      const fila = document.createElement("tr");
      fila.innerHTML = `
        <td>${carrera.id}</td>
        <td>${carrera.en_curso ? "En curso" : "Finalizada"}</td>
        <td>${carrera.importe_en_vivo.toFixed(2)} €</td>
      `;
      historialBody.appendChild(fila);
    });
  } catch (error) {
    mostrarMensaje(`No se pudo cargar el historial: ${error.message}`);
  }
}

btnIniciar.addEventListener("click", iniciarCarrera);
btnParado.addEventListener("click", () => cambiarEstado("parado"));
btnMovimiento.addEventListener("click", () => cambiarEstado("movimiento"));
btnFinalizar.addEventListener("click", finalizarCarrera);

btnMostrarRegistro.addEventListener("click", () => {
  formRegistro.hidden = !formRegistro.hidden;
});

formLogin.addEventListener("submit", async (evento) => {
  evento.preventDefault();
  mensajeLoginEl.textContent = "";
  try {
    const { token: nuevoToken } = await llamarApi("/auth/login", {
      method: "POST",
      body: JSON.stringify({
        username: document.getElementById("input-usuario").value.trim(),
        password: document.getElementById("input-password").value,
      }),
    });
    guardarToken(nuevoToken);
    mostrarTaximetro();
  } catch (error) {
    mensajeLoginEl.textContent = error.message;
  }
});

formRegistro.addEventListener("submit", async (evento) => {
  evento.preventDefault();
  mensajeLoginEl.textContent = "";
  const username = document.getElementById("input-registro-usuario").value.trim();
  const password = document.getElementById("input-registro-password").value;
  try {
    await llamarApi("/auth/registro", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    });
    const { token: nuevoToken } = await llamarApi("/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    });
    guardarToken(nuevoToken);
    mostrarTaximetro();
  } catch (error) {
    mensajeLoginEl.textContent = error.message;
  }
});

btnLogout.addEventListener("click", () => {
  limpiarToken();
  mostrarLogin();
});

const pieAnioEl = document.getElementById("pie-anio");
if (pieAnioEl) pieAnioEl.textContent = new Date().getFullYear();

if (token) {
  mostrarTaximetro();
} else {
  mostrarLogin();
}

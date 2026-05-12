/* =========================================================
   calendario.js — Lógica completa del calendario
========================================================= */

const MESES = ["Enero","Febrero","Marzo","Abril","Mayo","Junio",
               "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"];
const DIAS_CORTOS = ["Dom","Lun","Mar","Mié","Jue","Vie","Sáb"];

let viewYear, viewMonth;        // mes visible (1-based)
let todayY, todayM, todayD;
let recordatoriosMes = {};      // { "YYYY-MM-DD": [rec, ...] }
let modalDia = null;
let diaSeleccionado = null;
let editandoId = null;
let eliminarId = null;

/* ── Inicialización ─────────────────────────────────────── */
document.addEventListener("DOMContentLoaded", function () {
  const now = new Date();
  todayY = now.getFullYear();
  todayM = now.getMonth() + 1;
  todayD = now.getDate();
  viewYear  = todayY;
  viewMonth = todayM;

  poblarSelectores();
  cargarMes();

  modalDia = new bootstrap.Modal(document.getElementById("modalDia"));

  document.getElementById("btnPrevYear") .addEventListener("click", () => cambiarVista(-12));
  document.getElementById("btnNextYear") .addEventListener("click", () => cambiarVista(+12));
  document.getElementById("btnPrevMonth").addEventListener("click", () => cambiarVista(-1));
  document.getElementById("btnNextMonth").addEventListener("click", () => cambiarVista(+1));
  document.getElementById("btnHoy").addEventListener("click", irAHoy);
  document.getElementById("selMes").addEventListener("change", function () {
    viewMonth = parseInt(this.value);
    cargarMes();
  });
  document.getElementById("selAnio").addEventListener("change", function () {
    viewYear = parseInt(this.value);
    cargarMes();
  });

  document.getElementById("btnNuevoRec")   .addEventListener("click", abrirFormNuevo);
  document.getElementById("btnCancelarForm").addEventListener("click", cerrarForm);
  document.getElementById("btnGuardarRec") .addEventListener("click", guardarRecordatorio);
  document.getElementById("btnConfElim")   .addEventListener("click", confirmarEliminar);

  document.querySelectorAll(".cal-color-btn").forEach(btn => {
    btn.addEventListener("click", function () {
      document.querySelectorAll(".cal-color-btn").forEach(b => b.classList.remove("active"));
      this.classList.add("active");
    });
  });
});

/* ── Selectores año / mes ───────────────────────────────── */
function poblarSelectores() {
  const selMes  = document.getElementById("selMes");
  const selAnio = document.getElementById("selAnio");
  MESES.forEach((m, i) => {
    const opt = document.createElement("option");
    opt.value = i + 1;
    opt.textContent = m;
    selMes.appendChild(opt);
  });
  for (let y = todayY - 5; y <= todayY + 10; y++) {
    const opt = document.createElement("option");
    opt.value = y;
    opt.textContent = y;
    selAnio.appendChild(opt);
  }
}

function sincronizarSelectores() {
  document.getElementById("selMes").value  = viewMonth;
  document.getElementById("selAnio").value = viewYear;
}

/* ── Navegación ─────────────────────────────────────────── */
function cambiarVista(delta) {
  const d = new Date(viewYear, viewMonth - 1 + delta, 1);
  viewYear  = d.getFullYear();
  viewMonth = d.getMonth() + 1;
  cargarMes();
}

function irAHoy() {
  viewYear  = todayY;
  viewMonth = todayM;
  cargarMes();
}

/* ── Carga del mes vía API ──────────────────────────────── */
async function cargarMes() {
  sincronizarSelectores();
  const res  = await fetch(`/api/recordatorios?anio=${viewYear}&mes=${viewMonth}`);
  const data = await res.json();
  recordatoriosMes = {};
  data.forEach(r => {
    if (!recordatoriosMes[r.fecha]) recordatoriosMes[r.fecha] = [];
    recordatoriosMes[r.fecha].push(r);
  });
  renderGrid();
}

/* ── Renderizado del grid ───────────────────────────────── */
function renderGrid() {
  const grid = document.getElementById("calGrid");
  grid.innerHTML = "";

  const primerDia = new Date(viewYear, viewMonth - 1, 1).getDay(); // 0=dom
  const diasEnMes = new Date(viewYear, viewMonth, 0).getDate();

  // Días del mes anterior para rellenar
  const mesPrev  = viewMonth === 1 ? 12 : viewMonth - 1;
  const anioPrev = viewMonth === 1 ? viewYear - 1 : viewYear;
  const diasPrev = new Date(anioPrev, mesPrev, 0).getDate();

  let celdas = [];

  for (let i = 0; i < primerDia; i++) {
    celdas.push({ d: diasPrev - primerDia + 1 + i, m: mesPrev, y: anioPrev, otroMes: true });
  }
  for (let d = 1; d <= diasEnMes; d++) {
    celdas.push({ d, m: viewMonth, y: viewYear, otroMes: false });
  }
  const restantes = 42 - celdas.length;
  const mesSig  = viewMonth === 12 ? 1 : viewMonth + 1;
  const anioSig = viewMonth === 12 ? viewYear + 1 : viewYear;
  for (let d = 1; d <= restantes; d++) {
    celdas.push({ d, m: mesSig, y: anioSig, otroMes: true });
  }

  celdas.forEach(cel => {
    const div = document.createElement("div");
    div.className = "cal-day" + (cel.otroMes ? " otro-mes" : "");

    const esHoy = cel.d === todayD && cel.m === todayM && cel.y === todayY;
    if (esHoy) div.classList.add("hoy");

    const numSpan = document.createElement("div");
    numSpan.className = "cal-day-num";
    numSpan.textContent = cel.d;
    div.appendChild(numSpan);

    // Recordatorios del día
    const fechaKey = isoFecha(cel.y, cel.m, cel.d);
    const recs = recordatoriosMes[fechaKey] || [];
    const MAX_PILLS = 3;
    recs.slice(0, MAX_PILLS).forEach(r => {
      const pill = document.createElement("div");
      pill.className = `cal-pill color-${r.color}${r.completado ? " completado" : ""}`;
      pill.textContent = (r.hora ? r.hora + " " : "") + r.titulo;
      pill.addEventListener("click", e => { e.stopPropagation(); abrirDia(cel.y, cel.m, cel.d); });
      div.appendChild(pill);
    });
    if (recs.length > MAX_PILLS) {
      const mas = document.createElement("div");
      mas.className = "cal-day-mas";
      mas.textContent = `+${recs.length - MAX_PILLS} más`;
      div.appendChild(mas);
    }

    if (!cel.otroMes) {
      div.addEventListener("click", () => abrirDia(cel.y, cel.m, cel.d));
    }

    grid.appendChild(div);
  });
}

/* ── Modal del día ──────────────────────────────────────── */
function abrirDia(y, m, d) {
  diaSeleccionado = isoFecha(y, m, d);
  editandoId = null;

  const fecha = new Date(y, m - 1, d);
  document.getElementById("modalDiaFecha").textContent =
    `${d} de ${MESES[m-1]} de ${y}`;
  document.getElementById("modalDiaSubtitle").textContent =
    DIAS_CORTOS[fecha.getDay()];

  cerrarForm();
  renderListaModal();
  modalDia.show();
}

function renderListaModal() {
  const lista = document.getElementById("listaRecordatorios");
  lista.innerHTML = "";
  const recs = recordatoriosMes[diaSeleccionado] || [];

  if (!recs.length) {
    lista.innerHTML = `<div class="cal-rec-empty"><i class="bi bi-calendar2-x"></i>Sin recordatorios para este día.</div>`;
    return;
  }

  recs.forEach(r => {
    const item = document.createElement("div");
    item.className = `cal-rec-item${r.completado ? " completado" : ""}`;
    item.innerHTML = `
      <div class="cal-rec-dot color-${r.color}"></div>
      <div class="cal-rec-body">
        <div class="cal-rec-titulo${r.completado ? " completado" : ""}">${escHtml(r.titulo)}</div>
        ${r.hora ? `<div class="cal-rec-hora"><i class="bi bi-clock me-1"></i>${r.hora}</div>` : ""}
        ${r.descripcion ? `<div class="cal-rec-desc">${escHtml(r.descripcion)}</div>` : ""}
      </div>
      <div class="cal-rec-actions">
        <button class="cal-rec-action-btn check" title="${r.completado ? "Desmarcar" : "Marcar completado"}" data-id="${r.id}" data-completado="${r.completado}">
          <i class="bi bi-${r.completado ? "arrow-counterclockwise" : "check-lg"}"></i>
        </button>
        <button class="cal-rec-action-btn edit"   title="Editar"    data-id="${r.id}"><i class="bi bi-pencil"></i></button>
        <button class="cal-rec-action-btn delete" title="Eliminar"  data-id="${r.id}" data-titulo="${escHtml(r.titulo)}"><i class="bi bi-trash"></i></button>
      </div>`;

    item.querySelector(".check").addEventListener("click", async function () {
      await toggleCompletado(parseInt(this.dataset.id), this.dataset.completado === "true");
    });
    item.querySelector(".edit").addEventListener("click", function () {
      abrirFormEditar(parseInt(this.dataset.id));
    });
    item.querySelector(".delete").addEventListener("click", function () {
      pedirEliminar(parseInt(this.dataset.id), this.dataset.titulo);
    });

    lista.appendChild(item);
  });
}

/* ── Formulario crear / editar ──────────────────────────── */
function abrirFormNuevo() {
  editandoId = null;
  document.getElementById("formRecTitle").textContent = "Nuevo recordatorio";
  document.getElementById("recTitulo").value    = "";
  document.getElementById("recDescripcion").value = "";
  document.getElementById("recHora").value       = "";
  seleccionarColor("azul");
  mostrarForm();
}

function abrirFormEditar(id) {
  const recs = recordatoriosMes[diaSeleccionado] || [];
  const rec  = recs.find(r => r.id === id);
  if (!rec) return;
  editandoId = id;
  document.getElementById("formRecTitle").textContent = "Editar recordatorio";
  document.getElementById("recTitulo").value     = rec.titulo;
  document.getElementById("recDescripcion").value = rec.descripcion || "";
  document.getElementById("recHora").value        = rec.hora || "";
  seleccionarColor(rec.color);
  mostrarForm();
}

function mostrarForm() {
  document.getElementById("formRecordatorioWrap").classList.remove("d-none");
  document.getElementById("addRecWrap").classList.add("d-none");
  document.getElementById("errRecTitulo").classList.add("d-none");
  document.getElementById("recTitulo").focus();
}

function cerrarForm() {
  document.getElementById("formRecordatorioWrap").classList.add("d-none");
  document.getElementById("addRecWrap").classList.remove("d-none");
  editandoId = null;
}

function seleccionarColor(color) {
  document.querySelectorAll(".cal-color-btn").forEach(b => {
    b.classList.toggle("active", b.dataset.color === color);
  });
}

function colorSeleccionado() {
  const btn = document.querySelector(".cal-color-btn.active");
  return btn ? btn.dataset.color : "azul";
}

/* ── Guardar (crear / actualizar) ───────────────────────── */
async function guardarRecordatorio() {
  const titulo = document.getElementById("recTitulo").value.trim();
  const errDiv = document.getElementById("errRecTitulo");
  if (!titulo) { errDiv.classList.remove("d-none"); return; }
  errDiv.classList.add("d-none");

  const payload = {
    titulo,
    descripcion: document.getElementById("recDescripcion").value.trim(),
    fecha: diaSeleccionado,
    hora:  document.getElementById("recHora").value.trim(),
    color: colorSeleccionado(),
  };

  if (editandoId) {
    await fetch(`/api/recordatorios/${editandoId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
  } else {
    await fetch("/api/recordatorios", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
  }

  cerrarForm();
  await refrescarDia();
}

/* ── Toggle completado ──────────────────────────────────── */
async function toggleCompletado(id, estaCompletado) {
  await fetch(`/api/recordatorios/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ completado: !estaCompletado })
  });
  await refrescarDia();
}

/* ── Eliminar ───────────────────────────────────────────── */
function pedirEliminar(id, titulo) {
  eliminarId = id;
  document.getElementById("elimRecTitulo").textContent = titulo;
  new bootstrap.Modal(document.getElementById("modalConfElim")).show();
}

async function confirmarEliminar() {
  if (!eliminarId) return;
  await fetch(`/api/recordatorios/${eliminarId}`, { method: "DELETE" });
  eliminarId = null;
  bootstrap.Modal.getInstance(document.getElementById("modalConfElim"))?.hide();
  await refrescarDia();
}

/* ── Refrescar datos del día actual ─────────────────────── */
async function refrescarDia() {
  await cargarMes();
  if (diaSeleccionado) renderListaModal();
}

/* ── Helpers ────────────────────────────────────────────── */
function isoFecha(y, m, d) {
  return `${y}-${String(m).padStart(2,"0")}-${String(d).padStart(2,"0")}`;
}

function escHtml(str) {
  return String(str)
    .replace(/&/g,"&amp;").replace(/</g,"&lt;")
    .replace(/>/g,"&gt;").replace(/"/g,"&quot;");
}

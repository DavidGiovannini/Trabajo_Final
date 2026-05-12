/* =========================================================
   configuracion.js — Lógica de la vista Configuración de Muebles
========================================================= */

/* ── Helpers de formateo numérico estilo argentino ──────
   Muestra: 100.000  |  Envía al servidor: 100000
──────────────────────────────────────────────────────── */
function fmtARS(valor) {
  const n = parseFloat(valor) || 0;
  return n.toLocaleString("es-AR", { minimumFractionDigits: 0, maximumFractionDigits: 0 });
}
function parseARS(str) {
  // "100.000" → 100000;  "100,5" → 100.5
  return parseFloat(String(str).replace(/\./g, "").replace(",", ".")) || 0;
}

/* ── Guardar el valor original de cada precio al cargar ─ */
const fechaOriginal = document.getElementById("fechaTexto")?.innerText.trim() || "";
document.querySelectorAll(".precio-input").forEach(function (inp) {
  const raw = parseFloat(inp.value) || 0;
  inp.dataset.raw      = raw;           // valor numérico real
  inp.dataset.original = inp.value;
  inp.value            = fmtARS(raw);   // mostrar con puntos de miles
});

/* ── Colapsar / expandir cada card de línea ──────────────
   Delega el click al header (.toggle-card) más cercano.
──────────────────────────────────────────────────────── */
document.addEventListener("click", function (e) {
  const header = e.target.closest(".toggle-card");
  if (!header) return;

  const body   = header.nextElementSibling;
  const iconEl = header.querySelector(".arrow i");

  body.classList.toggle("d-none");
  iconEl?.classList.toggle("bi-chevron-down");
  iconEl?.classList.toggle("bi-chevron-up");
});

/* ── Mostrar botones Guardar/Cancelar cuando hay cambios ─
   Se llama desde cualquier interacción que modifique datos.
──────────────────────────────────────────────────────── */
function activarBloque(el) {
  const card = el.closest(".card");
  if (!card) return;

  /* Botones de la card específica */
  const acciones = card.querySelector(".bloque-acciones");
  if (acciones) {
    acciones.classList.remove("d-none");
    acciones.classList.add("d-flex");
  }

  /* Botones globales (barra superior) */
  const ga = document.getElementById("globalAcciones");
  if (ga) { ga.classList.remove("d-none"); ga.classList.add("d-flex"); }
}

/* ── Agregar nueva fila de mueble ────────────────────────
   Inserta una fila vacía (marcada como is-new) en el tbody.
──────────────────────────────────────────────────────── */
document.addEventListener("click", function (e) {
  const btn = e.target.closest(".btn-add-mueble");
  if (!btn) return;

  const tbody = btn.previousElementSibling;
  const row   = document.createElement("div");
  row.className = "cfg-row is-new";
  row.innerHTML = `
    <div><input type="checkbox" class="form-check-input chk-row"></div>
    <div>
      <input type="number" step="0.01" class="form-control form-control-sm" name="medida[]" value="0">
      <input type="hidden" name="tipo[]"  value="mueble">
      <input type="hidden" name="linea[]" value="${btn.dataset.linea}">
      <input type="hidden" name="ref[]"   value="new">
    </div>
    <div>
      <div class="input-group input-group-sm">
        <span class="input-group-text">$</span>
        <input class="form-control precio-input" name="base[]" value="0">
      </div>
    </div>
    <div>
      <div class="input-group input-group-sm">
        <span class="input-group-text">$</span>
        <input class="form-control precio-input" name="alacena[]" value="0">
      </div>
    </div>
    <div>
      <div class="input-group input-group-sm">
        <span class="input-group-text">$</span>
        <input class="form-control precio-input" name="inox[]" value="0">
      </div>
    </div>
    <div class="text-center">
      <button type="button" class="btn btn-sm btn-outline-danger btn-delete"
              data-id="new" data-tipo="mueble">
        <i class="bi bi-trash"></i>
      </button>
    </div>
  `;

  tbody.appendChild(row);
  activarBloque(btn);
});

/* ── Agregar nueva fila de adicional ─────────────────────
   Igual que la de mueble pero con 4 columnas (add).
──────────────────────────────────────────────────────── */
document.addEventListener("click", function (e) {
  const btn = e.target.closest(".btn-add-adicional");
  if (!btn) return;

  /* En el modal de configuración el btn-add-adicional también
     existe en el presupuestador; salir si no es cfg context */
  if (!btn.closest("#formConfig")) return;

  const tbody = btn.previousElementSibling;
  const row   = document.createElement("div");
  row.className = "cfg-row cfg-row-add is-new";
  row.innerHTML = `
    <div><input type="checkbox" class="form-check-input chk-row"></div>
    <div>
      <input class="form-control form-control-sm" name="nombre_adicional[]" placeholder="Nombre">
      <input type="hidden" name="tipo[]"  value="adicional">
      <input type="hidden" name="linea[]" value="${btn.dataset.linea}">
      <input type="hidden" name="ref[]"   value="new">
    </div>
    <div>
      <div class="input-group input-group-sm">
        <span class="input-group-text">$</span>
        <input class="form-control precio-input" name="precios_base[]" value="0">
      </div>
    </div>
    <div>
      <div class="input-group input-group-sm">
        <span class="input-group-text">$</span>
        <input class="form-control precio-input" name="precios_alacena[]" value="0">
      </div>
    </div>
    <div>
      <div class="input-group input-group-sm">
        <span class="input-group-text">$</span>
        <input class="form-control precio-input" name="precios_inox[]" value="0">
      </div>
    </div>
    <div class="text-center">
      <button type="button" class="btn btn-sm btn-outline-danger btn-delete"
              data-id="new" data-tipo="adicional">
        <i class="bi bi-trash"></i>
      </button>
    </div>
  `;

  tbody.appendChild(row);
  activarBloque(btn);
});

/* ── Eliminar fila ───────────────────────────────────────
   Si es nueva (id="new") la quita del DOM; si ya existe
   envía DELETE al servidor.
──────────────────────────────────────────────────────── */
document.addEventListener("click", async function (e) {
  const btn = e.target.closest(".btn-delete");
  if (!btn) return;
  if (!confirm("¿Eliminar definitivamente?")) return;

  if (btn.dataset.id === "new") {
    btn.closest(".cfg-row").remove();
    return;
  }

  const res = await fetch(`/configuracion/${btn.dataset.tipo}/${btn.dataset.id}`, {
    method: "DELETE"
  });

  if (res.ok) {
    btn.closest(".cfg-row").remove();
  } else {
    alert("Error al eliminar");
  }
});

/* ── Cancelar cambios de una card ────────────────────────
   Elimina filas nuevas y oculta los botones de acciones.
──────────────────────────────────────────────────────── */
document.addEventListener("click", function (e) {
  if (!e.target.classList.contains("btn-cancelar")) return;

  const card = e.target.closest(".card");

  /* Elimina filas que aún no se guardaron */
  card.querySelectorAll('input[name="ref[]"][value="new"]').forEach(function (i) {
    i.closest(".cfg-row").remove();
  });

  const acciones = card.querySelector(".bloque-acciones");
  acciones?.classList.add("d-none");
  acciones?.classList.remove("d-flex");
});

/* ── Guardar cambios de una card ─────────────────────────
   Envía el formulario completo (todos los datos del form).
──────────────────────────────────────────────────────── */
document.addEventListener("click", function (e) {
  if (!e.target.classList.contains("btn-guardar-bloque")) return;
  desformatearAntesDeEnviar();
  document.getElementById("formConfig").submit();
});

/* ── Sincronizar el checkbox global con los individuales ─
   Muestra indeterminate si hay selección parcial.
──────────────────────────────────────────────────────── */
function sincronizarGlobal() {
  const allChks    = document.querySelectorAll(".chk-row");
  const allChecked = document.querySelectorAll(".chk-row:checked");
  const g          = document.getElementById("selectAllGlobal");
  if (!g) return;
  g.indeterminate = allChecked.length > 0 && allChecked.length < allChks.length;
  g.checked       = allChks.length > 0 && allChks.length === allChecked.length;
}

/* Cambio en select-all de card individual o en chk-row */
document.addEventListener("change", function (e) {
  if (e.target.classList.contains("select-all")) {
    const card = e.target.closest(".card");
    card.querySelectorAll(".chk-row").forEach(function (c) {
      c.checked = e.target.checked;
    });
    sincronizarGlobal();
  }

  if (e.target.classList.contains("chk-row")) {
    const card     = e.target.closest(".card");
    const all      = card.querySelectorAll(".chk-row");
    const checked  = card.querySelectorAll(".chk-row:checked");
    const selectAll = card.querySelector(".select-all");
    if (selectAll) selectAll.checked = all.length === checked.length;
    sincronizarGlobal();
  }
});

/* ── Al hacer focus: mostrar número crudo para editar ─── */
document.addEventListener("focusin", function (e) {
  if (e.target.classList.contains("precio-input")) {
    const raw = parseARS(e.target.value);
    e.target.value = raw === 0 ? "" : String(raw);
    activarBloque(e.target);
  } else if (e.target.name === "medida[]") {
    if (parseFloat(e.target.value) === 0) e.target.value = "";
    activarBloque(e.target);
  }
});

/* ── Al salir del campo: volver a formato con puntos ────
   También actualiza la fecha si el valor cambió.
──────────────────────────────────────────────────────── */
document.addEventListener("blur", function (e) {
  if (e.target.classList.contains("precio-input")) {
    const raw   = parseARS(e.target.value);
    const antes = parseARS(e.target.dataset.original || "0");
    e.target.dataset.raw = raw;
    e.target.value       = fmtARS(raw);
    if (raw !== antes) autoSetFecha();
  }
}, true);

/* ── Aplicar porcentaje a filas seleccionadas (por card) ─ */
document.addEventListener("click", function (e) {
  if (!e.target.classList.contains("btn-aplicar")) return;

  const card       = e.target.closest(".card");
  const porcentaje = Number(card.querySelector(".porcentaje").value);

  if (!porcentaje) { alert("Ingresá un porcentaje"); return; }

  const filas = card.querySelectorAll(".chk-row:checked");
  if (!filas.length) { alert("Tenés que seleccionar al menos una fila"); return; }

  filas.forEach(function (chk) {
    const fila = chk.closest(".cfg-row");
    fila.querySelectorAll(".precio-input").forEach(function (input) {
      let val = parseARS(input.value);
      val += val * porcentaje / 100;
      input.dataset.raw = val;
      input.value       = fmtARS(val);
    });
  });

  activarBloque(e.target);
  autoSetFecha();
});

/* ── Formatear una fecha ISO a dd/mm/yyyy ─────────────── */
function formatearFecha(fechaISO) {
  if (!fechaISO) return "--/--/----";
  const [y, m, d] = fechaISO.split("-");
  return `${d}/${m}/${y}`;
}

/* ── Eventos del editor de fecha ─────────────────────────
   El lápiz muestra el input; "Guardar" persiste la fecha.
──────────────────────────────────────────────────────── */
document.addEventListener("click", async function (e) {
  if (e.target.closest("#btnEditarFecha")) {
    document.getElementById("fechaPrecioInput").classList.remove("d-none");
    document.getElementById("btnGuardarFecha").classList.remove("d-none");
    document.getElementById("fechaPrecioInput").focus();
  }

  if (e.target.id === "btnGuardarFecha") {
    const input = document.getElementById("fechaPrecioInput");
    const fecha = input.value;
    if (!fecha) { alert("Seleccioná una fecha"); return; }

    const res = await fetch("/configuracion/fecha", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ fecha })
    });

    if (res.ok) {
      document.getElementById("fechaTexto").innerText = formatearFecha(fecha);
      input.classList.add("d-none");
      e.target.classList.add("d-none");
    } else {
      alert("Error al guardar la fecha");
    }
  }
});

/* ── Auto-fecha: pone hoy automáticamente al editar ─────
   Se llama desde blur de precios y aplicar-porcentaje.
──────────────────────────────────────────────────────── */
async function autoSetFecha() {
  const hoy = new Date().toISOString().split("T")[0];
  document.getElementById("fechaTexto").innerText = formatearFecha(hoy);
  const inp = document.getElementById("fechaPrecioInput");
  if (inp) inp.value = hoy;
  try {
    await fetch("/configuracion/fecha", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ fecha: hoy })
    });
  } catch (_) {}
}

/* ── Select All global ───────────────────────────────── */
document.getElementById("selectAllGlobal")?.addEventListener("change", function () {
  document.querySelectorAll(".chk-row").forEach(function (c) { c.checked = this.checked; }, this);
  document.querySelectorAll(".select-all").forEach(function (s) { s.checked = this.checked; }, this);
});

/* ── Cancelar global: revierte todo ─────────────────────
   Restaura precios originales, elimina nuevas filas,
   revierte la fecha en servidor y oculta todos los botones.
──────────────────────────────────────────────────────── */
document.getElementById("btnCancelarGlobal")?.addEventListener("click", async function () {

  /* Revertir valores de precio */
  document.querySelectorAll(".precio-input[data-original]").forEach(function (inp) {
    inp.value = inp.dataset.original;
  });

  /* Eliminar filas nuevas en todas las cards */
  document.querySelectorAll('input[name="ref[]"][value="new"]').forEach(function (i) {
    i.closest(".cfg-row").remove();
  });

  /* Revertir la fecha mostrada */
  const textoEl = document.getElementById("fechaTexto");
  if (textoEl) textoEl.innerText = fechaOriginal || "--/--/----";

  /* Revertir la fecha en el servidor */
  if (fechaOriginal && fechaOriginal !== "--/--/----") {
    const [d, m, y] = fechaOriginal.split("/");
    try {
      await fetch("/configuracion/fecha", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ fecha: `${y}-${m}-${d}` })
      });
    } catch (_) {}
  }

  /* Ocultar botones de cada card */
  document.querySelectorAll(".bloque-acciones").forEach(function (b) {
    b.classList.add("d-none");
    b.classList.remove("d-flex");
  });

  /* Ocultar botones globales */
  const ga = document.getElementById("globalAcciones");
  if (ga) { ga.classList.add("d-none"); ga.classList.remove("d-flex"); }

  /* Desmarcar todos los checkboxes */
  document.querySelectorAll(".chk-row, .select-all").forEach(function (c) { c.checked = false; });
  const g = document.getElementById("selectAllGlobal");
  if (g) { g.checked = false; g.indeterminate = false; }
});

/* ── Desformatear precios antes de enviar al servidor ─── */
function desformatearAntesDeEnviar() {
  document.querySelectorAll(".precio-input").forEach(function (inp) {
    inp.value = String(parseARS(inp.value));
  });
}

/* ── Guardar global: envía el formulario ─────────────── */
document.getElementById("btnGuardarGlobal")?.addEventListener("click", function () {
  desformatearAntesDeEnviar();
  document.getElementById("formConfig").submit();
});

/* ── Aplicar % global a todas las filas seleccionadas ── */
document.getElementById("btnAplicarGlobal")?.addEventListener("click", function () {
  const porcentaje = Number(document.getElementById("porcentajeGlobal").value);
  if (!porcentaje) { alert("Ingresá un porcentaje"); return; }

  const filas = document.querySelectorAll(".chk-row:checked");
  if (!filas.length) { alert("Seleccioná al menos una fila"); return; }

  filas.forEach(function (chk) {
    chk.closest(".cfg-row")?.querySelectorAll(".precio-input").forEach(function (input) {
      let val = parseARS(input.value);
      val += val * porcentaje / 100;
      input.dataset.raw = val;
      input.value       = fmtARS(val);
    });
    activarBloque(chk);
  });

  autoSetFecha();
});

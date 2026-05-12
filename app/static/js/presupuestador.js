/* =========================================================
   presupuestador.js — Lógica del Presupuestador
   Requiere: window.PRECIOS_MUEBLES y window.ADICIONALES
   definidos en un bloque <script> inline del template.
========================================================= */

document.addEventListener("DOMContentLoaded", function () {

  /* ══════════════════════════════════════════════════════
     SEÑA
  ════════════════════════════════════════════════════ */
  const checkSena       = document.getElementById("checkSena");
  const inputSena       = document.getElementById("inputSena");
  const selectFormaPago = document.getElementById("selectFormaPago");
  const senaFields      = document.getElementById("senaFields");

  checkSena?.addEventListener("change", function () {
    const activo = this.checked;
    senaFields?.classList.toggle("d-none", !activo);
    inputSena.disabled       = !activo;
    selectFormaPago.disabled = !activo;
    if (!activo) { inputSena.value = ""; selectFormaPago.value = "Efectivo"; }
    actualizarResumen();
  });

  inputSena?.addEventListener("input", actualizarResumen);

  /* ══════════════════════════════════════════════════════
     FILTRO DE PRODUCTOS
     Filtra grupos y tarjetas; expande grupos con resultados.
  ════════════════════════════════════════════════════ */
  document.getElementById("filtroProducto")?.addEventListener("input", function () {
    const txt = this.value.toLowerCase().trim();

    document.querySelectorAll(".presu-grupo").forEach(function (grupo) {
      const tipoGrupo = grupo.dataset.grupoTipo || "";
      const items     = grupo.querySelectorAll(".producto-item");
      let visible     = 0;

      items.forEach(function (item) {
        const match = !txt ||
          (item.dataset.nombre || "").includes(txt) ||
          (item.dataset.tipo   || "").includes(txt) ||
          tipoGrupo.includes(txt);
        item.style.display = match ? "" : "none";
        if (match) visible++;
      });

      if (txt) {
        grupo.style.display = visible > 0 ? "" : "none";
        if (visible > 0) {
          const body = grupo.querySelector(".collapse");
          const btn  = grupo.querySelector(".presu-grupo-toggle");
          if (body) body.classList.add("show");
          if (btn)  btn.setAttribute("aria-expanded", "true");
        }
      } else {
        grupo.style.display = "";
      }
    });
  });

  /* ══════════════════════════════════════════════════════
     ESTADO COMPARTIDO
  ════════════════════════════════════════════════════ */
  const resumenItems  = [];       /* array de ítems del presupuesto */
  let   lineaSeleccionada = null; /* línea de mueble activa */

  const hiddenManual    = document.getElementById("items_manual_json");
  const summaryList     = document.getElementById("summaryList");
  const resumenSubtotal = document.getElementById("resumenSubtotal");
  const resumenSena     = document.getElementById("resumenSena");
  const resumenTotal    = document.getElementById("resumenTotal");

  /* Formatea un número como moneda AR */
  function money(n) {
    return "$" + Number(n || 0).toLocaleString("es-AR", {maximumFractionDigits: 0});
  }

  /* ──────────────────────────────────────────────────────
     HELPER: devuelve las opciones a mostrar en el builder.
     Reglas:
       - Exacto → [{ precios, resaltado:true }]
       - Fuera de rango (< min o > max) → el extremo resaltado
       - Entre dos medidas → ambas, con resaltado en la más
         cercana (si equidistante, ambas resaltadas)
  ──────────────────────────────────────────────────── */
  function getOpciones(linea, medidaReal) {
    const sorted = window.PRECIOS_MUEBLES
      .filter(function (x) { return x.linea === linea; })
      .sort(function (a, b) { return a.medida - b.medida; });

    if (!sorted.length) return [];

    /* Exacto */
    const exacto = sorted.find(function (x) { return x.medida === medidaReal; });
    if (exacto) return [{ precios: exacto, resaltado: true }];

    /* Por debajo del mínimo */
    if (medidaReal < sorted[0].medida) return [{ precios: sorted[0], resaltado: true }];

    /* Por encima del máximo */
    if (medidaReal > sorted[sorted.length - 1].medida) {
      return [{ precios: sorted[sorted.length - 1], resaltado: true }];
    }

    /* Entre dos medidas: buscar piso y techo */
    let floor = null, ceiling = null;
    for (const p of sorted) {
      if (p.medida < medidaReal) floor = p;
      if (p.medida > medidaReal && ceiling === null) ceiling = p;
    }

    const distFloor   = medidaReal - floor.medida;
    const distCeiling = ceiling.medida - medidaReal;

    return [
      { precios: floor,   resaltado: distFloor  <= distCeiling },
      { precios: ceiling, resaltado: distCeiling <= distFloor  }
    ];
  }

  /* ──────────────────────────────────────────────────────
     HELPER: renderiza adicionales de la línea seleccionada
  ──────────────────────────────────────────────────── */
  function renderAdicionales(linea) {
    const section   = document.getElementById("adicionalesSection");
    const container = document.getElementById("adicionalesContainer");
    if (!section || !container) return;

    const items = (window.ADICIONALES || []).filter(function (a) {
      return a.linea === linea;
    });

    /* Expandir: una card por cada tipo con precio cargado */
    const cards = [];
    items.forEach(function (a) {
      if (a.precio_base)    cards.push({ nombre: a.nombre, tipo: "Mueble",  precio: a.precio_base,    badge: "badge-mueble"  });
      if (a.precio_alacena) cards.push({ nombre: a.nombre, tipo: "Alacena", precio: a.precio_alacena, badge: "badge-alacena" });
      if (a.precio_inox)    cards.push({ nombre: a.nombre, tipo: "Inox",    precio: a.precio_inox,    badge: "badge-inox"    });
    });

    if (!cards.length) {
      section.classList.add("d-none");
      container.innerHTML = "";
      return;
    }

    const fmt = function (n) {
      return Number(n).toLocaleString("es-AR", { maximumFractionDigits: 0 });
    };

    container.innerHTML = cards.map(function (c) {
      return `<div class="add-card">
        <div>
          <div class="add-card-nombre">${c.nombre}</div>
          <span class="add-card-badge ${c.badge}">${c.tipo}</span>
        </div>
        <div class="add-card-precio">$${fmt(c.precio)}</div>
        <button type="button"
                class="add-card-btn btn-add-adicional"
                data-nombre="${c.nombre}" data-tipo="${c.tipo}"
                data-precio="${c.precio}" data-porcentaje="0">
          <i class="bi bi-plus-lg me-1"></i>Agregar
        </button>
      </div>`;
    }).join("");

    section.classList.remove("d-none");
  }

  /* ══════════════════════════════════════════════════════
     RESUMEN LATERAL
     Re-dibuja la lista de ítems y actualiza totales.
  ════════════════════════════════════════════════════ */
  function actualizarResumen() {
    if (!summaryList) return;
    summaryList.innerHTML = "";

    if (!resumenItems.length) {
      summaryList.innerHTML = `
        <div class="text-muted small text-center py-3">
          <i class="bi bi-cart" style="font-size:1.4rem;opacity:.3;display:block;margin-bottom:6px;"></i>
          Todavía no agregaste ítems.
        </div>`;
    } else {
      resumenItems.forEach(function (item, index) {
        const el = document.createElement("div");
        el.className = "summary-item";
        el.innerHTML = `
          <span class="summary-item-desc" title="${item.descripcion}">${item.descripcion}</span>
          <span class="summary-item-dots"></span>
          <span class="summary-item-price">${money(item.subtotal)}</span>
          <button type="button" class="summary-item-remove"
                  data-remove-index="${index}" title="Quitar">
            <i class="bi bi-x-lg"></i>
          </button>`;
        summaryList.appendChild(el);
      });
    }

    const subtotal = resumenItems.reduce(function (acc, x) { return acc + Number(x.subtotal || 0); }, 0);
    const sena     = Number(inputSena?.value || 0);

    resumenSubtotal.textContent = money(subtotal);
    resumenSena.textContent     = sena > 0 ? money(sena) : "$0";
    resumenTotal.textContent    = money(subtotal);

    hiddenManual.value = JSON.stringify(resumenItems);
    syncProductosBackend();
  }

  /* ── Quitar ítem por índice al hacer clic en ✕ ───────── */
  document.addEventListener("click", function (e) {
    const btn = e.target.closest("[data-remove-index]");
    if (!btn) return;
    const idx = Number(btn.getAttribute("data-remove-index"));
    if (!Number.isNaN(idx)) {
      resumenItems.splice(idx, 1);
      actualizarResumen();
    }
  });

  /* ── Mantiene sincronizados los checkboxes hidden del form */
  function syncProductosBackend() {
    document.querySelectorAll('input[name="prod_id[]"]').forEach(function (ch) {
      ch.checked = false;
    });
    resumenItems.forEach(function (item) {
      if (item.tipo === "producto" && item.producto_id) {
        const chk = document.querySelector(`input[name="prod_id[]"][value="${item.producto_id}"]`);
        if (chk) chk.checked = true;
      }
    });
  }

  /* ══════════════════════════════════════════════════════
     AGREGAR PRODUCTO INDEPENDIENTE
  ════════════════════════════════════════════════════ */
  document.addEventListener("click", function (e) {
    const btn = e.target.closest(".btn-agregar-producto");
    if (!btn) return;

    const id     = btn.dataset.id;
    const nombre = btn.dataset.nombre;
    const tipo   = btn.dataset.tipo;
    const precio = Number(btn.dataset.precio || 0);
    const cant   = Number(document.getElementById("cant_" + id)?.value || 1);

    resumenItems.push({
      tipo:       "producto",
      producto_id: id,
      descripcion: nombre + (tipo ? " (" + tipo + ")" : ""),
      cantidad:    cant,
      metros:      null,
      subtotal:    precio * cant
    });

    actualizarResumen();

    /* Feedback visual momentáneo en el botón */
    btn.textContent = "✓ Agregado";
    btn.disabled    = true;
    setTimeout(function () {
      btn.innerHTML = '<i class="bi bi-plus-lg me-1"></i>Agregar';
      btn.disabled  = false;
    }, 1200);
  });

  /* ══════════════════════════════════════════════════════
     SELECCIÓN DE LÍNEA DE MUEBLE
     Al elegir línea (incluso la misma) se blanquean todos los campos.
  ════════════════════════════════════════════════════ */
  function resetMuebleFields() {
    document.getElementById("mueble-medida-total").value = "";
    const radioBase = document.querySelector('input[name="comp-mueble"][value="base"]');
    if (radioBase) radioBase.checked = true;
    document.getElementById("sugerenciaMueble").innerHTML =
      `<i class="bi bi-info-circle me-1"></i>Ingresá una medida para ver la sugerencia de armado.`;
    document.getElementById("builderDetalle").innerHTML =
      `<div class="text-muted small">Todavía no hay componentes calculados.</div>`;
  }

  document.querySelectorAll(".linea-card").forEach(function (card) {
    card.addEventListener("click", function () {
      document.querySelectorAll(".linea-card").forEach(function (x) {
        x.classList.remove("active");
      });
      this.classList.add("active");
      lineaSeleccionada = this.dataset.linea;
      resetMuebleFields();
      renderAdicionales(lineaSeleccionada);
    });
  });

  /* Re-calcula al cambiar medida o componente */
  document.getElementById("mueble-medida-total")?.addEventListener("input", calcularMueblePreview);
  document.querySelectorAll('input[name="comp-mueble"]').forEach(function (r) {
    r.addEventListener("change", calcularMueblePreview);
  });

  /* ══════════════════════════════════════════════════════
     PREVIEW DEL CONSTRUCTOR DE MUEBLE
     Muestra 1 opción (exacta / fuera de rango) o 2 opciones
     (piso y techo) con la más cercana levemente resaltada.
     Sin repicero.
  ════════════════════════════════════════════════════ */
  function calcularMueblePreview() {
    const sugerencia = document.getElementById("sugerenciaMueble");
    const builder    = document.getElementById("builderDetalle");

    if (!lineaSeleccionada) {
      sugerencia.innerHTML = `<i class="bi bi-info-circle me-1"></i>Elegí primero una línea.`;
      builder.innerHTML    = `<div class="text-muted small">Todavía no hay componentes calculados.</div>`;
      return;
    }

    const medidaTotal = Number(document.getElementById("mueble-medida-total")?.value || 0);
    if (!medidaTotal) {
      sugerencia.innerHTML = `<i class="bi bi-info-circle me-1"></i>Ingresá una medida para ver la sugerencia de armado.`;
      builder.innerHTML    = `<div class="text-muted small">Todavía no hay componentes calculados.</div>`;
      return;
    }

    const opciones = getOpciones(lineaSeleccionada, medidaTotal);
    if (!opciones.length) {
      sugerencia.innerHTML = `<i class="bi bi-exclamation-triangle me-1"></i>No hay precios cargados para esa línea.`;
      builder.innerHTML    = `<div class="text-muted small">No se pudo calcular el mueble.</div>`;
      return;
    }

    const comp      = document.querySelector('input[name="comp-mueble"]:checked')?.value;
    const linNombre = lineaSeleccionada.charAt(0).toUpperCase() + lineaSeleccionada.slice(1);
    const doble     = opciones.length > 1;

    /* Caja de sugerencia */
    const baseTexto = opciones.map(function (o) {
      return o.precios.medida + " cm" + (doble && o.resaltado ? " ✓" : "");
    }).join(" / ");

    sugerencia.innerHTML = `
      <i class="bi bi-check-circle me-1"></i>
      <strong>Línea:</strong> ${linNombre} &nbsp;|&nbsp;
      <strong>Medida solicitada:</strong> ${medidaTotal} cm &nbsp;|&nbsp;
      <strong>Sugerida${doble ? "s" : ""}:</strong> ${baseTexto}
    `;

    if (!comp) {
      builder.innerHTML = `<div class="text-muted small">Seleccioná un tipo de componente.</div>`;
      return;
    }

    const labelComp = comp === "base"    ? "Mueble sin mesada"
                    : comp === "alacena" ? "Alacena"
                                         : "Mesada de acero inox";
    let html = "";

    opciones.forEach(function (opcion) {
      const precios  = opcion.precios;
      const base     = precios.medida;
      const subtotal = Number(precios[comp] || 0);
      const desc     = linNombre + " - " + labelComp + " " + base + " cm";

      /* Resaltado = más cercana; secundaria = la otra opción */
      const rowClass = opcion.resaltado
        ? "builder-row builder-row-highlight"
        : "builder-row builder-row-secondary";

      html += `<div class="${rowClass}">
        <div>
          <div class="fw-bold">${labelComp}</div>
          <div class="small text-muted">${base} cm</div>
        </div>
        <div class="d-flex align-items-center gap-2">
          <span class="builder-price">${money(subtotal)}</span>
          <button type="button"
                  class="btn btn-success btn-sm btn-soft btn-agregar-opcion"
                  data-subtotal="${subtotal}"
                  data-desc="${desc.replace(/"/g, "&quot;")}">
            <i class="bi bi-check2-circle me-1"></i>Agregar
          </button>
        </div>
      </div>`;
    });

    builder.innerHTML = html;
  }

  /* ══════════════════════════════════════════════════════
     CANCELAR — limpia constructor + vacía el resumen completo
  ════════════════════════════════════════════════════ */
  document.getElementById("btnCancelarMueble")?.addEventListener("click", function () {
    if (resumenItems.length > 0 && !confirm("¿Cancelar y borrar todo el presupuesto armado?")) return;

    lineaSeleccionada = null;
    document.querySelectorAll(".linea-card").forEach(function (x) { x.classList.remove("active"); });
    resetMuebleFields();

    /* Ocultar adicionales */
    const section = document.getElementById("adicionalesSection");
    if (section) section.classList.add("d-none");
    const container = document.getElementById("adicionalesContainer");
    if (container) container.innerHTML = "";

    /* Vaciar resumen */
    resumenItems.length = 0;
    actualizarResumen();
  });

  /* ══════════════════════════════════════════════════════
     AGREGAR OPCIÓN DEL BUILDER AL RESUMEN
     Cada fila del builder tiene su propio botón "Agregar"
     con el subtotal y la descripción ya calculados.
  ════════════════════════════════════════════════════ */
  document.addEventListener("click", function (e) {
    const btn = e.target.closest(".btn-agregar-opcion");
    if (!btn) return;

    const subtotal = Number(btn.dataset.subtotal || 0);
    const desc     = btn.dataset.desc || "";

    resumenItems.push({ tipo: "manual", descripcion: desc, cantidad: 1, metros: null, subtotal });
    actualizarResumen();

    /* Deshabilitar el botón para evitar doble agregado */
    btn.disabled  = true;
    btn.innerHTML = '<i class="bi bi-check2 me-1"></i>Agregado';
    btn.classList.replace("btn-success", "btn-secondary");
  });

  /* ══════════════════════════════════════════════════════
     ADICIONALES
  ════════════════════════════════════════════════════ */
  document.addEventListener("click", function (e) {
    const btn = e.target.closest(".btn-add-adicional");
    /* Solo actuar sobre adicionales del presupuestador (no de cfg) */
    if (!btn || btn.closest("#formConfig")) return;

    const nombre     = btn.dataset.nombre;
    const tipo       = btn.dataset.tipo || "";
    const precio     = Number(btn.dataset.precio || 0);
    const porcentaje = Number(btn.dataset.porcentaje || 0);

    let subtotal = precio;
    if (porcentaje > 0) {
      const subtotalActual = resumenItems.reduce(function (acc, x) {
        return acc + Number(x.subtotal || 0);
      }, 0);
      subtotal = subtotalActual * (porcentaje / 100);
    }

    const desc = tipo ? nombre + " (" + tipo + ")" : nombre;
    resumenItems.push({ tipo: "manual", descripcion: desc, cantidad: 1, metros: null, subtotal });
    actualizarResumen();
  });

  /* Dibuja el resumen inicial (vacío) */
  actualizarResumen();

  /* ══════════════════════════════════════════════════════
     VALIDACIÓN AL ENVIAR EL FORMULARIO
     Muestra mensajes inline antes de hacer el POST.
  ════════════════════════════════════════════════════ */
  document.getElementById("formPresupuesto")?.addEventListener("submit", function (e) {
    let ok = true;

    const valCliente   = document.getElementById("inputCliente")?.value.trim() || "";
    const valTelefono  = document.getElementById("inputTelefono")?.value.trim() || "";
    const errCliente   = document.getElementById("errCliente");
    const errTelefono  = document.getElementById("errTelefono");
    const errSena      = document.getElementById("errSena");

    /* Nombre / apellido obligatorio */
    if (!valCliente) {
      errCliente.textContent = "El nombre y apellido del cliente es obligatorio.";
      errCliente.classList.remove("d-none");
      ok = false;
    } else {
      errCliente.classList.add("d-none");
    }

    /* Teléfono obligatorio */
    if (!valTelefono) {
      errTelefono.textContent = "El teléfono del cliente es obligatorio.";
      errTelefono.classList.remove("d-none");
      ok = false;
    } else {
      errTelefono.classList.add("d-none");
    }

    /* Seña: si está marcada, forma de pago y monto son obligatorios */
    if (checkSena?.checked) {
      const monto = Number(inputSena?.value || 0);
      if (!monto || monto <= 0) {
        errSena.textContent = "Ingresá el monto de la seña.";
        errSena.classList.remove("d-none");
        ok = false;
      } else {
        errSena.classList.add("d-none");
      }
    } else {
      errSena?.classList.add("d-none");
    }

    if (!ok) e.preventDefault();
  });

});

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

  checkSena?.addEventListener("change", function () {
    const activo = this.checked;
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
    return "$" + Number(n || 0).toLocaleString("es-AR");
  }

  /* ──────────────────────────────────────────────────────
     HELPER: medida base más cercana (≤ medidaReal)
  ──────────────────────────────────────────────────── */
  function getMedidaBase(linea, medidaReal) {
    const medidas = window.PRECIOS_MUEBLES
      .filter(function (x) { return x.linea === linea; })
      .map(function (x)    { return x.medida; })
      .sort(function (a, b) { return a - b; });

    if (!medidas.length) return null;

    let base = medidas[0];
    for (const m of medidas) {
      if (m <= medidaReal) base = m;
      if (m >  medidaReal) break;
    }
    return base;
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
  ════════════════════════════════════════════════════ */
  document.querySelectorAll(".linea-card").forEach(function (card) {
    card.addEventListener("click", function () {
      document.querySelectorAll(".linea-card").forEach(function (x) {
        x.classList.remove("active");
      });
      this.classList.add("active");
      lineaSeleccionada = this.dataset.linea;
      calcularMueblePreview();
    });
  });

  /* Re-calcula al cambiar medida o componente */
  document.getElementById("mueble-medida-total")?.addEventListener("input", calcularMueblePreview);
  document.querySelectorAll('input[name="comp-mueble"]').forEach(function (r) {
    r.addEventListener("change", calcularMueblePreview);
  });

  /* ══════════════════════════════════════════════════════
     PREVIEW DEL CONSTRUCTOR DE MUEBLE
     Actualiza la sugerencia y el detalle del builder.
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

    const base    = getMedidaBase(lineaSeleccionada, medidaTotal);
    const precios = window.PRECIOS_MUEBLES.find(function (x) {
      return x.linea === lineaSeleccionada && x.medida === base;
    });

    if (!base || !precios) {
      sugerencia.innerHTML = `<i class="bi bi-exclamation-triangle me-1"></i>No hay precios cargados para esa línea.`;
      builder.innerHTML    = `<div class="text-muted small">No se pudo calcular el mueble.</div>`;
      return;
    }

    const diferencia = Math.max(0, medidaTotal - base);
    const comp       = document.querySelector('input[name="comp-mueble"]:checked')?.value;

    /* Caja de sugerencia */
    sugerencia.innerHTML = `
      <i class="bi bi-check-circle me-1"></i>
      <strong>Línea:</strong> ${lineaSeleccionada} &nbsp;|&nbsp;
      <strong>Medida solicitada:</strong> ${medidaTotal} cm &nbsp;|&nbsp;
      <strong>Base sugerida:</strong> ${base} cm
      ${diferencia > 0 ? `&nbsp;|&nbsp;<strong>Ajuste:</strong> ${diferencia} cm` : ""}
    `;

    let html = "";

    /* Fila del componente seleccionado */
    if (comp === "base") {
      html += `<div class="builder-row">
        <div><div class="fw-bold">Mueble sin mesada</div><div class="small text-muted">${base} cm</div></div>
        <div class="builder-price">${money(precios.base)}</div>
      </div>`;
    }
    if (comp === "alacena") {
      html += `<div class="builder-row">
        <div><div class="fw-bold">Alacena</div><div class="small text-muted">${base} cm</div></div>
        <div class="builder-price">${money(precios.alacena)}</div>
      </div>`;
    }
    if (comp === "inox") {
      html += `<div class="builder-row">
        <div><div class="fw-bold">Mesada de acero inox</div><div class="small text-muted">${base} cm</div></div>
        <div class="builder-price">${money(precios.inox)}</div>
      </div>`;
    }

    /* Fila de ajuste si la medida no coincide exactamente */
    if (diferencia > 0) {
      html += `<div class="builder-row">
        <div><div class="fw-bold">Ajuste / repicero estimado</div><div class="small text-muted">${diferencia} cm</div></div>
        <div class="builder-price">${money(diferencia * 1000)}</div>
      </div>`;
    }

    builder.innerHTML = html || `<div class="text-muted small">Seleccioná al menos un componente.</div>`;
  }

  /* ══════════════════════════════════════════════════════
     CANCELAR — limpia constructor + vacía el resumen completo
  ════════════════════════════════════════════════════ */
  document.getElementById("btnCancelarMueble")?.addEventListener("click", function () {
    if (resumenItems.length > 0 && !confirm("¿Cancelar y borrar todo el presupuesto armado?")) return;

    /* Resetear constructor */
    document.getElementById("mueble-medida-total").value = "";
    const radioBase = document.querySelector('input[name="comp-mueble"][value="base"]');
    if (radioBase) radioBase.checked = true;
    lineaSeleccionada = null;
    document.querySelectorAll(".linea-card").forEach(function (x) { x.classList.remove("active"); });
    document.getElementById("sugerenciaMueble").innerHTML =
      `<i class="bi bi-info-circle me-1"></i>Ingresá una medida para ver la sugerencia de armado.`;
    document.getElementById("builderDetalle").innerHTML =
      `<div class="text-muted small">Todavía no hay componentes calculados.</div>`;

    /* Vaciar resumen */
    resumenItems.length = 0;
    actualizarResumen();
  });

  /* ══════════════════════════════════════════════════════
     AGREGAR RECOMENDACIÓN AL RESUMEN
     Agrega el componente actual sin limpiar el constructor,
     permitiendo apilar varias medidas seguidas.
  ════════════════════════════════════════════════════ */
  document.getElementById("btnAgregarMueble")?.addEventListener("click", function () {
    if (!lineaSeleccionada) { alert("Elegí una línea."); return; }

    const medidaTotal = Number(document.getElementById("mueble-medida-total")?.value || 0);
    if (!medidaTotal) { alert("Ingresá la medida total."); return; }

    const base    = getMedidaBase(lineaSeleccionada, medidaTotal);
    const precios = window.PRECIOS_MUEBLES.find(function (x) {
      return x.linea === lineaSeleccionada && x.medida === base;
    });
    if (!base || !precios) { alert("No se pudo calcular el mueble."); return; }

    const comp       = document.querySelector('input[name="comp-mueble"]:checked')?.value;
    if (!comp) { alert("Seleccioná un tipo de componente."); return; }

    const diferencia = Math.max(0, medidaTotal - base);
    let subtotalMueble = 0;
    const partes       = [];

    if (comp === "base") {
      subtotalMueble += Number(precios.base || 0);
      partes.push("Mueble " + base + " cm");
    }
    if (comp === "alacena") {
      subtotalMueble += Number(precios.alacena || 0);
      partes.push("Alacena " + base + " cm");
    }
    if (comp === "inox") {
      subtotalMueble += Number(precios.inox || 0);
      partes.push("Mesada inox " + base + " cm");
    }
    if (diferencia > 0) {
      subtotalMueble += diferencia * 1000;
      partes.push("Ajuste " + diferencia + " cm");
    }

    if (!partes.length) { alert("Seleccioná al menos un componente."); return; }

    const linNombre = lineaSeleccionada.charAt(0).toUpperCase() + lineaSeleccionada.slice(1);
    resumenItems.push({
      tipo:        "manual",
      descripcion: linNombre + " - " + partes.join(" + "),
      cantidad:    1,
      metros:      null,
      subtotal:    subtotalMueble
    });

    actualizarResumen();
  });

  /* ══════════════════════════════════════════════════════
     ADICIONALES
  ════════════════════════════════════════════════════ */
  document.addEventListener("click", function (e) {
    const btn = e.target.closest(".btn-add-adicional");
    /* Solo actuar sobre adicionales del presupuestador (no de cfg) */
    if (!btn || btn.closest("#formConfig")) return;

    const nombre     = btn.dataset.nombre;
    const precio     = Number(btn.dataset.precio || 0);
    const porcentaje = Number(btn.dataset.porcentaje || 0);

    let subtotal = precio;
    if (porcentaje > 0) {
      const subtotalActual = resumenItems.reduce(function (acc, x) {
        return acc + Number(x.subtotal || 0);
      }, 0);
      subtotal = subtotalActual * (porcentaje / 100);
    }

    resumenItems.push({ tipo: "manual", descripcion: nombre, cantidad: 1, metros: null, subtotal });
    actualizarResumen();
  });

  /* Dibuja el resumen inicial (vacío) */
  actualizarResumen();

});

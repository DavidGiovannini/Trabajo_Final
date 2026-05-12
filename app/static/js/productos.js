/* =========================================================
   productos.js — Lógica de la vista Productos
========================================================= */

function fmtPrecio(n) {
  return "$" + Number(n).toLocaleString("es-AR", { maximumFractionDigits: 0 });
}

/* ══════════════════════════════════════════════════════
   TOOLBAR DE ACTUALIZACIÓN DE PRECIOS (estilo configuración)
════════════════════════════════════════════════════ */
(function () {
  const inputPct    = document.getElementById("inputPctProd");
  const btnAplicar  = document.getElementById("btnAplicarPctProd");
  const btnReset    = document.getElementById("btnResetPctProd");
  const btnGuardar  = document.getElementById("btnGuardarPctProd");
  const pctAcciones = document.getElementById("pctAcciones");

  btnAplicar?.addEventListener("click", function () {
    const pct = parseFloat(inputPct?.value);
    if (!pct) { alert("Ingresá un porcentaje."); return; }
    const mult = 1 + pct / 100;

    document.querySelectorAll(".prod-card-price").forEach(function (el) {
      const original = Number(el.dataset.precioOriginal || 0);
      const nuevo    = Math.round(original * mult);
      el.dataset.precioActual = nuevo;
      el.textContent = fmtPrecio(nuevo);
    });

    pctAcciones?.classList.remove("d-none");
    pctAcciones?.classList.add("d-flex");
  });

  btnReset?.addEventListener("click", function () {
    document.querySelectorAll(".prod-card-price").forEach(function (el) {
      const original = Number(el.dataset.precioOriginal || 0);
      delete el.dataset.precioActual;
      el.textContent = fmtPrecio(original);
    });
    if (inputPct) inputPct.value = "";
    pctAcciones?.classList.add("d-none");
    pctAcciones?.classList.remove("d-flex");
  });

  btnGuardar?.addEventListener("click", async function () {
    const items = [];
    document.querySelectorAll(".prod-card-price").forEach(function (el) {
      const pid    = el.dataset.pid;
      const precio = Number(el.dataset.precioActual ?? el.dataset.precioOriginal ?? 0);
      if (pid) items.push({ id: parseInt(pid, 10), precio });
    });

    try {
      btnGuardar.disabled = true;
      btnGuardar.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Guardando...';

      const res  = await fetch("/productos/bulk_precio", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(items)
      });
      const data = await res.json();
      if (!data.ok) throw new Error();

      /* Confirmar nuevos precios como base */
      document.querySelectorAll(".prod-card-price").forEach(function (el) {
        if (el.dataset.precioActual) {
          el.dataset.precioOriginal = el.dataset.precioActual;
          delete el.dataset.precioActual;
        }
      });

      if (inputPct) inputPct.value = "";
      pctAcciones?.classList.add("d-none");
      pctAcciones?.classList.remove("d-flex");
      btnGuardar.innerHTML = '<i class="bi bi-check-lg me-1"></i>Guardar cambios';
      btnGuardar.disabled  = false;

    } catch (_) {
      alert("Error al guardar los precios.");
      btnGuardar.innerHTML = '<i class="bi bi-check-lg me-1"></i>Guardar cambios';
      btnGuardar.disabled  = false;
    }
  });
})();

/* ══════════════════════════════════════════════════════
   EDITAR PRECIO INLINE (lápiz → tilde → guarda vía AJAX)
════════════════════════════════════════════════════ */
document.addEventListener("click", async function (e) {
  const btn = e.target.closest(".btn-precio-edit");
  if (!btn) return;

  const card      = btn.closest(".prod-card");
  const priceSpan = card.querySelector(".prod-card-price");
  const editWrap  = card.querySelector(".prod-precio-edit-wrap");
  const input     = card.querySelector(".prod-precio-input");
  const pid       = btn.dataset.pid;
  const editing   = btn.classList.contains("is-editing");

  if (!editing) {
    /* ── Entrar en modo edición ── */
    const current = Number(priceSpan.dataset.precioActual ?? priceSpan.dataset.precioOriginal ?? 0);
    input.value = current;
    priceSpan.classList.add("d-none");
    editWrap.classList.remove("d-none");
    btn.classList.add("is-editing");
    btn.querySelector("i").className = "bi bi-check2";
    input.focus();
    input.select();

  } else {
    /* ── Guardar ── */
    const nuevo = parseFloat(input.value);
    if (isNaN(nuevo) || nuevo < 0) { alert("Ingresá un precio válido."); return; }

    try {
      btn.disabled = true;

      const res  = await fetch("/productos/" + pid + "/precio", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ precio: nuevo })
      });
      const data = await res.json();
      if (!data.ok) throw new Error();

      /* Actualizar display y atributos */
      priceSpan.textContent            = fmtPrecio(nuevo);
      priceSpan.dataset.precioOriginal = nuevo;
      delete priceSpan.dataset.precioActual;

      /* Salir de modo edición */
      editWrap.classList.add("d-none");
      priceSpan.classList.remove("d-none");
      btn.classList.remove("is-editing");
      btn.querySelector("i").className = "bi bi-pencil";
      btn.disabled = false;

    } catch (_) {
      alert("Error al guardar el precio.");
      btn.disabled = false;
    }
  }
});

/* ══════════════════════════════════════════════════════
   CHECKBOX "TIENE STOCK" en formulario de agregar
════════════════════════════════════════════════════ */
document.getElementById("checkStockForm")?.addEventListener("change", function () {
  const inp = document.getElementById("inputStockForm");
  inp.disabled = !this.checked;
  if (!this.checked) inp.value = "";
});

/* ══════════════════════════════════════════════════════
   FILTRO DE BÚSQUEDA DE MÓDULOS Y PRODUCTOS
════════════════════════════════════════════════════ */
document.getElementById("filtroProd")?.addEventListener("input", function () {
  const txt = this.value.toLowerCase().trim();

  document.querySelectorAll(".module-group").forEach(function (grupo) {
    const tipoGrupo = grupo.dataset.grupo || "";
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
        const btn  = grupo.querySelector(".module-toggle");
        if (body) body.classList.add("show");
        if (btn)  btn.setAttribute("aria-expanded", "true");
      }
    } else {
      grupo.style.display = "";
    }
  });
});

/* ══════════════════════════════════════════════════════
   EDITAR STOCK INLINE
════════════════════════════════════════════════════ */

/* Muestra el formulario inline y oculta los botones normales */
document.querySelectorAll(".stock-edit-btn").forEach(function (btn) {
  btn.addEventListener("click", function () {
    const pid = this.dataset.pid;
    document.getElementById("stockForm" + pid).classList.remove("d-none");
    this.closest(".d-flex").classList.add("d-none");
  });
});

/* Cancela la edición sin guardar */
document.querySelectorAll(".stock-cancel-btn").forEach(function (btn) {
  btn.addEventListener("click", function () {
    const pid = this.dataset.pid;
    document.getElementById("stockForm" + pid).classList.add("d-none");
    this.closest(".prod-card-footer").querySelector(".d-flex").classList.remove("d-none");
  });
});

/* Guarda el nuevo stock vía AJAX y actualiza el badge */
document.querySelectorAll(".stock-save-btn").forEach(function (btn) {
  btn.addEventListener("click", async function () {
    const pid        = this.dataset.pid;
    const form       = document.getElementById("stockForm" + pid);
    const nuevoStock = parseInt(form.querySelector(".stock-edit-input").value, 10);

    if (isNaN(nuevoStock) || nuevoStock < 0) {
      alert("Ingresá un número válido mayor o igual a 0.");
      return;
    }

    try {
      const res  = await fetch("/productos/" + pid + "/stock", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ stock: nuevoStock })
      });
      const data = await res.json();
      if (!data.ok) throw new Error();

      const card  = form.closest(".producto-item");
      const badge = card.querySelector(".prod-stock-badge");
      const valEl = card.querySelector(".stock-val");
      if (valEl) valEl.textContent = data.stock;

      if (badge) {
        badge.classList.remove("d-none");
        badge.classList.toggle("prod-stock-ok",  data.stock > 0);
        badge.classList.toggle("prod-stock-out", data.stock <= 0);
      }

      form.classList.add("d-none");
      form.closest(".prod-card-footer").querySelector(".d-flex").classList.remove("d-none");

    } catch (_) {
      alert("Error al guardar el stock.");
    }
  });
});

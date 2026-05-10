/* =========================================================
   productos.js — Lógica de la vista Productos
========================================================= */

/* ── Checkbox "Tiene stock" habilita/deshabilita el input ─ */
document.getElementById("checkStockForm")?.addEventListener("change", function () {
  const inp = document.getElementById("inputStockForm");
  inp.disabled = !this.checked;
  if (!this.checked) inp.value = "";
});

/* ── Filtro de búsqueda de módulos y productos ─────────── */
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
      /* Expande automáticamente el módulo si tiene resultados */
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

/* ── Editar stock inline ────────────────────────────────── */

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
    this.closest(".card-footer").querySelector(".d-flex").classList.remove("d-none");
  });
});

/* Guarda el nuevo stock vía AJAX y actualiza el badge en pantalla */
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

      /* Actualizar badge de stock sin recargar la página */
      const card  = form.closest(".producto-item");
      const badge = card.querySelector(".stock-badge");
      const valEl = card.querySelector(".stock-val");
      if (valEl) valEl.textContent = data.stock;

      if (badge) {
        badge.classList.remove("d-none");
        if (data.stock > 0) {
          badge.style.background = "rgba(25,135,84,.1)";
          badge.style.border     = "1px solid rgba(25,135,84,.3)";
          badge.style.color      = "#157347";
        } else {
          badge.style.background = "rgba(220,53,69,.1)";
          badge.style.border     = "1px solid rgba(220,53,69,.3)";
          badge.style.color      = "#b02a37";
        }
      }

      /* Cerrar formulario y mostrar botones normales */
      form.classList.add("d-none");
      form.closest(".card-footer").querySelector(".d-flex").classList.remove("d-none");

    } catch (_) {
      alert("Error al guardar el stock.");
    }
  });
});

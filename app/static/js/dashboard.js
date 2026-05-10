/* =========================================================
   dashboard.js — Lógica del Dashboard
   Requiere: window.DASHBOARD_DATA definido en el template
   con los datos pasados desde Flask.
========================================================= */

/* ── Gráfico de dona: distribución por estado ($) ───────
   Usa DASHBOARD_DATA.totales { pendiente, en_curso, finalizado }
──────────────────────────────────────────────────────── */
(function () {
  const d = window.DASHBOARD_DATA;
  const totalGeneral = d.total_pendiente + d.total_en_curso + d.total_finalizado;

  const graficoDona = new Chart(document.getElementById("graficoDona"), {
    type: "doughnut",
    data: {
      labels: ["Pendientes", "En curso", "Finalizados"],
      datasets: [{
        data: [d.total_pendiente, d.total_en_curso, d.total_finalizado],
        backgroundColor: ["#4a4a4a", "#c46200", "#0b2a4a"],
        borderWidth: 2
      }]
    },
    options: {
      cutout: "65%",
      plugins: {
        legend: { position: "bottom" },
        tooltip: {
          callbacks: {
            /* Muestra valor en $ y porcentaje sobre el total */
            label: function (context) {
              const value      = Number(context.raw || 0);
              const percentage = totalGeneral > 0
                ? ((value / totalGeneral) * 100).toFixed(1)
                : "0.0";
              return context.label + ": $" + value.toLocaleString() + " (" + percentage + "%)";
            }
          }
        }
      },
      animation: {
        animateRotate: true,
        animateScale: true,
        duration: 1200,
        easing: "easeOutQuart"
      },
      responsive: true,
      maintainAspectRatio: false
    },
    /* Plugin inline que dibuja el total en el centro de la dona */
    plugins: [{
      id: "centerText",
      beforeDraw: function (chart) {
        const { ctx, chartArea } = chart;
        const centerX = (chartArea.left + chartArea.right) / 2;
        const centerY = (chartArea.top  + chartArea.bottom) / 2;
        ctx.save();
        ctx.font = "bold 22px sans-serif";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillStyle = "#333";
        ctx.fillText("$" + Number(totalGeneral).toLocaleString(), centerX, centerY);
        ctx.restore();
      }
    }]
  });

  /* Clic en un segmento de la dona → filtrar pedidos por estado */
  document.getElementById("graficoDona").addEventListener("click", function (evt) {
    const points = graficoDona.getElementsAtEventForMode(evt, "nearest", { intersect: true }, true);
    if (!points.length) return;
    const estado = ["PENDIENTE", "EN_CURSO", "FINALIZADO"][points[0].index];
    window.location.href = "/pedidos?estado=" + estado;
  });
})();

/* ── Gráfico de línea: ventas de los últimos 7 días ─────
   Usa DASHBOARD_DATA.serie_labels / serie_totales
──────────────────────────────────────────────────────── */
(function () {
  const d = window.DASHBOARD_DATA;
  new Chart(document.getElementById("graficoLinea"), {
    type: "line",
    data: {
      labels: d.serie_labels,
      datasets: [{
        label: "Total $",
        data: d.serie_totales,
        borderColor: "#0b2a4a",
        backgroundColor: "rgba(11,42,74,0.1)",
        tension: 0.3,
        fill: true
      }]
    },
    options: { responsive: true, maintainAspectRatio: false }
  });
})();

/* ── Gráfico de barras: productos más vendidos ────────
   Usa DASHBOARD_DATA.productos_labels / productos_cantidades
──────────────────────────────────────────────────────── */
(function () {
  const d = window.DASHBOARD_DATA;
  new Chart(document.getElementById("graficoBarras"), {
    type: "bar",
    data: {
      labels: d.productos_labels,
      datasets: [{
        label: "Cantidad",
        data: d.productos_cantidades,
        backgroundColor: "#c46200"
      }]
    },
    options: {
      indexAxis: "y",
      plugins: { legend: { display: false } },
      responsive: true,
      maintainAspectRatio: false
    }
  });
})();

/* ── Navegación del carrusel de gráficos ─────────────── */
document.addEventListener("DOMContentLoaded", function () {
  const shell = document.querySelector(".charts-shell");
  if (!shell) return;

  const track = shell.querySelector(".charts-track");
  const btnL  = shell.querySelector(".charts-nav.left");
  const btnR  = shell.querySelector(".charts-nav.right");

  /* Calcula el ancho de un slide + gap para el scroll */
  function slideWidth() {
    const slide = track.querySelector(".charts-slide");
    if (!slide) return 520;
    const gap = parseInt(getComputedStyle(track).gap || "16", 10);
    return slide.getBoundingClientRect().width + gap;
  }

  btnL?.addEventListener("click", function () {
    track.scrollBy({ left: -slideWidth(), behavior: "smooth" });
  });

  btnR?.addEventListener("click", function () {
    track.scrollBy({ left: slideWidth(), behavior: "smooth" });
  });
});

/* ── Filtros de la tabla de pedidos (modal expandido) ── */
(function () {
  const buscarInput  = document.getElementById("buscarCliente");
  const estadoSelect = document.getElementById("filtroEstado");
  const tablaBody    = document.querySelector("#modalTablaExpandida tbody");

  if (!buscarInput || !estadoSelect || !tablaBody) return;

  /* Recarga las filas de la tabla vía AJAX con filtros aplicados */
  async function cargarPedidos() {
    const estado  = estadoSelect.value;
    const cliente = buscarInput.value;

    const response = await fetch("/api/pedidos?estado=" + estado + "&cliente=" + cliente);
    const data     = await response.json();

    tablaBody.innerHTML = "";

    if (!data.pedidos.length) {
      tablaBody.innerHTML = `
        <tr>
          <td colspan="8" class="text-center text-muted py-4">
            <i class="bi bi-inbox" style="font-size:1.5rem;opacity:.3;display:block;margin-bottom:6px;"></i>
            No se encontraron pedidos.
          </td>
        </tr>`;
      return;
    }

    data.pedidos.forEach(function (p) {
      let badge = "";
      if (p.estado === "PENDIENTE")  badge = `<span class="badge bg-warning text-dark rounded-pill">Pendiente</span>`;
      if (p.estado === "EN_CURSO")   badge = `<span class="badge bg-secondary rounded-pill">En curso</span>`;
      if (p.estado === "FINALIZADO") badge = `<span class="badge bg-success rounded-pill">Finalizado</span>`;

      tablaBody.innerHTML += `
        <tr>
          <td class="text-muted small">#${p.id}</td>
          <td class="fw-semibold">${p.cliente}</td>
          <td>${p.forma_pago}</td>
          <td>${p.sena}</td>
          <td class="text-muted">${p.telefono}</td>
          <td>${badge}</td>
          <td class="fw-bold text-success">$${p.total.toFixed(2)}</td>
          <td>
            <button class="btn btn-outline-primary btn-sm" style="border-radius:8px;"
                    data-pedido-open="${p.id}">Ver</button>
          </td>
        </tr>`;
    });
  }

  estadoSelect.addEventListener("change", cargarPedidos);

  /* Debounce en el input de búsqueda para no disparar en cada tecla */
  buscarInput.addEventListener("input", function () {
    clearTimeout(this.delay);
    this.delay = setTimeout(cargarPedidos, 300);
  });

  /* Carga inicial cuando se abre el modal */
  document.getElementById("modalTablaExpandida")
    .addEventListener("shown.bs.modal", cargarPedidos);
})();

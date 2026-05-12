/* =========================================================
   dashboard.js
   Requiere: window.DASHBOARD_DATA definido en el template
========================================================= */

const d = window.DASHBOARD_DATA;

function fmtMoney(n) {
  return "$" + Number(n || 0).toLocaleString("es-AR", { maximumFractionDigits: 0 });
}

/* ── Estado compartido de filtros ────────────────────────── */
let donaMode       = "pesos"; // "pesos" | "cant"
let currentPeriodo = "7";     // "7" | "30" | "90"


/* ══════════════════════════════════════════════════════════
   PLUGIN: número en el centro de la dona
   Se define como variable para reutilizarlo en el chart
   expandido sin duplicar código.
══════════════════════════════════════════════════════════ */
const centerTextPlugin = {
  id: "centerText",
  beforeDraw: function (chart) {
    const { ctx, chartArea } = chart;
    if (!chartArea) return;
    const cx = (chartArea.left + chartArea.right) / 2;
    const cy = (chartArea.top + chartArea.bottom) / 2;
    ctx.save();
    const data  = chart.data.datasets[0].data;
    const total = data.reduce(function (a, b) { return a + b; }, 0);
    const label = donaMode === "pesos" ? fmtMoney(total) : total + " ped.";
    ctx.font         = "bold 18px sans-serif";
    ctx.textAlign    = "center";
    ctx.textBaseline = "middle";
    ctx.fillStyle    = "#1a1a2e";
    ctx.fillText(label, cx, cy);
    ctx.restore();
  }
};


/* ══════════════════════════════════════════════════════════
   GRÁFICO DONA — distribución por estado
══════════════════════════════════════════════════════════ */
function buildDonaData(mode) {
  if (mode === "pesos") {
    return {
      labels: ["Pendientes", "En curso", "Finalizados"],
      datasets: [{ data: [d.total_pendiente, d.total_en_curso, d.total_finalizado], backgroundColor: ["#f59e0b", "#4a4a4a", "#0b2a4a"], borderWidth: 2, borderColor: "#fff" }]
    };
  } else {
    return {
      labels: ["Pendientes", "En curso", "Finalizados"],
      datasets: [{ data: [d.cant_pendiente, d.cant_en_curso, d.cant_finalizado], backgroundColor: ["#f59e0b", "#4a4a4a", "#0b2a4a"], borderWidth: 2, borderColor: "#fff" }]
    };
  }
}

function buildDonaOpts() {
  return {
    cutout: "65%",
    plugins: {
      legend: { position: "bottom", labels: { boxWidth: 12, padding: 14, font: { size: 12 } } },
      tooltip: {
        callbacks: {
          label: function (ctx) {
            const val = Number(ctx.raw || 0);
            if (donaMode === "pesos") {
              const total = d.total_pendiente + d.total_en_curso + d.total_finalizado;
              const pct = total > 0 ? ((val / total) * 100).toFixed(1) : "0.0";
              return ctx.label + ": " + fmtMoney(val) + " (" + pct + "%)";
            } else {
              const total = d.cant_pendiente + d.cant_en_curso + d.cant_finalizado;
              const pct = total > 0 ? ((val / total) * 100).toFixed(1) : "0.0";
              return ctx.label + ": " + val + " pedidos (" + pct + "%)";
            }
          }
        }
      }
    },
    animation: { animateRotate: true, animateScale: true, duration: 900, easing: "easeOutQuart" },
    responsive: true,
    maintainAspectRatio: false
  };
}

const graficoDona = new Chart(document.getElementById("graficoDona"), {
  type:    "doughnut",
  data:    buildDonaData("pesos"),
  options: buildDonaOpts(),
  plugins: [centerTextPlugin]
});

document.getElementById("donaToglePesos")?.addEventListener("click", function () {
  donaMode = "pesos";
  graficoDona.data = buildDonaData("pesos");
  graficoDona.update();
  this.classList.add("active");
  document.getElementById("donaToggleCant")?.classList.remove("active");
  syncExpandedDona();
});

document.getElementById("donaToggleCant")?.addEventListener("click", function () {
  donaMode = "cant";
  graficoDona.data = buildDonaData("cant");
  graficoDona.update();
  this.classList.add("active");
  document.getElementById("donaToglePesos")?.classList.remove("active");
  syncExpandedDona();
});

/* Clic en segmento → filtrar pedidos */
document.getElementById("graficoDona")?.addEventListener("click", function (evt) {
  const pts = graficoDona.getElementsAtEventForMode(evt, "nearest", { intersect: true }, true);
  if (!pts.length) return;
  const estado = ["PENDIENTE", "EN_CURSO", "FINALIZADO"][pts[0].index];
  window.location.href = "/pedidos?estado=" + estado;
});


/* ══════════════════════════════════════════════════════════
   GRÁFICO LÍNEA — pedidos por día
══════════════════════════════════════════════════════════ */
const lineaData = {
  "7":  { labels: d.serie_labels_7,  data: d.serie_cant_7  },
  "30": { labels: d.serie_labels_30, data: d.serie_cant_30 },
  "90": { labels: d.serie_labels_90, data: d.serie_cant_90 }
};

function buildLineaData(periodo) {
  const src = lineaData[periodo] || lineaData["7"];
  return {
    labels: src.labels,
    datasets: [{
      label: "Pedidos",
      data: src.data,
      borderColor: "#c46200",
      backgroundColor: "rgba(196,98,0,.08)",
      tension: 0.35,
      fill: true,
      pointRadius: periodo === "90" ? 0 : 3,
      pointBackgroundColor: "#c46200"
    }]
  };
}

function buildLineaOpts() {
  return {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: {
      y: { beginAtZero: true, ticks: { stepSize: 1, precision: 0 }, grid: { color: "rgba(0,0,0,.05)" } },
      x: { grid: { display: false }, ticks: { maxTicksLimit: 10, font: { size: 10 } } }
    }
  };
}

const graficoLinea = new Chart(document.getElementById("graficoLinea"), {
  type:    "line",
  data:    buildLineaData("7"),
  options: buildLineaOpts()
});

document.querySelectorAll("[data-periodo]").forEach(function (btn) {
  btn.addEventListener("click", function () {
    currentPeriodo = this.dataset.periodo;
    graficoLinea.data = buildLineaData(currentPeriodo);
    graficoLinea.update();
    document.querySelectorAll("[data-periodo]").forEach(function (b) { b.classList.remove("active"); });
    this.classList.add("active");
    syncExpandedLinea();
  });
});


/* ══════════════════════════════════════════════════════════
   GRÁFICO BARRAS — productos más vendidos
══════════════════════════════════════════════════════════ */
const graficoBarras = new Chart(document.getElementById("graficoBarras"), {
  type: "bar",
  data: {
    labels: d.productos_labels,
    datasets: [{ label: "Cantidad", data: d.productos_cantidades, backgroundColor: "#0b2a4a", borderRadius: 4 }]
  },
  options: {
    indexAxis: "y",
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: {
      x: { beginAtZero: true, ticks: { stepSize: 1, precision: 0 }, grid: { color: "rgba(0,0,0,.05)" } },
      y: { grid: { display: false } }
    }
  }
});


/* ══════════════════════════════════════════════════════════
   GRÁFICO MESES — evolución mensual
══════════════════════════════════════════════════════════ */
const graficoMeses = new Chart(document.getElementById("graficoMeses"), {
  type: "bar",
  data: {
    labels: d.meses_labels,
    datasets: [{
      label: "Pedidos",
      data: d.meses_cant,
      backgroundColor: function (ctx) {
        return ctx.dataIndex === d.meses_cant.length - 1 ? "#c46200" : "rgba(11,42,74,.75)";
      },
      borderRadius: 5
    }]
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: {
      y: { beginAtZero: true, ticks: { stepSize: 1, precision: 0 }, grid: { color: "rgba(0,0,0,.05)" } },
      x: { grid: { display: false } }
    }
  }
});


/* ══════════════════════════════════════════════════════════
   EXPAND CHART MODAL
   Abre el gráfico en pantalla completa con sus filtros.
══════════════════════════════════════════════════════════ */
let expandedChart  = null;
let expandedTarget = null;

const CHART_META = {
  cardDona: {
    title:      "Distribución por Estado",
    filterType: "dona",
    clone:      function () { return buildDonaData(donaMode); },
    type:       "doughnut",
    buildOpts:  buildDonaOpts,
    plugins:    [centerTextPlugin]
  },
  cardLinea: {
    title:      "Pedidos por día",
    filterType: "linea",
    clone:      function () { return buildLineaData(currentPeriodo); },
    type:       "line",
    buildOpts:  buildLineaOpts,
    plugins:    []
  },
  cardBarras: {
    title:      "Productos más vendidos",
    filterType: null,
    clone:      function () { return graficoBarras.data; },
    type:       "bar",
    buildOpts:  function () { return JSON.parse(JSON.stringify(graficoBarras.options)); },
    plugins:    []
  },
  cardMeses: {
    title:      "Evolución mensual",
    filterType: null,
    clone:      function () { return graficoMeses.data; },
    type:       "bar",
    buildOpts:  function () { return JSON.parse(JSON.stringify(graficoMeses.options)); },
    plugins:    []
  }
};

/* Genera el HTML de los filtros según tipo */
function buildFilterHTML(filterType) {
  if (filterType === "dona") {
    return `<div class="btn-group btn-group-sm" role="group">
      <button type="button" class="btn btn-chart-toggle-modal ${donaMode === "pesos" ? "active" : ""}" data-modal-filter="dona-pesos" title="Por monto $">$</button>
      <button type="button" class="btn btn-chart-toggle-modal ${donaMode === "cant"  ? "active" : ""}" data-modal-filter="dona-cant"  title="Por cantidad">#</button>
    </div>`;
  }
  if (filterType === "linea") {
    return `<div class="btn-group btn-group-sm" role="group">
      <button type="button" class="btn btn-chart-toggle-modal ${currentPeriodo === "7"  ? "active" : ""}" data-modal-filter="linea-7">7d</button>
      <button type="button" class="btn btn-chart-toggle-modal ${currentPeriodo === "30" ? "active" : ""}" data-modal-filter="linea-30">30d</button>
      <button type="button" class="btn btn-chart-toggle-modal ${currentPeriodo === "90" ? "active" : ""}" data-modal-filter="linea-90">90d</button>
    </div>`;
  }
  return "";
}

/* Maneja los clics en los filtros del modal expandido */
document.getElementById("modalExpandFilters")?.addEventListener("click", function (e) {
  const btn = e.target.closest("[data-modal-filter]");
  if (!btn || !expandedChart) return;

  const filter = btn.dataset.modalFilter;

  /* Actualizar estado activo en el modal */
  this.querySelectorAll("[data-modal-filter]").forEach(function (b) { b.classList.remove("active"); });
  btn.classList.add("active");

  if (filter === "dona-pesos") {
    donaMode = "pesos";
    expandedChart.data = buildDonaData("pesos");
    expandedChart.update();
    graficoDona.data = buildDonaData("pesos");
    graficoDona.update();
    document.getElementById("donaToglePesos")?.classList.add("active");
    document.getElementById("donaToggleCant")?.classList.remove("active");

  } else if (filter === "dona-cant") {
    donaMode = "cant";
    expandedChart.data = buildDonaData("cant");
    expandedChart.update();
    graficoDona.data = buildDonaData("cant");
    graficoDona.update();
    document.getElementById("donaToglePesos")?.classList.remove("active");
    document.getElementById("donaToggleCant")?.classList.add("active");

  } else if (filter.startsWith("linea-")) {
    currentPeriodo = filter.replace("linea-", "");
    expandedChart.data = buildLineaData(currentPeriodo);
    expandedChart.update();
    graficoLinea.data = buildLineaData(currentPeriodo);
    graficoLinea.update();
    document.querySelectorAll("[data-periodo]").forEach(function (b) {
      b.classList.toggle("active", b.dataset.periodo === currentPeriodo);
    });
  }
});

/* Sincroniza el chart expandido cuando se cambia el filtro en la tarjeta principal */
function syncExpandedDona() {
  if (!expandedChart || expandedTarget !== "cardDona") return;
  expandedChart.data = buildDonaData(donaMode);
  expandedChart.update();
  /* Actualiza el estado activo de los botones en el modal */
  const filtersEl = document.getElementById("modalExpandFilters");
  if (filtersEl) {
    filtersEl.querySelector("[data-modal-filter='dona-pesos']")?.classList.toggle("active", donaMode === "pesos");
    filtersEl.querySelector("[data-modal-filter='dona-cant']")?.classList.toggle("active",  donaMode === "cant");
  }
}

function syncExpandedLinea() {
  if (!expandedChart || expandedTarget !== "cardLinea") return;
  expandedChart.data = buildLineaData(currentPeriodo);
  expandedChart.update();
  const filtersEl = document.getElementById("modalExpandFilters");
  if (filtersEl) {
    filtersEl.querySelectorAll("[data-modal-filter]").forEach(function (b) {
      b.classList.toggle("active", b.dataset.modalFilter === "linea-" + currentPeriodo);
    });
  }
}

/* Botones de expandir */
document.querySelectorAll(".btn-expand").forEach(function (btn) {
  btn.addEventListener("click", function () {
    expandedTarget = this.dataset.target;
    const meta = CHART_META[expandedTarget];
    if (!meta) return;

    document.getElementById("modalChartTitle").textContent = meta.title;

    /* Inyectar filtros en el header del modal */
    const filtersEl = document.getElementById("modalExpandFilters");
    if (filtersEl) filtersEl.innerHTML = buildFilterHTML(meta.filterType);

    const modal = new bootstrap.Modal(document.getElementById("modalChartExpand"));
    modal.show();

    document.getElementById("modalChartExpand").addEventListener("shown.bs.modal", function handler() {
      this.removeEventListener("shown.bs.modal", handler);
      if (expandedChart) { expandedChart.destroy(); expandedChart = null; }

      const opts = meta.buildOpts();
      opts.responsive        = true;
      opts.maintainAspectRatio = false;
      if (opts.animation) opts.animation.duration = 600;

      expandedChart = new Chart(document.getElementById("graficoExpanded"), {
        type:    meta.type,
        data:    meta.clone(),
        options: opts,
        plugins: meta.plugins
      });
    });

    document.getElementById("modalChartExpand").addEventListener("hidden.bs.modal", function handler() {
      this.removeEventListener("hidden.bs.modal", handler);
      if (expandedChart) { expandedChart.destroy(); expandedChart = null; }
      expandedTarget = null;
    });
  });
});


/* ══════════════════════════════════════════════════════════
   WIDGET PRÓXIMOS RECORDATORIOS
══════════════════════════════════════════════════════════ */
(function () {
  const wrap = document.getElementById("widgetProximosWrap");
  const body = document.getElementById("widgetProximosBody");
  if (!wrap || !body) return;

  const COLOR_BG = {
    azul: "#0b2a4a", naranja: "#c46200",
    verde: "#15803d", rojo: "#dc2626", gris: "#6b7280"
  };
  const DIAS_ES = ["Dom","Lun","Mar","Mié","Jue","Vie","Sáb"];

  fetch("/api/recordatorios/proximos")
    .then(function (r) { return r.json(); })
    .then(function (recs) {
      if (!recs.length) return;
      wrap.style.removeProperty("display");

      const hoyStr = new Date().toISOString().slice(0, 10);
      body.innerHTML = recs.map(function (r) {
        const fd   = new Date(r.fecha + "T00:00:00");
        const diff = Math.round((fd - new Date(hoyStr + "T00:00:00")) / 86400000);
        const label = diff === 0 ? "Hoy" : diff === 1 ? "Mañana"
                    : DIAS_ES[fd.getDay()] + " " + fd.getDate() + "/" + (fd.getMonth() + 1);
        const bg = COLOR_BG[r.color] || "#0b2a4a";
        return `
          <div class="d-flex align-items-center gap-3 py-2 border-bottom" style="border-color:rgba(0,0,0,.05)!important;">
            <div style="width:46px;height:46px;border-radius:10px;background:${bg};color:#fff;display:flex;flex-direction:column;align-items:center;justify-content:center;flex:0 0 46px;font-size:.68rem;font-weight:700;line-height:1.2;">
              <span>${fd.getDate()}</span>
              <span style="opacity:.75;">${["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"][fd.getMonth()]}</span>
            </div>
            <div class="flex-grow-1" style="min-width:0;">
              <div class="fw-semibold text-truncate" style="font-size:.88rem;">${escWgt(r.titulo)}</div>
              <div class="text-muted small">${label}${r.hora ? " · " + r.hora : ""}</div>
            </div>
            <a href="/calendario" class="btn btn-outline-secondary btn-sm" style="border-radius:8px;font-size:.75rem;flex-shrink:0;">Ver</a>
          </div>`;
      }).join("");
    })
    .catch(function () {});

  function escWgt(s) {
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }
})();


/* ══════════════════════════════════════════════════════════
   FILTROS TABLA MODAL (todos los pedidos)
══════════════════════════════════════════════════════════ */
(function () {
  const buscarInput  = document.getElementById("buscarCliente");
  const estadoSelect = document.getElementById("filtroEstado");
  const tablaBody    = document.querySelector("#modalTablaExpandida-body");

  if (!buscarInput || !estadoSelect || !tablaBody) return;

  async function cargarPedidos() {
    const estado  = estadoSelect.value;
    const cliente = buscarInput.value;
    const res  = await fetch("/api/pedidos?estado=" + estado + "&cliente=" + encodeURIComponent(cliente));
    const data = await res.json();
    tablaBody.innerHTML = "";
    if (!data.pedidos.length) {
      tablaBody.innerHTML = `<tr><td colspan="8" class="text-center text-muted py-4"><i class="bi bi-inbox" style="font-size:1.5rem;opacity:.3;display:block;margin-bottom:6px;"></i>No se encontraron pedidos.</td></tr>`;
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
          <td class="fw-bold text-success">${fmtMoney(p.total)}</td>
          <td><button class="btn btn-outline-primary btn-sm" style="border-radius:8px;" data-pedido-open="${p.id}">Ver</button></td>
        </tr>`;
    });
  }

  estadoSelect.addEventListener("change", cargarPedidos);
  buscarInput.addEventListener("input", function () {
    clearTimeout(this._delay);
    this._delay = setTimeout(cargarPedidos, 300);
  });
  document.getElementById("modalTablaExpandida")
    ?.addEventListener("shown.bs.modal", cargarPedidos);
})();

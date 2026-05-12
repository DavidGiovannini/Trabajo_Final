/* =========================================================
   dashboard.js
   Requiere: window.DASHBOARD_DATA definido en el template
========================================================= */

const d = window.DASHBOARD_DATA;

function fmtMoney(n) {
  return "$" + Number(n || 0).toLocaleString("es-AR", { maximumFractionDigits: 0 });
}

/* ── Gráfico dona: distribución por estado ──────────────── */
let donaMode = "pesos"; // "pesos" | "cant"

const graficoDona = new Chart(document.getElementById("graficoDona"), {
  type: "doughnut",
  data: buildDonaData("pesos"),
  options: {
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
  },
  plugins: [{
    id: "centerText",
    beforeDraw: function (chart) {
      const { ctx, chartArea } = chart;
      const cx = (chartArea.left + chartArea.right) / 2;
      const cy = (chartArea.top + chartArea.bottom) / 2;
      ctx.save();
      const data = chart.data.datasets[0].data;
      const total = data.reduce((a, b) => a + b, 0);
      const label = donaMode === "pesos" ? fmtMoney(total) : total + " ped.";
      ctx.font = "bold 18px sans-serif";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillStyle = "#1a1a2e";
      ctx.fillText(label, cx, cy);
      ctx.restore();
    }
  }]
});

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

document.getElementById("donaToglePesos")?.addEventListener("click", function () {
  donaMode = "pesos";
  graficoDona.data = buildDonaData("pesos");
  graficoDona.update();
  this.classList.add("active");
  document.getElementById("donaToggleCant")?.classList.remove("active");
});

document.getElementById("donaToggleCant")?.addEventListener("click", function () {
  donaMode = "cant";
  graficoDona.data = buildDonaData("cant");
  graficoDona.update();
  this.classList.add("active");
  document.getElementById("donaToglePesos")?.classList.remove("active");
});

/* Clic segmento dona → filtrar pedidos */
document.getElementById("graficoDona")?.addEventListener("click", function (evt) {
  const pts = graficoDona.getElementsAtEventForMode(evt, "nearest", { intersect: true }, true);
  if (!pts.length) return;
  const estado = ["PENDIENTE", "EN_CURSO", "FINALIZADO"][pts[0].index];
  window.location.href = "/pedidos?estado=" + estado;
});


/* ── Gráfico línea: pedidos por día ─────────────────────── */
const lineaData = {
  "7":  { labels: d.serie_labels_7,  data: d.serie_cant_7  },
  "30": { labels: d.serie_labels_30, data: d.serie_cant_30 },
  "90": { labels: d.serie_labels_90, data: d.serie_cant_90 }
};

const graficoLinea = new Chart(document.getElementById("graficoLinea"), {
  type: "line",
  data: buildLineaData("7"),
  options: {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: {
      y: { beginAtZero: true, ticks: { stepSize: 1, precision: 0 }, grid: { color: "rgba(0,0,0,.05)" } },
      x: { grid: { display: false }, ticks: { maxTicksLimit: 10, font: { size: 10 } } }
    }
  }
});

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

document.querySelectorAll("[data-periodo]").forEach(function (btn) {
  btn.addEventListener("click", function () {
    const p = this.dataset.periodo;
    graficoLinea.data = buildLineaData(p);
    graficoLinea.update();
    document.querySelectorAll("[data-periodo]").forEach(b => b.classList.remove("active"));
    this.classList.add("active");
  });
});


/* ── Gráfico barras: productos más vendidos ─────────────── */
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
    scales: { x: { beginAtZero: true, ticks: { stepSize: 1, precision: 0 }, grid: { color: "rgba(0,0,0,.05)" } }, y: { grid: { display: false } } }
  }
});


/* ── Gráfico evolución mensual ──────────────────────────── */
const graficoMeses = new Chart(document.getElementById("graficoMeses"), {
  type: "bar",
  data: {
    labels: d.meses_labels,
    datasets: [{
      label: "Pedidos",
      data: d.meses_cant,
      backgroundColor: function (ctx) {
        const i = ctx.dataIndex;
        return i === d.meses_cant.length - 1 ? "#c46200" : "rgba(11,42,74,.75)";
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


/* ── Expand chart modal ─────────────────────────────────── */
let expandedChart = null;

const CHART_META = {
  cardDona:   { title: "Distribución por Estado", clone: () => buildDonaData(donaMode),   type: "doughnut", opts: () => graficoDona.options   },
  cardLinea:  { title: "Pedidos por día",          clone: () => graficoLinea.data,         type: "line",     opts: () => graficoLinea.options   },
  cardBarras: { title: "Productos más vendidos",   clone: () => graficoBarras.data,        type: "bar",      opts: () => graficoBarras.options  },
  cardMeses:  { title: "Evolución mensual",        clone: () => graficoMeses.data,         type: "bar",      opts: () => graficoMeses.options   }
};

document.querySelectorAll(".btn-expand").forEach(function (btn) {
  btn.addEventListener("click", function () {
    const target = this.dataset.target;
    const meta   = CHART_META[target];
    if (!meta) return;
    document.getElementById("modalChartTitle").textContent = meta.title;
    const modal = new bootstrap.Modal(document.getElementById("modalChartExpand"));
    modal.show();
    document.getElementById("modalChartExpand").addEventListener("shown.bs.modal", function handler() {
      this.removeEventListener("shown.bs.modal", handler);
      if (expandedChart) { expandedChart.destroy(); expandedChart = null; }
      const opts = JSON.parse(JSON.stringify(meta.opts()));
      opts.responsive        = true;
      opts.maintainAspectRatio = false;
      if (opts.animation) opts.animation.duration = 600;
      expandedChart = new Chart(document.getElementById("graficoExpanded"), {
        type: meta.type,
        data: meta.clone(),
        options: opts
      });
    });
    document.getElementById("modalChartExpand").addEventListener("hidden.bs.modal", function handler() {
      this.removeEventListener("hidden.bs.modal", handler);
      if (expandedChart) { expandedChart.destroy(); expandedChart = null; }
    });
  });
});


/* ── Widget próximos recordatorios ─────────────────────── */
(function () {
  const wrap = document.getElementById("widgetProximosWrap");
  const body = document.getElementById("widgetProximosBody");
  if (!wrap || !body) return;

  const COLOR_BG = {
    azul:    "#0b2a4a", naranja: "#c46200",
    verde:   "#15803d", rojo:    "#dc2626", gris: "#6b7280"
  };
  const DIAS_ES = ["Dom","Lun","Mar","Mié","Jue","Vie","Sáb"];

  fetch("/api/recordatorios/proximos")
    .then(r => r.json())
    .then(recs => {
      if (!recs.length) return;
      wrap.style.removeProperty("display");

      const hoyStr = new Date().toISOString().slice(0, 10);
      body.innerHTML = recs.map(r => {
        const fd    = new Date(r.fecha + "T00:00:00");
        const diff  = Math.round((fd - new Date(hoyStr + "T00:00:00")) / 86400000);
        const label = diff === 0 ? "Hoy" : diff === 1 ? "Mañana" : DIAS_ES[fd.getDay()] + " " + fd.getDate() + "/" + (fd.getMonth()+1);
        const bg    = COLOR_BG[r.color] || "#0b2a4a";
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
    .catch(() => {});

  function escWgt(s) {
    return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
  }
})();

/* ── Filtros tabla modal ────────────────────────────────── */
(function () {
  const buscarInput  = document.getElementById("buscarCliente");
  const estadoSelect = document.getElementById("filtroEstado");
  const tablaBody    = document.querySelector("#modalTablaExpandida-body");

  if (!buscarInput || !estadoSelect || !tablaBody) return;

  async function cargarPedidos() {
    const estado  = estadoSelect.value;
    const cliente = buscarInput.value;
    const res     = await fetch("/api/pedidos?estado=" + estado + "&cliente=" + encodeURIComponent(cliente));
    const data    = await res.json();
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

/* =========================================================
   base.js — Scripts globales cargados en todas las páginas
========================================================= */

/* ── Modal de advertencia: cambio de precio vs pedidos activos ──────────────
   Uso:
     mostrarModalPrecio({
       mensaje : "<p>...</p>",    // HTML del cuerpo
       labelSi : "Sí, actualizar",
       labelNo : "No, cancelar",
       onSi    : function() { ... },   // callback botón Sí
       onNo    : function() { ... }    // callback botón No (opcional)
     });
────────────────────────────────────────────────────────── */
window.mostrarModalPrecio = function (opts) {
  var cuerpo = document.getElementById("modalPreciosCuerpo");
  var btnSi  = document.getElementById("modalPreciosSi");
  var btnNo  = document.getElementById("modalPreciosNo");
  if (!cuerpo || !btnSi || !btnNo) return;

  cuerpo.innerHTML  = opts.mensaje  || "";
  btnSi.textContent = opts.labelSi  || "Sí";
  btnNo.textContent = opts.labelNo  || "No";

  /* Reemplazar nodos para limpiar listeners anteriores */
  var nSi = btnSi.cloneNode(true);
  var nNo = btnNo.cloneNode(true);
  btnSi.replaceWith(nSi);
  btnNo.replaceWith(nNo);

  var modal = new bootstrap.Modal(document.getElementById("modalPreciosPedidos"));

  nSi.addEventListener("click", function () {
    modal.hide();
    if (typeof opts.onSi === "function") opts.onSi();
  });
  nNo.addEventListener("click", function () {
    modal.hide();
    if (typeof opts.onNo === "function") opts.onNo();
  });

  modal.show();
};

document.addEventListener("DOMContentLoaded", function () {

  /* ── Auto-cerrar alertas flash a los 3 segundos ──────── */
  setTimeout(function () {
    document.querySelectorAll(".alert").forEach(function (alertEl) {
      const bsAlert = new bootstrap.Alert(alertEl);
      bsAlert.close();
    });
  }, 3000);

  /* ── Marcar el link activo en la sidebar ─────────────── */
  const links = document.querySelectorAll(".sidebar-link");
  const path  = window.location.pathname;

  links.forEach(function (link) {
    const href = link.getAttribute("href");
    if (href && path.startsWith(href)) {
      link.classList.add("active");
    }
  });

  /* ── Expandir submenú si la ruta activa es un sub-link ─ */
  const subPaths    = ["/productos", "/configuracion"];
  const isSubActive = subPaths.some(function (p) { return path.startsWith(p); });

  if (isSubActive) {
    const collapse = document.getElementById("submenuProductos");
    const toggle   = document.querySelector('[data-bs-target="#submenuProductos"]');
    if (collapse) collapse.classList.add("show");
    if (toggle)   toggle.setAttribute("aria-expanded", "true");
    if (toggle)   toggle.classList.add("active");
  }

  /* ── Notificaciones del navegador: recordatorios de hoy ─ */
  if ("Notification" in window) {
    const disparar = function () {
      fetch("/api/recordatorios/hoy")
        .then(function (r) { return r.ok ? r.json() : []; })
        .then(function (recs) {
          recs.forEach(function (r) {
            const key = "notif_" + r.id + "_" + new Date().toDateString();
            if (sessionStorage.getItem(key)) return;
            sessionStorage.setItem(key, "1");
            new Notification("Recordatorio — S. Valvo y Cía", {
              body: (r.hora ? r.hora + " — " : "") + r.titulo + (r.descripcion ? "\n" + r.descripcion : ""),
              icon: "/static/img/logo.png",
              tag:  "rec-" + r.id
            });
          });
        })
        .catch(function () {});
    };

    if (Notification.permission === "granted") {
      disparar();
    } else if (Notification.permission !== "denied") {
      Notification.requestPermission().then(function (perm) {
        if (perm === "granted") disparar();
      });
    }
  }

});

/* =========================================================
   base.js — Scripts globales cargados en todas las páginas
========================================================= */

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

});

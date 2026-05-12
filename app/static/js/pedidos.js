/* ============================================================
   pedidos.js — Tablero Kanban de pedidos
   Dependencias: SortableJS (CDN), Bootstrap 5, pedido_modal.js
   ============================================================ */

document.addEventListener("DOMContentLoaded", () => {

  /* ---- Referencias al DOM ---- */
  const columns = document.querySelectorAll(".kanban-column");  // 3 columnas del kanban
  const trash   = document.getElementById("kanban-trash");      // zona de papelera inferior
  let pedidoDragging = null;  // referencia a la card que se está arrastrando actualmente

  /* ---- Muestra "columna vacía" cuando no quedan cards ---- */
  function refreshEmptyColumns() {
    columns.forEach(col => {
      col.classList.toggle("is-empty", !col.querySelector(".pedido-nueva"));
    });
  }

  /* ---- Poblar la fecha de creación de cada card desde data-created ---- */
  // El servidor renderiza la fecha en el atributo data-created; aquí la mostramos en el DOM
  document.querySelectorAll(".pedido-card").forEach(card => {
    const fecha = card.dataset.created;
    const el    = card.querySelector(".pedido-creado-fecha");
    if (el) el.textContent = fecha;
  });

  refreshEmptyColumns();

  /* ====================================================
     SortableJS: drag & drop entre las 3 columnas
     ==================================================== */
  columns.forEach(col => {
    new Sortable(col, {
      group:    "pedidos",          // mismo nombre = las columnas comparten el grupo
      animation: 150,
      draggable: ".pedido-nueva",   // solo las cards con esta clase son arrastrables
      handle:    ".pedido-header",  // el drag solo se inicia desde el header
      filter:    "button, .btn, a, input, select, textarea",
      preventOnFilter: true,        // un click en botón no inicia arrastre
      chosenClass: "sortable-chosen",
      dragClass:   "sortable-drag",

      /* Al iniciar arrastre: mostrar zona de papelera */
      onStart: (evt) => {
        pedidoDragging = evt.item;
        trash.classList.add("active");
      },

      /* Al soltar: actualizar estado en el servidor si cambió de columna */
      onEnd: async (evt) => {
        trash.classList.remove("active");
        trash.classList.remove("hover");
        pedidoDragging = null;

        const card      = evt.item;
        const pedidoId  = card.dataset.id;
        const newEstado = evt.to.id;  // el id del contenedor coincide con el nombre del estado

        refreshEmptyColumns();
        if (evt.from === evt.to) return;  // no cambió de columna → nada que guardar

        /* Actualizar clases de color en la card (borde + dot) */
        const estadoClass = "estado-" + newEstado.toLowerCase();
        card.classList.remove("estado-pendiente", "estado-en_curso", "estado-finalizado");
        card.classList.add(estadoClass);
        const titleWrap = card.querySelector(".pedido-title-wrap");
        if (titleWrap) {
          titleWrap.classList.remove("estado-pendiente", "estado-en_curso", "estado-finalizado");
          titleWrap.classList.add(estadoClass);
        }

        /* POST al backend para persistir el cambio de estado */
        try {
          const res = await fetch(`/pedidos/mover/${pedidoId}`, {
            method:  "POST",
            headers: { "Content-Type": "application/json" },
            body:    JSON.stringify({ estado: newEstado })
          });

          /* Si el servidor falló, devolver la card a la columna original */
          if (!res.ok) {
            evt.from.appendChild(card);
            refreshEmptyColumns();
            alert("Error al mover el pedido");
          }
        } catch (e) {
          evt.from.appendChild(card);
          refreshEmptyColumns();
          alert("Error al mover el pedido");
        }
      }
    });
  });

  /* ====================================================
     Toggle: colapsar / expandir el cuerpo de una card
     ==================================================== */
  // Delegar el click en el documento para cubrir cards generadas dinámicamente
  document.addEventListener("click", (e) => {
    const card = e.target.closest(".pedido-nueva");
    if (!card) return;

    /* Ignorar clicks sobre botones, links o cualquier control interactivo */
    if (e.target.closest("button, a, input, select, textarea, [data-pedido-open]")) return;

    const body = card.querySelector(".pedido-body");
    if (!body) return;

    /* Alternar clase de colapso y estado visual abierto/cerrado */
    body.classList.toggle("pedido-collapsed");
    card.classList.toggle("is-open");

    /* Rotar ícono chevron hacia arriba cuando está abierto */
    const icon = card.querySelector(".pedido-toggle i");
    if (icon) {
      icon.classList.toggle("bi-chevron-down");
      icon.classList.toggle("bi-chevron-up");
    }
  });

  /* ====================================================
     Zona de papelera: eliminar pedido arrastrando
     ==================================================== */

  /* Resaltar papelera cuando el drag nativo pasa encima */
  trash.addEventListener("dragover", (e) => {
    e.preventDefault();
    trash.classList.add("hover");
  });

  /* Quitar resaltado al salir de la zona */
  trash.addEventListener("dragleave", () => {
    trash.classList.remove("hover");
  });

  /* Al soltar sobre la papelera: confirmar y eliminar en el servidor */
  trash.addEventListener("drop", async (e) => {
    e.preventDefault();
    trash.classList.remove("hover");
    trash.classList.remove("active");

    if (!pedidoDragging) return;

    const card = pedidoDragging;
    const id   = card.dataset.id;
    pedidoDragging = null;

    if (!confirm("¿Eliminar este pedido?")) return;

    const res = await fetch(`/pedidos/eliminar/${id}`, { method: "POST" });
    if (!res.ok) { alert("No se pudo eliminar."); return; }

    /* Animación de desvanecido antes de quitar el nodo del DOM */
    card.style.transition = "all .2s ease";
    card.style.opacity    = "0";
    card.style.transform  = "scale(.9)";
    setTimeout(() => {
      card.remove();
      refreshEmptyColumns();
    }, 200);
  });

});

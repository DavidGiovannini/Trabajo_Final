/* ============================================================
   pedido_modal.js — Modal de detalle y pago de pedidos
   Incluido via partials/pedido_modal.html en dashboard y pedidos
   Dependencias: Bootstrap 5 (global via base.html)
   ============================================================ */

document.addEventListener("DOMContentLoaded", () => {

  /* ================================================================
     SECCIÓN 1 — REFERENCIAS GLOBALES DEL MODAL DE PEDIDO
     ================================================================ */

  const modalEl = document.getElementById("modalPedido");
  if (!modalEl) return;  // si no existe el modal en la página, salir

  const modal          = new bootstrap.Modal(modalEl);
  let pedidoActualId   = null;  // id del pedido que está abierto en el modal
  const badge          = document.getElementById("mp-estado-badge");


  /* ================================================================
     SECCIÓN 2 — EDICIÓN INLINE DE CAMPOS DEL PEDIDO
     Cada campo (dirección, teléfono, email, observaciones) tiene
     un span de lectura y un input oculto; se alternan al editar
     ================================================================ */

  /* Mapa campo → [id-span-lectura, id-input-edición] */
  const CAMPO_MAP = {
    pais:          ["mp-pais-view",       "mp-pais-input"],
    localidad:     ["mp-localidad-view",  "mp-localidad-input"],
    codigo_postal: ["mp-cp-view",         "mp-cp-input"],
    barrio:        ["mp-barrio-view",     "mp-barrio-input"],
    direccion:     ["mp-domicilio-view",  "mp-domicilio-input"],
    telefono:      ["mp-telefono-view",   "mp-telefono-input"],
    email:         ["mp-email-view",      "mp-email-input"],
    observaciones: ["mp-obs-view",        "mp-obs-input"]
  };

  /* Activa o desactiva el modo edición de un campo */
  function setModoEdicionCampo(field, activo) {
    const ids = CAMPO_MAP[field];
    if (!ids) return;

    const [viewId, inputId] = ids;
    document.getElementById(viewId)?.classList.toggle("d-none",  activo);
    document.getElementById(inputId)?.classList.toggle("d-none", !activo);

    /* Alternar visibilidad de botones Editar / Guardar */
    document.querySelector(`[data-edit-field="${field}"]`)?.classList.toggle("d-none",  activo);
    document.querySelector(`[data-save-field="${field}"]`)?.classList.toggle("d-none", !activo);
  }

  /* Envía PATCH al servidor con todos los campos editables y actualiza el DOM */
  async function guardarCampoPedido(field) {
    if (!pedidoActualId) return;

    const payload = {
      pais:          document.getElementById("mp-pais-input")?.value.trim()      || "",
      localidad:     document.getElementById("mp-localidad-input")?.value.trim() || "",
      codigo_postal: document.getElementById("mp-cp-input")?.value.trim()        || "",
      barrio:        document.getElementById("mp-barrio-input")?.value.trim()    || "",
      direccion:     document.getElementById("mp-domicilio-input").value.trim(),
      telefono:      document.getElementById("mp-telefono-input").value.trim(),
      email:         document.getElementById("mp-email-input").value.trim(),
      observaciones: document.getElementById("mp-obs-input").value.trim()
    };

    const res = await fetch(`/api/pedidos/${pedidoActualId}`, {
      method:  "PATCH",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify(payload)
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      alert(err.error || "No se pudieron guardar los cambios.");
      return;
    }

    const data = await res.json();

    /* Refrescar textos en los spans de lectura */
    document.getElementById("mp-pais-view").textContent      = data.pais          || "-";
    document.getElementById("mp-localidad-view").textContent = data.localidad     || "-";
    document.getElementById("mp-cp-view").textContent        = data.codigo_postal || "-";
    document.getElementById("mp-barrio-view").textContent    = data.barrio        || "-";
    document.getElementById("mp-domicilio-view").textContent = data.direccion     || "-";
    document.getElementById("mp-telefono-view").textContent  = data.telefono      || "-";
    document.getElementById("mp-email-view").textContent     = data.email         || "-";
    document.getElementById("mp-obs-view").textContent       = data.observaciones || "-";
    document.getElementById("mp-obs-input").value            = data.observaciones || "";

    /* Actualizar links de contacto con los nuevos datos */
    actualizarAccesosContacto({
      pais:         data.pais          || "",
      localidad:    data.localidad     || "",
      codigoPostal: data.codigo_postal || "",
      barrio:       data.barrio        || "",
      telefono:     data.telefono      || "",
      email:        data.email         || "",
      direccion:    data.direccion     || "",
      pedidoId:     data.id || pedidoActualId
    });

    setModoEdicionCampo(field, false);
    await refrescarDetallePedido();
  }

  /* Listeners para los botones Editar (lápiz) de cada campo */
  document.querySelectorAll(".mp-edit-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const field = btn.getAttribute("data-edit-field");
      if (field) setModoEdicionCampo(field, true);
    });
  });

  /* Listeners para los botones Guardar de cada campo */
  document.querySelectorAll(".mp-save-btn").forEach(btn => {
    btn.addEventListener("click", async () => {
      const field = btn.getAttribute("data-save-field");
      if (field) await guardarCampoPedido(field);
    });
  });

  /* Actualizar Maps en tiempo real mientras se tipea en cualquier campo de dirección */
  ["mp-pais-input","mp-localidad-input","mp-cp-input","mp-barrio-input","mp-domicilio-input"]
    .forEach(id => document.getElementById(id)?.addEventListener("input", () => {
      actualizarLinkMaps({
        pais:         document.getElementById("mp-pais-input")?.value      || "",
        localidad:    document.getElementById("mp-localidad-input")?.value || "",
        codigoPostal: document.getElementById("mp-cp-input")?.value        || "",
        barrio:       document.getElementById("mp-barrio-input")?.value    || "",
        direccion:    document.getElementById("mp-domicilio-input")?.value || ""
      });
    }));
  document.getElementById("mp-telefono-input")?.addEventListener("input", (e) =>
    actualizarLinkWhatsApp(e.target.value));
  document.getElementById("mp-email-input")?.addEventListener("input", (e) =>
    actualizarLinkMail(e.target.value, pedidoActualId));


  /* ================================================================
     SECCIÓN 3 — BADGE DE ESTADO
     ================================================================ */

  /* Aplica texto y clase CSS al badge de estado del pedido */
  function setBadge(estado) {
    badge.textContent = "";
    badge.className   = "badge";
    badge.classList.remove("d-none");

    if      (estado === "PENDIENTE")  { badge.textContent = "Pendiente";  badge.classList.add("mp-badge-pendiente");  }
    else if (estado === "EN_CURSO")   { badge.textContent = "En Curso";   badge.classList.add("mp-badge-curso");      }
    else if (estado === "FINALIZADO") { badge.textContent = "Finalizado"; badge.classList.add("mp-badge-finalizado"); }
    else    { badge.classList.add("d-none"); }
  }


  /* ================================================================
     SECCIÓN 4 — DEUDA EN CARD DEL KANBAN
     Actualiza el monto "Debe" en la card del tablero al registrar pagos
     ================================================================ */

  function actualizarDeudaCard(pedidoId, debe) {
    const el = document.getElementById(`pedido-debe-${pedidoId}`);
    if (!el) return;

    if (debe > 0) {
      el.textContent = `$${Number(debe).toLocaleString("es-AR", {maximumFractionDigits: 0})}`;
      el.classList.remove("text-success");
      el.classList.add("text-danger");
    } else {
      el.textContent = "No hay Deuda";
      el.classList.remove("text-danger");
      el.classList.add("text-success");
    }
  }


  /* ================================================================
     SECCIÓN 5 — REFRESCO COMPLETO DEL DETALLE DEL PEDIDO
     Re-fetch del pedido y actualización de todos los elementos del modal
     ================================================================ */

  async function refrescarDetallePedido() {
    if (!pedidoActualId) return;
    try {
      const res = await fetch(`/api/pedidos/${pedidoActualId}`);
      if (!res.ok) return;
      const p = await res.json();

      /* Datos de contacto (spans y inputs) */
      document.getElementById("mp-pais-view").textContent      = p.pais          || "-";
      document.getElementById("mp-localidad-view").textContent = p.localidad     || "-";
      document.getElementById("mp-cp-view").textContent        = p.codigo_postal || "-";
      document.getElementById("mp-barrio-view").textContent    = p.barrio        || "-";
      document.getElementById("mp-domicilio-view").textContent = p.direccion     || "-";
      document.getElementById("mp-telefono-view").textContent  = p.telefono      || "-";
      document.getElementById("mp-email-view").textContent     = p.email         || "-";
      document.getElementById("mp-obs-view").textContent       = p.observaciones || "-";

      if (document.getElementById("mp-pais-input"))
        document.getElementById("mp-pais-input").value      = p.pais          || "";
      if (document.getElementById("mp-localidad-input"))
        document.getElementById("mp-localidad-input").value = p.localidad     || "";
      if (document.getElementById("mp-cp-input"))
        document.getElementById("mp-cp-input").value        = p.codigo_postal || "";
      if (document.getElementById("mp-barrio-input"))
        document.getElementById("mp-barrio-input").value    = p.barrio        || "";
      document.getElementById("mp-domicilio-input").value = p.direccion || "";
      document.getElementById("mp-telefono-input").value  = p.telefono  || "";
      document.getElementById("mp-email-input").value     = p.email     || "";
      document.getElementById("mp-obs-input").value       = p.observaciones || "";

      actualizarAccesosContacto({
        pais:         p.pais          || "",
        localidad:    p.localidad     || "",
        codigoPostal: p.codigo_postal || "",
        barrio:       p.barrio        || "",
        telefono:     p.telefono      || "",
        email:        p.email         || "",
        direccion:    p.direccion     || "",
        pedidoId:     p.id || pedidoActualId,
        tokenPdf:     p.token_pdf     || null
      });

      setBadge(p.estado);

      /* Actualizar monto adeudado en el modal */
      const elDebe   = document.getElementById("mp-debe");
      const debeNum  = Number(p.debe || 0);
      elDebe.classList.remove("debe-ok", "debe-bad");
      if (debeNum > 0) {
        elDebe.textContent = fmtMoney(debeNum);
        elDebe.classList.add("debe-bad");
      } else {
        elDebe.textContent = "No hay Deudas";
        elDebe.classList.add("debe-ok");
      }

      actualizarDeudaCard(p.id, debeNum);
      renderPagos(p.pagos || []);

    } catch (e) {
      /* error silencioso para no interrumpir el flujo */
    }
  }


  /* ================================================================
     SECCIÓN 6 — ACCIONES SOBRE PAGOS (ver / eliminar)
     Delegación de eventos para botones generados dinámicamente
     ================================================================ */

  document.addEventListener("click", async (e) => {

    /* Botón "Ver" de un pago: abre el modal de pago en modo lectura */
    const btnVer = e.target.closest("[data-pay-view]");
    if (btnVer) {
      e.preventDefault();
      const rawId = btnVer.getAttribute("data-pay-view");
      if (!rawId) return;

      const res = await fetch(`/api/pedidos/${pedidoActualId}`);
      if (!res.ok) return;

      const p    = await res.json();
      const pago = (p.pagos || []).find(x => String(x.id) === String(rawId));
      if (pago) abrirPagoReadonly(pago);
      return;
    }

    /* Botón "Eliminar" de un pago */
    const btnDel = e.target.closest("[data-pay-del]");
    if (btnDel) {
      e.preventDefault();
      const payId = btnDel.getAttribute("data-pay-del");
      if (!payId || !confirm("¿Eliminar este registro?")) return;

      let res;
      /* La seña tiene un endpoint propio distinto al de los pagos normales */
      if (String(payId) === "sena") {
        res = await fetch(`/api/pedidos/${pedidoActualId}/sena`, { method: "DELETE" });
      } else {
        res = await fetch(`/api/pagos/${payId}`, { method: "DELETE" });
      }

      if (!res.ok) { alert("No se pudo eliminar el pago."); return; }
      await refrescarDetallePedido();
    }
  });


  /* ================================================================
     SECCIÓN 7 — UTILIDADES DE FORMATO
     ================================================================ */

  /* Convierte "YYYY-MM-DD" → "DD/MM/YYYY" */
  function fmtFechaISOtoAR(iso) {
    if (!iso) return "-";
    const [y, m, d] = iso.split("-");
    return `${d}/${m}/${y}`;
  }

  /* Formatea un número como moneda argentina */
  function fmtMoney(n) {
    return "$" + Number(n || 0).toLocaleString("es-AR", {maximumFractionDigits: 0});
  }


  /* ================================================================
     SECCIÓN 8 — RENDER DEL HISTORIAL DE PAGOS
     ================================================================ */

  function renderPagos(pagos) {
    const cont = document.getElementById("mp-pagos");
    if (!cont) return;
    cont.innerHTML = "";

    if (!pagos || !pagos.length) {
      cont.innerHTML = `<div class="text-muted">Sin pagos</div>`;
      return;
    }

    /* Construir una fila por cada pago con botones Ver y Eliminar */
    pagos.forEach(pay => {
      const row = document.createElement("div");
      row.className = "mp-pago-row";
      row.innerHTML = `
        <div class="mp-pago-left">
          <span>
            <strong>${pay.tipo === "SENA" ? "Seña" : "Pago " + (pay.numero_pago || pay.id)}</strong> -
            ${fmtFechaISOtoAR(pay.fecha_pago)} -
            ${fmtMoney(pay.monto_pagado)} -
            ${pay.metodo || "-"}
          </span>
        </div>
        <div class="mp-pago-actions">
          <button type="button" class="btn btn-success btn-sm" data-pay-view="${pay.id}">Ver</button>
          <button type="button" class="btn btn-danger  btn-sm" data-pay-del="${pay.id}">Eliminar</button>
        </div>
      `;
      cont.appendChild(row);
    });
  }


  /* ================================================================
     SECCIÓN 9 — MODAL DE PAGO EN MODO SOLO LECTURA
     Se usa al hacer click en "Ver" de un pago ya registrado
     ================================================================ */

  function abrirPagoReadonly(pago) {
    const modalPagoEl = document.getElementById("modalPago");
    const modalPago   = bootstrap.Modal.getOrCreateInstance(modalPagoEl);

    /* Cambiar título a Seña o Pago #N */
    const titulo = modalPagoEl.querySelector(".mp-header-title");
    if (titulo) {
      titulo.textContent = pago.tipo === "SENA"
        ? "Seña"
        : `Pago #${pago.numero_pago || pago.id}`;
    }

    /* Referencias a campos del formulario de pago */
    const payPedidoId   = document.getElementById("pay-pedido-id");
    const payMetodo     = document.getElementById("pay-metodo");
    const payFecha      = document.getElementById("pay-fecha");
    const payMonto      = document.getElementById("pay-monto");
    const payCuotas     = document.getElementById("pay-cuotas");
    const payMontoCuota = document.getElementById("pay-monto-cuota");
    const payTarjeta    = document.getElementById("pay-tarjeta");
    const payNormal     = document.getElementById("pay-normal");
    const formPago      = document.getElementById("formPago");
    const btnSubmit     = formPago?.querySelector('button[type="submit"]');

    /* Cargar datos del pago en los campos */
    payPedidoId.value = pago.pedido_id || "";
    payMetodo.value   = pago.metodo    || "";
    payFecha.value    = pago.fecha_pago || "";

    const isTarjeta = (pago.metodo === "Tarjeta");
    payTarjeta.classList.toggle("d-none", !isTarjeta);
    payNormal.classList.toggle("d-none",   isTarjeta);

    if (isTarjeta) {
      payCuotas.value     = pago.cuotas      ?? 1;
      payMontoCuota.value = pago.monto_cuota ?? "";
      payMonto.value      = "";
    } else {
      payMonto.value      = pago.monto_pagado ?? "";
      payCuotas.value     = 1;
      payMontoCuota.value = "";
    }

    /* Deshabilitar todos los campos (solo lectura) */
    document.querySelectorAll(".pay-method").forEach(b => b.disabled = true);
    payFecha.disabled      = true;
    payMonto.disabled      = true;
    payCuotas.disabled     = true;
    payMontoCuota.disabled = true;

    /* Ocultar botones de adjuntar comprobante */
    document.getElementById("btn-comprobante")?.classList.add("d-none");
    document.getElementById("btn-comprobante-tarjeta")?.classList.add("d-none");

    /* Manejo del preview de comprobante */
    const uploadWrap  = document.getElementById("pay-upload-wrap");
    const uploadBar   = document.getElementById("pay-upload-bar");
    const filePreview = document.getElementById("pay-file-preview");

    uploadBar.style.width = "0%";
    uploadWrap.classList.add("d-none");

    if (!pago.comprobantes || !pago.comprobantes.length) {
      filePreview.classList.add("d-none");
      filePreview.innerHTML = "";
    } else {
      filePreview.classList.remove("d-none");
      filePreview.innerHTML = `
        <div class="d-flex justify-content-between align-items-center">
          <div><i class="bi bi-file-earmark-text"></i> ${pago.comprobantes[0].original_name}</div>
          <a href="${pago.comprobantes[0].url}" target="_blank">Ver</a>
        </div>
      `;
    }

    /* Ocultar botón de submit */
    if (btnSubmit) { btnSubmit.disabled = true; btnSubmit.classList.add("d-none"); }

    /* Al cancelar, volver al modal del pedido */
    document.getElementById("pay-cancelar")?.addEventListener("click", () => {
      modalPago.hide();
      modal.show();
    }, { once: true });

    modal.hide();
    modalPago.show();
  }


  /* ================================================================
     SECCIÓN 10 — LINKS DE CONTACTO (WhatsApp, Maps, Gmail)
     ================================================================ */

  /* Normaliza un teléfono argentino al formato internacional 54XXXXXXXXXX
     Acepta: 3492-123456 | 03492 15-1234 | +54 9 3492 123456 | 011-4xxx-xxxx */
  function normalizarTelefonoAR(telefono) {
    if (!telefono) return null;
    let num = telefono.replace(/\D/g, "");
    if (!num) return null;

    // Quitar código de país 54
    if (num.startsWith("54")) num = num.substring(2);
    // Quitar prefijo troncal 0
    if (num.startsWith("0"))  num = num.substring(1);

    if (!num.startsWith("9")) {
      // Detectar y quitar el viejo prefijo "15" móvil (aparece después del código de área)
      // Los códigos de área argentinos tienen 2, 3 o 4 dígitos
      for (const off of [2, 3, 4]) {
        if (num.length > off + 2 && num.substring(off, off + 2) === "15") {
          num = num.substring(0, off) + num.substring(off + 2);
          break;
        }
      }
      // Agregar el "9" que requiere WhatsApp para números móviles argentinos
      num = "9" + num;
    }

    if (num.length !== 11) return null;
    return "54" + num;
  }

  /* Abre una URL externa sin pasar por el anchor — evita el bug del focus-trap de Bootstrap 5
     donde un <a target="_blank"> dentro del modal hace que la página quede sin respuesta
     al volver del tab. Usando window.open() el modal nunca pierde el foco gestionado. */
  function abrirLinkContacto(e, url) {
    e.preventDefault();
    if (!url || url === "#") return;
    window.open(url, "_blank", "noopener,noreferrer");
  }

  /* Arma el link de Google Maps combinando los 5 campos de dirección.
     Acepta un objeto { pais, localidad, codigoPostal, barrio, direccion }
     o (por compatibilidad) un string con la calle. */
  function actualizarLinkMaps(addr) {
    const mapsEl = document.getElementById("mp-maps");
    if (!mapsEl) return;

    let partes;
    if (typeof addr === "string") {
      partes = [addr.trim()].filter(Boolean);
    } else {
      /* El barrio se excluye intencionalmente: en Argentina muchos barrios
         comparten nombre con ciudades ("9 de Julio", "Palermo", etc.) y confunden
         a Maps. Con calle + localidad + CP + país la ubicación es unívoca. */
      partes = [
        (addr.direccion    || "").trim(),
        (addr.localidad    || "").trim(),
        (addr.codigoPostal || "").trim(),
        (addr.pais         || "").trim()
      ].filter(Boolean);
    }

    if (!partes.length) { mapsEl.dataset.url = ""; mapsEl.classList.add("d-none"); return; }

    /* Unir componentes para una búsqueda más precisa */
    const query = encodeURIComponent(partes.join(", "));
    mapsEl.dataset.url = `https://www.google.com/maps/search/?api=1&query=${query}&region=ar`;
    mapsEl.classList.remove("d-none");
  }

  /* Arma el link de WhatsApp (app móvil o web según el dispositivo) */
  function actualizarLinkWhatsApp(telefono, pedidoId = null, tokenPdf = null) {
    const wppEl = document.getElementById("mp-wpp");
    if (!wppEl) return;
    const numero = normalizarTelefonoAR((telefono || "").trim());

    if (!numero || !pedidoId) { wppEl.dataset.url = ""; wppEl.classList.add("d-none"); return; }

    // Usar ruta pública con token si está disponible (funciona hosteado),
    // si no caer a la ruta privada (solo red local)
    const pdfUrl = tokenPdf
      ? `${window.location.origin}/p/${tokenPdf}`
      : `${window.location.origin}/pedidos/${pedidoId}/pdf`;

    const mensaje = encodeURIComponent(
      `Hola, le enviamos su presupuesto de S. Valvo y Cía:\n${pdfUrl}`
    );
    const esMobile = /Android|iPhone|iPad|iPod/i.test(navigator.userAgent);
    wppEl.dataset.url = esMobile
      ? `https://api.whatsapp.com/send?phone=${numero}&text=${mensaje}`
      : `https://web.whatsapp.com/send?phone=${numero}&text=${mensaje}`;
    wppEl.classList.remove("d-none");
  }

  /* Arma el link de Gmail con asunto y cuerpo prellenados */
  function actualizarLinkMail(email, pedidoId = null) {
    const mailEl = document.getElementById("mp-gmail");
    if (!mailEl) return;
    const raw = (email || "").trim();

    if (!raw || !pedidoId) { mailEl.dataset.url = ""; mailEl.classList.add("d-none"); return; }

    const pdfUrl = window._tokenPdf
      ? `${window.location.origin}/p/${window._tokenPdf}`
      : `${window.location.origin}/pedidos/${pedidoId}/pdf`;
    const asunto = encodeURIComponent(`Presupuesto - S. Valvo y Cía`);
    const cuerpo = encodeURIComponent(
      `Hola, le enviamos su presupuesto de S. Valvo y Cía:\n${pdfUrl}`
    );
    mailEl.dataset.url = `https://mail.google.com/mail/?view=cm&fs=1&to=${encodeURIComponent(raw)}&su=${asunto}&body=${cuerpo}`;
    mailEl.classList.remove("d-none");
  }

  /* Actualiza los 3 links de contacto a la vez */
  function actualizarAccesosContacto({
    pais = "", localidad = "", codigoPostal = "", barrio = "",
    telefono = "", email = "", direccion = "", pedidoId = null, tokenPdf = null
  }) {
    actualizarLinkWhatsApp(telefono, pedidoId, tokenPdf);
    actualizarLinkMail(email, pedidoId);
    actualizarLinkMaps({ pais, localidad, codigoPostal, barrio, direccion });
  }

  /* Click handlers para los 3 links: usan window.open() en lugar de navegación href */
  document.getElementById("mp-maps")?.addEventListener("click", function(e) {
    abrirLinkContacto(e, this.dataset.url);
  });
  document.getElementById("mp-wpp")?.addEventListener("click", function(e) {
    abrirLinkContacto(e, this.dataset.url);
  });
  document.getElementById("mp-gmail")?.addEventListener("click", function(e) {
    abrirLinkContacto(e, this.dataset.url);
  });


  /* ================================================================
     SECCIÓN 11 — ABRIR MODAL DE DETALLE (función global)
     Expuesta como window.abrirDetallePedido para que otros scripts
     (dashboard.js, pedidos.js) puedan llamarla
     ================================================================ */

  window.abrirDetallePedido = async function(id) {
    pedidoActualId = id;

    /* Resetear contenido mientras carga */
    document.getElementById("mp-orden").textContent   = `Nro de Orden: #${id}`;
    document.getElementById("mp-cliente").textContent = "Cargando...";
    document.getElementById("mp-pais-view").textContent      = "-";
    document.getElementById("mp-localidad-view").textContent = "-";
    document.getElementById("mp-cp-view").textContent        = "-";
    document.getElementById("mp-barrio-view").textContent    = "-";
    document.getElementById("mp-domicilio-view").textContent = "-";
    document.getElementById("mp-telefono-view").textContent  = "-";
    document.getElementById("mp-email-view").textContent     = "-";
    document.getElementById("mp-obs-view").textContent       = "-";
    document.getElementById("mp-pais-input")?.setAttribute("value", "");
    document.getElementById("mp-localidad-input")?.setAttribute("value", "");
    document.getElementById("mp-cp-input")?.setAttribute("value", "");
    document.getElementById("mp-barrio-input")?.setAttribute("value", "");
    document.getElementById("mp-domicilio-input").value = "";
    document.getElementById("mp-telefono-input").value  = "";
    document.getElementById("mp-email-input").value     = "";
    document.getElementById("mp-obs-input").value       = "";

    actualizarAccesosContacto({
      pais: "", localidad: "", codigoPostal: "", barrio: "",
      telefono: "", email: "", direccion: "", pedidoId: id
    });

    document.getElementById("mp-items").innerHTML    = "<div class='text-muted'>Cargando...</div>";
    document.getElementById("mp-total").textContent  = "-";

    const elDebe = document.getElementById("mp-debe");
    elDebe.textContent = "-";
    elDebe.classList.remove("debe-ok", "debe-bad");

    badge.className   = "badge d-none";
    badge.textContent = "";

    /* Links de descarga PDF */
    document.getElementById("mp-pdf")?.setAttribute("href", `/pedidos/${id}/pdf`);
    document.getElementById("mp-remito")?.setAttribute("href", `/pedidos/${id}/remito`);

    modal.show();  // mostrar el modal con el loader antes de hacer el fetch

    /* Fetch de datos del pedido */
    let p;
    try {
      const res = await fetch(`/api/pedidos/${id}`);
      if (!res.ok) throw new Error("HTTP " + res.status);
      p = await res.json();
    } catch (err) {
      document.getElementById("mp-items").innerHTML =
        "<div class='text-danger'>Error cargando el pedido</div>";
      return;
    }

    renderPagos(p.pagos || []);
    setBadge(p.estado);

    /* Rellenar datos del cliente */
    document.getElementById("mp-cliente").textContent        = (p.cliente || "-").toString();
    document.getElementById("mp-pais-view").textContent      = p.pais          || "-";
    document.getElementById("mp-localidad-view").textContent = p.localidad     || "-";
    document.getElementById("mp-cp-view").textContent        = p.codigo_postal || "-";
    document.getElementById("mp-barrio-view").textContent    = p.barrio        || "-";
    document.getElementById("mp-domicilio-view").textContent = p.direccion     || "-";
    document.getElementById("mp-telefono-view").textContent  = p.telefono      || "-";
    document.getElementById("mp-email-view").textContent     = p.email         || "-";
    document.getElementById("mp-obs-view").textContent       = p.observaciones || "-";

    if (document.getElementById("mp-pais-input"))
      document.getElementById("mp-pais-input").value      = p.pais          || "";
    if (document.getElementById("mp-localidad-input"))
      document.getElementById("mp-localidad-input").value = p.localidad     || "";
    if (document.getElementById("mp-cp-input"))
      document.getElementById("mp-cp-input").value        = p.codigo_postal || "";
    if (document.getElementById("mp-barrio-input"))
      document.getElementById("mp-barrio-input").value    = p.barrio        || "";
    document.getElementById("mp-domicilio-input").value = p.direccion || "";
    document.getElementById("mp-telefono-input").value  = p.telefono  || "";
    document.getElementById("mp-email-input").value     = p.email     || "";
    document.getElementById("mp-obs-input").value       = p.observaciones || "";

    actualizarAccesosContacto({
      pais:         p.pais          || "",
      localidad:    p.localidad     || "",
      codigoPostal: p.codigo_postal || "",
      barrio:       p.barrio        || "",
      telefono:     p.telefono      || "",
      email:        p.email         || "",
      direccion:    p.direccion     || "",
      pedidoId:     p.id ?? id,
      tokenPdf:     p.token_pdf     || null
    });

    document.getElementById("mp-orden").textContent = `Nro de Orden: #${p.id ?? id}`;
    document.getElementById("mp-total").textContent =
      `$${Number(p.total || 0).toLocaleString("es-AR", {maximumFractionDigits: 0})}`;

    /* Calcular y mostrar deuda actual */
    const debeNum = (p.debe !== undefined && p.debe !== null)
      ? Number(p.debe)
      : (Number(p.total || 0) - Number(p.monto_sena || 0));

    elDebe.classList.remove("debe-ok", "debe-bad");
    if (debeNum > 0) {
      elDebe.textContent = `$${debeNum.toLocaleString("es-AR", {maximumFractionDigits: 0})}`;
      elDebe.classList.add("debe-bad");
    } else {
      elDebe.textContent = "No hay Deudas";
      elDebe.classList.add("debe-ok");
    }

    /* Renderizar lista de ítems del pedido */
    const cont = document.getElementById("mp-items");
    cont.innerHTML = "";
    if (!p.items || !p.items.length) {
      cont.innerHTML = "<div class='text-muted'>Sin items</div>";
    } else {
      p.items.forEach(it => {
        const row = document.createElement("div");
        row.className = "pedido-item-row";
        const subtotal = `$${Number(it.subtotal || 0).toLocaleString("es-AR", {maximumFractionDigits: 0})}`;
        row.innerHTML = `
          <div class="pedido-item-desc">${it.descripcion || "-"}</div>
          <div class="pedido-item-dots"></div>
          <div class="pedido-item-sub">${subtotal}</div>
        `;
        cont.appendChild(row);
      });
    }
  };



  /* ================================================================
     SECCIÓN 12 — CLICK DELEGADO EN data-pedido-open
     Escucha cualquier botón "Ver" de la tabla o el kanban
     ================================================================ */

  document.addEventListener("click", (e) => {
    const el = e.target.closest("[data-pedido-open]");
    if (!el) return;
    e.preventDefault();
    e.stopPropagation();

    const id = el.getAttribute("data-pedido-open");
    if (!id) return;

    /* Si el modal de tabla expandida está abierto, cerrarlo primero */
    const modalTablaEl = document.getElementById("modalTablaExpandida");
    const tablaInst    = modalTablaEl ? bootstrap.Modal.getInstance(modalTablaEl) : null;

    if (tablaInst) {
      modalTablaEl.addEventListener("hidden.bs.modal", () => {
        window.abrirDetallePedido(id);
      }, { once: true });
      tablaInst.hide();
      return;
    }

    window.abrirDetallePedido(id);
  });


  /* ================================================================
     SECCIÓN 13 — ELIMINAR PEDIDO DESDE EL MODAL
     ================================================================ */

  document.getElementById("mp-eliminar")?.addEventListener("click", async () => {
    if (!pedidoActualId || !confirm("¿Eliminar pedido?")) return;

    const res = await fetch(`/pedidos/eliminar/${pedidoActualId}`, { method: "POST" });
    if (!res.ok) { alert("No se pudo eliminar."); return; }

    /* Quitar la card del kanban si existe */
    document.querySelector(`.pedido-card[data-id="${pedidoActualId}"]`)?.remove();
    modal.hide();
  });


  /* ================================================================
     SECCIÓN 14 — MODAL DE REGISTRAR PAGO
     ================================================================ */

  const modalPagoEl = document.getElementById("modalPago");
  const btnAddPago  = document.getElementById("mp-add-pago");

  if (!modalPagoEl || !btnAddPago) return;  // si no existe el modal de pago, salir

  const modalPago     = bootstrap.Modal.getOrCreateInstance(modalPagoEl);

  /* Referencias a los campos del formulario de pago */
  const payPedidoId   = document.getElementById("pay-pedido-id");
  const payMetodo     = document.getElementById("pay-metodo");
  const payTarjeta    = document.getElementById("pay-tarjeta");
  const payNormal     = document.getElementById("pay-normal");
  const payMonto      = document.getElementById("pay-monto");
  const payCuotas     = document.getElementById("pay-cuotas");
  const payMontoCuota = document.getElementById("pay-monto-cuota");
  const payTotalHidden = document.getElementById("pay-total");
  const payFecha      = document.getElementById("pay-fecha");
  const btnCancelar   = document.getElementById("pay-cancelar");
  const formPago      = document.getElementById("formPago");

  /* Referencias para el adjunto del comprobante */
  const payFileInput  = document.getElementById("pay-comprobante");
  const btnComprobante = document.getElementById("btn-comprobante");
  const uploadWrap    = document.getElementById("pay-upload-wrap");
  const uploadBar     = document.getElementById("pay-upload-bar");
  const filePreview   = document.getElementById("pay-file-preview");

  let archivoSeleccionado = null;  // File seleccionado para subir como comprobante

  /* ---- Abrir selector de fecha al hacer click o focus ---- */
  payFecha?.addEventListener("click",  () => { if (payFecha.showPicker) payFecha.showPicker(); });
  payFecha?.addEventListener("focus",  () => { if (payFecha.showPicker) payFecha.showPicker(); });

  /* ---- Resetea el formulario de pago a su estado inicial ---- */
  function resetModalPago() {
    modalPagoEl.querySelector(".mp-header-title").textContent = "Cargar Nuevo Pago";

    /* Rehabilitar botones de método y campos */
    document.querySelectorAll(".pay-method").forEach(b => { b.disabled = false; b.classList.remove("active"); });
    payFecha.disabled      = false;
    payMonto.disabled      = false;
    payCuotas.disabled     = false;
    payMontoCuota.disabled = false;

    /* Mostrar botón de submit */
    const btnSubmit = formPago?.querySelector('button[type="submit"]');
    if (btnSubmit) { btnSubmit.disabled = false; btnSubmit.classList.remove("d-none"); }

    /* Mostrar botones de adjuntar */
    document.getElementById("btn-comprobante")?.classList.remove("d-none");
    document.getElementById("btn-comprobante-tarjeta")?.classList.remove("d-none");

    /* Limpiar archivo y preview */
    archivoSeleccionado = null;
    payFileInput.value  = "";
    filePreview.classList.add("d-none");
    filePreview.innerHTML = "";
    uploadWrap.classList.add("d-none");
    uploadBar.style.width = "0%";

    /* Limpiar valores */
    payMetodo.value       = "";
    payMonto.value        = "";
    payCuotas.value       = 1;
    payMontoCuota.value   = "";
    payTotalHidden.value  = "";
    payPedidoId.value     = "";

    /* Mostrar bloque "normal" (no tarjeta) por defecto */
    payNormal.classList.remove("d-none");
    payTarjeta.classList.add("d-none");
  }

  /* ---- Botones de adjuntar comprobante: disparan el input[type=file] ---- */
  btnComprobante?.addEventListener("click", () => payFileInput?.click());
  document.getElementById("btn-comprobante-tarjeta")?.addEventListener("click", () => payFileInput?.click());

  /* ---- Al seleccionar un archivo: mostrar preview con nombre y tamaño ---- */
  payFileInput?.addEventListener("change", () => {
    const f = payFileInput.files?.[0] ?? null;
    archivoSeleccionado = f;

    uploadWrap.classList.add("d-none");
    uploadBar.style.width = "0%";

    if (!f) { filePreview.classList.add("d-none"); filePreview.innerHTML = ""; return; }

    filePreview.classList.remove("d-none");
    filePreview.innerHTML = `
      <div class="d-inline-flex align-items-center gap-2 border rounded-3 px-2 py-1" style="max-width:520px;">
        <div class="d-flex align-items-center gap-2" style="min-width:0;">
          <i class="bi bi-file-earmark"></i>
          <div style="min-width:0;">
            <div class="small fw-semibold text-truncate" style="max-width:380px;">${f.name}</div>
            <div class="small text-muted" style="font-size:.75rem;">${Math.round(f.size/1024)} KB</div>
          </div>
        </div>
        <button type="button" class="btn btn-sm btn-outline-secondary p-0 d-flex align-items-center justify-content-center"
                id="pay-file-remove" aria-label="Eliminar archivo" style="width:28px;height:28px;">
          <i class="bi bi-x-lg"></i>
        </button>
      </div>
    `;

    /* Botón para quitar el archivo seleccionado */
    document.getElementById("pay-file-remove")?.addEventListener("click", () => {
      archivoSeleccionado = null;
      payFileInput.value  = "";
      uploadWrap.classList.add("d-none");
      uploadBar.style.width = "0%";
      filePreview.classList.add("d-none");
      filePreview.innerHTML = "";
    });
  });

  /* ---- Fecha de hoy en formato YYYY-MM-DD para valor por defecto ---- */
  function hoyISO() {
    const d  = new Date();
    const mm = String(d.getMonth() + 1).padStart(2, "0");
    const dd = String(d.getDate()).padStart(2, "0");
    return `${d.getFullYear()}-${mm}-${dd}`;
  }

  /* ---- Recalcular total al cambiar cuotas o monto de cuota (tarjeta) ---- */
  function calcTotalTarjeta() {
    const cuotas = Number(payCuotas.value  || 0);
    const cuota  = Number(payMontoCuota.value || 0);
    const total  = Math.max(0, cuotas) * Math.max(0, cuota);
    payTotalHidden.value = total ? total.toFixed(2) : "";
  }

  /* ---- Cambiar método de pago: alterna entre bloque Tarjeta y bloque Normal ---- */
  function setMetodo(m) {
    payMetodo.value = m;
    document.querySelectorAll(".pay-method").forEach(b =>
      b.classList.toggle("active", b.dataset.metodo === m)
    );

    const isTarjeta = (m === "Tarjeta");
    payTarjeta.classList.toggle("d-none", !isTarjeta);
    payNormal.classList.toggle("d-none",   isTarjeta);

    if (isTarjeta) {
      payMonto.required      = false;
      payCuotas.required     = true;
      payMontoCuota.required = true;
      payMonto.value         = "";
      if (!payCuotas.value) payCuotas.value = 1;
      calcTotalTarjeta();
    } else {
      payMonto.required      = true;
      payCuotas.required     = false;
      payMontoCuota.required = false;
      payCuotas.value        = 1;
      payMontoCuota.value    = "";
      payTotalHidden.value   = "";
    }
  }

  /* Click en botones de método (Efectivo, Transferencia, Tarjeta, MercadoPago) */
  document.querySelectorAll(".pay-method").forEach(btn =>
    btn.addEventListener("click", () => setMetodo(btn.dataset.metodo))
  );

  /* Recalcular total tarjeta al tipear en cuotas o monto por cuota */
  payCuotas?.addEventListener("input",     calcTotalTarjeta);
  payMontoCuota?.addEventListener("input", calcTotalTarjeta);

  /* ---- Abrir modal de pago al hacer click en "Registrar Pago" ---- */
  document.addEventListener("click", (e) => {
    const btn = e.target.closest("#mp-add-pago");
    if (!btn) return;
    if (!pedidoActualId) { alert("Primero abrí un pedido para registrar el pago."); return; }

    resetModalPago();
    payPedidoId.value = pedidoActualId;
    payFecha.value    = hoyISO();

    modal.hide();
    modalPago.show();
  });

  /* ---- Cancelar: volver al modal del pedido ---- */
  btnCancelar?.addEventListener("click", () => { modalPago.hide(); modal.show(); });


  /* ================================================================
     SECCIÓN 15 — SUBMIT DEL FORMULARIO DE PAGO
     Valida, arma FormData y envía via XHR con barra de progreso
     ================================================================ */

  formPago?.addEventListener("submit", (e) => {
    e.preventDefault();

    /* Validar método seleccionado */
    const metodo = (payMetodo.value || "").trim();
    if (!metodo) return alert("Seleccioná una forma de pago.");

    /* Validar fecha */
    const fecha = (payFecha.value || "").trim();
    if (!fecha) return alert("Seleccioná la fecha de pago.");

    /* Calcular monto final según método */
    let montoFinal = 0;
    let cuotas     = null;
    let montoCuota = null;

    if (metodo === "Tarjeta") {
      cuotas     = Number(payCuotas.value    || 0);
      montoCuota = Number(payMontoCuota.value || 0);
      montoFinal = Math.max(0, cuotas) * Math.max(0, montoCuota);
      if (!cuotas    || cuotas    < 1)  return alert("Ingresá la cantidad de cuotas.");
      if (!montoCuota || montoCuota <= 0) return alert("Ingresá el monto de la cuota.");
    } else {
      montoFinal = Number(payMonto.value || 0);
      if (!montoFinal || montoFinal <= 0) return alert("Ingresá el monto pagado.");
    }

    /* Validar que el monto no supere el saldo pendiente */
    const elDebe = document.getElementById("mp-debe");
    let debeActual = 0;
    if (elDebe?.textContent) {
      const limpio = elDebe.textContent.replace(/[^\d,-]/g, "").replace(/\./g, "").replace(",", ".");
      debeActual = Number(limpio) || 0;
    }
    if (montoFinal > debeActual) return alert("El monto ingresado supera el saldo pendiente.");

    /* Armar FormData */
    const fd = new FormData();
    fd.append("metodo",      metodo);
    fd.append("fecha_pago",  fecha);
    fd.append("monto_pagado", String(montoFinal));
    if (metodo === "Tarjeta") {
      fd.append("cuotas",      String(cuotas));
      fd.append("monto_cuota", String(montoCuota));
    }
    if (archivoSeleccionado) fd.append("comprobante", archivoSeleccionado);

    /* Envío con XHR para mostrar barra de progreso real */
    uploadWrap.classList.remove("d-none");
    uploadBar.style.width = "0%";

    const xhr = new XMLHttpRequest();
    xhr.open("POST", `/api/pedidos/${payPedidoId.value}/pagos`, true);

    /* Actualizar barra de progreso durante la subida */
    xhr.upload.onprogress = (evt) => {
      uploadWrap.classList.remove("d-none");
      if (!evt.lengthComputable) { uploadBar.style.width = "50%"; return; }
      uploadBar.style.width = Math.round((evt.loaded / evt.total) * 100) + "%";
    };

    /* Al completar la subida: refrescar detalle y volver al modal del pedido */
    xhr.onload = async () => {
      uploadBar.style.width = "100%";
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const resp = JSON.parse(xhr.responseText || "{}");
          /* Mostrar link al comprobante si se subió exitosamente */
          if (resp.comprobante_url) {
            filePreview.classList.remove("d-none");
            filePreview.innerHTML = `
              <div class="d-flex justify-content-between align-items-center">
                <div><i class="bi bi-check-circle-fill text-success me-1"></i> Comprobante cargado</div>
                <a href="${resp.comprobante_url}" target="_blank">Ver</a>
              </div>
            `;
          }
        } catch {}

        modalPago.hide();
        modal.show();
        await refrescarDetallePedido();
        return;
      }
      alert("No se pudo registrar el pago.");
    };

    xhr.onerror = () => alert("Error de red al registrar el pago.");
    xhr.send(fd);
  });


  /* ================================================================
     SECCIÓN 16 — FIX BACKDROP ZOMBIE DE BOOTSTRAP
     Al cerrar el modal del pedido, limpiar backdrops huérfanos
     si no hay otro modal abierto detrás
     ================================================================ */

  modalEl.addEventListener("hidden.bs.modal", () => {
    if (!document.querySelector(".modal.show")) {
      document.body.classList.remove("modal-open");
      document.body.style.removeProperty("padding-right");
      document.querySelectorAll(".modal-backdrop").forEach(b => b.remove());
    }
  });

});

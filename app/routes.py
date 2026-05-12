# ==============================================================================
#  routes.py  —  Registro de todas las rutas HTTP de la aplicación
#
#  Secciones:
#    · Productos            — CRUD de catálogo de productos con stock
#    · Configuración        — Precios de muebles por línea y adicionales
#    · Presupuestador       — Generación de presupuestos y creación de pedidos
#    · Pedidos              — Kanban de pedidos (Pendiente / En Curso / Finalizado)
#    · Dashboard            — KPIs y gráficos de actividad
#    · API Pedidos          — Endpoints JSON para el modal de detalle de pedido
#    · PDFs                 — Presupuesto (público vía token) y Remito interno
#    · Pagos                — Registro de pagos y subida de comprobantes
#    · Calendario           — CRUD de recordatorios
# ==============================================================================

from flask import render_template, request, redirect, url_for, flash, send_file, jsonify, current_app
from flask_login import login_required
from . import db
from .models import Producto, Pedido, PedidoItem, Pago, PagoComprobante, PrecioMueble, AdicionalMueble, ConfiguracionGeneral, Recordatorio
from sqlalchemy import func
from datetime import datetime, timedelta, date
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor
import os
import secrets
from werkzeug.utils import secure_filename
import json

# ------------------------------------------------------------------------------
#  Constantes de color compartidas entre los dos generadores de PDF
# ------------------------------------------------------------------------------
_PDF_NAVY   = HexColor("#0b2a4a")
_PDF_ORANGE = HexColor("#c46200")
_PDF_LGRAY  = HexColor("#f1f5f9")
_PDF_MGRAY  = HexColor("#64748b")
_PDF_WHITE  = HexColor("#ffffff")
_PDF_DARK   = HexColor("#1e293b")
_PDF_LLINE  = HexColor("#e2e8f0")

# ------------------------------------------------------------------------------
#  Helpers a nivel de módulo
# ------------------------------------------------------------------------------

def _decrementar_stock_pedido(pedido):
    """Descuenta el stock de cada ítem del pedido al finalizarlo.
    Solo actúa sobre productos que tienen stock habilitado (stock != None).
    El mínimo resultante es 0 para evitar valores negativos.
    """
    for item in pedido.items:
        if item.producto_id:
            prod = Producto.query.get(item.producto_id)
            if prod is not None and prod.stock is not None:
                prod.stock = max(0, prod.stock - item.cantidad)


def register_routes(app):

    # --------------------------------------------------------------------------
    #  Raíz: redirige al dashboard
    # --------------------------------------------------------------------------
    @app.get("/")
    def home():
        return redirect(url_for("dashboard"))

    # ==========================================================================
    #  PRODUCTOS
    #  CRUD del catálogo: alta, listado, edición de precio/stock, baja.
    #  Los precios se pueden actualizar de forma individual (AJAX) o en masa
    #  (bulk) aplicando un porcentaje de aumento a todos los productos.
    # ==========================================================================
    @app.get("/productos")
    @login_required
    def productos():
        items = Producto.query.order_by(Producto.nombre.asc()).all()
        return render_template("productos.html", productos=items)

    @app.post("/productos")
    @login_required
    def productos_post():
        nombre = request.form.get("nombre", "").strip()
        tipo = request.form.get("tipo", "").strip()
        precio_str = request.form.get("precio", "0").strip()
        tiene_stock = request.form.get("tiene_stock") == "on"
        stock_str = request.form.get("stock", "").strip()

        if not nombre or not tipo:
            flash("Completá Nombre y Tipo de Producto.", "warning")
            return redirect(url_for("productos"))

        try:
            precio = float(precio_str) if precio_str else 0.0
        except ValueError:
            flash("Precio inválido.", "danger")
            return redirect(url_for("productos"))

        stock = None
        if tiene_stock and stock_str:
            try:
                stock = int(stock_str)
            except ValueError:
                stock = None

        p = Producto(nombre=nombre, tipo=tipo, precio=precio, stock=stock)
        db.session.add(p)
        db.session.commit()
        flash("Producto agregado.", "success")
        return redirect(url_for("productos"))

    @app.post("/productos/<int:pid>/stock")
    @login_required
    def actualizar_stock(pid):
        p = Producto.query.get_or_404(pid)
        data = request.get_json() or {}
        nuevo = data.get("stock")
        p.stock = int(nuevo) if nuevo is not None else None
        db.session.commit()
        return jsonify({"ok": True, "stock": p.stock})

    @app.post("/productos/<int:pid>/precio")
    @login_required
    def actualizar_precio(pid):
        p = Producto.query.get_or_404(pid)
        data = request.get_json() or {}
        nuevo = data.get("precio")
        if nuevo is None:
            return jsonify({"ok": False}), 400
        p.precio = float(nuevo)
        db.session.commit()
        return jsonify({"ok": True, "precio": p.precio})

    @app.post("/productos/bulk_precio")
    @login_required
    def productos_bulk_precio():
        items = request.get_json() or []
        for item in items:
            pid   = item.get("id")
            precio = item.get("precio")
            if pid is None or precio is None:
                continue
            p = Producto.query.get(pid)
            if p:
                p.precio = float(precio)
        db.session.commit()
        return jsonify({"ok": True})

    @app.post("/productos/<int:pid>/delete")
    @login_required
    def productos_delete(pid):
        p = Producto.query.get_or_404(pid)
        db.session.delete(p)
        db.session.commit()
        flash("Producto eliminado.", "success")
        return redirect(url_for("productos"))

    # ==========================================================================
    #  CONFIGURACIÓN DE PRECIOS
    #  Maneja las tablas PrecioMueble (medidas × líneas) y AdicionalMueble
    #  (extras por línea). El formulario envía todos los registros en un
    #  único POST con arrays indexados; la ruta distingue nuevos vs. existentes
    #  por el valor del campo "ref" ("new" o ID numérico).
    # ==========================================================================
    @app.get("/configuracion")
    @login_required
    def configuracion():

        standard  = PrecioMueble.query.filter_by(linea="standard").order_by(PrecioMueble.medida).all()
        melamina  = PrecioMueble.query.filter_by(linea="melamina").order_by(PrecioMueble.medida).all()
        glaciar   = PrecioMueble.query.filter_by(linea="glaciar").order_by(PrecioMueble.medida).all()
        lujo      = PrecioMueble.query.filter_by(linea="lujo").order_by(PrecioMueble.medida).all()
        roble     = PrecioMueble.query.filter_by(linea="roble").order_by(PrecioMueble.medida).all()

        adicionales_standard = AdicionalMueble.query.filter_by(linea="standard").all()
        adicionales_melamina = AdicionalMueble.query.filter_by(linea="melamina").all()
        adicionales_glaciar  = AdicionalMueble.query.filter_by(linea="glaciar").all()
        adicionales_lujo     = AdicionalMueble.query.filter_by(linea="lujo").all()
        adicionales_roble    = AdicionalMueble.query.filter_by(linea="roble").all()

        config = ConfiguracionGeneral.query.first()

        return render_template(
            "configuracion.html",
            standard=standard,
            melamina=melamina,
            glaciar=glaciar,
            lujo=lujo,
            roble=roble,
            adicionales_standard=adicionales_standard,
            adicionales_melamina=adicionales_melamina,
            adicionales_glaciar=adicionales_glaciar,
            adicionales_lujo=adicionales_lujo,
            adicionales_roble=adicionales_roble,
            config_fecha=config.fecha_actualizacion if config else None
        )
    
    @app.route("/configuracion/fecha", methods=["POST"])
    @login_required
    def guardar_fecha_config():
        data = request.get_json()
        fecha_str = data.get("fecha")

        if not fecha_str:
            return jsonify({"error": "Fecha vacía"}), 400

        fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()

        config = ConfiguracionGeneral.query.first()

        if not config:
            config = ConfiguracionGeneral(fecha_actualizacion=fecha)
            db.session.add(config)
        else:
            config.fecha_actualizacion = fecha

        db.session.commit()

        return jsonify({"ok": True})
        
    @app.delete("/configuracion/adicional/<int:id>")
    @login_required
    def eliminar_adicional(id):
        a = AdicionalMueble.query.get_or_404(id)
        db.session.delete(a)
        db.session.commit()
        return {"ok": True}
    
    @app.delete("/configuracion/mueble/<int:id>")
    @login_required
    def eliminar_mueble(id):
        m = PrecioMueble.query.get_or_404(id)
        db.session.delete(m)
        db.session.commit()
        return {"ok": True}

    @app.post("/configuracion")
    @login_required
    def configuracion_post():

        refs = request.form.getlist("ref[]")
        tipos = request.form.getlist("tipo[]")
        lineas = request.form.getlist("linea[]")

        medidas = request.form.getlist("medida[]")
        bases = request.form.getlist("base[]")
        alacenas = request.form.getlist("alacena[]")
        inoxs = request.form.getlist("inox[]")

        nombres        = request.form.getlist("nombre_adicional[]")
        precios_base   = request.form.getlist("precios_base[]")
        precios_alacena= request.form.getlist("precios_alacena[]")
        precios_inox   = request.form.getlist("precios_inox[]")

        idx_mueble = 0
        idx_adicional = 0

        for i in range(len(refs)):

            tipo = tipos[i]
            ref = refs[i]
            linea = lineas[i]

            # =====================
            # MUEBLES
            # =====================
            if tipo == "mueble":

                try:
                    medida = float(medidas[idx_mueble] or 0)
                except:
                    medida = 0
                base = float(bases[idx_mueble] or 0)
                alacena = float(alacenas[idx_mueble] or 0)
                inox = float(inoxs[idx_mueble] or 0)

                if ref == "new":
                    m = PrecioMueble(
                        linea=linea,
                        medida=medida,
                        base=base,
                        alacena=alacena,
                        inox=inox
                    )
                    db.session.add(m)

                else:
                    m = PrecioMueble.query.get(int(ref))
                    if m:
                        m.medida = medida
                        m.base = base
                        m.alacena = alacena
                        m.inox = inox

                idx_mueble += 1

            # =====================
            # ADICIONALES
            # =====================
            elif tipo == "adicional":

                def _p(lst, idx):
                    v = float(lst[idx] or 0) if idx < len(lst) else 0
                    return v if v > 0 else None

                nombre = nombres[idx_adicional]
                pb = _p(precios_base,    idx_adicional)
                pa = _p(precios_alacena, idx_adicional)
                pi = _p(precios_inox,    idx_adicional)

                if ref == "new":
                    a = AdicionalMueble(
                        linea=linea, nombre=nombre,
                        precio_base=pb, precio_alacena=pa, precio_inox=pi
                    )
                    db.session.add(a)
                else:
                    a = AdicionalMueble.query.get(int(ref))
                    if a:
                        a.nombre = nombre
                        a.precio_base    = pb
                        a.precio_alacena = pa
                        a.precio_inox    = pi

                idx_adicional += 1

        db.session.commit()

        flash("Configuración actualizada", "success")
        return redirect(url_for("configuracion"))
    
    @app.delete("/configuracion/delete")
    @login_required
    def configuracion_delete():

        data = request.get_json() or {}
        origen = data.get("origen")
        ref = data.get("ref")

        try:
            # -------- MUEBLES --------
            if origen == "mueble":
                m = PrecioMueble.query.get_or_404(int(ref))
                db.session.delete(m)

            # -------- ADICIONALES --------
            elif origen == "adicional":
                a = AdicionalMueble.query.get_or_404(int(ref))
                db.session.delete(a)

            db.session.commit()
            return {"ok": True}, 200

        except Exception as e:
            return {"error": str(e)}, 500

    # ==========================================================================
    #  PRESUPUESTADOR
    #  Muestra la herramienta interactiva que arma presupuestos con muebles,
    #  adicionales y productos del catálogo. Al confirmar, crea un Pedido con
    #  sus PedidoItems y redirige al kanban de pedidos.
    # ==========================================================================
    @app.get("/presupuestador")
    @login_required
    def presupuestador():

        muebles = [
            {
                "id": m.id,
                "linea": m.linea,
                "medida": m.medida,
                "base": m.base,
                "alacena": m.alacena,
                "inox": m.inox
            }
            for m in PrecioMueble.query.all()
        ]
        adicionales = [
            {
                "id": a.id,
                "linea": a.linea,
                "nombre": a.nombre,
                "precio_base":    a.precio_base,
                "precio_alacena": a.precio_alacena,
                "precio_inox":    a.precio_inox,
            }
            for a in AdicionalMueble.query.all()
        ]
        productos = Producto.query.all()

        return render_template(
            "presupuestador.html",
            muebles=muebles,
            adicionales=adicionales,
            productos=productos
        )
    
    @app.post("/presupuestador/crear_pedido")
    @login_required
    def crear_pedido():
        cliente = request.form.get("cliente", "").strip()
        telefono = request.form.get("telefono", "").strip()
        email = request.form.get("email", "").strip()
        pais = request.form.get("pais", "").strip()
        localidad = request.form.get("localidad", "").strip()
        codigo_postal = request.form.get("codigo_postal", "").strip()
        barrio = request.form.get("barrio", "").strip()
        direccion = request.form.get("direccion", "").strip()
        entrega_sena = request.form.get("entrega_sena") == "1"
        forma_pago = (request.form.get("forma_pago") or "").strip()
        monto_sena_str = (request.form.get("monto_sena") or "").strip()
        observaciones = request.form.get("observaciones", "").strip() or None

        monto_sena = None

        if entrega_sena:
            if not forma_pago:
                flash("Seleccioná la forma de pago de la seña.", "warning")
                return redirect(url_for("presupuestador"))

            if not monto_sena_str:
                flash("Ingresá el monto de la seña.", "warning")
                return redirect(url_for("presupuestador"))

            try:
                monto_sena = float(monto_sena_str)
                if monto_sena <= 0:
                    raise ValueError()
            except ValueError:
                flash("Monto de seña inválido.", "danger")
                return redirect(url_for("presupuestador"))
        else:
            forma_pago = None
            monto_sena = None

        if not cliente:
            flash("Completá el nombre del cliente.", "warning")
            return redirect(url_for("presupuestador"))

        if not telefono:
            flash("Completá el teléfono del cliente.", "warning")
            return redirect(url_for("presupuestador"))

        # items manuales (productos + muebles + adicionales)
        items_manual_json = request.form.get("items_manual_json", "").strip()
        items_manual = []

        if items_manual_json:
            try:
                items_manual = json.loads(items_manual_json)
            except Exception:
                items_manual = []

        if not items_manual:
            flash("Agregá al menos un ítem al presupuesto.", "warning")
            return redirect(url_for("presupuestador"))

        ahora = datetime.utcnow()

        pedido = Pedido(
            cliente=cliente,
            telefono=telefono,
            email=email,
            pais=pais or None,
            localidad=localidad or None,
            codigo_postal=codigo_postal or None,
            barrio=barrio or None,
            direccion=direccion,
            observaciones=observaciones,
            total=0.0,
            forma_pago_preferida=forma_pago,
            monto_sena=monto_sena,
            estado="PENDIENTE",
            created_at=ahora,
            pendiente_at=ahora,
            token_pdf=secrets.token_urlsafe(24)
        )
        
        db.session.add(pedido)
        db.session.flush()  # para obtener pedido.id

        total = 0.0

        for it in items_manual:
            try:
                desc = (it.get("descripcion") or "").strip()
                cant = int(it.get("cantidad") or 1)
                metros = it.get("metros", None)
                subtotal = float(it.get("subtotal") or 0.0)
                prod_id_raw = it.get("producto_id")
                producto_id = int(prod_id_raw) if prod_id_raw else None

                if not desc or subtotal <= 0:
                    continue

                item = PedidoItem(
                    pedido_id=pedido.id,
                    descripcion=desc,
                    cantidad=cant,
                    metros=float(metros) if metros not in [None, ""] else None,
                    subtotal=subtotal,
                    producto_id=producto_id
                )

                total += subtotal
                db.session.add(item)

            except Exception:
                continue

        pedido.total = total
        db.session.commit()
        flash(f"Pedido creado. Total: ${total:.2f}", "success")
        return redirect(url_for("pedidos"))

    # ==========================================================================
    #  PEDIDOS — Kanban y acciones
    #  Vista principal con columnas Pendiente / En Curso / Finalizado.
    #  Las transiciones de estado se gestionan vía AJAX (POST /pedidos/mover).
    #  Al finalizar un pedido se descuenta el stock automáticamente (una sola
    #  vez, controlado por el flag stock_descontado).
    #  Los pedidos finalizados no se borran físicamente: se marcan activo=False.
    # ==========================================================================
    def pedidos_por_estado(estado):
        return Pedido.query.filter_by(
            estado=estado,
            activo=True
        ).order_by(Pedido.id.desc()).all()


    @app.get("/pedidos")
    @login_required
    def pedidos():
        return render_template(
            "pedidos.html",
            pedidos_pendientes=pedidos_por_estado("PENDIENTE"),
            pedidos_en_curso=pedidos_por_estado("EN_CURSO"),
            pedidos_finalizados=pedidos_por_estado("FINALIZADO"),
        )

    @app.post("/pedidos/<int:pid>/finalizar")
    @login_required
    def finalizar_pedido(pid):
        p = Pedido.query.get_or_404(pid)
        if not p.stock_descontado:
            _decrementar_stock_pedido(p)
            p.stock_descontado = True
        p.estado = "FINALIZADO"
        db.session.commit()
        flash("Pedido finalizado.", "success")
        return redirect(url_for("pedidos"))
    
    @app.get("/api/pedidos/<int:pid>")
    @login_required
    def api_pedido_detalle(pid):
        p = Pedido.query.get_or_404(pid)

        items = []
        for it in p.items:
            items.append({
                "descripcion": it.descripcion,
                "cantidad": int(it.cantidad or 0),
                "metros": float(it.metros) if it.metros is not None else None,
                "subtotal": float(it.subtotal or 0.0),
            })

        pagos = []
        total_pagado = 0.0
        numero_pago = 1

        # ===== Seña como primer registro del historial =====
        monto_sena_val = float(p.monto_sena or 0.0)

        if monto_sena_val > 0:
            pagos.append({
                "id": "sena",
                "tipo": "SENA",
                "numero_pago": numero_pago,
                "pedido_id": p.id,
                "metodo": p.forma_pago_preferida or "-",
                "monto_pagado": monto_sena_val,
                "cuotas": None,
                "monto_cuota": None,
                "fecha_pago": p.created_at.strftime("%Y-%m-%d") if p.created_at else None,
                "comprobantes": []
            })
            numero_pago += 1

        # ===== Pagos reales =====
        pagos_ordenados = sorted(
            getattr(p, "pagos", []) or [],
            key=lambda x: x.created_at or x.fecha_pago
        )

        for pay in pagos_ordenados:
            total_pagado += float(pay.monto_pagado or 0.0)

            pagos.append({
                "id": pay.id,
                "tipo": "PAGO",
                "numero_pago": numero_pago,
                "pedido_id": p.id,
                "metodo": pay.metodo,
                "monto_pagado": float(pay.monto_pagado or 0.0),
                "cuotas": pay.cuotas,
                "monto_cuota": float(pay.monto_cuota) if pay.monto_cuota is not None else None,
                "fecha_pago": pay.fecha_pago.strftime("%Y-%m-%d") if pay.fecha_pago else None,
                "comprobantes": [
                    {
                        "id": c.id,
                        "original_name": c.original_name,
                        "url": url_for("ver_comprobante", filename=c.filename)
                    } for c in (pay.comprobantes or [])
                ]
            })
            numero_pago += 1

        debe = float(p.total or 0.0) - monto_sena_val - total_pagado

        # Pedidos anteriores al campo token_pdf: generar uno ahora
        if not p.token_pdf:
            p.token_pdf = secrets.token_urlsafe(24)
            db.session.commit()

        return {
            "id": p.id,
            "cliente": p.cliente,
            "telefono": p.telefono or "-",
            "email": p.email or "-",
            "pais": p.pais or "",
            "localidad": p.localidad or "",
            "codigo_postal": p.codigo_postal or "",
            "barrio": p.barrio or "",
            "direccion": p.direccion or "-",
            "observaciones": p.observaciones or "-",
            "forma_pago": p.forma_pago_preferida or "-",
            "monto_sena": float(p.monto_sena) if p.monto_sena else None,
            "total_pagado": float(total_pagado),
            "debe": float(debe),
            "total": float(p.total or 0.0),
            "estado": p.estado,
            "items": items,
            "pagos": pagos,
            "token_pdf": p.token_pdf
        }
    
    @app.patch("/api/pedidos/<int:pid>")
    @login_required
    def api_actualizar_pedido(pid):
        pedido = Pedido.query.get_or_404(pid)

        data = request.get_json() or {}

        pedido.pais          = (data.get("pais")          or "").strip() or None
        pedido.localidad     = (data.get("localidad")     or "").strip() or None
        pedido.codigo_postal = (data.get("codigo_postal") or "").strip() or None
        pedido.barrio        = (data.get("barrio")        or "").strip() or None
        pedido.direccion     = (data.get("direccion")     or "").strip()
        pedido.telefono      = (data.get("telefono")      or "").strip()
        pedido.email         = (data.get("email")         or "").strip()
        pedido.observaciones = (data.get("observaciones") or "").strip() or None

        if not pedido.direccion:
            return {"error": "La dirección no puede estar vacía."}, 400

        if not pedido.telefono:
            return {"error": "El teléfono no puede estar vacío."}, 400

        db.session.commit()

        return {
            "ok": True,
            "pais":          pedido.pais          or "",
            "localidad":     pedido.localidad     or "",
            "codigo_postal": pedido.codigo_postal or "",
            "barrio":        pedido.barrio        or "",
            "direccion":     pedido.direccion,
            "telefono":      pedido.telefono,
            "email":         pedido.email         or "-",
            "observaciones": pedido.observaciones or "-"
        }, 200
    
    @app.delete("/api/pedidos/<int:pid>/sena")
    @login_required
    def api_eliminar_sena(pid):
        pedido = Pedido.query.get_or_404(pid)

        pedido.monto_sena = None
        pedido.forma_pago_preferida = None

        db.session.commit()

        return {"ok": True}, 200
    
    # ==========================================================================
    #  DASHBOARD
    #  Calcula KPIs (totales por estado), series temporales para los gráficos
    #  (7 / 30 / 90 días y evolución mensual), top-5 productos más vendidos y
    #  las últimas 5 filas para la tabla rápida.  Todo se inyecta en
    #  window.DASHBOARD_DATA dentro del template para que dashboard.js lo
    #  consuma sin llamadas AJAX adicionales.
    # ==========================================================================
    @app.get("/dashboard")
    @login_required
    def dashboard():
        base = Pedido.query.filter(Pedido.activo == True)

        total_pedidos = base.count()
        pendientes = base.filter(Pedido.estado == "PENDIENTE").count()
        en_curso = base.filter(Pedido.estado == "EN_CURSO").count()
        finalizados = base.filter(Pedido.estado == "FINALIZADO").count()

        # ===== Totales por estado ($) =====
        total_pendiente = db.session.query(
            func.coalesce(func.sum(Pedido.total), 0.0)
        ).filter_by(activo=True, estado="PENDIENTE").scalar()

        total_en_curso = db.session.query(
            func.coalesce(func.sum(Pedido.total), 0.0)
        ).filter_by(activo=True, estado="EN_CURSO").scalar()

        total_finalizado = db.session.query(
            func.coalesce(func.sum(Pedido.total), 0.0)
        ).filter_by(activo=True, estado="FINALIZADO").scalar()

        # Pedidos por día — múltiples períodos
        hoy = datetime.utcnow().date()

        def _serie_dias(n):
            dias = [hoy - timedelta(days=i) for i in range(n - 1, -1, -1)]
            labels, cant = [], []
            for d in dias:
                inicio = datetime(d.year, d.month, d.day)
                fin = inicio + timedelta(days=1)
                c = Pedido.query.filter(
                    Pedido.activo == True,
                    Pedido.created_at >= inicio,
                    Pedido.created_at < fin
                ).count()
                labels.append(d.strftime("%d/%m"))
                cant.append(int(c))
            return labels, cant

        serie_labels_7,  serie_cant_7  = _serie_dias(7)
        serie_labels_30, serie_cant_30 = _serie_dias(30)
        serie_labels_90, serie_cant_90 = _serie_dias(90)

        # mantener compatibilidad con variables antiguas
        serie_labels  = serie_labels_7
        serie_totales = []
        serie_cant    = serie_cant_7
        for d in [hoy - timedelta(days=i) for i in range(6, -1, -1)]:
            inicio = datetime(d.year, d.month, d.day)
            fin = inicio + timedelta(days=1)
            total_dia = db.session.query(func.coalesce(func.sum(Pedido.total), 0.0))\
                .filter(Pedido.activo == True, Pedido.created_at >= inicio, Pedido.created_at < fin).scalar()
            serie_totales.append(float(total_dia))

        # Evolución mensual últimos 6 meses (cantidad de pedidos)
        meses_labels, meses_cant = [], []
        for i in range(5, -1, -1):
            ref = hoy.replace(day=1) - timedelta(days=i * 28)
            mes_ini = ref.replace(day=1)
            if mes_ini.month == 12:
                mes_fin = mes_ini.replace(year=mes_ini.year + 1, month=1)
            else:
                mes_fin = mes_ini.replace(month=mes_ini.month + 1)
            c = Pedido.query.filter(
                Pedido.activo == True,
                Pedido.created_at >= datetime(mes_ini.year, mes_ini.month, mes_ini.day),
                Pedido.created_at < datetime(mes_fin.year, mes_fin.month, mes_fin.day)
            ).count()
            meses_labels.append(mes_ini.strftime("%b %Y"))
            meses_cant.append(c)

        # ===== Productos más vendidos =====
        productos_data = (
            db.session.query(
                PedidoItem.descripcion,
                func.sum(PedidoItem.cantidad)
            )
            .join(Pedido, Pedido.id == PedidoItem.pedido_id)
            .filter(Pedido.activo == True)
            .group_by(PedidoItem.descripcion)
            .order_by(func.sum(PedidoItem.cantidad).desc())
            .limit(5)
            .all()
        )

        productos_labels = [p[0] for p in productos_data]
        productos_cantidades = [int(p[1]) for p in productos_data]

        ultimos = Pedido.query.filter(Pedido.activo == True).order_by(Pedido.id.desc()).limit(5).all()
        pedidos_modal = Pedido.query.filter(Pedido.activo == True).order_by(Pedido.id.desc()).all()

        return render_template(
            "dashboard.html",
            total_pedidos=total_pedidos,
            pendientes=pendientes,
            en_curso=en_curso,
            finalizados=finalizados,
            total_pendiente=total_pendiente,
            total_en_curso=total_en_curso,
            total_finalizado=total_finalizado,
            serie_labels=serie_labels,
            serie_totales=serie_totales,
            serie_cant=serie_cant,
            serie_labels_7=serie_labels_7,   serie_cant_7=serie_cant_7,
            serie_labels_30=serie_labels_30, serie_cant_30=serie_cant_30,
            serie_labels_90=serie_labels_90, serie_cant_90=serie_cant_90,
            meses_labels=meses_labels,
            meses_cant=meses_cant,
            productos_labels=productos_labels,
            productos_cantidades=productos_cantidades,
            ultimos=ultimos,
            pedidos_modal=pedidos_modal,
        )
    
    # ==========================================================================
    #  API JSON — Pedidos
    #  Endpoints consumidos por el frontend JS para el modal de detalle,
    #  el modal de tabla expandida y el kanban (drag & drop de estado).
    # ==========================================================================
    @app.get("/api/pedidos")
    @login_required
    def api_pedidos():
        estado = request.args.get("estado")
        cliente = request.args.get("cliente")

        query = Pedido.query.filter(Pedido.activo == True)

        if estado and estado != "TODOS":
            query = query.filter_by(estado=estado)

        if cliente:
            query = query.filter(Pedido.cliente.ilike(f"%{cliente}%"))

        pedidos = query.order_by(Pedido.id.desc()).all()

        data = []
        for p in pedidos:
            estado = p.estado

            pend = "-"
            curso = "-"
            fin = "-"

            if estado == "PENDIENTE":
                pend = p.created_at.strftime("%d/%m/%Y") if p.created_at else "-"
            elif estado == "EN_CURSO":
                curso = p.en_curso_at.strftime("%d/%m/%Y") if p.en_curso_at else "-"
            elif estado == "FINALIZADO":
                fin = p.finalizado_at.strftime("%d/%m/%Y") if p.finalizado_at else "-"

            data.append({
                "id": p.id,
                "cliente": p.cliente,
                "forma_pago": p.forma_pago_preferida or "-",
                "sena": "Sí" if p.monto_sena else "No",
                "telefono": p.telefono,
                "estado": p.estado,
                "total": float(p.total),
                "pendiente_at": pend,
                "en_curso_at": curso,
                "finalizado_at": fin,
            })

        return {"pedidos": data}
    
    # ==========================================================================
    #  GENERACIÓN DE PDFs
    #  _generar_pdf_presupuesto — presupuesto para el cliente (A4, con logo,
    #    datos del cliente, detalle de ítems, total y condiciones de pago).
    #    Se accede vía token público (/p/<token>) o con login (/pedidos/<id>/pdf).
    #  pedido_remito — remito interno (A4) con tabla de ítems, casilleros de
    #    firma y sección de observaciones.  Solo accesible con login.
    # ==========================================================================
    def _generar_pdf_presupuesto(p):
        """Genera y devuelve el PDF de presupuesto para un objeto Pedido."""
        buf = BytesIO()
        cv  = canvas.Canvas(buf, pagesize=A4)
        W, H = A4
        MG   = 42
        UW   = W - 2 * MG
        FOOT_H = 28

        NAVY   = _PDF_NAVY
        ORANGE = _PDF_ORANGE
        LGRAY  = _PDF_LGRAY
        MGRAY  = _PDF_MGRAY
        WHITE  = _PDF_WHITE
        DARK   = _PDF_DARK
        LLINE  = _PDF_LLINE

        def ars(n):
            try:    return "$" + f"{int(round(float(n or 0))):,}".replace(",", ".")
            except: return "$0"

        def word_wrap(text, max_chars):
            words, lines, cur = str(text).split(), [], ""
            for w in words:
                if len(cur) + len(w) + 1 > max_chars:
                    if cur: lines.append(cur.rstrip())
                    cur = w + " "
                else:
                    cur += w + " "
            if cur.strip(): lines.append(cur.rstrip())
            return lines or [""]

        # ── HEADER BAND ────────────────────────────────────────────
        HDR_H = 90
        cv.setFillColor(NAVY)
        cv.rect(0, H - HDR_H, W, HDR_H, fill=1, stroke=0)

        logo = os.path.join(current_app.root_path, "static", "img", "logo.png")
        if os.path.exists(logo):
            try:
                cv.drawImage(logo, MG, H - HDR_H + 16, width=56, height=56,
                             preserveAspectRatio=True, mask="auto")
            except Exception:
                pass

        cv.setFillColor(WHITE)
        cv.setFont("Helvetica-Bold", 14)
        cv.drawString(MG + 68, H - 33, "S. VALVO Y CIA")
        cv.setFont("Helvetica", 8.5)
        cv.drawString(MG + 68, H - 47, "Muebles a medida")
        cv.drawString(MG + 68, H - 60, "Ruta 34 y Carlos Pellegrini, Rafaela")

        cv.setFillColor(ORANGE)
        cv.setFont("Helvetica-Bold", 20)
        cv.drawRightString(W - MG, H - 40, "PRESUPUESTO")
        cv.setFillColor(WHITE)
        cv.setFont("Helvetica", 9)
        cv.drawRightString(W - MG, H - 57, f"Fecha: {datetime.now().strftime('%d/%m/%Y')}")

        cv.setStrokeColor(ORANGE)
        cv.setLineWidth(3)
        cv.line(0, H - HDR_H, W, H - HDR_H)
        cv.setLineWidth(0.5)
        cv.setStrokeColor(DARK)

        y = H - HDR_H - 26

        # ── DATOS DEL CLIENTE ──────────────────────────────────────
        partes_dir = [x for x in [p.direccion, p.barrio, p.localidad,
                                   p.codigo_postal, p.pais] if x]
        dir_str = ", ".join(partes_dir) if partes_dir else "-"
        rows_cli = [("Nombre:", str(p.cliente or "-")),
                    ("Telefono:", str(p.telefono or "-")),
                    ("Direccion:", dir_str)]
        if p.email:
            rows_cli.append(("E-mail:", str(p.email)))

        LINE_H = 15
        box_h = len(rows_cli) * LINE_H + 30
        cv.setFillColor(LGRAY)
        cv.roundRect(MG, y - box_h + 16, UW, box_h, 5, fill=1, stroke=0)
        cv.setFillColor(NAVY)
        cv.setFont("Helvetica-Bold", 8.5)
        cv.drawString(MG + 12, y, "DATOS DEL CLIENTE")
        y -= LINE_H
        for lbl, val in rows_cli:
            cv.setFillColor(MGRAY)
            cv.setFont("Helvetica-Bold", 8.5)
            cv.drawString(MG + 12, y, lbl)
            cv.setFillColor(DARK)
            cv.setFont("Helvetica", 9)
            cv.drawString(MG + 82, y, val[:80])
            y -= LINE_H
        y -= 20

        # ── DETALLE COMBINADO ──────────────────────────────────────
        partes_items = []
        for it in p.items:
            desc = str(it.descripcion or "").strip()
            cant = f"x{it.cantidad}"
            if it.metros:
                cant += f" ({it.metros:.2f} m)"
            partes_items.append(f"{desc} {cant}")
        texto_items = " | ".join(partes_items) if partes_items else "-"

        MAX_CHARS = 88
        lineas_texto = word_wrap(texto_items, MAX_CHARS)
        det_box_h = len(lineas_texto) * 13 + 38
        cv.setFillColor(LGRAY)
        cv.roundRect(MG, y - det_box_h + 18, UW, det_box_h, 5, fill=1, stroke=0)

        cv.setFillColor(NAVY)
        cv.rect(MG, y - 2, UW, 18, fill=1, stroke=0)
        cv.setFillColor(WHITE)
        cv.setFont("Helvetica-Bold", 8.5)
        cv.drawString(MG + 12, y + 4, "DESCRIPCION DEL PEDIDO")
        y -= 6

        cv.setFillColor(DARK)
        cv.setFont("Helvetica", 9)
        for linea in lineas_texto:
            y -= 13
            if y < FOOT_H + 50:
                cv.showPage(); y = H - MG
            cv.drawString(MG + 12, y, linea)
        y -= 20

        # ── TOTAL BAR ──────────────────────────────────────────────
        if y < FOOT_H + 60:
            cv.showPage(); y = H - MG
        cv.setStrokeColor(ORANGE)
        cv.setLineWidth(1.2)
        cv.line(MG, y, W - MG, y)
        cv.setLineWidth(0.5)
        cv.setFillColor(NAVY)
        cv.rect(MG, y - 22, UW, 28, fill=1, stroke=0)
        cv.setFillColor(WHITE)
        cv.setFont("Helvetica-Bold", 13)
        cv.drawRightString(W - MG - 14, y - 10, f"TOTAL:   {ars(p.total)}")
        y -= 42

        # ── CONDICIONES ────────────────────────────────────────────
        if y < FOOT_H + 110:
            cv.showPage(); y = H - MG
        COND_H = 82
        cv.setStrokeColor(LLINE)
        cv.setFillColor(WHITE)
        cv.setLineWidth(0.8)
        cv.roundRect(MG, y - COND_H + 16, UW, COND_H, 5, fill=1, stroke=1)
        cv.setLineWidth(0.5)

        cv.setFillColor(NAVY)
        cv.setFont("Helvetica-Bold", 9)
        cv.drawString(MG + 12, y, "Condiciones de Pago:")
        y -= 14
        cv.setFillColor(DARK)
        cv.setFont("Helvetica", 9)
        cv.drawString(MG + 12, y,
            "Total de Contado (entrega 50% - saldo contraentrega de mercaderia)")
        y -= 20
        cv.setFillColor(NAVY)
        cv.setFont("Helvetica-Bold", 9)
        cv.drawString(MG + 12, y, "Validez del presupuesto: 5 dias")
        y -= 14
        cv.setFillColor(DARK)
        cv.setFont("Helvetica", 9)
        cv.drawString(MG + 12, y, "Ver promociones con tarjetas del momento")

        # ── FOOTER ─────────────────────────────────────────────────
        cv.setFillColor(NAVY)
        cv.rect(0, 0, W, FOOT_H, fill=1, stroke=0)
        cv.setFillColor(WHITE)
        cv.setFont("Helvetica", 7.5)
        cv.drawCentredString(W / 2, 10,
            "S. Valvo y Cia  |  Ruta 34 y Carlos Pellegrini, Rafaela  |  @s.valvo.cia")

        cv.showPage()
        cv.save()
        buf.seek(0)
        return send_file(buf, as_attachment=True,
                         download_name=f"presupuesto_{p.id}.pdf",
                         mimetype="application/pdf")

    @app.get("/p/<string:token>")
    def presupuesto_publico(token):
        """Ruta pública: cualquiera con el token puede descargar el presupuesto."""
        p = Pedido.query.filter_by(token_pdf=token, activo=True).first_or_404()
        return _generar_pdf_presupuesto(p)

    @app.get("/pedidos/<int:pid>/pdf")
    @login_required
    def pedido_pdf(pid):
        p = Pedido.query.get_or_404(pid)
        return _generar_pdf_presupuesto(p)

    @app.get("/pedidos/<int:pid>/remito")
    @login_required
    def pedido_remito(pid):
        p   = Pedido.query.get_or_404(pid)
        buf = BytesIO()
        cv  = canvas.Canvas(buf, pagesize=A4)
        W, H = A4
        MG   = 36
        UW   = W - 2 * MG

        NAVY   = _PDF_NAVY
        ORANGE = _PDF_ORANGE
        LGRAY  = _PDF_LGRAY
        MGRAY  = _PDF_MGRAY
        WHITE  = _PDF_WHITE
        DARK   = _PDF_DARK
        LLINE  = _PDF_LLINE

        # ── HEADER ─────────────────────────────────────────────────
        HDR_H = 68
        cv.setFillColor(NAVY)
        cv.rect(0, H - HDR_H, W, HDR_H, fill=1, stroke=0)

        logo = os.path.join(current_app.root_path, "static", "img", "logo.png")
        if os.path.exists(logo):
            try:
                cv.drawImage(logo, MG, H - HDR_H + 8, width=48, height=48,
                             preserveAspectRatio=True, mask="auto")
            except Exception:
                pass

        cv.setFillColor(WHITE)
        cv.setFont("Helvetica-Bold", 13)
        cv.drawString(MG + 58, H - 28, "S. VALVO Y CIA")
        cv.setFont("Helvetica", 8)
        cv.drawString(MG + 58, H - 40, "Muebles a medida")

        # REMITO label derecha
        cv.setFillColor(ORANGE)
        cv.setFont("Helvetica-Bold", 18)
        cv.drawRightString(W - MG, H - 30, "REMITO INTERNO")
        cv.setFillColor(WHITE)
        cv.setFont("Helvetica", 8.5)
        cv.drawRightString(W - MG, H - 44, f"{datetime.now().strftime('%d/%m/%Y')}")
        estado_txt = {"PENDIENTE": "Pendiente", "EN_CURSO": "En Curso", "FINALIZADO": "Finalizado"}.get(p.estado, p.estado)
        cv.drawRightString(W - MG, H - 56, f"Estado: {estado_txt}")

        cv.setStrokeColor(ORANGE)
        cv.setLineWidth(2.5)
        cv.line(0, H - HDR_H, W, H - HDR_H)
        cv.setLineWidth(0.5)
        cv.setStrokeColor(DARK)

        y = H - HDR_H - 20

        # ── INFO 2 COLUMNAS ─────────────────────────────────────────
        col_w = UW / 2 - 6
        box_h = 72
        # Col izquierda: cliente
        cv.setFillColor(LGRAY)
        cv.roundRect(MG, y - box_h + 14, col_w, box_h, 4, fill=1, stroke=0)
        cv.setFillColor(NAVY)
        cv.setFont("Helvetica-Bold", 8)
        cv.drawString(MG + 8, y, "CLIENTE")
        y2 = y - 13
        for lbl, val in [
            ("Nombre:", str(p.cliente   or "-")),
            ("Tel:",    str(p.telefono  or "-")),
            ("Email:",  str(p.email     or "-")),
        ]:
            cv.setFillColor(MGRAY)
            cv.setFont("Helvetica-Bold", 7.5)
            cv.drawString(MG + 8, y2, lbl)
            cv.setFillColor(DARK)
            cv.setFont("Helvetica", 8)
            cv.drawString(MG + 40, y2, val[:40])
            y2 -= 12

        # Col derecha: dirección
        rx = MG + col_w + 12
        cv.setFillColor(LGRAY)
        cv.roundRect(rx, y - box_h + 14, col_w, box_h, 4, fill=1, stroke=0)
        cv.setFillColor(NAVY)
        cv.setFont("Helvetica-Bold", 8)
        cv.drawString(rx + 8, y, "ENTREGA")
        y3 = y - 13
        # Dividir dirección en múltiples líneas si es larga
        dir_parts = [x for x in [p.direccion, p.barrio, p.localidad,
                                   p.codigo_postal, p.pais] if x]
        for part in dir_parts[:4]:
            cv.setFillColor(DARK)
            cv.setFont("Helvetica", 8)
            cv.drawString(rx + 8, y3, str(part)[:40])
            y3 -= 12

        y = y - box_h - 20

        # ── TABLA DE ÍTEMS ──────────────────────────────────────────
        # Encabezado de tabla — 4 columnas: # | Descripción | Cant. | Metros
        cols = [
            (MG,        24,   "#"),
            (MG + 24,  350,   "Descripcion"),
            (MG + 374,  75,   "Cant."),
            (MG + 449,  74,   "Metros"),
        ]
        ROW_H = 16

        def draw_table_header(y_pos):
            cv.setFillColor(NAVY)
            cv.rect(MG, y_pos - 3, UW, 18, fill=1, stroke=0)
            cv.setFillColor(WHITE)
            cv.setFont("Helvetica-Bold", 8.5)
            for (cx, cw, label) in cols:
                if label in ("#", "Cant.", "Metros"):
                    cv.drawCentredString(cx + cw / 2, y_pos + 2, label)
                else:
                    cv.drawString(cx + 4, y_pos + 2, label)

        draw_table_header(y)
        y -= 8

        for i, it in enumerate(p.items):
            if y < 100:
                cv.showPage()
                y = H - MG
                draw_table_header(y)
                y -= 8

            if i % 2 == 1:
                cv.setFillColor(LGRAY)
                cv.rect(MG, y - ROW_H + 5, UW, ROW_H, fill=1, stroke=0)

            cv.setFillColor(DARK)
            cv.setFont("Helvetica", 8.5)
            cv.drawCentredString(MG + 12,      y - 4, str(i + 1))
            cv.drawString(MG + 28,             y - 4, str(it.descripcion or "-")[:60])
            cv.drawCentredString(MG + 374 + 37, y - 4, str(it.cantidad))
            metros_str = f"{it.metros:.2f}" if it.metros else "-"
            cv.drawCentredString(MG + 449 + 37, y - 4, metros_str)

            cv.setStrokeColor(LLINE)
            cv.line(MG, y - ROW_H + 5, W - MG, y - ROW_H + 5)
            cv.setStrokeColor(DARK)
            y -= ROW_H

        y -= 16

        # ── OBSERVACIONES ──────────────────────────────────────────
        if p.observaciones:
            if y < 80:
                cv.showPage(); y = H - MG
            cv.setFillColor(LGRAY)
            cv.roundRect(MG, y - 50, UW, 62, 4, fill=1, stroke=0)
            cv.setFillColor(NAVY)
            cv.setFont("Helvetica-Bold", 8.5)
            cv.drawString(MG + 10, y, "OBSERVACIONES:")
            y -= 13
            cv.setFillColor(DARK)
            cv.setFont("Helvetica", 8.5)
            for line in str(p.observaciones).splitlines()[:4]:
                cv.drawString(MG + 10, y, line[:100])
                y -= 12
            y -= 10

        # ── FIRMA / ENTREGA ────────────────────────────────────────
        if y < 80:
            cv.showPage(); y = H - MG
        y -= 10
        cv.setStrokeColor(MGRAY)
        cv.setLineWidth(0.5)
        fw = UW / 3 - 10
        for i, label in enumerate(["Entregado por:", "Recibido por:", "Fecha de entrega:"]):
            fx = MG + i * (fw + 15)
            cv.line(fx, y - 20, fx + fw, y - 20)
            cv.setFillColor(MGRAY)
            cv.setFont("Helvetica", 7.5)
            cv.drawString(fx, y - 30, label)

        # ── FOOTER ─────────────────────────────────────────────────
        cv.setFillColor(NAVY)
        cv.rect(0, 0, W, 28, fill=1, stroke=0)
        cv.setFillColor(WHITE)
        cv.setFont("Helvetica", 7.5)
        cv.drawCentredString(W / 2, 10, "S. Valvo y Cia  |  Ruta 34 y Carlos Pellegrini, Rafaela  |  @s.valvo.cia")

        cv.showPage()
        cv.save()
        buf.seek(0)
        return send_file(buf, as_attachment=True,
                         download_name=f"remito_{p.id}.pdf",
                         mimetype="application/pdf")

    @app.post("/pedidos/mover/<int:id>")
    @login_required
    def mover_pedido(id):
        data = request.get_json() or {}
        pedido = Pedido.query.get_or_404(id)

        nuevo_estado = (data.get("estado") or "").upper()
        if nuevo_estado not in ["PENDIENTE", "EN_CURSO", "FINALIZADO"]:
            return {"error": "Estado inválido"}, 400

        if pedido.estado == nuevo_estado:
            return {"ok": True}, 200

        ahora = datetime.utcnow()

        if nuevo_estado == "PENDIENTE":
            if hasattr(pedido, "pendiente_at"):
                pedido.pendiente_at = ahora
            else:
                pedido.created_at = ahora

        elif nuevo_estado == "EN_CURSO":
            pedido.en_curso_at = ahora

        elif nuevo_estado == "FINALIZADO":
            pedido.finalizado_at = ahora

        if nuevo_estado == "FINALIZADO" and not pedido.stock_descontado:
            _decrementar_stock_pedido(pedido)
            pedido.stock_descontado = True

        pedido.estado = nuevo_estado
        db.session.commit()

        if nuevo_estado == "PENDIENTE":
            fecha = (pedido.pendiente_at if hasattr(pedido, "pendiente_at") else pedido.created_at)
        elif nuevo_estado == "EN_CURSO":
            fecha = pedido.en_curso_at
        else:
            fecha = pedido.finalizado_at

        return {
            "ok": True,
            "estado": nuevo_estado,
            "fecha_estado": fecha.strftime("%d/%m/%Y") if fecha else "-"
        }, 200
    
    @app.post("/pedidos/eliminar/<int:id>")
    @login_required
    def eliminar_pedido(id):
        try:
            pedido = Pedido.query.get_or_404(id)

            if pedido.estado in ["PENDIENTE", "EN_CURSO"]:
                db.session.delete(pedido)
            else:
                pedido.activo = False

            db.session.commit()
            return "", 204

        except Exception as e:
            return str(e), 500
    
    # ==========================================================================
    #  PAGOS
    #  Registro de pagos parciales/totales asociados a un pedido.
    #  Soporta efectivo, transferencia y tarjeta (con cuotas y monto/cuota).
    #  Cada pago puede tener un comprobante adjunto (PDF o imagen) que se
    #  almacena en instance/uploads/comprobantes/ con nombre único.
    # ==========================================================================
    @app.post("/api/pedidos/<int:pid>/pagos")
    @login_required
    def api_crear_pago(pid):
        pedido = Pedido.query.get_or_404(pid)

        metodo = (request.form.get("metodo") or "").strip()
        fecha_str = (request.form.get("fecha_pago") or "").strip()
        monto_str = (request.form.get("monto_pagado") or "").strip()

        if not metodo:
            return {"error": "metodo requerido"}, 400
        if not fecha_str:
            return {"error": "fecha_pago requerida"}, 400
        if not monto_str:
            return {"error": "monto_pagado requerido"}, 400

        try:
            monto_pagado = float(monto_str)
            if monto_pagado <= 0:
                raise ValueError()
        except ValueError:
            return {"error": "monto_pagado inválido"}, 400

        try:
            fecha_pago = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        except ValueError:
            return {"error": "fecha_pago inválida"}, 400

        cuotas = request.form.get("cuotas")
        monto_cuota = request.form.get("monto_cuota")

        pago = Pago(
            pedido_id=pedido.id,
            metodo=metodo,
            monto_pagado=monto_pagado,
            fecha_pago=fecha_pago
        )

        if metodo == "Tarjeta":
            try:
                c = int(cuotas or 0)
                mc = float(monto_cuota or 0)
                if c < 1 or mc <= 0:
                    raise ValueError()
            except ValueError:
                return {"error": "cuotas/monto_cuota inválidos"}, 400

            pago.cuotas = c
            pago.monto_cuota = mc

        db.session.add(pago)
        db.session.flush()  # pago.id

        # comprobante (opcional)
        file = request.files.get("comprobante")
        comprobante_url = None

        if file and file.filename:
            # validar tipo
            allowed = {"application/pdf", "image/png", "image/jpeg"}
            if file.mimetype not in allowed:
                return {"error": "Tipo de archivo no permitido"}, 400

            uploads_dir = app.config.get("UPLOADS_DIR")
            if not uploads_dir:
                return {"error": "Uploads no configurado"}, 500

            original = file.filename
            safe = secure_filename(original)
            unique = f"pago_{pago.id}_{int(datetime.utcnow().timestamp())}_{safe}"
            path = os.path.join(uploads_dir, unique)
            file.save(path)

            comp = PagoComprobante(
                pago_id=pago.id,
                filename=unique,
                original_name=original,
                mimetype=file.mimetype,
                size_bytes=getattr(file, "content_length", None)
            )
            db.session.add(comp)

            comprobante_url = url_for("ver_comprobante", filename=unique)

        db.session.commit()

        return {
            "ok": True,
            "pago_id": pago.id,
            "comprobante_url": comprobante_url
        }, 201
    
    @app.get("/uploads/comprobantes/<path:filename>")
    @login_required
    def ver_comprobante(filename):
        uploads_dir = app.config.get("UPLOADS_DIR")
        if not uploads_dir:
            return "Uploads no configurado", 500
        full = os.path.join(uploads_dir, filename)
        if not os.path.exists(full):
            return "No encontrado", 404
        return send_file(full)
    
    @app.delete("/api/pagos/<int:pay_id>")
    @login_required
    def api_eliminar_pago(pay_id):
        pago = Pago.query.get_or_404(pay_id)
        db.session.delete(pago)
        db.session.commit()
        return {"ok": True}, 200

    # ================================================================
    # CALENDARIO / RECORDATORIOS
    # ================================================================

    @app.get("/calendario")
    @login_required
    def calendario():
        return render_template("calendario.html")

    @app.get("/api/recordatorios")
    @login_required
    def api_recordatorios_listar():
        anio = request.args.get("anio", type=int)
        mes  = request.args.get("mes",  type=int)
        if anio and mes:
            desde = date(anio, mes, 1)
            if mes == 12:
                hasta = date(anio + 1, 1, 1)
            else:
                hasta = date(anio, mes + 1, 1)
            recs = Recordatorio.query.filter(
                Recordatorio.fecha >= desde,
                Recordatorio.fecha <  hasta
            ).order_by(Recordatorio.fecha, Recordatorio.hora).all()
        else:
            recs = Recordatorio.query.order_by(Recordatorio.fecha, Recordatorio.hora).all()
        return jsonify([r.to_dict() for r in recs])

    @app.get("/api/recordatorios/proximos")
    @login_required
    def api_recordatorios_proximos():
        hoy = date.today()
        limite = hoy + timedelta(days=7)
        recs = Recordatorio.query.filter(
            Recordatorio.fecha >= hoy,
            Recordatorio.fecha <= limite,
            Recordatorio.completado == False
        ).order_by(Recordatorio.fecha, Recordatorio.hora).limit(5).all()
        return jsonify([r.to_dict() for r in recs])

    @app.get("/api/recordatorios/hoy")
    @login_required
    def api_recordatorios_hoy():
        hoy = date.today()
        recs = Recordatorio.query.filter(
            Recordatorio.fecha == hoy,
            Recordatorio.completado == False
        ).order_by(Recordatorio.hora).all()
        return jsonify([r.to_dict() for r in recs])

    @app.post("/api/recordatorios")
    @login_required
    def api_recordatorio_crear():
        data = request.get_json() or {}
        titulo = (data.get("titulo") or "").strip()
        if not titulo:
            return jsonify({"error": "titulo requerido"}), 400
        fecha_str = (data.get("fecha") or "").strip()
        try:
            fecha = date.fromisoformat(fecha_str)
        except ValueError:
            return jsonify({"error": "fecha inválida"}), 400
        rec = Recordatorio(
            titulo=titulo,
            descripcion=(data.get("descripcion") or "").strip() or None,
            fecha=fecha,
            hora=(data.get("hora") or "").strip() or None,
            color=data.get("color") or "azul",
            created_at=datetime.utcnow(),
        )
        db.session.add(rec)
        db.session.commit()
        return jsonify(rec.to_dict()), 201

    @app.patch("/api/recordatorios/<int:rid>")
    @login_required
    def api_recordatorio_actualizar(rid):
        rec  = Recordatorio.query.get_or_404(rid)
        data = request.get_json() or {}
        if "titulo" in data:
            titulo = (data["titulo"] or "").strip()
            if not titulo:
                return jsonify({"error": "titulo requerido"}), 400
            rec.titulo = titulo
        if "descripcion" in data:
            rec.descripcion = (data["descripcion"] or "").strip() or None
        if "fecha" in data:
            try:
                rec.fecha = date.fromisoformat(data["fecha"])
            except ValueError:
                return jsonify({"error": "fecha inválida"}), 400
        if "hora" in data:
            rec.hora = (data["hora"] or "").strip() or None
        if "color" in data:
            rec.color = data["color"] or "azul"
        if "completado" in data:
            rec.completado = bool(data["completado"])
        db.session.commit()
        return jsonify(rec.to_dict())

    @app.delete("/api/recordatorios/<int:rid>")
    @login_required
    def api_recordatorio_eliminar(rid):
        rec = Recordatorio.query.get_or_404(rid)
        db.session.delete(rec)
        db.session.commit()
        return jsonify({"ok": True})
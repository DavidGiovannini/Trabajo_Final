from flask import render_template, request, redirect, url_for, flash, send_file, jsonify
from flask_login import login_required
from . import db
from .models import Producto, Pedido, PedidoItem, Pago, PagoComprobante, PrecioMueble, AdicionalMueble, ConfiguracionPrecio, ConfiguracionGeneral
from sqlalchemy import func
from datetime import datetime, timedelta, date
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from sqlalchemy import text
import os
from werkzeug.utils import secure_filename
import json

def _decrementar_stock_pedido(pedido):
    for item in pedido.items:
        if item.producto_id:
            prod = Producto.query.get(item.producto_id)
            if prod is not None and prod.stock is not None:
                prod.stock = max(0, prod.stock - item.cantidad)


def register_routes(app):
    @app.get("/")
    def home():
        return redirect(url_for("dashboard"))

    # ---------- PRODUCTOS ----------
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

    @app.post("/productos/<int:pid>/delete")
    @login_required
    def productos_delete(pid):
        p = Producto.query.get_or_404(pid)
        db.session.delete(p)
        db.session.commit()
        flash("Producto eliminado.", "success")
        return redirect(url_for("productos"))

    # ---------- CONFIGURACION ----------
    @app.get("/configuracion")
    @login_required
    def configuracion():

        standard = PrecioMueble.query.filter_by(linea="standard").order_by(PrecioMueble.medida).all()
        roble = PrecioMueble.query.filter_by(linea="roble").order_by(PrecioMueble.medida).all()
        lujo = PrecioMueble.query.filter_by(linea="lujo").order_by(PrecioMueble.medida).all()
        glaciar = PrecioMueble.query.filter_by(linea="glaciar").order_by(PrecioMueble.medida).all()

        adicionales_standard = AdicionalMueble.query.filter_by(linea="standard").all()
        adicionales_roble = AdicionalMueble.query.filter_by(linea="roble").all()
        adicionales_lujo = AdicionalMueble.query.filter_by(linea="lujo").all()
        adicionales_glaciar = AdicionalMueble.query.filter_by(linea="glaciar").all()

        config = ConfiguracionGeneral.query.first()

        return render_template(
            "configuracion.html",
            standard=standard,
            roble=roble,
            lujo=lujo,
            glaciar=glaciar,  
            adicionales_standard=adicionales_standard,
            adicionales_roble=adicionales_roble,
            adicionales_lujo=adicionales_lujo,
            adicionales_glaciar=adicionales_glaciar,
            config_fecha = config.fecha_actualizacion if config else None
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

        nombres = request.form.getlist("nombre_adicional[]")
        precios = request.form.getlist("precio_adicional[]")

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

                nombre = nombres[idx_adicional]
                precio = float(precios[idx_adicional] or 0)

                if ref == "new":
                    a = AdicionalMueble(
                        linea=linea,
                        nombre=nombre,
                        precio=precio
                    )
                    db.session.add(a)

                else:
                    a = AdicionalMueble.query.get(int(ref))
                    if a:
                        a.nombre = nombre
                        a.precio = precio

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
            print("ERROR DELETE:", e)
            return {"error": str(e)}, 500

    # ---------- PRESUPUESTADOR ----------
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
                "precio": a.precio
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

        if not cliente or not telefono:
            flash("Completá Cliente y Teléfono.", "warning")
            return redirect(url_for("presupuestador"))
        
        if not direccion:
            flash("Completá la Dirección.", "warning")
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
            direccion=direccion,
            observaciones=observaciones,
            total=0.0,
            forma_pago_preferida=forma_pago,
            monto_sena=monto_sena,
            estado="PENDIENTE",
            created_at=ahora,
            pendiente_at=ahora
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

    # ---------- PEDIDOS ----------
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

        return {
            "id": p.id,
            "cliente": p.cliente,
            "telefono": p.telefono or "-",
            "email": p.email or "-",
            "direccion": p.direccion or "-",
            "observaciones": p.observaciones or "-",
            "forma_pago": p.forma_pago_preferida or "-",
            "monto_sena": float(p.monto_sena) if p.monto_sena else None,
            "total_pagado": float(total_pagado),
            "debe": float(debe),                 # 👈 sigue igual
            "total": float(p.total or 0.0),
            "estado": p.estado,
            "items": items,
            "pagos": pagos
        }
    
    @app.patch("/api/pedidos/<int:pid>")
    @login_required
    def api_actualizar_pedido(pid):
        pedido = Pedido.query.get_or_404(pid)

        data = request.get_json() or {}

        pedido.direccion = (data.get("direccion") or "").strip()
        pedido.telefono = (data.get("telefono") or "").strip()
        pedido.email = (data.get("email") or "").strip()
        pedido.observaciones = (data.get("observaciones") or "").strip() or None

        if not pedido.direccion:
            return {"error": "La dirección no puede estar vacía."}, 400

        if not pedido.telefono:
            return {"error": "El teléfono no puede estar vacío."}, 400

        db.session.commit()

        return {
            "ok": True,
            "direccion": pedido.direccion,
            "telefono": pedido.telefono,
            "email": pedido.email or "-",
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

        # Ventas / totales últimos 7 días (por fecha de creación)
        hoy = datetime.utcnow().date()
        dias = [hoy - timedelta(days=i) for i in range(6, -1, -1)]

        serie_labels = [d.strftime("%d/%m") for d in dias]
        serie_totales = []
        serie_cant = []

        for d in dias:
            inicio = datetime(d.year, d.month, d.day)
            fin = inicio + timedelta(days=1)
            total_dia = db.session.query(func.coalesce(func.sum(Pedido.total), 0.0))\
                .filter(Pedido.activo == True, Pedido.created_at >= inicio, Pedido.created_at < fin).scalar()
            cant_dia = Pedido.query.filter(Pedido.activo == True, Pedido.created_at >= inicio, Pedido.created_at < fin).count()
            serie_totales.append(float(total_dia))
            serie_cant.append(int(cant_dia))

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
            productos_labels=productos_labels,
            productos_cantidades=productos_cantidades,
            ultimos=ultimos,
            pedidos_modal=pedidos_modal,
        )
    
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
    
    @app.get("/pedidos/<int:pid>/pdf")
    @login_required
    def pedido_pdf(pid):
        p = Pedido.query.get_or_404(pid)

        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        w, h = A4

        y = h - 50
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, y, "Comprobante de Pedido")
        y -= 25

        c.setFont("Helvetica", 11)
        c.drawString(50, y, f"Pedido: #{p.id}")
        y -= 16
        c.drawString(50, y, f"Cliente: {p.cliente}")
        y -= 16
        c.drawString(50, y, f"Teléfono: {p.telefono}")
        y -= 16
        c.drawString(50, y, f"Dirección: {p.direccion}")
        y -= 16
        c.drawString(50, y, f"Estado: {p.estado}")
        y -= 22

        if p.observaciones:
            c.setFont("Helvetica-Bold", 11)
            c.drawString(50, y, "Observaciones:")
            y -= 16
            c.setFont("Helvetica", 11)
            # simple wrap
            text = c.beginText(50, y)
            for line in str(p.observaciones).splitlines():
                text.textLine(line)
            c.drawText(text)
            y = text.getY() - 10

        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y, "Detalle:")
        y -= 18

        c.setFont("Helvetica", 11)
        for it in p.items:
            linea = f"- {it.descripcion} | Cant: {it.cantidad} | Subtotal: ${it.subtotal:.2f}"
            c.drawString(55, y, linea[:110])
            y -= 14
            if y < 80:
                c.showPage()
                y = h - 50

        y -= 10
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y, f"TOTAL: ${p.total:.2f}")

        c.showPage()
        c.save()

        buffer.seek(0)
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"pedido_{p.id}.pdf",
            mimetype="application/pdf"
        )

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

            print("Estado:", pedido.estado)
            print("Activo:", pedido.activo)

            if pedido.estado in ["PENDIENTE", "EN_CURSO"]:
                db.session.delete(pedido)
            else:
                pedido.activo = False

            db.session.commit()
            return "", 204

        except Exception as e:
            print("ERROR:", e)
            return str(e), 500
    
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

        # (opcional) si querés, podés validar que el pedido esté activo
        pedido = Pedido.query.get_or_404(pago.pedido_id)

        db.session.delete(pago)
        db.session.commit()

        return {"ok": True}, 200
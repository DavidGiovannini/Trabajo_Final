from flask import render_template, request, redirect, url_for, flash, send_file
from flask_login import login_required
from . import db
from .models import Producto, PrecioPorMetro, Pedido, PedidoItem, Pago, PagoComprobante
from sqlalchemy import func
from datetime import datetime, timedelta, date
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import os
from werkzeug.utils import secure_filename

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
        material = request.form.get("material", "").strip()
        por_metro = request.form.get("por_metro") == "on"
        precio_str = request.form.get("precio", "0").strip()

        if not nombre or not material:
            flash("Completá Tipo y Material.", "warning")
            return redirect(url_for("productos"))

        try:
            precio = 0.0 if por_metro else float(precio_str)
        except ValueError:
            flash("Precio inválido.", "danger")
            return redirect(url_for("productos"))

        p = Producto(nombre=nombre, material=material, por_metro=por_metro, precio=precio)
        db.session.add(p)
        db.session.commit()
        flash("Producto agregado.", "success")
        return redirect(url_for("productos"))

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
        rows = PrecioPorMetro.query.order_by(PrecioPorMetro.material.asc()).all()
        return render_template("configuracion.html", rows=rows)

    @app.post("/configuracion")
    @login_required
    def configuracion_post():
        # Recibimos arrays: material[] y precio[]
        materiales = request.form.getlist("material[]")
        precios = request.form.getlist("precio[]")

        PrecioPorMetro.query.delete()
        for m, p in zip(materiales, precios):
            m = (m or "").strip()
            if not m:
                continue
            try:
                val = float((p or "0").strip())
            except ValueError:
                flash(f"Precio inválido para {m}.", "danger")
                return redirect(url_for("configuracion"))
            db.session.add(PrecioPorMetro(material=m, precio=val))

        db.session.commit()
        flash("Precios actualizados.", "success")
        return redirect(url_for("configuracion"))

    # ---------- PRESUPUESTADOR ----------
    @app.get("/presupuestador")
    @login_required
    def presupuestador():
        productos = Producto.query.order_by(Producto.nombre.asc()).all()
        precios_pm = {x.material: x.precio for x in PrecioPorMetro.query.all()}
        return render_template("presupuestador.html", productos=productos, precios_pm=precios_pm)

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

        # items: ids seleccionados
        ids = request.form.getlist("prod_id[]")
        if not ids:
            flash("Seleccioná al menos un producto.", "warning")
            return redirect(url_for("presupuestador"))

        precios_pm = {x.material: x.precio for x in PrecioPorMetro.query.all()}

        pedido = Pedido(
            cliente=cliente,
            telefono=telefono,
            email=email,
            direccion=direccion,
            observaciones=observaciones,
            total=0.0,
            forma_pago_preferida=forma_pago,
            monto_sena=monto_sena
        )
        db.session.add(pedido)
        db.session.flush()  # para obtener pedido.id

        total = 0.0
        for pid in ids:
            prod = Producto.query.get(int(pid))
            if not prod:
                continue

            if prod.por_metro:
                metros = float(request.form.get(f"metros_{prod.id}", "1").strip() or 1)
                cant = int(request.form.get(f"cant_{prod.id}", "1").strip() or 1)
                precio_m = precios_pm.get(prod.material, 0.0)
                subtotal = cant * metros * precio_m
                desc = f"{prod.nombre} - {prod.material} ({metros}m x ${precio_m})"
                item = PedidoItem(pedido_id=pedido.id, descripcion=desc, cantidad=cant, metros=metros, subtotal=subtotal)
            else:
                cant = int(request.form.get(f"cant_{prod.id}", "1").strip() or 1)
                subtotal = cant * prod.precio
                desc = f"{prod.nombre} - {prod.material} (${prod.precio})"
                item = PedidoItem(pedido_id=pedido.id, descripcion=desc, cantidad=cant, metros=None, subtotal=subtotal)

            total += subtotal
            db.session.add(item)

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

        # pagos (opcional para mostrar historial)
        pagos = []
        total_pagado = 0.0

        for pay in getattr(p, "pagos", []) or []:
            total_pagado += float(pay.monto_pagado or 0.0)
            pagos.append({
                "id": pay.id,
                "pedido_id": pay.id,
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

        monto_sena_val = float(p.monto_sena or 0.0)
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
            "debe": float(debe),
            "total": float(p.total or 0.0),
            "estado": p.estado,
            "items": items,
            "pagos": pagos
        }
    
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
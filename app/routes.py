from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required
from . import db
from .models import Producto, PrecioPorMetro, Pedido, PedidoItem
from sqlalchemy import func
from datetime import datetime, timedelta
from flask import send_file
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

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
        forma_pago = request.form.get("forma_pago")
        monto_sena = request.form.get("monto_sena")
        observaciones = request.form.get("observaciones", "").strip() or None

        tiene_sena = True if monto_sena else False
        monto_sena = float(monto_sena) if monto_sena else None

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

        pedido = Pedido(cliente=cliente, telefono=telefono, email=email, direccion=direccion, observaciones=observaciones, total=0.0, forma_pago=forma_pago, tiene_sena=tiene_sena, monto_sena=monto_sena)
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
    
    @app.get("/dashboard")
    @login_required
    def dashboard():
        total_pedidos = Pedido.query.count()
        pendientes = Pedido.query.filter_by(estado="PENDIENTE").count()
        en_curso = Pedido.query.filter_by(estado="EN_CURSO").count()
        finalizados = Pedido.query.filter_by(estado="FINALIZADO").count()

        # ===== Totales por estado ($) =====
        total_pendiente = db.session.query(
            func.coalesce(func.sum(Pedido.total), 0.0)
        ).filter_by(estado="PENDIENTE").scalar()

        total_en_curso = db.session.query(
            func.coalesce(func.sum(Pedido.total), 0.0)
        ).filter_by(estado="EN_CURSO").scalar()

        total_finalizado = db.session.query(
            func.coalesce(func.sum(Pedido.total), 0.0)
        ).filter_by(estado="FINALIZADO").scalar()

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
                .filter(Pedido.created_at >= inicio, Pedido.created_at < fin).scalar()
            cant_dia = Pedido.query.filter(Pedido.created_at >= inicio, Pedido.created_at < fin).count()
            serie_totales.append(float(total_dia))
            serie_cant.append(int(cant_dia))

        # ===== Productos más vendidos =====
        productos_data = (
            db.session.query(
                PedidoItem.descripcion,
                func.sum(PedidoItem.cantidad)
            )
            .group_by(PedidoItem.descripcion)
            .order_by(func.sum(PedidoItem.cantidad).desc())
            .limit(5)
            .all()
        )

        productos_labels = [p[0] for p in productos_data]
        productos_cantidades = [int(p[1]) for p in productos_data]

        ultimos = Pedido.query.order_by(Pedido.id.desc()).limit(5).all()

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
        )
    
    @app.get("/api/pedidos")
    @login_required
    def api_pedidos():
        estado = request.args.get("estado")
        cliente = request.args.get("cliente")

        query = Pedido.query

        if estado and estado != "TODOS":
            query = query.filter_by(estado=estado)

        if cliente:
            query = query.filter(Pedido.cliente.ilike(f"%{cliente}%"))

        pedidos = query.order_by(Pedido.id.desc()).all()

        data = []
        for p in pedidos:
            data.append({
                "id": p.id,
                "cliente": p.cliente,
                "forma_pago": p.forma_pago or "-",
                "sena": "Sí" if p.monto_sena else "No",
                "telefono": p.telefono,
                "estado": p.estado,
                "total": float(p.total)
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
        data = request.get_json()
        pedido = Pedido.query.get_or_404(id)

        nuevo_estado = data.get("estado", "").upper()

        if nuevo_estado not in ["PENDIENTE", "EN_CURSO", "FINALIZADO"]:
            return "Estado inválido", 400

        pedido.estado = nuevo_estado

        if "fecha_estimada" in data:
            pedido.fecha_estimada = datetime.strptime(
                data["fecha_estimada"], "%Y-%m-%d"
            )

        db.session.commit()
        return "", 204
    
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
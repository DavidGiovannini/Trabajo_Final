from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from . import db, login_manager
from datetime import datetime, date

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    @staticmethod
    def create_default_admin():
        u = User(username="admin")
        u.password_hash = generate_password_hash("admin123")
        return u

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

class Producto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    material = db.Column(db.String(100))
    precio = db.Column(db.Float)
    por_metro = db.Column(db.Boolean)

class PrecioPorMetro(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    material = db.Column(db.String(120), unique=True, nullable=False)
    precio = db.Column(db.Float, nullable=False)

class Pedido(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    cliente = db.Column(db.String(150), nullable=False)
    telefono = db.Column(db.String(50))
    direccion = db.Column(db.String(200))
    email = db.Column(db.String(120))

    observaciones = db.Column(db.Text)

    total = db.Column(db.Float, nullable=False)

    estado = db.Column(db.String(20), default="PENDIENTE", nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Fechas de transición (si querés simplificar aún más, podés borrar en_curso_at/finalizado_at)
    pendiente_at = db.Column(db.DateTime, nullable=True)
    en_curso_at = db.Column(db.DateTime, nullable=True)
    finalizado_at = db.Column(db.DateTime, nullable=True)

    # Seña: con esto alcanza (si es None o 0 → no hay seña)
    monto_sena = db.Column(db.Float, nullable=True)

    # Opcional: si querés guardar la "preferencia" cuando creás el pedido
    forma_pago_preferida = db.Column(db.String(50), nullable=True)

    activo = db.Column(db.Boolean, nullable=False, default=True)

    items = db.relationship(
        "PedidoItem",
        back_populates="pedido",
        cascade="all, delete-orphan"
    )

    pagos = db.relationship(
        "Pago",
        back_populates="pedido",
        cascade="all, delete-orphan"
    )

class PedidoItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    pedido_id = db.Column(
        db.Integer,
        db.ForeignKey("pedido.id"),
        nullable=False
    )

    descripcion = db.Column(db.String(255), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False, default=1)
    metros = db.Column(db.Float, nullable=True)
    subtotal = db.Column(db.Float, nullable=False, default=0.0)

    pedido = db.relationship(
        "Pedido",
        back_populates="items"
    )

class Pago(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    pedido_id = db.Column(db.Integer, db.ForeignKey("pedido.id"), nullable=False)

    # Efectivo / Transferencia / Tarjeta / MercadoPago
    metodo = db.Column(db.String(50), nullable=False)

    monto_pagado = db.Column(db.Float, nullable=False)

    # Solo si metodo == "Tarjeta"
    cuotas = db.Column(db.Integer, nullable=True)
    monto_cuota = db.Column(db.Float, nullable=True)

    fecha_pago = db.Column(db.Date, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    pedido = db.relationship("Pedido", back_populates="pagos")

    comprobantes = db.relationship(
        "PagoComprobante",
        back_populates="pago",
        cascade="all, delete-orphan"
    )

class PagoComprobante(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    pago_id = db.Column(db.Integer, db.ForeignKey("pago.id"), nullable=False)

    filename = db.Column(db.String(255), nullable=False)       # nombre guardado
    original_name = db.Column(db.String(255), nullable=False)  # nombre original
    mimetype = db.Column(db.String(120), nullable=True)
    size_bytes = db.Column(db.Integer, nullable=True)

    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    pago = db.relationship("Pago", back_populates="comprobantes")
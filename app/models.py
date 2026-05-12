from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from . import db, login_manager
from datetime import datetime, date

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# =========================
# USUARIO
# =========================
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

# =========================
# PRODUCTOS
# =========================
class Producto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    tipo = db.Column(db.String(100))
    precio = db.Column(db.Float)
    stock = db.Column(db.Integer, nullable=True)

class AdicionalMueble(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    linea = db.Column(db.String(50), nullable=False)  # standard / roble / lujo / laqueado
    nombre = db.Column(db.String(150), nullable=False)
    precio = db.Column(db.Float, nullable=False)
    def __repr__(self):
        return f"<Adicional {self.linea} - {self.nombre}>"

# =========================
# CONFIGURACIONES
# =========================
class ConfiguracionPrecio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    clave = db.Column(db.String(100), unique=True, nullable=False)
    valor = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f"<Config {self.clave}={self.valor}>"
    
class ConfiguracionGeneral(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha_actualizacion = db.Column(db.Date, nullable=False)

    def __repr__(self):
        return f"<ConfigGeneral fecha={self.fecha_actualizacion}>"


# =========================
# NUEVO: PRECIOS MUEBLES
# =========================
class PrecioMueble(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    linea = db.Column(db.String(50), nullable=False)
    medida = db.Column(db.Integer, nullable=False)
    base = db.Column(db.Float, default=0)
    alacena = db.Column(db.Float, default=0)
    inox = db.Column(db.Float, default=0)

    def __repr__(self):
        return f"<Mueble {self.linea} {self.medida}cm>"


# =========================
# PEDIDOS
# =========================
class Pedido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cliente = db.Column(db.String(150), nullable=False)
    telefono = db.Column(db.String(50))
    pais = db.Column(db.String(100))
    localidad = db.Column(db.String(100))
    codigo_postal = db.Column(db.String(20))
    barrio = db.Column(db.String(100))
    direccion = db.Column(db.String(200))
    email = db.Column(db.String(120))
    observaciones = db.Column(db.Text)
    total = db.Column(db.Float, nullable=False)
    estado = db.Column(db.String(20), default="PENDIENTE", nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    pendiente_at = db.Column(db.DateTime, nullable=True)
    en_curso_at = db.Column(db.DateTime, nullable=True)
    finalizado_at = db.Column(db.DateTime, nullable=True)
    monto_sena = db.Column(db.Float, nullable=True)
    forma_pago_preferida = db.Column(db.String(50), nullable=True)
    activo = db.Column(db.Boolean, nullable=False, default=True)
    stock_descontado = db.Column(db.Boolean, nullable=False, default=False, server_default='0')
    token_pdf = db.Column(db.String(32), unique=True, nullable=True)
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
    producto_id = db.Column(db.Integer, db.ForeignKey("producto.id"), nullable=True)
    descripcion = db.Column(db.String(255), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False, default=1)
    metros = db.Column(db.Float, nullable=True)
    subtotal = db.Column(db.Float, nullable=False, default=0.0)
    pedido = db.relationship(
        "Pedido",
        back_populates="items"
    )


# =========================
# PAGOS
# =========================
class Pago(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey("pedido.id"), nullable=False)
    metodo = db.Column(db.String(50), nullable=False)
    monto_pagado = db.Column(db.Float, nullable=False)
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
    filename = db.Column(db.String(255), nullable=False)
    original_name = db.Column(db.String(255), nullable=False)
    mimetype = db.Column(db.String(120), nullable=True)
    size_bytes = db.Column(db.Integer, nullable=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    pago = db.relationship("Pago", back_populates="comprobantes")


# =========================
# RECORDATORIOS / CALENDARIO
# =========================
class Recordatorio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    fecha = db.Column(db.Date, nullable=False)
    hora = db.Column(db.String(5), nullable=True)   # "HH:MM" o None
    color = db.Column(db.String(20), nullable=False, default="azul")
    completado = db.Column(db.Boolean, nullable=False, default=False)
    notificado = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "titulo": self.titulo,
            "descripcion": self.descripcion or "",
            "fecha": self.fecha.isoformat(),
            "hora": self.hora or "",
            "color": self.color,
            "completado": self.completado,
        }
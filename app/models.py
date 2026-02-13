from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from . import db, login_manager
from datetime import datetime

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
        u.password_hash = generate_password_hash("admin123")  # cambiá esto después
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
    observaciones = db.Column(db.Text)
    total = db.Column(db.Float, nullable=False)
    estado = db.Column(db.String(20), default="EN_CURSO")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # EN_CURSO / FINALIZADO
    email = db.Column(db.String(120))
    forma_pago = db.Column(db.String(50))
    tiene_sena = db.Column(db.Boolean, default=False)
    monto_sena = db.Column(db.Float)

class PedidoItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey("pedido.id"), nullable=False)
    descripcion = db.Column(db.String(255), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False, default=1)
    metros = db.Column(db.Float, nullable=True)
    subtotal = db.Column(db.Float, nullable=False, default=0.0)
    pedido = db.relationship("Pedido", backref=db.backref("items", lazy=True))
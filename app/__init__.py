from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from pathlib import Path

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "login"

def create_app():
    app = Flask(__name__, instance_relative_config=True)

    # Clave simple para entorno LAN interno (igual podés cambiarla)
    app.config["SECRET_KEY"] = "cambia-esta-clave"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + str(Path(app.instance_path) / "app.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)

    from .models import User, Producto, PrecioPorMetro, Pedido, PedidoItem

    with app.app_context():
        db.create_all()

        # Seed: 1 usuario admin
        if not User.query.first():
            admin = User.create_default_admin()
            db.session.add(admin)

        # Seed: precios por metro iniciales (como tu ConfiguracionView)
        if PrecioPorMetro.query.count() == 0:
            db.session.add(PrecioPorMetro(material="Melamina", precio=7000))
            db.session.add(PrecioPorMetro(material="Chapa MDF", precio=6800))
            db.session.add(PrecioPorMetro(material="Melamina premium", precio=8500))

        db.session.commit()

    from .auth import register_auth
    from .routes import register_routes
    register_auth(app)
    register_routes(app)

    return app
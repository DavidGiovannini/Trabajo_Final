from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from pathlib import Path
from flask_migrate import Migrate

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "login"

def create_app():
    app = Flask(__name__, instance_relative_config=True)

    # SECRET_KEY: se genera automáticamente y se guarda en instance/secret.key
    # De esta forma es única por instalación y persiste entre reinicios
    import secrets as _secrets
    _key_file = Path(app.instance_path) / "secret.key"
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    if _key_file.exists():
        _secret = _key_file.read_text().strip()
    else:
        _secret = _secrets.token_hex(32)
        _key_file.write_text(_secret)
    app.config["SECRET_KEY"] = _secret

    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + str(Path(app.instance_path) / "app.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Hardening de cookies de sesión
    app.config["SESSION_COOKIE_HTTPONLY"] = True   # JS no puede leer la cookie
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"  # Protege contra CSRF básico
    app.config["REMEMBER_COOKIE_HTTPONLY"] = True

    # uploads (comprobantes)
    uploads_dir = Path(app.instance_path) / "uploads" / "comprobantes"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    app.config["UPLOADS_DIR"] = str(uploads_dir)

    db.init_app(app)
    migrate = Migrate(app, db)
    login_manager.init_app(app)

    from .models import User, Producto, Pedido, PedidoItem, PrecioMueble, AdicionalMueble

    with app.app_context():
        db.create_all()

        # Seed: 1 usuario admin
        if not User.query.first():
            admin = User.create_default_admin()
            db.session.add(admin)

        db.session.commit()

    from .auth import register_auth
    from .routes import register_routes
    register_auth(app)
    register_routes(app)

    return app
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user
from urllib.parse import urlparse, urljoin
from collections import defaultdict
import time

from .models import User

# ── Rate limiting en memoria ─────────────────────────────────────────────────
# Estructura: { ip: [timestamp_intento1, timestamp_intento2, ...] }
_failed = defaultdict(list)
_MAX_INTENTOS   = 5     # intentos fallidos antes de bloquear
_VENTANA_SEG    = 300   # ventana de 5 minutos para contar intentos
_BLOQUEO_SEG    = 300   # tiempo de bloqueo: 5 minutos

def _ip():
    return request.environ.get("HTTP_X_FORWARDED_FOR", request.remote_addr) or "unknown"

def _limpiar(ip):
    ahora = time.time()
    _failed[ip] = [t for t in _failed[ip] if ahora - t < _VENTANA_SEG]

def _bloqueado(ip):
    _limpiar(ip)
    return len(_failed[ip]) >= _MAX_INTENTOS

def _registrar_fallo(ip):
    _failed[ip].append(time.time())

def _limpiar_exito(ip):
    _failed.pop(ip, None)

def _url_segura(target):
    """Verifica que el redirect 'next' sea relativo al propio host (no open redirect)."""
    if not target:
        return False
    ref  = urlparse(request.host_url)
    test = urlparse(urljoin(request.host_url, target))
    return test.scheme in ("http", "https") and ref.netloc == test.netloc


def register_auth(app):

    @app.get("/login")
    def login():
        return render_template("login.html")

    @app.post("/login")
    def login_post():
        ip = _ip()

        if _bloqueado(ip):
            flash("Demasiados intentos fallidos. Esperá 5 minutos e intentá de nuevo.", "danger")
            return redirect(url_for("login"))

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(username=username).first()
        if not user or not user.check_password(password):
            _registrar_fallo(ip)
            restantes = _MAX_INTENTOS - len(_failed[ip])
            if restantes > 0:
                flash(f"Usuario o contraseña incorrectos. ({restantes} intento{'s' if restantes != 1 else ''} restante{'s' if restantes != 1 else ''})", "danger")
            else:
                flash("Cuenta bloqueada por 5 minutos por demasiados intentos fallidos.", "danger")
            return redirect(url_for("login"))

        _limpiar_exito(ip)
        login_user(user)

        next_url = request.args.get("next") or request.form.get("next")
        if next_url and _url_segura(next_url):
            return redirect(next_url)
        return redirect(url_for("productos"))

    @app.get("/logout")
    def logout():
        logout_user()
        return redirect(url_for("login"))

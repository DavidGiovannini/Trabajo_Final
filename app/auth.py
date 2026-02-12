from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user
from .models import User

def register_auth(app):
    @app.get("/login")
    def login():
        return render_template("login.html")

    @app.post("/login")
    def login_post():
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(username=username).first()
        if not user or not user.check_password(password):
            flash("Usuario o contraseña incorrectos.", "danger")
            return redirect(url_for("login"))

        login_user(user)
        return redirect(url_for("productos"))

    @app.get("/logout")
    def logout():
        logout_user()
        return redirect(url_for("login"))
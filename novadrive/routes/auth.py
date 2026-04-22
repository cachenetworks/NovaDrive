from __future__ import annotations

import secrets

from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user

from novadrive.forms import LoginForm, RegistrationForm
from novadrive.services.auth_service import AuthService

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            user = AuthService.create_user(
                username=form.username.data,
                email=form.email.data,
                password=form.password.data,
            )
            flash(
                "Account created successfully. You can sign in now."
                if user.role != "admin"
                else "Admin account created successfully. You can sign in now.",
                "success",
            )
            return redirect(url_for("auth.login"))
        except ValueError as exc:
            flash(str(exc), "error")
    return render_template("auth/register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    form = LoginForm()
    if form.validate_on_submit():
        user = AuthService.authenticate(form.login.data, form.password.data)
        if not user:
            flash("Invalid credentials. Please try again.", "error")
        else:
            login_user(user, remember=form.remember.data)
            session["nova_session_token"] = secrets.token_urlsafe(32)
            session.permanent = True
            AuthService.ensure_user_session(
                user=user,
                session_token=session["nova_session_token"],
                user_agent=request.headers.get("User-Agent"),
                ip_address=request.headers.get("X-Forwarded-For", request.remote_addr),
                lifetime_hours=current_app.config["PERMANENT_SESSION_LIFETIME_HOURS"],
            )
            flash("Welcome back to NovaDrive.", "success")
            return redirect(request.args.get("next") or url_for("dashboard.index"))
    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    AuthService.deactivate_user_session(session.get("nova_session_token"))
    logout_user()
    session.clear()
    flash("You have been signed out.", "success")
    return redirect(url_for("auth.login"))

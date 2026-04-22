from __future__ import annotations

import secrets
from datetime import timedelta
from urllib.parse import urljoin

from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user

from novadrive.extensions import db
from novadrive.models import User, utcnow
from novadrive.forms import LoginForm, RegistrationForm
from novadrive.services.auth_service import AuthService
from novadrive.services.email_service import EmailDeliveryError
from novadrive.services.verification_service import VerificationService, VerificationTokenError

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            require_verification = current_app.config["EMAIL_VERIFICATION_REQUIRED"]
            if require_verification:
                VerificationService.ensure_smtp_available(current_app.config)

            user = AuthService.create_user(
                username=form.username.data,
                email=form.email.data,
                password=form.password.data,
                email_verified=not require_verification,
            )
        except (ValueError, EmailDeliveryError) as exc:
            flash(str(exc), "error")
        else:
            if require_verification:
                try:
                    _send_verification_email(user)
                    flash(
                        "Account created. Confirm your email before signing in."
                        if user.role != "admin"
                        else "Admin account created. Confirm your email before signing in.",
                        "success",
                    )
                except EmailDeliveryError as exc:
                    flash(
                        f"Account created, but the verification email could not be sent: {exc}",
                        "error",
                    )
                return redirect(url_for("auth.login", email=user.email))

            flash(
                "Account created successfully. You can sign in now."
                if user.role != "admin"
                else "Admin account created successfully. You can sign in now.",
                "success",
            )
            return redirect(url_for("auth.login"))
    return render_template("auth/register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    form = LoginForm()
    pending_verification_email = request.args.get("email", "").strip().lower()
    if form.validate_on_submit():
        user = AuthService.authenticate(form.login.data, form.password.data)
        if not user:
            flash("Invalid credentials. Please try again.", "error")
        elif not AuthService.can_use_password_login(user, current_app.config):
            pending_verification_email = user.email
            flash("Confirm your email before signing in.", "error")
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
    return render_template(
        "auth/login.html",
        form=form,
        pending_verification_email=pending_verification_email,
    )


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    AuthService.deactivate_user_session(session.get("nova_session_token"))
    logout_user()
    session.clear()
    flash("You have been signed out.", "success")
    return redirect(url_for("auth.login"))


@auth_bp.route("/api-key/regenerate", methods=["POST"])
@login_required
def regenerate_api_key():
    session["nova_generated_api_key"] = AuthService.generate_api_key(current_user)
    flash("A new API key is ready. Copy it now because it will not be shown again.", "success")
    return redirect(request.referrer or url_for("dashboard.index"))


@auth_bp.route("/api-key/revoke", methods=["POST"])
@login_required
def revoke_api_key():
    AuthService.revoke_api_key(current_user)
    session.pop("nova_generated_api_key", None)
    flash("API key revoked.", "success")
    return redirect(request.referrer or url_for("dashboard.index"))


@auth_bp.get("/verify-email/<token>")
def verify_email(token: str):
    try:
        payload = VerificationService.verify_email_token(
            token,
            current_app.secret_key,
            current_app.config["EMAIL_VERIFICATION_MAX_AGE_SECONDS"],
        )
        user = db.session.get(User, int(payload["user_id"]))
        if not user:
            raise VerificationTokenError("That verification link is invalid.")
        if user.email.lower() != str(payload["email"]).lower():
            raise VerificationTokenError("That verification link is invalid.")
        AuthService.mark_email_verified(user)
        flash("Email confirmed. You can sign in now.", "success")
    except VerificationTokenError as exc:
        flash(str(exc), "error")
    return redirect(url_for("auth.login"))


@auth_bp.route("/resend-verification", methods=["POST"])
def resend_verification():
    email = (request.form.get("email") or "").strip().lower()
    if current_user.is_authenticated and not email:
        email = current_user.email.lower()

    if not email:
        flash("Enter the email address that needs a verification link.", "error")
        return redirect(url_for("auth.login"))

    user = AuthService.find_by_email(email)
    if not user:
        flash("If that account exists, a new verification email has been sent.", "success")
        return redirect(url_for("auth.login", email=email))

    if user.is_email_verified:
        flash("That email address is already verified.", "success")
        return redirect(url_for("auth.login", email=user.email))

    if not current_app.config["EMAIL_VERIFICATION_REQUIRED"]:
        flash("Email verification is not required in this deployment.", "info")
        return redirect(url_for("auth.login", email=user.email))

    last_sent_at = user.email_verification_sent_at
    resend_interval = current_app.config["EMAIL_VERIFICATION_RESEND_INTERVAL_SECONDS"]
    if last_sent_at and last_sent_at + timedelta(seconds=resend_interval) > utcnow():
        flash("Wait a moment before requesting another verification email.", "error")
        return redirect(url_for("auth.login", email=user.email))

    try:
        _send_verification_email(user)
        flash("Verification email sent.", "success")
    except EmailDeliveryError as exc:
        flash(str(exc), "error")
    return redirect(url_for("auth.login", email=user.email))


def _send_verification_email(user: User) -> None:
    token = VerificationService.generate_email_token(user, current_app.secret_key)
    verify_url = _external_url("auth.verify_email", token=token)
    VerificationService.send_verification_email(
        user=user,
        verify_url=verify_url,
        config=current_app.config,
    )
    AuthService.note_verification_email_sent(user)


def _external_url(endpoint: str, **values) -> str:
    configured_base = current_app.config["APP_EXTERNAL_URL"]
    local_path = url_for(endpoint, _external=False, **values)
    if configured_base:
        return urljoin(f"{configured_base}/", local_path.lstrip("/"))
    return url_for(endpoint, _external=True, **values)

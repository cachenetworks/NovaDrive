from __future__ import annotations

from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required

from novadrive.models import File
from novadrive.services.file_service import AccessError, FileService
from novadrive.services.overlay_service import OverlayService
from novadrive.utils.urls import external_url

overlay_bp = Blueprint("overlay", __name__, url_prefix="/overlay")


@overlay_bp.get("/obs")
def obs():
    return redirect(url_for("overlay.obs_background"))


@overlay_bp.get("/obs/background")
def obs_background():
    return render_template(
        "overlay/background.html",
        background_endpoint=url_for("api.overlay_background"),
    )


@overlay_bp.route("/obs/background/settings", methods=["GET", "POST"])
@login_required
def background_settings():
    settings = OverlayService.get_or_create_settings(current_user)
    if request.method == "POST":
        try:
            settings = OverlayService.update_background_settings(current_user, request.form)
            flash("OBS background settings saved.", "success")
            return redirect(url_for("overlay.background_settings"))
        except (LookupError, AccessError, ValueError) as exc:
            flash(str(exc), "error")

    selectable_files = OverlayService.selectable_background_files(current_user)
    selected_file_ids = set(OverlayService.selected_file_ids(settings))
    generated_api_key = session.pop("nova_generated_api_key", None)
    overlay_key = generated_api_key or "YOUR_API_KEY"
    overlay_url = external_url(
        "overlay.obs_background",
        api_key=overlay_key,
    )
    background_api_url = external_url(
        "api.overlay_background",
        apikey=overlay_key,
    )
    return render_template(
        "overlay/background_settings.html",
        settings=settings,
        selectable_files=selectable_files,
        selected_file_ids=selected_file_ids,
        folder_options=FileService.folder_options(current_user),
        selected_folder_id=settings.folder_id,
        generated_api_key=generated_api_key,
        overlay_url=overlay_url,
        background_api_url=background_api_url,
        preview_files=_preview_files(current_user, settings),
    )


def _preview_files(user, settings) -> list[File]:
    try:
        return OverlayService.background_files(user, settings)[:12]
    except Exception as exc:
        current_app.logger.warning("Could not load OBS background preview files: %s", exc)
        return []

from __future__ import annotations

from flask import Blueprint, abort, current_app, render_template

from novadrive.services.file_delivery import FileDeliveryService
from novadrive.services.share_service import ShareService

share_bp = Blueprint("share", __name__)


@share_bp.route("/s/<token>")
def view(token: str):
    share_link = ShareService.get_valid_link(token)
    if not share_link:
        abort(404)
    preview_kind = FileDeliveryService.preview_kind(share_link.file)
    text_preview = FileDeliveryService.get_text_preview(share_link.file, current_app.config)
    return render_template(
        "share/view.html",
        share_link=share_link,
        file=share_link.file,
        preview_kind=preview_kind,
        text_preview=text_preview,
    )


@share_bp.route("/s/<token>/download")
def download(token: str):
    share_link = ShareService.get_valid_link(token)
    if not share_link:
        abort(404)
    return FileDeliveryService.build_response(
        share_link.file,
        current_app.config,
        as_attachment=True,
        download_name=share_link.file.filename,
    )


@share_bp.route("/s/<token>/raw")
def raw(token: str):
    share_link = ShareService.get_valid_link(token)
    if not share_link:
        abort(404)
    return FileDeliveryService.build_response(
        share_link.file,
        current_app.config,
        as_attachment=False,
        download_name=share_link.file.filename,
    )

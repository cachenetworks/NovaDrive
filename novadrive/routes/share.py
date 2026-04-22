from __future__ import annotations

from flask import Blueprint, abort, current_app, render_template, send_file

from novadrive.services.file_service import FileService
from novadrive.services.share_service import ShareService

share_bp = Blueprint("share", __name__)


@share_bp.route("/s/<token>")
def view(token: str):
    share_link = ShareService.get_valid_link(token)
    if not share_link:
        abort(404)
    return render_template("share/view.html", share_link=share_link, file=share_link.file)


@share_bp.route("/s/<token>/download")
def download(token: str):
    share_link = ShareService.get_valid_link(token)
    if not share_link:
        abort(404)
    file_stream, _ = FileService.rebuild_file(share_link.file, current_app.config)
    return send_file(
        file_stream,
        mimetype=share_link.file.mime_type,
        as_attachment=True,
        download_name=share_link.file.filename,
        max_age=0,
    )

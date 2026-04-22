from __future__ import annotations

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)
from flask_login import current_user, login_required

from novadrive.forms import ShareLinkForm
from novadrive.models import ShareLink
from novadrive.services.file_service import AccessError, FileService
from novadrive.services.share_service import ShareService
from novadrive.utils.validators import ValidationError

files_bp = Blueprint("files", __name__, url_prefix="/files")


def _wants_json() -> bool:
    return request.headers.get("X-Requested-With") == "XMLHttpRequest"


@files_bp.route("/upload", methods=["POST"])
@login_required
def upload():
    folder_id = request.form.get("folder_id", type=int)
    uploads = request.files.getlist("files")
    try:
        folder = (
            FileService.get_folder_or_404(current_user, folder_id)
            if folder_id
            else FileService.get_accessible_root_folder(current_user)
        )
        records = FileService.upload_files(current_user, folder, uploads, current_app.config)
        if not records:
            raise ValidationError("Choose at least one file to upload.")

        response_payload = {
            "success": True,
            "uploaded": [
                {
                    "id": file_record.id,
                    "filename": file_record.filename,
                    "size": file_record.total_size,
                    "chunks": file_record.total_chunks,
                }
                for file_record in records
            ],
        }
        if _wants_json():
            return jsonify(response_payload)
        flash(f"Uploaded {len(records)} file(s) to NovaDrive.", "success")
    except (LookupError, AccessError):
        if _wants_json():
            return jsonify({"success": False, "error": "Folder not found."}), 404
        flash("The target folder could not be found.", "error")
    except (ValidationError, ValueError) as exc:
        if _wants_json():
            return jsonify({"success": False, "error": str(exc)}), 400
        flash(str(exc), "error")
    except Exception:
        current_app.logger.exception("Upload failed.")
        if _wants_json():
            return jsonify({"success": False, "error": "Upload failed unexpectedly."}), 500
        flash("Upload failed unexpectedly.", "error")

    return redirect(
        url_for("dashboard.index", folder_id=folder_id) if folder_id else url_for("dashboard.index")
    )


@files_bp.route("/<int:file_id>")
@login_required
def details(file_id: int):
    try:
        file_record = FileService.get_file_or_404(current_user, file_id)
    except LookupError:
        abort(404)
    except AccessError:
        abort(403)

    share_form = ShareLinkForm()
    share_links = (
        ShareLink.query.filter_by(file_id=file_record.id)
        .order_by(ShareLink.created_at.desc())
        .all()
    )
    return render_template(
        "dashboard/file_details.html",
        file=file_record,
        share_form=share_form,
        share_links=share_links,
        breadcrumbs=FileService.build_breadcrumbs(file_record.folder),
        folder_options=FileService.folder_options(current_user),
    )


@files_bp.route("/<int:file_id>/download")
@login_required
def download(file_id: int):
    try:
        file_record = FileService.get_file_or_404(current_user, file_id)
        file_stream, _ = FileService.rebuild_file(file_record, current_app.config)
        return send_file(
            file_stream,
            mimetype=file_record.mime_type,
            as_attachment=True,
            download_name=file_record.filename,
            max_age=0,
        )
    except LookupError:
        abort(404)
    except AccessError:
        abort(403)
    except Exception as exc:
        flash(str(exc), "error")
        return redirect(url_for("dashboard.index", folder_id=request.args.get("folder_id", type=int)))


@files_bp.route("/<int:file_id>/rename", methods=["POST"])
@login_required
def rename(file_id: int):
    try:
        file_record = FileService.get_file_or_404(current_user, file_id)
        FileService.rename_file(current_user, file_record, request.form.get("filename", ""))
        flash("File renamed.", "success")
    except (LookupError, AccessError):
        flash("File not found.", "error")
    except (ValidationError, ValueError) as exc:
        flash(str(exc), "error")
    return redirect(url_for("files.details", file_id=file_id))


@files_bp.route("/<int:file_id>/move", methods=["POST"])
@login_required
def move(file_id: int):
    try:
        file_record = FileService.get_file_or_404(current_user, file_id)
        destination_folder = FileService.get_folder_or_404(
            current_user,
            request.form.get("destination_folder_id", type=int),
        )
        FileService.move_file(current_user, file_record, destination_folder)
        flash("File moved.", "success")
        return redirect(url_for("dashboard.index", folder_id=destination_folder.id))
    except (LookupError, AccessError):
        flash("Unable to move that file.", "error")
    except (ValidationError, ValueError) as exc:
        flash(str(exc), "error")
    return redirect(url_for("files.details", file_id=file_id))


@files_bp.route("/<int:file_id>/delete", methods=["POST"])
@login_required
def delete(file_id: int):
    redirect_folder_id = request.form.get("folder_id", type=int)
    hard_delete = request.form.get("hard_delete") == "true"
    try:
        file_record = FileService.get_file_or_404(current_user, file_id)
        FileService.delete_file(current_user, file_record, hard_delete=hard_delete)
        flash("File deleted.", "success")
    except (LookupError, AccessError):
        flash("File not found.", "error")
    return redirect(
        url_for("dashboard.index", folder_id=redirect_folder_id)
        if redirect_folder_id
        else url_for("dashboard.index")
    )


@files_bp.route("/<int:file_id>/share", methods=["POST"])
@login_required
def create_share_link(file_id: int):
    form = ShareLinkForm()
    try:
        file_record = FileService.get_file_or_404(current_user, file_id)
        if not form.validate_on_submit():
            flash("The share form was invalid.", "error")
            return redirect(url_for("files.details", file_id=file_id))

        share_link = ShareService.create_link(
            file_record=file_record,
            expires_at=form.expires_at.data,
            user_id=current_user.id,
        )
        flash("Share link created.", "success")
        return redirect(url_for("files.details", file_id=file_id, created_share=share_link.token))
    except (LookupError, AccessError):
        flash("File not found.", "error")
    except ValueError as exc:
        flash(str(exc), "error")
    return redirect(url_for("files.details", file_id=file_id))

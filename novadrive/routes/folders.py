from __future__ import annotations

from flask import Blueprint, flash, redirect, request, url_for
from flask_login import current_user, login_required

from novadrive.services.file_service import AccessError, FileService
from novadrive.utils.validators import ValidationError

folders_bp = Blueprint("folders", __name__, url_prefix="/folders")


@folders_bp.route("/create", methods=["POST"])
@login_required
def create():
    parent_id = request.form.get("parent_id", type=int)
    try:
        parent_folder = (
            FileService.get_folder_or_404(current_user, parent_id)
            if parent_id
            else FileService.get_accessible_root_folder(current_user)
        )
        folder = FileService.create_folder(current_user, parent_folder, request.form.get("name", ""))
        flash("Folder created.", "success")
        return redirect(url_for("dashboard.index", folder_id=folder.id))
    except (LookupError, AccessError):
        flash("Parent folder not found.", "error")
    except (ValidationError, ValueError) as exc:
        flash(str(exc), "error")
    return redirect(url_for("dashboard.index", folder_id=parent_id) if parent_id else url_for("dashboard.index"))


@folders_bp.route("/<int:folder_id>/rename", methods=["POST"])
@login_required
def rename(folder_id: int):
    try:
        folder = FileService.get_folder_or_404(current_user, folder_id)
        FileService.rename_folder(current_user, folder, request.form.get("name", ""))
        flash("Folder renamed.", "success")
    except (LookupError, AccessError):
        flash("Folder not found.", "error")
    except (ValidationError, ValueError) as exc:
        flash(str(exc), "error")
    return redirect(url_for("dashboard.index", folder_id=folder_id))


@folders_bp.route("/<int:folder_id>/move", methods=["POST"])
@login_required
def move(folder_id: int):
    try:
        folder = FileService.get_folder_or_404(current_user, folder_id)
        destination = FileService.get_folder_or_404(
            current_user,
            request.form.get("destination_folder_id", type=int),
        )
        FileService.move_folder(current_user, folder, destination)
        flash("Folder moved.", "success")
        return redirect(url_for("dashboard.index", folder_id=destination.id))
    except (LookupError, AccessError):
        flash("Unable to move that folder.", "error")
    except (ValidationError, ValueError) as exc:
        flash(str(exc), "error")
    return redirect(url_for("dashboard.index", folder_id=folder_id))


@folders_bp.route("/<int:folder_id>/delete", methods=["POST"])
@login_required
def delete(folder_id: int):
    parent_id = request.form.get("parent_id", type=int)
    hard_delete = request.form.get("hard_delete") == "true"
    try:
        folder = FileService.get_folder_or_404(current_user, folder_id)
        FileService.delete_folder(current_user, folder, hard_delete=hard_delete)
        flash("Folder deleted.", "success")
    except (LookupError, AccessError):
        flash("Folder not found.", "error")
    except (ValidationError, ValueError) as exc:
        flash(str(exc), "error")
    return redirect(url_for("dashboard.index", folder_id=parent_id) if parent_id else url_for("dashboard.index"))

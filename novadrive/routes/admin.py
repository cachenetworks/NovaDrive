from __future__ import annotations

from flask import Blueprint, current_app, render_template
from flask_login import login_required
from sqlalchemy import func

from novadrive.extensions import db
from novadrive.models import ActivityLog, File, Folder, User
from novadrive.services.discord_storage import DiscordStorageBackend, StorageBackendError
from novadrive.utils.decorators import admin_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/")
@login_required
@admin_required
def index():
    user_count = User.query.count()
    file_count = File.query.filter(File.deleted_at.is_(None), File.upload_status == "complete").count()
    folder_count = Folder.query.filter(Folder.deleted_at.is_(None)).count()
    total_storage = (
        db.session.query(func.coalesce(func.sum(File.total_size), 0))
        .filter(File.deleted_at.is_(None), File.upload_status == "complete")
        .scalar()
    )
    recent_activity = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(20).all()

    backend = DiscordStorageBackend(current_app.config)
    try:
        storage_health = backend.health_check()
    except StorageBackendError as exc:
        storage_health = {"ok": False, "error": str(exc)}

    return render_template(
        "admin/index.html",
        users=User.query.order_by(User.created_at.asc()).all(),
        stats={
            "user_count": user_count,
            "file_count": file_count,
            "folder_count": folder_count,
            "total_storage": int(total_storage or 0),
        },
        recent_activity=recent_activity,
        storage_health=storage_health,
        config_snapshot={
            "allow_public_sharing": current_app.config["ALLOW_PUBLIC_SHARING"],
            "chunk_size": current_app.config["DISCORD_CHUNK_SIZE_BYTES"],
            "channels": current_app.config["DISCORD_STORAGE_CHANNEL_IDS"],
            "bridge_url": current_app.config["DISCORD_BOT_BRIDGE_URL"],
        },
    )

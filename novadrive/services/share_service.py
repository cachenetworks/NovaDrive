from __future__ import annotations

import secrets

from flask import current_app

from novadrive.extensions import db
from novadrive.models import File, ShareLink
from novadrive.services.activity_service import ActivityService


class ShareService:
    @staticmethod
    def create_link(file_record: File, expires_at=None, user_id: int | None = None) -> ShareLink:
        if not current_app.config["ALLOW_PUBLIC_SHARING"]:
            raise ValueError("Public sharing is disabled.")

        share_link = ShareLink(
            file_id=file_record.id,
            token=secrets.token_urlsafe(current_app.config["SHARE_TOKEN_BYTES"]),
            expires_at=expires_at,
            is_active=True,
        )
        db.session.add(share_link)
        db.session.commit()

        ActivityService.log(
            action="share.created",
            target_type="share_link",
            target_id=share_link.id,
            user_id=user_id,
            metadata={"file_id": file_record.id, "expires_at": expires_at},
        )
        return share_link

    @staticmethod
    def get_valid_link(token: str) -> ShareLink | None:
        share_link = ShareLink.query.filter_by(token=token, is_active=True).first()
        if not share_link:
            return None
        if share_link.is_expired or share_link.file.is_deleted or share_link.file.upload_status != "complete":
            return None
        return share_link


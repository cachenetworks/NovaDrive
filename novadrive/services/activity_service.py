from __future__ import annotations

import json
from typing import Any

from novadrive.extensions import db
from novadrive.models import ActivityLog


class ActivityService:
    @staticmethod
    def log(
        action: str,
        target_type: str,
        target_id: int | None = None,
        user_id: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ActivityLog:
        activity = ActivityLog(
            user_id=user_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            metadata_json=json.dumps(metadata or {}, default=str),
        )
        db.session.add(activity)
        db.session.commit()
        return activity


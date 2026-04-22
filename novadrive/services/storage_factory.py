from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from novadrive.services.discord_storage import DiscordStorageBackend
from novadrive.services.storage_base import StorageBackendError

_BACKEND_LABELS = {
    "discord": "Discord",
    "s3": "S3",
}


def configured_storage_backend_name(config: Mapping[str, Any]) -> str:
    return str(config.get("STORAGE_BACKEND", "discord")).strip().lower() or "discord"


def storage_backend_label(name: str) -> str:
    return _BACKEND_LABELS.get(name, name.upper())


def get_storage_backend(config: Mapping[str, Any], backend_name: str | None = None):
    resolved_name = (backend_name or configured_storage_backend_name(config)).strip().lower()
    if resolved_name == "discord":
        return DiscordStorageBackend(config)
    if resolved_name == "s3":
        from novadrive.services.s3_storage import S3StorageBackend

        return S3StorageBackend(config)
    raise StorageBackendError(f"Unsupported storage backend '{resolved_name}'.")

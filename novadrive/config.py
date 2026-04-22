from __future__ import annotations

import os
from pathlib import Path


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _as_int(value: str | None, default: int) -> int:
    try:
        return int(value) if value is not None else default
    except (TypeError, ValueError):
        return default


class Config:
    APP_NAME = "NovaDrive"

    BASE_DIR = Path(__file__).resolve().parent.parent
    INSTANCE_DIR = BASE_DIR / "instance"

    SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{(INSTANCE_DIR / 'novadrive.db').as_posix()}",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAX_UPLOAD_SIZE_BYTES = _as_int(os.getenv("MAX_UPLOAD_SIZE_BYTES"), 536_870_912)
    MAX_CONTENT_LENGTH = MAX_UPLOAD_SIZE_BYTES
    SPOOL_MAX_MEMORY_BYTES = _as_int(os.getenv("SPOOL_MAX_MEMORY_BYTES"), 8_388_608)

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = _as_bool(os.getenv("SESSION_COOKIE_SECURE"), False)
    PERMANENT_SESSION_LIFETIME_HOURS = _as_int(
        os.getenv("PERMANENT_SESSION_LIFETIME_HOURS"),
        24,
    )

    WTF_CSRF_TIME_LIMIT = None

    STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "discord")
    ALLOW_PUBLIC_SHARING = _as_bool(os.getenv("ALLOW_PUBLIC_SHARING"), True)
    SOFT_DELETE_ENABLED = _as_bool(os.getenv("SOFT_DELETE_ENABLED"), True)

    DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")
    DISCORD_GUILD_ID = _as_int(os.getenv("DISCORD_GUILD_ID"), 0)
    DISCORD_STORAGE_CHANNEL_IDS = [
        int(channel_id.strip())
        for channel_id in os.getenv("DISCORD_STORAGE_CHANNEL_IDS", "").split(",")
        if channel_id.strip().isdigit()
    ]
    DISCORD_ATTACHMENT_LIMIT_BYTES = _as_int(
        os.getenv("DISCORD_ATTACHMENT_LIMIT_BYTES"),
        8_000_000,
    )
    DISCORD_CHUNK_MARGIN_BYTES = _as_int(
        os.getenv("DISCORD_CHUNK_MARGIN_BYTES"),
        262_144,
    )
    DISCORD_CHUNK_SIZE_BYTES = _as_int(
        os.getenv("DISCORD_CHUNK_SIZE_BYTES"),
        max(1, DISCORD_ATTACHMENT_LIMIT_BYTES - DISCORD_CHUNK_MARGIN_BYTES),
    )
    DISCORD_BOT_BRIDGE_URL = os.getenv(
        "DISCORD_BOT_BRIDGE_URL",
        "http://127.0.0.1:5051",
    ).rstrip("/")
    DISCORD_BOT_BRIDGE_SHARED_SECRET = os.getenv(
        "DISCORD_BOT_BRIDGE_SHARED_SECRET",
        "novadrive-local-secret",
    )
    DISCORD_BOT_BRIDGE_TIMEOUT_SECONDS = _as_int(
        os.getenv("DISCORD_BOT_BRIDGE_TIMEOUT_SECONDS"),
        60,
    )
    DISCORD_UPLOAD_RETRY_COUNT = _as_int(os.getenv("DISCORD_UPLOAD_RETRY_COUNT"), 3)

    SHARE_TOKEN_BYTES = _as_int(os.getenv("SHARE_TOKEN_BYTES"), 24)
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()


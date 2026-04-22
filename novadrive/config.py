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


def _resolve_database_uri(base_dir: Path, instance_dir: Path) -> str:
    configured_value = (os.getenv("DATABASE_URL") or "").strip()
    if not configured_value:
        return f"sqlite:///{(instance_dir / 'novadrive.db').as_posix()}"

    sqlite_prefixes = ("sqlite:///", "sqlite+pysqlite:///")
    for prefix in sqlite_prefixes:
        if not configured_value.startswith(prefix):
            continue

        raw_path = configured_value[len(prefix):]
        path_part, separator, query = raw_path.partition("?")
        if not path_part or path_part == ":memory:" or path_part.startswith("/") or path_part.startswith("file:"):
            return configured_value

        absolute_path = (base_dir / path_part).resolve()
        suffix = f"{separator}{query}" if separator else ""
        return f"{prefix}{absolute_path.as_posix()}{suffix}"

    return configured_value


class Config:
    APP_NAME = "NovaDrive"

    BASE_DIR = Path(__file__).resolve().parent.parent
    INSTANCE_DIR = BASE_DIR / "instance"
    APP_EXTERNAL_URL = os.getenv("APP_EXTERNAL_URL", "").rstrip("/")

    SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
    SQLALCHEMY_DATABASE_URI = _resolve_database_uri(BASE_DIR, INSTANCE_DIR)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAX_UPLOAD_SIZE_BYTES = _as_int(os.getenv("MAX_UPLOAD_SIZE_BYTES"), 536_870_912)
    MAX_CONTENT_LENGTH = MAX_UPLOAD_SIZE_BYTES
    SPOOL_MAX_MEMORY_BYTES = _as_int(os.getenv("SPOOL_MAX_MEMORY_BYTES"), 8_388_608)
    TEXT_PREVIEW_MAX_BYTES = _as_int(os.getenv("TEXT_PREVIEW_MAX_BYTES"), 1_048_576)
    DEFAULT_USER_STORAGE_QUOTA_BYTES = _as_int(
        os.getenv("DEFAULT_USER_STORAGE_QUOTA_BYTES"),
        10 * 1024 * 1024 * 1024,
    )
    DEFAULT_ADMIN_STORAGE_QUOTA_BYTES = _as_int(
        os.getenv("DEFAULT_ADMIN_STORAGE_QUOTA_BYTES"),
        0,
    )

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
    WEBDAV_ENABLED = _as_bool(os.getenv("WEBDAV_ENABLED"), True)
    WEBDAV_REALM = os.getenv("WEBDAV_REALM", "NovaDrive WebDAV")
    S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL", "").strip()
    S3_REGION = os.getenv("S3_REGION", "").strip()
    S3_ACCESS_KEY_ID = os.getenv("S3_ACCESS_KEY_ID", "").strip()
    S3_SECRET_ACCESS_KEY = os.getenv("S3_SECRET_ACCESS_KEY", "").strip()
    S3_SESSION_TOKEN = os.getenv("S3_SESSION_TOKEN", "").strip()
    S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "").strip()
    S3_PREFIX = os.getenv("S3_PREFIX", "novadrive").strip().strip("/")
    S3_FORCE_PATH_STYLE = _as_bool(os.getenv("S3_FORCE_PATH_STYLE"), True)
    S3_PRESIGN_TTL_SECONDS = _as_int(os.getenv("S3_PRESIGN_TTL_SECONDS"), 900)

    EMAIL_VERIFICATION_REQUIRED = _as_bool(
        os.getenv("EMAIL_VERIFICATION_REQUIRED"),
        False,
    )
    EMAIL_VERIFICATION_MAX_AGE_SECONDS = _as_int(
        os.getenv("EMAIL_VERIFICATION_MAX_AGE_SECONDS"),
        86_400,
    )
    EMAIL_VERIFICATION_RESEND_INTERVAL_SECONDS = _as_int(
        os.getenv("EMAIL_VERIFICATION_RESEND_INTERVAL_SECONDS"),
        60,
    )

    SMTP_HOST = os.getenv("SMTP_HOST", "").strip()
    SMTP_PORT = _as_int(os.getenv("SMTP_PORT"), 587)
    SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    SMTP_USE_TLS = _as_bool(os.getenv("SMTP_USE_TLS"), True)
    SMTP_USE_SSL = _as_bool(os.getenv("SMTP_USE_SSL"), False)
    SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", "").strip()
    SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", APP_NAME)
    SMTP_TIMEOUT_SECONDS = _as_int(os.getenv("SMTP_TIMEOUT_SECONDS"), 20)

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


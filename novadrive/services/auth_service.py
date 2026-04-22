from __future__ import annotations

import hashlib
import secrets
from datetime import timedelta

from sqlalchemy import func, or_

from novadrive.extensions import db
from novadrive.models import Folder, User, UserSession, utcnow
from novadrive.services.activity_service import ActivityService


class AuthService:
    API_KEY_PREFIX = "ndv_"

    @staticmethod
    def create_user(
        username: str,
        email: str,
        password: str,
        force_role: str | None = None,
        email_verified: bool = False,
    ) -> User:
        normalized_username = username.strip()
        normalized_email = email.strip().lower()

        if AuthService.find_by_username(normalized_username):
            raise ValueError("That username is already taken.")
        if AuthService.find_by_email(normalized_email):
            raise ValueError("That email is already in use.")

        role = force_role or ("admin" if User.query.count() == 0 else "user")
        user = User(
            username=normalized_username,
            email=normalized_email,
            role=role,
            email_verified_at=utcnow() if email_verified else None,
        )
        user.set_password(password)
        db.session.add(user)
        db.session.flush()

        root_folder = Folder(
            name="My Drive",
            owner_id=user.id,
            is_root=True,
        )
        db.session.add(root_folder)
        db.session.commit()

        ActivityService.log(
            action="user.created",
            target_type="user",
            target_id=user.id,
            user_id=user.id,
            metadata={"role": role},
        )
        return user

    @staticmethod
    def authenticate(login: str, password: str, *, record_login: bool = True) -> User | None:
        identity = login.strip().lower()
        user = User.query.filter(
            or_(
                func.lower(User.username) == identity,
                func.lower(User.email) == identity,
            )
        ).first()
        if user and user.check_password(password):
            if record_login:
                user.last_login_at = utcnow()
                db.session.commit()
            return user
        return None

    @staticmethod
    def can_use_password_login(user: User, config) -> bool:
        if not config["EMAIL_VERIFICATION_REQUIRED"]:
            return True
        return user.is_email_verified

    @staticmethod
    def ensure_user_session(
        user: User,
        session_token: str,
        user_agent: str | None,
        ip_address: str | None,
        lifetime_hours: int,
    ) -> UserSession:
        token_hash = hashlib.sha256(session_token.encode("utf-8")).hexdigest()
        session = UserSession(
            user_id=user.id,
            session_token_hash=token_hash,
            user_agent=(user_agent or "")[:255] or None,
            ip_address=ip_address,
            expires_at=utcnow() + timedelta(hours=lifetime_hours),
        )
        db.session.add(session)
        db.session.commit()
        return session

    @staticmethod
    def deactivate_user_session(session_token: str | None) -> None:
        if not session_token:
            return
        token_hash = hashlib.sha256(session_token.encode("utf-8")).hexdigest()
        session = UserSession.query.filter_by(session_token_hash=token_hash, is_active=True).first()
        if not session:
            return
        session.is_active = False
        db.session.commit()

    @staticmethod
    def get_root_folder(user: User) -> Folder:
        root = Folder.query.filter_by(owner_id=user.id, is_root=True, deleted_at=None).first()
        if root:
            return root
        root = Folder(name="My Drive", owner_id=user.id, is_root=True)
        db.session.add(root)
        db.session.commit()
        return root

    @staticmethod
    def find_by_username(username: str) -> User | None:
        return User.query.filter(func.lower(User.username) == username.lower()).first()

    @staticmethod
    def find_by_email(email: str) -> User | None:
        return User.query.filter(func.lower(User.email) == email.lower()).first()

    @staticmethod
    def generate_api_key(user: User) -> str:
        raw_key = f"{AuthService.API_KEY_PREFIX}{secrets.token_urlsafe(32)}"
        user.api_key_hash = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
        user.api_key_last4 = raw_key[-4:]
        user.api_key_created_at = utcnow()
        db.session.commit()

        ActivityService.log(
            action="user.api_key.generated",
            target_type="user",
            target_id=user.id,
            user_id=user.id,
        )
        return raw_key

    @staticmethod
    def ensure_api_key(user: User) -> str | None:
        if user.has_api_key:
            return None
        return AuthService.generate_api_key(user)

    @staticmethod
    def revoke_api_key(user: User) -> None:
        if not user.has_api_key:
            return

        user.api_key_hash = None
        user.api_key_last4 = None
        user.api_key_created_at = None
        db.session.commit()

        ActivityService.log(
            action="user.api_key.revoked",
            target_type="user",
            target_id=user.id,
            user_id=user.id,
        )

    @staticmethod
    def authenticate_api_key(api_key: str | None) -> User | None:
        candidate = (api_key or "").strip()
        if not candidate:
            return None
        digest = hashlib.sha256(candidate.encode("utf-8")).hexdigest()
        return User.query.filter_by(api_key_hash=digest).first()

    @staticmethod
    def mark_email_verified(user: User) -> User:
        if user.is_email_verified:
            return user

        user.email_verified_at = utcnow()
        db.session.commit()

        ActivityService.log(
            action="user.email_verified",
            target_type="user",
            target_id=user.id,
            user_id=user.id,
        )
        return user

    @staticmethod
    def note_verification_email_sent(user: User) -> None:
        user.email_verification_sent_at = utcnow()
        db.session.commit()

        ActivityService.log(
            action="user.verification_email.sent",
            target_type="user",
            target_id=user.id,
            user_id=user.id,
        )

    @staticmethod
    def update_role(user: User, role: str, actor_id: int | None = None) -> User:
        role_value = role.strip().lower()
        if role_value not in {"admin", "user"}:
            raise ValueError("Invalid role.")

        if user.role == "admin" and role_value != "admin" and AuthService.count_admins() <= 1:
            raise ValueError("At least one admin account must remain.")

        user.role = role_value
        db.session.commit()

        ActivityService.log(
            action="user.role.updated",
            target_type="user",
            target_id=user.id,
            user_id=actor_id,
            metadata={"role": role_value},
        )
        return user

    @staticmethod
    def count_admins() -> int:
        return User.query.filter_by(role="admin").count()


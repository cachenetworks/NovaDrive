from __future__ import annotations

import hashlib
from datetime import timedelta

from sqlalchemy import func, or_

from novadrive.extensions import db
from novadrive.models import Folder, User, UserSession, utcnow
from novadrive.services.activity_service import ActivityService


class AuthService:
    @staticmethod
    def create_user(
        username: str,
        email: str,
        password: str,
        force_role: str | None = None,
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
    def authenticate(login: str, password: str) -> User | None:
        identity = login.strip().lower()
        user = User.query.filter(
            or_(
                func.lower(User.username) == identity,
                func.lower(User.email) == identity,
            )
        ).first()
        if user and user.check_password(password):
            user.last_login_at = utcnow()
            db.session.commit()
            return user
        return None

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


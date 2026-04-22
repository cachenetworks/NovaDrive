from __future__ import annotations

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from novadrive.models import User
from novadrive.services.email_service import EmailDeliveryError, EmailService


class VerificationTokenError(ValueError):
    pass


class VerificationService:
    EMAIL_SALT = "novadrive-email-verification"

    @staticmethod
    def generate_email_token(user: User, secret_key: str) -> str:
        serializer = URLSafeTimedSerializer(secret_key)
        return serializer.dumps({"user_id": user.id, "email": user.email}, salt=VerificationService.EMAIL_SALT)

    @staticmethod
    def verify_email_token(token: str, secret_key: str, max_age_seconds: int) -> dict[str, object]:
        serializer = URLSafeTimedSerializer(secret_key)
        try:
            payload = serializer.loads(
                token,
                salt=VerificationService.EMAIL_SALT,
                max_age=max_age_seconds,
            )
        except SignatureExpired as exc:
            raise VerificationTokenError("That verification link has expired.") from exc
        except BadSignature as exc:
            raise VerificationTokenError("That verification link is invalid.") from exc
        return payload

    @staticmethod
    def send_verification_email(*, user: User, verify_url: str, config) -> None:
        text_body = (
            f"Hello {user.username},\n\n"
            f"Confirm your NovaDrive email address by opening this link:\n{verify_url}\n\n"
            "If you did not create this account, you can ignore this email."
        )
        html_body = (
            f"<p>Hello {user.username},</p>"
            f"<p>Confirm your NovaDrive email address by opening this link:</p>"
            f'<p><a href="{verify_url}">{verify_url}</a></p>'
            "<p>If you did not create this account, you can ignore this email.</p>"
        )
        EmailService.send_email(
            config=config,
            to_email=user.email,
            subject="Confirm your NovaDrive email",
            text_body=text_body,
            html_body=html_body,
        )

    @staticmethod
    def ensure_smtp_available(config) -> None:
        if not EmailService.is_configured(config):
            raise EmailDeliveryError("SMTP is not configured for verification emails.")

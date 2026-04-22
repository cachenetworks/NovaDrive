from __future__ import annotations

import smtplib
from email.message import EmailMessage


class EmailDeliveryError(RuntimeError):
    pass


class EmailService:
    @staticmethod
    def is_configured(config) -> bool:
        return bool(config["SMTP_HOST"] and config["SMTP_FROM_EMAIL"])

    @staticmethod
    def send_email(
        *,
        config,
        to_email: str,
        subject: str,
        text_body: str,
        html_body: str | None = None,
    ) -> None:
        if not EmailService.is_configured(config):
            raise EmailDeliveryError("SMTP is not configured.")

        message = EmailMessage()
        sender_name = config["SMTP_FROM_NAME"].strip()
        sender_email = config["SMTP_FROM_EMAIL"].strip()
        message["Subject"] = subject
        message["From"] = f"{sender_name} <{sender_email}>" if sender_name else sender_email
        message["To"] = to_email
        message.set_content(text_body)
        if html_body:
            message.add_alternative(html_body, subtype="html")

        try:
            smtp = EmailService._connect(config)
            try:
                smtp.send_message(message)
            finally:
                smtp.quit()
        except Exception as exc:
            raise EmailDeliveryError("SMTP delivery failed.") from exc

    @staticmethod
    def _connect(config):
        host = config["SMTP_HOST"]
        port = config["SMTP_PORT"]
        timeout = config["SMTP_TIMEOUT_SECONDS"]

        if config["SMTP_USE_SSL"]:
            smtp = smtplib.SMTP_SSL(host=host, port=port, timeout=timeout)
        else:
            smtp = smtplib.SMTP(host=host, port=port, timeout=timeout)
            if config["SMTP_USE_TLS"]:
                smtp.starttls()

        if config["SMTP_USERNAME"]:
            smtp.login(config["SMTP_USERNAME"], config["SMTP_PASSWORD"])
        return smtp

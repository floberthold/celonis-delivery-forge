from __future__ import annotations

import smtplib
from email.message import EmailMessage

from foundry.settings import get_settings


def send_email(*, to_email: str, subject: str, body_text: str) -> None:
    settings = get_settings()
    if not settings.smtp_host.strip() or not settings.smtp_from_email.strip():
        raise ValueError("SMTP is not configured. Set FORGE_SMTP_HOST and FORGE_SMTP_FROM_EMAIL.")

    message = EmailMessage()
    message["From"] = settings.smtp_from_email
    message["To"] = to_email.strip().lower()
    message["Subject"] = subject
    message.set_content(body_text)

    if settings.smtp_use_ssl:
        with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port) as smtp:
            if settings.smtp_username:
                smtp.login(settings.smtp_username, settings.smtp_password)
            smtp.send_message(message)
        return

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as smtp:
        if settings.smtp_starttls:
            smtp.starttls()
        if settings.smtp_username:
            smtp.login(settings.smtp_username, settings.smtp_password)
        smtp.send_message(message)

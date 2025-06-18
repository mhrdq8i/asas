import logging

from pydantic import EmailStr
from fastapi_mail import (
    FastMail,
    MessageSchema,
    ConnectionConfig,
    MessageType,
)

from src.core.config import settings


logger = logging.getLogger(__name__)

# --- Build ConnectionConfig ---
# This logic determines if credentials
# should be used for the SMTP server.
use_credentials = bool(
    settings.MAIL_USERNAME and settings.MAIL_PASSWORD
)

password = settings.MAIL_PASSWORD.get_secret_value(
) if settings.MAIL_PASSWORD else ""

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME or "",
    MAIL_PASSWORD=password,
    MAIL_FROM=settings.MAIL_FROM_EMAIL,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_STARTTLS=settings.MAIL_USE_TLS,
    MAIL_SSL_TLS=settings.MAIL_USE_SSL,
    USE_CREDENTIALS=use_credentials,
    VALIDATE_CERTS=True if settings.MAIL_SERVER not in [
        "localhost", "127.0.0.1", "mailhog"
    ] else False,
    TIMEOUT=settings.MAIL_TIMEOUT,
)


fm = FastMail(conf)


async def send_email_async(
    email_to: EmailStr,
    subject: str,
    html_content: str,
) -> None:
    """
    Sends an email using fastapi-mail with detailed error logging.
    """

    if not settings.MAIL_FROM_EMAIL:
        logger.error(
            "MAIL_FROM_EMAIL is not configured. Cannot send email."
        )

        return

    message = MessageSchema(
        subject=subject,
        recipients=[email_to],
        body=html_content,
        subtype=MessageType.html,
    )

    try:
        logger.info(
            f"Attempting to send email to {email_to} via "
            f"{settings.MAIL_SERVER}:{settings.MAIL_PORT}"
        )

        await fm.send_message(message)

        logger.info(
            f"Email successfully sent to {email_to} with subject: {subject}"
        )

    except Exception as e:
        # This will catch any error during the send_message call,
        # including connection errors, auth errors, etc.
        logger.error(
            f"Failed to send email to {email_to}. Error: {e}",
            exc_info=True  # This includes the full traceback in the log
        )
        # Re-raise the exception so the Celery
        # task knows it failed and can retry
        raise e


async def send_email_verification(
    email_to: EmailStr, username: str, verification_token: str
) -> None:
    """
    Prepares and sends the email verification message.
    """

    project_name = settings.APP_NAME

    if not settings.FRONTEND_URL:
        logger.error(
            "FRONTEND_URL is not configured. "
            "Cannot generate verification link."
        )

        return

    verification_link = (
        f"{settings.FRONTEND_URL}/verify-email?token={verification_token}"
    )

    subject = f"Verify your email for {project_name}"

    html_content = f"""
    <html><body>
        <p>Hi {username},</p>
        <p>Thanks for registering!</p>
        <p>Please verify your email by clicking the link below:</p>
        <p><a href="{verification_link}">Verify Email Address</a></p>
    </body></html>
    """

    await send_email_async(
        email_to=email_to, subject=subject, html_content=html_content
    )


async def send_password_reset_email(
    email_to: EmailStr, username: str, reset_token: str
) -> None:
    """
    Prepares and sends the password reset message.
    """

    project_name = settings.APP_NAME

    if not settings.FRONTEND_URL:
        logger.error(
            "FRONTEND_URL is not configured. Cannot generate reset link."
        )

        return

    reset_link = (
        f"{settings.FRONTEND_URL}/reset-password-confirm?token={reset_token}"
    )

    subject = f"Password Reset Request for {project_name}"

    html_content = f"""
    <html><body>
        <p>Hi {username},</p>
        <p>You requested a password reset. Click the link below:</p>
        <p><a href="{reset_link}">Reset Password</a></p>
    </body></html>
    """

    await send_email_async(
        email_to=email_to, subject=subject, html_content=html_content
    )

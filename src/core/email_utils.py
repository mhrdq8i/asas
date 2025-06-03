from pydantic import EmailStr
from fastapi_mail import (
    FastMail,
    MessageSchema,
    ConnectionConfig,
    MessageType
)

from src.core.config import settings

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    # Pass SecretStr | None directly
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM_EMAIL,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_STARTTLS=settings.MAIL_USE_TLS,
    MAIL_SSL_TLS=settings.MAIL_USE_SSL,
    # This logic remains important
    USE_CREDENTIALS=bool(
        settings.MAIL_USERNAME and settings.MAIL_PASSWORD
    ),
    VALIDATE_CERTS=True if settings.MAIL_SERVER not in [
        "localhost", "127.0.0.1"
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
    Sends an email using fastapi-mail
    with direct HTML content.
    """
    mail_from = "MAIL_FROM_EMAIL must be set in settings"
    assert settings.MAIL_FROM_EMAIL, mail_from

    message = MessageSchema(
        subject=subject,
        recipients=[email_to],
        html=html_content,
        subtype=MessageType.html
    )

    try:
        await fm.send_message(message)
        print(
            f"Email successfully sent to {email_to} with subject: {subject}"
        )
    except Exception as e:
        print(
            f"Error sending email to {email_to}: {e}"
        )


async def send_email_verification(
    email_to: EmailStr,
    username: str,
    verification_token: str
) -> None:
    project_name = settings.APP_NAME
    frontend_msg = "FRONTEND_URL must be set in settings"
    assert settings.FRONTEND_URL, frontend_msg
    verification_link = \
        f"{settings.FRONTEND_URL}/verify-email?token={verification_token}"
    token_expiry_hours = settings.EMAIL_VERIFY_TOKEN_EXPIRE_MINUTES // 60

    subject = f"Verify your email for {project_name}"
    html_content = f"""
    <html><body>
        <p>Hi {username},</p>
        <p>Thanks for registering!
        Please verify your email by clicking the link below:</p>
        <p><a href="{verification_link}">Verify Email Address</a></p>
        <p>This link will expire in {token_expiry_hours} hour(s).</p>
        <p>Thanks,<br>The {project_name} Team</p>
    </body></html>
    """
    await send_email_async(
        email_to=email_to,
        subject=subject,
        html_content=html_content
    )


async def send_password_reset_email(
    email_to: EmailStr,
    username: str,
    reset_token: str
) -> None:
    project_name = settings.APP_NAME
    frontend_msg = "FRONTEND_URL must be set in settings"
    assert settings.FRONTEND_URL, frontend_msg
    reset_link = \
        f"{settings.FRONTEND_URL}/reset-password-confirm?token={reset_token}"
    token_expiry_minutes = settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES

    subject = f"Password Reset Request for {project_name}"
    html_content = f"""
    <html><body>
        <p>Hi {username},</p>
        <p>You requested a password reset
          for your account on {project_name}.</p>
        <p>Click the link below to set a new password:</p>
        <p><a href="{reset_link}">Reset Password</a></p>
        <p>If you did not request this, please ignore this email.</p>
        <p>This link will expire in {token_expiry_minutes} minutes.</p>
        <p>Thanks,<br>The {project_name} Team</p>
    </body></html>
    """
    await send_email_async(
        email_to=email_to,
        subject=subject,
        html_content=html_content
    )

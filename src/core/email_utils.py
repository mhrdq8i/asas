from pydantic import EmailStr
from fastapi_mail import (
    FastMail,
    MessageSchema,
    ConnectionConfig,
    MessageType
)

from src.core.config import settings


effective_mail_username_str: str | None = None
effective_mail_password_str: str | None = None

if settings.MAIL_USERNAME \
        and settings.MAIL_USERNAME.strip():
    effective_mail_username_str = settings.MAIL_USERNAME
    # If username is provided and non-empty,
    # password must also be provided
    # (as per our Settings validator)
    if settings.MAIL_PASSWORD:
        effective_mail_password_str \
            = settings.MAIL_PASSWORD.get_secret_value()
else:
    effective_mail_username_str = None
    effective_mail_password_str = None

use_actual_credentials = bool(
    effective_mail_username_str
    and effective_mail_password_str
)

# --- DEBUG PRINT ---
print("\n--- DEBUG: fastapi-mail ConnectionConfig effective values ---")
print(
    "Effective MAIL_USERNAME (str): "
    f"{effective_mail_username_str}"
)
print(
    "Effective MAIL_PASSWORD (str): "
    f"{'********' if effective_mail_password_str else None}"
)
print(
    "MAIL_FROM: "
    f"{settings.MAIL_FROM_EMAIL}"
)
print(
    "MAIL_PORT: "
    f"{settings.MAIL_PORT}"
)
print(
    "MAIL_SERVER: "
    f"{settings.MAIL_SERVER}"
)
print(
    "MAIL_FROM_NAME: "
    f"{settings.MAIL_FROM_NAME}"
)
print(
    "MAIL_STARTTLS: "
    f"{settings.MAIL_USE_TLS}"
)
print(
    "MAIL_SSL_TLS: "
    f"{settings.MAIL_USE_SSL}"
)
print(
    "USE_CREDENTIALS (passed to ConnectionConfig): "
    f"{use_actual_credentials}"
)
print(
    "VALIDATE_CERTS: "
    f"{True if settings.MAIL_SERVER not in ['localhost', '127.0.0.1'] else False}"
)
print(
    "TIMEOUT: "
    f"{settings.MAIL_TIMEOUT}"
)

# print("--- END DEBUG ---")

conf = ConnectionConfig(
    MAIL_USERNAME=effective_mail_username_str
    if effective_mail_username_str is not None else "",
    MAIL_PASSWORD=effective_mail_password_str
    if effective_mail_password_str is not None else "",
    MAIL_FROM=settings.MAIL_FROM_EMAIL,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_STARTTLS=settings.MAIL_USE_TLS,
    MAIL_SSL_TLS=settings.MAIL_USE_SSL,
    USE_CREDENTIALS=use_actual_credentials,
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
    if not settings.MAIL_FROM_EMAIL:
        print(
            "ERROR: "
            "MAIL_FROM_EMAIL is not configured. "
            "Cannot send email."
        )
        return

    message = MessageSchema(
        subject=subject,
        recipients=[email_to],
        body=html_content,
        subtype=MessageType.html
    )

    try:
        print(
            "Attempting to send "
            f"email to {email_to} "
            f"with subject: {subject} "
            "via server "
            f"{settings.MAIL_SERVER}:{settings.MAIL_PORT}"
        )
        await fm.send_message(
            message
        )
        print(
            "Email successfully sent "
            f"to {email_to} "
            f"with subject: {subject} "
        )

    except Exception as e:
        print(
            "Error sending email "
            f"to {email_to}: {e}"
        )


async def send_email_verification(
    email_to: EmailStr,
    username: str,
    verification_token: str
) -> None:
    project_name = settings.APP_NAME
    if not settings.FRONTEND_URL:
        print(
            "ERROR: "
            "FRONTEND_URL is not configured. "
            "Cannot generate verification link. "
        )
        return

    verification_link = (
        f"{settings.FRONTEND_URL}/verify-email?token={verification_token}"
    )
    token_expiry_hours = settings.EMAIL_VERIFY_TOKEN_EXPIRE_MINUTES // 60

    print(
        "*******************************\n"
        "DEBUG !!!\n"
        "Generated TOKEN IS:\n"
        f"{verification_token}\n"
        "*******************************"
    )

    subject = f"Verify your email for {project_name}"
    html_content = f"""
    <html><body>
        <p>Hi {username},</p>
        <p>Thanks for registering! Please verify your email by clicking the link below:</p>
        <p><a href="{verification_link}">Verify Email Address</a></p>
        <p>If you did not create an account, no further action is required.</p>
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
    if not settings.FRONTEND_URL:
        print(
            "ERROR: "
            "FRONTEND_URL is not configured. "
            "Cannot generate reset link."
        )
        return

    reset_link = (
        f"{settings.FRONTEND_URL}/reset-password-confirm?token={reset_token}"
    )
    token_expiry_minutes = (
        settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES
    )

    subject = f"Password Reset Request for {project_name}"
    html_content = f"""
    <html><body>
        <p>Hi {username},</p>
        <p>You (or someone else) requested a password reset</p>
        <p>for your account on {project_name}.</p>
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

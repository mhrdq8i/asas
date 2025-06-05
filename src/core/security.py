from typing import Any, Union
from datetime import (
    datetime,
    timedelta,
    timezone
)
from jose import (
    jwt,
    JWTError,
    ExpiredSignatureError
)
from pwdlib import PasswordHash

from src.core.config import settings


password_hasher = PasswordHash.recommended()


ALGORITHM = str(
    settings.ALGORITHM
)
SECRET_KEY = str(
    settings.SECRET_KEY
)
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    settings.ACCESS_TOKEN_EXPIRE_MINUTES
)


def verify_password(
        plain_password: str,
        hashed_password: str
) -> bool:
    try:
        return password_hasher.verify(
            plain_password.encode('utf-8'),
            hashed_password
        )

    except Exception as e:
        print(
            "DEBUG: Password verification failed: "
            f"{type(e).__name__} - {e}"
        )

        return False


def get_password_hash(
        password: str
) -> str:
    return password_hasher.hash(
        password.encode('utf-8')
    )


def create_access_token(
    subject: Union[str, Any],
    expires_delta: timedelta | None = None
) -> str:

    default_expiry_minutes = (
        ACCESS_TOKEN_EXPIRE_MINUTES
    )

    if isinstance(
        subject, dict
    ):
        token_type = subject.get("type")

        if token_type == "password_reset":
            default_expiry_minutes = (
                settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES
            )

        elif token_type == "email_verification":
            default_expiry_minutes = (
                settings.EMAIL_VERIFY_TOKEN_EXPIRE_MINUTES
            )

    if expires_delta:
        expire = datetime.now(
            timezone.utc
        ) + expires_delta
    else:
        expire = datetime.now(
            timezone.utc
        ) + timedelta(
            minutes=default_expiry_minutes
        )

    if isinstance(
        subject, dict
    ):
        to_encode = subject.copy()
    else:
        to_encode = {
            "sub": str(subject)
        }

    to_encode["exp"] = expire

    print(
        f"DEBUG create_access_token: Encoding with "
        f"ALGORITHM: {ALGORITHM} "
        "SECRET_KEY: "
        f"{SECRET_KEY[:5]}...{SECRET_KEY[-5:]}"
        if len(SECRET_KEY) > 10 else SECRET_KEY
    )

    encoded_jwt = jwt.encode(
        to_encode, SECRET_KEY,
        algorithm=ALGORITHM
    )

    return encoded_jwt


def decode_token(token: str) -> dict | None:
    """
    Decodes a JWT token.
    Providing more specific error logging.
    Catches general JWTError
    for signature/algorithm issues.
    """

    # --- DEBUG LINES ---
    print(
        "--- DEBUG: Attempting to decode token ---"
        "\n"
        f"Token (first 10 chars): {token[:10]}..."
    )
    # Mask most of the secret
    # key for security in logs
    masked_secret_key = (
        f"{SECRET_KEY[:3]}...{SECRET_KEY[-3:]}"
        if len(SECRET_KEY) > 6 else SECRET_KEY
    )
    print(
        f"Using SECRET_KEY (masked): {masked_secret_key}"
    )
    print(
        f"Using ALGORITHM: {ALGORITHM}"
    )
    # --- END DEBUG LINES ---

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )
        print(
            "DEBUG: Token decoded successfully. "
            f"Payload subject: {payload.get('sub')}, "
            f"type: {payload.get('type')}"
        )
        return payload

    except ExpiredSignatureError:
        print(
            "ERROR decode_token: Token has expired."
        )
        return None

    except JWTError as e:
        print(
            f"ERROR decode_token: A JWTError occurred: "
            f"{type(e).__name__} - {e}. "
            "This could be due to an invalid signature, "
            "algorithm mismatch, or a tampered token."
        )
        return None

    except Exception as e:
        print(
            f"ERROR decode_token: "
            "An unexpected error occurred "
            "during token decoding: "
            f"{type(e).__name__} - {e}"
        )
        return None

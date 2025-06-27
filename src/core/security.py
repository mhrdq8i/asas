from logging import getLogger
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


logger = getLogger(__name__)

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

    except Exception:
        logger.warning(
            "Password verification failed "
            "with an unexpected error.",
            exc_info=True
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

    default_expiry_minutes = ACCESS_TOKEN_EXPIRE_MINUTES

    if isinstance(subject, dict):
        token_type = subject.get("type")

        if token_type == "password_reset":
            default_expiry_minutes = \
                settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES

        elif token_type == "email_verification":
            default_expiry_minutes = \
                settings.EMAIL_VERIFY_TOKEN_EXPIRE_MINUTES

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta

    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=default_expiry_minutes
        )

    if isinstance(subject, dict):
        to_encode = subject.copy()

    else:
        to_encode = {"sub": str(subject)}

    to_encode["exp"] = expire

    encoded_jwt = jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return encoded_jwt


def decode_token(token: str) -> dict | None:
    """
    Decodes a JWT token.
    Provides specific error logging.
    """

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        logger.debug(
            "Token decoded successfully for subject "
            f"{payload.get('sub')}"
        )

        return payload

    except ExpiredSignatureError:
        logger.warning(
            "Token decoding failed: "
            "Token has expired."
        )

        return None

    except JWTError as e:
        logger.warning(
            f"Token decoding failed due to JWTError: {e}. "
            "This could be due to an "
            "invalid signature, algorithm mismatch, "
            "or a tampered token."
        )

        return None

    except Exception:
        logger.error(
            "An unexpected error occurred "
            "during token decoding.",
            exc_info=True
        )

        return None

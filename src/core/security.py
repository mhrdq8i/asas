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

ALGORITHM = str(settings.ALGORITHM)
SECRET_KEY = str(settings.SECRET_KEY)
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
            "DEBUG: Password "
            f"verification failed: {e}"
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

    if expires_delta:
        expire = datetime.now(
            timezone.utc
        ) + expires_delta
    else:
        expire = datetime.now(
            timezone.utc
        ) + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
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

    encoded_jwt = jwt.encode(
        to_encode,
        key=SECRET_KEY,
        algorithm=ALGORITHM
    )
    return encoded_jwt


def decode_token(
        token: str
) -> dict | None:
    """
    Decodes a JWT token,
    providing more specific error logging.
    Catches general JWTError for
    signature/algorithm issues.
    """
    try:
        payload = jwt.decode(
            token,
            key=SECRET_KEY,
            algorithms=[ALGORITHM]
        )
        return payload

    except ExpiredSignatureError:
        print(
            "ERROR decode_token: "
            "Token has expired."
        )
        return None

    except JWTError as e:
        print(
            "ERROR decode_token: A JWTError occurred: "
            f"{type(e).__name__} - {e}. "
            "This could be due to an invalid signature, "
            "algorithm mismatch, or a tampered token."
        )
        return None

    except Exception as e:
        print(
            "ERROR decode_token: "
            "An unexpected error occurred "
            "during token decoding: "
            f"{type(e).__name__} - {e}"
        )
        return None

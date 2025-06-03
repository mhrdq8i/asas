from datetime import (
    datetime,
    timedelta,
    timezone
)
from typing import Any, Union
from jose import jwt, JWTError
from pwdlib import PasswordHash

from src.core.config import settings


# This will typically use Argon2
# if installed with 'pwdlib[argon2]'
password_hasher = PasswordHash.recommended()


ALGORITHM = settings.ALGORITHM
# The SECRET_KEY should be a strong, random string
SECRET_KEY = settings.SECRET_KEY
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES


def verify_password(
    plain_password: str,
    hashed_password: str
) -> bool:
    """
    Verifies a plain password against
     a hashed password using pwdlib.
    """

    # pwdlib expects bytes for password,
    # so we encode the plain password
    return password_hasher.verify(
        plain_password.encode('utf-8'),
        hashed_password
    )


def get_password_hash(
        password: str
) -> str:
    """
    Hashes a plain password using pwdlib.
    """

    # pwdlib expects bytes for
    # password, so we encode it
    # The hash produced will be a string

    return password_hasher.hash(
        password.encode('utf-8')
    )


def create_access_token(
    subject: Union[str, Any],
    expires_delta: timedelta | None = None
) -> str:
    """
    Creates a new JWT access token.

    Args:

        subject:
            The subject of the token
            (e.g., username or user ID).

        expires_delta: Optional timedelta for token expiration.
                        If None, uses default expiration
                        from settings.

    Returns:
        The encoded JWT access token.
    """

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

    to_encode = {
        "exp": expire,
        "sub": str(subject)
    }

    encoded_jwt = jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return encoded_jwt


def decode_token(
    token: str
) -> dict | None:
    """
    Decodes a JWT token.

    Args:

        token: The JWT token string.

    Returns:
        The decoded payload if the token is
        valid and not expired, otherwise None.
    """

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )
        return payload

    except JWTError:
        # This could be due to token expiration or an invalid signature
        # You might want to log the specific JWTError here
        return None

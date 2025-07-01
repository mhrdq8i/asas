from jose import JWTError
from typing import Annotated

from fastapi import Depends
from fastapi.security import (
    OAuth2PasswordBearer
)

from src.exceptions.user_exceptions import (
    NotAuthenticatedException,
    InsufficientPermissionsException
)
from src.services.user_service import (
    UserService
)
from src.models.user import User
from src.core import security
from src.dependencies.service_deps import (
    get_user_service
)

# This defines the security scheme for OAuth2.
# It tells FastAPI how to find the token.
# The `tokenUrl` points to the login
# endpoint where clients can obtain a token.
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/token"
)


async def get_current_user(
    token: Annotated[
        str,
        Depends(
            oauth2_scheme
        )
    ],
    user_service: Annotated[
        UserService,
        Depends(
            get_user_service
        )
    ]
) -> User:
    """
    Decodes a JWT token to retrieve the current user.

    This is the foundational dependency for authentication.
    It performs the
    following steps:
    1. Receives the token from the `Authorization:
       Bearer <token>` header.
    2. Decodes and validates the JWT signature and expiration.
    3. Extracts the subject ('sub', which is the username)
       from the token payload.
    4. Fetches the corresponding user from the database.

    Args:
        token: The JWT token string provided by the client.
        user_service: An instance of UserService to
        interact with the database.

    Raises:
        NotAuthenticatedException:
          If the token is invalid, expired, malformed,
         or the user does not exist in the database.

    Returns:
        The authenticated User model instance from the database.
    """

    try:
        payload = security.decode_token(
            token
        )

        if payload is None:
            raise NotAuthenticatedException(
                detail=(
                    "Could not validate credentials "
                    "-"
                    " token invalid or expired"
                )
            )

        token_sub = payload.get("sub")

        if token_sub is None:
            raise NotAuthenticatedException(
                detail=(
                    "Could not validate credentials "
                    "-"
                    " token subject missing"
                )
            )

        # Assumes 'sub' claim in the
        # JWT payload is the username.
        user = await \
            user_service.crud_user.get_user_by_username(
                username=token_sub
            )

    # Covers various JWT issues
    # like signature, expiry etc
    except JWTError:

        # Log the specific JWTError
        # for debugging if needed
        raise NotAuthenticatedException(
            detail=(
                "Could not validate credentials "
                "-"
                " JWT error"
            )
        )

    # Re-raise the custom exception
    # to be handled by FastAPI.
    except NotAuthenticatedException:
        raise

    # Catch any other unexpected
    # errors during token processing
    except Exception as e:
        print(
            "Unexpected error during "
            f"token processing: {e}"
        )

        raise NotAuthenticatedException(
            detail=(
                "Could not validate credentials "
                "-"
                " unexpected error"
            )
        )

    if user is None:
        raise NotAuthenticatedException(
            detail=(
                "User not found "
                "or "
                "credentials invalid"
            )
        )

    return user


async def get_current_active_user(
    current_user: Annotated[
        User,
        Depends(
            get_current_user
        )
    ]
) -> User:
    """
    Ensures the authenticated user is currently active.

    This dependency builds upon `get_current_user`.
    After successfully authenticating the user,
    it checks the `is_active` flag.
    It should be used for most endpoints
    that require a logged-in and active user.

    Args:
        current_user:
            The User object injected by the
            `get_current_user` dependency.

    Raises:
        InsufficientPermissionsException:
            If the user's `is_active` attribute is False.

    Returns:
        The authenticated and active User model instance.
    """

    if not current_user.is_active:
        # You might want a more specific
        # exception here
        # e.g., InactiveUserException
        raise InsufficientPermissionsException(
            detail="Inactive user"
        )

    return current_user


async def get_current_active_superuser(
    current_user: Annotated[
        User,
        Depends(
            get_current_active_user
        )
    ]
) -> User:
    """
    Ensures the authenticated user is an active superuser.

    This is the highest level of authorization,
    intended for administrative endpoints.
    It builds upon `get_current_active_user`,
    adding a check for the `is_superuser` flag.

    Args:
        current_user:
            The User object injected by the
            `get_current_active_user` dependency.

    Raises:
        InsufficientPermissionsException:
            If the user's `is_superuser` attribute is False.

    Returns:
        The authenticated, active, and superuser User model instance.
    """

    if not current_user.is_superuser:
        raise InsufficientPermissionsException(
            detail=(
                "The user doesn't have "
                "enough privileges "
                "(not a superuser)."
            )
        )

    return current_user


# async def get_current_user_with_role(
#     required_role: UserRoleEnum,
#     current_user: User = Depends(
#         get_current_active_user
#     )
# ):
#     if current_user.role != required_role:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Operation not permitted for this user role.")
#     return current_user

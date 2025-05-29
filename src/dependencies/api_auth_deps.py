from jose import JWTError
from typing import Annotated

from fastapi import Depends
from fastapi.security import (
    OAuth2PasswordBearer
)

from src.exceptions import (
    NotAuthenticatedException,
    InsufficientPermissionsException
)
from src.services.user_service import (
    UserService
)
from src.models.user import User
from src.core import security
from src.dependencies.service_deps import get_user_service

# OAuth2PasswordBearer scheme
# The tokenUrl should point to your login
# endpoint (which we will create in auth.py)
# Make sure the path is correct based on your
# router prefix for auth.
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/token"
)


async def get_current_user(
    token: Annotated[
        str,
        Depends(oauth2_scheme)
    ],
    user_service: Annotated[
        UserService,
        Depends(
        get_user_service
        )
    ]  # Inject UserService
) -> User:
    """
    Dependency to get the current user from a JWT token.
    Decodes the token, validates it,
    and retrieves the user from the database.
    Raises HTTPException if authentication fails.
    """
    try:
        payload = security.decode_token(
            token
        )
        if payload is None:
            raise NotAuthenticatedException(
                detail="Could not validate credentials -\
                    token invalid or expired"
            )

        token_sub = payload.get("sub")
        if token_sub is None:
            raise NotAuthenticatedException(
                detail="Could not validate credentials -\
                    token subject missing"
            )

        # Assuming 'sub' in the token is the username.
        # If 'sub' is user_id (UUID), you'd parse it
        # as UUID and use get_user_by_id.
        # For this example, let's assume 'sub' is username.
        # If you store user_id in 'sub', change this part:
        # try:
        #     user_id = UUID(token_sub)
        # except ValueError:
        #     raise NotAuthenticatedException(
        # detail="Invalid user identifier in token"
        # )
        # user = await user_service.get_user_by_id(user_id=user_id)

        # If 'sub' is username:
        # Accessing crud_user directly for this specific lookup
        user = await user_service.crud_user.get_user_by_username(
            username=token_sub
        )

    # Covers various JWT issues like signature, expiry etc
    except JWTError:
        # Log the specific JWTError for debugging if needed
        raise NotAuthenticatedException(
            detail="Could not validate credentials - JWT error"
        )
    except NotAuthenticatedException:  # Re-raise our custom exception
        raise
    # Catch any other unexpected errors during token processing
    except Exception as e:
        # Log error e
        print(f"Unexpected error during token processing: {e}")
        raise NotAuthenticatedException(
            detail="Could not validate credentials - unexpected error"
        )

    if user is None:
        raise NotAuthenticatedException(
            detail="User not found or credentials invalid"
        )

    return user


async def get_current_active_user(
    current_user: Annotated[
        User,
        Depends(get_current_user)
    ]
) -> User:
    """
    Dependency to get the current active user.
    Relies on get_current_user and then checks if the user is active.
    """
    if not current_user.is_active:
        # You might want a more specific exception here
        # e.g., InactiveUserException
        raise InsufficientPermissionsException(
            detail="Inactive user"
        )

    return current_user


async def get_current_active_superuser(
    current_user: Annotated[
        User,
        Depends(get_current_active_user)
    ]
) -> User:
    """
    Dependency to get the current active superuser.
    Relies on get_current_active_user and
    then checks if the user is a superuser.
    """
    if not current_user.is_superuser:
        raise InsufficientPermissionsException(
            detail="The user doesn't have enough privileges (not a superuser)."
        )

    return current_user


# async def get_current_user_with_role(
#     required_role: UserRoleEnum,
#     current_user: User = Depends(
#         get_current_active_user
#     )
# ):
#     if current_user.role != required_role:
#         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
#                             detail="Operation not permitted for this user role.")
#     return current_user

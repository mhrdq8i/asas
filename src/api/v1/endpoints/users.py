from uuid import UUID
from typing import Annotated, List

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)

from src.api.v1.schemas.user_schemas import (
    UserCreate,
    UserRead,
    UserUpdate
)
from src.dependencies.service_deps import (
    get_user_service
)
from src.dependencies.api_auth_deps import (
    get_current_active_user,
    get_current_active_superuser
)
from src.services.user_service import (
    UserService
)
from src.models.user import (
    User as UserModel
)
from src.exceptions.base_exceptions import (
    AppException
)
from src.exceptions.common_exceptions import (
    DuplicateResourceException
)
from src.exceptions.user_exceptions import (
    UserNotFoundException
)


router = APIRouter(
    prefix="/users"
)


@router.post(
    "/",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register New User",
    description="Create a new user account.\
        Username and email must be unique."
)
async def register_new_user(
    user_in: UserCreate,
    user_service: Annotated[
        UserService,
        Depends(get_user_service)
    ]
):
    """
    Create a new user.
    - `username`: Must be unique.
    - `email`: Must be unique.
    - `password`: Will be hashed.
    """

    try:
        created_user = await user_service.register_user(
            user_in=user_in
        )
        return created_user

    except DuplicateResourceException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.detail,
        )

    # Catch other custom app exceptions from service
    except AppException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.detail
        )

    # Catch any unexpected errors
    except Exception as e:
        # Log the error e server-side
        print(f"Unexpected error during user registration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during user registration.",
        )


@router.get(
    "/me",
    response_model=UserRead,
    summary="Get Current User",
    description="Get all information about the currently authenticated user."
)
async def read_users_me(
    current_user: Annotated[
        UserModel,
        Depends(get_current_active_user)
    ]
):
    """
    Get current logged-in user's information.
    """

    # The get_current_active_user dependency
    # already returns the user model.
    # No further service call is strictly needed
    # here if UserRead can be created from UserModel.

    return current_user


@router.put(
    "/me",
    response_model=UserRead,
    summary="Update Current User Profile",
    description="Update the profile information \
      for the currently authenticated user."
)
async def update_users_me(
    user_update_in: UserUpdate,
    current_user: Annotated[
        UserModel,
        Depends(get_current_active_user)
    ],
    user_service: Annotated[
        UserService,
        Depends(get_user_service)
    ],
):
    """
    Update current logged-in user's profile information.
    Password updates should be handled by a separate endpoint.
    """

    try:
        updated_user = await user_service.update_user_profile(
            current_user=current_user,
            user_in=user_update_in
        )
        return updated_user

    except DuplicateResourceException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.detail
        )

    # Should not happen if current_user is from a valid token
    except UserNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.detail
        )

    except AppException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.detail
        )

    except Exception as e:
        print(f"Unexpected error during user profile update: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while updating the profile.",
        )


# --- Admin Endpoints (Example) ---
# These would typically be
# protected by a dependency like
# Depends(get_current_active_superuser)
@router.get(
    "/",
    response_model=List[UserRead],
    summary="List Users (Admin)",
    description="Get a list of all users. Requires superuser privileges.",
    dependencies=[
        Depends(
            get_current_active_superuser
        )
    ]  # Protect this endpoint
)
async def read_users_list(
    user_service: Annotated[
        UserService,
        Depends(get_user_service)
    ],
    skip: int = 0,
    limit: int = 100
):
    """
    Retrieve a list of users.
    Accessible only by superusers.
    """

    users = await user_service.get_users_list(
        skip=skip,
        limit=limit
    )

    return users


@router.get(
    "/{user_id}",
    response_model=UserRead,
    summary="Get User by ID (Admin)",
    description="Get a specific user by their ID.\
        Requires superuser privileges.",
    dependencies=[
        Depends(
            get_current_active_superuser
        )
    ]
)
async def read_user_by_id_admin(
    user_id: UUID,
    user_service: Annotated[
        UserService,
        Depends(
            get_user_service
        )
    ]
):
    """
    Retrieve a specific user by ID.
    Accessible only by superusers.
    """

    try:
        user = await user_service.get_user_by_id(
            user_id=user_id
        )
        return user

    except UserNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.detail
        )

    except AppException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.detail
        )

# You would also add endpoints for admin to update users,
# soft/hard delete users, etc.
# Example:
# @router.delete(
#     "/{user_id}/soft-delete",
#     response_model=UserRead,
#     summary="Soft Delete User (Admin)",
#     dependencies=[Depends(get_current_active_superuser)]
# )
# async def soft_delete_user_admin(
#     user_id_to_delete: uuid.UUID,
#     current_admin_user: Annotated[UserModel, Depends(
# get_current_active_superuser)],
#     user_service: Annotated[UserService, Depends(get_user_service)]
# ):
#     try:
#         deleted_user = await user_service.soft_delete_user(
#             user_to_delete_id=user_id_to_delete,
#             performing_user=current_admin_user
#         )
#         return deleted_user
#     except UserNotFoundException as e:
#         raise HTTPException(
# status_code=status.HTTP_404_NOT_FOUND,
#  detail=e.detail)
#     except InvalidOperationException as e:
#     # e.g., user already deleted or cannot be deleted
#         raise HTTPException(
# status_code=status.HTTP_400_BAD_REQUEST,
#  detail=e.detail
# )
#     except AppException as e:
#         raise HTTPException(
# status_code=e.status_code,
#  detail=e.detail)

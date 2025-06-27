from typing import Annotated, List
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from src.api.v1.schemas.user_schemas import (
    UserCreate,
    UserRead,
    UserUpdate,
    UserUpdatePassword,
)
from src.dependencies.service_deps import (
    get_user_service
)
from src.dependencies.auth_deps import (
    get_current_active_user,
    get_current_active_superuser,
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

# ===================
# Router Definitions
# ===================

# Public user router
# (for registration and self-management)
user_router = APIRouter(
    prefix="/users",
)

# Admin router
# (for managing all users, requires superuser privileges)
admin_router = APIRouter(
    prefix="/admin/users",
    dependencies=[
        Depends(get_current_active_superuser)
    ]
)


# ======================
# Public User Endpoints
# ======================


@user_router.post(
    "/",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register New User"
)
async def register_new_user(
    user_in: UserCreate,
    user_service: Annotated[
        UserService,
        Depends(get_user_service)
    ],
) -> UserRead:
    """
    Create a new user account.
    - Username and email must be unique.
    - A verification email will be queued by the service via Celery.
    """

    try:
        created_user = await user_service.register_user(
            user_in=user_in
        )

        return created_user

    except AppException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.detail
        )


@user_router.get(
    "/me",
    response_model=UserRead,
    summary="Get Current User's Profile"
)
async def read_current_user_me(
    current_user: Annotated[
        UserModel,
        Depends(get_current_active_user)
    ]
) -> UserRead:
    """
    Get all profile information for
    the currently authenticated user.
    """

    return current_user


@user_router.put(
    "/me",
    response_model=UserRead,
    summary="Update Current User's Profile"
)
async def update_current_user_me(
    user_update_in: UserUpdate,
    current_user: Annotated[UserModel, Depends(get_current_active_user)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> UserRead:
    """
    Update the profile information for
    the currently authenticated user.
    """

    try:
        updated_user = await user_service.update_user_profile(
            current_user=current_user,
            user_in=user_update_in
        )

        return updated_user

    except AppException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.detail
        )


@user_router.post(
    "/me/change-password",
    response_model=UserRead,
    summary="Change Current User's Password"
)
async def change_current_user_password(
    password_in: UserUpdatePassword,
    current_user: Annotated[
        UserModel,
        Depends(get_current_active_user)
    ],
    user_service: Annotated[
        UserService,
        Depends(get_user_service)
    ],
) -> UserRead:
    """
    Change the password for the
    currently authenticated user.
    """

    try:
        updated_user = await user_service.change_password(
            current_user=current_user,
            password_in=password_in
        )

        return updated_user

    except AppException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.detail
        )


@user_router.get(
    "/commanders",
    response_model=List[UserRead],
    summary="List All Incident Commanders"
)
async def list_commanders(
    user_service: Annotated[
        UserService,
        Depends(get_user_service)
    ]
) -> List[UserRead]:
    """
    Get a list of all active users designated as Incident Commanders.
    This is useful for populating dropdowns in the frontend.
    """

    try:
        commanders = await user_service.get_commander_list()

        return commanders

    except AppException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.detail
        )


# ================
# Admin Endpoints
# ================


@admin_router.get(
    "/",
    response_model=List[UserRead],
    summary="List All Users (Admin)"
)
async def read_all_users_admin(
    user_service: Annotated[
        UserService,
        Depends(get_user_service)
    ],
    skip: int = 0,
    limit: int = 100
) -> List[UserRead]:
    """
    Get a list of all users with pagination.
    Requires superuser privileges.
    """

    try:
        users = await user_service.get_users_list(
            skip=skip,
            limit=limit
        )

        return users

    except AppException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.detail
        )


@admin_router.get(
    "/{user_id_to_get}",
    response_model=UserRead,
    summary="Get User by ID (Admin)"
)
async def read_user_by_id_admin(
    user_id_to_get: UUID,
    user_service: Annotated[
        UserService,
        Depends(get_user_service)
    ]
) -> UserRead:
    """
    Get a specific user by their ID.
    Requires superuser privileges.
    """

    try:
        user = await user_service.get_user_by_id(
            user_id=user_id_to_get
        )
        return user

    except AppException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.detail
        )


@admin_router.delete(
    "/{user_id_to_delete}/soft-delete",
    response_model=UserRead,
    summary="Soft Delete User (Admin)"
)
async def soft_delete_user_by_admin(
    user_id_to_delete: UUID,
    performing_admin_user: Annotated[
        UserModel,
        Depends(
            get_current_active_superuser
        )
    ],
    user_service: Annotated[
        UserService,
        Depends(get_user_service)
    ]
):
    """
    Soft delete a user. Requires superuser privileges.
    This action is irreversible through the API.
    Cannot delete active incident commanders.
    """

    try:
        deleted_user = await user_service.soft_delete_user(
            user_to_delete_id=user_id_to_delete,
            performing_user=performing_admin_user
        )

        return deleted_user

    except AppException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.detail
        )

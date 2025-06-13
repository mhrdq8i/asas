from typing import Annotated, List
import uuid

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    BackgroundTasks
)

from src.api.v1.schemas.user_schemas import (
    UserCreate,
    UserRead,
    UserUpdate
)
from src.core.email_utils import send_email_verification
from src.dependencies.service_deps import get_user_service
from src.dependencies.auth_deps import (
    get_current_active_user,
    get_current_active_superuser
)
from src.services.user_service import UserService
from src.models.user import User as UserModel
from src.exceptions.base_exceptions import AppException
from src.exceptions.common_exceptions import (
    InvalidOperationException
)


user_router = APIRouter(
    prefix="/users",
)


admin_router = APIRouter(
    prefix="/admin",
    # Protect all routes in this router
    dependencies=[
        Depends(
            get_current_active_superuser
        )
    ]
)


@user_router.post(
    "/",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register New User",
    description=(
        "Create a new user account. "
        "Username and email must be unique."
    )
)
async def register_new_user(
    user_in: UserCreate,
    user_service: Annotated[
        UserService,
        Depends(get_user_service)
    ],
    background_tasks: BackgroundTasks
):
    """
    Create a new user.
    - **username**: Must be unique.
    - **email**: Must be unique.
    - **password**: Will be hashed.
    - An email verification link will be sent.
    """
    try:
        created_user = await user_service.register_user(
            user_in=user_in
        )

        # Attempt to send verification
        # email in the background
        try:
            (
                updated_user_for_email,
                verification_token,
                _
            ) = await user_service.prepare_email_verification_data(
                current_user=created_user
            )
            if verification_token:
                background_tasks.add_task(
                    send_email_verification,
                    email_to=updated_user_for_email.email,
                    username=updated_user_for_email.username,
                    verification_token=verification_token
                )
        except InvalidOperationException as e_verify:
            # Log this internally,
            # but don't fail the
            # user registration
            print(
                "Could not schedule email verification "
                f"for new user {created_user.email}: "
                f"{e_verify.detail}"
            )
        except Exception as e_task:
            print(
                "Error preparing email verification task "
                f"for {created_user.email}: {e_task}"
            )

        return created_user

    except AppException as e:
        # Catch all custom application
        # exceptions and convert
        # them to HTTPException
        raise HTTPException(
            status_code=e.status_code,
            detail=e.detail
        )

    except Exception as e:
        # Catch any unexpected errors
        print(
            "Unexpected error during "
            f"user registration: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "An unexpected error occurred "
                "during user registration."
            )
        )


@user_router.get(
    "/me",
    response_model=UserRead,
    summary="Get Current User",
    description=(
        "Get all information about "
        "the currently authenticated user."
    )
)
async def read_current_user_me(
    current_user: Annotated[
        UserModel,
        Depends(get_current_active_user)
    ]
):
    return current_user


@user_router.put(
    "/me",
    response_model=UserRead,
    summary="Update Current User Profile",
    description=(
        "Update the profile information for "
        "the currently authenticated user."
    )
)
async def update_current_user_me(
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


@user_router.get(
    "/commanders",
    response_model=List[UserRead]
)
async def list_commanders(
    user_service: Annotated[
        UserService,
        Depends(get_user_service)
    ]
):
    """
    Get a list of all active users designated as Incident Commanders.
    This is useful for populating dropdowns in the frontend.
    """
    commanders = await user_service.get_commander_list()

    return commanders


# --- Admin Endpoints ---

@admin_router.get(
    "/",
    response_model=List[UserRead],
    summary="List Users (Admin)",
    description=(
        "Get a list of all users. "
        "Requires superuser privileges."
    )
)
async def read_all_users_admin(
    user_service: Annotated[
        UserService,
        Depends(get_user_service)
    ],
    skip: int = 0,
    limit: int = 100
):
    users = await user_service.get_users_list(
        skip=skip,
        limit=limit
    )
    return users


@admin_router.get(
    "/{user_id_to_get}",
    response_model=UserRead,
    summary="Get User by ID (Admin)",
    description=(
        "Get a specific user by their ID. "
        "Requires superuser privileges."
    )
)
async def read_user_by_id_admin(
    user_id_to_get: uuid.UUID,
    user_service: Annotated[
        UserService,
        Depends(get_user_service)
    ]
):
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
    summary="Soft Delete User (Admin)",
    description=(
        "Soft delete a user. "
        "Requires superuser privileges. "
        "Cannot delete active incident commanders."
    )
)
async def soft_delete_user_by_admin(
    user_id_to_delete: uuid.UUID,
    performing_admin_user: Annotated[
        UserModel,
        Depends(get_current_active_superuser)
    ],
    user_service: Annotated[
        UserService,
        Depends(get_user_service)
    ]
):
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

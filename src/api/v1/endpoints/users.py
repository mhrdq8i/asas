from typing import Annotated, List
import uuid

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks

# Import schemas, dependencies, services, models, and exceptions
from src.api.v1.schemas.user_schemas import UserCreate, UserRead, UserUpdate
from src.dependencies.service_deps import get_user_service
from src.dependencies.api_auth_deps import get_current_active_user, get_current_active_superuser
from src.services.user_service import UserService
from src.models.user import User as UserModel
from src.exceptions.base_exceptions import AppException
from src.exceptions.common_exceptions import DuplicateResourceException, InvalidOperationException
from src.exceptions.user_exceptions import UserNotFoundException, InsufficientPermissionsException
from src.core.email_utils import send_email_verification_email

router = APIRouter(
    prefix="/users",  # Prefix for all routes in this router
    tags=["Users"]    # Tag for API documentation
)


@router.post(
    "/",  # Path will be /users/
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register New User",
    description="Create a new user account. Username and email must be unique. An email verification link will be sent."
)
async def register_new_user(
    user_in: UserCreate,
    user_service: Annotated[UserService, Depends(get_user_service)],
    background_tasks: BackgroundTasks
):
    """
    Create a new user.
    - **username**: Must be unique.
    - **email**: Must be unique.
    - **password**: Will be hashed.
    - An email verification link will be (conceptually) sent.
    """
    try:
        created_user = await user_service.register_user(user_in=user_in)

        # After successful registration, prepare and send verification email
        try:
            # The prepare_email_verification_data service method creates the token
            # and updates the user (e.g., stores token hash).
            # It returns the user object and the raw token.
            updated_user_for_email, verification_token, _ = await user_service.prepare_email_verification_data(
                current_user=created_user  # Pass the newly created user
            )
            if verification_token:
                background_tasks.add_task(
                    send_email_verification_email,
                    email_to=updated_user_for_email.email,
                    username=updated_user_for_email.username,
                    verification_token=verification_token
                )
                print(
                    f"Email verification task added to background for new user: {updated_user_for_email.email}")
            else:
                # This case should ideally not happen if prepare_email_verification_data works as expected
                print(
                    f"WARNING: Verification token was not generated for new user: {created_user.email}")

        except InvalidOperationException as e_verify:
            # e.g., if user is somehow already verified or inactive immediately after creation (unlikely)
            print(
                f"Could not schedule email verification for new user {created_user.email}: {e_verify.detail}")
        except Exception as e_task:
            print(
                f"Error preparing or adding email verification task for {created_user.email}: {e_task}")

        return created_user

    except DuplicateResourceException as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,  # 409 is more appropriate for duplicates
            detail=e.detail,
        )
    except AppException as e:  # Catch other custom app exceptions from service
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:  # Catch any unexpected errors
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
async def read_current_user_me(  # Renamed for clarity
    current_user: Annotated[UserModel, Depends(get_current_active_user)]
):
    """
    Get current logged-in user's information.
    """
    return current_user


@router.put(
    "/me",
    response_model=UserRead,
    summary="Update Current User Profile",
    description="Update the profile information for the currently authenticated user."
)
async def update_current_user_me(  # Renamed for clarity
    user_update_in: UserUpdate,
    current_user: Annotated[UserModel, Depends(get_current_active_user)],
    user_service: Annotated[UserService, Depends(get_user_service)],
):
    """
    Update current logged-in user's profile information.
    Password updates should be handled by a separate endpoint.
    """
    try:
        updated_user = await user_service.update_user_profile(
            current_user=current_user, user_in=user_update_in
        )
        return updated_user
    except DuplicateResourceException as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=e.detail)
    except UserNotFoundException as e:
        # This specific exception case is unlikely here because get_current_active_user
        # would have already failed if the user didn't exist.
        # However, keeping it for robustness in case the user is deleted between token issuance and this call.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=e.detail)
    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        print(f"Unexpected error during user profile update: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while updating the profile.",
        )

# --- Admin Endpoints ---


@router.get(
    "/",  # Path will be /users/ (due to router prefix)
    response_model=List[UserRead],
    summary="List Users (Admin)",
    description="Get a list of all users. Requires superuser privileges.",
    dependencies=[Depends(get_current_active_superuser)]
)
async def read_all_users_admin(  # Renamed for clarity
    skip: int = 0,
    limit: int = 100,
    user_service: Annotated[UserService, Depends(get_user_service)]
):
    """
    Retrieve a list of users. Accessible only by superusers.
    """
    users = await user_service.get_users_list(skip=skip, limit=limit)
    return users


@router.get(
    "/{user_id_to_get}",  # Path will be /users/{user_id_to_get}
    response_model=UserRead,
    summary="Get User by ID (Admin)",
    description="Get a specific user by their ID. Requires superuser privileges.",
    dependencies=[Depends(get_current_active_superuser)]
)
async def read_user_by_id_admin(  # Renamed parameter to avoid conflict
    user_id_to_get: uuid.UUID,
    user_service: Annotated[UserService, Depends(get_user_service)]
):
    """
    Retrieve a specific user by ID. Accessible only by superusers.
    """
    try:
        user = await user_service.get_user_by_id(user_id=user_id_to_get)
        return user
    except UserNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=e.detail)
    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.delete(
    "/{user_id_to_delete}/soft-delete",
    response_model=UserRead,
    summary="Soft Delete User (Admin)",
    description="Soft delete a user. Requires superuser privileges. Cannot delete active incident commanders.",
    dependencies=[Depends(get_current_active_superuser)]
)
async def soft_delete_user_by_admin(
    user_id_to_delete: uuid.UUID,
    # The admin performing the action, obtained from the dependency
    performing_admin_user: Annotated[UserModel, Depends(get_current_active_superuser)],
    user_service: Annotated[UserService, Depends(get_user_service)]
):
    """
    Soft delete a user by an admin.
    The 'performing_admin_user' is the authenticated superuser.
    """
    try:
        deleted_user = await user_service.soft_delete_user(
            user_to_delete_id=user_id_to_delete, performing_user=performing_admin_user
        )
        return deleted_user
    except UserNotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=e.detail)
    except InvalidOperationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=e.detail)
    except InsufficientPermissionsException as e:
        # This should ideally be caught by the dependency, but added for completeness
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=e.detail)
    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        print(f"Unexpected error during admin soft delete user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during soft delete operation.",
        )

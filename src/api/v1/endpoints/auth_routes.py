from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    BackgroundTasks,
    Request
)
from fastapi.security import (
    OAuth2PasswordRequestForm
)

from src.core import security
from src.services.user_service import UserService
from src.api.v1.schemas.auth_schemas import (
    Token,
    PasswordResetRequest,
    PasswordResetConfirm,
    PasswordResetConfirmWithToken,
    Msg,
    EmailVerifyTokenSchema
)
from src.dependencies.service_deps import (
    get_user_service
)
from src.dependencies.auth_deps import (
    get_current_active_user
)
from src.exceptions.base_exceptions import AppException
from src.exceptions.user_exceptions import (
    AuthenticationFailedException,
    UserNotFoundException,
)
from src.models.user import User as UserModel
from src.core.email_utils import (
    send_password_reset_email,
    send_email_verification
)

router = APIRouter(
    prefix="/auth",
    tags=["V1 - Authentication"]
)


@router.post(
    "/token",
    response_model=Token
)
async def login_for_access_token(
    request: Request,
    form_data: Annotated[
        OAuth2PasswordRequestForm,
        Depends()
    ],
    user_service: Annotated[
        UserService,
        Depends(get_user_service)
    ]
):
    """
    OAuth2 compatible token login,
    get an access token for future requests.
    """
    client_ip = request.client.host if request.client else None
    try:
        user = await user_service.authenticate_user(
            username=form_data.username,
            password=form_data.password,
            client_ip=client_ip
        )
        access_token = security.create_access_token(
            subject=user.username
        )

        return {
            "access_token": access_token,
            "token_type": "bearer"
        }

    except AuthenticationFailedException as e:
        # Special handling for login to
        # include the WWW-Authenticate header
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.detail,
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )

    except AppException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.detail
        )


@router.post(
    "/password-recovery",
    response_model=Msg,
    status_code=status.HTTP_200_OK
)
async def password_recovery(
    email_in: PasswordResetRequest,
    user_service: Annotated[
        UserService,
        Depends(get_user_service)
    ],
    background_tasks: BackgroundTasks
):
    """
    Request a password recovery email.
    """
    try:
        (
            user,
            reset_token,
            msg_to_client
        ) = await user_service.prepare_password_reset_data(
            email_in=email_in
        )
        if user and reset_token:
            background_tasks.add_task(
                send_password_reset_email,
                email_to=user.email,
                username=user.username,
                reset_token=reset_token
            )
        return Msg(message=msg_to_client)

    except AppException as e:
        # For security, always return a
        # generic success message for this endpoint
        # to prevent email enumeration.
        # The actual error can be logged internally.
        print(
            f"Error during password recovery request: {e.detail}"
        )
        return Msg(
            message=(
                "If an account with this email exists, "
                "a password reset link has been sent."
            )
        )


@router.post(
    "/reset-password",
    response_model=Msg
)
async def reset_password(
    reset_data: PasswordResetConfirmWithToken,
    user_service: Annotated[
        UserService,
        Depends(get_user_service)
    ]
):
    """
    Reset password using a
    token and new password.
    """
    try:
        new_password_schema = PasswordResetConfirm(
            new_password=reset_data.new_password
        )
        await user_service.confirm_password_reset(
            token_in=reset_data.token,
            new_password_in=new_password_schema
        )
        return Msg(
            message=(
                "Your password has been "
                "reset successfully."
            )
        )
    except AppException as e:
        # To prevent user enumeration,
        # we mask UserNotFoundException.
        if isinstance(
            e, UserNotFoundException
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Invalid or expired "
                    "password reset token."
                )
            )
        raise HTTPException(
            status_code=e.status_code,
            detail=e.detail
        )


@router.post(
    "/email-verification",
    response_model=Msg,
    status_code=status.HTTP_200_OK
)
async def email_verification(
    current_user: Annotated[
        UserModel,
        Depends(get_current_active_user)
    ],
    user_service: Annotated[
        UserService,
        Depends(get_user_service)
    ],
    background_tasks: BackgroundTasks
):
    """
    Requests a new email verification
    token for the current user.
    """
    try:
        (
            user,
            verification_token,
            msg_to_client
        ) = await user_service.prepare_email_verification_data(
            current_user=current_user
        )
        if user and verification_token:
            background_tasks.add_task(
                send_email_verification,
                email_to=user.email,
                username=user.username,
                verification_token=verification_token
            )
        return Msg(
            message=msg_to_client
        )

    except AppException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.detail
        )


@router.post(
    "/verify-email",
    response_model=Msg
)
async def verify_email(
    token_data: EmailVerifyTokenSchema,
    user_service: Annotated[
        UserService,
        Depends(get_user_service)
    ]
):
    """
    Verify user's email address
    using the provided token.
    """
    try:
        await user_service.confirm_email_verification(
            token_in=token_data.token
        )
        return Msg(
            message=(
                "Your email address has been "
                "successfully verified."
            )
        )
    except AppException as e:
        # To prevent user enumeration,
        # we mask UserNotFoundException.
        if isinstance(
            e,
            UserNotFoundException
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Invalid or expired "
                    "email verification token."
                )
            )
        raise HTTPException(
            status_code=e.status_code,
            detail=e.detail
        )

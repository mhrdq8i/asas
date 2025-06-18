from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Request,
)
from fastapi.security import (
    OAuth2PasswordRequestForm
)

from src.core import security
from src.services.user_service import UserService
from src.api.v1.schemas.auth_schemas import (
    Token,
    PasswordResetRequest,
    PasswordResetConfirmWithToken,
    Msg,
    EmailVerifyTokenSchema,
)
from src.dependencies.service_deps import get_user_service
from src.dependencies.auth_deps import get_current_active_user
from src.exceptions.base_exceptions import AppException
from src.models.user import User as UserModel


router = APIRouter(
    prefix="/auth"
)


@router.post("/token", response_model=Token)
async def login_for_access_token(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    user_service: Annotated[UserService, Depends(get_user_service)],
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
        access_token = security.create_access_token(subject=user.username)

        return {
            "access_token": access_token,
            "token_type": "bearer"
        }

    except AppException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.detail,
            headers={
                "WWW-Authenticate": "Bearer"
            } if e.status_code == 401 else None,
        )


@router.post(
    "/password-recovery",
    response_model=Msg,
    status_code=status.HTTP_200_OK
)
async def password_recovery(
    email_in: PasswordResetRequest,
    user_service: Annotated[UserService, Depends(get_user_service)],
):
    """
    Request a password recovery email.
    The service queues the email task.
    """

    try:
        message = await user_service.prepare_password_reset_data(
            email_in=email_in
        )

        return Msg(message=message)

    except Exception as e:
        print(f"Error during password recovery request: {e}")
        return Msg(
            message=(
                "If an account with this email exists, "
                "a password reset link has been sent."
            )
        )


@router.post("/reset-password", response_model=Msg)
async def reset_password(
    reset_data: PasswordResetConfirmWithToken,
    user_service: Annotated[UserService, Depends(get_user_service)],
):
    """
    Reset password using a token and new
    password provided in the request body.
    """

    try:
        await user_service.confirm_password_reset(
            token_in=reset_data.token,
            new_password_in=reset_data
        )

        return Msg(
            message="Your password has been reset successfully."
        )

    except AppException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.detail
        )


@router.post(
    "/email-verification",
    response_model=Msg,
    status_code=status.HTTP_200_OK
)
async def request_new_email_verification(
    current_user: Annotated[UserModel, Depends(get_current_active_user)],
    user_service: Annotated[UserService, Depends(get_user_service)],
):
    """
    Requests a new email verification token for the current user.
    The task is handled in the background by Celery.
    """

    try:
        message = await user_service.request_new_verification_email(
            current_user=current_user
        )

        return Msg(message=message)

    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post("/verify-email", response_model=Msg)
async def verify_email(
    token_data: EmailVerifyTokenSchema,
    user_service: Annotated[UserService, Depends(get_user_service)],
):
    """
    Verify a user's email address using the provided token.
    Upon successful verification,
    a welcome email task is queued by the service.
    """
    try:
        await user_service.confirm_email_verification(
            token_in=token_data.token
        )

        return Msg(
            message="Your email address has been successfully verified."
        )

    except AppException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.detail
        )

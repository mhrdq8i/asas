from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    BackgroundTasks,
    Request
)
from fastapi.security import OAuth2PasswordRequestForm

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
from src.dependencies.service_deps import get_user_service
from src.dependencies.api_auth_deps import get_current_active_user
from src.exceptions.base_exceptions import (
    AppException
)
from src.exceptions.common_exceptions import (
    InvalidInputException,
    InvalidOperationException,
)
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
    prefix="/auth"
)


@router.post("/token", response_model=Token, summary="Login for Access Token")
async def login_for_access_token(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    user_service: Annotated[UserService, Depends(get_user_service)]
):
    """
    OAuth2 compatible token login, get an access token for future requests.
    Pass username and password as form data.
    Email must be verified to login.
    """
    client_ip = request.client.host if request.client else None
    try:
        user = await user_service.authenticate_user(
            username=form_data.username,
            password=form_data.password,
            client_ip=client_ip
        )
    except AuthenticationFailedException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.detail,
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = security.create_access_token(subject=user.username)
    return {"access_token": access_token, "token_type": "bearer"}


@router.post(
    "/request-password-recovery",
    response_model=Msg,
    status_code=status.HTTP_200_OK,
    summary="Request Password Recovery"
)
async def request_password_recovery_endpoint(
    email_in: PasswordResetRequest,
    user_service: Annotated[UserService, Depends(get_user_service)],
    background_tasks: BackgroundTasks
):
    """
    Request a password recovery email.
    An email will be sent to the user with a reset token if the user
    exists and is active.
    """
    try:
        user, reset_token, msg_to_client = await user_service.prepare_password_reset_data(
            email_in=email_in
        )

        if user and reset_token:
            background_tasks.add_task(
                send_password_reset_email,
                email_to=user.email,
                username=user.username,
                reset_token=reset_token
            )
            # Server-side log for successful token generation and email task scheduling
            print(f"Password reset email task added for {user.email}")

        return Msg(message=msg_to_client)

    except AppException as e:
        # This handles specific AppExceptions if prepare_password_reset_data raises them
        # beyond the controlled (None, None, message) return for user not found/inactive.
        # For security, it's often better to return a generic success-like message
        # for password recovery requests to prevent email enumeration.
        # The service layer is designed to return a generic message for UserNotFound/Inactive.
        # So, this HTTPException might be for other unexpected AppExceptions.
        if isinstance(e, UserNotFoundException):
            # Log for server admin, but return generic message to client
            print(
                f"Info: Password recovery for non-existent/inactive user: {email_in.email}")
            return Msg(
                message="If an account with this email exists and is active, "
                        "a password reset link has been sent."
            )
        # For other AppExceptions, re-raise as HTTPException
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        # Catch-all for unexpected errors
        print(
            f"Unexpected error in password recovery for {email_in.email}: {e}")
        # Return a generic message to avoid leaking information
        return Msg(
            message="An error occurred. If your email is registered, "
                    "you might receive a password reset link."
        )


@router.post("/reset-password", response_model=Msg, summary="Reset Password")
async def reset_password_endpoint(
    reset_data: PasswordResetConfirmWithToken,
    user_service: Annotated[UserService, Depends(get_user_service)]
):
    """
    Reset password using a token and new password provided in the request body.
    """
    try:
        # The service method confirm_password_reset expects new_password_data
        # (PasswordResetConfirm) and token_in separately.
        new_password_schema = PasswordResetConfirm(
            new_password=reset_data.new_password
        )
        await user_service.confirm_password_reset(
            token_in=reset_data.token, new_password_in=new_password_schema
        )
        return Msg(message="Your password has been reset successfully.")
    except InvalidInputException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=e.detail
        )
    except UserNotFoundException:
        # Masking UserNotFound to a more generic invalid token message
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset token."
        )
    except AuthenticationFailedException as e:
        # If token verification fails within the service for other reasons
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=e.detail
        )
    except AppException as e:  # Catch other specific app exceptions
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post(
    "/request-email-verification",
    response_model=Msg,
    status_code=status.HTTP_200_OK,
    summary="Request Email Verification Token"
)
async def request_email_verification_token_endpoint(
    current_user: Annotated[UserModel, Depends(get_current_active_user)],
    user_service: Annotated[UserService, Depends(get_user_service)],
    background_tasks: BackgroundTasks
):
    """
    Requests a new email verification token for the currently authenticated user.
    Sends an email with the verification link.
    """
    try:
        user, verification_token, msg_to_client = (
            await user_service.prepare_email_verification_data(
                current_user=current_user
            )
        )

        if user and verification_token:
            background_tasks.add_task(
                send_email_verification,
                email_to=user.email,
                username=user.username,
                verification_token=verification_token
            )
            # Server-side log
            print(f"Email verification task added for {user.email}")

        return Msg(message=msg_to_client)
    except InvalidOperationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=e.detail
        )
    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.post("/verify-email", response_model=Msg, summary="Verify Email Address")
async def verify_email_endpoint(
    token_data: EmailVerifyTokenSchema,
    user_service: Annotated[UserService, Depends(get_user_service)]
):
    """
    Verify user's email address using the provided token in the request body.
    """
    try:
        await user_service.confirm_email_verification(token_in=token_data.token)
        return Msg(message="Your email address has been successfully verified.")
    except InvalidInputException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=e.detail
        )
    except UserNotFoundException:
        # Masking UserNotFound to a more generic invalid token message
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired email verification token."
        )
    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)

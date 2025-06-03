from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)
from fastapi.security import (
    OAuth2PasswordRequestForm
)

from src.core import security
from src.models.user import User as UserModel
from src.services.user_service import UserService
from src.api.v1.schemas.auth_schemas import (
    Token,
    PasswordResetRequest,
    PasswordResetConfirm,
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
    InvalidOperationException
)
from src.exceptions.user_exceptions import (
    AuthenticationFailedException,
    UserNotFoundException,
)


router = APIRouter()


@router.post(
    "/token",
    response_model=Token,
    summary="Login for Access Token"
)
async def login_for_access_token(
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
    Pass username and password as form data.
    """
    try:
        user = await user_service.authenticate_user(
            username=form_data.username,
            password=form_data.password
        )

    except AuthenticationFailedException as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.detail,
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )

    # This check is technically redundant if
    # authenticate_user always raises on failure
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )

    access_token = security.create_access_token(
        # Using username as the token subject
        subject=user.username
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.post(
    "/password-recovery",
    response_model=Msg,
    status_code=status.HTTP_200_OK,
    summary="Request Password Recovery"
)
async def request_password_recovery(
    email_in: PasswordResetRequest,
    user_service: Annotated[
        UserService,
        Depends(get_user_service)
    ],
    # If email sending is a background task
    # background_tasks: BackgroundTasks
):
    """
    Request a password recovery email.
    An email will be (conceptually) sent
    to the user with a reset token.
    """
    try:
        # The service method is designed to
        # not reveal if an email exists for security.
        # It will "send" an email if the user exists and is active.
        response_message = await user_service.request_password_reset(
            email_in=email_in
        )

        # In a real app, the email sending would be a background task.
        # background_tasks.add_task(
        # user_service.send_password_reset_email,
        # email_in.email, reset_token
        # )

        return Msg(
            message=response_message
        )

    except UserNotFoundException:
        # Even if service raises,
        # we return a generic message to
        # prevent email enumeration
        return Msg(
            message="If your email is registered and active,\
                you will receive a password reset link shortly."
        )

    # e.g. user is inactive
    except InvalidOperationException:
        # Again, generic message to prevent info leakage
        return Msg(
            message="If your email is registered and active,\
                you will receive a password reset link shortly."
        )
    # Catch other app-specific
    # errors from service
    except AppException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.detail
        )


@router.post(
    "/reset-password",
    response_model=Msg,
    summary="Reset Password"
)
async def reset_password(
    # Token can be sent as a
    # query parameter or in the body
    token: str,
    new_password_data: PasswordResetConfirm,
    user_service: Annotated[
        UserService,
        Depends(get_user_service)
    ]
):
    """
    Reset password using a token received via email.
    The token should be provided as a query parameter
    or in the request body.
    For this example,
    we expect it as a query parameter `token`.
    """

    try:
        await user_service.confirm_password_reset(
            token_in=token,
            new_password_in=new_password_data
        )
        return Msg(
            message="Your password has been reset successfully."
        )

    except InvalidInputException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.detail
        )

    # Should ideally not happen if token is valid
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


@router.post(
    "/email-verification",
    response_model=Msg,
    status_code=status.HTTP_200_OK,
    summary="Request Email Verification Token"
)
async def request_email_verification_token_endpoint(
    current_user: Annotated[
        UserModel,
        Depends(
            get_current_active_user
        )
    ],
    user_service: Annotated[
        UserService,
        Depends(
            get_user_service
        )
    ],
    # background_tasks: BackgroundTasks
):
    """
    Requests a new email verification token
    for the currently authenticated user.
    (Conceptually) sends an email with
    the verification link.
    """
    try:
        response_message = await user_service.request_email_verification_token(
            current_user=current_user
        )
        # background_tasks.add_task(
        # user_service.send_verification_email,
        # current_user.email, verification_token
        # )

        return Msg(
            message=response_message
        )

    # e.g., email already verified or user inactive
    except InvalidOperationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.detail
        )

    except AppException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.detail
        )


# Or GET /verify-email?token=...
@router.post(
    "/verify-email",
    response_model=Msg,
    summary="Verify Email Address"
)
async def verify_email_endpoint(
    # Assuming token is sent in request body for POST
    token_data: EmailVerifyTokenSchema,
    user_service: Annotated[
        UserService,
        Depends(
            get_user_service
        )
    ]
):
    """
    Verify user's email address using the provided token.
    If using GET, token would be a query parameter:
    token: str = Query(...)
    """
    try:
        await user_service.confirm_email_verification(
            token_in=token_data.token
        )

        return Msg(
            message="Your email address has been successfully verified."
        )

    # e.g. token invalid, expired, or already used
    except InvalidInputException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.detail
        )

    # Should ideally not happen if token is valid
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

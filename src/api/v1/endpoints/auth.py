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
from src.services.user_service import (
    UserService
)
from src.api.v1.schemas.auth_schemas import Token
from src.dependencies.service_deps import (
    get_user_service
)
from src.exceptions import (
    AuthenticationFailedException
)

router = APIRouter()


@router.post(
    "/token",
    response_model=Token
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

    # Should not happen if UserService.
    # authenticate_user raises on failure
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )

    # Using username is common for 'sub' claim.
    # If using ID, ensure it's a string.
    access_token = security.create_access_token(
        subject=user.username  # Or str(user.id)
    )
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

# You might add other auth-related endpoints here later, e.g.,
# - /password-recovery
# - /reset-password
# - /verify-email

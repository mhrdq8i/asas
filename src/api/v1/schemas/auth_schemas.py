from pydantic import (
    BaseModel,
    EmailStr,
    Field as PydanticField
)


class Token(BaseModel):
    """
    Schema for the access token response.
    """
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """
    Schema for the data (payload) encoded within the JWT.
    'sub' (subject) typically holds the username or user ID.
    """
    sub: str | None = None
    # To differentiate token types (
    # e.g.,
    # access,
    # refresh,
    # password_reset,
    # email_verify
    # )
    type: str | None = None
    # Expiration time (timestamp),
    # usually handled by JWT library
    exp: int | None = None


class PasswordResetRequest(BaseModel):
    """
    Schema for requesting a password reset.
    """
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """
    Schema for confirming a password
    reset with a new password.
    The token will be passed as a path
    or query parameter in the endpoint.
    """
    new_password: str = PydanticField(
        min_length=8,
        description="The new password"
    )


class PasswordResetConfirmWithToken(PasswordResetConfirm):
    """
    Schema for confirming a password reset,
    including the token in the body.
    This can be an alternative if you prefer to
    send the token in the request body.
    """
    token: str = PydanticField(
        description="The password reset token received by the user"
    )


class EmailVerificationRequest(BaseModel):
    """
    Schema for requesting an email verification link.
    Typically, this would be for the currently logged-in user,
    so no email field is needed here.
    The endpoint would get the user from the auth token.
    """
    pass  # No fields needed, user is identified by auth token


class EmailVerifyTokenSchema(BaseModel):
    """
    Schema for verifying an email using a token.
    The token is usually passed as a query parameter.
    """
    token: str = PydanticField(
        description="The email verification token"
    )


class Msg(BaseModel):
    """
    Generic message schema for simple responses.
    """
    message: str

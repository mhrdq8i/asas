from logging import getLogger

from fastapi import (
    FastAPI,
    Request,
    status
)
from fastapi.responses import (
    JSONResponse
)
from fastapi.exceptions import (
    RequestValidationError
)
from pydantic import ValidationError

from src.exceptions.base_exceptions import (
    AppException,
)
from src.exceptions.user_exceptions import (
    AuthenticationFailedException,
    UserNotFoundException
)

logger = getLogger(__name__)


async def app_exception_handler(
    request: Request,
    exc: AppException
):
    """
    Handles any custom application exception
    that inherits from AppException.
    """

    logger.warning(
        f"Application exception caught: {exc.detail} "
        f"for request {request.url.path} ",

        extra={
            "status_code": exc.status_code,
            "exception_type": type(exc).__name__
        }
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail
        }
    )


async def user_not_found_exception_handler(
    request: Request,
    exc: UserNotFoundException
):
    """
    Handles the specific UserNotFoundException to provide a richer response.
    """

    logger.warning(
        "UserNotFoundException caught for identifier "
        f"'{exc.identifier}' on path '{request.url.path}'"
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "resource_name": "User",
            "identifier": exc.identifier
        }
    )


async def request_validation_exception_handler(
    request: Request,
    exc: RequestValidationError
):
    """
    Handles FastAPI's own request validation errors.
    """

    logger.warning(
        f"RequestValidationError caught for path '{request.url.path}'",
        extra={"errors": exc.errors()}
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation Error",
            "errors": exc.errors()
        }
    )


async def pydantic_validation_error_handler(
    request: Request,
    exc: ValidationError
):
    """
    Handles Pydantic ValidationErrors that
    might be raised manually in the code.
    """

    logger.warning(
        "Pydantic ValidationError (manual) caught "
        f"for path '{request.url.path}'",
        extra={"errors": exc.errors()}
    )

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "detail": "Data validation failed.",
            "errors": [err for err in exc.errors()]
        }
    )


async def generic_exception_handler(
    request: Request,
    exc: Exception
):
    """
    Handles any other unhandled Python exceptions.
    This is the last resort handler.
    """

    logger.error(
        f"Unhandled exception caught for request: {request.url.path}",
        exc_info=True
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An unexpected internal server error occurred."
        }
    )


def register_error_handlers(app: FastAPI):
    """
    Registers all custom and default exception
    handlers with the FastAPI application.
    """

    # Specific custom exceptions
    app.add_exception_handler(
        UserNotFoundException,
        user_not_found_exception_handler
    )

    # This handler can be removed if the
    # base app_exception_handler is sufficient
    app.add_exception_handler(
        AuthenticationFailedException,
        app_exception_handler
    )

    # Base custom app exception
    app.add_exception_handler(
        AppException,
        app_exception_handler
    )

    # Pydantic/FastAPI validation errors
    app.add_exception_handler(
        RequestValidationError,
        request_validation_exception_handler
    )

    app.add_exception_handler(
        ValidationError,
        pydantic_validation_error_handler
    )

    # Generic fallback handler (should be last)
    app.add_exception_handler(
        Exception,
        generic_exception_handler
    )

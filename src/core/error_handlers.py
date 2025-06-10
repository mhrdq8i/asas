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


async def app_exception_handler(
    request: Request,
    exc: AppException
):
    """
    Handles any custom application exception
    that inherits from AppException.
    """

    # Log the exception here if needed
    import logging
    logger = logging.getLogger(__name__)
    logger.error(
        f"AppException caught: {exc.detail}",
        exc_info=True
    )

    print(
        "AppException Handler: "
        f"{type(exc).__name__} "
        f"Detail: {exc.detail}, "
        f"Status Code: {exc.status_code}"
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


async def user_not_found_exception_handler(
    request: Request,
    exc: UserNotFoundException
):

    print(
        "UserNotFoundException "
        f"Handler: {exc.detail}"
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "resource_name": "User",
            "identifier": exc.identifier
        },
    )


async def request_validation_exception_handler(
    request: Request,
    exc: RequestValidationError
):
    """
    Handles FastAPI's own request validation errors
    (from Pydantic models in path/query/body).
    """

    errors = []
    for error in exc.errors():
        errors.append(
            {
                "loc": error["loc"],
                "msg": error["msg"],
                "type": error["type"],
            }
        )

    print(
        "RequestValidationError Handler: "
        f"Path={request.url.path}, "
        f" Errors: {errors}"
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation Error",
            "errors": errors
        },
    )


async def pydantic_validation_error_handler(
    request: Request,
    exc: ValidationError
):
    """
    Handles Pydantic ValidationErrors
    that might be raised manually in your code
    (e.g., when validating data outside of
    FastAPI's automatic request validation).
    """

    errors = []
    # exc.errors() is a list of dicts
    for error in exc.errors():
        errors.append(
            {
                # loc might not always be present
                "loc": error.get(
                    "loc", ["unknown"]
                ),
                "msg": error.get(
                    "msg", "Unknown validation error"
                ),
                "type": error.get(
                    "type", "validation_error"
                ),
            }
        )
    print(
        "Pydantic ValidationError Handler(manual): "
        f"Path={request.url.path}, "
        f"Errors: {errors}"
    )

    return JSONResponse(
        # Or 422 depending on context
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "detail": "Data validation failed.",
            "errors": errors
        }
    )


async def generic_exception_handler(
    request: Request,
    exc: Exception
):
    """
    Handles any other unhandled Python exceptions.
    This should be the last handler registered
    to catch all fallbacks.
    """
    print(
        "GenericExceptionHandler: "
        "An unhandled exception occurred: "
        f"{type(exc).__name__} - {str(exc)} "
        f" for request: {request.url.path}"
    )

    import traceback
    # FIX: Correctly import the logging module and get a logger instance.
    import logging
    logger = logging.getLogger(__name__)

    traceback.print_exc()
    # In production,
    # log exc_info = True
    # with your logger
    logger.error(
        "Unhandled exception:",
        exc_info=True
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An unexpected internal server "
            "error occurred. Please try again later."
        },
    )


def register_error_handlers(
        app: FastAPI
):
    """
    Registers all custom and default exception
    handlers with the FastAPI application.
    The order of specific handlers before more
    generic ones can be important if exceptions inherit.
    """

    # Specific custom exceptions
    # (if they need handling
    # different from AppException)
    app.add_exception_handler(
        UserNotFoundException,
        user_not_found_exception_handler
    )

    # Will be caught
    # by AppException
    # if not specified
    app.add_exception_handler(
        AuthenticationFailedException,
        app_exception_handler
    )

    # Base custom app exception
    # (catches all its children
    # if not handled more specifically)
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

    # Generic fallback handler
    # (should be last)
    app.add_exception_handler(
        Exception,
        generic_exception_handler
    )

    print(
        "Custom and default error handlers registered."
    )

from fastapi import status


class AppException(
    Exception
):
    """
    Base class for custom application exceptions.
    This allows for a general way to catch
    application-specific errors.
    """

    def __init__(
        self,
        detail: str | None = None,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    ):
        self.detail = detail or "An application error occurred."
        self.status_code = status_code

        super().__init__(self.detail)


class ConfigurationError(
    AppException
):
    """
    Raised for application configuration errors.
    """

    def __init__(
            self,
            detail: str = "Application configuration error"
    ):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

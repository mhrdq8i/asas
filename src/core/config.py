from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict
)
from pydantic import (
    PostgresDsn,
    model_validator,
    EmailStr,
    SecretStr
)
from typing import Any, Dict


class Settings(BaseSettings):
    """
    Application settings are managed
    by this class.
    Values MUST be provided via
    environment variables
    or a .env file for required fields.
    """

    # --- Application Metadata ---
    APP_NAME: str = "Incident Management System API"
    APP_VERSION: str = "0.1.0"
    DEBUG_MODE: bool = False
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8000
    LOG_LEVEL: str

    # --- Database Settings ---
    POSTGRES_SCHEME: str | None = None
    POSTGRES_USER: str | None = None
    POSTGRES_PASSWORD: SecretStr | None = None
    POSTGRES_SERVER: str | None = None
    POSTGRES_PORT: str | None = None
    POSTGRES_DB: str | None = None

    DATABASE_URL: PostgresDsn | str | None = None
    DATABASE_ECHO: bool

    # --- JWT Settings ---
    # This should ideally also be SecretStr
    # for consistency if handled by Pydantic
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int
    EMAIL_VERIFY_TOKEN_EXPIRE_MINUTES: int

    # --- Frontend URL ---
    FRONTEND_URL: str

    # --- Email Settings ---
    MAIL_SERVER: str
    MAIL_PORT: int
    MAIL_USERNAME: str | None = None
    # Defined as SecretStr
    MAIL_PASSWORD: SecretStr | None = None
    MAIL_FROM_EMAIL: EmailStr
    MAIL_FROM_NAME: str | None = None
    MAIL_USE_TLS: bool
    MAIL_USE_SSL: bool
    MAIL_TIMEOUT: int = 60

    # --- Notification Settings ---
    INCIDENT_NOTIFICATION_RECIPIENTS: str | None = None

    # --- Celery Settings ---
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str

    # --- Prometheus Settings ---
    PROMETHEUS_API_URL: str | None = None
    ALERT_CHECK_INTERVAL_SECONDS: int

    @model_validator(mode='before')
    @classmethod
    def assemble_database_url(
        cls,
        values: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Constructs DATABASE_URL if not provided,
        or validates it if provided.
        Ensures all necessary DB components are
        present if DATABASE_URL is to be constructed.
        """

        db_url_provided = values.get('DATABASE_URL')

        if db_url_provided and isinstance(
            db_url_provided,
            str
        ) and db_url_provided.strip():

            if "sqlite" in db_url_provided:
                values[
                    'DATABASE_URL'
                ] = db_url_provided

            elif db_url_provided.startswith(
                "postgresql://"
            ) or db_url_provided.startswith(
                "postgres://"
            ):

                values[
                    'DATABASE_URL'
                ] = db_url_provided.replace(
                    "postgresql://",
                    "postgresql+asyncpg://"
                ).replace(
                    "postgres://",
                    "postgresql+asyncpg://"
                )

            elif not db_url_provided.startswith(
                "postgresql+asyncpg://"
            ):

                error_msg = (
                    f"DATABASE_URL '{db_url_provided}' "
                    "for PostgreSQL must use "
                    "'postgresql+asyncpg://', "
                    "'postgresql://', or "
                    "'postgres://' scheme."
                )

                raise ValueError(error_msg)

            return values

        elif db_url_provided is not None:
            raise ValueError(
                "DATABASE_URL must be a "
                "non-empty string if provided, "
                f"got: '{db_url_provided}' "
                f"(type: {type(db_url_provided)})"
            )

        scheme = values.get('POSTGRES_SCHEME')
        user = values.get('POSTGRES_USER')

        # In 'before' mode validator,
        # password_from_env
        # is still a raw string or None
        password_from_env = values.get(
            'POSTGRES_PASSWORD'
        )
        server = values.get('POSTGRES_SERVER')
        port_str = values.get('POSTGRES_PORT')
        db_name = values.get('POSTGRES_DB')

        essential_db_parts = {
            "POSTGRES_SCHEME": scheme,
            "POSTGRES_USER": user,
            "POSTGRES_PASSWORD": password_from_env,
            "POSTGRES_SERVER": server,
            "POSTGRES_PORT": port_str,
            "POSTGRES_DB": db_name,
        }

        missing_db_params = [
            key for (
                key, value
            ) in essential_db_parts.items()
            if value is None or (
                isinstance(
                    value, str
                ) and not value.strip()
            )
        ]

        # If password_from_env was
        # a string but empty,
        # it's caught by
        # `not value.strip()`

        if missing_db_params:
            error_message = (
                "Cannot construct DATABASE_URL. "
                "DATABASE_URL is not set or is empty, "
                "and the following parameters required "
                "for its construction are "
                "missing or empty: "
                f"{', '.join(missing_db_params)}. "
                "Please provide either a full "
                "DATABASE_URL or all of these: "
                "POSTGRES_SCHEME, POSTGRES_USER, "
                "POSTGRES_PASSWORD, POSTGRES_SERVER, "
                "POSTGRES_PORT, POSTGRES_DB "
                "with non-empty values in the "
                "environment or .env file."
            )

            raise ValueError(error_message)

        # Should be true
        assert (
            scheme and
            user and
            password_from_env and
            server and
            port_str and
            db_name
        )

        try:
            port = int(port_str)

            # Use password_from_env
            # directly as it's the plain string here
            password_plain = str(password_from_env)

            constructed_url = (
                f"{scheme}://"
                f"{user}:{password_plain}@"
                f"{server}:{port}/"
                f"{db_name}"
            )

            if "sqlite" not in scheme:
                PostgresDsn(
                    constructed_url
                )  # Validate the constructed DSN

            values['DATABASE_URL'] = constructed_url

        except ValueError as e:
            original_error_msg = str(e)
            prefix = (
                "Error constructing "
                "DATABASE_URL from parts. "
            )
            current_detailed_error: str

            if "invalid port number" \
                in original_error_msg.lower() or \
               "invalid literal for int()" in \
                    original_error_msg.lower():

                current_detailed_error = (
                    f"POSTGRES_PORT ('{port_str}') "
                    "must be a valid integer."
                )

            else:

                msg_part1 = "Ensure all parts (USER, PASSWORD, SERVER, "
                msg_part2 = "PORT, DB, SCHEME) form a valid DSN. "
                msg_part3 = f"Original error: {original_error_msg}"

                current_detailed_error = (
                    msg_part1 + msg_part2 + msg_part3
                )

            raise ValueError(
                f"{prefix}{current_detailed_error}"
            )

        return values

    @model_validator(mode='before')
    @classmethod
    def validate_mail_credentials(
        cls,
        values: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validates that if MAIL_USERNAME
        is provided, MAIL_PASSWORD is
        also provided and non-empty.
        """

        mail_user = values.get(
            'MAIL_USERNAME'
        )

        # This is a raw string or None
        mail_pass_from_env = values.get(
            'MAIL_PASSWORD'
        )

        # If mail_user is provided (and not empty),
        # mail_pass_from_env must also be
        # provided (and not empty)
        if mail_user and (
                isinstance(
                    mail_user,
                    str
                ) and mail_user.strip()
        ):

            if not mail_pass_from_env or (
                    isinstance(
                        mail_pass_from_env,
                        str
                    ) and not mail_pass_from_env.strip()
            ):

                raise ValueError(
                    "If MAIL_USERNAME is provided and\
                         non-empty, MAIL_PASSWORD must also be "
                    "provided and non-empty in the .env file."
                )

        return values

    def get_notification_recipients(
        self
    ) -> list[str]:
        """
        Returns a list of notification
        recipient email addresses.
        """

        if not self.INCIDENT_NOTIFICATION_RECIPIENTS:
            return []

        return [
            email.strip(
            ) for email in
            self.INCIDENT_NOTIFICATION_RECIPIENTS.split(',')
        ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding='utf-8',
        extra='ignore'
    )


settings = Settings()

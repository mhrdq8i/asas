from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict
)
from pydantic import (
    PostgresDsn,
    model_validator
)
from typing import Any, Dict


class Settings(BaseSettings):
    """
    Application settings are managed by this class.
    Values MUST be provided via
    environment variables or a .env file.
    No default values are assumed in the
    class definition itself for most fields.
    """
    POSTGRES_SCHEME: str | None = None
    POSTGRES_USER: str | None = None
    POSTGRES_PASSWORD: str | None = None
    POSTGRES_SERVER: str | None = None
    POSTGRES_PORT: str | None = None
    POSTGRES_DB: str | None = None

    DATABASE_URL: PostgresDsn | str | None = None
    # Must be in .env or environment
    DATABASE_ECHO: bool

    # JWT settings - Must be in .env or environment
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    @model_validator(mode='before')
    @classmethod
    def assemble_and_validate_db_connection(
        cls,
        values: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Constructs DATABASE_URL if not provided,
        or validates it if provided.
        Ensures all necessary DB components are present
        if DATABASE_URL is to be constructed.
        """

        print(
            f"--------------------------------------------------\n\
DEBUG: Initial values received by validator: {values} \n\
--------------------------------------------------"
        )

        db_url_provided = values.get('DATABASE_URL')

        if db_url_provided and isinstance(
            db_url_provided,
            str
        ):
            # If DATABASE_URL is fully provided,
            # validate and normalize it
            if "sqlite" in db_url_provided:
                values['DATABASE_URL'] = db_url_provided  # Allow sqlite

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
                raise ValueError(
                    f"DATABASE_URL '{db_url_provided}' for PostgreSQL \
                        must use 'postgresql+asyncpg://', "
                    f"'postgresql://', or 'postgres://' scheme."
                )

            return values

        elif db_url_provided is not None and not isinstance(
                db_url_provided, str
        ):
            # If DATABASE_URL is provided but not a string
            # (e.g. set to null in some env config)
            raise ValueError(
                f"DATABASE_URL must be a string if provided,\
                      got: {type(db_url_provided)}"
            )

        # If DATABASE_URL is not provided
        # (i.e., db_url_provided is None),
        # construct it from parts
        # All parts now MUST be present in
        # 'values' (from .env or environment)
        scheme = values.get('POSTGRES_SCHEME')
        user = values.get('POSTGRES_USER')
        password = values.get('POSTGRES_PASSWORD')
        server = values.get('POSTGRES_SERVER')
        port_str = values.get('POSTGRES_PORT')
        db_name = values.get('POSTGRES_DB')

        # Check if all necessary components for
        # PostgreSQL construction are provided
        # These are now effectively mandatory
        # if DATABASE_URL is not set.
        essential_parts = {
            "POSTGRES_SCHEME": scheme,
            "POSTGRES_USER": user,
            "POSTGRES_PASSWORD": password,
            "POSTGRES_SERVER": server,
            "POSTGRES_PORT": port_str,
            "POSTGRES_DB": db_name,
        }

        missing_params = [
            key for key,
            value in essential_parts.items() if value is None
        ]

        if missing_params:
            raise ValueError(
                f"Cannot construct DATABASE_URL.\
                     DATABASE_URL is not set, and the following "
                f"parameters required for its construction are missing:\
                     {', '.join(missing_params)}. "
                f"Please provide either a full DATABASE_URL or all of these: "
                f"{', '.join(essential_parts.keys())} \
                    in the environment or .env file."
            )

        try:
            # Port can be None if not specified,
            # PostgresDsn.build handles default
            port: int | None = None

            # Should not be None if missing_params is empty
            if port_str is not None:
                # Ensure port_str is treated
                # as string before int conversion
                port = int(str(port_str))

            # Construct the DSN string
            # Assert parts are not None
            # due to the check above,
            # help type checker
            assert scheme is not None
            assert user is not None
            assert password is not None
            assert server is not None
            assert db_name is not None

            constructed_url = f"{scheme}://{user}:{password}@{server}:{port}/{db_name}"

            # Validate the constructed URL with PostgresDsn
            # (or let it be a string if it's for sqlite)
            if "sqlite" not in scheme:
                # This will raise ValueError if invalid
                PostgresDsn(constructed_url)

            values[
                'DATABASE_URL'
            ] = constructed_url
            print(
                f"DEBUG: \Constructed DATABASE_URL: {constructed_url}"
            )
        # Catches int() conversion or
        # PostgresDsn validation error
        except ValueError as e:
            # Add more context to the error
            original_error_msg = str(e)

            if "invalid port number" in \
                original_error_msg.lower() or \
                    "invalid literal \
                        for int()" in original_error_msg.lower():

                detailed_error = f"POSTGRES_PORT \
                    ('{port_str}') must be a valid integer."

            else:
                detailed_error = f"Ensure all parts \
                      (USER, PASSWORD, SERVER, PORT, DB, SCHEME) \
                          form a valid DSN. \
                            Original Pydantic/validation\
                                 error: {original_error_msg}"

            raise ValueError(
                f"Error constructing DATABASE_URL \
                    from parts. {detailed_error}")

        return values

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding='utf-8',
        extra='ignore'
    )


# Create an instance of the settings.
# Pydantic will raise validation errors if
# required fields are missing.
# (those without defaults and not set by the validator)
settings = Settings()

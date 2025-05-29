from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import PostgresDsn, model_validator
from typing import Any, Dict


class Settings(BaseSettings):
    """
    Application settings are managed by this class.
    Values are read from environment variables or a .env file.
    """
    POSTGRES_USER: str | None = None
    POSTGRES_PASSWORD: str | None = None
    POSTGRES_SERVER: str | None = "localhost"
    POSTGRES_PORT: str | None = "5432"
    POSTGRES_DB: str | None = None

    # DATABASE_URL can be fully provided or constructed from the parts above
    DATABASE_URL: PostgresDsn | str | None = None
    DATABASE_ECHO: bool = True

    # JWT settings
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    @model_validator(mode='before')
    @classmethod
    def assemble_db_connection(
        cls,
        values: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Constructs the DATABASE_URL from individual PostgreSQL components
        if DATABASE_URL is not explicitly provided.
        It also ensures that the URL uses the asyncpg driver for PostgreSQL.
        Raises ValueError for configuration issues.
        """
        db_url = values.get('DATABASE_URL')

        # If DATABASE_URL is already set
        if db_url and isinstance(db_url, str):
            # Allow sqlite for local testing/dev
            if "sqlite" in db_url:
                pass
            elif db_url.startswith(
                "postgresql://"
            ) or db_url.startswith(
                "postgres://"
            ):
                values['DATABASE_URL'] = db_url.replace(
                    "postgresql://", "postgresql+asyncpg://"
                ).replace(
                    "postgres://", "postgresql+asyncpg://"
                )
            elif not db_url.startswith(
                "postgresql+asyncpg://"
            ):
                raise ValueError(
                    f"DATABASE_URL '{db_url}' is for PostgreSQL but\
                          does not use the 'postgresql+asyncpg://' scheme. "
                    "Please ensure the URL starts with 'postgresql+asyncpg://'\
                          or is a valid SQLite DSN."
                )
            return values

        # If DATABASE_URL is not set, try to construct it from parts
        pg_user = values.get('POSTGRES_USER')
        pg_password = values.get('POSTGRES_PASSWORD')
        pg_server = values.get('POSTGRES_SERVER')
        pg_port_str = values.get('POSTGRES_PORT')
        pg_db = values.get('POSTGRES_DB')

        required_pg_params = {
            "POSTGRES_USER": pg_user,
            "POSTGRES_PASSWORD": pg_password,
            "POSTGRES_DB": pg_db
        }
        missing_params = [key for key,
                          value in required_pg_params.items() if value is None]

        if missing_params:
            if db_url is None:
                raise ValueError(
                    f"DATABASE_URL is not set and the following \
                        PostgreSQL connection parameters are missing: "
                    f"{', '.join(missing_params)}.\
                          Please provide either a full DATABASE_URL or all "
                    "POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_SERVER,\
                          POSTGRES_PORT, POSTGRES_DB "
                    "in the environment or .env file."
                )

        try:
            port_number: int | None = None
            if pg_port_str is not None:
                port_number = int(pg_port_str)

            if pg_user is None or pg_password is None or pg_db is None:
                # This case should ideally be caught by the missing_params
                # check if DATABASE_URL was also None.
                # Adding an explicit check here for robustness
                # before calling PostgresDsn.build
                raise ValueError(
                    "Cannot construct DATABASE_URL:\
                          User, Password, or DB name is missing."
                )

            values['DATABASE_URL'] = str(
                PostgresDsn.build(
                    scheme="postgresql+asyncpg",
                    username=pg_user,
                    password=pg_password,
                    host=pg_server or "localhost",
                    port=port_number,
                    path=f"/{pg_db}"
                )
            )
        except ValueError as e:
            raise ValueError(
                f"Error constructing DATABASE_URL from parts. "
                f"POSTGRES_PORT ('{pg_port_str}') must be \
                    a valid integer if provided. Original error: {e}"
            )

        return values

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding='utf-8',
        extra='ignore'
    )


# Create an instance of the settings
settings = Settings()

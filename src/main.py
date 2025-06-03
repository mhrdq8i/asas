from contextlib import (
    asynccontextmanager
)
from typing import AsyncGenerator

from fastapi import FastAPI

from src.database.session import init_db
from src.core.config import settings
from src.core.error_handlers import register_error_handlers
from src.api.v1.endpoints import auth as auth_router_v1
from src.api.v1.endpoints import users as users_router_v1


@asynccontextmanager
async def lifespan(
    app_instance: FastAPI
) -> AsyncGenerator[None, None]:
    """
    Context manager to handle application
    startup and shutdown events.
    - On startup: create database tables.
    - On shutdown: (can add cleanup logic here if needed)
    """

    print(
        "Application Lifespan: Startup sequence initiated."
    )

    print(
        "Creating database tables if they don't exist..."
    )

    await init_db()

    print(
        "Database tables check/creation complete."
    )

    yield

    print(
        "Application Lifespan: Shutdown sequence initiated."
    )

app = FastAPI(
    title=getattr(
        settings,
        'APP_NAME',
        "Incident Management System"
    ),
    version=getattr(
        settings,
        'APP_VERSION',
        "0.1.0"
    ),
    description="Incidents management tracking.",
    lifespan=lifespan,
    openapi_url="/api/v1/openapi.json",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc"
)

register_error_handlers(app)
print(
    "Custom error handlers registered "
    "with the application."
)

# Authentication router
app.include_router(
    auth_router_v1.router,
    prefix="/api/v1",
    tags=["V1 - Authentication"]
)
print(
    "Included auth router with prefix /api/v1/auth"
)

# Users router
app.include_router(
    users_router_v1.router,
    prefix="/api/v1",
    tags=["V1 - Users"]
)
print(
    "Included users router with prefix /api/v1/users"
)


@app.get(
    "/",
    tags=["Root"],
    summary="Root Endpoint"
)
async def root():
    """
    Root endpoint to check if the API is running.
    Provides basic information about the API.
    """
    return {
        "message": f"Welcome to the {app.title}",
        "version": app.version,
        "documentation_swagger": app.docs_url,
        "documentation_redoc": app.redoc_url
    }

if __name__ == "__main__":
    import uvicorn
    print(
        "Starting Uvicorn server programmatically"
    )

    server_host = getattr(
        settings,
        'SERVER_HOST',
        "0.0.0.0"
    )
    server_port = getattr(
        settings,
        'SERVER_PORT',
        8000
    )
    # Default to True
    # for dev if not set
    debug_mode = getattr(
        settings,
        'DEBUG_MODE',
        True
    )
    log_level = getattr(
        settings,
        'LOG_LEVEL',
        "info"
    ).lower()

    uvicorn.run(
        "main:app",
        host=server_host,
        port=server_port,
        # Enable reload if DEBUG_MODE is True
        reload=debug_mode,
        log_level=log_level,
        # For development, 1 worker is usually fine
        # workers=1
    )

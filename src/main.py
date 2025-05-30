from contextlib import (
    asynccontextmanager
)
from typing import AsyncGenerator

from fastapi import FastAPI

from src.database.session import init_db
from src.core.config import settings
from src.core.error_handlers import (
    register_error_handlers
)
from src.api.v1.endpoints import (
    auth as auth_router_v1
)
from src.api.v1.endpoints import (
    users as users_router_v1
)


@asynccontextmanager
async def lifespan(
    _app: FastAPI
) -> AsyncGenerator[None, None]:
    """
    Context manager to handle application
      startup and shutdown events.
    - On startup: create database tables.
    - On shutdown: (can add cleanup logic here if needed, e.g.,
        close DB engine for some drivers)
    """

    print("Application Lifespan: Startup sequence initiated.")
    print("Creating database tables if they don't exist...")

    await init_db()

    print("Database tables check/creation complete.")

    yield

    print("Application Lifespan: Shutdown sequence initiated.")


app = FastAPI(
    title=settings.APP_NAME if hasattr(
        settings, 'APP_NAME'
    ) else "Incident Management System API",
    version=settings.APP_VERSION if hasattr(
        settings, 'APP_VERSION'
    ) else "0.1.0",
    description="API for managing incidents, users, and related entities.",
    lifespan=lifespan,

    # openapi_url="/api/v1/openapi.json",
    # docs_url="/api/v1/docs",
    # redoc_url="/api/v1/redoc"
)

register_error_handlers(app)
print("Custom error handlers registered.")

app.include_router(
    auth_router_v1.router,
    prefix="/api/v1/auth",
    tags=["V1 - Authentication"]
)

app.include_router(
    users_router_v1.router,
    prefix="/api/v1/users",
    tags=["V1 - Users"]
)

# Example for admin router if you create one
# app.include_router(
#     admin_router_example.router,
#     prefix="/api/v1/admin",
#     tags=["V1 - Admin"]
#     # Protect all admin routes
#     # dependencies=[Depends(get_current_active_superuser)]
# )

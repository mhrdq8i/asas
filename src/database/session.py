from logging import getLogger

from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import (
    AsyncSession
)
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncEngine
)

from src.core.config import settings


logger = getLogger(__name__)

engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    echo=True,
    future=True
)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db():

    logger.info(
        "Attempting to initialize database and create tables."
    )

    try:
        known_models = list(
            SQLModel.metadata.tables.keys()
        )

        if not known_models:
            logger.critical(
                "SQLModel.metadata is empty! "
                "Models might not have been "
                "imported correctly. "
                "Ensure 'src.models' is imported."
            )

            return

        logger.debug(
            f"Models known by SQLModel: {known_models}"
        )

        async with engine.begin() as conn:
            await conn.run_sync(
                SQLModel.metadata.create_all
            )

        logger.info(
            "Database tables checked/created successfully."
        )

    except Exception:
        logger.critical(
            "Failed to create database tables.",
            exc_info=True
        )

        raise


async def get_async_session() -> AsyncSession:  # type: ignore

    async_session = AsyncSessionLocal()

    try:
        yield async_session

    finally:
        await async_session.close()

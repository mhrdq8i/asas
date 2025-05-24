from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    create_async_engine
)
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings


def get_engine() -> AsyncEngine:
    return create_async_engine(
        settings.DATABASE_URL,
        echo=True,
        future=True
    )


engine = get_engine()

async_session = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session

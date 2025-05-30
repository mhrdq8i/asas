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
    print("Creating database tables (async)...")

    try:
        print(f"Models known by SQLModel.metadata before create_all:\
               {list(SQLModel.metadata.tables.keys())}"
              )

        if not SQLModel.metadata.tables:
            print(
                "CRITICAL: SQLModel.metadata is empty in create_db_and_tables!"
                "Models might not have been imported correctly via 'from . "
                "import models' in database.py"
            )

        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

        print("Database tables created successfully (async).")

    except Exception as e:
        print(f"Error creating database tables (async): {e}")


async def get_async_session() -> AsyncSession:
    async_session = AsyncSessionLocal()
    try:
        yield async_session
    finally:
        await async_session.close()

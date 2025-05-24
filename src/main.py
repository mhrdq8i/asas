from contextlib import asynccontextmanager
import uvicorn

from fastapi import FastAPI

from app.routes import (
    author_routes,
    auth_user,
    password_reset,
    book_routes
)

from app.core.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(lifespan=lifespan)

app.include_router(author_routes.router)
app.include_router(auth_user.router)
app.include_router(book_routes.router)
app.include_router(password_reset.router)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

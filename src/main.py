from contextlib import asynccontextmanager
import uvicorn

from fastapi import FastAPI


from src.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

app = FastAPI(lifespan=lifespan)


@app.get("/")
async def landing():
    return {"Message": "OK"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="trace"
    )

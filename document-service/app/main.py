from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.middleware import LoggingMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app = FastAPI(
    title="Document Service",
    lifespan=lifespan
)

app.add_middleware(LoggingMiddleware)

app.include_router(health_router)

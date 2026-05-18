from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.middleware import LoggingMiddleware
from app.llm.client import anthropic_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    await anthropic_client.setup()

    yield


app = FastAPI(
    title="Document Service",
    lifespan=lifespan
)

app.add_middleware(LoggingMiddleware)

app.include_router(health_router)

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.agent import router as agent_router
from app.api.documents import router as documents_router
from app.api.exception_handlers import register_exception_handlers
from app.api.health import router as health_router
from app.api.middleware import LoggingMiddleware
from app.api.requests import router as requests_router
from app.core.logger import logger
from app.core.redis_conn import redis_manager
from app.llm.client import llm_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting document service")

    await llm_client.setup()
    try:
        await redis_manager.connect()
    except Exception as ex:
        logger.warning("Redis connection failed during startup", error=str(ex))

    yield

    logger.info("Shutting down document service")

    await redis_manager.close()
    logger.info("Stopping document service")


app = FastAPI(
    title="Document Service",
    lifespan=lifespan
)

app.add_middleware(LoggingMiddleware)
register_exception_handlers(app)

app.include_router(health_router, prefix="/api/v1")
app.include_router(documents_router, prefix="/api/v1")
app.include_router(requests_router, prefix="/api/v1")
app.include_router(agent_router, prefix="/api/v1")

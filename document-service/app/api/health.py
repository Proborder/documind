from fastapi import APIRouter, status
from sqlalchemy import text
from starlette.responses import JSONResponse

from app.api.dependencies import DBDep
from app.core.config import settings
from app.core.logger import logger
from app.core.redis_conn import redis_manager

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/ping")
async def ping():
    logger.info("healthcheck_called")
    return {"status": "ok", "model": settings.ANTHROPIC_MODEL}


@router.get("/live")
async def live():
    return {"status": "ok"}


@router.get("/ready")
async def ready(db: DBDep) -> JSONResponse:
    logger.info("Readiness check called")

    checks = {"postgres": "ok", "redis": "ok"}
    status_code = status.HTTP_200_OK

    try:
        db.session.execute(text("SELECT 1"))
    except Exception as ex:
        logger.warning("Readiness check failed: PostgreSQL is unavailable", error=ex)
        checks["postgresql"] = "Unavailable"
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    try:
        await redis_manager.ping()
    except Exception as ex:
        logger.warning("Readiness check failed: Redis is unavailable", error=ex)
        checks["redis"] = "Unavailable"
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(status_code=status_code, content=checks)

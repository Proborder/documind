from fastapi import APIRouter

from app.core.config import settings
from app.core.logger import logger

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/ping")
async def ping():
    logger.info("healthcheck_called")
    return {"status": "ok", "model": settings.ANTHROPIC_MODEL}

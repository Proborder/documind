import redis.asyncio as redis

from app.core.config import settings
from app.core.logger import logger


class RedisManager:
    _redis: redis.Redis

    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port

    async def connect(self):
        logger.info(f"Connect to Redis host={self.host}, port={self.port}")
        self._redis = redis.Redis(host=self.host, port=self.port, decode_responses=True)
        await self._redis.ping()
        logger.info(f"Success connect to Redis host={self.host}, port={self.port}")

    async def set(self, key: str, value: str, expire: int | None = None):
        if expire:
            await self._redis.set(key, value, ex=expire)
        else:
            await self._redis.set(key, value)

    async def get(self, key: str):
        return await self._redis.get(key)

    async def delete(self, key: str):
        await self._redis.delete(key)

    async def ping(self):
        await self._redis.ping()

    async def close(self):
        if hasattr(self, "_redis"):
            await self._redis.aclose()
            logger.info("Redis connection closed")


redis_manager = RedisManager(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT
)

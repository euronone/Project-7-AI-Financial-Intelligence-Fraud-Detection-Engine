import time

import structlog
from fastapi import Request
from redis.asyncio import from_url as redis_from_url

from app.config import get_settings
from app.core.exceptions import RateLimitError

logger = structlog.get_logger()

_redis_client = None


async def get_redis():
    global _redis_client
    if _redis_client is None:
        settings = get_settings()
        _redis_client = redis_from_url(settings.redis_url, decode_responses=True)
    return _redis_client


async def check_rate_limit(key: str, max_requests: int, window_seconds: int = 60) -> None:
    """Sliding window rate limiter backed by Redis.

    Raises RateLimitError if the limit is exceeded.
    """
    redis = await get_redis()
    now = time.time()
    window_start = now - window_seconds
    pipe_key = f"rate_limit:{key}"

    pipe = redis.pipeline()
    pipe.zremrangebyscore(pipe_key, 0, window_start)
    pipe.zadd(pipe_key, {str(now): now})
    pipe.zcard(pipe_key)
    pipe.expire(pipe_key, window_seconds + 1)
    results = await pipe.execute()

    current_count = results[2]
    if current_count > max_requests:
        logger.warning("rate_limit_exceeded", key=key, count=current_count, limit=max_requests)
        raise RateLimitError(f"Rate limit exceeded: {max_requests} requests per {window_seconds}s")


async def rate_limit_auth(request: Request) -> None:
    """Rate limiter for auth endpoints: 100 req/min per IP."""
    client_ip = request.client.host if request.client else "unknown"
    await check_rate_limit(f"auth:{client_ip}", max_requests=100, window_seconds=60)


async def rate_limit_data(request: Request) -> None:
    """Rate limiter for data endpoints: 1000 req/min per IP."""
    client_ip = request.client.host if request.client else "unknown"
    await check_rate_limit(f"data:{client_ip}", max_requests=1000, window_seconds=60)

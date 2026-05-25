"""全局限流中间件 — 基于 Redis 的滑动窗口限流，支持多实例部署."""

import time
from fastapi import Request, HTTPException
from config.settings import settings
from src.common.logger import get_logger

logger = get_logger(__name__)


class RedisRateLimiter:
    """基于 Redis 的滑动窗口限流器."""

    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window = window_seconds
        self._redis = None

    def _get_redis(self):
        if self._redis is None:
            import redis
            self._redis = redis.from_url(settings.redis_url, decode_responses=True)
        return self._redis

    def check(self, client_id: str) -> bool:
        now = time.time()
        window_start = now - self.window
        key = f"ratelimit:{client_id}"

        try:
            r = self._get_redis()
            pipe = r.pipeline()
            # 移除窗口外的旧记录
            pipe.zremrangebyscore(key, 0, window_start)
            # 统计当前窗口内的请求数
            pipe.zcard(key)
            # 添加当前请求
            pipe.zadd(key, {str(now): now})
            # 设置 key 过期时间（自动清理）
            pipe.expire(key, self.window)
            results = pipe.execute()

            request_count = results[1]
            return request_count < self.max_requests
        except Exception as e:
            # Redis 不可用时放行（降级策略）
            logger.warning(f"Rate limiter Redis error, allowing request: {e}")
            return True


limiter = RedisRateLimiter(max_requests=60, window_seconds=60)


async def rate_limit_middleware(request: Request, call_next):
    client_id = request.client.host if request.client else "unknown"
    if not limiter.check(client_id):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    return await call_next(request)

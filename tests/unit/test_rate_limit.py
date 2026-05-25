"""限流器单元测试."""

import pytest
from unittest.mock import MagicMock, patch
from src.api.middleware.rate_limit import RedisRateLimiter


class TestRedisRateLimiter:
    def _make_limiter(self, max_requests=3, window_seconds=60):
        """创建带 mock Redis 的限流器."""
        limiter = RedisRateLimiter(max_requests=max_requests, window_seconds=window_seconds)
        # 使用内存 dict 模拟 Redis sorted set
        store = {}

        class MockRedis:
            def pipeline(self):
                return MockPipeline(store, max_requests, window_seconds)

        class MockPipeline:
            def __init__(self, store, max_req, window):
                self.store = store
                self.max_req = max_req
                self.window = window
                self.ops = []

            def zremrangebyscore(self, key, min_val, max_val):
                self.ops.append(("zrem", key, min_val, max_val))

            def zcard(self, key):
                self.ops.append(("zcard", key))

            def zadd(self, key, mapping):
                self.ops.append(("zadd", key, mapping))

            def expire(self, key, ttl):
                self.ops.append(("expire", key, ttl))

            def execute(self):
                results = []
                key = None
                for op in self.ops:
                    if op[0] == "zrem":
                        key = op[1]
                        if key in self.store:
                            self.store[key] = [(s, v) for s, v in self.store[key] if s > op[2]]
                        results.append(0)
                    elif op[0] == "zcard":
                        key = op[1]
                        results.append(len(self.store.get(key, [])))
                    elif op[0] == "zadd":
                        key = op[1]
                        if key not in self.store:
                            self.store[key] = []
                        for member, score in op[2].items():
                            self.store[key].append((score, member))
                        results.append(1)
                    elif op[0] == "expire":
                        results.append(True)
                return results

        limiter._redis = MockRedis()
        return limiter

    def test_allows_within_limit(self):
        limiter = self._make_limiter(max_requests=3)
        assert limiter.check("user1")
        assert limiter.check("user1")
        assert limiter.check("user1")

    def test_blocks_over_limit(self):
        limiter = self._make_limiter(max_requests=2)
        assert limiter.check("user1")
        assert limiter.check("user1")
        assert not limiter.check("user1")

    def test_different_clients_independent(self):
        limiter = self._make_limiter(max_requests=1)
        assert limiter.check("user1")
        assert limiter.check("user2")
        assert not limiter.check("user1")

    def test_graceful_degradation_on_redis_error(self):
        limiter = RedisRateLimiter(max_requests=1)
        limiter._redis = None

        class BrokenRedis:
            def pipeline(self):
                raise ConnectionError("Redis down")

        limiter._redis = BrokenRedis()
        # Redis 故障时应降级放行
        assert limiter.check("user1")

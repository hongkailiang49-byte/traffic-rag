"""LLM Gateway 单元测试 — 熔断器逻辑."""

import time
import pytest
from src.generation_layer.llm_gateway import CircuitBreakerState, LLMGateway


class TestCircuitBreakerState:
    def test_initial_state(self):
        cb = CircuitBreakerState()
        assert cb.should_allow()
        assert not cb.is_open
        assert cb.failure_count == 0

    def test_opens_after_threshold(self):
        cb = CircuitBreakerState(threshold=3)
        for _ in range(3):
            cb.record_failure()
        assert cb.is_open
        assert not cb.should_allow()

    def test_recovers_after_timeout(self):
        cb = CircuitBreakerState(threshold=1, recovery_timeout=0.1)
        cb.record_failure()
        assert cb.is_open
        time.sleep(0.15)
        assert cb.should_allow()

    def test_success_resets_failure_count(self):
        cb = CircuitBreakerState(threshold=3)
        cb.record_failure()
        cb.record_failure()
        cb.record_success()
        assert cb.failure_count == 0

    def test_closes_after_recovery_successes(self):
        cb = CircuitBreakerState(threshold=1, recovery_timeout=0.01)
        cb.record_failure()
        assert cb.is_open
        time.sleep(0.02)
        # 需要 3 次成功才能关闭
        cb.record_success()
        cb.record_success()
        cb.record_success()
        assert not cb.is_open


class TestLLMGateway:
    def test_resolve_provider_fallback(self):
        gw = LLMGateway()
        # 当主 provider 熔断时，应降级到备选
        gw.breakers["mimo"].record_failure()
        gw.breakers["mimo"].record_failure()
        gw.breakers["mimo"].record_failure()
        gw.breakers["mimo"].record_failure()
        gw.breakers["mimo"].record_failure()
        assert gw.breakers["mimo"].is_open
        provider = gw._resolve_provider("mimo")
        assert provider == "mimo_pro"

    def test_build_messages(self):
        messages = LLMGateway._build_messages("hello", "system msg")
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"

    def test_build_messages_no_system(self):
        messages = LLMGateway._build_messages("hello", "")
        assert len(messages) == 1
        assert messages[0]["role"] == "user"

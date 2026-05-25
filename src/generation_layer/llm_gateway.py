"""LLM 统一调用网关 — mimo-v2.5 主力 + mimo-v2.5-pro 备选."""

import time
from dataclasses import dataclass
from src.common.logger import get_logger
from src.common.exceptions import LLMGatewayError

logger = get_logger(__name__)


@dataclass
class CircuitBreakerState:
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: float = 0
    is_open: bool = False
    threshold: int = 5
    recovery_timeout: float = 60.0

    def record_success(self):
        self.success_count += 1
        self.failure_count = 0
        if self.is_open and self.success_count >= 3:
            self.is_open = False

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.threshold:
            self.is_open = True

    def should_allow(self) -> bool:
        if not self.is_open:
            return True
        return time.time() - self.last_failure_time > self.recovery_timeout


class LLMGateway:
    """统一 LLM 调用网关 — mimo-v2.5 为主，mimo-v2.5-pro 为备."""

    PROVIDERS = ["mimo", "mimo_pro"]

    def __init__(
        self,
        mimo_base_url: str = "",
        mimo_api_key: str = "",
        mimo_model: str = "mimo-v2.5",
        mimo_pro_model: str = "mimo-v2.5-pro",
    ):
        self.mimo_base_url = mimo_base_url
        self.mimo_api_key = mimo_api_key
        self.mimo_model = mimo_model
        self.mimo_pro_model = mimo_pro_model
        self.breakers = {k: CircuitBreakerState() for k in self.PROVIDERS}
        self._async_client = None
        self._sync_client = None

    def _get_model(self, provider: str) -> str:
        return self.mimo_pro_model if provider == "mimo_pro" else self.mimo_model

    async def invoke(self, prompt: str, provider: str = "mimo", system_prompt: str = "", **kwargs) -> str:
        provider = self._resolve_provider(provider)
        try:
            result = await self._call_api(provider, prompt, system_prompt)
            self.breakers[provider].record_success()
            return result
        except Exception as e:
            self.breakers[provider].record_failure()
            logger.warning(f"LLM [{provider}] failed: {e}")
            next_provider = self._fallback(provider)
            if next_provider != provider:
                return await self.invoke(prompt, provider=next_provider, system_prompt=system_prompt, **kwargs)
            raise LLMGatewayError(f"All LLM providers failed: {e}")

    def invoke_sync(self, prompt: str, provider: str = "mimo", system_prompt: str = "", **kwargs) -> str:
        provider = self._resolve_provider(provider)
        try:
            result = self._call_api_sync(provider, prompt, system_prompt)
            self.breakers[provider].record_success()
            return result
        except Exception as e:
            self.breakers[provider].record_failure()
            logger.warning(f"LLM [{provider}] failed: {e}")
            next_provider = self._fallback(provider)
            if next_provider != provider:
                return self.invoke_sync(prompt, provider=next_provider, system_prompt=system_prompt, **kwargs)
            raise LLMGatewayError(f"All LLM providers failed: {e}")

    def _resolve_provider(self, provider: str) -> str:
        if provider in self.PROVIDERS and self.breakers[provider].should_allow():
            return provider
        return self._fallback(provider)

    def _get_async_client(self):
        if self._async_client is None:
            from openai import AsyncOpenAI
            self._async_client = AsyncOpenAI(base_url=self.mimo_base_url, api_key=self.mimo_api_key)
        return self._async_client

    def _get_sync_client(self):
        if self._sync_client is None:
            from openai import OpenAI
            self._sync_client = OpenAI(base_url=self.mimo_base_url, api_key=self.mimo_api_key)
        return self._sync_client

    async def _call_api(self, provider: str, prompt: str, system_prompt: str) -> str:
        client = self._get_async_client()
        messages = self._build_messages(prompt, system_prompt)
        response = await client.chat.completions.create(model=self._get_model(provider), messages=messages)
        return response.choices[0].message.content

    def _call_api_sync(self, provider: str, prompt: str, system_prompt: str) -> str:
        client = self._get_sync_client()
        messages = self._build_messages(prompt, system_prompt)
        response = client.chat.completions.create(model=self._get_model(provider), messages=messages)
        return response.choices[0].message.content

    @staticmethod
    def _build_messages(prompt: str, system_prompt: str) -> list[dict]:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        return messages

    def _fallback(self, failed_provider: str) -> str:
        for name in self.PROVIDERS:
            if name != failed_provider and self.breakers[name].should_allow():
                return name
        return failed_provider

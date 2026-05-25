"""重试装饰器 — 基于 tenacity."""

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type


def llm_retry(max_attempts: int = 3):
    """LLM 调用重试：指数退避，最多 3 次."""
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        reraise=True,
    )


def db_retry(max_attempts: int = 3):
    """数据库操作重试."""
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=0.5, min=1, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        reraise=True,
    )

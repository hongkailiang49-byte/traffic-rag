"""Reranker 抽象基类."""

from abc import ABC, abstractmethod


class BaseReranker(ABC):
    """重排序器接口."""

    @abstractmethod
    def rerank(self, query: str, documents: list[str], top_k: int = 5) -> list[tuple[str, float]]:
        """重排序，返回 (document, score) 列表."""
        ...

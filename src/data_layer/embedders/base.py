"""Embedding 服务抽象基类."""

from abc import ABC, abstractmethod


class BaseEmbedder(ABC):
    """Embedding 服务接口."""

    @abstractmethod
    def encode(self, texts: list[str]) -> list[list[float]]:
        """批量向量化."""
        ...

    @abstractmethod
    def encode_query(self, query: str) -> list[float]:
        """单条查询向量化（可能带指令前缀）."""
        ...

    @property
    @abstractmethod
    def dimension(self) -> int:
        """向量维度."""
        ...

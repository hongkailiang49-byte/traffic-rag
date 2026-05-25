"""检索器抽象基类."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class RetrievalResult:
    """检索结果."""
    content: str
    score: float
    metadata: dict = field(default_factory=dict)
    chunk_id: str = ""
    source: str = ""  # vector / graph / hybrid


class BaseRetriever(ABC):
    """检索器接口."""

    @abstractmethod
    def retrieve(self, query: str, top_k: int = 5, **kwargs) -> list[RetrievalResult]:
        ...

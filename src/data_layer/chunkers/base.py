"""切片器抽象基类."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class Chunk:
    """切片结果."""
    content: str
    metadata: dict = field(default_factory=dict)
    chunk_id: str = ""

    def __post_init__(self):
        if not self.chunk_id:
            import hashlib
            self.chunk_id = hashlib.md5(self.content.encode()).hexdigest()[:16]


class BaseChunker(ABC):
    """切片器接口 — 策略模式."""

    @abstractmethod
    def chunk(self, text: str, metadata: dict | None = None) -> list[Chunk]:
        """将文本切分为 chunks."""
        ...

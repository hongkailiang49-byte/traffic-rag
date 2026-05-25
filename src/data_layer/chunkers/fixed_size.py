"""固定窗口切片器（兜底方案）."""

from .base import BaseChunker, Chunk


class FixedSizeChunker(BaseChunker):
    """按固定字符数切分，带重叠窗口."""

    def __init__(self, chunk_size: int = 1000, overlap: int = 200):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str, metadata: dict | None = None) -> list[Chunk]:
        metadata = metadata or {}
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            content = text[start:end].strip()
            if content:
                chunks.append(Chunk(content=content, metadata=metadata))
            start += self.chunk_size - self.overlap
        return chunks

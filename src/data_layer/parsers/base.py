"""文档解析器抽象基类."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ParsedDocument:
    """解析后的统一文档结构."""
    content: str
    metadata: dict = field(default_factory=dict)
    source_path: str = ""
    doc_type: str = ""

    @property
    def char_count(self) -> int:
        return len(self.content)


class BaseParser(ABC):
    """文档解析器接口 — 策略模式."""

    @abstractmethod
    def parse(self, file_path: Path) -> ParsedDocument:
        """解析文件，返回统一结构."""
        ...

    @abstractmethod
    def supports(self, file_path: Path) -> bool:
        """判断是否支持该文件格式."""
        ...

    @staticmethod
    def _extract_metadata_from_filename(file_path: Path) -> dict:
        """从文件名提取通用元数据."""
        name = file_path.stem
        parts = name.split("_", 1)
        metadata = {"filename": file_path.name}
        if len(parts) >= 2 and parts[0].isdigit():
            metadata["doc_id"] = parts[0]
            metadata["title"] = parts[1]
        else:
            metadata["title"] = name
        return metadata

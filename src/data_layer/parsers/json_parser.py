"""JSON 文档解析器 — 将嵌套 JSON 展平为可读文本."""

from pathlib import Path
from .base import BaseParser, ParsedDocument


class JSONParser(BaseParser):
    """解析 JSON 文件，将嵌套结构展平为文本."""

    def supports(self, file_path: Path) -> bool:
        return file_path.suffix.lower() == ".json"

    def parse(self, file_path: Path) -> ParsedDocument:
        import json

        metadata = self._extract_metadata_from_filename(file_path)
        metadata["source_path"] = str(file_path)

        data = json.loads(file_path.read_text(encoding="utf-8"))
        content = self._flatten_to_text(data, prefix="")
        return ParsedDocument(content=content, metadata=metadata, source_path=str(file_path), doc_type="json")

    def _flatten_to_text(self, obj, prefix: str) -> str:
        if isinstance(obj, dict):
            parts = []
            for k, v in obj.items():
                new_prefix = f"{prefix}.{k}" if prefix else k
                parts.append(self._flatten_to_text(v, new_prefix))
            return "\n".join(parts)
        elif isinstance(obj, list):
            parts = []
            for i, item in enumerate(obj):
                new_prefix = f"{prefix}[{i}]"
                parts.append(self._flatten_to_text(item, new_prefix))
            return "\n".join(parts)
        else:
            return f"{prefix}: {obj}"

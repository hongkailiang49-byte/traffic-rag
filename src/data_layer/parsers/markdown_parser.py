"""Markdown 文档解析器."""

import re
from pathlib import Path
from .base import BaseParser, ParsedDocument


class MarkdownParser(BaseParser):
    """解析 Markdown 文件，提取 frontmatter 和正文."""

    def supports(self, file_path: Path) -> bool:
        return file_path.suffix.lower() in (".md", ".markdown")

    def parse(self, file_path: Path) -> ParsedDocument:
        raw = file_path.read_text(encoding="utf-8")
        metadata = self._extract_metadata_from_filename(file_path)
        frontmatter, body = self._split_frontmatter(raw)
        metadata.update(frontmatter)
        metadata["source_path"] = str(file_path)
        return ParsedDocument(content=body.strip(), metadata=metadata, source_path=str(file_path), doc_type="markdown")

    @staticmethod
    def _split_frontmatter(text: str) -> tuple[dict, str]:
        """分离 YAML frontmatter 和正文."""
        pattern = r"^---\s*\n(.*?)\n---\s*\n(.*)$"
        match = re.match(pattern, text, re.DOTALL)
        if not match:
            return {}, text
        fm_text = match.group(1)
        body = match.group(2)
        fm = {}
        for line in fm_text.strip().split("\n"):
            if ":" in line:
                key, val = line.split(":", 1)
                fm[key.strip()] = val.strip().strip('"').strip("'")
        return fm, body

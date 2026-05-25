"""层级 Markdown 切片器 — 适配交通法规的章-节-条结构."""

import re
from .base import BaseChunker, Chunk


class HierarchicalMarkdownChunker(BaseChunker):
    """按 Markdown 标题层级切片，保留面包屑路径上下文."""

    def __init__(self, max_chunk_size: int = 1500, min_chunk_size: int = 100):
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size

    def chunk(self, text: str, metadata: dict | None = None) -> list[Chunk]:
        metadata = metadata or {}
        sections = self._split_by_headings(text)
        chunks = []

        for section in sections:
            breadcrumb = section["breadcrumb"]
            content = section["content"].strip()

            if not content or len(content) < self.min_chunk_size:
                continue

            # 尝试按"第X条"进一步切分
            articles = self._split_by_article(content)
            for article in articles:
                if len(article) < self.min_chunk_size:
                    continue
                # 前置面包屑路径
                full_content = f"[{breadcrumb}]\n{article}" if breadcrumb else article
                # 如果超长，用固定窗口二次切分
                if len(full_content) > self.max_chunk_size:
                    sub_chunks = self._split_by_size(full_content)
                    for sc in sub_chunks:
                        chunks.append(Chunk(content=sc, metadata={**metadata, "breadcrumb": breadcrumb}))
                else:
                    chunks.append(Chunk(content=full_content, metadata={**metadata, "breadcrumb": breadcrumb}))

        return chunks if chunks else [Chunk(content=text[: self.max_chunk_size], metadata=metadata)]

    def _split_by_headings(self, text: str) -> list[dict]:
        """按 Markdown 标题层级切分."""
        heading_pattern = re.compile(r"^(#{1,4})\s+(.+)$", re.MULTILINE)
        matches = list(heading_pattern.finditer(text))

        if not matches:
            return [{"breadcrumb": "", "content": text}]

        sections = []
        heading_stack = []

        for i, match in enumerate(matches):
            level = len(match.group(1))
            title = match.group(2).strip()
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)

            # 更新标题栈
            while heading_stack and heading_stack[-1]["level"] >= level:
                heading_stack.pop()
            heading_stack.append({"level": level, "title": title})

            breadcrumb = " > ".join(h["title"] for h in heading_stack)
            content = text[start:end].strip()

            sections.append({"breadcrumb": breadcrumb, "content": content})

        return sections

    @staticmethod
    def _split_by_article(text: str) -> list[str]:
        """按"第X条"或"第X款"切分."""
        pattern = re.compile(r"^((?:第[一二三四五六七八九十百千万零\d]+[条条款项目])|(?:\d+[.、]))", re.MULTILINE)
        matches = list(pattern.finditer(text))
        if len(matches) <= 1:
            return [text]
        articles = []
        for i, match in enumerate(matches):
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            articles.append(text[start:end].strip())
        return articles

    def _split_by_size(self, text: str) -> list[str]:
        """按最大长度切分（兜底策略）."""
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + self.max_chunk_size, len(text))
            # 尝试在句号处断开
            if end < len(text):
                last_period = text.rfind("。", start, end)
                if last_period > start + self.min_chunk_size:
                    end = last_period + 1
            chunks.append(text[start:end])
            start = end
        return chunks

"""引用溯源管理."""


class CitationManager:
    """管理回答中的引用溯源."""

    def build_context_with_citation(self, chunks: list) -> str:
        """为每个 chunk 附加引用标记，返回组装后的上下文."""
        context_parts = []
        for i, chunk in enumerate(chunks):
            ref_id = f"[{i + 1}]"
            source_info = self._format_source(chunk.metadata if hasattr(chunk, "metadata") else {})
            content = chunk.content if hasattr(chunk, "content") else str(chunk)
            context_parts.append(f"{ref_id} {source_info}\n{content}")
        return "\n\n---\n\n".join(context_parts)

    @staticmethod
    def _format_source(metadata: dict) -> str:
        if metadata.get("standard_id"):
            return f"来源：{metadata['standard_id']} {metadata.get('breadcrumb', '')}"
        if metadata.get("title"):
            return f"来源：{metadata['title']}"
        if metadata.get("source_path"):
            return f"来源：{metadata['source_path']}"
        return "来源：知识库"

    @staticmethod
    def extract_citations(answer: str) -> list[str]:
        """从回答中提取引用标记."""
        import re
        return re.findall(r"\[(\d+)\]", answer)

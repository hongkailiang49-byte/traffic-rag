"""PDF 文档解析器 — 基于 pdfplumber."""

from pathlib import Path
from .base import BaseParser, ParsedDocument


class PDFParser(BaseParser):
    """解析 PDF 文件，提取文本和表格."""

    def supports(self, file_path: Path) -> bool:
        return file_path.suffix.lower() == ".pdf"

    def parse(self, file_path: Path) -> ParsedDocument:
        import pdfplumber

        metadata = self._extract_metadata_from_filename(file_path)
        metadata["source_path"] = str(file_path)
        pages_text = []

        with pdfplumber.open(file_path) as pdf:
            metadata["total_pages"] = len(pdf.pages)
            for page in pdf.pages:
                text = page.extract_text() or ""
                tables = page.extract_tables()
                if tables:
                    for table in tables:
                        table_str = self._format_table(table)
                        text += "\n" + table_str
                pages_text.append(text)

        content = "\n\n".join(pages_text)
        return ParsedDocument(content=content, metadata=metadata, source_path=str(file_path), doc_type="pdf")

    @staticmethod
    def _format_table(table: list[list]) -> str:
        """将表格数据格式化为 Markdown 表格."""
        if not table or not table[0]:
            return ""
        header = [str(c) if c else "" for c in table[0]]
        lines = ["| " + " | ".join(header) + " |"]
        lines.append("| " + " | ".join(["---"] * len(header)) + " |")
        for row in table[1:]:
            cells = [str(c) if c else "" for c in row]
            while len(cells) < len(header):
                cells.append("")
            lines.append("| " + " | ".join(cells[: len(header)]) + " |")
        return "\n".join(lines)

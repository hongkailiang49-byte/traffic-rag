"""离线索引 Pipeline — 从原始文件到向量入库的完整编排."""

from pathlib import Path
from dataclasses import dataclass
from src.common.logger import get_logger
from src.data_layer.parsers.base import BaseParser, ParsedDocument
from src.data_layer.parsers.markdown_parser import MarkdownParser
from src.data_layer.parsers.pdf_parser import PDFParser
from src.data_layer.parsers.json_parser import JSONParser
from src.data_layer.chunkers.base import Chunk
from src.data_layer.chunkers.hierarchical import HierarchicalMarkdownChunker
from src.data_layer.chunkers.fixed_size import FixedSizeChunker
from src.data_layer.embedders.base import BaseEmbedder
from src.data_layer.stores.vector_store import MilvusVectorStore

logger = get_logger(__name__)


@dataclass
class IngestionResult:
    total_files: int
    total_chunks: int
    success_files: int
    failed_files: list[str]


class IndexingPipeline:
    """离线索引 Pipeline：文件解析 → 切片 → Embedding → 入库."""

    def __init__(self, embedder: BaseEmbedder, vector_store: MilvusVectorStore):
        self.embedder = embedder
        self.vector_store = vector_store
        self.parsers: list[BaseParser] = [MarkdownParser(), PDFParser(), JSONParser()]
        self.hierarchical_chunker = HierarchicalMarkdownChunker()
        self.fixed_chunker = FixedSizeChunker()

    def _get_parser(self, file_path: Path) -> BaseParser | None:
        for parser in self.parsers:
            if parser.supports(file_path):
                return parser
        return None

    def _select_chunker(self, doc: ParsedDocument):
        if doc.doc_type == "markdown":
            return self.hierarchical_chunker
        return self.fixed_chunker

    def ingest_file(self, file_path: Path) -> list[Chunk]:
        """处理单个文件：解析 → 切片."""
        parser = self._get_parser(file_path)
        if not parser:
            logger.warning(f"No parser for: {file_path}")
            return []

        doc = parser.parse(file_path)
        logger.info(f"Parsed {file_path.name}: {doc.char_count} chars")

        chunker = self._select_chunker(doc)
        chunks = chunker.chunk(doc.content, metadata=doc.metadata)
        logger.info(f"Chunked into {len(chunks)} pieces")
        return chunks

    def embed_and_store(self, chunks: list[Chunk]) -> int:
        """Embedding + 入库."""
        if not chunks:
            return 0

        texts = [c.content for c in chunks]
        embeddings = self.embedder.encode(texts)

        records = []
        for chunk, embedding in zip(chunks, embeddings):
            record = {
                "chunk_id": chunk.chunk_id,
                "content": chunk.content,
                "embedding": embedding,
                "category": chunk.metadata.get("category", ""),
                "title": chunk.metadata.get("title", ""),
                "source_path": chunk.metadata.get("source_path", ""),
                "standard_id": chunk.metadata.get("standard_id", ""),
                "year": int(chunk.metadata.get("year", 0)) if chunk.metadata.get("year") else 0,
                "authority": chunk.metadata.get("authority", ""),
                "region": chunk.metadata.get("region", ""),
                "geo_hash": chunk.metadata.get("geo_hash", ""),
                "road_id": chunk.metadata.get("road_id", ""),
                "timestamp": chunk.metadata.get("timestamp", ""),
            }
            records.append(record)

        return self.vector_store.insert(records)

    def run(self, data_dir: str | Path) -> IngestionResult:
        """批量处理目录下所有文件."""
        data_path = Path(data_dir)
        files = [f for f in data_path.rglob("*") if f.is_file() and self._get_parser(f)]
        logger.info(f"Found {len(files)} files to ingest")

        total_chunks = 0
        success = 0
        failed = []

        for file_path in files:
            try:
                chunks = self.ingest_file(file_path)
                count = self.embed_and_store(chunks)
                total_chunks += count
                success += 1
                logger.info(f"Ingested {file_path.name}: {count} chunks")
            except Exception as e:
                failed.append(str(file_path))
                logger.error(f"Failed to ingest {file_path.name}: {e}")

        result = IngestionResult(
            total_files=len(files), total_chunks=total_chunks, success_files=success, failed_files=failed
        )
        logger.info(f"Ingestion complete: {result}")
        return result

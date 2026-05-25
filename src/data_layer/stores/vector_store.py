"""Milvus 向量数据库实现."""

from dataclasses import dataclass
from pymilvus import connections, Collection, CollectionSchema, FieldSchema, DataType, utility
from config.settings import settings
from src.common.logger import get_logger

logger = get_logger(__name__)


@dataclass
class SearchResult:
    content: str
    score: float
    metadata: dict
    chunk_id: str = ""


class MilvusVectorStore:
    """Milvus 向量存储 — 支持标量过滤 + 向量检索."""

    def __init__(self, collection_name: str | None = None):
        self.collection_name = collection_name or settings.milvus_collection
        self._collection: Collection | None = None
        self._connect()

    def _connect(self) -> None:
        """建立 Milvus 连接."""
        connections.connect(alias="default", host=settings.milvus_host, port=settings.milvus_port)
        logger.info(f"Connected to Milvus at {settings.milvus_host}:{settings.milvus_port}")

    def _get_collection(self) -> Collection:
        if self._collection is None:
            self._collection = Collection(self.collection_name)
            self._collection.load()
        return self._collection

    def create_collection(self, dimension: int = 1024) -> None:
        """创建 Collection（如果不存在）."""
        if utility.has_collection(self.collection_name):
            logger.info(f"Collection {self.collection_name} already exists")
            self._collection = Collection(self.collection_name)
            self._collection.load()
            return

        fields = [
            FieldSchema(name="chunk_id", dtype=DataType.VARCHAR, is_primary=True, max_length=64),
            FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dimension),
            # 标量字段用于过滤
            FieldSchema(name="category", dtype=DataType.VARCHAR, max_length=128),
            FieldSchema(name="title", dtype=DataType.VARCHAR, max_length=512),
            FieldSchema(name="source_path", dtype=DataType.VARCHAR, max_length=1024),
            FieldSchema(name="standard_id", dtype=DataType.VARCHAR, max_length=128),
            FieldSchema(name="year", dtype=DataType.INT64),
            FieldSchema(name="authority", dtype=DataType.VARCHAR, max_length=128),
            FieldSchema(name="region", dtype=DataType.VARCHAR, max_length=128),
            FieldSchema(name="geo_hash", dtype=DataType.VARCHAR, max_length=32),
            FieldSchema(name="road_id", dtype=DataType.VARCHAR, max_length=256),
            FieldSchema(name="timestamp", dtype=DataType.VARCHAR, max_length=64),
        ]

        schema = CollectionSchema(fields, description="Traffic RAG Knowledge Base")
        self._collection = Collection(self.collection_name, schema)

        # 创建 HNSW 索引
        index_params = {
            "metric_type": "COSINE",
            "index_type": "HNSW",
            "params": {"M": 16, "efConstruction": 256},
        }
        self._collection.create_index("embedding", index_params)
        logger.info(f"Created collection: {self.collection_name}")

    def insert(self, records: list[dict]) -> int:
        """批量插入记录."""
        collection = self._get_collection()
        # 统一字段
        for r in records:
            for key in ["category", "title", "source_path", "standard_id", "authority", "region", "geo_hash", "road_id", "timestamp"]:
                r.setdefault(key, "")
            r.setdefault("year", 0)
        result = collection.insert(records)
        collection.flush()
        logger.info(f"Inserted {len(records)} records")
        return len(records)

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 10,
        filter_expr: str = "",
        output_fields: list[str] | None = None,
    ) -> list[SearchResult]:
        """向量检索 + 标量过滤."""
        collection = self._get_collection()
        if output_fields is None:
            output_fields = ["content", "category", "title", "source_path", "standard_id", "year", "authority"]

        search_params = {"metric_type": "COSINE", "params": {"ef": 128}}
        results = collection.search(
            data=[query_embedding],
            anns_field="embedding",
            param=search_params,
            limit=top_k,
            expr=filter_expr if filter_expr else None,
            output_fields=output_fields,
        )

        search_results = []
        for hit in results[0]:
            entity = hit.entity
            search_results.append(
                SearchResult(
                    content=entity.get("content", ""),
                    score=float(hit.score),
                    metadata={k: entity.get(k) for k in output_fields if k != "content"},
                    chunk_id=hit.id,
                )
            )
        return search_results

    def count(self) -> int:
        collection = self._get_collection()
        return collection.num_entities

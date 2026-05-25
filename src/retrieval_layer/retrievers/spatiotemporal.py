"""场景2 — 时空多模态检索器：向量 + 空间范围过滤 + 时间衰减."""

import math
from datetime import datetime
from .base import BaseRetriever, RetrievalResult
from src.data_layer.stores.vector_store import MilvusVectorStore
from src.data_layer.embedders.base import BaseEmbedder


class SpatioTemporalRetriever(BaseRetriever):
    """时空增强检索：向量 + GeoHash 过滤 + 时间衰减排序."""

    def __init__(self, vector_store: MilvusVectorStore, embedder: BaseEmbedder):
        self.vector_store = vector_store
        self.embedder = embedder

    def retrieve(self, query: str, top_k: int = 5, **kwargs) -> list[RetrievalResult]:
        geo_hash_prefix = kwargs.get("geo_hash_prefix", "")
        time_range = kwargs.get("time_range", (None, None))

        query_embedding = self.embedder.encode_query(query)

        filter_parts = []
        if geo_hash_prefix:
            safe_hash = str(geo_hash_prefix).replace("'", "").replace('"', "").replace('\\', '')
            if safe_hash.isalnum():
                filter_parts.append(f"geo_hash like '{safe_hash}%'")
        if time_range[0]:
            safe_start = str(time_range[0]).replace("'", "").replace('"', '')
            filter_parts.append(f"timestamp >= '{safe_start}'")
        if time_range[1]:
            safe_end = str(time_range[1]).replace("'", "").replace('"', '')
            filter_parts.append(f"timestamp <= '{safe_end}'")
        filter_expr = " and ".join(filter_parts) if filter_parts else ""

        candidates = self.vector_store.search(
            query_embedding=query_embedding, top_k=30, filter_expr=filter_expr
        )

        # 时间衰减排序
        for c in candidates:
            ts = c.metadata.get("timestamp", "")
            if ts:
                try:
                    age_hours = (datetime.now() - datetime.fromisoformat(ts)).total_seconds() / 3600
                    c.score *= math.exp(-0.01 * age_hours)
                except (ValueError, TypeError):
                    pass

        candidates.sort(key=lambda x: x.score, reverse=True)
        return [RetrievalResult(
            content=c.content, score=c.score, metadata=c.metadata,
            chunk_id=c.chunk_id, source="vector_spatiotemporal"
        ) for c in candidates[:top_k]]

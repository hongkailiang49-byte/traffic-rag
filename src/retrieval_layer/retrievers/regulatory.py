"""场景1 — 法规精准检索器：向量召回 + 元数据硬过滤 + Rerank."""

from .base import BaseRetriever, RetrievalResult
from src.data_layer.stores.vector_store import MilvusVectorStore
from src.data_layer.embedders.base import BaseEmbedder
from src.retrieval_layer.rerankers.base import BaseReranker


class RegulatoryRetriever(BaseRetriever):
    """法规检索：向量召回 → 元数据过滤 → Rerank 精排."""

    def __init__(self, vector_store: MilvusVectorStore, embedder: BaseEmbedder, reranker: BaseReranker | None = None):
        self.vector_store = vector_store
        self.embedder = embedder
        self.reranker = reranker

    def retrieve(self, query: str, top_k: int = 5, **kwargs) -> list[RetrievalResult]:
        filters = kwargs.get("filters", {})
        filter_expr = self._build_filter_expr(filters)

        query_embedding = self.embedder.encode_query(query)
        candidates = self.vector_store.search(
            query_embedding=query_embedding,
            top_k=50,
            filter_expr=filter_expr,
        )

        if self.reranker and candidates:
            texts = [c.content for c in candidates]
            reranked = self.reranker.rerank(query, texts, top_k=top_k)
            results = []
            for i, (text, score) in enumerate(reranked):
                orig = next((c for c in candidates if c.content == text), candidates[0])
                results.append(RetrievalResult(
                    content=text, score=score, metadata=orig.metadata,
                    chunk_id=orig.chunk_id, source="vector"
                ))
            return results

        return [RetrievalResult(
            content=c.content, score=c.score, metadata=c.metadata,
            chunk_id=c.chunk_id, source="vector"
        ) for c in candidates[:top_k]]

    @staticmethod
    def _build_filter_expr(filters: dict) -> str:
        conditions = []
        if filters.get("year_from"):
            val = filters["year_from"]
            if isinstance(val, int) or (isinstance(val, str) and val.isdigit()):
                conditions.append(f"year >= {int(val)}")
        if filters.get("authority"):
            val = str(filters["authority"]).replace("'", "").replace('"', "")
            conditions.append(f"authority == '{val}'")
        if filters.get("region"):
            val = str(filters["region"]).replace("'", "").replace('"', "")
            conditions.append(f"region in ['全国', '{val}']")
        if filters.get("category"):
            val = str(filters["category"]).replace("'", "").replace('"', "")
            conditions.append(f"category == '{val}'")
        return " and ".join(conditions) if conditions else ""

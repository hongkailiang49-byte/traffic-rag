"""混合检索编排器 — 根据意图路由到对应检索器."""

from .base import BaseRetriever, RetrievalResult
from .regulatory import RegulatoryRetriever
from .spatiotemporal import SpatioTemporalRetriever
from .graph_rag import GraphRAGRetriever


class HybridRetriever:
    """混合检索编排：根据意图选择最优检索策略."""

    def __init__(
        self,
        regulatory: RegulatoryRetriever,
        spatiotemporal: SpatioTemporalRetriever,
        graph_rag: GraphRAGRetriever,
    ):
        self.retrievers = {
            "regulatory": regulatory,
            "spatiotemporal": spatiotemporal,
            "graph_rag": graph_rag,
        }

    def retrieve(self, query: str, intent: str = "regulatory", top_k: int = 5, **kwargs) -> list[RetrievalResult]:
        retriever = self.retrievers.get(intent, self.retrievers["regulatory"])
        return retriever.retrieve(query, top_k=top_k, **kwargs)

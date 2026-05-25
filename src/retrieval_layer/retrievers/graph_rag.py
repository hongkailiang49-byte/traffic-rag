"""场景4 — GraphRAG 双路召回：向量 + 图遍历 + Rerank 融合."""

from .base import BaseRetriever, RetrievalResult
from src.data_layer.stores.vector_store import MilvusVectorStore
from src.data_layer.stores.graph_store import Neo4jGraphStore
from src.data_layer.embedders.base import BaseEmbedder
from src.retrieval_layer.rerankers.base import BaseReranker


class GraphRAGRetriever(BaseRetriever):
    """图谱增强检索：向量召回 + 图遍历 + 融合 Rerank."""

    def __init__(
        self,
        vector_store: MilvusVectorStore,
        graph_store: Neo4jGraphStore,
        embedder: BaseEmbedder,
        reranker: BaseReranker | None = None,
    ):
        self.vector_store = vector_store
        self.graph_store = graph_store
        self.embedder = embedder
        self.reranker = reranker

    def retrieve(self, query: str, top_k: int = 5, **kwargs) -> list[RetrievalResult]:
        # Step 1: 向量召回
        query_embedding = self.embedder.encode_query(query)
        vector_results = self.vector_store.search(query_embedding=query_embedding, top_k=20)

        # Step 2: 图遍历召回
        graph_chunks = self._graph_retrieve(query)

        # Step 3: 融合去重
        all_results = {}
        for c in vector_results:
            all_results[c.chunk_id] = RetrievalResult(
                content=c.content, score=c.score, metadata=c.metadata,
                chunk_id=c.chunk_id, source="vector"
            )
        for gc in graph_chunks:
            if gc.chunk_id not in all_results:
                all_results[gc.chunk_id] = gc

        merged = list(all_results.values())

        # Step 4: Rerank
        if self.reranker and merged:
            texts = [r.content for r in merged]
            reranked = self.reranker.rerank(query, texts, top_k=top_k)
            results = []
            for text, score in reranked:
                orig = next((r for r in merged if r.content == text), merged[0])
                orig.score = score
                orig.source = "hybrid"
                results.append(orig)
            return results

        merged.sort(key=lambda x: x.score, reverse=True)
        return merged[:top_k]

    def _graph_retrieve(self, query: str) -> list[RetrievalResult]:
        """从查询中提取实体，进行图遍历."""
        entities = self._extract_entities(query)
        results = []
        for entity in entities:
            node_id = self.graph_store.resolve_entity(entity)
            if node_id:
                subgraph = self.graph_store.traverse(node_id, max_hops=2)
                for path in subgraph:
                    for node in path.get("nodes", []):
                        name = node.get("name", "")
                        if name:
                            results.append(RetrievalResult(
                                content=f"图谱实体: {name}", score=0.5,
                                metadata={"entity": name, "labels": node.get("labels", [])},
                                source="graph"
                            ))
        return results

    @staticmethod
    def _extract_entities(query: str) -> list[str]:
        """简单实体提取（基于关键词匹配）."""
        import re
        entity_patterns = [
            r"([一-鿿]+(?:高速|公路|路段|大道|快速路))",
            r"([一-鿿]+(?:隧道|大桥|桥))",
            r"([一-鿿]+(?:收费站|服务区|立交))",
            r"([一-鿿]+(?:事故|拥堵|管制))",
        ]
        entities = []
        for pattern in entity_patterns:
            entities.extend(re.findall(pattern, query))
        return list(set(entities))

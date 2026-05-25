"""Cross-Encoder Reranker — 基于 BGE-Reranker."""

from .base import BaseReranker


class CrossEncoderReranker(BaseReranker):
    """基于 Cross-Encoder 的精排器."""

    def __init__(self, model_name: str = "BAAI/bge-reranker-v2-m3", device: str = "cpu"):
        from sentence_transformers import CrossEncoder
        self.model = CrossEncoder(model_name, max_length=512, device=device)

    def rerank(self, query: str, documents: list[str], top_k: int = 5) -> list[tuple[str, float]]:
        if not documents:
            return []
        pairs = [[query, doc] for doc in documents]
        scores = self.model.predict(pairs)
        doc_scores = [(doc, float(score)) for doc, score in zip(documents, scores)]
        doc_scores.sort(key=lambda x: x[1], reverse=True)
        return doc_scores[:top_k]

"""BGE 系列 Embedding 实现."""

from .base import BaseEmbedder


class BGEEmbedder(BaseEmbedder):
    """基于 sentence-transformers 的 BGE Embedding."""

    def __init__(self, model_name: str = "BAAI/bge-large-zh-v1.5", device: str = "cpu"):
        from sentence_transformers import SentenceTransformer
        self._model = SentenceTransformer(model_name, device=device)
        self._dimension = self._model.get_sentence_embedding_dimension()
        self._query_prefix = "为这个句子生成表示以用于检索相关文章："

    def encode(self, texts: list[str]) -> list[list[float]]:
        embeddings = self._model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        return embeddings.tolist()

    def encode_query(self, query: str) -> list[float]:
        prefixed = self._query_prefix + query
        embedding = self._model.encode([prefixed], normalize_embeddings=True)
        return embedding[0].tolist()

    @property
    def dimension(self) -> int:
        return self._dimension

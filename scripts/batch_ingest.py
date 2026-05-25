"""批量数据入库脚本."""

import sys
sys.path.insert(0, ".")

from config.settings import settings
from src.data_layer.embedders.bge_embedder import BGEEmbedder
from src.data_layer.stores.vector_store import MilvusVectorStore
from src.data_layer.pipeline import IndexingPipeline
from src.common.logger import setup_logging

setup_logging("INFO")


def main():
    data_dir = settings.data_dir
    print(f"Ingesting from: {data_dir}")

    print("Loading embedding model...")
    embedder = BGEEmbedder(model_name=settings.embedding_model, device=settings.embedding_device)

    print("Connecting to Milvus...")
    vector_store = MilvusVectorStore()
    vector_store.create_collection(dimension=embedder.dimension)

    pipeline = IndexingPipeline(embedder, vector_store)
    result = pipeline.run(data_dir)

    print(f"\n=== Ingestion Complete ===")
    print(f"Total files: {result.total_files}")
    print(f"Success: {result.success_files}")
    print(f"Total chunks: {result.total_chunks}")
    if result.failed_files:
        print(f"Failed: {result.failed_files}")


if __name__ == "__main__":
    main()

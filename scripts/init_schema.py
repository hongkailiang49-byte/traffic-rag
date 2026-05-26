"""初始化 Milvus Collection + Neo4j Schema."""

import sys
sys.path.insert(0, ".")

from config.settings import settings
from src.data_layer.stores.vector_store import MilvusVectorStore
from src.data_layer.stores.graph_store import Neo4jGraphStore
from src.data_layer.stores.user_store import UserStore
from src.common.logger import setup_logging

setup_logging("INFO")


def main():
    print("=== Initializing Vector Store ===")
    vs = MilvusVectorStore()
    vs.create_collection(dimension=settings.embedding_dimension)
    print(f"Collection '{settings.milvus_collection}' ready")

    print("\n=== Initializing Graph Store ===")
    gs = Neo4jGraphStore()
    gs.create_constraints()
    print("Graph constraints created")

    print("\n=== Initializing Chat History Schema ===")
    us = UserStore()
    us.create_indexes()
    print("Chat history constraints created")

    gs.close()
    us.close()
    print("\nSchema initialization complete!")


if __name__ == "__main__":
    main()

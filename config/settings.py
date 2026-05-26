"""Pydantic Settings — 全局配置统一入口."""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # === LLM Provider (mimo via OpenAI-compatible API) ===
    mimo_base_url: str = ""
    mimo_api_key: str = ""
    mimo_model: str = "mimo-v2.5"
    mimo_pro_model: str = "mimo-v2.5-pro"

    # === Vector DB ===
    milvus_host: str = "localhost"
    milvus_port: int = 19530
    milvus_collection: str = "traffic_knowledge"

    # === Graph DB ===
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = ""

    # === Redis ===
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""

    # === Auth ===
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480

    # === Embedding (local model) ===
    embedding_model: str = str(PROJECT_ROOT / "models" / "models--BAAI--bge-large-zh-v1.5" / "snapshots" / "79e7739b6ab944e86d6171e44d24c997fc1e0116")
    embedding_device: str = "cpu"
    embedding_dimension: int = 1024

    # === Reranker (local model) ===
    reranker_model: str = str(PROJECT_ROOT / "models" / "models--BAAI--bge-reranker-v2-m3" / "snapshots" / "953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e")
    reranker_device: str = "cpu"

    # === Application ===
    app_env: str = "development"
    app_log_level: str = "INFO"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    cors_origins: str = "*"

    # === Data Path ===
    data_dir: str = str(Path(__file__).parent.parent / "rag_information")
    sensitive_words_path: str = str(Path(__file__).parent.parent / "data" / "sensitive_words" / "traffic_words.txt")

    @property
    def redis_url(self) -> str:
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


settings = Settings()

"""自定义异常体系."""


class TrafficRAGError(Exception):
    """所有业务异常基类."""

    def __init__(self, message: str, code: str = "UNKNOWN_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


class DocumentParseError(TrafficRAGError):
    """文档解析失败."""

    def __init__(self, message: str):
        super().__init__(message, code="DOCUMENT_PARSE_ERROR")


class EmbeddingError(TrafficRAGError):
    """Embedding 生成失败."""

    def __init__(self, message: str):
        super().__init__(message, code="EMBEDDING_ERROR")


class VectorStoreError(TrafficRAGError):
    """向量数据库操作失败."""

    def __init__(self, message: str):
        super().__init__(message, code="VECTOR_STORE_ERROR")


class GraphStoreError(TrafficRAGError):
    """图数据库操作失败."""

    def __init__(self, message: str):
        super().__init__(message, code="GRAPH_STORE_ERROR")


class LLMGatewayError(TrafficRAGError):
    """LLM 调用失败."""

    def __init__(self, message: str):
        super().__init__(message, code="LLM_GATEWAY_ERROR")


class GuardrailBlockedError(TrafficRAGError):
    """安全层拦截."""

    def __init__(self, message: str, reason: str = ""):
        self.reason = reason
        super().__init__(message, code="GUARDRAIL_BLOCKED")


class SessionNotFoundError(TrafficRAGError):
    """会话不存在."""

    def __init__(self, session_id: str):
        super().__init__(f"Session not found: {session_id}", code="SESSION_NOT_FOUND")

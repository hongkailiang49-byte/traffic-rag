"""查询请求/响应模型."""

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000, description="用户问题")
    session_id: str = Field(default="", description="会话ID（多轮对话）")
    intent: str = Field(default="auto", description="意图：auto/regulatory/spatiotemporal/graph_rag/emergency")
    filters: dict = Field(default_factory=dict, description="过滤条件")
    top_k: int = Field(default=5, ge=1, le=20)


class QueryResponse(BaseModel):
    answer: str
    intent: str
    sources: list[dict]
    session_id: str = ""
    phase: str = ""  # 对话状态（应急场景用）
    clarification: str = ""  # 反问内容（应急场景用）


class IngestRequest(BaseModel):
    directory: str = Field(default="", description="数据目录路径（空则用默认路径）")


class IngestResponse(BaseModel):
    total_files: int
    total_chunks: int
    success_files: int
    failed_files: list[str]
    message: str

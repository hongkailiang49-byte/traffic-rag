"""统一查询入口 — /api/v1/query."""

import uuid
from fastapi import APIRouter, Depends
from src.api.schemas.query import QueryRequest, QueryResponse
from src.api.middleware.auth import verify_token
from src.common.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1", tags=["query"])


def _get_app_state():
    from src.api.main import app_state
    return app_state

def _get_engine():
    """延迟初始化 RAG Engine（避免导入时初始化模型）."""
    return _get_app_state().get("engine")


@router.post("/query", response_model=QueryResponse)
async def query(req: QueryRequest, user: dict = Depends(verify_token)):
    """统一查询接口."""
    engine = _get_engine()
    if not engine:
        return QueryResponse(answer="系统正在初始化，请稍后重试", intent="error", sources=[])

    session_id = req.session_id or str(uuid.uuid4())[:8]

    result = await engine.query(
        question=req.question,
        session_id=session_id,
        intent=req.intent,
        filters=req.filters,
        top_k=req.top_k,
        user_context=user,
    )

    # 记录用户查询行为
    app_state = _get_app_state()
    user_store = app_state.get("user_store")
    if user_store and user.get("user_id") and user["user_id"] != "dev_user":
        try:
            user_store.record_query(user["user_id"], req.question, result.get("intent", ""))
        except Exception as e:
            logger.warning(f"Failed to record query: {e}")

    return QueryResponse(
        answer=result["answer"],
        intent=result.get("intent", ""),
        sources=result.get("sources", []),
        session_id=session_id,
        phase=result.get("phase", ""),
        clarification=result.get("clarification", ""),
    )

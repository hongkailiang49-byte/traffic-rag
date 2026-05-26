"""会话管理 — /api/v1/session."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api.middleware.auth import verify_token
from src.common.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1", tags=["session"])


class SessionRequest(BaseModel):
    session_id: str
    message: str


class SessionResponse(BaseModel):
    session_id: str
    phase: str
    response: str
    missing_slots: list[str] = []
    collected_slots: dict = {}


class MessageOut(BaseModel):
    role: str
    content: str
    seq: int
    created_at: str


class SessionOut(BaseModel):
    session_id: str
    intent: str
    created_at: str
    message_count: int
    first_message: str = ""


@router.post("/session/message", response_model=SessionResponse)
async def session_message(req: SessionRequest, user: dict = Depends(verify_token)):
    """应急调度多轮对话."""
    from src.api.main import app_state

    dialogue_mgr = app_state.get("dialogue_manager")
    if not dialogue_mgr:
        return SessionResponse(session_id=req.session_id, phase="error", response="对话系统未初始化")

    result = await dialogue_mgr.process(req.session_id, req.message)

    return SessionResponse(
        session_id=req.session_id,
        phase=result.get("phase", ""),
        response=result.get("dispatch_order", "") or result.get("clarification", ""),
        missing_slots=result.get("missing_slots", []),
        collected_slots=result.get("collected_slots", {}),
    )


@router.get("/sessions", response_model=list[SessionOut])
async def list_sessions(user: dict = Depends(verify_token)):
    """获取当前用户的所有会话."""
    from src.api.main import app_state

    user_store = app_state.get("user_store")
    if not user_store:
        return []

    email = user.get("user_id")
    if not email or email == "dev_user":
        return []

    sessions = user_store.get_user_sessions(email)
    return [
        SessionOut(
            session_id=s["session_id"],
            intent=s.get("intent", ""),
            created_at=s.get("created_at", ""),
            message_count=s.get("message_count", 0),
            first_message=s.get("first_message", "") or "",
        )
        for s in sessions
    ]


@router.get("/sessions/{session_id}/messages", response_model=list[MessageOut])
async def get_session_messages(session_id: str, user: dict = Depends(verify_token)):
    """获取指定会话的聊天记录."""
    from src.api.main import app_state

    user_store = app_state.get("user_store")
    if not user_store:
        return []

    messages = user_store.get_chat_history(session_id)
    return [
        MessageOut(
            role=m["role"],
            content=m["content"],
            seq=m["seq"],
            created_at=m.get("created_at", ""),
        )
        for m in messages
    ]


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str, user: dict = Depends(verify_token)):
    """删除指定会话及其所有消息."""
    from src.api.main import app_state

    user_store = app_state.get("user_store")
    if not user_store:
        return {"ok": False, "error": "服务未初始化"}

    user_store.delete_session(session_id)
    return {"ok": True}

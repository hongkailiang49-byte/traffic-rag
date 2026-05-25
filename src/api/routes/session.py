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

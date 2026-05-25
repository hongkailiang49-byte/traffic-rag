"""Redis Session 存储."""

import json
import redis
from config.settings import settings
from src.common.logger import get_logger

logger = get_logger(__name__)


class SessionStore:
    """基于 Redis 的会话存储."""

    def __init__(self, redis_url: str | None = None):
        self._redis = redis.from_url(redis_url or settings.redis_url, decode_responses=True)

    def create_session(self, session_id: str, ttl: int = 3600) -> dict:
        """创建新会话."""
        session_data = {
            "session_id": session_id,
            "messages": [],
            "state": {},
            "intent": "",
        }
        self._redis.setex(f"session:{session_id}", ttl, json.dumps(session_data, ensure_ascii=False))
        return session_data

    def get_session(self, session_id: str) -> dict | None:
        """获取会话."""
        data = self._redis.get(f"session:{session_id}")
        return json.loads(data) if data else None

    def update_session(self, session_id: str, session_data: dict, ttl: int = 3600) -> None:
        """更新会话."""
        self._redis.setex(f"session:{session_id}", ttl, json.dumps(session_data, ensure_ascii=False))

    def add_message(self, session_id: str, role: str, content: str) -> None:
        """向会话添加消息."""
        session = self.get_session(session_id)
        if not session:
            session = self.create_session(session_id)
        session["messages"].append({"role": role, "content": content})
        self.update_session(session_id, session)

    def get_history(self, session_id: str, limit: int = 10) -> list[dict]:
        """获取会话历史."""
        session = self.get_session(session_id)
        if not session:
            return []
        return session["messages"][-limit:]

    def delete_session(self, session_id: str) -> None:
        """删除会话."""
        self._redis.delete(f"session:{session_id}")

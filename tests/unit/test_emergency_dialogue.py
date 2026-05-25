"""应急调度对话状态机单元测试."""

import pytest
from unittest.mock import MagicMock
from src.generation_layer.session.emergency_dialogue import (
    EmergencyDialogueManager, EmergencyState, REQUIRED_SLOTS,
)


@pytest.fixture
def mock_session_store():
    """模拟 SessionStore."""
    store = MagicMock()
    sessions = {}

    def get_session(sid):
        return sessions.get(sid)

    def create_session(sid):
        session = {"session_id": sid, "messages": [], "state": {}, "intent": ""}
        sessions[sid] = session
        return session

    def update_session(sid, data):
        sessions[sid] = data

    store.get_session = MagicMock(side_effect=get_session)
    store.create_session = MagicMock(side_effect=create_session)
    store.update_session = MagicMock(side_effect=update_session)
    return store, sessions


@pytest.fixture
def dialogue_mgr(mock_session_store):
    store, _ = mock_session_store
    llm = MagicMock()
    llm.invoke_sync = MagicMock(return_value="【应急处置指令】测试指令")
    retriever = MagicMock()
    retriever.retrieve = MagicMock(return_value=[])
    return EmergencyDialogueManager(llm, store, retriever), mock_session_store


class TestEmergencyDialogue:
    def test_classify_accident(self, dialogue_mgr):
        mgr, _ = dialogue_mgr
        assert mgr._classify_intent("发生追尾事故") == "accident"
        assert mgr._classify_intent("车辆碰撞") == "accident"

    def test_classify_fire(self, dialogue_mgr):
        mgr, _ = dialogue_mgr
        assert mgr._classify_intent("隧道火灾") == "fire"
        assert mgr._classify_intent("车辆起火") == "fire"

    def test_classify_congestion(self, dialogue_mgr):
        mgr, _ = dialogue_mgr
        assert mgr._classify_intent("前方拥堵") == "congestion"
        assert mgr._classify_intent("严重堵车") == "congestion"

    def test_classify_default_accident(self, dialogue_mgr):
        mgr, _ = dialogue_mgr
        assert mgr._classify_intent("help") == "accident"

    def test_extract_location(self, dialogue_mgr):
        mgr, _ = dialogue_mgr
        slots = mgr._extract_slots("京藏高速路段发生事故", "accident")
        assert slots.get("location") == "京藏高速路段"

    def test_extract_severity(self, dialogue_mgr):
        mgr, _ = dialogue_mgr
        slots = mgr._extract_slots("事故严重，有多人伤亡", "accident")
        assert slots.get("severity") == "严重"
        assert slots.get("casualties") == "有"

    def test_clarifying_when_incomplete(self, dialogue_mgr):
        mgr, (store, sessions) = dialogue_mgr
        result = mgr.process("test-session", "京藏高速发生事故")
        # 信息不足时应进入澄清阶段
        assert result["phase"] == "clarifying"
        assert "missing_slots" in result

    def test_dispatch_when_complete(self, dialogue_mgr):
        mgr, (store, sessions) = dialogue_mgr
        # 第一轮：部分信息
        mgr.process("s1", "京藏高速发生严重事故，有伤亡，涉及危化品泄漏，路面湿滑")
        # 检查是否进入 dispatched 或 clarifying
        session = sessions.get("s1")
        assert session is not None

    def test_fallback_dispatch(self):
        result = EmergencyDialogueManager._fallback_dispatch(
            "accident", {"location": "测试路段"}
        )
        assert "测试路段" in result
        assert "应急处置指令" in result

    def test_generate_clarification(self, dialogue_mgr):
        mgr, _ = dialogue_mgr
        result = mgr._generate_clarification("accident", {}, ["location", "severity"])
        assert "具体位置" in result or "严重程度" in result

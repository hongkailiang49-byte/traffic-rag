"""API 路由集成测试."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient


@pytest.fixture
def mock_app_state():
    """模拟 app_state 中的组件."""
    engine = MagicMock()
    engine.query = AsyncMock(return_value={
        "answer": "测试回答",
        "intent": "regulatory",
        "sources": [{"content": "来源片段", "score": 0.9, "source": "vector"}],
    })

    pipeline = MagicMock()
    pipeline.run = MagicMock(return_value=MagicMock(
        total_files=10, total_chunks=50, success_files=10, failed_files=[]
    ))

    dialogue_mgr = MagicMock()
    dialogue_mgr.process = MagicMock(return_value={
        "phase": "clarifying",
        "clarification": "请补充位置信息",
        "missing_slots": ["location"],
        "collected_slots": {},
    })

    return engine, pipeline, dialogue_mgr


@pytest.fixture
def client(mock_app_state):
    """创建测试客户端."""
    engine, pipeline, dialogue_mgr = mock_app_state
    from src.api.main import app, app_state

    app_state["engine"] = engine
    app_state["pipeline"] = pipeline
    app_state["dialogue_manager"] = dialogue_mgr

    # 强制开发模式跳过认证
    with patch("src.api.middleware.auth.settings") as mock_settings:
        mock_settings.app_env = "development"
        mock_settings.jwt_secret_key = "test-key"
        mock_settings.jwt_algorithm = "HS256"
        mock_settings.jwt_expire_minutes = 480
        yield TestClient(app)


class TestHealthEndpoint:
    def test_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"


class TestQueryEndpoint:
    def test_query_success(self, client):
        resp = client.post("/api/v1/query", json={
            "question": "公路工程技术标准是什么？",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "answer" in data
        assert "intent" in data
        assert "sources" in data

    def test_query_with_session(self, client):
        resp = client.post("/api/v1/query", json={
            "question": "JTG B01规范",
            "session_id": "test-123",
        })
        assert resp.status_code == 200

    def test_query_with_filters(self, client):
        resp = client.post("/api/v1/query", json={
            "question": "法规查询",
            "filters": {"authority": "交通运输部", "year_from": 2020},
        })
        assert resp.status_code == 200

    def test_query_empty_question_rejected(self, client):
        resp = client.post("/api/v1/query", json={"question": ""})
        assert resp.status_code == 422

    def test_query_too_long_rejected(self, client):
        resp = client.post("/api/v1/query", json={"question": "x" * 2001})
        assert resp.status_code == 422


class TestSessionEndpoint:
    def test_session_message(self, client):
        resp = client.post("/api/v1/session/message", json={
            "session_id": "s1",
            "message": "京藏高速发生事故",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "phase" in data
        assert "response" in data


class TestIngestEndpoint:
    def test_ingest(self, client):
        resp = client.post("/api/v1/ingest", json={})
        assert resp.status_code == 200
        data = resp.json()
        assert "total_files" in data
        assert "message" in data

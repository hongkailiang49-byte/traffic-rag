"""检索器单元测试."""

import pytest
from src.retrieval_layer.intent_router import IntentRouter


class TestIntentRouter:
    def test_regulatory_keywords(self, intent_router):
        assert intent_router.classify("公路工程技术标准是什么") == "regulatory"
        assert intent_router.classify("JTG B01规范内容") == "regulatory"

    def test_spatiotemporal_keywords(self, intent_router):
        assert intent_router.classify("京藏高速实时流量") == "spatiotemporal"
        assert intent_router.classify("当前拥堵情况") == "spatiotemporal"

    def test_emergency_keywords(self, intent_router):
        assert intent_router.classify("隧道火灾报警") == "emergency"
        assert intent_router.classify("危险品泄漏处置") == "emergency"

    def test_graph_keywords(self, intent_router):
        assert intent_router.classify("事故对周边路段的连锁影响") == "graph_rag"

    def test_default_to_regulatory(self, intent_router):
        assert intent_router.classify("你好") == "regulatory"

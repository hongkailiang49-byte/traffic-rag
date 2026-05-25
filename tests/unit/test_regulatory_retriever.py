"""法规检索器单元测试 — 过滤表达式构建."""

import pytest
from src.retrieval_layer.retrievers.regulatory import RegulatoryRetriever


class TestBuildFilterExpr:
    def test_empty_filters(self):
        assert RegulatoryRetriever._build_filter_expr({}) == ""

    def test_year_from_int(self):
        result = RegulatoryRetriever._build_filter_expr({"year_from": 2020})
        assert "year >= 2020" in result

    def test_year_from_string(self):
        result = RegulatoryRetriever._build_filter_expr({"year_from": "2020"})
        assert "year >= 2020" in result

    def test_year_from_invalid_string(self):
        result = RegulatoryRetriever._build_filter_expr({"year_from": "abc"})
        assert result == ""

    def test_authority_sanitized(self):
        result = RegulatoryRetriever._build_filter_expr({"authority": "交通运输部"})
        assert "authority == '交通运输部'" in result

    def test_authority_injection_blocked(self):
        result = RegulatoryRetriever._build_filter_expr({"authority": "test' OR 1==1 --"})
        assert "OR" not in result
        assert "test" in result

    def test_region(self):
        result = RegulatoryRetriever._build_filter_expr({"region": "北京"})
        assert "region in ['全国', '北京']" in result

    def test_category(self):
        result = RegulatoryRetriever._build_filter_expr({"category": "应急预案"})
        assert "category == '应急预案'" in result

    def test_multiple_filters(self):
        result = RegulatoryRetriever._build_filter_expr({
            "year_from": 2020,
            "authority": "交通运输部",
            "region": "全国",
        })
        assert "year >= 2020" in result
        assert "authority" in result
        assert "region" in result
        assert " and " in result

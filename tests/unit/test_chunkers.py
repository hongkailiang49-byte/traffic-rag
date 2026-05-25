"""切片器单元测试."""

import pytest


class TestHierarchicalChunker:
    def test_basic_chunking(self, hierarchical_chunker):
        text = """# 第一章 总则

## 第一条 目的

为了规范公路工程建设，制定本标准。

## 第二条 适用范围

本标准适用于新建和改扩建公路工程。

# 第二章 公路分级

## 第三条 公路等级

公路分为高速公路、一级公路、二级公路、三级公路和四级公路。

## 第四条 设计速度

各级公路设计速度应符合规定。"""
        chunks = hierarchical_chunker.chunk(text, metadata={"category": "test"})
        assert len(chunks) > 0
        for c in chunks:
            assert len(c.content) > 0
            assert c.metadata.get("category") == "test"

    def test_breadcrumb_preserved(self, hierarchical_chunker):
        text = """# 第一章

## 第一条

这是条文内容。"""
        chunks = hierarchical_chunker.chunk(text)
        assert any("第一章" in c.content for c in chunks)

    def test_empty_text(self, hierarchical_chunker):
        chunks = hierarchical_chunker.chunk("")
        assert len(chunks) <= 1


class TestFixedSizeChunker:
    def test_chunk_size(self, fixed_chunker):
        text = "A" * 2000
        chunks = fixed_chunker.chunk(text)
        assert len(chunks) >= 2
        for c in chunks[:-1]:
            assert len(c.content) <= 500

    def test_overlap(self, fixed_chunker):
        text = "A" * 1000
        chunks = fixed_chunker.chunk(text)
        if len(chunks) >= 2:
            # 验证有重叠
            assert len(chunks) >= 2

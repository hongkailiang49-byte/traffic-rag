"""测试 Fixtures."""

import pytest
from src.data_layer.chunkers.hierarchical import HierarchicalMarkdownChunker
from src.data_layer.chunkers.fixed_size import FixedSizeChunker
from src.data_layer.parsers.markdown_parser import MarkdownParser
from src.guardrails.input_guard import InputGuard, AhoCorasickFilter
from src.guardrails.output_guard import OutputGuard
from src.retrieval_layer.intent_router import IntentRouter


@pytest.fixture
def hierarchical_chunker():
    return HierarchicalMarkdownChunker(max_chunk_size=1000, min_chunk_size=50)


@pytest.fixture
def fixed_chunker():
    return FixedSizeChunker(chunk_size=500, overlap=100)


@pytest.fixture
def markdown_parser():
    return MarkdownParser()


@pytest.fixture
def input_guard():
    return InputGuard()


@pytest.fixture
def output_guard():
    return OutputGuard()


@pytest.fixture
def intent_router():
    return IntentRouter()

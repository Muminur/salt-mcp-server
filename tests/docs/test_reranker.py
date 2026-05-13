"""Tests for the optional bge-reranker-base with passthrough fallback."""
from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

from salt_cisco_mcp.docs.reranker import Reranker, RerankResult


def _make_candidates(n: int = 5) -> list[tuple[str, float]]:
    """Return (text, score) tuples in descending BM25 score order."""
    return [(f"chunk text {i}", float(n - i)) for i in range(n)]


def test_reranker_passthrough_when_unavailable() -> None:
    """Reranker.rerank() returns input order when fastembed is missing."""
    with patch.dict(sys.modules, {"fastembed": None}):
        rr = Reranker(model="BAAI/bge-reranker-base")
        candidates = _make_candidates(3)
        results = rr.rerank("bgp neighbors", candidates)

    assert len(results) == 3
    for i, r in enumerate(results):
        assert r.text == candidates[i][0]
        assert r.original_score == candidates[i][1]


def test_reranker_available_returns_false_when_missing() -> None:
    """available() is False when fastembed is not installed."""
    with patch.dict(sys.modules, {"fastembed": None}):
        rr = Reranker(model="BAAI/bge-reranker-base")
        assert rr.available() is False


def test_reranker_available_with_mock() -> None:
    """available() is True when fastembed reranker is importable."""
    mock_fe = MagicMock()
    mock_fe.FlagEmbedding = MagicMock()

    with patch.dict(sys.modules, {"fastembed": mock_fe}):
        rr = Reranker(model="BAAI/bge-reranker-base")
        assert rr.available() is True


def test_reranker_sorts_by_rerank_score() -> None:
    """rerank() returns RerankResult list sorted by descending rerank_score."""
    candidates = _make_candidates(4)

    mock_rerank_model = MagicMock()
    mock_rerank_model.rerank.return_value = [
        MagicMock(score=0.9),
        MagicMock(score=0.3),
        MagicMock(score=0.7),
        MagicMock(score=0.5),
    ]

    mock_fe = MagicMock()
    mock_fe.FlagEmbedding.return_value = mock_rerank_model

    with patch.dict(sys.modules, {"fastembed": mock_fe}):
        rr = Reranker(model="BAAI/bge-reranker-base")
        results = rr.rerank("bgp neighbors", candidates)

    assert len(results) == 4
    scores = [r.rerank_score for r in results]
    assert scores == sorted(scores, reverse=True)


def test_reranker_result_fields() -> None:
    """RerankResult has text, original_score, and rerank_score fields."""
    r = RerankResult(text="hello", original_score=1.0, rerank_score=0.8)
    assert r.text == "hello"
    assert r.original_score == 1.0
    assert r.rerank_score == 0.8


def test_reranker_empty_candidates() -> None:
    """rerank() with empty candidates returns empty list without error."""
    with patch.dict(sys.modules, {"fastembed": None}):
        rr = Reranker(model="BAAI/bge-reranker-base")
        results = rr.rerank("any query", [])
    assert results == []

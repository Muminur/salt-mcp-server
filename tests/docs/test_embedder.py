"""Tests for the fastembed-backed embedder with graceful BM25-only fallback."""
from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

import pytest

from salt_cisco_mcp.docs.embedder import Embedder, EmbedderUnavailableError


def test_embedder_unavailable_when_fastembed_missing() -> None:
    """Embedder.available() returns False when fastembed is not installed."""
    with patch.dict(sys.modules, {"fastembed": None}):
        emb = Embedder(model="BAAI/bge-small-en-v1.5", device="cpu")
        assert emb.available() is False


def test_embedder_embed_raises_when_unavailable() -> None:
    """embed() raises EmbedderUnavailableError when fastembed is missing."""
    with patch.dict(sys.modules, {"fastembed": None}):
        emb = Embedder(model="BAAI/bge-small-en-v1.5", device="cpu")
        with pytest.raises(EmbedderUnavailableError):
            emb.embed("test query")


def test_embedder_embed_batch_raises_when_unavailable() -> None:
    """embed_batch() raises EmbedderUnavailableError when fastembed is missing."""
    with patch.dict(sys.modules, {"fastembed": None}):
        emb = Embedder(model="BAAI/bge-small-en-v1.5", device="cpu")
        with pytest.raises(EmbedderUnavailableError):
            emb.embed_batch(["text one", "text two"])


def test_embedder_embed_returns_list_of_floats() -> None:
    """embed() returns a list[float] of fixed dimension when fastembed is mocked."""
    dim = 384
    mock_vec = [0.1] * dim

    mock_model = MagicMock()
    mock_model.embed.return_value = iter([[mock_vec]])

    mock_fe = MagicMock()
    mock_fe.TextEmbedding.return_value = mock_model

    with patch.dict(sys.modules, {"fastembed": mock_fe}):
        emb = Embedder(model="BAAI/bge-small-en-v1.5", device="cpu")
        result = emb.embed("napalm bgp neighbors")

    assert isinstance(result, list)
    assert len(result) == dim
    assert all(isinstance(v, float) for v in result)


def test_embedder_embed_batch_returns_list_of_lists() -> None:
    """embed_batch() returns list[list[float]], one vector per input text."""
    dim = 384
    texts = ["text one", "text two", "text three"]
    mock_vecs = [[float(i)] * dim for i in range(len(texts))]

    mock_model = MagicMock()
    mock_model.embed.return_value = iter([mock_vecs])

    mock_fe = MagicMock()
    mock_fe.TextEmbedding.return_value = mock_model

    with patch.dict(sys.modules, {"fastembed": mock_fe}):
        emb = Embedder(model="BAAI/bge-small-en-v1.5", device="cpu")
        results = emb.embed_batch(texts)

    assert len(results) == len(texts)
    for vec in results:
        assert isinstance(vec, list)
        assert len(vec) == dim


def test_embedder_available_with_mock_fastembed() -> None:
    """available() returns True when fastembed can be imported."""
    mock_fe = MagicMock()
    mock_fe.TextEmbedding.return_value = MagicMock()

    with patch.dict(sys.modules, {"fastembed": mock_fe}):
        emb = Embedder(model="BAAI/bge-small-en-v1.5", device="cpu")
        assert emb.available() is True


def test_embedder_model_name_stored() -> None:
    """Embedder stores the model name passed at construction."""
    emb = Embedder(model="BAAI/bge-small-en-v1.5", device="cpu")
    assert emb.model == "BAAI/bge-small-en-v1.5"

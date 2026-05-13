"""Fastembed-backed text embedder with graceful BM25-only fallback."""
from __future__ import annotations

from typing import Any


class EmbedderUnavailableError(RuntimeError):
    """Raised when embed() is called but fastembed is not installed."""


class Embedder:
    """Wraps fastembed.TextEmbedding; degrades gracefully when fastembed is absent."""

    def __init__(self, model: str, device: str = "cpu") -> None:
        self.model = model
        self._device = device
        self._inner: Any = None
        self._checked = False

    def _ensure(self) -> bool:
        if self._checked:
            return self._inner is not None
        self._checked = True
        try:
            import fastembed

            self._inner = fastembed.TextEmbedding(model_name=self.model)
            return True
        except (ImportError, Exception):
            return False

    def available(self) -> bool:
        """Return True if fastembed is importable and the model loaded."""
        return self._ensure()

    def embed(self, text: str) -> list[float]:
        """Return a single embedding vector for *text*."""
        if not self._ensure():
            raise EmbedderUnavailableError("fastembed is not installed")
        for batch in self._inner.embed([text]):
            return [float(v) for v in batch[0]]
        raise EmbedderUnavailableError("embed produced no output")

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Return one embedding vector per text in *texts*."""
        if not self._ensure():
            raise EmbedderUnavailableError("fastembed is not installed")
        results: list[list[float]] = []
        for batch in self._inner.embed(texts):
            for vec in batch:
                results.append([float(v) for v in vec])
        return results

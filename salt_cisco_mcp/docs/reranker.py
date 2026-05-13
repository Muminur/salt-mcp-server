"""Optional bge-reranker-base wrapper with passthrough fallback."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class RerankResult:
    text: str
    original_score: float
    rerank_score: float


class Reranker:
    """Wraps fastembed reranker; returns original order when fastembed is absent."""

    def __init__(self, model: str) -> None:
        self.model = model
        self._inner: Any = None
        self._checked = False

    def _ensure(self) -> bool:
        if self._checked:
            return self._inner is not None
        self._checked = True
        try:
            import fastembed  # type: ignore[import-not-found]

            self._inner = fastembed.FlagEmbedding(model_name=self.model)
            return True
        except (ImportError, AttributeError, Exception):
            return False

    def available(self) -> bool:
        """Return True if fastembed reranker can be loaded."""
        return self._ensure()

    def rerank(
        self,
        query: str,
        candidates: list[tuple[str, float]],
    ) -> list[RerankResult]:
        """Re-rank *candidates* for *query*.

        *candidates* is a list of (text, original_score) tuples.
        Returns RerankResult list sorted by descending rerank_score.
        When unavailable, rerank_score mirrors original_score (passthrough).
        """
        if not candidates:
            return []

        if not self._ensure():
            return [
                RerankResult(text=text, original_score=score, rerank_score=score)
                for text, score in candidates
            ]

        texts = [text for text, _ in candidates]
        rerank_scores: list[float] = []
        try:
            for item in self._inner.rerank(query, texts):
                rerank_scores.append(float(item.score))
        except Exception:  # noqa: BLE001
            return [
                RerankResult(text=text, original_score=score, rerank_score=score)
                for text, score in candidates
            ]

        results = [
            RerankResult(
                text=candidates[i][0],
                original_score=candidates[i][1],
                rerank_score=rerank_scores[i] if i < len(rerank_scores) else candidates[i][1],
            )
            for i in range(len(candidates))
        ]
        results.sort(key=lambda r: r.rerank_score, reverse=True)
        return results

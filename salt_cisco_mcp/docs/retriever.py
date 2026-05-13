from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from salt_cisco_mcp.docs.embedder import Embedder
from salt_cisco_mcp.docs.store import DocStore


@dataclass
class SearchResult:
    chunk_id: int
    text: str
    anchor: str
    heading: str
    kind: str
    score: float
    doc_hash: str
    url: str = ""


def bm25_search(store: DocStore, query: str, limit: int = 10) -> list[SearchResult]:
    """Search using FTS5 BM25 ranking. Returns [] on empty query or error."""
    if not query or not query.strip():
        return []
    try:
        rows = store.fts_search(query, limit)
    except sqlite3.Error:
        return []

    results: list[SearchResult] = []
    for row in rows:
        results.append(
            SearchResult(
                chunk_id=int(row.get("id", 0)),
                text=str(row.get("text", "")),
                anchor=str(row.get("anchor", "")),
                heading=str(row.get("heading", "")),
                kind=str(row.get("kind", "")),
                score=-float(row.get("rank", 0.0)),
                doc_hash=str(row.get("doc_hash", "")),
                url=str(row.get("url", "")),
            )
        )
    return results


def hybrid_search(
    store: DocStore,
    query: str,
    embedder: Embedder,
    limit: int = 10,
    rrf_k: int = 60,
) -> list[SearchResult]:
    """Hybrid BM25 + vector search with Reciprocal Rank Fusion.

    Falls back to BM25-only when the embedder is unavailable or vec schema is absent.
    """
    bm25_results = bm25_search(store, query, limit=limit)

    vec_chunk_ids: list[int] = []
    if embedder.available():
        try:
            query_vec = embedder.embed(query)
            vec_rows = store.vec_search(query_vec, limit=limit)
            vec_chunk_ids = [row["chunk_id"] for row in vec_rows]
        except Exception:
            pass

    if not vec_chunk_ids:
        return bm25_results

    # Build RRF score map: sum reciprocal ranks from both lists
    rrf_scores: dict[int, float] = {}
    for rank, r in enumerate(bm25_results):
        rrf_scores[r.chunk_id] = rrf_scores.get(r.chunk_id, 0.0) + 1.0 / (rrf_k + rank + 1)
    for rank, cid in enumerate(vec_chunk_ids):
        rrf_scores[cid] = rrf_scores.get(cid, 0.0) + 1.0 / (rrf_k + rank + 1)

    # Collect all unique SearchResult objects, prefer from bm25 (already fetched)
    by_id: dict[int, SearchResult] = {r.chunk_id: r for r in reversed(bm25_results)}
    for cid in vec_chunk_ids:
        if cid not in by_id:
            row = store.get_chunk_by_id(cid)
            if row:
                by_id[cid] = SearchResult(
                    chunk_id=cid,
                    text=str(row.get("text", "")),
                    anchor=str(row.get("anchor", "")),
                    heading=str(row.get("heading", "")),
                    kind=str(row.get("kind", "")),
                    score=rrf_scores.get(cid, 0.0),
                    doc_hash=str(row.get("doc_hash", "")),
                    url=str(row.get("url", "")),
                )

    merged = sorted(by_id.values(), key=lambda r: rrf_scores.get(r.chunk_id, 0.0), reverse=True)
    return merged[:limit]


def trim_to_budget(results: list[SearchResult], token_budget: int) -> list[SearchResult]:
    """Keep results in order until token budget is exhausted."""
    kept: list[SearchResult] = []
    accumulated = 0
    for r in results:
        tokens = len(r.text.split())
        if accumulated + tokens > token_budget:
            break
        kept.append(r)
        accumulated += tokens
    return kept

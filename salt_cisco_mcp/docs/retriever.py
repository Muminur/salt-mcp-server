from __future__ import annotations

import sqlite3
from dataclasses import dataclass

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
        results.append(SearchResult(
            chunk_id=int(row.get("id", 0)),
            text=str(row.get("text", "")),
            anchor=str(row.get("anchor", "")),
            heading=str(row.get("heading", "")),
            kind=str(row.get("kind", "")),
            score=-float(row.get("rank", 0.0)),
            doc_hash=str(row.get("doc_hash", "")),
        ))
    return results


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

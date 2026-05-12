from __future__ import annotations

import hashlib

from salt_cisco_mcp.docs.chunker import Chunk
from salt_cisco_mcp.docs.normalizer import PageMeta
from salt_cisco_mcp.docs.store import DocStore


def compute_doc_hash(text: str) -> str:
    """SHA-256 hex digest of text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def index_page(store: DocStore, chunks: list[Chunk], meta: PageMeta) -> int:
    """Upsert all chunks into store. Returns count indexed."""
    if not chunks:
        return 0
    combined_text = " ".join(c.text for c in chunks)
    doc_hash = compute_doc_hash(combined_text)
    count = 0
    for chunk in chunks:
        store.upsert_chunk(chunk, meta, doc_hash)
        count += 1
    return count

from __future__ import annotations

import sqlite3
from typing import Any

from salt_cisco_mcp.docs.chunker import Chunk
from salt_cisco_mcp.docs.normalizer import PageMeta

_SCHEMA_VEC = """
CREATE VIRTUAL TABLE IF NOT EXISTS chunks_vec USING vec0(
    chunk_id INTEGER PRIMARY KEY,
    embedding float[{dim}]
);
"""

_SCHEMA_CHUNKS = """
CREATE TABLE IF NOT EXISTS chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT NOT NULL,
    anchor TEXT NOT NULL,
    heading TEXT NOT NULL,
    kind TEXT NOT NULL,
    salt_version TEXT NOT NULL,
    text TEXT NOT NULL,
    token_count INTEGER NOT NULL,
    doc_hash TEXT NOT NULL,
    UNIQUE(url, anchor)
);
"""

_SCHEMA_FTS = """
CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
    text, anchor, heading, content=chunks, content_rowid=id
);
"""

_MAX_QUERY_LEN = 4096


class DocStore:
    def __init__(self, db_path: str) -> None:
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row

    def init_schema(self) -> None:
        cur = self._conn.cursor()
        cur.executescript(_SCHEMA_CHUNKS + _SCHEMA_FTS)
        self._conn.commit()

    def upsert_chunk(self, chunk: Chunk, meta: PageMeta, doc_hash: str) -> int:
        cur = self._conn.cursor()

        # Fetch existing row so we can remove its OLD tokens from FTS before updating.
        cur.execute(
            "SELECT id, text, anchor, heading FROM chunks WHERE url=? AND anchor=?",
            (meta.url, chunk.anchor),
        )
        existing = cur.fetchone()

        if existing is not None:
            old_id = int(existing[0])
            old_text = str(existing[1])
            old_anchor = str(existing[2])
            old_heading = str(existing[3])
            # Remove OLD FTS entry (must use OLD values, not incoming chunk values).
            cur.execute(
                "INSERT INTO chunks_fts(chunks_fts, rowid, text, anchor, heading) "
                "VALUES('delete', ?, ?, ?, ?)",
                (old_id, old_text, old_anchor, old_heading),
            )
            cur.execute(
                "UPDATE chunks SET heading=?, kind=?, salt_version=?, text=?, "
                "token_count=?, doc_hash=? WHERE id=?",
                (
                    chunk.heading,
                    chunk.kind,
                    meta.salt_version,
                    chunk.text,
                    chunk.token_count,
                    doc_hash,
                    old_id,
                ),
            )
            row_id = old_id
        else:
            cols = "(url, anchor, heading, kind, salt_version, text, token_count, doc_hash)"
            cur.execute(
                f"INSERT INTO chunks{cols} VALUES(?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    meta.url,
                    chunk.anchor,
                    chunk.heading,
                    chunk.kind,
                    meta.salt_version,
                    chunk.text,
                    chunk.token_count,
                    doc_hash,
                ),
            )
            row_id = cur.lastrowid if cur.lastrowid is not None else 0

        cur.execute(
            "INSERT INTO chunks_fts(rowid, text, anchor, heading) VALUES(?, ?, ?, ?)",
            (row_id, chunk.text, chunk.anchor, chunk.heading),
        )
        self._conn.commit()
        return row_id

    def get_chunk_by_id(self, chunk_id: int) -> dict[str, Any] | None:
        cur = self._conn.cursor()
        cur.execute("SELECT * FROM chunks WHERE id=?", (chunk_id,))
        row = cur.fetchone()
        if row is None:
            return None
        return dict(row)

    def fts_search(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        if not query or not query.strip():
            return []
        if len(query) > _MAX_QUERY_LEN:
            return []
        cur = self._conn.cursor()
        # Build per-token prefix query: "salt module" → "salt"* "module"*
        # This avoids the "phrase"* multi-word FTS5 syntax error.
        tokens = [t.replace('"', '""') for t in query.split() if t]
        if not tokens:
            return []
        fts_query = " ".join(f'"{t}"*' for t in tokens)
        try:
            cur.execute(
                "SELECT c.*, f.rank FROM chunks c "
                "JOIN chunks_fts f ON c.id = f.rowid "
                "WHERE chunks_fts MATCH ? ORDER BY rank LIMIT ?",
                (fts_query, limit),
            )
            return [dict(row) for row in cur.fetchall()]
        except sqlite3.OperationalError:
            return []

    def get_chunk_by_anchor_url(self, anchor_url: str) -> dict[str, Any] | None:
        """Look up a chunk by its full anchor URL (url + '#' + anchor fragment)."""
        if "#" in anchor_url:
            idx = anchor_url.rindex("#")
            url, anchor = anchor_url[:idx], anchor_url[idx:]
        else:
            url, anchor = anchor_url, ""
        cur = self._conn.cursor()
        cur.execute("SELECT * FROM chunks WHERE url=? AND anchor=?", (url, anchor))
        row = cur.fetchone()
        return dict(row) if row else None

    def list_module_urls(self, kind: str | None = None) -> list[dict[str, Any]]:
        """Return distinct (url, kind) rows, optionally filtered by kind."""
        cur = self._conn.cursor()
        if kind is not None:
            cur.execute(
                "SELECT DISTINCT url, kind FROM chunks WHERE kind=? ORDER BY url",
                (kind,),
            )
        else:
            cur.execute("SELECT DISTINCT url, kind FROM chunks ORDER BY url")
        return [dict(row) for row in cur.fetchall()]

    def get_chunks_by_url(self, url: str) -> list[dict[str, Any]]:
        """Return all chunks belonging to the given page URL."""
        cur = self._conn.cursor()
        cur.execute("SELECT * FROM chunks WHERE url=? ORDER BY id", (url,))
        return [dict(row) for row in cur.fetchall()]

    def get_chunk_by_heading(self, heading: str) -> dict[str, Any] | None:
        """Return the first chunk whose heading exactly matches the given value."""
        cur = self._conn.cursor()
        cur.execute("SELECT * FROM chunks WHERE heading=? LIMIT 1", (heading,))
        row = cur.fetchone()
        return dict(row) if row else None

    def count_chunks(self) -> int:
        cur = self._conn.cursor()
        cur.execute("SELECT COUNT(*) FROM chunks")
        result = cur.fetchone()
        return int(result[0]) if result else 0

    def load_vec_extension(self) -> None:
        """Load the sqlite-vec extension into this connection."""
        import sqlite_vec  # type: ignore[import-untyped]

        self._conn.enable_load_extension(True)
        sqlite_vec.load(self._conn)
        self._conn.enable_load_extension(False)

    def init_vec_schema(self, dim: int) -> None:
        """Create the chunks_vec virtual table with *dim*-dimensional embeddings."""
        self._conn.executescript(_SCHEMA_VEC.format(dim=dim))
        self._conn.commit()

    def upsert_embedding(self, chunk_id: int, embedding: list[float]) -> None:
        """Insert or replace an embedding vector for *chunk_id*."""
        import struct

        blob = struct.pack(f"{len(embedding)}f", *embedding)
        cur = self._conn.cursor()
        cur.execute(
            "INSERT OR REPLACE INTO chunks_vec(chunk_id, embedding) VALUES(?, ?)",
            (chunk_id, blob),
        )
        self._conn.commit()

    def vec_search(self, query_embedding: list[float], limit: int = 10) -> list[dict[str, Any]]:
        """Return the *limit* nearest chunks by L2 distance to *query_embedding*."""
        import struct

        blob = struct.pack(f"{len(query_embedding)}f", *query_embedding)
        cur = self._conn.cursor()
        cur.execute(
            "SELECT chunk_id, distance FROM chunks_vec "
            "WHERE embedding MATCH ? AND k=? "
            "ORDER BY distance",
            (blob, limit),
        )
        return [{"chunk_id": int(row[0]), "distance": float(row[1])} for row in cur.fetchall()]

    def close(self) -> None:
        self._conn.close()

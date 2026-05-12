"""Live fallback: ETag-aware disk-cached HTTP client."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx


def domain_allowed(url: str, allowed_domains: frozenset[str]) -> bool:
    host = urlparse(url).hostname or ""
    return host in allowed_domains


def _cache_key(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()


def _cache_path(cache_dir: str, url: str) -> Path:
    return Path(cache_dir) / (_cache_key(url) + ".json")


def _load_cache(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except (json.JSONDecodeError, OSError):
        return None


def _save_cache(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data), encoding="utf-8")
    tmp.replace(path)


async def fetch(
    url: str,
    *,
    network_enabled: bool,
    allowed_domains: frozenset[str],
    cache_dir: str,
    ttl_s: int,
    client: httpx.AsyncClient,
) -> dict[str, Any]:
    """Fetch *url* with ETag-aware disk cache.

    Returns a dict with keys: url, content, status_code, source ('live'|'live-cache'|'cache').
    ttl_s=0 forces revalidation on every call even when cached content is fresh.
    """
    if not network_enabled:
        cached = _load_cache(_cache_path(cache_dir, url))
        if cached is not None:
            return {**cached, "source": "cache"}
        return {"error": "live network access is disabled and no cache available", "url": url}

    if not domain_allowed(url, allowed_domains):
        host = urlparse(url).hostname
        return {"error": f"domain not in allowlist: {host}", "url": url}

    cache_path = _cache_path(cache_dir, url)
    cached = _load_cache(cache_path)

    if cached is not None and ttl_s > 0:
        age = time.time() - cached.get("cached_at", 0.0)
        if age < ttl_s:
            return {**cached, "source": "live-cache"}

    headers: dict[str, str] = {}
    if cached is not None and "etag" in cached:
        headers["If-None-Match"] = cached["etag"]

    try:
        response = await client.get(url, headers=headers, follow_redirects=True)

        if response.status_code == 304 and cached is not None:
            updated = {**cached, "cached_at": time.time()}
            try:
                _save_cache(cache_path, updated)
            except OSError:
                pass
            return {**updated, "source": "live-cache"}

        response.raise_for_status()

        data: dict[str, Any] = {
            "url": url,
            "status_code": response.status_code,
            "content": response.text,
            "cached_at": time.time(),
        }
        if "etag" in response.headers:
            data["etag"] = response.headers["etag"]

        try:
            _save_cache(cache_path, data)
        except OSError:
            pass

        return {**data, "source": "live"}

    except httpx.HTTPError as exc:
        return {"error": str(exc), "url": url}

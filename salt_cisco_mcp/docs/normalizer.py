from __future__ import annotations

import re
from dataclasses import dataclass

from markdownify import markdownify
from selectolax.parser import HTMLParser


@dataclass
class PageMeta:
    title: str
    anchor: str
    breadcrumb: str
    kind: str          # "module" | "state" | "proxy" | "runner" | "grain" | "other"
    salt_version: str  # always "3007"
    url: str


def _slugify(text: str) -> str:
    slug = text.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug


def _determine_kind(url: str) -> str:
    if "/ref/modules/" in url:
        return "module"
    if "/ref/states/" in url:
        return "state"
    if "/ref/proxy/" in url:
        return "proxy"
    if "/ref/runners/" in url:
        return "runner"
    if "/ref/grains/" in url:
        return "grain"
    return "other"


def _extract_salt_version(url: str) -> str:
    m = re.search(r"/en/(\d+)/", url)
    return m.group(1) if m else "3007"


def _build_breadcrumb(url: str, salt_version: str) -> str:
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        parts = [p for p in parsed.path.split("/") if p and p != salt_version and p != "en"]
        return "Salt " + salt_version + " > " + " > ".join(parts)
    except Exception:
        return "Salt " + salt_version


def normalize_page(html: str, url: str) -> tuple[str, PageMeta]:
    """Parse HTML, return (markdown, PageMeta)."""
    if not html or not html.strip():
        kind = _determine_kind(url)
        salt_version = _extract_salt_version(url)
        return "", PageMeta(
            title="",
            anchor="#",
            breadcrumb=_build_breadcrumb(url, salt_version),
            kind=kind,
            salt_version=salt_version,
            url=url,
        )

    tree = HTMLParser(html)

    # Extract title: h1 first, then <title>, then ""
    h1_node = tree.css_first("h1")
    title_node = tree.css_first("title")
    if h1_node is not None and h1_node.text(strip=True):
        title = h1_node.text(strip=True)
    elif title_node is not None and title_node.text(strip=True):
        title = title_node.text(strip=True)
    else:
        title = ""

    # Determine anchor from URL fragment or slugified title
    if "#" in url:
        anchor = "#" + url.split("#", 1)[1]
    else:
        anchor = "#" + _slugify(title) if title else "#"

    kind = _determine_kind(url)
    salt_version = _extract_salt_version(url)
    breadcrumb = _build_breadcrumb(url, salt_version)

    # Convert to markdown
    md = markdownify(html)
    if not isinstance(md, str):
        md = str(md)

    meta = PageMeta(
        title=title,
        anchor=anchor,
        breadcrumb=breadcrumb,
        kind=kind,
        salt_version=salt_version,
        url=url,
    )
    return md, meta

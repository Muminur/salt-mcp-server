from salt_cisco_mcp.docs.chunker import chunk_page
from salt_cisco_mcp.docs.normalizer import PageMeta

_META = PageMeta(
    title="Test Page",
    anchor="#test-page",
    breadcrumb="Salt 3007 > Test",
    kind="module",
    salt_version="3007",
    url="https://docs.saltproject.io/en/3007/ref/modules/all/salt.modules.test.html",
)


def test_chunk_single_section_returns_one_chunk() -> None:
    md = "# Config Module\n\nThis module provides configuration access.\n"
    chunks = chunk_page(md, _META)
    assert len(chunks) == 1


def test_chunk_preserves_code_blocks() -> None:
    md = (
        "# Usage\n\nSome text.\n\n"
        "```\nsalt-call config.get key\n```\n\n"
        "# Next Section\n\nMore text.\n"
    )
    chunks = chunk_page(md, _META, max_tokens=5)
    full_text = "\n".join(c.text for c in chunks)
    assert "salt-call config.get key" in full_text


def test_chunk_respects_max_tokens() -> None:
    words = " ".join(f"word{i}" for i in range(1000))
    md = f"# Big Section\n\n{words}\n"
    chunks = chunk_page(md, _META, max_tokens=100)
    for chunk in chunks:
        assert chunk.token_count <= 150


def test_chunk_heading_captured() -> None:
    md = "# Installation\n\nInstall with pip.\n\n# Configuration\n\nSet env vars.\n"
    chunks = chunk_page(md, _META)
    headings = [c.heading for c in chunks]
    assert any("Installation" in h for h in headings)
    assert any("Configuration" in h for h in headings)


def test_chunk_anchor_format() -> None:
    md = "# Section\n\nContent here.\n"
    chunks = chunk_page(md, _META)
    for chunk in chunks:
        assert chunk.anchor.startswith("#") or chunk.anchor.startswith("http")


def test_chunk_empty_markdown_returns_empty_list() -> None:
    assert chunk_page("", _META) == []


def test_chunk_inherits_kind_from_meta() -> None:
    md = "# Proxy Config\n\nProxy configuration.\n"
    chunks = chunk_page(md, _META)
    for chunk in chunks:
        assert chunk.kind == _META.kind

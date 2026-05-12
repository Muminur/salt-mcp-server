from salt_cisco_mcp.docs.normalizer import PageMeta, normalize_page


def test_normalize_simple_html_returns_markdown() -> None:
    html = "<h1>Title</h1><p>Body text.</p>"
    md, meta = normalize_page(html, url="https://docs.saltproject.io/en/3007/topics/foo.html")
    assert "Title" in md
    assert "Body text" in md


def test_normalize_preserves_code_blocks() -> None:
    html = "<pre><code>salt-call test.ping</code></pre>"
    md, _ = normalize_page(html, url="https://docs.saltproject.io/en/3007/topics/foo.html")
    assert "salt-call test.ping" in md


def test_normalize_extracts_title() -> None:
    html = (
        "<html><head><title>Config Module</title></head>"
        "<body><h1>Config Module</h1></body></html>"
    )
    _, meta = normalize_page(html, url="https://docs.saltproject.io/en/3007/topics/foo.html")
    assert meta.title != ""
    assert "Config" in meta.title


def test_normalize_extracts_kind_module() -> None:
    html = "<h1>Execution</h1>"
    _, meta = normalize_page(
        html, url="https://docs.saltproject.io/en/3007/ref/modules/all/salt.modules.config.html"
    )
    assert meta.kind == "module"


def test_normalize_extracts_kind_state() -> None:
    html = "<h1>State</h1>"
    _, meta = normalize_page(
        html, url="https://docs.saltproject.io/en/3007/ref/states/all/salt.states.file.html"
    )
    assert meta.kind == "state"


def test_normalize_extracts_kind_other() -> None:
    html = "<h1>Guide</h1>"
    _, meta = normalize_page(
        html, url="https://docs.saltproject.io/en/3007/topics/installation/index.html"
    )
    assert meta.kind == "other"


def test_normalize_sets_salt_version() -> None:
    html = "<h1>X</h1>"
    _, meta = normalize_page(html, url="https://docs.saltproject.io/en/3007/topics/foo.html")
    assert meta.salt_version == "3007"


def test_normalize_empty_html_returns_empty_markdown() -> None:
    md, meta = normalize_page("", url="https://docs.saltproject.io/en/3007/topics/foo.html")
    assert isinstance(md, str)
    assert isinstance(meta, PageMeta)

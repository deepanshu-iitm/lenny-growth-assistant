from app.artifacts import sanitize_html, strip_code_fence, title_from_html, title_from_markdown


def test_markdown_title():
    assert title_from_markdown("# How Duolingo Grew\n\nHello") == "How Duolingo Grew"


def test_html_title_and_fence():
    raw = "```html\n<title>Duolingo one-pager</title><h1>Hi</h1>\n```"
    assert title_from_html(raw) == "Duolingo one-pager"
    assert strip_code_fence(raw).startswith("<title>")


def test_sanitize_strips_script_and_handlers():
    dirty = '<p onclick="alert(1)">ok</p><script>steal()</script>'
    clean = sanitize_html(dirty)
    assert "script" not in clean.lower()
    assert "onclick" not in clean.lower()
    assert "ok" in clean

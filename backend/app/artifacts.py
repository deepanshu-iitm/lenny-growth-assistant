import re

from app.models import Artifact


def strip_code_fence(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z]*\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()


def title_from_html(html: str) -> str:
    html = strip_code_fence(html)
    match = re.search(r"<title>(.*?)</title>", html, flags=re.I | re.S)
    if match:
        return re.sub(r"\s+", " ", match.group(1)).strip()[:300]
    match = re.search(r"<h1[^>]*>(.*?)</h1>", html, flags=re.I | re.S)
    if match:
        return re.sub(r"<[^>]+>", "", match.group(1)).strip()[:300]
    return "HTML one-pager"


def title_from_markdown(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()[:300]
    return "Untitled artifact"


def sanitize_html(html: str) -> str:
    cleaned = re.sub(r"<script[\s\S]*?</script>", "", html, flags=re.I)
    cleaned = re.sub(r"<iframe[\s\S]*?</iframe>", "", cleaned, flags=re.I)
    cleaned = re.sub(r"<(object|embed|link|meta)[\s\S]*?>", "", cleaned, flags=re.I)
    cleaned = re.sub(r"\son\w+\s*=", " ", cleaned, flags=re.I)
    cleaned = re.sub(r"javascript:", "", cleaned, flags=re.I)
    return cleaned


def make_artifact(
    session_id, message_id, kind: str, title: str, content: str
) -> Artifact:
    body = sanitize_html(strip_code_fence(content)) if kind == "html" else content
    return Artifact(
        session_id=session_id,
        message_id=message_id,
        kind=kind,
        title=title,
        content=body,
    )

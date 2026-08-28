import re

from app.models import Artifact


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
    body = sanitize_html(content) if kind == "html" else content
    return Artifact(
        session_id=session_id,
        message_id=message_id,
        kind=kind,
        title=title,
        content=body,
    )

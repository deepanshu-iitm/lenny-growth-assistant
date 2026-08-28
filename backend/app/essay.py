import re

ESSAY_MARKERS = (
    "ship 30",
    "ship30",
    "atomic essay",
    "write an essay",
    "write a essay",
    "draft an essay",
)


def wants_essay(text: str) -> bool:
    lowered = text.lower()
    if any(marker in lowered for marker in ESSAY_MARKERS):
        return True
    return "essay" in lowered and any(
        word in lowered for word in ("write", "draft", "ship")
    )


HTML_MARKERS = (
    "html",
    "one-pager",
    "one pager",
    "onepager",
    "landing page",
    "web page",
)


def wants_html(text: str) -> bool:
    lowered = text.lower()
    if wants_essay(text):
        return False
    return any(marker in lowered for marker in HTML_MARKERS)


def topic_query(text: str) -> str:
    cleaned = text
    for marker in ESSAY_MARKERS + HTML_MARKERS:
        cleaned = re.sub(re.escape(marker), " ", cleaned, flags=re.I)
    cleaned = re.sub(r"\bessay\b", " ", cleaned, flags=re.I)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" :-")
    return cleaned or text

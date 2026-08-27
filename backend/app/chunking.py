def _word_count(text: str) -> int:
    return len(text.split())


def chunk_markdown(text: str, target_words: int = 400, overlap_words: int = 40) -> list[dict]:
    sections: list[tuple[str | None, list[str]]] = []
    heading = None
    paras: list[str] = []

    def flush_section():
        if paras:
            sections.append((heading, paras.copy()))
            paras.clear()

    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("#"):
            flush_section()
            heading = line.lstrip("#").strip()
            continue
        if not line:
            if paras and paras[-1] != "":
                paras.append("")
            continue
        paras.append(line)
    flush_section()

    chunks = []
    for heading, lines in sections:
        body = "\n".join(p for p in lines if p)
        words = body.split()
        if not words:
            continue
        start = 0
        while start < len(words):
            end = min(start + target_words, len(words))
            piece = " ".join(words[start:end])
            chunks.append(
                {
                    "heading": heading,
                    "content": piece,
                    "token_count": max(1, _word_count(piece)),
                }
            )
            if end == len(words):
                break
            start = max(end - overlap_words, start + 1)
    return chunks

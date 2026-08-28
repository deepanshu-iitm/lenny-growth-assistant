import httpx

from app.config import settings
from app.models import Chunk


def _context(hits: list[Chunk]) -> str:
    blocks = []
    for chunk in hits:
        source = chunk.source
        who = source.guest or "unknown guest"
        blocks.append(
            f"Source: {source.title} ({who})\nPath: {source.path}\n{chunk.content}"
        )
    return "\n\n---\n\n".join(blocks)


async def write_grounded_answer(question: str, hits: list[Chunk]) -> str | None:
    if settings.llm_provider != "ollama" or not hits:
        return None
    prompt = (
        "You answer product and growth questions using ONLY the transcript excerpts below. "
        "If they are not enough, say so. Do not invent guests, companies, or claims. "
        "Write clearly. Mention the source titles you used.\n\n"
        f"Excerpts:\n{_context(hits)}\n\n"
        f"Question: {question}\n"
    )
    url = settings.ollama_base_url.rstrip("/") + "/api/chat"
    try:
        async with httpx.AsyncClient(timeout=settings.llm_timeout_seconds) as client:
            res = await client.post(
                url,
                json={
                    "model": settings.chat_model,
                    "stream": False,
                    "messages": [
                        {"role": "user", "content": prompt},
                    ],
                },
            )
            res.raise_for_status()
            data = res.json()
            text = (data.get("message") or {}).get("content") or ""
            return text.strip() or None
    except Exception:
        return None

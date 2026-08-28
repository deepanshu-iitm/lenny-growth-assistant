from pathlib import Path

import httpx

from app.config import settings
from app.models import Chunk

PROMPT = (
    "You answer product and growth questions using ONLY the transcript excerpts below. "
    "If they are not enough, say so. Do not invent guests, companies, or claims. "
    "Write clearly. Mention the source titles you used."
)


def _context(hits: list[Chunk]) -> str:
    blocks = []
    for chunk in hits:
        source = chunk.source
        who = source.guest or "unknown guest"
        blocks.append(
            f"Source: {source.title} ({who})\nPath: {source.path}\n{chunk.content}"
        )
    return "\n\n---\n\n".join(blocks)


def _user_prompt(question: str, hits: list[Chunk]) -> str:
    return f"{PROMPT}\n\nExcerpts:\n{_context(hits)}\n\nQuestion: {question}\n"


async def _ollama(prompt: str) -> str | None:
    url = settings.ollama_base_url.rstrip("/") + "/api/chat"
    async with httpx.AsyncClient(timeout=settings.llm_timeout_seconds) as client:
        res = await client.post(
            url,
            json={
                "model": settings.chat_model,
                "stream": False,
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        res.raise_for_status()
        data = res.json()
        text = (data.get("message") or {}).get("content") or ""
        return text.strip() or None


async def _openai(
    prompt: str, temperature: float = 0.2, max_tokens: int | None = None
) -> str | None:
    key = settings.openai_api_key.strip()
    if not key:
        return None
    url = settings.openai_base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": settings.openai_model,
        "temperature": temperature,
        "messages": [{"role": "user", "content": prompt}],
    }
    if max_tokens:
        payload["max_tokens"] = max_tokens
    async with httpx.AsyncClient(timeout=settings.llm_timeout_seconds) as client:
        res = await client.post(
            url,
            headers={"Authorization": f"Bearer {key}"},
            json=payload,
        )
        res.raise_for_status()
        data = res.json()
        choice = (data.get("choices") or [{}])[0]
        text = ((choice.get("message") or {}).get("content")) or ""
        return text.strip() or None


async def complete(
    prompt: str, temperature: float = 0.2, max_tokens: int | None = None
) -> str | None:
    try:
        if settings.llm_provider == "openai":
            return await _openai(prompt, temperature=temperature, max_tokens=max_tokens)
        if settings.llm_provider == "ollama":
            return await _ollama(prompt)
    except Exception:
        return None
    return None


async def write_grounded_answer(question: str, hits: list[Chunk]) -> str | None:
    if not hits:
        return None
    return await complete(_user_prompt(question, hits))


def load_skill(name: str) -> str:
    path = Path(settings.skills_dir) / name / "SKILL.md"
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


async def write_ship30_essay(topic: str, hits: list[Chunk]) -> str | None:
    if not hits:
        return None
    skill = load_skill("ship30")
    prompt = (
        f"{skill}\n\n---\n\nTranscript excerpts:\n{_context(hits)}\n\n"
        f"Write the essay on: {topic}\n"
    )
    return await complete(prompt, temperature=0.2, max_tokens=2800)

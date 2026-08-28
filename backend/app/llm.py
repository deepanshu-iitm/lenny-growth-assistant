from pathlib import Path

import httpx

from app.config import settings
from app.log import log
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


def _user_prompt(question: str, hits: list[Chunk], history: list[tuple[str, str]] | None = None) -> str:
    parts = [PROMPT]
    if history:
        lines = []
        for role, text in history[-8:]:
            lines.append(f"{role}: {text[:500]}")
        parts.append(
            "Earlier in this chat (the new question may refer to it). "
            "Still use ONLY the excerpts for facts.\n" + "\n".join(lines)
        )
    parts.append(f"Excerpts:\n{_context(hits)}")
    parts.append(f"Question: {question}")
    return "\n\n".join(parts)


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
    provider = settings.llm_provider
    model = settings.active_model()
    try:
        if provider == "openai":
            if not settings.openai_api_key.strip():
                log.warning(
                    "openai key missing",
                    extra={"event": "llm", "provider": provider, "model": model},
                )
                return None
            text = await _openai(prompt, temperature=temperature, max_tokens=max_tokens)
        elif provider == "ollama":
            text = await _ollama(prompt)
        else:
            log.warning(
                "unknown provider",
                extra={"event": "llm", "provider": provider},
            )
            return None
    except Exception as exc:
        log.warning(
            "llm failed",
            extra={
                "event": "llm",
                "provider": provider,
                "model": model,
                "error": str(exc),
            },
        )
        return None
    if not text:
        log.warning(
            "llm returned empty",
            extra={"event": "llm", "provider": provider, "model": model},
        )
        return None
    log.info(
        "llm ok",
        extra={"event": "llm", "provider": provider, "model": model},
    )
    return text


async def write_grounded_answer(
    question: str,
    hits: list[Chunk],
    history: list[tuple[str, str]] | None = None,
) -> str | None:
    if not hits:
        return None
    return await complete(_user_prompt(question, hits, history))


def load_skill(name: str) -> str:
    path = Path(settings.skills_dir) / name / "SKILL.md"
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


async def write_ship30_essay(
    topic: str, hits: list[Chunk], history: list[tuple[str, str]] | None = None
) -> str | None:
    if not hits:
        return None
    skill = load_skill("ship30")
    prior = ""
    if history:
        prior = "Chat so far (topic may be implied):\n" + "\n".join(
            f"{role}: {text[:400]}" for role, text in history[-6:]
        )
        prior += "\n\n"
    prompt = (
        f"{skill}\n\n---\n\n{prior}Transcript excerpts:\n{_context(hits)}\n\n"
        f"Write the essay on: {topic}\n"
    )
    return await complete(prompt, temperature=0.2, max_tokens=2800)


async def write_html_onepager(topic: str, hits: list[Chunk]) -> str | None:
    if not hits:
        return None
    skill = load_skill("artifacts")
    prompt = (
        f"{skill}\n\n---\n\nTranscript excerpts:\n{_context(hits)}\n\n"
        f"Build the one-pager about: {topic}\n"
    )
    return await complete(prompt, temperature=0.2, max_tokens=2500)

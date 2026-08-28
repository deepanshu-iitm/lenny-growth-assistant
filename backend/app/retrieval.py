import re

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Chunk


def query_terms(query: str) -> list[str]:
    return [w for w in re.findall(r"[A-Za-z0-9]+", query.lower()) if len(w) > 3]


def citation_from_chunk(chunk: Chunk) -> dict:
    source = chunk.source
    return {
        "title": source.title,
        "guest": source.guest,
        "path": source.path,
        "source_type": source.source_type,
        "heading": chunk.heading,
    }


def _score(chunk: Chunk, terms: list[str]) -> int:
    title = (chunk.source.title or "").lower()
    guest = (chunk.source.guest or "").lower()
    body = (chunk.content or "").lower()
    score = 0
    for term in terms:
        if term in title:
            score += 4
        elif term in guest:
            score += 3
        elif term in body:
            score += 1
    return score


async def search_chunks(db: AsyncSession, query: str, limit: int = 4) -> list[Chunk]:
    terms = query_terms(query)
    if not terms:
        return []
    clauses = [Chunk.content.ilike(f"%{term}%") for term in terms]
    result = await db.execute(
        select(Chunk)
        .options(selectinload(Chunk.source))
        .where(or_(*clauses))
        .limit(80)
    )
    ranked = []
    for chunk in result.scalars():
        score = _score(chunk, terms)
        if score:
            ranked.append((score, chunk))
    if not ranked:
        return []
    ranked.sort(key=lambda item: item[0], reverse=True)
    best = ranked[0][0]
    # Keep the best matches only, so "duolingo grow" does not drag in
    # every transcript that merely says "grow".
    ranked = [item for item in ranked if item[0] >= best - 1]

    hits = []
    seen = set()
    for _, chunk in ranked:
        path = chunk.source.path
        if path in seen:
            continue
        seen.add(path)
        hits.append(chunk)
        if len(hits) == limit:
            break
    return hits


def answer_from_hits(hits: list[Chunk]) -> tuple[str, list[dict]]:
    if not hits:
        return (
            "The archive I have doesn't support a reliable answer to that. Try a narrower question, or a topic that shows up in the ingested transcripts.",
            [],
        )

    parts = []
    citations = []
    for chunk in hits:
        source = chunk.source
        label = source.title
        if source.guest:
            label += f" - {source.guest}"
        parts.append(f"**{label}**\n{chunk.content}")
        citations.append(citation_from_chunk(chunk))
    text = "Here's what the archive says:\n\n" + "\n\n".join(parts)
    return text, citations

import re

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Chunk


def _query_terms(query: str) -> list[str]:
    return [w for w in re.findall(r"[A-Za-z0-9]+", query.lower()) if len(w) > 3]


async def search_chunks(db: AsyncSession, query: str, limit: int = 8) -> list[Chunk]:
    terms = _query_terms(query)
    if not terms:
        return []
    clauses = [Chunk.content.ilike(f"%{term}%") for term in terms]
    result = await db.execute(
        select(Chunk)
        .options(selectinload(Chunk.source))
        .where(or_(*clauses))
        .order_by(Chunk.ordinal)
        .limit(limit)
    )
    return list(result.scalars().all())


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
        citations.append(
            {
                "title": source.title,
                "guest": source.guest,
                "path": source.path,
                "source_type": source.source_type,
                "heading": chunk.heading,
            }
        )
    text = "Here's what the archive says:\n\n" + "\n\n".join(parts)
    return text, citations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Chunk


def _safe_like(query: str) -> str:
    cleaned = query.strip().replace("%", " ").replace("_", " ")
    return f"%{cleaned}%"


async def search_chunks(db: AsyncSession, query: str, limit: int = 8) -> list[Chunk]:
    if not query.strip():
        return []
    result = await db.execute(
        select(Chunk)
        .options(selectinload(Chunk.source))
        .where(Chunk.content.ilike(_safe_like(query)))
        .order_by(Chunk.ordinal)
        .limit(limit)
    )
    return list(result.scalars().all())

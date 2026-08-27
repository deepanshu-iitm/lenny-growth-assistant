from datetime import date
import uuid

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.ingest import ingest_sources
from app.models import Source
from app.retrieval import search_chunks

router = APIRouter(prefix="/admin", tags=["admin"])


class SourceOut(BaseModel):
    id: uuid.UUID
    source_type: str
    title: str
    guest: str | None
    published_at: date | None
    path: str

    model_config = {"from_attributes": True}


@router.post("/ingest")
async def ingest(db: AsyncSession = Depends(get_db)):
    return await ingest_sources(db)


@router.get("/sources", response_model=list[SourceOut])
async def list_sources(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Source).order_by(Source.title))
    return result.scalars().all()


class HitOut(BaseModel):
    chunk_id: uuid.UUID
    heading: str | None
    content: str
    title: str
    guest: str | None
    path: str
    source_type: str


@router.get("/search", response_model=list[HitOut])
async def search(q: str = Query(min_length=1), db: AsyncSession = Depends(get_db)):
    hits = await search_chunks(db, q)
    return [
        HitOut(
            chunk_id=chunk.id,
            heading=chunk.heading,
            content=chunk.content,
            title=chunk.source.title,
            guest=chunk.source.guest,
            path=chunk.source.path,
            source_type=chunk.source.source_type,
        )
        for chunk in hits
    ]

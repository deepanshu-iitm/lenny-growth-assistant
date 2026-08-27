from datetime import date
import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.ingest import ingest_sources
from app.models import Source

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

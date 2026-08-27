import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import DEMO_USER_ID, get_db
from app.models import ChatSession

router = APIRouter(prefix="/sessions", tags=["sessions"])


class SessionOut(BaseModel):
    id: uuid.UUID
    title: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MessageOut(BaseModel):
    id: uuid.UUID
    role: str
    content: str
    citations: list
    created_at: datetime

    model_config = {"from_attributes": True}


class SessionDetail(SessionOut):
    messages: list[MessageOut] = []


class SessionCreate(BaseModel):
    title: str = "New chat"


@router.get("", response_model=list[SessionOut])
async def list_sessions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == DEMO_USER_ID)
        .order_by(ChatSession.updated_at.desc())
    )
    return result.scalars().all()


@router.post("", response_model=SessionOut, status_code=201)
async def create_session(body: SessionCreate, db: AsyncSession = Depends(get_db)):
    session = ChatSession(user_id=DEMO_USER_ID, title=body.title)
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


@router.get("/{session_id}", response_model=SessionDetail)
async def get_session(session_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ChatSession)
        .options(selectinload(ChatSession.messages))
        .where(
            ChatSession.id == session_id,
            ChatSession.user_id == DEMO_USER_ID,
        )
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    session.messages.sort(key=lambda m: m.created_at)
    return session

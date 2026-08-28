import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db import DEMO_USER_ID, get_db
from app.essay import topic_query, wants_essay
from app.llm import write_grounded_answer, write_ship30_essay
from app.models import ChatSession, Message
from app.retrieval import answer_from_hits, search_chunks

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


class MessageCreate(BaseModel):
    content: str


class MessageReply(BaseModel):
    user: MessageOut
    assistant: MessageOut


async def _get_owned_session(
    session_id: uuid.UUID, db: AsyncSession, load_messages: bool = False
) -> ChatSession:
    stmt = select(ChatSession).where(
        ChatSession.id == session_id,
        ChatSession.user_id == DEMO_USER_ID,
    )
    if load_messages:
        stmt = stmt.options(selectinload(ChatSession.messages))
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


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
    session = await _get_owned_session(session_id, db, load_messages=True)
    session.messages.sort(key=lambda m: m.created_at)
    return session


@router.post("/{session_id}/messages", response_model=MessageReply, status_code=201)
async def add_message(
    session_id: uuid.UUID,
    body: MessageCreate,
    db: AsyncSession = Depends(get_db),
):
    session = await _get_owned_session(session_id, db)
    content = body.content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    user_message = Message(session_id=session.id, role="user", content=content)
    search_text = topic_query(content) if wants_essay(content) else content
    hits = await search_chunks(db, search_text, limit=6 if wants_essay(content) else 4)
    fallback, citations = answer_from_hits(hits)
    if wants_essay(content):
        written = await write_ship30_essay(search_text, hits)
        if written is None and hits:
            fallback = (
                "I couldn't reach the model to draft the Ship 30 essay. "
                "Select OpenAI (or start Ollama) and try again. "
                "Here is the source material I would have used:\n\n"
                + fallback
            )
    else:
        written = await write_grounded_answer(content, hits)
    assistant_message = Message(
        session_id=session.id,
        role="assistant",
        content=written or fallback,
        citations=citations,
    )
    session.updated_at = datetime.now(timezone.utc)
    db.add_all([user_message, assistant_message])
    await db.commit()
    await db.refresh(user_message)
    await db.refresh(assistant_message)
    return MessageReply(user=user_message, assistant=assistant_message)

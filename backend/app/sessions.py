import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.artifacts import make_artifact, title_from_html, title_from_markdown
from app.db import DEMO_USER_ID, get_db
from app.essay import topic_query, wants_essay, wants_html
from app.llm import write_grounded_answer, write_html_onepager, write_ship30_essay
from app.models import Artifact, ChatSession, Message
from app.retrieval import (
    answer_from_hits,
    chunks_from_best_source,
    search_chunks,
)

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


class ArtifactOut(BaseModel):
    id: uuid.UUID
    kind: str
    title: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class SessionDetail(SessionOut):
    messages: list[MessageOut] = []
    artifacts: list[ArtifactOut] = []


class SessionCreate(BaseModel):
    title: str = "New chat"


class MessageCreate(BaseModel):
    content: str


class MessageReply(BaseModel):
    user: MessageOut
    assistant: MessageOut
    artifacts: list[ArtifactOut] = []


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
    result = await db.execute(
        select(Artifact)
        .where(Artifact.session_id == session.id)
        .order_by(Artifact.created_at)
    )
    return SessionDetail(
        id=session.id,
        title=session.title,
        created_at=session.created_at,
        updated_at=session.updated_at,
        messages=session.messages,
        artifacts=list(result.scalars().all()),
    )


@router.post("/{session_id}/messages", response_model=MessageReply, status_code=201)
async def add_message(
    session_id: uuid.UUID,
    body: MessageCreate,
    db: AsyncSession = Depends(get_db),
):
    session = await _get_owned_session(session_id, db, load_messages=True)
    content = body.content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    prior = sorted(session.messages, key=lambda m: m.created_at)
    history = [(m.role, m.content) for m in prior]
    last_user = next((m.content for m in reversed(prior) if m.role == "user"), None)

    user_message = Message(session_id=session.id, role="user", content=content)
    special = wants_essay(content) or wants_html(content)
    search_text = topic_query(content) if special else content
    if last_user:
        search_text = f"{last_user} {search_text}"
    hits = await search_chunks(db, search_text, limit=6 if special else 4)
    if special:
        hits = await chunks_from_best_source(db, hits)
    fallback, citations = answer_from_hits(hits)
    written = None
    kind = None
    if wants_essay(content):
        kind = "markdown"
        written = await write_ship30_essay(search_text, hits, history)
        if written is None and hits:
            fallback = (
                "I couldn't reach the model to draft the Ship 30 essay. "
                "Select OpenAI (or start Ollama) and try again. "
                "Here is the source material I would have used:\n\n"
                + fallback
            )
    elif wants_html(content):
        kind = "html"
        written = await write_html_onepager(search_text, hits)
        if written is None and hits:
            fallback = (
                "I couldn't reach the model to build the HTML one-pager. "
                "Select OpenAI (or start Ollama) and try again."
            )
    else:
        written = await write_grounded_answer(content, hits, history)
    chat_text = written or fallback
    made = []
    title = ""
    if kind == "markdown" and written:
        title = title_from_markdown(written)
        chat_text = f"I drafted **{title}** and opened it beside the chat."
    elif kind == "html" and written:
        title = title_from_html(written)
        chat_text = f"I built **{title}** as an HTML one-pager and opened it beside the chat."
    assistant_message = Message(
        session_id=session.id,
        role="assistant",
        content=chat_text,
        citations=citations,
    )
    session.updated_at = datetime.now(timezone.utc)
    db.add_all([user_message, assistant_message])
    await db.flush()
    if kind and written:
        artifact = make_artifact(
            session.id,
            assistant_message.id,
            kind,
            title,
            written,
        )
        db.add(artifact)
        made.append(artifact)
    await db.commit()
    await db.refresh(user_message)
    await db.refresh(assistant_message)
    for item in made:
        await db.refresh(item)
    return MessageReply(user=user_message, assistant=assistant_message, artifacts=made)
